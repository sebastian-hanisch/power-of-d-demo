"""Simulation: Wahlregel einzeln (von Hand), Mini-Instanz von Hand gerechnet, Little als exakte Pfad-Identität, Invarianten, Vergleich gegen
die unabhängige Markov-Kette (N = 2 und 3) und gegen M/M/1."""

import pytest

import pod_constants as C
import pod_formulas as F
import pod_simulation as S
from conftest import ScriptedRng
from ctmc_reference import exact_mean_wait, policy_probabilities


# ---------------------------------------------------------------- Einheit: Wahlregel

def test_choose_queue_picks_the_shorter_of_two_samples():
    """4 Spuren mit Längen [3, 1, 2, 0]; Zufall 0.1 → Spur 0, 0.6 → Spur 2: Spur 2 (Länge 2) ist kürzer als Spur 0 (Länge 3)."""
    assert S.choose_queue([3, 1, 2, 0], 2, ScriptedRng(uniform_values=[0.1, 0.6])) == 2


def test_choose_queue_keeps_the_first_sample_on_a_tie_and_may_pick_the_same_lane_twice():
    assert S.choose_queue([2, 2, 2, 2], 2, ScriptedRng(uniform_values=[0.3, 0.8])) == 1              # Gleichstand: zuerst angesehen
    assert S.choose_queue([5, 0, 5, 5], 3, ScriptedRng(uniform_values=[0.3, 0.3, 0.3])) == 1         # dreimal dieselbe Spur (Zurücklegen)


def test_choose_queue_with_replacement_can_miss_the_idle_lane():
    """Länge der angesehenen Spuren 5 und 5: die leere Spur 1 wird nicht gesehen, also nicht gewählt."""
    assert S.choose_queue([5, 0, 5, 5], 2, ScriptedRng(uniform_values=[0.0, 0.8])) == 0              # Spuren 0 und 3, Gleichstand: zuerst gesehen
    assert S.choose_queue([5, 0, 5, 5], 2, ScriptedRng(uniform_values=[0.0, 0.3])) == 1              # Spuren 0 und 1: die leere gewinnt


def test_choose_queue_d_one_takes_the_first_sample():
    assert S.choose_queue([9, 0, 9], 1, ScriptedRng(uniform_values=[0.0])) == 0


def test_choose_queue_all_picks_uniformly_among_the_shortest():
    """JSQ: Längen [2, 0, 0, 3] → kürzeste sind Spuren 1 und 2; Zufall 0.5 wählt den zweiten Kandidaten (Spur 2), 0.0 den ersten."""
    assert S.choose_queue([2, 0, 0, 3], C.D_ALL, ScriptedRng(uniform_values=[0.5])) == 2
    assert S.choose_queue([2, 0, 0, 3], C.D_ALL, ScriptedRng(uniform_values=[0.0])) == 1
    assert S.choose_queue([2, 0, 0, 3], 4, ScriptedRng(uniform_values=[0.0])) == 1                   # d ≥ n ist JSQ


def test_choose_queue_uses_every_lane_equally_often():
    rng = S.SplitMix64(5)
    hits = [0] * 5
    for _ in range(50_000):
        hits[S.choose_queue([0] * 5, 2, rng)] += 1
    assert all(abs(h - 10_000) < 400 for h in hits)


# ---------------------------------------------------------------- Mini-Instanz von Hand

