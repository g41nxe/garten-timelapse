"""Konfiguration: TOML -> typisierte Config mit Defaults (ADR 0001).

Liest eine `zeitraffer.toml` über die stdlib (`tomllib`, ab Python 3.11 — keine
Zusatz-Abhängigkeit) und füllt fehlende Werte mit den Defaults. CLI-Overrides für
`mode` / `transform` / `out` werden zuletzt angewandt.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_MODES = {"reference", "sequential"}
_TRANSFORMS = {"euclidean", "affine", "homography"}
_FILLS = {"replicate", "black"}


@dataclass
class StabilizeConfig:
    enabled: bool = True
    mode: str = "reference"
    transform: str = "euclidean"
    reference: str = "auto"
    min_inliers: int = 20
    retries: int = 3
    max_zoom: float = 1.5
    fill: str = "replicate"


@dataclass
class RenderConfig:
    width: int = 800
    colors: int = 128
    caption: bool = True


@dataclass
class Config:
    src: Path
    out: Path
    fps: int = 12
    stabilize: StabilizeConfig = field(default_factory=StabilizeConfig)
    render: RenderConfig = field(default_factory=RenderConfig)

    def validate(self) -> None:
        s = self.stabilize
        if s.mode not in _MODES:
            raise ValueError(f"mode muss aus {_MODES} sein, nicht {s.mode!r}")
        if s.transform not in _TRANSFORMS:
            raise ValueError(f"transform muss aus {_TRANSFORMS} sein, nicht {s.transform!r}")
        if s.fill not in _FILLS:
            raise ValueError(f"fill muss aus {_FILLS} sein, nicht {s.fill!r}")
        if s.max_zoom < 1.0:
            raise ValueError(f"max_zoom muss >= 1.0 sein, nicht {s.max_zoom}")


def load_config(path: str | Path, overrides: dict | None = None) -> Config:
    """Lädt die TOML-Config, wendet Overrides an und validiert.

    `overrides` darf die Schlüssel 'mode', 'transform', 'out' enthalten (None = ignorieren).
    """
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    inp = data.get("input", {})
    out = data.get("output", {})
    stab = data.get("stabilize", {})
    rend = data.get("render", {})

    if "src" not in inp:
        raise ValueError("[input].src fehlt in der Config")
    if "path" not in out:
        raise ValueError("[output].path fehlt in der Config")

    cfg = Config(
        src=Path(inp["src"]),
        out=Path(out["path"]),
        fps=int(out.get("fps", 12)),
        stabilize=StabilizeConfig(**{k: stab[k] for k in stab if k in StabilizeConfig.__annotations__}),
        render=RenderConfig(**{k: rend[k] for k in rend if k in RenderConfig.__annotations__}),
    )

    overrides = overrides or {}
    if overrides.get("mode"):
        cfg.stabilize.mode = overrides["mode"]
    if overrides.get("transform"):
        cfg.stabilize.transform = overrides["transform"]
    if overrides.get("out"):
        cfg.out = Path(overrides["out"])

    cfg.validate()
    return cfg
