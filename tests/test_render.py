"""Tests für die Ausgabe (Slice 1: Passthrough-MP4; Slice 2: Zeitstempel)."""
from datetime import datetime

import imageio.v3 as iio
import numpy as np

from garten_timelapse.config import RenderConfig
from garten_timelapse.render import format_caption, prepare_frame, write


def test_write_mp4_contains_all_frames(tmp_path):
    frames = [np.full((64, 96, 3), fill, dtype=np.uint8) for fill in (20, 130, 240)]
    out = tmp_path / "clip.mp4"

    write(frames, out, fps=10)

    assert out.exists() and out.stat().st_size > 0
    back = iio.imread(out, index=None)   # alle Frames als (T, H, W, C)
    assert back.shape[0] == 3


def test_prepare_frame_resizes_to_width_keeping_aspect():
    img = np.zeros((600, 800, 3), dtype=np.uint8)   # H=600, W=800 (4:3)
    out = prepare_frame(img, None, RenderConfig(width=400, caption=False))
    assert out.shape[1] == 400   # Breite
    assert out.shape[0] == 300   # Höhe proportional


def test_prepare_frame_does_not_upscale():
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    out = prepare_frame(img, None, RenderConfig(width=800, caption=False))
    assert out.shape[:2] == (300, 400)   # kleiner als width -> unverändert


def test_format_caption_deutscher_wochentag():
    assert format_caption(datetime(2026, 6, 29, 6, 23, 58)) == "Mo 29.06.2026 06:23"


def test_prepare_frame_draws_caption_when_enabled():
    img = np.full((200, 300, 3), 128, dtype=np.uint8)   # einfarbig grau, keine Skalierung
    ts = datetime(2026, 6, 29, 6, 23, 58)
    without = prepare_frame(img, ts, RenderConfig(width=300, caption=False))
    withcap = prepare_frame(img, ts, RenderConfig(width=300, caption=True))

    assert withcap.shape == without.shape
    assert not np.array_equal(withcap, without)   # Caption verändert das Bild
    assert withcap[-1].min() == 0                 # schwarzer Balken unten enthält reines Schwarz


def test_prepare_frame_no_caption_without_timestamp():
    img = np.full((200, 300, 3), 128, dtype=np.uint8)
    out = prepare_frame(img, None, RenderConfig(width=300, caption=True))
    assert np.array_equal(out, img)   # ohne Zeitstempel keine Einblendung
