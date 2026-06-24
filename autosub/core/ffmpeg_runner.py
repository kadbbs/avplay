from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable


class FFmpegError(RuntimeError):
    def __init__(self, message: str, command: list[str], stderr: str = ""):
        super().__init__(message)
        self.command = command
        self.stderr = stderr


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FFmpegError(
            f"处理失败：未找到 {name}。\n建议：请先安装 FFmpeg，并确认 `{name} -version` 可以运行。",
            [name],
        )
    return path


def run_ffmpeg(command: list[str]) -> subprocess.CompletedProcess[str]:
    require_binary(command[0])
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise FFmpegError(
            f"FFmpeg 执行失败：{command[0]} 返回 {result.returncode}",
            command,
            result.stderr,
        )
    return result


def parse_ffmpeg_time(line: str) -> float | None:
    match = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def run_ffmpeg_with_progress(
    command: list[str],
    duration: float,
    on_progress: Callable[[float], None] | None = None,
) -> int:
    require_binary(command[0])
    process = subprocess.Popen(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None
    output: list[str] = []

    for line in process.stdout:
        output.append(line)
        current = parse_ffmpeg_time(line)
        if current is not None and duration > 0 and on_progress:
            on_progress(min(current / duration, 1.0))

    code = process.wait()
    if code != 0:
        raise FFmpegError(
            f"FFmpeg 执行失败：{command[0]} 返回 {code}",
            command,
            "".join(output),
        )
    return code
