from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from streamforge.core.errors import BinaryNotFoundError, ProcessFailedError


@dataclass(slots=True)
class MediaProbe:
    input: str
    duration: float
    width: int
    height: int
    video_codec: str | None
    audio_codec: str | None
    has_video: bool
    has_audio: bool


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise BinaryNotFoundError(f"未找到 {name}，请先安装 FFmpeg 并确认 `{name} -version` 可运行。")
    return path


def probe_input(input_url: str) -> MediaProbe:
    require_binary("ffprobe")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        input_url,
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ProcessFailedError(f"ffprobe 探测失败：{result.stderr.strip()}")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration") or 0.0)

    return MediaProbe(
        input=input_url,
        duration=duration,
        width=int(video.get("width") or 0) if video else 0,
        height=int(video.get("height") or 0) if video else 0,
        video_codec=video.get("codec_name") if video else None,
        audio_codec=audio.get("codec_name") if audio else None,
        has_video=video is not None,
        has_audio=audio is not None,
    )
