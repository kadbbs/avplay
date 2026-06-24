from __future__ import annotations

import re

from autosub.models.subtitle_segment import SubtitleSegment


DEFAULT_FILLER_WORDS = ["嗯", "啊", "呃", "额", "就是", "然后然后"]


def wrap_subtitle_text(text: str, max_chars_per_line: int = 18, max_lines: int = 2) -> str:
    clean = " ".join(text.strip().split())
    if len(clean) <= max_chars_per_line:
        return clean

    break_chars = "，。！？；、,.!?; "
    lines: list[str] = []
    rest = clean

    while rest and len(lines) < max_lines:
        if len(rest) <= max_chars_per_line:
            lines.append(rest)
            break

        window = rest[: max_chars_per_line + 1]
        cut = max(window.rfind(ch) for ch in break_chars)
        if cut <= 0:
            cut = max_chars_per_line
        line = rest[:cut].strip()
        if line:
            lines.append(line)
        rest = rest[cut:].strip()

    if rest and lines:
        lines[-1] = f"{lines[-1]}{rest}"

    return "\n".join(lines[:max_lines])


def apply_offset(segments: list[SubtitleSegment], offset: float) -> list[SubtitleSegment]:
    shifted: list[SubtitleSegment] = []
    for i, seg in enumerate(segments, start=1):
        start = max(0.0, seg.start + offset)
        end = max(start + 0.01, seg.end + offset)
        shifted.append(SubtitleSegment(i, start, end, seg.text))
    return shifted


def ensure_min_duration(
    segments: list[SubtitleSegment],
    min_duration: float = 1.0,
) -> list[SubtitleSegment]:
    fixed: list[SubtitleSegment] = []
    for i, seg in enumerate(segments):
        next_start = segments[i + 1].start if i + 1 < len(segments) else None
        end = max(seg.end, seg.start + min_duration)
        if next_start is not None:
            end = min(end, max(seg.start + 0.01, next_start - 0.05))
        fixed.append(SubtitleSegment(seg.index, seg.start, end, seg.text))
    return fixed


def remove_filler_words(text: str, filler_words: list[str] | None = None) -> str:
    result = text
    for word in filler_words or DEFAULT_FILLER_WORDS:
        result = result.replace(word, "")
    return " ".join(result.split()).strip()


def normalize_punctuation(text: str, language: str = "auto") -> str:
    result = text.strip()
    result = re.sub(r"[!?！？]{2,}", "！" if language == "zh" else "!", result)
    result = re.sub(r"[.。]{2,}", "。" if language == "zh" else ".", result)
    result = re.sub(r"\s+([，。！？；：,.!?;:])", r"\1", result)
    if language == "zh":
        result = result.replace(",", "，").replace("?", "？").replace(";", "；")
    return result


def clean_segments(
    segments: list[SubtitleSegment],
    language: str = "auto",
    offset: float = 0.0,
    remove_fillers: bool = False,
    wrap: bool = True,
) -> list[SubtitleSegment]:
    cleaned: list[SubtitleSegment] = []
    for i, seg in enumerate(segments, start=1):
        text = normalize_punctuation(seg.text, language)
        if remove_fillers:
            text = remove_filler_words(text)
        if wrap:
            text = wrap_subtitle_text(text, 18 if language == "zh" else 42)
        if text:
            cleaned.append(SubtitleSegment(i, seg.start, seg.end, text))

    cleaned = apply_offset(cleaned, offset) if offset else cleaned
    cleaned = ensure_min_duration(cleaned)
    return [SubtitleSegment(i, seg.start, seg.end, seg.text) for i, seg in enumerate(cleaned, start=1)]
