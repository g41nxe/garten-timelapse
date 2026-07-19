"""End-to-end-Test der Pipeline (Slice 1: Passthrough)."""
import imageio.v3 as iio
import numpy as np

from garten_timelapse.config import Config
from garten_timelapse.pipeline import run


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
