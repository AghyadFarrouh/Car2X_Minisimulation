
# Car2X‑Minisimulation (Python)

**Ziel:** Eine extrem einfache, lauffähige Simulation, die zeigt, wie ein Einsatzfahrzeug per Car2X‑Broadcast
normale Fahrzeuge im Umkreis informiert – und diese daraufhin kurzfristig Platz machen (verringern die Geschwindigkeit).

## Features
- 1D‑Strecke mit diskreter Zeitschritt‑Simulation
- Einsatzfahrzeug sendet periodisch PRIORITY‑Nachrichten (Broadcast, Reichweite konfigurierbar)
- Normale Fahrzeuge im Wirkbereich wechseln temporär in den Zustand **YIELDING** (Platz machen)
- CSV‑Log aller Fahrzeugzustände über die Zeit
- Optional: Plot der Fahrzeugtrajektorien (Matplotlib)

## Installation & Ausführung
- Benötigt: **Python 3.7+** (3.9+ empfohlen)

- Empfohlene Abhängigkeiten für die Viewer‑UI und erweiterte Ausgabe sind in `requirements.txt` aufgeführt:

```bash
python -m pip install -r requirements.txt
```

- Simulation lokal ausführen (CLI):

```bash
python car2x_simulation.py
```

Nach dem Lauf werden erzeugt:
- `car2x_log.csv` – Zeitreihenlog (Time, vehicle_id, type, position, speed, state)
- `car2x_positions.png` – Liniendiagramm der Positionen (falls Matplotlib + Pandas installiert)

### car2x_viewer (Streamlit UI)

Eine einfache Streamlit‑Benutzeroberfläche `car2x_viewer.py` wurde hinzugefügt, um Logs interaktiv zu betrachten und die Simulation direkt aus der UI zu starten.

Kurzfunktionen:
- **Run simulation**: Startet `car2x_simulation.py` im Hintergrund und lädt danach `car2x_log.csv`, falls erzeugt.
- **Load local car2x_log.csv**: Lädt die lokale CSV aus dem Projektverzeichnis.
- **Upload CSV**: Ermöglicht das Hochladen einer beliebigen CSV zum Anzeigen.
- Interaktive Filter, Positions‑Plot (Altair) und Status‑Zusammenfassung pro Fahrzeug.

Viewer starten:

```bash
python -m streamlit run car2x_viewer.py
```

Hinweise:
- `requirements.txt` listet `streamlit`, `pandas`, `altair` und `matplotlib` (optional) — für die Viewer‑UI sind `streamlit`, `pandas` und `altair` nötig.
- `car2x_viewer.py` enthält eine kurze Runtime/Version‑Prüfung (Python >= 3.7) und zeigt Fehlermeldungen, falls Abhängigkeiten fehlen.
- Auf Windows können Antivirus/Permissions das Schreiben von `car2x_log.csv` verhindern; stelle sicher, dass der Prozess Schreibrechte im Projektordner hat.

## Konfiguration
Direkt oben in `car2x_simulation.py`:
- `N_VEHICLES` (Anzahl Fahrzeuge)
- `PRIORITY_RADIUS` (Reichweite der Car2X‑Prioritätsnachricht)
- `YIELD_DURATION`, `YIELD_SPEED`
- `BASE_SPEED`, `EMERGENCY_SPEED`

## Idee für Erweiterungen
- C2I: Simulierte Ampel, die auf PRIORITY umschaltet
- Unterschiedliche Funktechnologien (WLANp vs. LTE/5G) als unterschiedliche Latenz/Radius‑Profile
- Einfache Kollisionsprüfung / Mindestabstände
- Visualisierung als Animation

## Hinweis
Diese Minisimulation abstrahiert realen Car2X‑Standard (z. B. CAM/DENM) stark und dient nur als
**anschauliches Demo‑Showcase** für Bewerbungszwecke.
