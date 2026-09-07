from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .formats import render_transcript_markdown, to_jsonable, utc_now_iso, write_json


class TranscriptionError(RuntimeError):
    """Raised when FunASR transcription fails."""


def load_hotwords(path: Path | None, inline: str | None = None) -> str:
    terms: list[str] = []
    if path:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#"):
                terms.append(line)
    if inline:
        terms.extend(part.strip() for part in inline.split(",") if part.strip())
    return " ".join(dict.fromkeys(terms))


def transcribe_audio(
    wav_path: Path,
    output_dir: Path,
    *,
    source_file: Path,
    source_probe: dict[str, Any],
    clip_start_seconds: float = 0,
    clip_duration_seconds: float | None = None,
    requested_device: str = "auto",
    asr_model: str = "paraformer-zh",
    hotwords: str = "",
    batch_size_seconds: int = 120,
    force: bool = False,
) -> tuple[Path, Path]:
    transcript_path = output_dir / "transcript.json"
    markdown_path = output_dir / "transcript.md"
    if transcript_path.exists() and markdown_path.exists() and not force:
        return transcript_path, markdown_path

    output_dir.mkdir(parents=True, exist_ok=True)
    selected = select_device(requested_device)
    try:
        result = _run_funasr(
            wav_path,
            device=selected,
            asr_model=asr_model,
            hotwords=hotwords,
            batch_size_seconds=batch_size_seconds,
        )
        actual_device = selected
    except Exception as error:
        if requested_device == "auto" and selected == "mps":
            print(
                f"MPS 转写失败，自动回退 CPU：{error}",
                file=sys.stderr,
            )
            result = _run_funasr(
                wav_path,
                device="cpu",
                asr_model=asr_model,
                hotwords=hotwords,
                batch_size_seconds=batch_size_seconds,
            )
            actual_device = "cpu"
        else:
            raise TranscriptionError(str(error)) from error

    raw_path = output_dir / "raw.funasr.json"
    write_json(raw_path, result)
    time_offset_ms = int(round(clip_start_seconds * 1_000))
    segments = extract_segments(result, time_offset_ms=time_offset_ms)
    speakers = sorted(
        {segment["speaker"] for segment in segments if segment["speaker"] != "UNKNOWN"}
    )
    transcript = {
        "metadata": {
            "title": f"{source_file.stem} 语音逐字稿",
            "source_file": source_file.name,
            "source_path": str(source_file.resolve()),
            "working_audio": str(wav_path.resolve()),
            "duration_seconds": source_probe.get("duration_seconds"),
            "duration_hms": source_probe.get("duration_hms"),
            "clip_start_seconds": clip_start_seconds,
            "clip_duration_seconds": clip_duration_seconds,
            "timestamps_reference": "source_audio",
            "asr_model": asr_model,
            "speaker_model": "cam++",
            "device": actual_device,
            "hotwords": hotwords.split() if hotwords else [],
            "generated_at": utc_now_iso(),
            "speaker_labels_reviewed": False,
        },
        "speakers": speakers,
        "segments": segments,
    }
    write_json(transcript_path, transcript)
    markdown_path.write_text(render_transcript_markdown(transcript), encoding="utf-8")
    write_json(
        output_dir / "speaker-map.example.json",
        {speaker: "" for speaker in speakers},
    )
    return transcript_path, markdown_path


def select_device(requested: str) -> str:
    if requested in {"cpu", "mps"}:
        return requested
    if requested != "auto":
        raise ValueError(f"不支持的设备：{requested}")
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def _run_funasr(
    wav_path: Path,
    *,
    device: str,
    asr_model: str,
    hotwords: str,
    batch_size_seconds: int,
) -> list[dict[str, Any]]:
    try:
        from funasr import AutoModel
    except ImportError as error:
        raise TranscriptionError("FunASR 尚未安装，请先运行 VA 入口完成 uv 同步。") from error

    print(f"加载 FunASR：model={asr_model}, device={device}")
    model = AutoModel(
        model=asr_model,
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 60_000},
        punc_model="ct-punc",
        spk_model="cam++",
        spk_mode="punc_segment",
        device=device,
        ncpu=8,
        disable_update=True,
    )
    options: dict[str, Any] = {
        "input": str(wav_path),
        "cache": {},
        "batch_size_s": batch_size_seconds,
        "sentence_timestamp": True,
    }
    if hotwords:
        options["hotword"] = hotwords
    return to_jsonable(model.generate(**options))


