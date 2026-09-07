from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class AudioToolError(RuntimeError):
    """Raised when ffmpeg or ffprobe cannot process an audio file."""


def require_audio_tools() -> tuple[str, str]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise AudioToolError(
            "找不到 ffmpeg/ffprobe。请先执行 `brew install ffmpeg`。"
        )
    return ffmpeg, ffprobe


def probe_audio(path: Path) -> dict[str, Any]:
    _, ffprobe = require_audio_tools()
    source = path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"录音不存在：{source}")

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,format_name:stream=codec_name,sample_rate,channels,channel_layout",
        "-of",
        "json",
        str(source),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise AudioToolError(completed.stderr.strip() or "ffprobe 无法读取录音")

    data = json.loads(completed.stdout)
    stream = next(
        (item for item in data.get("streams", []) if item.get("codec_name")), {}
    )
    format_info = data.get("format", {})
    duration_seconds = float(format_info.get("duration") or 0)
    return {
        "path": str(source),
        "name": source.name,
        "duration_seconds": duration_seconds,
        "duration_hms": format_duration(duration_seconds),
        "size_bytes": int(format_info.get("size") or source.stat().st_size),
        "format": format_info.get("format_name"),
        "codec": stream.get("codec_name"),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "channel_layout": stream.get("channel_layout"),
    }


def convert_to_asr_wav(
    source: Path,
    destination: Path,
    *,
    start_seconds: float | None = None,
    duration_seconds: float | None = None,
    force: bool = False,
) -> Path:
    ffmpeg, _ = require_audio_tools()
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"录音不存在：{source}")
    if destination.exists() and not force:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if start_seconds is not None:
        command.extend(["-ss", str(start_seconds)])
    command.extend(["-i", str(source)])
    if duration_seconds is not None:
        command.extend(["-t", str(duration_seconds)])
    command.extend(
        [
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            "-y" if force else "-n",
            str(destination),
        ]
    )
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise AudioToolError(completed.stderr.strip() or "ffmpeg 音频转换失败")
    return destination


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
