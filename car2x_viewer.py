import streamlit as st
import pandas as pd
import altair as alt
import subprocess
import sys
from pathlib import Path
import os

# --- Minimal runtime/version checks ---
MIN_PY = (3, 7)
if sys.version_info < MIN_PY:
    raise SystemExit(f"Python {MIN_PY[0]}.{MIN_PY[1]}+ is required; running {sys.version}")

try:
    # importlib.metadata exists on Python >=3.8; for 3.7 the backport may not be installed
    try:
        import importlib.metadata as importlib_metadata
    except Exception:
        import importlib_metadata

    def _pkg_ver(name: str) -> str:
        try:
            return importlib_metadata.version(name)
        except Exception:
            return "not installed"
except Exception:
    def _pkg_ver(name: str) -> str:
        return "unknown"

st.set_page_config(page_title="Car2X Simulation Viewer", layout="wide")

st.title("Car2X – Minisimulation Viewer")
st.write("Eine extrem einfache, lauffähige Simulation, die zeigt, wie ein Einsatzfahrzeug per Car2X‑Broadcastnormale Fahrzeuge im Umkreis informiert – und diese daraufhin kurzfristig Platz machen (verringern die Geschwindigkeit).")
st.write("Diese Minisimulation abstrahiert realen Car2X‑Standard (z. B. CAM/DENM) stark und dient nur als anschauliches Demo‑Showcase für Bewerbungszwecke.")

# determine project root (directory of this file)
ROOT = Path(__file__).resolve().parent

# Try to import the simulation module to obtain default configuration values
SIM_DEFAULTS = {}
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("car2x_simulation", str(ROOT / "car2x_simulation.py"))
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)
    SIM_DEFAULTS = {
        "SEED": getattr(sim, "SEED", 42),
        "ROAD_LENGTH_M": getattr(sim, "ROAD_LENGTH_M", 2000),
        "DT": getattr(sim, "DT", 0.5),
        "T_MAX": getattr(sim, "T_MAX", 120),
        "N_VEHICLES": getattr(sim, "N_VEHICLES", 8),
        "BASE_SPEED": getattr(sim, "BASE_SPEED", 22.0),
        "EMERGENCY_SPEED": getattr(sim, "EMERGENCY_SPEED", 30.0),
        "PRIORITY_BROADCAST_PERIOD": getattr(sim, "PRIORITY_BROADCAST_PERIOD", 1.0),
        "PRIORITY_RADIUS": getattr(sim, "PRIORITY_RADIUS", 300.0),
        "YIELD_Time": getattr(sim, "YIELD_Time", 10.0),
        "YIELD_SPEED": getattr(sim, "YIELD_SPEED", 5.0),
    }
except Exception:
    SIM_DEFAULTS = {}

# session storage for dataframe
if "df" not in st.session_state:
    st.session_state.df = None

# Toolbar: run simulation or load local CSV (stacked)
# Upload CSV file
uploaded = st.file_uploader("Lade eine CSV-Datei hoch", type=["csv"])
if uploaded:
    st.session_state.df = pd.read_csv(uploaded)

# Load local CSV from project
if st.button("Load previous session"):
    log_path = ROOT / "car2x_log.csv"
    if log_path.exists():
        st.session_state.df = pd.read_csv(log_path)
        st.success("Previous session loaded successfully.")
    else:
        st.error(f"Previous session not found: {log_path}")



