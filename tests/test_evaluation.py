"""Auswertung: Live-Lauf mit Bezugswerten, Studienzelle (Mittel, Standardfehler), Vollständigkeit der vorgerechneten Datei."""

import pytest

import pod_constants as C
import pod_evaluation as E
import pod_formulas as F


def test_mean_and_se_by_hand():
    assert E.mean_and_se([1.0, 3.0]) == (2.0, 1.0)                       # Standardabweichung √2, Standardfehler √2/√2
    assert E.mean_and_se([5.0]) == (5.0, None)


def test_nearest_picks_the_closest_option_and_the_smaller_on_a_tie():
    assert E.nearest(C.STUDY_N, 30) == 10 and E.nearest(C.STUDY_N, 31) == 50 and E.nearest(C.STUDY_N, 120) == 50
    assert E.nearest(C.STUDY_RHO, 0.85) == 0.8 and E.nearest(C.STUDY_RHO, 0.5) == 0.8


def test_live_report_structure_and_reference_values():
    r = E.live_report(10, 0.8, 2, seed=3, customers=8_000)
    assert r["wait_mm1"] == pytest.approx(F.mm1_wait(0.8)) and r["wait_fluid"] == pytest.approx(F.fluid_wait(0.8, 2))
    assert r["wait_pooled"] == pytest.approx(F.pooled_wait(10, 0.8)) and r["idle_fluid"] == pytest.approx(1 - 0.8 ** 2)
    assert len(r["lens"]) == len(r["lens_base"]) == 10 and r["tail_sim"][0] == 1.0
    assert r["sim"].d == 2 and r["base"].d == 1 and r["wait_sim"] == r["sim"].mean_wait


def test_live_report_with_d_one_uses_the_same_run_as_baseline():
    r = E.live_report(10, 0.8, 1, seed=3, customers=5_000)
    assert r["base"] is r["sim"] and r["lens"] == r["lens_base"]


def test_study_cell_run_small_structure():
    cell = E.study_cell_run(10, 0.8, 2, 8_000, 5, reps=3)
    assert cell["reps"] == 3 and len(cell["waits"]) == 3 and len(cell["tail"]) == C.TAIL_LEVELS
    assert cell["wait"] == pytest.approx(sum(cell["waits"]) / 3) and cell["wait_se"] > 0
    assert all(a >= b for a, b in zip(cell["tail"], cell["tail"][1:])) and 0 < cell["idle"] < 1 and cell["util"] == pytest.approx(0.8, abs=0.06)
    assert E.study_cell_run(10, 0.8, 1, 3_000, 5, reps=1)["wait_se"] is None


def test_precomputed_file_is_complete():
    pre = E.load_precomputed()
    keys = {(x["n"], x["rho"], x["d"]) for x in pre["study"]}
    assert keys == {(n, r, d) for n in C.STUDY_N for r in C.STUDY_RHO for d in C.STUDY_D}
    assert pre["study_customers"] == C.STUDY_CUSTOMERS and pre["study_reps"] == C.STUDY_REPS and pre["warmup_fraction"] == C.WARMUP_FRACTION
    for x in pre["study"]:
        assert x["reps"] == C.STUDY_REPS and x["customers"] == C.STUDY_CUSTOMERS and len(x["tail"]) == C.TAIL_LEVELS and len(x["waits"]) == C.STUDY_REPS


def test_study_cell_lookup_and_missing_cell():
    pre = E.load_precomputed()
    assert E.study_cell(pre, 50, 0.9, 2)["n"] == 50
    with pytest.raises(KeyError):
        E.study_cell(pre, 51, 0.9, 2)


def test_study_d_snaps_to_the_study_axis():
    assert E.study_d(2) == 2 and E.study_d(4) == 3
