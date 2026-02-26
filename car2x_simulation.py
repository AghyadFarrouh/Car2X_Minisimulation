
"""
Extrem einfache Car2X‑Minisimulation (Python, ohne externe Abhängigkeiten außer matplotlib/pandas optional)
---------------------------------------------------------------------------------------------
Was wird simuliert?
- 1D-Straße (Gerade) mit normalen Fahrzeugen und einem Einsatzfahrzeug.
- Das Einsatzfahrzeug sendet periodisch eine Car2X-Prioritätsnachricht (Broadcast) mit Reichweite.
- Normale Fahrzeuge, die die Nachricht empfangen und in Fahrtrichtung vor dem Einsatzfahrzeug liegen,
  gehen in den Zustand "YIELDING" (Platz machen): sie reduzieren die Geschwindigkeit für kurze Zeit.
- Es wird ein Log erzeugt und optional eine Grafik gespeichert.

Ausführen:
    python car2x_simulation.py

Parametertuning: Unten im Abschnitt "Konfiguration" anpassen.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import math
import random
import csv
import os

# Optional: Plot & CSV-Ausgabe
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

try:
    import pandas as pd
    HAS_PD = True
except Exception:
    HAS_PD = False

# ----------------------------
# Konfiguration
# ----------------------------
SEED = 42                 # für reproduzierbare Ergebnisse
ROAD_LENGTH_M = 2000      # Länge der Simulationsstrecke (Meter)
DT = 0.5                  # Zeitschritt in Sekunden
T_MAX = 120               # Simulationsdauer in Sekunden

N_VEHICLES = 8            # Anzahl normaler Fahrzeuge
BASE_SPEED = 22.0         # m/s ~ 79 km/h (normales Fahrzeug)
EMERGENCY_SPEED = 30.0    # m/s ~ 108 km/h (Einsatzfahrzeug)

PRIORITY_BROADCAST_PERIOD = 1.0   # Sekunden
PRIORITY_RADIUS = 300.0           # Meter, effektiver Wirkbereich der Nachricht
YIELD_Time = 10.0             # Sekunden, wie lange ein Fahrzeug Platz macht
YIELD_SPEED = 5.0                 # m/s während des Platzmachens

LOG_CSV = "car2x_log.csv"
PLOT_PNG = "car2x_positions.png"

random.seed(SEED)

# ----------------------------
# Modelle
# ----------------------------
@dataclass
class Message:
    msg_type: str
    sender_id: str
    position: float
    timestamp: float
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Vehicle:
    vid: str
    position: float
    speed: float
    state: str = "NORMAL"  # NORMAL | YIELDING
    yield_timer: float = 0.0

    def step(self, dt: float):
        # Zustand updaten
        if self.state == "YIELDING":
            self.yield_timer -= dt
            if self.yield_timer <= 0:
                self.state = "NORMAL"

        # Geschwindigkeit abhängig vom Zustand
        v = YIELD_SPEED if self.state == "YIELDING" else self.speed
        self.position += v * dt

@dataclass
class EmergencyVehicle(Vehicle):
    last_broadcast: float = -1e9

    def maybe_broadcast_priority(self, t: float) -> List[Message]:
        msgs = []
        if (t - self.last_broadcast) >= PRIORITY_BROADCAST_PERIOD:
            msgs.append(Message(
                msg_type="PRIORITY",
                sender_id=self.vid,
                position=self.position,
                timestamp=t,
                payload={"radius": PRIORITY_RADIUS}
            ))
            self.last_broadcast = t
        return msgs

class SimpleBroker:
    """
    Minimaler In‑Memory‑Broker: verteilt Broadcast‑Nachrichten an alle Fahrzeuge.
    Keine echten Topics/Subscriptions – für die Demo ausreichend.
    """
    def __init__(self, vehicles: List[Vehicle]):
        self.vehicles = vehicles

    def broadcast(self, msg: Message, emergency: EmergencyVehicle):
        for v in self.vehicles:
            if v.vid == emergency.vid:
                continue
            self.deliver(msg, v, emergency)

    def deliver(self, msg: Message, receiver: Vehicle, emergency: EmergencyVehicle):
        # Einfache Empfangslogik: nur wenn im Radius und vor dem Einsatzfahrzeug
        if msg.msg_type == "PRIORITY":
            dx = receiver.position - emergency.position
            in_front = dx > 0
            in_radius = abs(dx) <= msg.payload.get("radius", PRIORITY_RADIUS)
            if in_front and in_radius:
                # Receiver macht Platz, wenn nicht bereits yielding
                if receiver.state != "YIELDING":
                    receiver.state = "YIELDING"
                    receiver.yield_timer = YIELD_Time

# ----------------------------
# Aufbau der Szene
# ----------------------------

def build_scene():
    # Einsatzfahrzeug startet bei 0 m
    ev = EmergencyVehicle(vid="EV-1", position=0.0, speed=EMERGENCY_SPEED)

    vehicles: List[Vehicle] = [ev]

    # Normale Fahrzeuge zufällig entlang der Strecke vor dem EV platzieren
    # zwischen 200 m und 1200 m, mit kleiner Speed‑Streuung
    for i in range(N_VEHICLES):
        pos = random.uniform(200, 1200)
        spd = max(12.0, random.gauss(BASE_SPEED, 2.5))
        vehicles.append(Vehicle(vid=f"V-{i+1}", position=pos, speed=spd))

    return ev, vehicles

# ----------------------------
# Simulation
# ----------------------------

def run_simulation(log_csv: str = LOG_CSV, plot_png: str = PLOT_PNG):
    ev, vehicles = build_scene()
    broker = SimpleBroker(vehicles)

    # Log vorbereiten
    fields = ["Time", "vehicle_id", "type", "position", "speed", "state"]
    rows = []

    t = 0.0
    while t <= T_MAX:
        # EV broadcastet ggf. eine Prioritätsnachricht
        for msg in ev.maybe_broadcast_priority(t):
            broker.broadcast(msg, ev)

        # Schritt für alle Fahrzeuge
        for v in vehicles:
            v.step(DT)

        # Log erfassen
        for v in vehicles:
            rows.append({
                "Time": round(t, 2),
                "vehicle_id": v.vid,
                "type": "EV" if isinstance(v, EmergencyVehicle) else "CAR",
                "position": round(v.position, 2),
                "speed": round((YIELD_SPEED if v.state == "YIELDING" else v.speed), 2),
                "state": v.state
            })

        # Ende, falls EV am Ziel (Streckenende)
        if ev.position >= ROAD_LENGTH_M:
            break

        t += DT

    # CSV schreiben
    with open(log_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Plot erzeugen (optional)
    if HAS_PD and HAS_MPL:
        import pandas as pd
        df = pd.DataFrame(rows)
        # Liniendiagramm: Position über Zeit für jedes Fahrzeug
        plt.figure(figsize=(10, 6))
        for vid, g in df.groupby("vehicle_id"):
            if vid.startswith("EV"):
                plt.plot(g["Time"], g["position"], label=f"{vid} (Einsatz)", linewidth=2.5, color="#d62728")
            else:
                plt.plot(g["Time"], g["position"], alpha=0.9)
        plt.title("Car2X‑Minisimulation: Einsatzfahrzeug und übrige Fahrzeuge", fontweight="bold")
        plt.xlabel("Zeit (s)")
        plt.ylabel("Position auf der Strecke (m)")
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(plot_png, dpi=160)
        plt.close()

    return log_csv, (plot_png if os.path.exists(plot_png) else None)

# ----------------------------
# Demo‑Runner
# ----------------------------

def run_demo():
    log_csv, plot_png = run_simulation()
    print("Simulation abgeschlossen.")
    print("Log:", log_csv)
    if plot_png:
        print("Plot:", plot_png)

if __name__ == "__main__":
    run_demo()
