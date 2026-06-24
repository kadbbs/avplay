from __future__ import annotations

import argparse
import json
from pathlib import Path

from autosub.config import load_style
from autosub.core.ffprobe import probe_media
from autosub.core.subtitle_burner import burn_subtitle
from autosub.core.subtitle_muxer import mux_soft_subtitle
from autosub.models.task import SubtitleTask
from autosub.services.pipeline import run_pipeline
from autosub.services.task_queue import run_batch
from autosub.utils.path_utils import task_output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autosub", description="AutoSub Studio CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    info = sub.add_parser("info", help="查看视频信息")
    info.add_argument("input")

    transcribe = sub.add_parser("transcribe", help="生成字幕")
    transcribe.add_argument("input")
    transcribe.add_argument("--lang", default="auto")
    transcribe.add_argument("--model", default="small")
    transcribe.add_argument("--format", default="srt", choices=["srt", "vtt", "all"])
    transcribe.add_argument("--style", default="classic")
    transcribe.add_argument("--output-dir", default="output")
    transcribe.add_argument("--offset", type=float, default=0.0)

    burn = sub.add_parser("burn", help="烧录已有字幕")
    burn.add_argument("input")
    burn.add_argument("--subtitle", required=True)
    burn.add_argument("--style", default="classic")
    burn.add_argument("--crf", type=int, default=20)
    burn.add_argument("--preset", default="medium")
    burn.add_argument("--output")

    all_cmd = sub.add_parser("all", help="生成字幕并烧录")
    all_cmd.add_argument("input")
    all_cmd.add_argument("--lang", default="auto")
    all_cmd.add_argument("--model", default="small")
    all_cmd.add_argument("--style", default="classic")
    all_cmd.add_argument("--format", default="srt", choices=["srt", "vtt", "all"])
    all_cmd.add_argument("--output-dir", default="output")
    all_cmd.add_argument("--offset", type=float, default=0.0)
    all_cmd.add_argument("--crf", type=int, default=20)
    all_cmd.add_argument("--preset", default="medium")
    all_cmd.add_argument("--soft-subtitle", action="store_true")
    all_cmd.add_argument("--no-hard-subtitle", action="store_true")

    mux = sub.add_parser("mux", help="封装软字幕")
    mux.add_argument("input")
    mux.add_argument("--subtitle", required=True)
    mux.add_argument("--output", required=True)

    batch = sub.add_parser("batch", help="批量处理目录")
    batch.add_argument("directory")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--lang", default="auto")
    batch.add_argument("--model", default="small")
    batch.add_argument("--style", default="classic")
    batch.add_argument("--output-dir", default="output")
    batch.add_argument("--no-skip-done", action="store_true")

    return parser


def command_info(input_path: str) -> None:
    media = probe_media(input_path)
    print(f"文件名: {Path(media.path).name}")
    print(f"时长: {media.duration:.2f}s")
    print(f"分辨率: {media.width}x{media.height}")
    print(f"视频编码: {media.video_codec}")
    print(f"音频编码: {media.audio_codec or '无'}")
    print(f"是否有音轨: {'是' if media.has_audio else '否'}")
    print(f"是否有字幕轨: {'是' if media.has_subtitle else '否'}")


def command_transcribe(args: argparse.Namespace) -> None:
    task = SubtitleTask(
        input_path=args.input,
        output_dir=args.output_dir,
        language=args.lang,
        model=args.model,
        subtitle_format=args.format,
        style_name=args.style,
        burn_subtitle=False,
        soft_subtitle=False,
        offset=args.offset,
    )
    report = run_pipeline(task)
    print(json.dumps(report["outputs"], ensure_ascii=False, indent=2))


def command_burn(args: argparse.Namespace) -> None:
    load_style(args.style)  # Validate the style name early for CLI consistency.
    media = probe_media(args.input)
    output = args.output
    if not output:
        work_dir = task_output_dir(args.input, "output")
        work_dir.mkdir(parents=True, exist_ok=True)
        output = str(work_dir / f"{Path(args.input).stem}_subtitled.mp4")
    result = burn_subtitle(args.input, args.subtitle, output, args.crf, args.preset, media.duration)
    print(result)


def command_all(args: argparse.Namespace) -> None:
    task = SubtitleTask(
        input_path=args.input,
        output_dir=args.output_dir,
        language=args.lang,
        model=args.model,
        subtitle_format=args.format,
        style_name=args.style,
        burn_subtitle=not args.no_hard_subtitle,
        soft_subtitle=args.soft_subtitle,
        offset=args.offset,
        crf=args.crf,
        preset=args.preset,
    )
    report = run_pipeline(task)
    print(json.dumps(report["outputs"], ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            command_info(args.input)
        elif args.command == "transcribe":
            command_transcribe(args)
        elif args.command == "burn":
            command_burn(args)
        elif args.command == "all":
            command_all(args)
        elif args.command == "mux":
            print(mux_soft_subtitle(args.input, args.subtitle, args.output))
        elif args.command == "batch":
            report = run_batch(
                args.directory,
                args.output_dir,
                args.recursive,
                args.lang,
                args.model,
                args.style,
                skip_done=not args.no_skip_done,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, f"{exc}\n")
