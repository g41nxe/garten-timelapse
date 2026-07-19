"""Frame-Ausrichtung per OpenCV ORB + RANSAC, Warp und Zuschnitt (ADR 0001).

STUB — noch nicht implementiert (per TDD zu füllen). Die Schnittstelle ist bewusst
rein: Eingang sind numpy-Bildarrays, Ausgang die stabilisierten Arrays plus ein
Bericht (welche Frames scheiterten, welcher Zuschnitt angewandt wurde). So testbar
mit synthetisch verschobenen Bildern, ohne echtes Material.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .config import StabilizeConfig


@dataclass
class StabilizeReport:
    aligned: int = 0
    failed_indices: list[int] = field(default_factory=list)  # unstabilisiert gebliebene Frames
    crop_zoom: float = 1.0                                    # angewandter Zuschnitt-Faktor
    crop_clamped: bool = False                               # am max_zoom-Deckel geklemmt?


def estimate_transform(src_gray: np.ndarray, ref_gray: np.ndarray, transform: str):
    """Schätzt die Transform (src -> ref) per ORB-Matching + RANSAC.

    Rückgabe: (matrix, inliers) oder (None, 0) wenn zu wenige Matches.
    """
    raise NotImplementedError("estimate_transform: per TDD implementieren")


def stabilize_series(frames: list[np.ndarray], cfg: StabilizeConfig) -> tuple[list[np.ndarray], StabilizeReport]:
    """Richtet die ganze Serie aus und schneidet sie zu.

    Modus (reference/sequential), Transform-Modell, Retry/Identitäts-Fallback und
    Zuschnitt-Deckel (max_zoom, fill) kommen aus `cfg`. Liefert die stabilisierten
    Frames und einen StabilizeReport (für Warnungen/Summary im pipeline-Modul).
    """
    raise NotImplementedError("stabilize_series: per TDD implementieren")
