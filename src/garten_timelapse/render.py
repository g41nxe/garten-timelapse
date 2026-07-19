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
from PIL import Image, ImageDraw, ImageFont

from .config import RenderConfig

_WEEKDAYS_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
# Schriftkandidaten: Windows (Arial Bold), Linux/Pi (DejaVu), sonst Pillow-Default.
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def format_caption(dt: datetime) -> str:
    """Zeitstempel als Einblendungstext, deutscher Wochentag ohne Locale-Abhängigkeit."""
    return f"{_WEEKDAYS_DE[dt.weekday()]} {dt:%d.%m.%Y %H:%M}"


def _load_font(size: int):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_caption(img: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(img)
    font = _load_font(max(14, img.width // 28))
    pad = max(6, img.width // 60)
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    y = img.height - th - 2 * pad
    draw.rectangle([0, y - pad, tw + 3 * pad, img.height], fill=(0, 0, 0))
    draw.text((pad + 1, y + 1), text, font=font, fill=(0, 0, 0))   # Schatten
    draw.text((pad, y), text, font=font, fill=(255, 255, 255))


def prepare_frame(image: np.ndarray, timestamp: datetime | None, cfg: RenderConfig) -> np.ndarray:
    """Skaliert auf cfg.width (kein Upscale) und blendet (falls cfg.caption) den Zeitstempel ein."""
    img = Image.fromarray(image)
    if img.width > cfg.width:
        height = round(img.height * cfg.width / img.width)
        img = img.resize((cfg.width, height), Image.LANCZOS)
    if cfg.caption and timestamp is not None:
        _draw_caption(img, format_caption(timestamp))
    return np.asarray(img)


def write(frames: list[np.ndarray], out: Path, fps: int, colors: int = 128) -> None:
    """Schreibt die Frames als Zeitraffer. Format ergibt sich aus out.suffix.

    .mp4 -> H.264, .webm -> VP9 (beide via imageio-ffmpeg), .gif -> Palette (colors).
    """
    out = Path(out)
    shapes = {f.shape for f in frames}
    if len(shapes) != 1:
        raise ValueError(
            f"Alle Frames müssen dieselbe Größe haben; gefunden: {sorted(shapes)}. "
            "Stammen die Bilder aus verschiedenen Auflösungen/Seitenverhältnissen?"
        )
    stack = np.stack(frames)
    if out.suffix.lower() == ".gif":
        iio.imwrite(out, stack, duration=1000 / fps, loop=0)
    else:
        # H.264/VP9 brauchen gerade Kantenlängen; sonst padded imageio auf Vielfache von 16
        # (Warnung + schwarzer Rand). Auf gerade Maße zuschneiden und Padding abschalten.
        h, w = stack.shape[1:3]
        stack = stack[:, : h - h % 2, : w - w % 2]
        iio.imwrite(out, stack, fps=fps, macro_block_size=1)
