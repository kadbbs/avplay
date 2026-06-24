from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autosub.models.task import SubtitleTask
from autosub.services.file_service import scan_videos
from autosub.services.pipeline import run_pipeline


def run_batch(
    directory: str | Path,
    output_dir: str | Path = "output",
    recursive: bool = False,
    language: str = "auto",
    model: str = "small",
    style_name: str = "classic",
    skip_done: bool = True,
) -> dict[str, Any]:
    videos = scan_videos(directory, recursive)
    items: list[dict[str, Any]] = []
    success = failed = skipped = 0

    for video in videos:
        task_dir = Path(output_dir) / video.stem
        expected = task_dir / f"{video.stem}_subtitled.mp4"
        if skip_done and expected.exists():
            skipped += 1
            items.append({"input": str(video), "status": "skipped", "output": str(expected)})
            continue

        task = SubtitleTask(
            input_path=str(video),
            output_dir=str(output_dir),
            language=language,
            model=model,
            subtitle_format="srt",
            style_name=style_name,
            burn_subtitle=True,
            soft_subtitle=False,
        )
        try:
            report = run_pipeline(task)
            success += 1
            items.append({"input": str(video), "status": "success", "output": report["outputs"].get("video")})
        except Exception as exc:
            failed += 1
            items.append({"input": str(video), "status": "failed", "reason": str(exc)})

    batch_report = {
        "total": len(videos),
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "items": items,
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "batch_report.json").write_text(
        json.dumps(batch_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return batch_report
