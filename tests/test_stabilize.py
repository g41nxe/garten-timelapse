"""Tests für die Stabilisierung (Slice 3: reference + euclidean).

Kein echtes Bildmaterial nötig: eine synthetische Szene mit klaren Kanten (Rechtecken)
liefert ORB genug Features; nach bekannter Verschiebung muss die Ausrichtung sie zurückholen.
"""
import cv2
import numpy as np

from garten_timelapse.config import StabilizeConfig
from garten_timelapse.stabilize import crop_series, stabilize_series


def _shift(img, dx, dy):
    return cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, dy]]), (img.shape[1], img.shape[0]))


def _scene(h=240, w=320, seed=1):
    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), 40, dtype=np.uint8)
    for _ in range(50):
        x, y = int(rng.integers(0, w - 40)), int(rng.integers(0, h - 40))
        ww, hh = int(rng.integers(12, 40)), int(rng.integers(12, 40))
        color = tuple(int(c) for c in rng.integers(70, 255, 3))
        img[y : y + hh, x : x + ww] = color
    return img


def test_reference_mode_recovers_known_shift():
    ref = _scene()
    dx, dy = 14, -9
    shifted = cv2.warpAffine(ref, np.float32([[1, 0, dx], [0, 1, dy]]), (ref.shape[1], ref.shape[0]))

    out, report = stabilize_series(
        [ref, shifted], StabilizeConfig(mode="reference", transform="euclidean")
    )

    assert report.failed_indices == []           # beide Frames ausgerichtet
    center = (slice(30, 210), slice(40, 280))     # ohne Warp-Ränder
    diff = np.abs(out[1][center].astype(int) - ref[center].astype(int)).mean()
    assert diff < 12, f"Restversatz nach Stabilisierung zu groß: {diff}"


def test_first_frame_is_unchanged_reference():
    ref = _scene(seed=2)
    out, _ = stabilize_series([ref], StabilizeConfig(mode="reference", transform="euclidean"))
    assert np.array_equal(out[0], ref)


def test_crop_removes_black_borders_within_max_zoom():
    ref = _scene()
    cfg = StabilizeConfig(transform="euclidean", fill="black", max_zoom=1.5)
    frames, report = stabilize_series([ref, _shift(ref, 14, -9)], cfg)

    cropped = crop_series(frames, report, cfg)

    assert cropped[0].shape[0] < ref.shape[0]     # es wurde zugeschnitten (reingezoomt)
    assert report.crop_zoom > 1.0
    assert not report.crop_clamped
    assert cropped[1].min() > 0                    # keine schwarzen Rand-Pixel mehr (Hintergrund=40)


def test_crop_clamps_at_max_zoom_for_large_shift():
    ref = _scene()
    cfg = StabilizeConfig(transform="euclidean", fill="black", max_zoom=1.2)
    frames, report = stabilize_series([ref, _shift(ref, 80, 60)], cfg)   # großer Sprung

    crop_series(frames, report, cfg)

    assert report.crop_clamped
    assert abs(report.crop_zoom - 1.2) < 1e-6      # auf max_zoom geklemmt


def test_min_inliers_gate_marks_frame_failed():
    ref = _scene()
    shifted = _shift(ref, 14, -9)
    frames, report = stabilize_series([ref, shifted], StabilizeConfig(min_inliers=100000, retries=0))

    assert report.failed_indices == [1]
    assert np.array_equal(frames[1], shifted)      # unerreichbare Schwelle -> Identität


def test_retry_recovers_far_frame_via_neighbor():
    ref = _scene(w=340)
    frames = [ref, _shift(ref, 110, 0), _shift(ref, 210, 0)]   # far scheitert an ref (40<50), nicht an mid (66)
    cfg = StabilizeConfig(transform="euclidean", min_inliers=50, retries=3)

    _, report = stabilize_series(frames, cfg)

    assert report.failed_indices == []             # far über mid gekettet
    assert report.transforms[2] is not None


def test_without_retry_far_frame_fails():
    ref = _scene(w=340)
    frames = [ref, _shift(ref, 110, 0), _shift(ref, 210, 0)]
    cfg = StabilizeConfig(transform="euclidean", min_inliers=50, retries=0)

    _, report = stabilize_series(frames, cfg)

    assert report.failed_indices == [2]            # ohne Retry scheitert far an der Referenz
