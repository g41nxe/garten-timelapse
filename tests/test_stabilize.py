"""Tests für die Stabilisierung (Slice 3: reference + euclidean).

Kein echtes Bildmaterial nötig: eine synthetische Szene mit klaren Kanten (Rechtecken)
liefert ORB genug Features; nach bekannter Verschiebung muss die Ausrichtung sie zurückholen.
"""
import cv2
import numpy as np

from garten_timelapse.config import StabilizeConfig
from garten_timelapse.stabilize import stabilize_series


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
