from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir: str | Path = "logs") -> logging.Logger:
    output = Path(log_dir)
    output.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autosub")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        path = output / f"autosub_{datetime.now().strftime('%Y-%m-%d')}.log"
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger
