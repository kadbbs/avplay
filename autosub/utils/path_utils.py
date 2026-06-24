from __future__ import annotations

from pathlib import Path


def task_output_dir(input_path: str | Path, output_dir: str | Path) -> Path:
    path = Path(input_path)
    return Path(output_dir) / path.stem


def ensure_dir(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output
