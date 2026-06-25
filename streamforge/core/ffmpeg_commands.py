from __future__ import annotations

from pathlib import Path

from streamforge.core.channel import Channel


def _input_args(channel: Channel) -> list[str]:
    args = ["-hide_banner"]
    if channel.input.startswith("rtsp://"):
        args += ["-rtsp_transport", channel.rtsp_transport]
    if not channel.input.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        args += ["-stream_loop", "-1", "-re"]
    args += ["-i", channel.input]
    return args


def _low_latency_encode_args() -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-tune",
        "zerolatency",
        "-pix_fmt",
        "yuv420p",
        "-g",
        "50",
        "-sc_threshold",
        "0",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
    ]


def build_hls_command(channel: Channel) -> list[str]:
    channel.hls_dir.mkdir(parents=True, exist_ok=True)
    segment_pattern = channel.hls_dir / "segment_%05d.ts"
    return (
        ["ffmpeg"]
        + _input_args(channel)
        + _low_latency_encode_args()
        + [
            "-f",
            "hls",
            "-hls_time",
            "2",
            "-hls_list_size",
            "6",
            "-hls_flags",
            "delete_segments+append_list+program_date_time",
            "-hls_segment_filename",
            str(segment_pattern),
            str(channel.hls_playlist),
        ]
    )


def build_publish_rtsp_command(channel: Channel) -> list[str]:
    return (
        ["ffmpeg"]
        + _input_args(channel)
        + _low_latency_encode_args()
        + [
            "-f",
            "rtsp",
            "-rtsp_transport",
            "tcp",
            channel.mediamtx_rtsp_url,
        ]
    )


def build_push_rtmp_command(channel: Channel, output_url: str | None = None) -> list[str]:
    target = output_url or channel.push_rtmp or channel.mediamtx_rtmp_url
    return (
        ["ffmpeg"]
        + _input_args(channel)
        + _low_latency_encode_args()
        + ["-f", "flv", target]
    )


def build_snapshot_command(input_url: str, output_path: str | Path, rtsp_transport: str = "tcp") -> list[str]:
    args = ["ffmpeg", "-hide_banner"]
    if input_url.startswith("rtsp://"):
        args += ["-rtsp_transport", rtsp_transport]
    args += ["-y", "-i", input_url, "-frames:v", "1", "-q:v", "2", str(output_path)]
    return args
