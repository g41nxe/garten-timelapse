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


def _warp(img: np.ndarray, M: np.ndarray, transform: str) -> np.ndarray:
    h, w = img.shape[:2]
    if transform == "homography":
        return cv2.warpPerspective(img, M, (w, h))
    return cv2.warpAffine(img, M, (w, h))


def stabilize_series(frames: list[np.ndarray], cfg: StabilizeConfig) -> tuple[list[np.ndarray], StabilizeReport]:
    """Richtet die Serie im reference-Modus aus (jedes Frame -> erstes Frame).

    Slice 3: euclidean/affine/homography, Fehlschlag -> Identität (Frame bleibt drin,
    Index im Report). Retry/min_inliers (Slice 5), Zuschnitt (Slice 4) und sequential
    (Slice 6) folgen.
    """
    report = StabilizeReport()
    if not frames:
        return [], report

    ref_gray = _to_gray(frames[0])
    out = [frames[0]]
    report.aligned = 1
    for i in range(1, len(frames)):
        M, _inliers = estimate_transform(_to_gray(frames[i]), ref_gray, cfg.transform)
        if M is None:
            out.append(frames[i])
            report.failed_indices.append(i)
        else:
            out.append(_warp(frames[i], M, cfg.transform))
            report.aligned += 1
    return out, report
