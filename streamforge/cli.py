from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from streamforge.core.channel import Channel, load_channels
from streamforge.core.ffmpeg_commands import (
    build_hls_command,
    build_publish_rtsp_command,
    build_push_rtmp_command,
    build_snapshot_command,
)
from streamforge.core.pipeline import describe_channel, ensure_runtime_dirs, run_channel
from streamforge.core.pipeline import build_channel_processes
from streamforge.core.process_manager import ProcessGroup
from streamforge.core.probe import probe_input


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="streamctl", description="StreamForge Gateway CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="使用 ffprobe 探测输入")
    probe.add_argument("input")

    cmd = sub.add_parser("command", help="只打印 FFmpeg 命令，不执行")
    cmd.add_argument("name")
    cmd.add_argument("input")
    cmd.add_argument("--kind", choices=["hls", "rtsp", "rtmp"], default="hls")
    cmd.add_argument("--rtsp-transport", default="tcp")
    cmd.add_argument("--rtmp-url")

    run = sub.add_parser("run-channel", help="启动一个通道")
    run.add_argument("name")
    run.add_argument("input")
    run.add_argument("--rtsp-transport", default="tcp")
    run.add_argument("--runtime-dir", default="runtime")
    run.add_argument("--hls", action="store_true")
    run.add_argument("--publish-rtsp", action="store_true")
    run.add_argument("--push-rtmp")

    config = sub.add_parser("run-config", help="按 channels.json 启动多个通道")
    config.add_argument("config")

    snapshot = sub.add_parser("snapshot", help="抓取一帧 JPEG")
    snapshot.add_argument("input")
    snapshot.add_argument("output")
    snapshot.add_argument("--rtsp-transport", default="tcp")

    serve = sub.add_parser("serve", help="启动本地 dashboard 和 HLS 静态服务")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8080)

    return parser


def _print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _shell_join(command: list[str]) -> str:
    import shlex

    return " ".join(shlex.quote(part) for part in command)


def make_channel(args: argparse.Namespace) -> Channel:
    return Channel(
        name=args.name,
        input=args.input,
        rtsp_transport=getattr(args, "rtsp_transport", "tcp"),
        hls=bool(getattr(args, "hls", False)),
        publish_rtsp=bool(getattr(args, "publish_rtsp", False)),
        push_rtmp=getattr(args, "push_rtmp", None),
        runtime_dir=Path(getattr(args, "runtime_dir", "runtime")),
    )


def command_probe(args: argparse.Namespace) -> None:
    _print_json(asdict(probe_input(args.input)))


def command_print(args: argparse.Namespace) -> None:
    channel = Channel(
        name=args.name,
        input=args.input,
        rtsp_transport=args.rtsp_transport,
        hls=True,
        publish_rtsp=args.kind == "rtsp",
        push_rtmp=args.rtmp_url,
    )
    if args.kind == "hls":
        command = build_hls_command(channel)
    elif args.kind == "rtsp":
        command = build_publish_rtsp_command(channel)
    else:
        command = build_push_rtmp_command(channel, args.rtmp_url)
    print(_shell_join(command))


def command_run_channel(args: argparse.Namespace) -> None:
    channel = make_channel(args)
    if not channel.hls and not channel.publish_rtsp and not channel.push_rtmp:
        channel.hls = True
    ensure_runtime_dirs(channel.runtime_dir)
    _print_json(describe_channel(channel))
    run_channel(channel)


def command_run_config(args: argparse.Namespace) -> None:
    channels = load_channels(args.config)
    if not channels:
        raise ValueError("配置文件里没有 channels。")
    processes = []
    for channel in channels:
        ensure_runtime_dirs(channel.runtime_dir)
        _print_json(describe_channel(channel))
        processes.extend(build_channel_processes(channel))
    ProcessGroup(processes).run_forever()


def command_snapshot(args: argparse.Namespace) -> None:
    import subprocess

    command = build_snapshot_command(args.input, args.output, args.rtsp_transport)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    print(args.output)


class DashboardHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def command_serve(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parent / "web"
    hls = Path.cwd() / "runtime" / "hls"
    hls.mkdir(parents=True, exist_ok=True)

    # Serve dashboard files from streamforge/web. Symlink-like access to HLS is handled by
    # the page using relative /hls paths generated by a tiny handler override.
    class Handler(DashboardHandler):
        def translate_path(self, path: str) -> str:
            if path.startswith("/hls/"):
                return str(hls / path.removeprefix("/hls/"))
            relative = path.lstrip("/") or "index.html"
            return str(root / relative)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Dashboard: http://127.0.0.1:{args.port}")
    print(f"Local HLS base: http://127.0.0.1:{args.port}/hls/<channel>/index.m3u8")
    server.serve_forever()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "probe":
            command_probe(args)
        elif args.command == "command":
            command_print(args)
        elif args.command == "run-channel":
            command_run_channel(args)
        elif args.command == "run-config":
            command_run_config(args)
        elif args.command == "snapshot":
            command_snapshot(args)
        elif args.command == "serve":
            command_serve(args)
    except Exception as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
