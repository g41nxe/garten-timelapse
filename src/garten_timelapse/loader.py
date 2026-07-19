"""Bilderserie laden: Fotos finden und chronologisch nach Zeitstempel sortieren.

Der Zeitstempel kommt aus dem Dateinamen (photo_YYYYMMDD_HHMMSS.jpg), nicht aus der
Dateisystem-Reihenfolge — so bleibt die Serie über Ordner-/Kopiervorgänge hinweg stabil.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_TS_RE = re.compile(r"photo_(\d{8})_(\d{6})\.jpg$", re.IGNORECASE)


def parse_timestamp(path: Path) -> datetime | None:
    """Zeitstempel aus dem Dateinamen, oder None wenn das Muster nicht passt."""
    m = _TS_RE.search(path.name)
    if not m:
        return None
    return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")


def find_photos(src: str | Path) -> list[Path]:
    """Alle photo_*.jpg unter `src` (rekursiv), chronologisch sortiert.

    Dateien ohne parsbaren Zeitstempel (z. B. latest.jpg) werden übersprungen.
    """
    src = Path(src)
    dated = [(parse_timestamp(p), p) for p in src.rglob("photo_*.jpg")]
    return [p for ts, p in sorted((d for d in dated if d[0] is not None))]
