from __future__ import annotations

from pathlib import Path

from autosub.core.ffmpeg_runner import FFmpegError, run_ffmpeg_with_progress


def escape_subtitles_filter_path(path: Path) -> str:
    # FFmpeg filter arguments use ':' and '\' as special characters.
    text = str(path.resolve())
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def burn_subtitle(
    video_path: str | Path,
    subtitle_path: str | Path,
    output_path: str | Path,
    crf: int = 20,
    preset: str = "medium",
    duration: float = 0.0,
) -> str:
    video = Path(video_path)
    subtitle = Path(subtitle_path)
    output = Path(output_path)
    if not video.exists():
        raise FileNotFoundError(f"处理失败：视频文件不存在。\n文件：{video}")
    if not subtitle.exists():
        raise FileNotFoundError(f"处理失败：字幕文件不存在。\n文件：{subtitle}")

    output.parent.mkdir(parents=True, exist_ok=True)
    vf = f"subtitles='{escape_subtitles_filter_path(subtitle)}'"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-crf",
        str(crf),
        "-preset",
        preset,
        "-c:a",
        "copy",
        str(output),
    ]
    run_ffmpeg_with_progress(command, duration)
    if not output.exists() or output.stat().st_size == 0:
        raise FFmpegError(f"处理失败：字幕烧录后输出文件为空。\n文件：{output}", command)
    return str(output)
