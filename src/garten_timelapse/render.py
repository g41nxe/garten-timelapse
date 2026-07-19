"""Ausgabe des Zeitraffers via imageio; Format über die Dateiendung (ADR 0001).

STUB — noch nicht implementiert (per TDD). Zwei getrennte Verantwortlichkeiten:
`prepare_frame` (Skalierung + Zeitstempel-Einblendung mit Pillow, format-unabhängig)
und `write` (imageio, .mp4/.gif/.webm anhand der Endung).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image

from .config import RenderConfig


def prepare_frame(image: np.ndarray, timestamp: datetime | None, cfg: RenderConfig) -> np.ndarray:
    """Skaliert auf cfg.width (kein Upscale) und blendet (falls cfg.caption) den Zeitstempel ein."""
    img = Image.fromarray(image)
    if img.width > cfg.width:
        height = round(img.height * cfg.width / img.width)
        img = img.resize((cfg.width, height), Image.LANCZOS)
    # Zeitstempel-Einblendung: Slice 2.
    return np.asarray(img)


def write(frames: list[np.ndarray], out: Path, fps: int, colors: int = 128) -> None:
    """Schreibt die Frames als Zeitraffer. Format ergibt sich aus out.suffix.

    .mp4 -> H.264, .webm -> VP9 (beide via imageio-ffmpeg), .gif -> Palette (colors).
    """
    out = Path(out)
    stack = np.stack(frames)
    if out.suffix.lower() == ".gif":
        iio.imwrite(out, stack, duration=1000 / fps, loop=0)
    else:
        # H.264/VP9 brauchen gerade Kantenlängen; sonst padded imageio auf Vielfache von 16
        # (Warnung + schwarzer Rand). Auf gerade Maße zuschneiden und Padding abschalten.
        h, w = stack.shape[1:3]
        stack = stack[:, : h - h % 2, : w - w % 2]
        iio.imwrite(out, stack, fps=fps, macro_block_size=1)
