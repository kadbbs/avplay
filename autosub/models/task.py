from dataclasses import dataclass


@dataclass(slots=True)
class SubtitleTask:
    input_path: str
    output_dir: str
    language: str
    model: str
    subtitle_format: str
    style_name: str
    burn_subtitle: bool
    soft_subtitle: bool
    status: str = "PENDING"
    offset: float = 0.0
    crf: int = 20
    preset: str = "medium"
