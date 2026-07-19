"""CLI (user-facing): Argumente parsen, Config laden, Overrides anwenden, Pipeline starten."""
from __future__ import annotations

import argparse
import logging
import sys

from .config import load_config
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="garten-timelapse",
        description="Stabilisierter Zeitraffer aus einer Bilderserie.",
    )
    parser.add_argument("--config", required=True, help="Pfad zur TOML-Konfiguration")
    # Overrides für die meist-experimentierten Regler (Rest nur über Config):
    parser.add_argument("--mode", choices=["reference", "sequential"], help="Ausrichtungs-Modus (übersteuert Config)")
    parser.add_argument("--transform", choices=["euclidean", "affine", "homography"], help="Transform-Modell (übersteuert Config)")
    parser.add_argument("--out", help="Ausgabepfad; Format über die Endung (übersteuert Config)")
    parser.add_argument("-v", "--verbose", action="store_true", help="ausführliche Ausgabe")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        cfg = load_config(args.config, overrides={"mode": args.mode, "transform": args.transform, "out": args.out})
    except (FileNotFoundError, ValueError) as e:
        print(f"Konfigurationsfehler: {e}", file=sys.stderr)
        return 2

    return run(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
