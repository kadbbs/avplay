from dataclasses import dataclass


@dataclass(slots=True)
class SubtitleSegment:
    index: int
    start: float
    end: float
    text: str
