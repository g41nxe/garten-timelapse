# Implementierungsplan — vertikale Slices

Jeder Slice ist ein **lauffähiger Pfad durch die ganze Pipeline** und endet mit einer
echten Ausgabedatei plus grünen Tests. Kein horizontales Schichten. Vorgehen je Slice:
**roter Test zuerst → minimal grün → Refactor → committen** (ADR 0001).

Voraussetzung (einmalig): `pip install -e ".[dev]"` — zieht opencv-python,
imageio[ffmpeg], pillow, numpy, pytest.

---

## Slice 1 — Passthrough-Zeitraffer (Tracer-Bullet) — ✅ erledigt (20a574a)

**Ziel:** Aus dem Bild-Ordner entsteht eine echte MP4 — *ohne* Stabilisierung, *ohne*
Zeitstempel. Beweist, dass loader → render → pipeline → cli end-to-end läuft.
_Verifiziert auf 111 echten Fotos: 800×600, 2,8 MB, 13 Tests grün._

- **Implementieren:** `render.prepare_frame` (nur Skalierung auf `width`),
  `render.write` (imageio, Format via Endung — hier `.mp4`), `pipeline.run`
  (laden → prepare → write, echte Summary-Zeile).
- **Test:** `write()` erzeugt Datei mit N Frames im MP4-Format; `run()` end-to-end auf
  3 synthetischen Bildern → Datei existiert, Frame-Zahl stimmt.
- **Sichtbar:** `garten-timelapse --config zeitraffer.toml` → abspielbare MP4.

## Slice 2 — Zeitstempel-Einblendung — ✅ erledigt

**Ziel:** Die MP4 zeigt pro Frame den Aufnahme-Zeitpunkt.
_`format_caption` (deutscher Wochentag, locale-frei) + Balken/Schatten in `prepare_frame`; auf 111 Fotos verifiziert. 16 Tests grün._

- **Implementieren:** Caption-Overlay in `prepare_frame` (Pillow, Balken + Schatten),
  Zeitstempel kommt aus `loader.parse_timestamp`. Schalter `render.caption`.
- **Test:** Caption-Formatierung (`datetime → "Mo 29.06.2026 06:23"`); `caption=False`
  lässt das Bild unverändert.
- **Sichtbar:** MP4 mit eingeblendetem Datum/Uhrzeit.

## Slice 3 — Stabilisierung (Kern): reference + euclidean, noch ohne Crop — ✅ erledigt

**Ziel:** Die MP4 steht sichtbar ruhiger (schwarze Ränder noch erlaubt).
_ORB+RANSAC (`estimate_transform`, alle 3 Transform-Modelle), `stabilize_series` im reference-Modus (Fehlschlag→Identität); in pipeline verdrahtet (resize→stabilisieren→Caption). Real-Beweis: auf einem Gleich-Licht-Paar 72 % weniger Restversatz (8,06→2,29); 111 Fotos in 56 s, 0 Fehler. 22 Tests grün._

- **Implementieren:** `stabilize.estimate_transform` (ORB-Features → Match → RANSAC,
  `estimateAffinePartial2D` = euclidean); `stabilize_series` im `reference`-Modus
  (jedes Frame → festes Referenzbild, `warpAffine`); in `pipeline` vor `prepare` einhängen.
- **Test (rein, ohne echtes Material):** synthetisches Bild um bekannte dx/dy verschieben
  → `stabilize_series` holt es zurück (Ergebnis ≈ Referenz, Restversatz < 1 px).
- **Sichtbar:** vorher/nachher-MP4 — Wackeln weg, Ränder noch da.

## Slice 4 — Zuschnitt + max-zoom + fill — ✅ erledigt

**Ziel:** Saubere Kanten statt schwarzer Ränder.
_`crop_series`: gemeinsames gültiges Rechteck (Masken via Konstant-0-Warp) → größtes zentrales Rechteck, gedeckelt bei `max_zoom`; `fill` steuert Warp-Border (replicate/black). Report crop_zoom/crop_clamped + Warnungen in pipeline. Real: 111 Fotos → 1.13× (704×528), in-memory randfrei (Kanten 38–54). 24 Tests grün. (Das Schwarz unten-links im finalen Video ist der Zeitstempel-Balken, kein Warp-Rand — Crop verifiziert sauber.)_

- **Implementieren:** größtes gemeinsames gültiges Rechteck über alle Warps; Deckel
  `max_zoom`; bei Überschreitung klemmen + Rest-Rand `fill` (`replicate`/`black`).
  Report trägt `crop_zoom`/`crop_clamped`.
- **Test:** verschobene Frames → Ausgabe randfrei; künstlich großer Versatz → Zuschnitt
  auf `max_zoom` geklemmt, `crop_clamped=True`.
- **Sichtbar:** MP4 ohne Ränder; bei großem Sprung dezenter Zoom statt Extrembeschnitt.

## Slice 5 — Fehlschlag-Robustheit + Warnungen — ✅ erledigt

**Ziel:** Kein Frame verworfen; schlechte Frames bleiben unverändert und werden gemeldet.
_Konfidenz-Gate (`min_inliers`), Retry gegen nächstgelegene gute Nachbarn mit Transform-Verkettung (`_compose`), sonst Identität. pipeline: Warnung pro Frame (mit Zeitstempel) + Lauf-Zusammenfassung. Real (min_inliers=150): 106/111 über Ketten gerettet, 5 ehrlich gemeldet. 28 Tests grün._

- **Implementieren:** Konfidenz = RANSAC-Inlier; `< min_inliers` → Fehlschlag; bis
  `retries` gegen alternative Anker; sonst Identität. `pipeline` gibt pro Fehlschlag eine
  **Warnung** (mit Zeitstempel) und am Ende die **Lauf-Zusammenfassung** aus; ebenso
  Warnung bei `crop_clamped`.
- **Test:** feature-armes Frame (Rauschen) → im Report `failed_indices`, bleibt Identität,
  Warnung geloggt; Summary zählt korrekt.
- **Sichtbar:** Konsole listet die übersprungenen (Nacht-)Frames + Zusammenfassung.

## Slice 6 — Flexibilität: Modi, Transforms, Formate — ✅ erledigt

**Ziel:** Die Regler aus der Config/CLI greifen alle.
_`sequential`-Modus (Frame→Vorgänger, kumulativ via `_compose`); affine/homographie fließen durch estimate_transform/_warp; `write` mit Format-Dispatch: GIF (Palette `colors`), WebM (VP9), MP4 (H.264, CRF 18). Real verifiziert: MP4/WebM/sequential über CLI. 33 Tests grün._

- **Implementieren:** `mode="sequential"` (Frame→Vorgänger, Transforms kumulativ);
  `transform` affine (`estimateAffine2D`) / homography (`findHomography` + `warpPerspective`);
  Ausgabe `.gif` (Palette/`colors`) und `.webm` (VP9) über dieselbe `write()`-Dispatch.
- **Test:** sequential summiert Transforms; jeder Transform-Zweig wählt den richtigen
  Schätzer/Warp; `.gif`/`.webm` werden erzeugt.
- **Sichtbar:** `--mode sequential`, `--transform affine`, `--out x.gif|x.webm`.

---

**Nach Slice 6** ist das Tool vollständig gemäß ADR 0001. Optional/offen gehalten:
**Segment-Modus** (getrennte Referenz vor/nach großem Wartungs-Sprung) — erst bauen, wenn
sich am echten Material zeigt, dass ein einzelnes Referenzbild beide Hälften nicht abdeckt.
