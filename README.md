
# Car2X‑Minisimulation (Python)

**Ziel:** Eine extrem einfache, lauffähige Simulation, die zeigt, wie ein Einsatzfahrzeug per Car2X‑Broadcast
normale Fahrzeuge im Umkreis informiert – und diese daraufhin kurzfristig Platz machen (verringern die Geschwindigkeit).

## Features
## Features
- 1D‑Straße mit diskreter Zeitschritt‑Simulation
- Einsatzfahrzeug sendet periodisch PRIORITY‑Broadcasts (reichweite konfigurierbar)
- Fahrzeuge, die die Nachricht empfangen und sich vor dem Einsatzfahrzeug befinden, wechseln temporär in den Zustand **YIELDING** und reduzieren ihre Geschwindigkeit
- Einfacher In‑Memory‑Broker zur Demonstration der Nachrichtenverteilung
- CSV‑Log aller Fahrzeugzustände über die Zeit (Time, vehicle_id, type, position, speed, state)
- Plot der Positionstrajektorien mit Matplotlib
- Interaktiver Viewer mit Streamlit + Altair zum Filtern und Visualisieren

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
Die wichtigsten Einstellmöglichkeiten finden Sie in der Sidebar des Viewers (siehe `car2x_viewer.py`).

- **Seed:** Zufallsstartwert für reproduzierbare Ergebnisse (`SEED`).
- **Road length (m):** Länge der Simulationsstrecke in Metern (`ROAD_LENGTH_M`).
- **Time step (s):** Zeitschritt Δt in Sekunden (`DT`).
- **Simulation duration (s):** Gesamtlaufzeit der Simulation in Sekunden (`T_MAX`).
- **Number of vehicles:** Anzahl der normalen Fahrzeuge (ohne Einsatzfahrzeug) (`N_VEHICLES`).
- **Base speed (m/s):** Typische Reisegeschwindigkeit normaler Fahrzeuge (`BASE_SPEED`).
- **Emergency speed (m/s):** Geschwindigkeit des Einsatzfahrzeugs (`EMERGENCY_SPEED`).
- **Priority broadcast period (s):** Intervall, in dem das Einsatzfahrzeug Prioritätsnachrichten sendet (`PRIORITY_BROADCAST_PERIOD`).
- **Priority radius (m):** Wirkreichweite der Prioritätsnachricht in Metern (`PRIORITY_RADIUS`).
- **Yield time (s):** Dauer, wie lange ein Fahrzeug Platz macht (`YIELD_Time`).
- **Yield speed (m/s):** Geschwindigkeit während des Platzmachens (`YIELD_SPEED`).

Alternativ können dieselben Konstanten auch direkt oben in `car2x_simulation.py` angepasst werden.

## Hinweis
Diese Minisimulation abstrahiert realen Car2X‑Standard (z. B. CAM/DENM) stark und dient nur als
**anschauliches Demo‑Showcase** für Bewerbungszwecke.
