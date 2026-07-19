"""End-to-end-Test der Pipeline (Slice 1: Passthrough; Slice 3: Stabilisierung)."""
import cv2
import imageio.v3 as iio
import numpy as np

from garten_timelapse.config import Config
from garten_timelapse.pipeline import run


def _scene(h=120, w=160, seed=3):
    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), 40, dtype=np.uint8)
    for _ in range(30):
        x, y = int(rng.integers(0, w - 20)), int(rng.integers(0, h - 20))
        img[y : y + 15, x : x + 15] = tuple(int(c) for c in rng.integers(80, 255, 3))
    return img


def test_run_produces_video_from_folder(tmp_path):
    src = tmp_path / "imgs"
    src.mkdir()
    names = [
        "photo_20260629_060000.jpg",
        "photo_20260629_120000.jpg",
        "photo_20260629_180000.jpg",
    ]
    for i, name in enumerate(names):
        iio.imwrite(src / name, np.full((64, 96, 3), 30 + i * 80, dtype=np.uint8))

    out = tmp_path / "out.mp4"
    cfg = Config(src=src, out=out, fps=10)
    cfg.stabilize.enabled = False   # Slice 1: noch keine Stabilisierung

    assert run(cfg) == 0
    assert out.exists()
    assert iio.imread(out, index=None).shape[0] == 3


def test_run_with_stabilization_enabled(tmp_path):
    src = tmp_path / "imgs"
    src.mkdir()
    ref = _scene()
    shifted = cv2.warpAffine(ref, np.float32([[1, 0, 6], [0, 1, -4]]), (ref.shape[1], ref.shape[0]))
    iio.imwrite(src / "photo_20260629_060000.jpg", ref)
    iio.imwrite(src / "photo_20260629_120000.jpg", shifted)

    out = tmp_path / "stab.mp4"
    cfg = Config(src=src, out=out, fps=10)   # stabilize.enabled ist per Default True

    assert run(cfg) == 0
    assert iio.imread(out, index=None).shape[0] == 2


def test_run_survives_all_frames_failing_alignment(tmp_path):
    src = tmp_path / "imgs"
    src.mkdir()
    ref = _scene()
    iio.imwrite(src / "photo_20260629_060000.jpg", ref)
    iio.imwrite(src / "photo_20260629_120000.jpg", cv2.warpAffine(
        ref, np.float32([[1, 0, 8], [0, 1, -4]]), (ref.shape[1], ref.shape[0])))

    out = tmp_path / "fail.mp4"
    cfg = Config(src=src, out=out, fps=10)
    cfg.stabilize.min_inliers = 10**9   # unerreichbar -> alle Frames bleiben Identität

    assert run(cfg) == 0
    assert iio.imread(out, index=None).shape[0] == 2
