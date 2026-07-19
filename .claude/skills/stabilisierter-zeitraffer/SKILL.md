---
name: stabilisierter-zeitraffer
description: Erzeugt aus einem Ordner mit Einzelbildern einen stabilisierten Zeitraffer (MP4/GIF/WebM) mit dem Werkzeug garten-timelapse. Verwenden, wenn ein stabilisierter Zeitraffer bzw. Timelapse aus einer Bilderserie gewünscht ist ("stabilisierter Zeitraffer", "Timelapse aus Fotos", "Wackeln rausrechnen").
---

# Stabilisierter Zeitraffer (garten-timelapse)

Dieser Skill bedient das Werkzeug **garten-timelapse**: aus einer **Bilderserie** (Ordner
mit Einzelbildern) wird ein **stabilisierter Zeitraffer**. Jeder Frame wird per
Feature-Matching (OpenCV ORB + RANSAC) auf ein **Referenzbild** ausgerichtet, sodass
Wind-Wackler und einmalige Positionssprünge verschwinden; danach wird auf das gemeinsame
gültige Rechteck zugeschnitten und in ein konfigurierbares Format gerendert. Domänensprache
und Entscheidungen: siehe `CONTEXT.md` und `docs/adr/0001` im Repo.

## Ablauf

1. **Werkzeug bereit machen.** Prüfe, ob `garten-timelapse` installiert ist
   (`python -c "import garten_timelapse"`). Falls nicht, einmalig im Repo installieren:
   ```bash
   pip install -e ".[dev]"   # in C:/Users/g41nx/Repositories/garten-timelapse
   ```
   Braucht Python ≥ 3.11; zieht opencv-python, imageio[ffmpeg], pillow, numpy.

2. **Eingang und Ausgabe klären.** Frage bzw. bestimme:
   - **Bilder-Ordner** (rekursiv nach `photo_YYYYMMDD_HHMMSS.jpg` durchsucht — der
     Zeitstempel im Dateinamen liefert Reihenfolge und Einblendung).
   - **Ausgabe-Pfad** — das **Format ergibt sich aus der Endung**: `.mp4` (H.264,
     Standard), `.gif`, `.webm` (VP9).

3. **Konfiguration schreiben.** Lege eine `zeitraffer.toml` an (Vorlage:
   `zeitraffer.example.toml`) mit mindestens `[input].src` und `[output].path`. Alle
   weiteren Regler haben sinnvolle Defaults (siehe Referenz unten) — nur anfassen, wenn nötig.

4. **Ausführen.**
   ```bash
   garten-timelapse --config zeitraffer.toml
   # schnelle Varianten ohne Config-Änderung:
   garten-timelapse --config zeitraffer.toml --mode sequential --out test.mp4
   ```

5. **Ergebnis verifizieren.** Lies die **Lauf-Zusammenfassung**
   (`Stabilisierung: N/M ausgerichtet, K unverändert; Zuschnitt X.XXx`) und die
   Warnungen. Bestätige, dass die Ausgabedatei existiert und die erwartete Frame-Zahl trägt.

## Richtlinien & Best Practices

- **Defaults nicht vorschnell ändern.** `mode=reference` (driftfrei) und
  `transform=euclidean` (starr, verzerrungsfrei) sind bewusst gewählt. Höhere
  Transform-Freiheitsgrade (affine/homographie) können bei schlechten Matches verzerren.
- **`reference` vs `sequential` empirisch entscheiden.** Beide teilen die Pipeline; bei
  Zweifel *beide* laufen lassen (`--mode`) und das ruhigere Ergebnis behalten. `reference`
  ist driftfrei; `sequential` kettet über den Vorgänger (kann driften, hilft bei starken
  Szenenwechseln).
- **Warnungen ernst nehmen:**
  - „*Frame nicht ausgerichtet*" (mit Zeitstempel): meist dunkle/kontrastarme Bilder
    (Dämmerung/Nacht) — sie bleiben unverändert im Video. Wenige davon sind normal.
  - „*Zuschnitt auf max_zoom geklemmt*": der Versatz (z. B. ein großer Positionssprung
    durch Wartung) war zu groß fürs Zoom-Limit. Dann entweder `max_zoom` erhöhen **oder**
    die Serie am Sprung in zwei Teile trennen und getrennt rendern (Segment-Ansatz).
- **Nie behaupten, es sei stabilisiert, ohne die Zusammenfassung geprüft zu haben.** Bei
  vielen „nicht ausgerichtet"-Frames ist das Material das Problem (zu wenige Features), nicht
  das Werkzeug.
- **Das Schwarz unten im Video ist der Zeitstempel-Balken**, kein Warp-Rand. Wer keine
  Einblendung will: `[render].caption = false`.

## Referenz: Config-Parameter

```toml
[input]
src = "camera-fotos/Garten01"     # Bilder-Ordner (rekursiv)

[output]
path = "garten.mp4"               # .mp4 / .gif / .webm — Format über die Endung
fps  = 12

[stabilize]
enabled     = true
mode        = "reference"         # reference (driftfrei) | sequential (Frame→Vorgänger)
transform   = "euclidean"         # euclidean | affine | homography
min_inliers = 20                  # Konfidenz-Schwelle; höher = strenger, mehr Retries/Fehlschläge
retries     = 3                   # Retry gegen nächstgelegene gute Nachbarn (Verkettung)
max_zoom    = 1.5                 # Deckel für den Auto-Zuschnitt (≥ ~67 % bleiben)
fill        = "replicate"         # Rest-Rand beim Deckel: replicate (Kanten fortsetzen) | black

[render]
width   = 800                     # max. Breite in px
colors  = 128                     # nur GIF: Palettengröße
caption = true                    # Zeitstempel pro Frame einblenden
```

CLI-Overrides (übersteuern die Config): `--mode`, `--transform`, `--out`.