def test_hand_computed_mini_instance(jsq_mini_streams):
    """Siehe conftest: 2 Spuren, JSQ, vier Lkw. Ankünfte 1.0, 1.5, 1.8, 2.5; Lkw 3 wartet 0.2. Integrale über [0, 2.5]:
    Lkw im System 0 / 1 / 2 / 3 / 2 / 1 auf 1.0 / 0.5 / 0.3 / 0.2 / 0.2 / 0.3 → ∫ = 0.5 + 0.6 + 0.6 + 0.4 + 0.3 = 2.4;
    beschäftigte Spuren 0.5 + 0.6 + 0.4 + 0.4 + 0.3 = 2.2 (Auslastung 2.2/5 = 0.44); Spuren mit ≥ 2 Lkw: 0.2 (s_2 = 0.2/5 = 0.04)."""
    res, g = S.simulate(2, 0.5, 2, 4, seed=0, warm_fraction=0.0, rngs=jsq_mini_streams, return_gate=True)
    assert (res.arrivals, res.found_idle) == (4, 3)
    assert res.horizon == pytest.approx(2.5) and g.wait_n == 4 and g.wait_sum == pytest.approx(0.2)
    assert res.mean_wait == pytest.approx(0.05)
    assert g.area_jobs == pytest.approx(2.4) and res.mean_jobs == pytest.approx(0.96)
    assert res.utilisation == pytest.approx(0.44) and res.tail[1] == pytest.approx(0.44) and res.tail[2] == pytest.approx(0.04)
    assert g.sojourn_sum == pytest.approx(0.9) and g.completed == 2           # fertig: Lkw 2 (0.5) und Lkw 3 (0.4)
    assert g.lens == [1, 1] and g.total_jobs == 2                              # Lkw 1 (Spur 0) und Lkw 4 (Spur 1) im System


def test_hand_computed_event_order_departure_before_arrival():
    """Ein Abgang vor der nächsten Ankunft wird vor ihr verarbeitet: 1 Spur, Lkw 1 bei 1.0 (Abfertigung 0.5, Abgang 1.5), Lkw 2 bei 2.0
    findet die Spur leer, wartet nicht."""
    rngs = (ScriptedRng(exp_values=[1.0, 1.0, 100.0]), ScriptedRng(uniform_values=[0.0, 0.0]), ScriptedRng(exp_values=[0.5, 0.5]))
    res = S.simulate(1, 0.5, 1, 2, seed=0, warm_fraction=0.0, rngs=rngs)
    assert (res.arrivals, res.found_idle, res.mean_wait) == (2, 2, 0.0)


# ---------------------------------------------------------------- Invarianten und Gegenproben

@pytest.mark.parametrize("n,rho,d", [(5, 0.8, 1), (5, 0.8, 2), (8, 0.9, 3), (6, 0.7, C.D_ALL)])
def test_littles_law_holds_exactly_along_the_path(n, rho, d):
    """Ohne Einschwingen und ohne Löschen gilt für die ganze Spanne [0, T] EXAKT: ∫ Lkw im System dt = Σ Verweilzeiten der fertigen Lkw
    + Σ (T − Ankunft) der noch im System; ebenso für die Wartenden: ∫ (Lkw − Beschäftigte) dt = Σ Wartezeiten der begonnenen
    Abfertigungen + Σ (T − Ankunft) der noch Wartenden."""
    res, g = S.simulate(n, rho, d, 20_000, seed=3, warm_fraction=0.0, return_gate=True)
    T = g.clock
    in_system = sum(T - a for q in g.jobs for a in q)
    assert g.area_jobs == pytest.approx(g.sojourn_sum + in_system, rel=1e-9)
    waiting = sum(T - a for q in g.jobs for a in list(q)[1:])
    assert g.area_jobs - g.area_busy == pytest.approx(g.wait_sum + waiting, rel=1e-6, abs=1e-6)


def test_state_invariants_after_a_run():
    res, g = S.simulate(6, 0.9, 2, 5_000, seed=9, warm_fraction=0.0, return_gate=True)
    assert g.lens == [len(q) for q in g.jobs] and sum(g.lens) == g.total_jobs
    for k in range(len(g.cnt)):
        assert g.cnt[k] == sum(1 for x in g.lens if x >= k)
    assert len(g.departures) == sum(1 for x in g.lens if x > 0)               # jede beschäftigte Spur hat genau einen geplanten Abgang
    assert res.tail[0] == 1.0 and all(0 <= x <= 1 for x in res.tail)
    assert all(a >= b for a, b in zip(res.tail, res.tail[1:]))                # der Schwanz fällt monoton


