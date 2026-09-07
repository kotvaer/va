from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .audio import convert_to_asr_wav, probe_audio
from .structure import structure_transcript
from .transcription import apply_speaker_map, load_hotwords, transcribe_audio


def default_output_root() -> Path:
    configured = os.getenv("VA_OUTPUT_ROOT", "").strip()
    return Path(configured) if configured else Path.home() / "Documents" / "VA" / "outputs"


def default_work_root() -> Path:
    configured = os.getenv("VA_WORK_ROOT", "").strip()
    return Path(configured) if configured else Path.home() / "Library" / "Caches" / "VA" / "work"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice2structure",
        description="本地转写、区分说话人并结构化语音录音。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="查看录音编码、时长和声道信息")
    inspect_parser.add_argument("audio", type=Path)
    inspect_parser.set_defaults(handler=handle_inspect)

    transcribe_parser = subparsers.add_parser(
        "transcribe", help="本地执行音频预处理、转写和说话人分离"
    )
    transcribe_parser.add_argument("audio", type=Path)
    transcribe_parser.add_argument("--output-root", type=Path, default=default_output_root())
    transcribe_parser.add_argument("--work-root", type=Path, default=default_work_root())
    transcribe_parser.add_argument("--device", choices=["auto", "mps", "cpu"], default="auto")
    transcribe_parser.add_argument("--asr-model", default="paraformer-zh")
    transcribe_parser.add_argument("--hotwords-file", type=Path)
    transcribe_parser.add_argument("--hotwords")
    transcribe_parser.add_argument("--batch-size-seconds", type=int, default=120)
    transcribe_parser.add_argument("--sample-start", type=float)
    transcribe_parser.add_argument("--sample-duration", type=float)
    transcribe_parser.add_argument("--force", action="store_true")
    transcribe_parser.set_defaults(handler=handle_transcribe)

    label_parser = subparsers.add_parser("label", help="人工确认说话人姓名或角色")
    label_parser.add_argument("transcript", type=Path)
    label_parser.add_argument(
        "--map",
        action="append",
        required=True,
        dest="mappings",
        metavar="SPEAKER_0=主持人",
    )
    label_parser.add_argument("--output", type=Path)
    label_parser.set_defaults(handler=handle_label)

    structure_parser = subparsers.add_parser(
        "structure", help="纯本地合并相邻同说话人片段，生成可追溯的对话轮次"
    )
    structure_parser.add_argument("transcript", type=Path)
    structure_parser.add_argument("--output", type=Path)
    structure_parser.set_defaults(handler=handle_structure)

    return parser


def handle_inspect(args: argparse.Namespace) -> int:
    print(json.dumps(probe_audio(args.audio), ensure_ascii=False, indent=2))
    return 0


def handle_transcribe(args: argparse.Namespace) -> int:
    source = args.audio.expanduser().resolve()
    source_probe = probe_audio(source)
    run_id = build_run_id(source.stem, args.sample_start, args.sample_duration)
    output_dir = args.output_root.expanduser().resolve() / run_id
    work_dir = args.work_root.expanduser().resolve()
    wav_path = work_dir / f"{run_id}.16k.wav"

    if args.sample_start is not None and args.sample_start < 0:
        raise ValueError("--sample-start 不能为负数。")
    if args.sample_duration is not None and args.sample_duration <= 0:
        raise ValueError("--sample-duration 必须大于 0。")

    print(f"预处理录音：{source}")
    convert_to_asr_wav(
        source,
        wav_path,
        start_seconds=args.sample_start,
        duration_seconds=args.sample_duration,
        force=args.force,
    )
    processed_probe = probe_audio(wav_path)
    hotwords = load_hotwords(args.hotwords_file, args.hotwords)
    transcript_path, markdown_path = transcribe_audio(
        wav_path,
        output_dir,
        source_file=source,
        source_probe=processed_probe,
        clip_start_seconds=args.sample_start or 0,
        clip_duration_seconds=args.sample_duration,
        requested_device=args.device,
        asr_model=args.asr_model,
        hotwords=hotwords,
        batch_size_seconds=args.batch_size_seconds,
        force=args.force,
    )
    print(f"逐字稿 JSON：{transcript_path}")
    print(f"逐字稿 Markdown：{markdown_path}")
    return 0


def handle_label(args: argparse.Namespace) -> int:
    mapping = parse_mappings(args.mappings)
    json_path, markdown_path = apply_speaker_map(
        args.transcript.expanduser().resolve(),
        mapping,
        output_path=args.output.expanduser().resolve() if args.output else None,
    )
    print(f"已标注 JSON：{json_path}")
    print(f"已标注 Markdown：{markdown_path}")
    return 0


def handle_structure(args: argparse.Namespace) -> int:
    json_path, markdown_path = structure_transcript(
        args.transcript.expanduser().resolve(),
        output_path=args.output.expanduser().resolve() if args.output else None,
    )
    print(f"结构化对话 JSON：{json_path}")
    print(f"结构化对话 Markdown：{markdown_path}")
    return 0


def parse_mappings(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"映射格式错误：{item}；应为 SPEAKER_0=主持人")
        speaker, role = item.split("=", 1)
        speaker = speaker.strip()
        role = role.strip()
        if not speaker or not role:
            raise ValueError(f"映射不能为空：{item}")
        mapping[speaker] = role
    return mapping


def build_run_id(stem: str, start: float | None, duration: float | None) -> str:
    if start is None and duration is None:
        return stem
    start_text = compact_number(start or 0)
    duration_text = compact_number(duration or 0)
    return f"{stem}_sample_{start_text}s_{duration_text}s"


def compact_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value).replace(".", "p")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code = args.handler(args)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(1) from error
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
