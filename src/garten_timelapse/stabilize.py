"""Frame-Ausrichtung per OpenCV ORB + RANSAC, Warp und Zuschnitt (ADR 0001).

STUB — noch nicht implementiert (per TDD zu füllen). Die Schnittstelle ist bewusst
rein: Eingang sind numpy-Bildarrays, Ausgang die stabilisierten Arrays plus ein
Bericht (welche Frames scheiterten, welcher Zuschnitt angewandt wurde). So testbar
mit synthetisch verschobenen Bildern, ohne echtes Material.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .config import StabilizeConfig


@dataclass
class StabilizeReport:
    aligned: int = 0
    failed_indices: list[int] = field(default_factory=list)  # unstabilisiert gebliebene Frames
    transforms: list = field(default_factory=list)           # Transform je Frame (None = Identität)
    crop_zoom: float = 1.0                                    # angewandter Zuschnitt-Faktor
    crop_clamped: bool = False                               # am max_zoom-Deckel geklemmt?


def _to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def estimate_transform(src_gray: np.ndarray, ref_gray: np.ndarray, transform: str):
    """Schätzt die Transform (src -> ref) per ORB-Matching + RANSAC.

    Rückgabe: (matrix, inliers) oder (None, 0) wenn zu wenige/schlechte Matches.
    """
    orb = cv2.ORB_create(2000)
    k1, d1 = orb.detectAndCompute(src_gray, None)
    k2, d2 = orb.detectAndCompute(ref_gray, None)
    if d1 is None or d2 is None or len(k1) < 4 or len(k2) < 4:
        return None, 0

    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d1, d2)
    if len(matches) < 4:
        return None, 0
    src_pts = np.float32([k1[m.queryIdx].pt for m in matches])
    dst_pts = np.float32([k2[m.trainIdx].pt for m in matches])

    if transform == "homography":
        M, inliers = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
    elif transform == "affine":
        M, inliers = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC)
    else:  # euclidean (Translation + Rotation + einheitliche Skalierung)
        M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC)

    if M is None:
        return None, 0
    return M, int(inliers.sum()) if inliers is not None else 0


def _warp(img: np.ndarray, M: np.ndarray, transform: str, border: int = cv2.BORDER_CONSTANT) -> np.ndarray:
    h, w = img.shape[:2]
    if transform == "homography":
        return cv2.warpPerspective(img, M, (w, h), borderMode=border)
    return cv2.warpAffine(img, M, (w, h), borderMode=border)


def stabilize_series(frames: list[np.ndarray], cfg: StabilizeConfig) -> tuple[list[np.ndarray], StabilizeReport]:
    """Richtet die Serie im reference-Modus aus (jedes Frame -> erstes Frame).

    Größen-erhaltend: den Zuschnitt macht crop_series (mit den hier gesammelten
    Transforms). Fehlschlag -> Identität (Frame bleibt drin, Index im Report).
    Retry/min_inliers (Slice 5) und sequential (Slice 6) folgen.
    """
    report = StabilizeReport()
    if not frames:
        return [], report

    border = cv2.BORDER_REPLICATE if cfg.fill == "replicate" else cv2.BORDER_CONSTANT
    ref_gray = _to_gray(frames[0])
    out = [frames[0]]
    report.transforms = [None]   # Referenz = Identität
    report.aligned = 1
    for i in range(1, len(frames)):
        M, _inliers = estimate_transform(_to_gray(frames[i]), ref_gray, cfg.transform)
        report.transforms.append(M)
        if M is None:
            out.append(frames[i])
            report.failed_indices.append(i)
        else:
            out.append(_warp(frames[i], M, cfg.transform, border))
            report.aligned += 1
    return out, report


def _largest_centered_scale(valid: np.ndarray) -> float:
    """Größter Skalenfaktor s in (0,1], für den das zentrale s-Rechteck komplett gültig ist."""
    h, w = valid.shape
    cy, cx = h / 2, w / 2

    def ok(s: float) -> bool:
        y0, y1 = round(cy - s * h / 2), round(cy + s * h / 2)
        x0, x1 = round(cx - s * w / 2), round(cx + s * w / 2)
        return bool(valid[y0:y1, x0:x1].all())

    if ok(1.0):
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if ok(mid):
            lo = mid
        else:
            hi = mid
    return lo


def crop_series(frames: list[np.ndarray], report: StabilizeReport, cfg: StabilizeConfig) -> list[np.ndarray]:
    """Schneidet alle Frames auf das größte gemeinsame gültige Rechteck, gedeckelt bei max_zoom.

    Setzt report.crop_zoom / crop_clamped. Bei Überschreitung des Deckels bleibt ein
    Rest-Rand — dessen Aussehen (schwarz oder Kanten-Fortsetzung) hat bereits der
    Warp-Schritt über cfg.fill bestimmt.
    """
    if not frames:
        return frames

    h, w = frames[0].shape[:2]
    valid = np.ones((h, w), dtype=bool)
    for M in report.transforms:
        if M is None:   # Identität -> überall gültig
            continue
        mask = _warp(np.full((h, w), 255, np.uint8), M, cfg.transform, cv2.BORDER_CONSTANT)
        valid &= mask == 255   # nur voll abgedeckte Pixel zählen als gültig

    s_needed = _largest_centered_scale(valid)
    s_floor = 1.0 / cfg.max_zoom
    s_used = max(s_needed, s_floor)
    report.crop_zoom = 1.0 / s_used
    report.crop_clamped = s_needed < s_floor - 1e-9

    cy, cx = h / 2, w / 2
    y0, y1 = round(cy - s_used * h / 2), round(cy + s_used * h / 2)
    x0, x1 = round(cx - s_used * w / 2), round(cx + s_used * w / 2)
    return [f[y0:y1, x0:x1] for f in frames]
