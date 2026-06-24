from dataclasses import dataclass


@dataclass(slots=True)
class SubtitleStyle:
    name: str
    font_name: str
    font_size: int
    primary_color: str
    outline_color: str
    outline: int
    shadow: int
    alignment: int
    margin_v: int
