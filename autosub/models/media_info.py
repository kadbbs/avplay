from dataclasses import dataclass


@dataclass(slots=True)
class MediaInfo:
    path: str
    duration: float
    width: int
    height: int
    video_codec: str
    audio_codec: str | None
    has_audio: bool
    has_subtitle: bool
