"""Orakel-Test (zweiter, anderer Rechenweg als tests/ctmc_reference.py): Markov-Kette über SORTIERTE Längenvektoren (Symmetrie),
Wahlwahrscheinlichkeit in geschlossener Form P(kürzeste gezogene Spur hat Länge l) = a_l^d − a_{l+1}^d (a_l = Anteil Spuren mit mindestens
l Lkw) statt Aufzählen aller Stichproben. Geprüft werden außer der Wartezeit auch die angezeigten Kennzahlen (Anteil freier Spuren,
Schwanzanteile s_k) an vier Spuren, wo die Wahlregel d = 2, 3 noch von „alle ansehen“ verschieden ist. Dazu: gemeinsame Schlange gegen die
Geburts-Sterbe-Kette und die Gleichgewichtsgleichung des Fluid-Grenzwerts (Differentialform, nicht die telescopierte Rekursion)."""

import itertools
import math

import pytest

import pod_formulas as F
import pod_simulation as S

np = pytest.importorskip("numpy")
sparse = pytest.importorskip("scipy.sparse")
splinalg = pytest.importorskip("scipy.sparse.linalg")


def sorted_chain(n, rho, d, cap):
    """(mittlere Wartezeit, Anteil Lkw mit freier Spur, [s_1..s_3]) aus der stationären Verteilung der sortierten Kette."""
    states = list(itertools.combinations_with_replacement(range(cap + 1), n))
    idx = {s: i for i, s in enumerate(states)}
    q = sparse.lil_matrix((len(states), len(states)))
    for s, i in idx.items():
        frac = lambda level: sum(1 for x in s if x >= level) / n          # noqa: E731  a_level
        for length in set(s):
            if length < cap:
                p = (1.0 if length == min(s) else 0.0) if d >= n else frac(length) ** d - frac(length + 1) ** d
                if p > 0:
                    t = list(s)
                    t.remove(length)
                    t.append(length + 1)
                    q[i, idx[tuple(sorted(t))]] += n * rho * p
            if length >= 1:
                t = list(s)
                t.remove(length)
                t.append(length - 1)
                q[i, idx[tuple(sorted(t))]] += s.count(length)
    q = q.tocsr()
    gen = (q - sparse.diags(np.asarray(q.sum(axis=1)).ravel())).T.tolil()
    gen[0, :] = 1.0
    rhs = np.zeros(len(states))
    rhs[0] = 1.0
    pi = splinalg.spsolve(gen.tocsr(), rhs)
    wait = sum(pi[i] * sum(s) for s, i in idx.items()) / (n * rho) - 1.0
    idle = sum(pi[i] * ((1.0 if min(s) == 0 else 0.0) if d >= n else 1.0 - (sum(1 for x in s if x >= 1) / n) ** d) for s, i in idx.items())
    tail = [sum(pi[i] * sum(1 for x in s if x >= k) / n for s, i in idx.items()) for k in (1, 2, 3)]
    return wait, idle, tail


def test_the_sorted_chain_is_itself_correct_on_hand_cases():
    """Selbsttest: eine Spur und d = 1 sind M/M/1; zwei Spuren mit d = 1 zerfallen in zwei M/M/1."""
    assert sorted_chain(1, 0.6, 1, 60)[0] == pytest.approx(F.mm1_wait(0.6), rel=1e-6)
    assert sorted_chain(2, 0.7, 1, 60)[0] == pytest.approx(F.mm1_wait(0.7), rel=1e-4)


@pytest.mark.parametrize("d", [2, 3])
def test_simulation_matches_the_chain_for_wait_idle_fraction_and_tail(d):
    n, rho = 4, 0.7
    wait, idle, tail = sorted_chain(n, rho, d, 10)
    runs = [S.simulate(n, rho, d, 40_000, 300 + 17 * r) for r in range(5)]
    waits = np.array([r.mean_wait for r in runs])
    se = waits.std(ddof=1) / math.sqrt(len(waits))
    assert abs(waits.mean() - wait) < max(4 * se, 0.04 * wait), (wait, waits.mean(), se)
    assert np.mean([r.idle_found_fraction() for r in runs]) == pytest.approx(idle, abs=0.012)
    for k in (1, 2, 3):
        assert np.mean([r.tail[k] if k < len(r.tail) else 0.0 for r in runs]) == pytest.approx(tail[k - 1], abs=0.012)


@pytest.mark.parametrize("n", [1, 2, 5, 20])
@pytest.mark.parametrize("rho", [0.5, 0.9])
def test_pooled_wait_matches_the_birth_death_chain(n, rho):
    a, size = n * rho, 4000
    p = np.ones(size)
    for k in range(1, size):
        p[k] = p[k - 1] * a / min(k, n)
    p /= p.sum()
    lq = sum(p[k] * (k - n) for k in range(n + 1, size))
    assert F.pooled_wait(n, rho) == pytest.approx(lq / a, rel=1e-6)


@pytest.mark.parametrize("d", [1, 2, 3, 5])
@pytest.mark.parametrize("rho", [0.5, 0.9, 0.95])
def test_fluid_limit_satisfies_the_balance_equations_of_the_differential_form(d, rho):
    """Gleichgewicht der Mitzenmacher-Gleichung ds_k/dt = ρ(s_{k−1}^d − s_k^d) − (s_k − s_{k+1}) = 0 für jedes k."""
    s = F.fluid_tail(rho, d)
    s = s + [0.0, 0.0]
    for k in range(1, len(s) - 1):
        assert rho * (s[k - 1] ** d - s[k] ** d) - (s[k] - s[k + 1]) == pytest.approx(0.0, abs=1e-12)
