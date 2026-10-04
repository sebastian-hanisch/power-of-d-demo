"""Power-of-d-Choices - welche Schlange? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Konzepte-Linie "Warteschlangentheorie und Simulation": Das Terminal-Gate hat N Spuren mit je eigener Schlange (nicht
eine gemeinsame wie in Stück 3). Jeder Lkw sieht sich d zufällige Schlangen an und reiht sich in die kürzeste ein. Die Demo vergleicht
Simulation und Fluid-Grenzwert und zeigt, wie viel jede weitere Auskunft bringt, ab wie vielen Spuren der Grenzwert trägt und wie weit
die gemeinsame Schlange noch voraus ist. Siehe README für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import pod_constants as C
import pod_formulas as F
from pod_evaluation import live_report, load_precomputed, nearest, study_cell
from pod_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from pod_visualization import (build_choices_chart, build_gap_chart, build_pooling_chart, build_snapshot_chart, build_tail_chart,
                               d_label, d_phrase)

st.set_page_config(page_title="Power-of-d-Choices – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _precomputed():
    return load_precomputed()


@st.cache_data(show_spinner=False)
def _live(n, rho, d, seed):
    return live_report(n, rho, d, seed)


def _min(x):
    """Zeit in Abfertigungsdauern → Text in Minuten."""
    return f"{F.to_minutes(x):.2f} min"


st.title("🚚 Power-of-d-Choices: welche Schlange?")
st.markdown(
    """
In Stück 3 standen alle Lkw in **einer gemeinsamen Schlange** vor den Spuren, das beste Ergebnis, das ein Gate mit gleichen Spuren
erreichen kann. Viele Anlagen haben aber **eine Schlange je Spur**, und der Lkw muss sich entscheiden. **Zufällig** zu wählen ist
schlecht: Manche Spuren laufen über, andere stehen leer. **Alle** Schlangen anzusehen ist teuer. Der Kompromiss heißt
**Power-of-d-Choices**: Der Lkw sieht sich nur **d zufällig gewählte Schlangen** an und nimmt die kürzeste. Schon **d = 2** verändert das
Gate qualitativ, jede weitere Auskunft bringt weniger.
"""
)
st.caption(
    "Siebtes Stück der Linie „Warteschlangentheorie und Simulation“, aufbauend auf "
    "[mmc-queue-demo](https://sebastianhanisch-mmc-queue-demo.streamlit.app/) (eine gemeinsame Schlange, Erlang C) und "
    "[mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/) (je Spur eine M/M/1-Schlange). Jedes Folgestück hebt eine "
    "der Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So funktioniert die Wahlregel", expanded=True):
    st.markdown(
        """
- **Gate:** N Spuren mit je eigener Schlange (FIFO). Lkw kommen insgesamt mit der Rate N·ρ an, jede Spur fertigt exponentiell ab (Mittel
  3 min), ρ ist die Auslastung je Spur.
- **Wahlregel:** Jeder Lkw zieht d Spuren **zufällig mit Zurücklegen**, sieht sich deren Schlangenlängen an und reiht sich in die
  kürzeste ein (bei Gleichstand in die zuerst angesehene). **d = 1** ist zufällige Zuteilung, **„alle (JSQ)“** heißt: die kürzeste aller
  Schlangen (*Join the Shortest Queue*).
- **Grenzwert für viele Spuren:** Der Anteil sₖ der Spuren mit mindestens k Lkw erfüllt im Gleichgewicht sₖ = ρ·sₖ₋₁ᵈ. Für d = 1 fällt
  er nur exponentiell (ρᵏ), für d ≥ 2 **doppelt exponentiell**. Mit dem Gesetz von Little folgt die mittlere Wartezeit.
- **Simulation:** Ereignisse für Ankunft und Abgang, eigene Schlange je Spur, die ersten 20 % der Lkw werden nicht ausgewertet.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{name}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n = st.select_slider("Zahl der Spuren N", options=C.N_OPTIONS, key="n_select",
                         help="So viele Spuren hat das Gate, jede mit eigener Schlange.")
    rho_pct = st.slider("Auslastung ρ je Spur", *bounds("rho_slider"), step=C.RHO_PCT_STEP, key="rho_slider", format="%d %%",
                        help="Anteil der Zeit, in der eine Spur im Mittel beschäftigt ist.")
    d = st.select_slider("Schlangen, die jeder Lkw ansieht (d)", options=C.D_OPTIONS, key="d_select", format_func=d_label,
                         help="1 = zufällige Zuteilung, 2 = zwei ansehen und die kürzere nehmen, alle = die kürzeste aller Schlangen.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt alle Zufallszahlen der Simulation.")
    st.button("🎲 Neuen Lauf würfeln", on_click=randomize_seed)

