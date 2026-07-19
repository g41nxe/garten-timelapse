"""Orchestrierung: laden -> (stabilisieren) -> rendern, plus Warnungen & Summary.

Bindet die reinen Bausteine (loader/stabilize/render) zusammen und übernimmt die
Nutzer-Rückmeldung: Warnung pro unstabilisiert gebliebenem Frame, Warnung beim
geklemmten Zuschnitt, und eine Lauf-Zusammenfassung am Ende (ADR 0001).

STUB — das Laden/Rendern ruft noch nicht implementierte Bausteine; die Struktur
zeigt den Ablauf.
"""
from __future__ import annotations

import logging
from dataclasses import replace

import imageio.v3 as iio

from . import loader, render, stabilize
from .config import Config

logger = logging.getLogger("garten_timelapse")


def run(cfg: Config) -> int:
    """Führt einen kompletten Lauf aus. Rückgabe: Exit-Code (0 = ok)."""
    photos = loader.find_photos(cfg.src)
    if not photos:
        logger.error("Keine photo_*.jpg unter %s", cfg.src)
        return 1
    logger.info("%d Bilder gefunden.", len(photos))

    timestamps = [loader.parse_timestamp(p) for p in photos]

    if cfg.stabilize.enabled:
        # Erst skalieren (schnell, Caption nicht mitverzerren), dann stabilisieren, dann Caption.
        no_caption = replace(cfg.render, caption=False)
        frames = [render.prepare_frame(iio.imread(p), None, no_caption) for p in photos]
        frames, report = stabilize.stabilize_series(frames, cfg.stabilize)
        frames = stabilize.crop_series(frames, report, cfg.stabilize)
        for idx in report.failed_indices:
            ts = timestamps[idx]
            label = ts.strftime("%d.%m.%Y %H:%M") if ts else photos[idx].name
            logger.warning("Frame nicht ausgerichtet, bleibt unverändert: %s", label)
        if report.crop_clamped:
            logger.warning(
                "Zuschnitt auf max_zoom=%.2f geklemmt (Versatz zu groß) — evtl. Segment-Modus erwägen.",
                cfg.stabilize.max_zoom,
            )
        logger.info(
            "Stabilisierung: %d/%d ausgerichtet, %d unverändert; Zuschnitt %.2fx",
            report.aligned, len(photos), len(report.failed_indices), report.crop_zoom,
        )
        frames = [render.prepare_frame(f, ts, cfg.render) for f, ts in zip(frames, timestamps)]
    else:
        frames = [
            render.prepare_frame(iio.imread(p), ts, cfg.render)
            for p, ts in zip(photos, timestamps)
        ]

    render.write(frames, cfg.out, cfg.fps, cfg.render.colors)
    logger.info("Zeitraffer geschrieben: %s (%d Frames)", cfg.out, len(frames))
    return 0
