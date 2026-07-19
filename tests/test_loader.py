from datetime import datetime
from pathlib import Path

from garten_timelapse.loader import find_photos, parse_timestamp


def test_parse_timestamp():
    assert parse_timestamp(Path("photo_20260629_062358.jpg")) == datetime(2026, 6, 29, 6, 23, 58)


def test_parse_timestamp_rejects_non_matching():
    assert parse_timestamp(Path("latest.jpg")) is None
    assert parse_timestamp(Path("foto_20260629.jpg")) is None


def test_find_photos_sorted_by_timestamp(tmp_path):
    # In verwürfelter Reihenfolge anlegen; latest.jpg muss ignoriert werden.
    for name in [
        "photo_20260630_120102.jpg",
        "photo_20260629_062358.jpg",
        "latest.jpg",
        "photo_20260629_200005.jpg",
    ]:
        (tmp_path / name).write_bytes(b"x")

    result = [p.name for p in find_photos(tmp_path)]
    assert result == [
        "photo_20260629_062358.jpg",
        "photo_20260629_200005.jpg",
        "photo_20260630_120102.jpg",
    ]


def test_find_photos_recursive(tmp_path):
    sub = tmp_path / "Garten01"
    sub.mkdir()
    (sub / "photo_20260629_062358.jpg").write_bytes(b"x")
    assert len(find_photos(tmp_path)) == 1
