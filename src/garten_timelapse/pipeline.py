"""Orchestrierung: laden -> (stabilisieren) -> rendern, plus Warnungen & Summary.

Bindet die reinen Bausteine (loader/stabilize/render) zusammen und übernimmt die
Nutzer-Rückmeldung: Warnung pro unstabilisiert gebliebenem Frame, Warnung beim
geklemmten Zuschnitt, und eine Lauf-Zusammenfassung am Ende (ADR 0001).

STUB — das Laden/Rendern ruft noch nicht implementierte Bausteine; die Struktur
zeigt den Ablauf.
"""
from __future__ import annotations

import logging

import imageio.v3 as iio

from . import loader, render
from .config import Config

logger = logging.getLogger("garten_timelapse")


def run(cfg: Config) -> int:
    """Führt einen kompletten Lauf aus. Rückgabe: Exit-Code (0 = ok)."""
    photos = loader.find_photos(cfg.src)
    if not photos:
        logger.error("Keine photo_*.jpg unter %s", cfg.src)
        return 1
    logger.info("%d Bilder gefunden.", len(photos))

    # Slice 3 hängt hier die Stabilisierung (stabilize.stabilize_series) vor prepare ein.
    frames = [
        render.prepare_frame(iio.imread(p), loader.parse_timestamp(p), cfg.render)
        for p in photos
    ]

    render.write(frames, cfg.out, cfg.fps, cfg.render.colors)
    logger.info("Zeitraffer geschrieben: %s (%d Frames)", cfg.out, len(frames))
    return 0
