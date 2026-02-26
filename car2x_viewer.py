import streamlit as st
import pandas as pd
import altair as alt
import subprocess
import sys
from pathlib import Path

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
st.write("Visualisierung der Log-Daten aus der Car2X-Python-Simulation.")

# determine project root (directory of this file)
ROOT = Path(__file__).resolve().parent

# session storage for dataframe
if "df" not in st.session_state:
    st.session_state.df = None

# Toolbar: run simulation or load local CSV
col1, col2 = st.columns(2)
with col1:
    if st.button("Run simulation (car2x_simulation.py)"):
        sim_path = ROOT / "car2x_simulation.py"
        try:
            subprocess.run([sys.executable, str(sim_path)], check=True, capture_output=True, text=True)
            log_path = ROOT / "car2x_log.csv"
            if log_path.exists():
                st.session_state.df = pd.read_csv(log_path)
                st.success("Simulation ausgeführt und car2x_log.csv geladen.")
            else:
                st.warning(f"Simulation beendet, aber {log_path.name} nicht gefunden.")
        except subprocess.CalledProcessError as e:
            st.error(f"Fehler beim Ausführen der Simulation: {e}")
            if e.stdout:
                st.text(e.stdout)
            if e.stderr:
                st.text(e.stderr)

with col2:
    if st.button("Load local car2x_log.csv"):
        log_path = ROOT / "car2x_log.csv"
        if log_path.exists():
            st.session_state.df = pd.read_csv(log_path)
            st.success("Lokale car2x_log.csv geladen.")
        else:
            st.error(f"Lokale Datei nicht gefunden: {log_path}")

# Also allow manual upload
uploaded = st.file_uploader("Oder lade eine CSV-Datei hoch", type=["csv"])
if uploaded:
    st.session_state.df = pd.read_csv(uploaded)

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
    st.info("Bitte lade zuerst die Datei `car2x_log.csv` hoch oder starte die Simulation.")