from __future__ import annotations

import json
from pathlib import Path

from autosub.core.ffmpeg_runner import FFmpegError, run_ffmpeg
from autosub.models.media_info import MediaInfo


def probe_media(input_path: str | Path) -> MediaInfo:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"处理失败：输入文件不存在。\n文件：{path}")

    result = run_ffmpeg(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    subtitle = next((s for s in streams if s.get("codec_type") == "subtitle"), None)

    if not video:
        raise FFmpegError(
            f"处理失败：输入文件没有检测到视频流。\n文件：{path}\n建议：请确认输入是否为视频文件。",
            ["ffprobe", str(path)],
            result.stderr,
        )

    duration = float(data.get("format", {}).get("duration") or 0.0)
    return MediaInfo(
        path=str(path),
        duration=duration,
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        video_codec=video.get("codec_name") or "unknown",
        audio_codec=audio.get("codec_name") if audio else None,
        has_audio=audio is not None,
        has_subtitle=subtitle is not None,
    )
