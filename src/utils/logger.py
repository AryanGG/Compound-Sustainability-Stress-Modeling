"""
src/utils/logger.py
────────────────────
Centralised Loguru logger factory for the SSI pipeline.

Usage:
    from src.utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Starting ERA5 ingestion for {city}", city="mumbai")
"""

import sys
from pathlib import Path
from loguru import logger

from src.utils.config_loader import load_config


def _ensure_stdout_utf8() -> None:
    """
    Attempt to reconfigure sys.stdout to UTF-8 (Windows cp1252 fix).

    Only acts on the real stdout (has a .buffer attribute), not on pytest's
    StringIO capture. On non-Windows or already-UTF-8 streams this is a no-op.
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # Silently ignore — e.g. when pytest already closed the file


def get_logger(name: str = "ssi_pipeline") -> "logger":
    """
    Return a Loguru logger pre-configured from config.yml.

    Args:
        name: Module name displayed in log records (pass __name__).

    Returns:
        Configured loguru logger instance.
    """
    _ensure_stdout_utf8()

    config = load_config()
    log_cfg = config.get("logging", {})
    level = log_cfg.get("level", "INFO")
    fmt = log_cfg.get(
        "format",
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[name]} | {message}",
    )

    log_dir = Path(config["paths"].get("logs", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove any existing handlers so multiple imports don't duplicate
    logger.remove()

    # Console handler — write directly to sys.stdout; stdout is now UTF-8 if possible
    logger.add(
        sys.stdout,
        format=fmt,
        level=level,
        colorize=False,   # colorize=False avoids ANSI passthrough issues on Windows
        enqueue=False,    # synchronous for pytest compatibility
    )

    # Rotating file handler (10 MB, keep 7 days) — always UTF-8
    logger.add(
        log_dir / "pipeline.log",
        format=fmt,
        level=level,
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
    )

    return logger.bind(name=name)
