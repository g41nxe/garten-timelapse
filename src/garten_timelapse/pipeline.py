"""Orchestrierung: laden -> (stabilisieren) -> rendern, plus Warnungen & Summary.

Bindet die reinen Bausteine (loader/stabilize/render) zusammen und übernimmt die
Nutzer-Rückmeldung: Warnung pro unstabilisiert gebliebenem Frame, Warnung beim
geklemmten Zuschnitt, und eine Lauf-Zusammenfassung am Ende (ADR 0001).

STUB — das Laden/Rendern ruft noch nicht implementierte Bausteine; die Struktur
zeigt den Ablauf.
"""
from __future__ import annotations

import logging

from . import loader
from .config import Config

logger = logging.getLogger("garten_timelapse")


def run(cfg: Config) -> int:
    """Führt einen kompletten Lauf aus. Rückgabe: Exit-Code (0 = ok)."""
    photos = loader.find_photos(cfg.src)
    if not photos:
        logger.error("Keine photo_*.jpg unter %s", cfg.src)
        return 1
    logger.info("%d Bilder gefunden.", len(photos))

    # TODO (TDD): Bilder laden -> stabilize.stabilize_series -> render.prepare_frame -> render.write
    #  - pro Eintrag in report.failed_indices eine Warnung mit Zeitstempel
    #  - bei report.crop_clamped eine Warnung (Sprung > max_zoom -> Segment-Modus erwägen)
    #  - Abschluss-Zusammenfassung (N ausgerichtet, M unverändert, Crop-Faktor)
    raise NotImplementedError("pipeline.run: Verarbeitung per TDD implementieren")
