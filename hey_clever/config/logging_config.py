"""Logging configuration for hey-clever."""

from __future__ import annotations

import logging


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    for name in ("httpcore", "httpx", "faster_whisper", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING if not debug else logging.DEBUG)
