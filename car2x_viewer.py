from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Car2X Simulation Viewer", layout="wide")

st.title("Car2X – Minisimulation Viewer")
st.write("Eine extrem einfache, lauffähige Simulation, die zeigt, wie ein Einsatzfahrzeug per Car2X‑Broadcastnormale Fahrzeuge im Umkreis informiert – und diese daraufhin kurzfristig Platz machen (verringern die Geschwindigkeit).")
st.write("Diese Minisimulation abstrahiert realen Car2X‑Standard (z. B. CAM/DENM) stark und dient nur als anschauliches Demo‑Showcase für Bewerbungszwecke.")

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
DEFAULT_LOG_PATH = ARTIFACTS_DIR / "car2x_log.csv"
TIMELINE_PNG_PATH = ARTIFACTS_DIR / "car2x_timeline.png"


def _ensure_repo_on_path() -> None:
    root_str = str(ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _get_simulation_module():
    _ensure_repo_on_path()
    import importlib

    return importlib.import_module("car2x_simulation")


def _simulation_defaults(simulation: Any) -> dict[str, Any]:
    return {
        "SEED": getattr(simulation, "SEED", 42),
        "ROAD_LENGTH_M": getattr(simulation, "ROAD_LENGTH_M", 2000),
        "DT": getattr(simulation, "DT", 0.5),
        "T_MAX": getattr(simulation, "T_MAX", 120),
        "N_VEHICLES": getattr(simulation, "N_VEHICLES", 8),
        "BASE_SPEED": getattr(simulation, "BASE_SPEED", 22.0),
        "EMERGENCY_SPEED": getattr(simulation, "EMERGENCY_SPEED", 30.0),
        "PRIORITY_BROADCAST_PERIOD": getattr(simulation, "PRIORITY_BROADCAST_PERIOD", 1.0),
        "PRIORITY_RADIUS": getattr(simulation, "PRIORITY_RADIUS", 300.0),
        "YIELD_Time": getattr(simulation, "YIELD_Time", 10.0),
        "YIELD_SPEED": getattr(simulation, "YIELD_SPEED", 5.0),
    }


def _load_csv(uploaded_file=None, path: Path | None = None) -> pd.DataFrame:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    if path is not None:
        return pd.read_csv(path)
    raise ValueError("Either uploaded_file or path must be provided")


def _run_simulation(sim: Any, settings: dict[str, Any]) -> str:
    for key, value in settings.items():
        setattr(sim, key, value)

    # Keep deterministic behavior aligned with SEED.
    try:
        sim.random.seed(sim.SEED)
    except Exception:
        pass

    log_csv, _plot_png = sim.run_simulation(output_dir=str(ARTIFACTS_DIR))
    return log_csv


def _get_timeline_module():
    _ensure_repo_on_path()
    import importlib

    return importlib.import_module("car2x_timeline")


def _generate_timeline_artifacts(df: pd.DataFrame) -> Path | None:
    timeline = _get_timeline_module()
    timeline_df = timeline._ensure_time_column(df.copy())

    if "t" not in timeline_df.columns or timeline_df["t"].isna().all():
        raise ValueError("CSV enthält keine gültige Zeit-Spalte (erwartet 't' oder 'Time').")

    png_out = timeline.plot_timeline(timeline_df, out_png=str(TIMELINE_PNG_PATH))

    png_path = Path(png_out) if png_out else None
    return png_path

if "df" not in st.session_state:
    st.session_state.df = None

uploaded = st.file_uploader("Lade eine CSV-Datei hoch", type=["csv"])
if uploaded is not None:
    st.session_state.df = _load_csv(uploaded_file=uploaded)

if st.button("Load previous session"):
    if DEFAULT_LOG_PATH.exists():
        st.session_state.df = _load_csv(path=DEFAULT_LOG_PATH)
        st.success("Previous session loaded successfully.")
    else:
        st.error(f"Previous session not found: {DEFAULT_LOG_PATH}")



with st.sidebar:
    st.header("Simulation settings")

    try:
        sim = _get_simulation_module()
        defaults = _simulation_defaults(sim)
    except Exception as e:
        sim = None
        defaults = {}
        st.error(f"Could not import simulation module: {e}")

    seed = st.number_input("Seed", value=int(defaults.get("SEED", 42)), step=1)
    road_length = st.number_input("Road length (m)", value=int(defaults.get("ROAD_LENGTH_M", 2000)), step=100)
    dt = st.number_input("Time step (s)", value=float(defaults.get("DT", 0.5)), format="%.3f")
    t_max = st.number_input("Simulation duration (s)", value=int(defaults.get("T_MAX", 120)), step=10)
    n_vehicles = st.number_input("Number of vehicles", value=int(defaults.get("N_VEHICLES", 8)), step=1)
    base_speed = st.number_input("Base speed (m/s)", value=float(defaults.get("BASE_SPEED", 22.0)), format="%.2f")
    emergency_speed = st.number_input(
        "Emergency speed (m/s)", value=float(defaults.get("EMERGENCY_SPEED", 30.0)), format="%.2f"
    )
    priority_period = st.number_input(
        "Priority broadcast period (s)",
        value=float(defaults.get("PRIORITY_BROADCAST_PERIOD", 1.0)),
        format="%.2f",
    )
    priority_radius = st.number_input(
        "Priority radius (m)",
        value=float(defaults.get("PRIORITY_RADIUS", 300.0)),
        step=10.0,
        format="%.1f",
    )
    yield_time = st.number_input("Yield time (s)", value=float(defaults.get("YIELD_Time", 10.0)), format="%.1f")
    yield_speed = st.number_input("Yield speed (m/s)", value=float(defaults.get("YIELD_SPEED", 5.0)), format="%.2f")

    if st.button("Run simulation with these settings", disabled=(sim is None)):
        settings = {
            "SEED": int(seed),
            "ROAD_LENGTH_M": int(road_length),
            "DT": float(dt),
            "T_MAX": int(t_max),
            "N_VEHICLES": int(n_vehicles),
            "BASE_SPEED": float(base_speed),
            "EMERGENCY_SPEED": float(emergency_speed),
            "PRIORITY_BROADCAST_PERIOD": float(priority_period),
            "PRIORITY_RADIUS": float(priority_radius),
            "YIELD_Time": float(yield_time),
            "YIELD_SPEED": float(yield_speed),
        }
        with st.spinner("Running simulation..."):
            try:
                log_csv = _run_simulation(sim, settings)
                st.session_state.df = _load_csv(path=Path(log_csv))
                st.success("Simulation ausgeführt und geladen.")

                try:
                    png_path = _generate_timeline_artifacts(st.session_state.df)
                    if png_path is not None:
                        st.success(f"Timeline PNG geschrieben: {png_path}")
                except Exception as timeline_error:
                    st.warning(f"Simulation erfolgreich, aber Timeline konnte nicht erzeugt werden: {timeline_error}")
            except Exception as e:
                st.error(f"Fehler beim Ausführen der Simulation: {e}")

# If we have a dataframe (from any source), show it
df = st.session_state.df
if df is not None:
    required_cols = {"vehicle_id", "Time", "position", "speed", "state"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        st.error(f"CSV fehlt Spalten: {', '.join(sorted(missing_cols))}")
        st.stop()

    st.subheader("Rohdaten (CSV)")
    st.dataframe(df, use_container_width=True)

    st.subheader("Fahrzeuge filtern")
    vehicles = df["vehicle_id"].unique().tolist()
    selected = st.multiselect("Wähle Fahrzeuge", vehicles, default=vehicles)

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

    st.subheader("Car2X Timeline Ergebnisse")

    if TIMELINE_PNG_PATH.exists():
        st.image(str(TIMELINE_PNG_PATH), caption="car2x_timeline.png", use_container_width=True)
    else:
        st.info("Noch kein Timeline-PNG gefunden. Es wird beim Ausführen der Simulation automatisch erzeugt.")
else:
    st.info("Bitte starte die Simulation.")