n, rho_pct, d, seed = int(n), int(rho_pct), int(d), int(seed)
rho = rho_pct / 100.0
sync_query_params({"n_select": n, "rho_slider": rho_pct, "d_select": d, "seed_input": seed})

pre = _precomputed()
study_n, study_rho = nearest(C.STUDY_N, n), nearest(C.STUDY_RHO, rho)
with st.spinner("Simuliere das Gate …"):
    live = _live(n, rho, d, seed)

st.markdown("---")
st.markdown("## 🚚 Eine Schlange je Spur")
st.caption(
    f"{n} Spuren, Auslastung {C.fmt_pct(rho)}, jeder Lkw sieht sich {d_phrase(d)} an. Simuliert: {C.fmt_int(C.LIVE_CUSTOMERS)} Lkw "
    f"(die ersten {C.fmt_pct(C.WARMUP_FRACTION)} nicht ausgewertet)."
)
r1 = st.columns(3)
r1[0].metric("Mittlere Wartezeit (Simulation)", _min(live["wait_sim"]))
r1[1].metric("Mittlere Wartezeit (Grenzwert für viele Spuren)", _min(live["wait_fluid"]),
             help="Fluid-Grenzwert (N → ∞) der Wahlregel; bei „alle (JSQ)“ null.")
r1[2].metric("Ohne Wahl (d = 1, Formel M/M/1)", _min(live["wait_mm1"]), help="Jede Spur ist eine eigene M/M/1-Schlange, unabhängig von N.")
r2 = st.columns(3)
r2[0].metric("Gemeinsame Schlange (Erlang C, Stück 3)", _min(live["wait_pooled"]),
             help="Alle Lkw in einer Schlange vor denselben Spuren: die Grenze dessen, was Wählen erreichen kann.")
r2[1].metric("Lkw, die eine freie Spur finden (Simulation)", C.fmt_pct(live["idle_sim"], 1),
             help=f"Grenzwert: 1 − ρ^d = {C.fmt_pct(live['idle_fluid'], 1)}.")
if live["wait_fluid"] > 0:
    r2[2].metric("Wartezeit-Verhältnis gegenüber d = 1 (Grenzwert)", f"1 : {F.improvement_factor(rho, 1, d):.1f}" if d > 1 else "1 : 1")
else:
    r2[2].metric("Wartezeit-Verhältnis gegenüber d = 1 (Grenzwert)", "Wartezeit null")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Wie lang sind die Schlangen? (Anteil der Spuren mit mindestens k Lkw)**")
    st.plotly_chart(build_tail_chart(live["tail_sim"], live["tail_fluid"], live["tail_base_fluid"], d), width="stretch",
                    key=f"tail_{n}_{rho}_{d}_{seed}")
with col_b:
    st.markdown("**Momentaufnahme am Ende des Laufs (gleiche Zufallszahlen)**")
    st.plotly_chart(build_snapshot_chart(live["lens"], live["lens_base"], d), width="stretch", key=f"snap_{n}_{rho}_{d}_{seed}")
st.info(
    f"Sieht sich jeder Lkw {d_phrase(d)} an, warten die Lkw im Mittel **{_min(live['wait_sim'])}**; ohne Wahl wären es **{_min(live['wait_mm1'])}** "
    f"(Formel), mit einer gemeinsamen Schlange {_min(live['wait_pooled'])}. {C.fmt_pct(live['idle_sim'], 1)} der Lkw finden eine freie Spur "
    f"(Grenzwert {C.fmt_pct(live['idle_fluid'], 1)})."
)
st.caption(
    f"Ein Live-Lauf ist kurz ({C.fmt_int(C.LIVE_CUSTOMERS)} Lkw): Die tatsächliche Auslastung dieses Laufs beträgt "
    f"{C.fmt_pct(live['sim'].utilisation, 1)} statt {C.fmt_pct(rho)}, und schon ein Prozentpunkt verschiebt Wartezeit und Anteil freier Spuren "
    "spürbar; bei hoher Auslastung und d = 1 streut die Wartezeit eines einzelnen Laufs um Zehntel des Wertes. Die Studien unten mitteln "
    "je vier lange Läufe."
)

