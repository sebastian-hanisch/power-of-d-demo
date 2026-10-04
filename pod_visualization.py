"""Plotly-Abbildungen der Power-of-d-Demo: Schwanz der Schlangenlängen (Simulation gegen Fluid-Grenzwert), Wartezeit über die Zahl der
Auskünfte, Genauigkeit des Grenzwerts über die Gate-Größe, Abstand zur gemeinsamen Schlange. Achsen sind gesperrt (fixedrange),
damit Touch-Geräte beim Scrollen nicht zoomen."""

import plotly.graph_objects as go

import pod_constants as C
import pod_evaluation as E
import pod_formulas as F

SIM_COLOR = "#f58518"
FLUID_COLOR = "#4c78a8"
BASE_COLOR = "#9d9d9d"
POOL_COLOR = "#54a24b"
RHO_COLORS = {0.8: "#4c78a8", 0.9: "#e45756", 0.95: "#72b7b2"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.25, top=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=top, b=10), legend=dict(orientation="h", y=legend_y),
                      plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def d_label(d):
    """Lesbare Wahl: 1, 2, 3, 5, alle (JSQ)."""
    return "alle (JSQ)" if d >= C.D_ALL else str(d)


def d_name(d):
    """Legendenname: "d = 2" bzw. "alle (JSQ)"."""
    return "alle (JSQ)" if d >= C.D_ALL else f"d = {d}"


def d_phrase(d):
    """Satzteil: "eine Schlange", "2 Schlangen", "alle Schlangen"."""
    if d >= C.D_ALL:
        return "alle Schlangen"
    return "eine Schlange" if d == 1 else f"{d} Schlangen"


def _positive(values):
    return [v if v is not None and v > 0 else None for v in values]


def build_tail_chart(tail_sim, tail_fluid, tail_base, d):
    """Anteil s_k der Spuren mit mindestens k Lkw (logarithmisch): Simulation gegen Fluid-Grenzwert, dazu d = 1 als Bezug."""
    kmax = min(14, max(len(tail_sim), len(tail_fluid)) - 1)
    ks = list(range(0, kmax + 1))
    pad = lambda t: [t[k] if k < len(t) else 0.0 for k in ks]
    fig = go.Figure()
    if d != 1:
        fig.add_trace(go.Scatter(x=ks, y=_positive(pad(tail_base)), mode="lines", line=dict(color=BASE_COLOR, width=2, dash="dot"),
                                 name="ohne Wahl (d = 1, Grenzwert)"))
    fig.add_trace(go.Scatter(x=ks, y=_positive(pad(tail_fluid)), mode="lines", line=dict(color=FLUID_COLOR, width=2.5),
                             name=f"Grenzwert ({d_name(d)})"))
    fig.add_trace(go.Scatter(x=ks, y=_positive(pad(tail_sim)), mode="markers", marker=dict(color=SIM_COLOR, size=9),
                             name=f"Simulation ({d_name(d)})"))
    fig.update_xaxes(title_text="mindestens k Lkw in der Spur", dtick=1)
    fig.update_yaxes(title_text="Anteil der Spuren (logarithmisch)", type="log", range=[-6.5, 0.2], tickvals=[1e-6, 1e-4, 1e-2, 1],
                     ticktext=["10⁻⁶", "10⁻⁴", "0.01", "1"])
    return _base(fig, 340)


def build_choices_chart(pre, rho):
    """Wartezeit (Minuten, logarithmisch) über die Zahl der Auskünfte d: Linien = Grenzwert für drei Auslastungen, Punkte = Simulation
    mit 200 Spuren aus der Studie."""
    ds = list(range(1, 9))
    fig = go.Figure()
    for r in C.STUDY_RHO:
        ys = [F.to_minutes(F.fluid_wait(r, d)) for d in ds]
        fig.add_trace(go.Scatter(x=ds, y=ys, mode="lines", line=dict(color=RHO_COLORS[r], width=2.5, dash="solid" if r == rho else "dot"),
                                 name=f"Grenzwert, Auslastung {C.fmt_pct(r)}"))
        dots = [(d, E.study_cell(pre, 200, r, d)["wait"]) for d in C.STUDY_D if d < C.D_ALL]
        fig.add_trace(go.Scatter(x=[d for d, _ in dots], y=[F.to_minutes(w) for _, w in dots], mode="markers",
                                 marker=dict(color=RHO_COLORS[r], size=9, symbol="circle-open", line=dict(width=2)),
                                 name=f"Simulation 200 Spuren, {C.fmt_pct(r)}", showlegend=False))
    fig.update_xaxes(title_text="Schlangen, die jeder Lkw ansieht (d)", dtick=1)
    fig.update_yaxes(title_text="mittlere Wartezeit in Minuten (logarithmisch)", type="log")
    return _base(fig, 340, legend_y=-0.3)