# Sidebar: editable configuration
with st.sidebar:
    st.header("Simulation settings")
    seed = st.number_input("Seed", value=int(SIM_DEFAULTS.get("SEED", 42)), step=1)
    road_length = st.number_input("Road length (m)", value=int(SIM_DEFAULTS.get("ROAD_LENGTH_M", 2000)), step=100)
    dt = st.number_input("Time step (s)", value=float(SIM_DEFAULTS.get("DT", 0.5)), format="%.3f")
    t_max = st.number_input("Simulation duration (s)", value=int(SIM_DEFAULTS.get("T_MAX", 120)), step=10)
    n_vehicles = st.number_input("Number of vehicles", value=int(SIM_DEFAULTS.get("N_VEHICLES", 8)), step=1)
    base_speed = st.number_input("Base speed (m/s)", value=float(SIM_DEFAULTS.get("BASE_SPEED", 22.0)), format="%.2f")
    emergency_speed = st.number_input("Emergency speed (m/s)", value=float(SIM_DEFAULTS.get("EMERGENCY_SPEED", 30.0)), format="%.2f")
    priority_period = st.number_input("Priority broadcast period (s)", value=float(SIM_DEFAULTS.get("PRIORITY_BROADCAST_PERIOD", 1.0)), format="%.2f")
    priority_radius = st.number_input("Priority radius (m)", value=float(SIM_DEFAULTS.get("PRIORITY_RADIUS", 300.0)), step=10.0, format="%.1f")
    yield_time = st.number_input("Yield time (s)", value=float(SIM_DEFAULTS.get("YIELD_Time", 10.0)), format="%.1f")
    yield_speed = st.number_input("Yield speed (m/s)", value=float(SIM_DEFAULTS.get("YIELD_SPEED", 5.0)), format="%.2f")

    if st.button("Run simulation with these settings"):
        # Read original simulation source
        sim_path = ROOT / "car2x_simulation.py"
        try:
            content = sim_path.read_text(encoding="utf-8")

            start_marker = "# ----------------------------\n# Konfiguration\n# ----------------------------\n"
            start = content.find(start_marker)
            end = content.find("LOG_CSV", start) if start != -1 else -1
            if start == -1 or end == -1:
                st.error("Konnte Konfigurationsabschnitt in car2x_simulation.py nicht finden.")
            else:
                # Build new config block
                new_block = (
                    start_marker
                    + f"SEED = {int(seed)}\n"
                    + f"ROAD_LENGTH_M = {int(road_length)}\n"
                    + f"DT = {float(dt)}\n"
                    + f"T_MAX = {int(t_max)}\n\n"
                    + f"N_VEHICLES = {int(n_vehicles)}\n"
                    + f"BASE_SPEED = {float(base_speed)}\n"
                    + f"EMERGENCY_SPEED = {float(emergency_speed)}\n\n"
                    + f"PRIORITY_BROADCAST_PERIOD = {float(priority_period)}\n"
                    + f"PRIORITY_RADIUS = {float(priority_radius)}\n"
                    + f"YIELD_Time = {float(yield_time)}\n"
                    + f"YIELD_SPEED = {float(yield_speed)}\n\n"
                )

                new_content = content[:start] + new_block + content[end:]

                # Write temporary simulation file
                tmp_path = ROOT / "car2x_simulation_tmp.py"
                tmp_path.write_text(new_content, encoding="utf-8")

                # Run the temporary simulation
                try:
                    subprocess.run([sys.executable, str(tmp_path)], check=True, capture_output=True, text=True)
                    log_path = ROOT / "car2x_log.csv"
                    if log_path.exists():
                        st.session_state.df = pd.read_csv(log_path)
                        st.success("Simulation ausgeführt und geladen.")
                    else:
                        st.warning(f"Simulation beendet, aber {log_path.name} nicht gefunden.")
                except subprocess.CalledProcessError as e:
                    st.error(f"Fehler beim Ausführen der Simulation: {e}")
                    if e.stdout:
                        st.text(e.stdout)
                    if e.stderr:
                        st.text(e.stderr)
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        except Exception as e:
            st.error(f"Fehler beim Vorbereiten der Simulation: {e}")

# If we have a dataframe (from any source), show it
df = st.session_state.df
if df is not None:
    st.subheader("Rohdaten (CSV)")
    st.dataframe(df, use_container_width=True)

    st.subheader("Fahrzeuge filtern")
    vehicles = df["vehicle_id"].unique()
    selected = st.multiselect("Wähle Fahrzeuge", vehicles, default=list(vehicles))

    plot_df = df[df["vehicle_id"].isin(selected)]

    st.subheader("Positionsverlauf über die Zeit")

    chart = (
        alt.Chart(plot_df)
        .mark_line()
        .encode(
            x=alt.X("Time:Q", title="Zeit (s)"),
            y=alt.Y("position:Q", title="Position (m)"),
            color="vehicle_id:N",
            tooltip=["vehicle_id", "Time", "position", "speed", "state"],
        )
        .properties(width="container", height=400)
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Status-Analyse")
    st.write("Anteil der Zeit in YIELDING vs NORMAL")

    state_summary = (
        df.groupby(["vehicle_id", "state"]) 
        .size()
        .reset_index(name="count")
        .pivot(index="vehicle_id", columns="state", values="count")
        .fillna(0)
    )

    st.dataframe(state_summary, use_container_width=True)
else:
    st.info("Bitte starte die Simulation.")