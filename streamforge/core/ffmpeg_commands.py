from __future__ import annotations

from pathlib import Path

from streamforge.core.channel import Channel


def _input_args(channel: Channel) -> list[str]:
    args = ["-hide_banner"]

    # RTSP can run over UDP or TCP. TCP is the default here because it is
    # usually easier to get stable first when learning with IP cameras and NAT.
    if channel.input.startswith("rtsp://"):
        args += ["-rtsp_transport", channel.rtsp_transport]

    # Local files are not live sources. To use a file as a fake camera/live
    # stream, loop it forever and read it at real-time speed.
    if not channel.input.startswith(("rtsp://", "rtmp://", "http://", "https://")):
        args += ["-stream_loop", "-1", "-re"]

    args += ["-i", channel.input]
    return args


def _low_latency_encode_args() -> list[str]:
    # These options trade compression efficiency for predictable live behavior.
    # H.264/AAC are chosen because RTMP, HLS and most WebRTC gateways handle
    # them well. yuv420p is the safest pixel format for browsers and players.
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

    # HLS is just a playlist plus short media files. FFmpeg writes the .m3u8
    # playlist and rotating .ts segments into runtime/hls/<channel>/.
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
    # FFmpeg publishes an RTSP stream to MediaMTX. MediaMTX then exposes that
    # path as RTSP, HLS and WebRTC for clients.
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

    # RTMP conventionally carries FLV, so the muxer is "-f flv" even though the
    # encoded video/audio inside are still H.264/AAC.
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
