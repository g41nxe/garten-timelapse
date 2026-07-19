# 1. Stabilisierter Zeitraffer aus einer Bilderserie

Aus einem Ordner mit Einzelbildern wird ein stabilisierter Zeitraffer. Die Frames
werden per Feature-Matching auf ein Referenzbild ausgerichtet (entzittert), dann in
ein konfigurierbares Format (MP4/GIF/WebM) gerendert. Das Werkzeug ist
kamera-agnostisch; das Herunterladen der Bilder vom Raspberry Pi bleibt im
`garden`-Projekt.

## Kontext

Die Garten-Kamera bewegt sich leicht (Wind) und wurde bei einer Wartung minimal
umpositioniert — ein einmaliger Sprung mitten in der Serie. Ein direkt aus den
Rohbildern erzeugter Zeitraffer wackelt dadurch sichtbar. Die Bilder liegen nach dem
Download (garden, `fetch-camera-photos.ps1`) lokal als `photo_YYYYMMDD_HHMMSS.jpg`
vor; die Serie überspannt mehrere Tage mit großer Lichtspanne (Dämmerung bis Nacht).

## Entscheidung

- **Eigenständiges, kamera-agnostisches Repo.** Eingang ist ein Bilder-Ordner,
  Ausgang ein Zeitraffer. Der Pi-Transfer bleibt in `garden` (saubere Grenze).

- **Ausrichtung per OpenCV ORB + RANSAC.** Feature-basiert, weil die Lichtspanne
  (Tag/Nacht) intensitätsbasierte Verfahren (ECC, Phasenkorrelation) scheitern lässt;
  ORB matcht strukturelle Features (Zaun, Töpfe), die lichtunabhängig vorhanden sind.

- **Ausrichtungs-Modus konfigurierbar** (`--mode`): `reference` (Default, driftfrei) und
  `sequential` (Frame→Vorgänger, kumulativ). Beide teilen fast die ganze Pipeline; die
  Wahl wird empirisch am eigenen Material getroffen. Default `reference`, weil ein
  einmaliger Wartungs-Sprung als *eine* große Translation absorbiert wird, während
  `sequential` die vielen kleinen Wind-Korrekturen zu Drift aufsummiert.

- **Transform-Modell konfigurierbar** (`--transform`): `euclidean` (Default, starr) /
  `affine` / `homography`. Mehr Freiheitsgrade können bei schlechten Matches verzerren —
  der Default schützt, das Opt-in erlaubt Experimente.

- **Fehlschlag → Identität, nie verwerfen.** Konfidenz = RANSAC-Inlier-Anzahl; unter
  `min_inliers` gilt ein Frame als gescheitert. Dann bis zu `retries` (Default 3)
  Versuche gegen alternative Anker; danach bleibt das Frame **unverändert** im Zeitraffer
  und löst eine **Warnung** aus (mit Zeitstempel). Am Ende eine Lauf-Zusammenfassung.

- **Zuschnitt mit Deckel.** Auto-Zuschnitt auf das größte gemeinsame gültige Rechteck,
  aber höchstens `max_zoom` (Default 1.5×, ≥ ~67 % bleiben). Bei Überschreitung
  (großer Sprung): klemmen, Rest-Rand per `fill` füllen (`replicate` Default, sonst
  `black`) und **warnen** — dann ist ggf. ein Segment-Modus (vor/nach Wartung) besser.

- **Ausgabe über imageio-ffmpeg, Format via Dateiendung.** `.mp4` (H.264, Default) /
  `.gif` / `.webm` (VP9). Bundelt statisches ffmpeg — kein System-ffmpeg nötig. Die
  Frame-Aufbereitung (Skalierung, Zeitstempel-Einblendung mit Pillow) ist
  format-unabhängig; nur der letzte Encode-Schritt unterscheidet sich.

- **Konfiguration in TOML.** Alle Parameter in einer `zeitraffer.toml` (stdlib
  `tomllib`, keine Zusatz-Abhängigkeit); CLI-Overrides nur für die meist-experimentierten
  `--mode` / `--transform` / `--out`.

- **Struktur: `src/`-Layout + `pyproject.toml` (PEP 621, hatchling).** Modulgrenzen nach
  den Design-Achsen: `stabilize` (OpenCV), `render` (imageio), `config` (TOML),
  `loader` (I/O), `cli` (user-facing), `pipeline` (Orchestrierung + Warnungen). `tests/`
  spiegelt die Module.

## Konsequenzen

- Lokale Abhängigkeiten: `opencv-python`, `imageio[ffmpeg]`, `pillow`, `numpy` — bewusst
  außerhalb von `garden` (dessen Produktiv-Daemon bleibt schlank bei `paho-mqtt`).
- `stabilize` ist rein testbar (synthetisch verschobene Bilder → erwartete Rück-Transform),
  ohne echtes Bildmaterial.
- Der ADR 0027 des `garden`-Repos (Daemon-seitige GIF-Erzeugung via ffmpeg auf dem Pi,
  Bild-Puffer, `/timelapse`) bleibt davon unberührt — anderer Ort, andere Randbedingungen.
- Offen für später: ein **Segment-Modus** (getrennte Referenz vor/nach einem großen
  Positionssprung), falls ein einzelnes Referenzbild die beiden Hälften nicht abdeckt.
