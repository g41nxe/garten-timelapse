# garten-timelapse

Aus einem Ordner mit Einzelbildern wird ein **stabilisierter Zeitraffer**
(MP4 / GIF / WebM). Kamera-agnostisch — die Bilder können von der Garten-Kamera,
einer Baustelle oder einer Pflanze am Fenster stammen.

Die Stabilisierung richtet jeden Frame per Feature-Matching (OpenCV ORB + RANSAC)
auf ein Referenzbild aus und entzittert so Wind-Wackler und einmalige
Positionssprünge (z. B. nach Wartung). Siehe [docs/adr/0001](docs/adr/0001-stabilisierter-zeitraffer.md).

## Installation

```bash
pip install -e .            # legt den Befehl `garten-timelapse` an
# oder: pip install -e ".[dev]"   für die Tests
```

Benötigt Python ≥ 3.11 (für `tomllib`). Zieht `opencv-python`, `imageio[ffmpeg]`,
`pillow`, `numpy` — alles rein lokal, kein System-ffmpeg nötig.

## Nutzung

```bash
cp zeitraffer.example.toml zeitraffer.toml   # anpassen
garten-timelapse --config zeitraffer.toml

# CLI-Overrides für schnelle A/B-Vergleiche:
garten-timelapse --config zeitraffer.toml --mode sequential --out test.mp4
```

Alle Parameter (Ausrichtungs-Modus, Transform, Zuschnitt-Deckel, Format, FPS …)
stehen in der TOML-Config; `--mode` / `--transform` / `--out` lassen sich auf der
CLI übersteuern.

## Herkunft

Entstanden als eigenständiges Werkzeug neben dem `garden`-Projekt: dort werden die
Kamera-Fotos vom Raspberry Pi geholt (`fetch-camera-photos.ps1`), hier werden sie
zum Zeitraffer verarbeitet. Saubere Grenze — garden besitzt den Pi-Transfer, dieses
Repo die Bild-→-Video-Verarbeitung.
