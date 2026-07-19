"""Ausgabe des Zeitraffers via imageio; Format über die Dateiendung (ADR 0001).

STUB — noch nicht implementiert (per TDD). Zwei getrennte Verantwortlichkeiten:
`prepare_frame` (Skalierung + Zeitstempel-Einblendung mit Pillow, format-unabhängig)
und `write` (imageio, .mp4/.gif/.webm anhand der Endung).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from .config import RenderConfig


def prepare_frame(image: np.ndarray, timestamp: datetime | None, cfg: RenderConfig) -> np.ndarray:
    """Skaliert auf cfg.width und blendet (falls cfg.caption) den Zeitstempel ein."""
    raise NotImplementedError("prepare_frame: per TDD implementieren")


def write(frames: list[np.ndarray], out: Path, fps: int, colors: int = 128) -> None:
    """Schreibt die Frames als Zeitraffer. Format ergibt sich aus out.suffix.

    .mp4 -> H.264, .webm -> VP9 (beide via imageio-ffmpeg), .gif -> Palette (colors).
    """
    raise NotImplementedError("write: per TDD implementieren")
