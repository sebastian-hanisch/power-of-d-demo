"""Auswertung: Live-Lauf mit Fluid-, M/M/1- und Pooling-Vergleich, vorgerechnete Studie (N × ρ × d), Genauigkeit des Grenzwerts. Die
teure Studie (viele lange Läufe) steht vorgerechnet in `precomputed_sweep.json` (Generator: generate_precomputed.py, Laden:
`load_precomputed`)."""

import json
import math
from pathlib import Path

import pod_constants as C
import pod_formulas as F
from pod_simulation import simulate

PRECOMPUTED_PATH = Path(__file__).resolve().parent / "precomputed_sweep.json"


def mean_and_se(values):
    """Mittelwert und Standardfehler des Mittelwerts unabhängiger Wiederholungen (None bei nur einer)."""
    n = len(values)
    m = sum(values) / n
    if n < 2:
        return m, None
    var = sum((v - m) ** 2 for v in values) / (n - 1)
    return m, math.sqrt(var / n)


def live_report(n, rho, d, seed, customers=C.LIVE_CUSTOMERS):
    """Ein Live-Lauf (Wahl `d`) mit demselben Seed wie ein Bezugslauf ohne Wahl (d = 1), dazu die Formelwerte: Fluid-Grenzwert, M/M/1
    (d = 1), gemeinsame Schlange (Erlang C). Enthält auch die Schlangenlängen am Ende beider Läufe (Momentaufnahme)."""
    res, gate = simulate(n, rho, d, customers, seed, warm_fraction=C.WARMUP_FRACTION, return_gate=True)
    if d == 1:
        base, base_gate = res, gate
    else:
        base, base_gate = simulate(n, rho, 1, customers, seed, warm_fraction=C.WARMUP_FRACTION, return_gate=True)
    return {"sim": res, "base": base, "wait_sim": res.mean_wait, "wait_base": base.mean_wait, "wait_fluid": F.fluid_wait(rho, d),
            "wait_mm1": F.mm1_wait(rho), "wait_pooled": F.pooled_wait(n, rho), "idle_sim": res.idle_found_fraction(),
            "idle_fluid": F.prob_idle_found(rho, d), "tail_sim": res.tail, "tail_fluid": F.fluid_tail(rho, d),
            "tail_base_fluid": F.fluid_tail(rho, 1), "lens": list(gate.lens), "lens_base": list(base_gate.lens)}


def study_cell_run(n, rho, d, customers, seed, reps):
    """Eine Studienzelle: `reps` unabhängige Läufe (Seeds seed, seed + 1, …); Mittel und Standardfehler der Wartezeit, mittlere Schwanzanteile
    s_1 … s_K, Anteil Lkw mit freier Spur und die Auslastung."""
    runs = [simulate(n, rho, d, customers, seed + 1000 * r, warm_fraction=C.WARMUP_FRACTION) for r in range(reps)]
    wait, wait_se = mean_and_se([r.mean_wait for r in runs])
    idle, _ = mean_and_se([r.idle_found_fraction() for r in runs])
    util, _ = mean_and_se([r.utilisation for r in runs])
    tails = []
    for k in range(1, C.TAIL_LEVELS + 1):
        tails.append(sum(r.tail[k] if k < len(r.tail) else 0.0 for r in runs) / reps)
    return {"n": n, "rho": rho, "d": d, "reps": reps, "customers": customers, "wait": wait, "wait_se": wait_se,
            "waits": [r.mean_wait for r in runs], "idle": idle, "util": util, "tail": tails}


def load_precomputed():
    return json.loads(PRECOMPUTED_PATH.read_text(encoding="utf-8"))


def nearest(options, value):
    """Nächster Wert aus `options` (bei Gleichstand der kleinere)."""
    return min(options, key=lambda o: (abs(o - value), o))


def study_cell(pre, n, rho, d):
    for cell in pre["study"]:
        if cell["n"] == n and abs(cell["rho"] - rho) < 1e-9 and cell["d"] == d:
            return cell
    raise KeyError((n, rho, d))


def study_d(d):
    """Nächste in der Studie vorhandene Wahl (`D_OPTIONS` ist gleich `STUDY_D`)."""
    return d if d in C.STUDY_D else nearest(C.STUDY_D, d)