def test_same_seed_same_result_and_different_seed_differs():
    a, b, c = S.simulate(8, 0.8, 2, 8_000, 5), S.simulate(8, 0.8, 2, 8_000, 5), S.simulate(8, 0.8, 2, 8_000, 6)
    assert a == b and a.mean_wait != c.mean_wait


def test_utilisation_equals_rho_up_to_noise_and_little_matches_the_direct_wait():
    res = S.simulate(20, 0.8, 2, 120_000, 11)
    assert res.utilisation == pytest.approx(0.8, abs=0.02)
    assert res.little_sojourn() - 1.0 == pytest.approx(res.mean_wait, abs=0.03)        # zwei Wege zur Wartezeit


def test_a_single_lane_is_mm1_for_every_rule():
    """N = 1: nur eine Wahl möglich, jede Regel ist M/M/1 (Wartezeit ρ/(1−ρ) = 1 bei ρ = 0.5)."""
    for d in (1, 2, C.D_ALL):
        res = S.simulate(1, 0.5, d, 300_000, 21)
        assert res.mean_wait == pytest.approx(F.mm1_wait(0.5), rel=0.06), d


# ---------------------------------------------------------------- unabhängige Referenz: abgeschnittene Markov-Kette

def test_policy_probabilities_by_hand():
    """3 Spuren [0, 1, 1], d = 2: geordnete Paare (9); die leere Spur 0 gewinnt, wenn sie dabei ist: 1 − (2/3)² = 5/9."""
    p = policy_probabilities((0, 1, 1), 2)
    assert p[0] == pytest.approx(5 / 9) and p[1] == pytest.approx(2 / 9) and p[2] == pytest.approx(2 / 9)
    assert policy_probabilities((1, 0, 0), C.D_ALL) == [0.0, 0.5, 0.5]


@pytest.mark.parametrize("n,rho,d,cap", [(2, 0.7, 1, 60), (2, 0.7, C.D_ALL, 60), (3, 0.6, 2, 22), (3, 0.6, 1, 22)])
def test_simulation_matches_the_exact_chain(n, rho, d, cap):
    """Abgeschnittene Markov-Kette (Aufzählen der Wahlregel, lineares System) gegen die Simulation: 6 Läufe à 250 000 Lkw."""
    exact = exact_mean_wait(n, rho, d, cap)
    runs = [S.simulate(n, rho, d, 250_000, 100 + 17 * r).mean_wait for r in range(6)]
    mean = sum(runs) / len(runs)
    se = (sum((x - mean) ** 2 for x in runs) / (len(runs) - 1) / len(runs)) ** 0.5
    assert abs(mean - exact) < max(4 * se, 0.02 * exact), (exact, mean, se)


def test_the_exact_chain_itself_agrees_with_mm1_and_with_jsq_ordering():
    """Selbsttest der Referenz: für n = 1 gilt M/M/1; für n = 2 ordnet sich die Wartezeit JSQ < zufällig."""
    assert exact_mean_wait(1, 0.6, 1, 80) == pytest.approx(F.mm1_wait(0.6), rel=1e-6)
    assert exact_mean_wait(2, 0.7, C.D_ALL, 60) < exact_mean_wait(2, 0.7, 1, 60)
    assert exact_mean_wait(2, 0.7, 1, 60) == pytest.approx(F.mm1_wait(0.7), rel=1e-4)          # d = 1 zerlegt in zwei M/M/1


def test_clock_conservation():
    """Der Lauf endet bei der letzten Ankunft; der ausgewertete Zeitraum ist Endzeit minus Beginn der Messung."""
    res, g = S.simulate(4, 0.8, 2, 3_000, 2, warm_fraction=0.2, return_gate=True)
    assert res.horizon == pytest.approx(g.clock - g.t_start) and g.t_start > 0
    assert res.arrivals == 3_000 - int(0.2 * 3_000)
