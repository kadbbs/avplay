from __future__ import annotations

from pathlib import Path

from streamforge.core.channel import Channel
from streamforge.core.ffmpeg_commands import (
    build_hls_command,
    build_publish_rtsp_command,
    build_push_rtmp_command,
)
from streamforge.core.process_manager import ManagedProcess, ProcessGroup


def build_channel_processes(channel: Channel) -> list[ManagedProcess]:
    logs = channel.runtime_dir / "logs" / channel.name
    processes: list[ManagedProcess] = []

    # Each enabled output is intentionally a separate FFmpeg process. That makes
    # the commands easy to study and logs easy to inspect. A more advanced
    # version could use one FFmpeg command with multiple outputs.
    if channel.hls:
        processes.append(
            ManagedProcess(
                name=f"{channel.name}:hls",
                command=build_hls_command(channel),
                log_path=logs / "hls.log",
            )
        )

    if channel.publish_rtsp:
        processes.append(
            ManagedProcess(
                name=f"{channel.name}:rtsp-publish",
                command=build_publish_rtsp_command(channel),
                log_path=logs / "rtsp_publish.log",
            )
        )

    if channel.push_rtmp:
        processes.append(
            ManagedProcess(
                name=f"{channel.name}:rtmp-push",
                command=build_push_rtmp_command(channel),
                log_path=logs / "rtmp_push.log",
            )
        )

    return processes


def run_channel(channel: Channel) -> None:
    processes = build_channel_processes(channel)
    if not processes:
        raise ValueError("通道没有启用任何输出，请至少启用 HLS、RTSP publish 或 RTMP push。")
    ProcessGroup(processes).run_forever()


def describe_channel(channel: Channel) -> dict[str, str | bool]:
    return {
        "name": channel.name,
        "input": channel.input,
        "local_hls": str(channel.hls_playlist) if channel.hls else "",
        "rtsp": channel.mediamtx_rtsp_url,
        "rtmp": channel.mediamtx_rtmp_url,
        "hls": channel.mediamtx_hls_url,
        "webrtc": channel.mediamtx_webrtc_url,
        "hls_enabled": channel.hls,
        "publish_rtsp": channel.publish_rtsp,
        "push_rtmp": bool(channel.push_rtmp),
    }


def ensure_runtime_dirs(runtime_dir: str | Path = "runtime") -> None:
    root = Path(runtime_dir)
    (root / "hls").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
