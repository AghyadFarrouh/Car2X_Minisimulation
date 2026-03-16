
"""
car2x_timeline.py
------------------
Zeigt die Car2X-Nachrichtenwirkung als **visuelle Timeline** (YIELDING vs. NORMAL je Fahrzeug)
auf Basis des von der Minisimulation erzeugten Logs `car2x_log.csv`.

Nutzung:
    python car2x_timeline.py [pfad_zur_csv]

Ergebnis:
    - car2x_timeline.png  (horizontale Timeline je Fahrzeug)
    - optional: car2x_timeline.html (interaktive Plotly-Version, falls Paket verfügbar)

Hinweis:
    Das CSV enthält Zustände je Zeitschritt (t, vehicle_id, state). Die Timeline gruppiert
    zusammenhängende Abschnitte gleicher Zustände zu farbigen Balken (NORMAL / YIELDING).
    Damit visualisieren wir **die Wirkung** der PRIORITY-Broadcasts (YIELDING-Phasen),
    auch wenn die einzelnen Nachrichten im CSV nicht separat geloggt sind.
"""

import sys
import os
import math
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Farben für Zustände
COLOR_MAP = {
    'NORMAL': '#4c78a8',   # Blau
    'YIELDING': '#f58518'  # Orange
}


def _segment_state_intervals(df):
    """Für jedes Fahrzeug zusammenhängende Zeitintervalle je Zustand bestimmen.

    Returns: dict(vehicle_id -> list of dict(start, end, state))
    """
    intervals = defaultdict(list)

    for vid, g in df.sort_values(['vehicle_id', 't']).groupby('vehicle_id'):
        current_state = None
        start_t = None
        last_t = None
        dt = None

        # dt heuristisch bestimmen (Differenz der ersten beiden Zeitstempel)
        t_values = g['t'].values
        if len(t_values) >= 2:
            dt = round(float(t_values[1] - t_values[0]), 10)
        else:
            dt = 0.5  # Fallback

        for _, row in g.iterrows():
            t = float(row['t'])
            state = str(row['state'])

            if current_state is None:
                current_state = state
                start_t = t
                last_t = t
                continue

            if state != current_state:
                # Intervall abschließen bis zur Mitte zwischen last_t und t; praktikabler: bis t
                end_t = last_t + (dt if dt else 0)
                intervals[vid].append({'start': start_t, 'end': end_t, 'state': current_state})
                current_state = state
                start_t = t

            last_t = t

        # letztes Intervall schließen
        if start_t is not None:
            end_t = (last_t + (dt if dt else 0))
            intervals[vid].append({'start': start_t, 'end': end_t, 'state': current_state})

    return intervals


def plot_timeline(df, out_png='car2x_timeline.png'):
    intervals = _segment_state_intervals(df[df['type'] != 'EV'])  # nur normale Fahrzeuge
    vehicles = sorted(intervals.keys(), key=lambda x: int(x.split('-')[-1]) if '-' in x else x)

    fig, ax = plt.subplots(figsize=(12, 0.6*max(6, len(vehicles))))

    ytick_pos = []
    ytick_labels = []

    y_base = 10
    height = 6
    gap = 6

    for i, vid in enumerate(vehicles):
        y = y_base + i * (height + gap)
        ytick_pos.append(y + height/2)
        ytick_labels.append(vid)

        segs = []
        colors = []
        for seg in intervals[vid]:
            start = seg['start']
            duration = seg['end'] - seg['start']
            if duration <= 0:
                continue
            segs.append( (start, duration) )
            colors.append(COLOR_MAP.get(seg['state'], '#888888'))

        if segs:
            ax.broken_barh(segs, (y, height), facecolors=colors, edgecolors='none')

    # Achsen & Styling
    ax.set_xlabel('Zeit (s)')
    ax.set_yticks(ytick_pos)
    ax.set_yticklabels(ytick_labels)
    ax.set_title('Car2X – Visuelle Timeline der Zustände (YIELDING vs. NORMAL)')
    ax.grid(True, axis='x', alpha=0.3)

    # Legende
    from matplotlib.patches import Patch
    legend_patches = [Patch(color=COLOR_MAP['NORMAL'], label='NORMAL'),
                      Patch(color=COLOR_MAP['YIELDING'], label='YIELDING')]
    ax.legend(handles=legend_patches, loc='upper right')

    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close(fig)
    return out_png


def plot_timeline_interactive(df, out_html='car2x_timeline.html'):
    try:
        import plotly.express as px
        import plotly.io as pio
    except Exception:
        return None

    # Intervalltabelle bauen
    intervals = _segment_state_intervals(df[df['type'] != 'EV'])
    rows = []
    for vid, segs in intervals.items():
        for seg in segs:
            rows.append({
                'vehicle_id': vid,
                'Start': seg['start'],
                'Ende': seg['end'],
                'Zustand': seg['state']
            })

    tdf = pd.DataFrame(rows)
    if tdf.empty:
        return None

    fig = px.timeline(
        tdf,
        x_start='Start', x_end='Ende', y='vehicle_id', color='Zustand',
        color_discrete_map={'NORMAL': '#4c78a8', 'YIELDING': '#f58518'}
    )
    fig.update_layout(
        title='Car2X – Visuelle Timeline (interaktiv)',
        xaxis_title='Zeit (s)', yaxis_title='Fahrzeug',
        legend_title='Zustand', height=max(400, 40*len(tdf['vehicle_id'].unique()))
    )

    pio.write_html(fig, file=out_html, include_plotlyjs='cdn', full_html=True)
    return out_html


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'car2x_log.csv'
    if not os.path.exists(csv_path):
        print(f"CSV nicht gefunden: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # Basistimeline (PNG)
    png = plot_timeline(df)
    print('PNG geschrieben:', png)

    # Interaktive Version (optional)
    html = plot_timeline_interactive(df)
    if html:
        print('HTML geschrieben:', html)
    else:
        print('Plotly nicht installiert – HTML wird übersprungen.')

if __name__ == '__main__':
    main()
