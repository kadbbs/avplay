from __future__ import annotations

from pathlib import Path

from autosub.constants import VIDEO_EXTENSIONS


def scan_videos(directory: str | Path, recursive: bool = False) -> list[Path]:
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"处理失败：目录不存在。\n目录：{root}")
    pattern = "**/*" if recursive else "*"
    return sorted(
        p for p in root.glob(pattern)
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )
