from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from autosub.config import load_style
from autosub.constants import (
    TASK_DONE,
    TASK_EXPORTING_SUBTITLE,
    TASK_EXTRACTING_AUDIO,
    TASK_FAILED,
    TASK_POST_PROCESSING,
    TASK_PROBING,
    TASK_RENDERING,
    TASK_TRANSCRIBING,
)
from autosub.core.audio_extractor import extract_audio
from autosub.core.ffprobe import probe_media
from autosub.core.subtitle_burner import burn_subtitle
from autosub.core.subtitle_cleaner import clean_segments
from autosub.core.subtitle_muxer import mux_soft_subtitle
from autosub.core.subtitle_writer import write_ass, write_srt, write_vtt
from autosub.core.transcriber import transcribe_audio
from autosub.models.task import SubtitleTask
from autosub.services.report_service import write_report
from autosub.utils.logger import setup_logger
from autosub.utils.path_utils import task_output_dir


def _elapsed(start: float) -> float:
    return round(time.perf_counter() - start, 3)


def run_pipeline(task: SubtitleTask) -> dict[str, Any]:
    logger = setup_logger()
    total_start = time.perf_counter()
    timings: dict[str, float] = {}
    outputs: dict[str, str] = {}
    work_dir = task_output_dir(task.input_path, task.output_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(task.input_path).stem
    report_path = work_dir / "report.json"

    report: dict[str, Any] = {
        "input_path": task.input_path,
        "output_dir": str(work_dir),
        "status": "running",
        "stage": task.status,
    }

    try:
        logger.info("Start task: %s", task.input_path)

        task.status = TASK_PROBING
        started = time.perf_counter()
        media = probe_media(task.input_path)
        timings["probe"] = _elapsed(started)
        logger.info("Probe media success: duration=%s", media.duration)

        task.status = TASK_EXTRACTING_AUDIO
        started = time.perf_counter()
        audio_path = work_dir / "audio.wav"
        extract_audio(task.input_path, audio_path)
        outputs["audio"] = str(audio_path)
        timings["extract_audio"] = _elapsed(started)

        task.status = TASK_TRANSCRIBING
        started = time.perf_counter()
        raw_segments = transcribe_audio(audio_path, task.model, task.language)
        timings["transcribe"] = _elapsed(started)

        raw_srt = work_dir / f"{stem}.raw.srt"
        write_srt(raw_segments, raw_srt)
        outputs["raw_srt"] = str(raw_srt)

        task.status = TASK_POST_PROCESSING
        started = time.perf_counter()
        cleaned = clean_segments(raw_segments, task.language, task.offset)
        timings["post_process"] = _elapsed(started)

        task.status = TASK_EXPORTING_SUBTITLE
        started = time.perf_counter()
        cleaned_srt = work_dir / f"{stem}.cleaned.srt"
        write_srt(cleaned, cleaned_srt)
        outputs["srt"] = str(cleaned_srt)

        if task.subtitle_format in {"vtt", "all"}:
            vtt = work_dir / f"{stem}.vtt"
            write_vtt(cleaned, vtt)
            outputs["vtt"] = str(vtt)

        style = load_style(task.style_name)
        ass = work_dir / f"{stem}.ass"
        write_ass(cleaned, ass, style)
        outputs["ass"] = str(ass)
        timings["export_subtitle"] = _elapsed(started)

        if task.burn_subtitle:
            task.status = TASK_RENDERING
            started = time.perf_counter()
            video_output = work_dir / f"{stem}_subtitled.mp4"
            burn_subtitle(task.input_path, ass, video_output, task.crf, task.preset, media.duration)
            outputs["video"] = str(video_output)
            timings["render"] = _elapsed(started)

        if task.soft_subtitle:
            started = time.perf_counter()
            soft_output = work_dir / f"{stem}_softsub.mp4"
            mux_soft_subtitle(task.input_path, cleaned_srt, soft_output)
            outputs["soft_video"] = str(soft_output)
            timings["mux"] = _elapsed(started)

        task.status = TASK_DONE
        report.update(
            {
                "status": "success",
                "stage": task.status,
                "duration": media.duration,
                "media": {
                    "width": media.width,
                    "height": media.height,
                    "video_codec": media.video_codec,
                    "audio_codec": media.audio_codec,
                },
                "subtitle": {
                    "segments": len(cleaned),
                    "language": task.language,
                    "format": ["srt", "ass"] + (["vtt"] if "vtt" in outputs else []),
                    "style": task.style_name,
                },
                "outputs": outputs,
                "time_cost": {**timings, "total": _elapsed(total_start)},
            }
        )
        logger.info("Task done")
    except Exception as exc:
        task.status = TASK_FAILED
        logger.error("Task failed: %s", task.input_path)
        logger.error("Stage: %s", report.get("stage", task.status))
        logger.error("Reason: %s", exc)
        report.update(
            {
                "status": "failed",
                "stage": task.status,
                "reason": str(exc),
                "outputs": outputs,
                "time_cost": {**timings, "total": _elapsed(total_start)},
            }
        )
        write_report(report, report_path)
        raise

    write_report(report, report_path)
    return report
