# Context: garten-timelapse

Kamera-agnostisches Werkzeug: aus einer **Bilderserie** (Ordner mit Einzelbildern)
wird ein **stabilisierter Zeitraffer**. Domänensprache Deutsch.

## Glossar

### Bilderserie
Der Ordner mit den chronologisch geordneten Einzelbildern (Eingang). Die Reihenfolge
ergibt sich aus dem Zeitstempel im Dateinamen (`photo_YYYYMMDD_HHMMSS.jpg`), nicht aus
der Sortierung des Dateisystems.
_Avoid_: Frames-Ordner, Input-Dir.

### Referenzbild
Das eine Bild, auf das im Modus `reference` **alle** Frames ausgerichtet werden.
Fest gewählt (driftfrei). `auto` = ein gut ausgeleuchtetes, feature-reiches Frame.
_Avoid_: Ankerbild (außer im Fehlschlag-Kontext), Master-Frame.

### Ausrichtungs-Modus
`reference` (jedes Frame → dasselbe Referenzbild, kein Drift) oder `sequential`
(jedes Frame → Vorgänger, Transforms kumulativ; glatt, aber driftanfällig).
_Avoid_: Alignment-Strategie.

### Transform-Modell
Die erlaubten Freiheitsgrade der Ausrichtung: `euclidean` (Translation + Rotation,
starr, verzerrungsfrei), `affine` (+ Skalierung/Scherung), `homography` (volle
Perspektive, 8 DOF). Mehr DOF = mehr Risiko sichtbarer Verzerrung bei schlechten Matches.
_Avoid_: Warp-Typ.

### Inlier / Konfidenz
Die Feature-Paare, die nach RANSAC zur geschätzten Transform passen. Ihre Anzahl ist
das Konfidenzmaß: unter `min_inliers` gilt die Ausrichtung eines Frames als **gescheitert**.
_Avoid_: Match-Score.

### Aufgeben-Fall (Identität)
Scheitert die Ausrichtung eines Frames auch nach `retries` Versuchen (gegen alternative
Anker), bleibt es **unverändert** (Identitäts-Transform) im Zeitraffer — nie verworfen —
und löst eine **Warnung** aus.
_Avoid_: Skip, Drop.

### Zuschnitt-Deckel (max-zoom)
Nach dem Warpen entstehen Ränder; der Auto-Zuschnitt schneidet auf das größte gemeinsame
gültige Rechteck, aber **höchstens** bis zum Faktor `max_zoom`. Reicht die Überlappung
weiter (großer Positionssprung), wird geklemmt, der Rest-Rand per `fill` gefüllt
(`replicate` = Kanten fortsetzen, `black` = schwarz) und eine Warnung ausgegeben.
_Avoid_: Crop-Limit.

### Zeitstempel-Einblendung (Caption)
Der aus dem Dateinamen geparste Aufnahme-Zeitpunkt, pro Frame ins Bild gerendert
(`Mo 29.06.2026 06:23`). Format-unabhängig, Teil der Frame-Aufbereitung.
_Avoid_: Overlay, Wasserzeichen.
