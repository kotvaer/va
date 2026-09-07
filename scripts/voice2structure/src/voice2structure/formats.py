from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return str(value)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(data), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def milliseconds_to_timestamp(value: int | float | None) -> str:
    total_ms = max(0, int(round(float(value or 0))))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def render_transcript_markdown(transcript: dict[str, Any]) -> str:
    metadata = transcript.get("metadata", {})
    lines = [
        f"# {metadata.get('title') or '语音逐字稿'}",
        "",
        f"- 来源：{metadata.get('source_file', '未知')}",
        f"- 时长：{metadata.get('duration_hms', '未知')}",
        f"- 转写模型：{metadata.get('asr_model', '未知')}",
        f"- 设备：{metadata.get('device', '未知')}",
        "",
        "> 说话人标签来自自动聚类。用于分析前，请人工确认角色和关键原话。",
        "",
    ]

    for segment in transcript.get("segments", []):
        start = milliseconds_to_timestamp(segment.get("start_ms"))
        end = milliseconds_to_timestamp(segment.get("end_ms"))
        speaker = segment.get("role") or segment.get("speaker") or "UNKNOWN"
        text = str(segment.get("text") or "").strip()
        lines.extend([f"## [{start} – {end}] {speaker}", "", text, ""])
    return "\n".join(lines).rstrip() + "\n"


def render_structured_transcript_markdown(structured: dict[str, Any]) -> str:
    metadata = structured.get("metadata", {})
    lines = [
        f"# {metadata.get('title') or '结构化语音对话'}",
        "",
        f"- 来源：{metadata.get('source_file', '未知')}",
        f"- 时长：{metadata.get('duration_hms', '未知')}",
        f"- 对话轮次：{len(structured.get('turns') or [])}",
        "",
        "> 相邻且说话人相同的逐句片段已合并；每个轮次保留原始片段 ID，便于回溯。",
        "",
    ]
    for turn in structured.get("turns") or []:
        speaker = turn.get("role") or turn.get("speaker") or "UNKNOWN"
        segment_ids = ", ".join(str(item) for item in turn.get("source_segment_ids") or [])
        lines.extend(
            [
                f"## 轮次 {turn.get('turn_id')} · [{turn.get('start')} – {turn.get('end')}] · {speaker}",
                "",
                str(turn.get("text") or "").strip(),
                "",
                f"<!-- source_segment_ids: {segment_ids} -->",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
