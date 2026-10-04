"""Formeln: Fluid-Rekursion von Hand, geschlossene Form, M/M/1, Erlang C gegen die Summenformel, Little, Monotonie."""

import math

import pytest

import pod_constants as C
import pod_formulas as F


def test_fluid_recursion_by_hand():
    s = F.fluid_tail(0.5, 2, tol=1e-3)
    assert s[:4] == pytest.approx([1.0, 0.5, 0.125, 0.5 * 0.125 ** 2])          # s_k = ρ·s_{k−1}^d
    assert F.fluid_tail(0.5, 1, tol=1e-3)[:4] == pytest.approx([1.0, 0.5, 0.25, 0.125])


@pytest.mark.parametrize("rho", [0.3, 0.8, 0.95])
@pytest.mark.parametrize("d", [1, 2, 3, 5])
def test_recursion_matches_closed_form(rho, d):
    s = F.fluid_tail(rho, d)
    for k in range(min(len(s), 8)):
        assert s[k] == pytest.approx(F.tail_closed_form(rho, d, k), rel=1e-12)


@pytest.mark.parametrize("rho", [0.5, 0.8, 0.9, 0.95])
def test_d1_is_mm1_for_every_n(rho):
    assert F.fluid_sojourn(rho, 1) == pytest.approx(1 / (1 - rho), rel=1e-9)
    assert F.fluid_wait(rho, 1) == pytest.approx(F.mm1_wait(rho), rel=1e-9) and F.mm1_wait(rho) == pytest.approx(rho / (1 - rho))


def test_sojourn_by_hand_for_d2_rho_half():
    """ρ = 0.5, d = 2: s = 0.5, 0.125, 0.0078125, 0.5·0.0078125², …; W = Σ s / ρ."""
    total = sum(F.fluid_tail(0.5, 2)[1:])
    assert total == pytest.approx(0.5 + 0.125 + 0.0078125 + 0.5 * 0.0078125 ** 2 + 0.5 * (0.5 * 0.0078125 ** 2) ** 2, rel=1e-6)
    assert F.fluid_sojourn(0.5, 2) == pytest.approx(total / 0.5)


def test_jsq_limit_has_no_waiting_and_always_finds_an_idle_lane():
    assert F.fluid_tail(0.9, C.D_ALL) == [1.0, 0.9] and F.fluid_wait(0.9, C.D_ALL) == 0.0
    assert F.prob_idle_found(0.9, C.D_ALL) == 1.0


def test_probability_of_finding_an_idle_lane_is_one_minus_rho_to_the_d():
    assert F.prob_idle_found(0.9, 1) == pytest.approx(0.1) and F.prob_idle_found(0.9, 2) == pytest.approx(1 - 0.81)
    assert F.prob_idle_found(0.5, 3) == pytest.approx(0.875)


def test_more_choices_never_hurt_and_wait_falls_with_every_step():
    for rho in (0.5, 0.8, 0.95):
        waits = [F.fluid_wait(rho, d) for d in (1, 2, 3, 4, 5, 8, 16)]
        assert all(a > b > 0 for a, b in zip(waits, waits[1:]))


def test_the_tail_falls_doubly_exponentially_for_d_two():
    """−log s_k wächst für d = 2 selbst exponentiell (Verhältnis log s_{k+1} / log s_k → 2), für d = 1 nur linear."""
    s2 = F.fluid_tail(0.9, 2)
    ratios = [math.log(s2[k + 1]) / math.log(s2[k]) for k in range(4, 8)]
    assert ratios == pytest.approx([2.0] * 4, rel=0.04)
    s1 = F.fluid_tail(0.9, 1)
    assert math.log(s1[10]) / math.log(s1[5]) == pytest.approx(2.0, rel=1e-9)        # linear: Verhältnis 10/5


def test_improvement_factor_matches_the_ratio_of_waits():
    assert F.improvement_factor(0.9, 1, 2) == pytest.approx(9.0 / F.fluid_wait(0.9, 2)) and 5.5 < F.improvement_factor(0.9, 1, 2) < 5.7
    assert F.improvement_factor(0.9, 2, 3) < F.improvement_factor(0.9, 1, 2)


def test_erlang_c_against_the_explicit_sum():
    for c, a in ((1, 0.5), (3, 2.0), (10, 9.0)):
        top = a ** c / math.factorial(c) * c / (c - a)
        bottom = sum(a ** k / math.factorial(k) for k in range(c)) + top
        assert F.erlang_c(c, a) == pytest.approx(top / bottom, rel=1e-12)
    assert F.erlang_c(1, 0.5) == pytest.approx(0.5)                              # M/M/1: P(warten) = ρ


def test_pooled_wait_is_below_the_choice_systems_for_large_gates():
    """Eine gemeinsame Schlange schlägt jede Wahlregel; für c = 1 stimmt sie mit M/M/1 überein. Der Grenzwert gilt nur für große N: bei
    N = 10 liegt der gepoolte Wert (0.67) noch über dem Grenzwert für d = 5 (0.63), das ist ein Vergleich Endlich gegen Grenzwert."""
    assert F.pooled_wait(1, 0.8) == pytest.approx(F.mm1_wait(0.8))
    for n in (50, 200):
        assert F.pooled_wait(n, 0.9) < F.fluid_wait(0.9, 5) < F.fluid_wait(0.9, 1)
    assert F.pooled_wait(10, 0.9) < F.fluid_wait(0.9, 1)


def test_pooled_wait_by_hand_for_two_lanes():
    """M/M/2 mit ρ = 0.5 (a = 1): C = 1/3, Wq = C/(2·(1−ρ)) = 1/3."""
    assert F.erlang_c(2, 1.0) == pytest.approx(1 / 3) and F.pooled_wait(2, 0.5) == pytest.approx(1 / 3)


def test_invalid_input_is_rejected():
    for bad in (0.0, 1.0, 1.2, -0.1):
        with pytest.raises(ValueError):
            F.fluid_tail(bad, 2)
        with pytest.raises(ValueError):
            F.mm1_wait(bad)
    with pytest.raises(ValueError):
        F.erlang_c(3, 3.0)


def test_helpers():
    assert F.to_minutes(2.0) == 6.0 and F.finite_gap(1.1, 1.0) == pytest.approx(0.1)
    assert F.finite_gap(1.0, 0.0) is None and F.finite_gap(float("nan"), 1.0) is None
