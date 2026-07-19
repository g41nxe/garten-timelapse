"""Macht das src-Layout ohne vorherige Installation testbar (`pytest` läuft direkt)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
