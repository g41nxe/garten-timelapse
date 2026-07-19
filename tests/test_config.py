import pytest

from garten_timelapse.config import load_config

_MINIMAL = '[input]\nsrc = "imgs"\n[output]\npath = "out.mp4"\n'


def _cfg(tmp_path, body):
    p = tmp_path / "z.toml"
    p.write_text(body, encoding="utf-8")
    return load_config(p)


def test_defaults_applied(tmp_path):
    cfg = _cfg(tmp_path, _MINIMAL)
    assert str(cfg.src) == "imgs"
    assert cfg.out.name == "out.mp4"
    assert cfg.fps == 12
    assert cfg.stabilize.mode == "reference"
    assert cfg.stabilize.transform == "euclidean"
    assert cfg.stabilize.max_zoom == 1.5
    assert cfg.stabilize.fill == "replicate"
    assert cfg.render.width == 800


def test_values_from_file(tmp_path):
    body = _MINIMAL + '[stabilize]\nmode = "sequential"\nmax_zoom = 2.0\n[render]\nwidth = 640\n'
    cfg = _cfg(tmp_path, body)
    assert cfg.stabilize.mode == "sequential"
    assert cfg.stabilize.max_zoom == 2.0
    assert cfg.render.width == 640


def test_overrides_win(tmp_path):
    p = tmp_path / "z.toml"
    p.write_text(_MINIMAL, encoding="utf-8")
    cfg = load_config(p, overrides={"mode": "sequential", "transform": "affine", "out": "x.gif"})
    assert cfg.stabilize.mode == "sequential"
    assert cfg.stabilize.transform == "affine"
    assert cfg.out.name == "x.gif"


def test_invalid_mode_raises(tmp_path):
    with pytest.raises(ValueError):
        _cfg(tmp_path, _MINIMAL + '[stabilize]\nmode = "wackeln"\n')


def test_missing_src_raises(tmp_path):
    with pytest.raises(ValueError):
        _cfg(tmp_path, '[output]\npath = "out.mp4"\n')
