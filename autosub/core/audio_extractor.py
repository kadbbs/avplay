from __future__ import annotations

from pathlib import Path

from autosub.core.ffmpeg_runner import FFmpegError, run_ffmpeg
from autosub.core.ffprobe import probe_media


def extract_audio(input_path: str | Path, output_audio_path: str | Path) -> str:
    media = probe_media(input_path)
    if not media.has_audio:
        raise FFmpegError(
            f"处理失败：当前视频没有检测到音轨，无法生成字幕。\n文件：{input_path}\n建议：请确认视频是否包含声音。",
            ["ffmpeg", str(input_path)],
        )

    output = Path(output_audio_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output),
        ]
    )
    if not output.exists() or output.stat().st_size == 0:
        raise FFmpegError(f"处理失败：音频提取后文件为空。\n文件：{output}", ["ffmpeg"])
    return str(output)