def build_gap_chart(pre, rho):
    """Abweichung der Simulation vom Grenzwert (sim/Grenzwert − 1, in Prozent) über die Zahl der Spuren, für d = 2, 3, 5; Fehlerbalken =
    Standardfehler. Null heißt: Grenzwert trifft."""
    fig = go.Figure()
    colors = {2: "#e45756", 3: "#4c78a8", 5: "#54a24b"}
    for d in (2, 3, 5):
        xs, ys, errs = [], [], []
        for n in C.STUDY_N:
            cell = E.study_cell(pre, n, rho, d)
            fl = F.fluid_wait(rho, d)
            xs.append(n)
            ys.append(100 * (cell["wait"] / fl - 1))
            errs.append(100 * (cell["wait_se"] or 0.0) / fl)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=colors[d], width=2.5), error_y=dict(type="data", array=errs, visible=True),
                                 name=f"d = {d}"))
    fig.add_hline(y=0, line=dict(color=BASE_COLOR, dash="dash"))
    fig.update_xaxes(title_text="Zahl der Spuren N", type="log", tickvals=list(C.STUDY_N), ticktext=[str(n) for n in C.STUDY_N])
    fig.update_yaxes(title_text="Abweichung der Wartezeit vom Grenzwert (%)", ticksuffix=" %")
    return _base(fig, 340)


def build_pooling_chart(pre, n, rho):
    """Mittlere Wartezeit (Minuten, logarithmisch) bei der Studienzelle (n, ρ): d = 1, 2, 3, 5, alle (JSQ) gegen die gemeinsame Schlange."""
    labels = [d_name(d) for d in C.STUDY_D] + ["gemeinsame Schlange (Erlang C)"]
    waits = [F.to_minutes(E.study_cell(pre, n, rho, d)["wait"]) for d in C.STUDY_D] + [F.to_minutes(F.pooled_wait(n, rho))]
    colors = [BASE_COLOR] + [FLUID_COLOR] * (len(C.STUDY_D) - 1) + [POOL_COLOR]
    fig = go.Figure(go.Bar(x=labels, y=waits, marker_color=colors, text=[f"{w:.2f}" for w in waits], textposition="outside"))
    fig.update_yaxes(title_text="mittlere Wartezeit in Minuten (logarithmisch)", type="log")
    fig.update_xaxes(title_text="")
    return _base(fig, 340, top=20)


def build_snapshot_chart(lens, lens_base, d):
    """Momentaufnahme am Ende des Laufs: Schlangenlängen aller Spuren, absteigend sortiert (ohne Wahl gegen gewählte Regel)."""
    order = lambda v: sorted(v, reverse=True)
    xs = list(range(1, len(lens) + 1))
    fig = go.Figure()
    if d != 1:
        fig.add_trace(go.Scatter(x=xs, y=order(lens_base), mode="lines", line_shape="hv", line=dict(color=BASE_COLOR, width=2.5),
                                 name="ohne Wahl (d = 1)"))
    fig.add_trace(go.Scatter(x=xs, y=order(lens), mode="lines", line_shape="hv", line=dict(color=FLUID_COLOR, width=3),
                             name=d_name(d)))
    fig.update_xaxes(title_text="Spuren, nach Länge sortiert (längste links)")
    fig.update_yaxes(title_text="Lkw in der Spur (inkl. Abfertigung)", rangemode="tozero")
    return _base(fig, 340)
