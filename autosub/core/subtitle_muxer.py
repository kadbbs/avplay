from __future__ import annotations

from pathlib import Path

from autosub.core.ffmpeg_runner import FFmpegError, run_ffmpeg


def mux_soft_subtitle(
    video_path: str | Path,
    subtitle_path: str | Path,
    output_path: str | Path,
) -> str:
    video = Path(video_path)
    subtitle = Path(subtitle_path)
    output = Path(output_path)
    if not video.exists():
        raise FileNotFoundError(f"处理失败：视频文件不存在。\n文件：{video}")
    if not subtitle.exists():
        raise FileNotFoundError(f"处理失败：字幕文件不存在。\n文件：{subtitle}")

    output.parent.mkdir(parents=True, exist_ok=True)
    suffix = output.suffix.lower()
    if suffix == ".mkv":
        command = ["ffmpeg", "-y", "-i", str(video), "-i", str(subtitle), "-c", "copy", "-c:s", "srt", str(output)]
    else:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(subtitle),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "mov_text",
            str(output),
        ]
    run_ffmpeg(command)
    if not output.exists() or output.stat().st_size == 0:
        raise FFmpegError(f"处理失败：软字幕封装后输出文件为空。\n文件：{output}", command)
    return str(output)
