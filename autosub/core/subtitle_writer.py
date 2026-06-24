from __future__ import annotations

from pathlib import Path

from autosub.models.subtitle_segment import SubtitleSegment
from autosub.models.subtitle_style import SubtitleStyle


def format_srt_time(seconds: float) -> str:
    ms_total = max(0, round(seconds * 1000))
    hours, rem = divmod(ms_total, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_vtt_time(seconds: float) -> str:
    return format_srt_time(seconds).replace(",", ".")


def format_ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, rem = divmod(centiseconds, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def write_srt(segments: list[SubtitleSegment], output_path: str | Path) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fp:
        for i, seg in enumerate(segments, start=1):
            fp.write(f"{i}\n")
            fp.write(f"{format_srt_time(seg.start)} --> {format_srt_time(seg.end)}\n")
            fp.write(f"{seg.text.strip()}\n\n")
    return str(output)


def write_vtt(segments: list[SubtitleSegment], output_path: str | Path) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fp:
        fp.write("WEBVTT\n\n")
        for seg in segments:
            fp.write(f"{format_vtt_time(seg.start)} --> {format_vtt_time(seg.end)}\n")
            fp.write(f"{seg.text.strip()}\n\n")
    return str(output)


def _escape_ass_text(text: str) -> str:
    return text.replace("\n", r"\N").replace("{", r"\{").replace("}", r"\}")


def write_ass(
    segments: list[SubtitleSegment],
    output_path: str | Path,
    style: SubtitleStyle,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fp:
        fp.write("[Script Info]\n")
        fp.write("Title: AutoSub Studio\n")
        fp.write("ScriptType: v4.00+\n\n")
        fp.write("[V4+ Styles]\n")
        fp.write(
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        )
        fp.write(
            f"Style: Default,{style.font_name},{style.font_size},{style.primary_color},"
            f"{style.outline_color},1,{style.outline},{style.shadow},{style.alignment},"
            f"10,10,{style.margin_v},1\n\n"
        )
        fp.write("[Events]\n")
        fp.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for seg in segments:
            fp.write(
                f"Dialogue: 0,{format_ass_time(seg.start)},{format_ass_time(seg.end)},"
                f"Default,,0,0,0,,{_escape_ass_text(seg.text.strip())}\n"
            )
    return str(output)