def extract_segments(
    result: list[dict[str, Any]], *, time_offset_ms: int = 0
) -> list[dict[str, Any]]:
    if not result:
        raise TranscriptionError("FunASR 没有返回结果。")
    root = result[0]
    sentence_info = root.get("sentence_info") or []
    segments: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentence_info):
        text = str(sentence.get("text") or "").strip()
        if not text:
            continue
        raw_speaker = sentence.get("spk")
        speaker = normalize_speaker(raw_speaker)
        segments.append(
            {
                "id": index + 1,
                "start_ms": _as_milliseconds(sentence.get("start")) + time_offset_ms,
                "end_ms": _as_milliseconds(sentence.get("end")) + time_offset_ms,
                "speaker": speaker,
                "role": None,
                "text": text,
                "timestamp": _offset_timestamps(
                    sentence.get("timestamp") or [], time_offset_ms
                ),
            }
        )

    if segments:
        return segments
    text = str(root.get("text") or "").strip()
    if not text:
        raise TranscriptionError("FunASR 返回结果中没有可用文本。")
    return [
        {
            "id": 1,
            "start_ms": 0,
            "end_ms": 0,
            "speaker": "UNKNOWN",
            "role": None,
            "text": text,
            "timestamp": root.get("timestamp") or [],
        }
    ]


def normalize_speaker(value: Any) -> str:
    if value is None or str(value).strip() == "":
        return "UNKNOWN"
    normalized = str(value).strip().upper().replace(" ", "_")
    if normalized.startswith("SPEAKER_"):
        return normalized
    return f"SPEAKER_{normalized}"


def _as_milliseconds(value: Any) -> int:
    if value is None:
        return 0
    return max(0, int(round(float(value))))


def _offset_timestamps(timestamps: Any, offset_ms: int) -> Any:
    if not offset_ms or not isinstance(timestamps, list):
        return timestamps
    adjusted: list[Any] = []
    for item in timestamps:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            adjusted.append(
                [
                    _as_milliseconds(item[0]) + offset_ms,
                    _as_milliseconds(item[1]) + offset_ms,
                    *item[2:],
                ]
            )
        else:
            adjusted.append(item)
    return adjusted


def apply_speaker_map(
    transcript_path: Path,
    mapping: dict[str, str],
    *,
    output_path: Path | None = None,
) -> tuple[Path, Path]:
    from .formats import read_json

    transcript = read_json(transcript_path)
    normalized_mapping = {
        normalize_speaker(key): value.strip()
        for key, value in mapping.items()
        if value.strip()
    }
    if not normalized_mapping:
        raise ValueError("至少需要一个非空的说话人映射。")
    for segment in transcript.get("segments", []):
        speaker = normalize_speaker(segment.get("speaker"))
        segment["speaker"] = speaker
        segment["role"] = normalized_mapping.get(speaker)

    metadata = transcript.setdefault("metadata", {})
    metadata["speaker_map"] = normalized_mapping
    observed = {segment.get("speaker") for segment in transcript.get("segments", [])}
    metadata["speaker_labels_reviewed"] = observed.issubset(normalized_mapping)
    metadata["labeled_at"] = utc_now_iso()

    destination = output_path or transcript_path.with_name("transcript.labeled.json")
    markdown_path = destination.with_suffix(".md")
    write_json(destination, transcript)
    markdown_path.write_text(render_transcript_markdown(transcript), encoding="utf-8")
    return destination, markdown_path
