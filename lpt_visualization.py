"""Plotly-Abbildungen der LPT-Demo: Auftragsübersicht, Mehrzeilen-Gantt (eine Zeile je Maschine), Maschinenlast-
Vergleich, Sweep, Timing. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen.

Das Mehrzeilen-Gantt baut EIN Trace JE MASCHINE mit `base`-Array je Auftrag, nicht einen Trace je Auftrag -
mit vielen Einzel-Traces auf wenigen Kategoriewerten teilt Plotlys Default-Gruppierung sonst die Zeilenhöhe
durch die Trace-Zahl auf (gefunden in `johnson-rule-demo`, siehe
[[feedback_plotly_many_traces_per_category_shrinks_bars]] - hier von Anfang an richtig gebaut)."""

import numpy as np
import plotly.graph_objects as go

JOB_COLOR = "#4c78a8"
MACHINE_COLORS = ["#4c78a8", "#54a24b", "#e45756", "#f58518", "#b279a2", "#9c755f"]
ARB_COLOR = "#e45756"
RANDOM_COLOR = "#7f7f7f"
SETUP_COLOR = "#f58518"
BOUND_COLOR = "#54a24b"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_jobs_chart(p):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(range(len(p))), y=p.tolist(), marker_color=JOB_COLOR, hovertemplate="Auftrag %{x}<br>Dauer %{y}<extra></extra>"))
    fig.update_xaxes(title_text="Auftrag (unsortiert)")
    fig.update_yaxes(title_text="Bearbeitungszeit")
    return _base(fig, 260)


def build_machine_gantt(p, machine, completion, m, upto=None):
    """EIN Trace je Maschine (siehe Moduldocstring) - Lücken entstehen durch eine Rüstzeit beim
    Familienwechsel auf derselben Maschine (Vehikel B)."""
    n = len(p)
    upto = n if upto is None else upto
    order_by_completion = np.argsort(completion)          # Einplanungsreihenfolge je Maschine ergibt sich aus der Fertigstellung
    included = set(order_by_completion[:upto].tolist())
    fig = go.Figure()
    rows = [f"Maschine {k + 1}" for k in range(m)]
    for k in range(m):
        jobs_k = [j for j in range(n) if machine[j] == k and j in included]
        jobs_k.sort(key=lambda j: completion[j])
        if not jobs_k:
            continue
        starts = [float(completion[j] - p[j]) for j in jobs_k]
        durations = [float(p[j]) for j in jobs_k]
        fig.add_trace(go.Bar(x=durations, y=[rows[k]] * len(jobs_k), base=starts, orientation="h", width=0.6,
                              marker=dict(color=MACHINE_COLORS[k % len(MACHINE_COLORS)], line=dict(width=1, color="white")),
                              customdata=jobs_k, showlegend=False, hovertemplate="Auftrag %{customdata}<br>Dauer %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Zeit")
    fig.update_yaxes(categoryorder="array", categoryarray=rows, autorange="reversed")
    return _base(fig, max(160, 40 * m))


def build_load_comparison(lpt_loads, arb_loads):
    """Endlast je Maschine - LPT gegen dieselbe Zuweisung ohne Sortierung. Cmax ist die HÖCHSTE Last je
    Gruppe - zeigt direkt, warum eine ausgeglichenere Verteilung eine niedrigere Gesamtdurchlaufzeit bedeutet."""
    m = len(lpt_loads)
    machines = [f"M{k + 1}" for k in range(m)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=machines, y=lpt_loads.tolist(), name="LPT", marker_color=JOB_COLOR))
    fig.add_trace(go.Bar(x=machines, y=arb_loads.tolist(), name="Beliebige Reihenfolge", marker_color=ARB_COLOR))
    fig.add_hline(y=float(lpt_loads.max()), line=dict(color=JOB_COLOR, width=1.5, dash="dot"))
    fig.add_hline(y=float(arb_loads.max()), line=dict(color=ARB_COLOR, width=1.5, dash="dot"))
    fig.update_xaxes(title_text="Maschine")
    fig.update_yaxes(title_text="Endlast")
    fig.update_layout(barmode="group")
    return _base(fig, 320)


def build_sweep(rows, param_label, value_key="value", y_keys=(("gap_arbitrary", "LPT gegen beliebige Reihenfolge", ARB_COLOR), ("gap_random", "LPT gegen Zufall", RANDOM_COLOR))):
    xs = [r[value_key] for r in rows]
    fig = go.Figure()
    for key, name, color in y_keys:
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines+markers", line=dict(color=color, width=2.5), name=name))
    fig.update_xaxes(title_text=param_label)
    fig.update_yaxes(title_text="Abstand zu LPT (%)")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 360)


def build_timing(rows):
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["exact_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=ARB_COLOR, width=2.5), name="CP-SAT (Zeitlimit, im schlimmsten Fall exponentiell)"))
    fig.add_trace(go.Scatter(x=xs, y=[r["lpt_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=JOB_COLOR, width=2.5), name="LPT (O(n log n))"))
    fig.update_xaxes(title_text="Aufträge")
    fig.update_yaxes(title_text="Rechenzeit (ms)", type="log")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 340)


def build_setup_gap(rows):
    xs = [r["value"] for r in rows]
    upper = [r["gap_max"] for r in rows]
    lower = [r["gap_min"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=upper + lower[::-1], fill="toself", fillcolor="rgba(245,133,24,0.15)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=[r["gap_mean"] for r in rows], mode="lines+markers", line=dict(color=SETUP_COLOR, width=2.5), name="LPT über dem echten Optimum (CP-SAT)"))
    fig.update_xaxes(title_text="Rüstzeit je Familienwechsel (Minuten)")
    fig.update_yaxes(title_text="Abstand zum Optimum (%)")
    return _base(fig, 340)


def build_graham_chart(rows, m):
    """Beobachtetes Verhältnis LPT/Optimum je n (bei fester Maschinenzahl m) gegen Grahams bewiesene Schranke -
    der Beweis-Check dieses Stücks: die beobachteten Punkte müssen IMMER unter der Schranke bleiben."""
    filtered = [r for r in rows if r["m"] == m]
    xs = [r["n"] for r in filtered]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["worst_ratio"] for r in filtered], mode="lines+markers", line=dict(color=JOB_COLOR, width=2.5), name="Schlechtestes beobachtetes LPT/Optimum"))
    fig.add_trace(go.Scatter(x=xs, y=[r["bound"] for r in filtered], mode="lines", line=dict(color=BOUND_COLOR, width=2, dash="dash"), name=f"Grahams Schranke (4/3 - 1/(3·{m}))"))
    fig.update_xaxes(title_text="Aufträge")
    fig.update_yaxes(title_text="Verhältnis zum Optimum")
    return _base(fig, 340)
