from __future__ import annotations

import json
from pathlib import Path

from autosub.models.subtitle_style import SubtitleStyle


PRESET_DIR = Path(__file__).with_name("presets")


def load_style(name: str) -> SubtitleStyle:
    path = PRESET_DIR / f"{name}.json"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in PRESET_DIR.glob("*.json")))
        raise FileNotFoundError(f"字幕样式不存在：{name}。可用样式：{available}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return SubtitleStyle(**data)
