"""Frame-Ausrichtung per OpenCV ORB + RANSAC, Warp und Zuschnitt (ADR 0001).

Reine Schnittstelle: Eingang sind numpy-Bildarrays, Ausgang die stabilisierten Arrays
plus ein Bericht (welche Frames scheiterten, welcher Zuschnitt angewandt wurde). So
testbar mit synthetisch verschobenen Bildern, ohne echtes Material.
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


def _detect(gray: np.ndarray):
    """ORB-Keypoints + Deskriptoren für ein Graustufenbild."""
    return cv2.ORB_create(2000).detectAndCompute(gray, None)


def _match(feat_src, feat_ref, transform: str):
    """Schätzt die Transform (src -> ref) aus vorberechneten Features + RANSAC."""
    (k1, d1), (k2, d2) = feat_src, feat_ref
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


def estimate_transform(src_gray: np.ndarray, ref_gray: np.ndarray, transform: str):
    """Schätzt die Transform (src -> ref) per ORB-Matching + RANSAC.

    Rückgabe: (matrix, inliers) oder (None, 0) wenn zu wenige/schlechte Matches.
    """
    return _match(_detect(src_gray), _detect(ref_gray), transform)


def _warp(img: np.ndarray, M: np.ndarray, transform: str, border: int = cv2.BORDER_CONSTANT) -> np.ndarray:
    h, w = img.shape[:2]
    if transform == "homography":
        return cv2.warpPerspective(img, M, (w, h), borderMode=border)
    return cv2.warpAffine(img, M, (w, h), borderMode=border)


def _compose(a2r: np.ndarray, i2a: np.ndarray, transform: str) -> np.ndarray:
    """Verkettet: frame_i -> ref = (anchor -> ref) ∘ (frame_i -> anchor)."""
    if transform == "homography":
        return a2r @ i2a

    def _to3(M):
        return np.vstack([M, [0.0, 0.0, 1.0]])

    return (_to3(a2r) @ _to3(i2a))[:2]


def stabilize_series(frames: list[np.ndarray], cfg: StabilizeConfig) -> tuple[list[np.ndarray], StabilizeReport]:
    """Richtet die Serie im reference-Modus aus (jedes Frame -> erstes Frame).

    Eine Ausrichtung gilt erst ab `min_inliers` als vertrauenswürdig. Scheitert sie an
    der Referenz, wird sie gegen die nächstgelegenen bereits gut ausgerichteten Frames
    versucht (bis `retries`) und über deren bekannte Transform verkettet; sonst bleibt
    das Frame unverändert (Identität, Index im Report). Größen-erhaltend — den Zuschnitt
    macht crop_series.
    """
    report = StabilizeReport()
    if not frames:
        return [], report

    border = cv2.BORDER_REPLICATE if cfg.fill == "replicate" else cv2.BORDER_CONSTANT
    feats = [_detect(_to_gray(f)) for f in frames]   # Features einmal pro Frame (F2)
    out = [frames[0]]
    report.transforms = [None]   # Referenz = Identität
    report.aligned = 1

    if cfg.mode == "sequential":
        prev_M, prev_i = None, 0   # (Vorgänger -> Referenz, Index des Vorgängers)
        for i in range(1, len(frames)):
            M_local, n = _match(feats[i], feats[prev_i], cfg.transform)
            if M_local is None or n < cfg.min_inliers:
                # Fehlschlag: Frame unverändert (Identität); Kette startet ab hier neu
                # (koordinaten-sauber statt gegen einen unpassenden Anker zu komponieren).
                report.transforms.append(None)
                report.failed_indices.append(i)
                out.append(frames[i])
                prev_M, prev_i = None, i
            else:
                M = M_local if prev_M is None else _compose(prev_M, M_local, cfg.transform)
                report.transforms.append(M)
                out.append(_warp(frames[i], M, cfg.transform, border))
                report.aligned += 1
                prev_M, prev_i = M, i
        return out, report

    for i in range(1, len(frames)):
        M, n = _match(feats[i], feats[0], cfg.transform)
        if M is None or n < cfg.min_inliers:
            M = None   # zu wenig Konfidenz -> verwerfen und über Nachbarn versuchen
            anchors = sorted(
                (j for j in range(1, i) if report.transforms[j] is not None),
                key=lambda j: abs(j - i),
            )[: cfg.retries]
            for j in anchors:
                M_ij, n_ij = _match(feats[i], feats[j], cfg.transform)
                if M_ij is not None and n_ij >= cfg.min_inliers:
                    M = _compose(report.transforms[j], M_ij, cfg.transform)
                    break

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
