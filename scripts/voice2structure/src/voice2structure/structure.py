from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .formats import (
    milliseconds_to_timestamp,
    read_json,
    render_structured_transcript_markdown,
    utc_now_iso,
    write_json,
)


def structure_transcript(
    transcript_path: Path, *, output_path: Path | None = None
) -> tuple[Path, Path]:
    """Merge adjacent segments from the same speaker into traceable dialogue turns."""
    transcript = read_json(transcript_path)
    turns = merge_adjacent_segments(transcript.get("segments") or [])
    if not turns:
        raise ValueError("逐字稿中没有可结构化的片段。")

    metadata = deepcopy(transcript.get("metadata") or {})
    metadata.update(
        {
            "source_transcript": str(transcript_path.resolve()),
            "structured_at": utc_now_iso(),
            "structure_method": "adjacent_same_speaker",
            "turn_count": len(turns),
        }
    )
    structured = {
        "metadata": metadata,
        "speakers": transcript.get("speakers") or sorted(
            {turn["speaker"] for turn in turns}
        ),
        "speaker_stats": build_speaker_stats(turns),
        "turns": turns,
    }

    destination = output_path or transcript_path.with_name(
        f"{transcript_path.stem}.structured.json"
    )
    markdown_path = destination.with_suffix(".md")
    write_json(destination, structured)
    markdown_path.write_text(
        render_structured_transcript_markdown(structured), encoding="utf-8"
    )
    return destination, markdown_path


def merge_adjacent_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    last_start_ms = -1
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if not text or not any(character.isalnum() for character in text):
            continue
        start_ms = _as_int(segment.get("start_ms"))
        end_ms = max(start_ms, _as_int(segment.get("end_ms")))
        if start_ms < last_start_ms:
            raise ValueError("逐字稿时间戳不是递增顺序，无法安全合并。")
        last_start_ms = start_ms
        speaker = str(segment.get("speaker") or "UNKNOWN")
        role = segment.get("role")
        segment_id = segment.get("id")

        if turns and turns[-1]["speaker"] == speaker:
            turn = turns[-1]
            turn["end_ms"] = max(turn["end_ms"], end_ms)
            turn["end"] = milliseconds_to_timestamp(turn["end_ms"])
            turn["text"] = join_text(turn["text"], text)
            turn["speech_duration_ms"] += max(0, end_ms - start_ms)
            turn["source_segment_ids"].append(segment_id)
            if not turn.get("role") and role:
                turn["role"] = role
            continue

        turns.append(
            {
                "turn_id": len(turns) + 1,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start": milliseconds_to_timestamp(start_ms),
                "end": milliseconds_to_timestamp(end_ms),
                "speaker": speaker,
                "role": role,
                "text": text,
                "speech_duration_ms": max(0, end_ms - start_ms),
                "source_segment_ids": [segment_id],
            }
        )
    return turns


def join_text(left: str, right: str) -> str:
    if not left:
        return right
    if not right:
        return left
    if left[-1].isascii() and left[-1].isalnum() and right[0].isascii() and right[0].isalnum():
        return f"{left} {right}"
    return left + right


def build_speaker_stats(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for turn in turns:
        speaker = turn["speaker"]
        current = stats.setdefault(
            speaker,
            {
                "speaker": speaker,
                "role": turn.get("role"),
                "turn_count": 0,
                "character_count": 0,
                "speech_duration_seconds": 0.0,
            },
        )
        current["turn_count"] += 1
        current["character_count"] += len(turn["text"])
        current["speech_duration_seconds"] += turn["speech_duration_ms"] / 1_000
        if not current.get("role") and turn.get("role"):
            current["role"] = turn["role"]
    for current in stats.values():
        current["speech_duration_seconds"] = round(
            current["speech_duration_seconds"], 3
        )
    return [stats[speaker] for speaker in sorted(stats)]


def _as_int(value: Any) -> int:
    return max(0, int(round(float(value or 0))))
