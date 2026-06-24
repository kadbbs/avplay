from __future__ import annotations

from pathlib import Path


def ensure_file(path: str | Path, label: str = "文件") -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"处理失败：{label}不存在。\n文件：{p}")
    return p