st.markdown("---")
st.subheader("📐 Wie viel bringt jede weitere Auskunft?")
st.markdown(
    "Mittlere Wartezeit im Grenzwert für viele Spuren (Linien, exakt aus der Rekursion) und in der Simulation mit 200 Spuren (Kreise), für "
    "drei Auslastungen. Die gewählte Auslastung ist durchgezogen."
)
st.plotly_chart(build_choices_chart(pre, rho), width="stretch", key=f"choices_{rho}")
rows = [f"| {d_label(x)} | {_min(F.fluid_wait(rho, x))} | "
        f"{('1 : ' + format(F.improvement_factor(rho, 1, x), '.1f')) if 1 < x < C.D_ALL else ('1 : 1' if x == 1 else 'Wartezeit null')} | "
        f"{C.fmt_pct(F.prob_idle_found(rho, x), 1)} |" for x in C.D_OPTIONS]
st.markdown("| Auskünfte d | Wartezeit (Grenzwert) | Verhältnis gegenüber d = 1 | Lkw mit freier Spur |\n|---|---|---|---|\n" + "\n".join(rows))
w1, w2, w3 = F.fluid_wait(rho, 1), F.fluid_wait(rho, 2), F.fluid_wait(rho, 3)
st.info(
    f"Bei Auslastung {C.fmt_pct(rho)}: von d = 1 auf d = 2 sinkt die Wartezeit im Grenzwert von {_min(w1)} auf {_min(w2)} "
    f"(Faktor {w1 / w2:.1f}); von d = 2 auf d = 3 auf {_min(w3)} (Faktor {w2 / w3:.1f}). Die erste zusätzliche Auskunft bringt am meisten."
)

st.markdown("---")
st.subheader("🔬 Ab wie vielen Spuren trägt der Grenzwert?")
st.markdown(
    f"Abweichung der simulierten Wartezeit vom Grenzwert für 10, 50 und 200 Spuren bei Auslastung {C.fmt_pct(study_rho)}; Fehlerbalken = "
    f"Standardfehler. Je Zelle {pre['study_reps']} Läufe à {C.fmt_int(pre['study_customers'])} Lkw."
)
st.plotly_chart(build_gap_chart(pre, study_rho), width="stretch", key=f"gap_{study_rho}")
header = "| d | " + " | ".join(f"{k} Spuren" for k in C.STUDY_N) + " |\n|---|" + "---|" * len(C.STUDY_N) + "\n"
body = ""
for x in (2, 3, 5):
    fl = F.fluid_wait(study_rho, x)
    body += f"| {x} | " + " | ".join(f"{100 * (study_cell(pre, k, study_rho, x)['wait'] / fl - 1):+.0f} %" for k in C.STUDY_N) + " |\n"
st.markdown(header + body)
g10 = study_cell(pre, 10, study_rho, 2)["wait"] / F.fluid_wait(study_rho, 2) - 1
g200 = study_cell(pre, 200, study_rho, 2)["wait"] / F.fluid_wait(study_rho, 2) - 1
st.info(
    f"Bei Auslastung {C.fmt_pct(study_rho)} und d = 2 liegt die simulierte Wartezeit mit 10 Spuren {100 * g10:+.0f} % und mit 200 Spuren "
    f"{100 * g200:+.0f} % neben dem Grenzwert: ein kleines Gate wartet länger, als die Formel für viele Spuren sagt."
)

st.markdown("---")
st.subheader("🔬 Wie weit ist die gemeinsame Schlange noch voraus?")
st.markdown(
    f"Mittlere Wartezeit bei {study_n} Spuren und Auslastung {C.fmt_pct(study_rho)}: zufällige Zuteilung, 2, 3, 5 Auskünfte, alle "
    "Schlangen (JSQ) und die gemeinsame Schlange aus Stück 3."
)
st.plotly_chart(build_pooling_chart(pre, study_n, study_rho), width="stretch", key=f"pool_{study_n}_{study_rho}")
cells = {x: study_cell(pre, study_n, study_rho, x) for x in C.STUDY_D}
st.info(
    f"Bei {study_n} Spuren und Auslastung {C.fmt_pct(study_rho)}: zufällig {_min(cells[1]['wait'])}, zwei Auskünfte {_min(cells[2]['wait'])}, "
    f"alle Schlangen {_min(cells[C.D_ALL]['wait'])}, gemeinsame Schlange {_min(F.pooled_wait(study_n, study_rho))}. Auch wer jede Schlange "
    "kennt, schlägt die gemeinsame Schlange nicht: ein Lkw, der sich einmal eingereiht hat, bleibt dort, auch wenn nebenan eine Spur frei wird."
)

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Auskunft ist sofort und kostenlos** | Jede Nachfrage ist eine Nachricht, und eine veraltete Auskunft lässt viele Lkw dieselbe „kürzeste“ Schlange wählen (Herdenverhalten). Hier sehen alle den aktuellen Stand. | kein Folgestück |
| **Abfertigungsdauer exponentiell, alle Spuren gleich schnell** | Die Wartezeit hängt von der Streuung der Dauer ab; bei ungleich schnellen Spuren verschiebt sich die beste Wahl. | **[M/G/1, Kingman-Näherung](https://sebastianhanisch-mg1-kingman-demo.streamlit.app/)** |
| **Lkw wechseln die Schlange nicht** | Wer umsteigt, sobald nebenan eine Spur frei wird, nähert sich der gemeinsamen Schlange an. | kein Folgestück |
| **Alle Lkw gleich wichtig** | Eilige Lkw brauchen Vorfahrt; das verschiebt die Wartezeit zwischen den Klassen. | **[Prioritätsklassen](https://sebastianhanisch-priority-queue-demo.streamlit.app/)** |
| **Unbegrenzte Schlange** | Mit begrenzten Stellplätzen gehen Lkw verloren, wenn alle angesehenen Schlangen voll sind. | **[M/M/c/c (Erlang B)](https://sebastianhanisch-erlang-b-demo.streamlit.app/)** |
| **Konstante Ankunftsrate** | Echte Gates haben Wellen; die Wahlregel muss dann zu jeder Zeit mit der aktuellen Spurzahl funktionieren. | **[Zeitvariable Ankünfte](https://sebastianhanisch-time-varying-arrivals-demo.streamlit.app/)** |
| **Ein Gate** | Wellen und Wartezeiten laufen durch mehrere Stationen (Gate, Kran, Stapel). | **Jackson-Netze** (Folgestück) |
"""
)
st.caption(
    "Verwandt im Portfolio: [mmc-queue-demo](https://sebastianhanisch-mmc-queue-demo.streamlit.app/) (Stück 3: eine gemeinsame Schlange, "
    "der Grenzfall dieser Demo), [mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/) (Stück 1: eine Spur, die "
    "Schlange bei d = 1), [erlang-a-demo](https://sebastianhanisch-erlang-a-demo.streamlit.app/) (Stück 4: gemeinsame Schlange mit "
    "Abwanderung) und die Hafen-Demo [truck-appointment-demo](https://sebastianhanisch-truck-appointment-demo.streamlit.app/) "
    "(Terminvergabe für Lkw: dort planen Termine die Ankünfte, hier wählen die Lkw ihre Schlange)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** $N$ Spuren, je eine FIFO-Schlange, Ankunftsrate $N\rho$ (Poisson), exponentielle Abfertigung mit Mittel 1. Ein Lkw zieht
$d$ Spuren gleichverteilt **mit Zurücklegen** und reiht sich in die kürzeste ein (bei Gleichstand in die zuerst gezogene); $d = 1$ ist
zufällige Zuteilung, $d \ge N$ steht hier für „alle ansehen, unter den kürzesten zufällig wählen“ (JSQ).

**Fluid-Grenzwert** ($N \to \infty$). Sei $s_k$ der Anteil der Spuren mit mindestens $k$ Lkw. Im Gleichgewicht gilt
$$s_k = \rho\, s_{k-1}^{\,d}, \quad s_0 = 1, \qquad\text{also}\qquad s_k = \rho^{(d^k - 1)/(d - 1)}\ (d \ge 2),\quad s_k = \rho^k\ (d = 1).$$
Für $d \ge 2$ fällt $s_k$ doppelt exponentiell. Mit dem Gesetz von Little ($L/N = \sum_{k \ge 1} s_k$, Ankunftsrate $\rho$ je Spur) ist die
mittlere Verweilzeit $W = \frac{1}{\rho}\sum_{k \ge 1} s_k$ und die mittlere Wartezeit $W - 1$. Der Anteil der Lkw, die eine freie Spur
finden, ist $1 - \rho^{d}$.

**Gemeinsame Schlange** (Stück 3, $M/M/N$): $W_q = C(N, N\rho)/\bigl(N(1-\rho)\bigr)$ mit der Erlang-C-Formel.

**Simulation.** Ereignisse Ankunft und Abgang, Abgänge in einem Heap, je Spur eine Warteschlange der Ankunftszeiten; Zeitintegrale der
Lkw im System und der Spuren mit mindestens $k$ Lkw (Zeitmittel für $s_k$), Wartezeit je begonnener Abfertigung. Gegenproben: das Gesetz
von Little gilt entlang jedes Pfades exakt, und für $N = 2, 3$ stimmen die Mittel mit der gelösten Markov-Kette über alle Längenvektoren
überein.

Implementiert in `pod_formulas.py` (Grenzwert, Erlang C), `pod_simulation.py` (Wahlregel, Ereignisschleife), `pod_evaluation.py`
(Live-Lauf, Studienzelle), `generate_precomputed.py` (vorgerechnete Studie).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html))."
)
