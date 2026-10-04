"""Formeln zu Power-of-d-Choices (JSQ(d)): N Spuren mit je eigener Schlange, Ankunftsrate N·ρ, Abfertigung exponentiell mit Mittel 1
(Zeiteinheit = mittlere Abfertigungsdauer). Jeder Lkw sieht sich d zufällig gewählte Schlangen an (mit Zurücklegen) und reiht sich in
die kürzeste ein; d = 1 ist zufällige Zuteilung, ganz viele d (`D_ALL`) heißt: die kürzeste aller Schlangen (JSQ).

**Fluid-Grenzwert** (N → ∞; Vvedenskaya, Dobrushin und Karpelevich 1996, Mitzenmacher 2001): der Anteil s_k der Spuren mit mindestens k
Lkw im System erfüllt im Gleichgewicht s_k = ρ·s_{k−1}^d mit s_0 = 1, in geschlossener Form s_k = ρ^((d^k − 1)/(d − 1)) für d ≥ 2 und
s_k = ρ^k für d = 1. Die mittlere Verweilzeit folgt aus Little: W = Σ_{k≥1} s_k / ρ, die mittlere Wartezeit ist W − 1. Der Schwanz fällt
für d ≥ 2 **doppelt exponentiell**, für d = 1 nur exponentiell.

Zum Vergleich: M/M/1-Schlangen je Spur (d = 1, exakt: W = 1/(1 − ρ)) und das gepoolte System mit einer gemeinsamen Schlange (M/M/N,
Erlang C; Kopie der Erlang-B/C-Formeln aus mmc-queue-demo, bewusst ohne Import zwischen Repos)."""

import math

from pod_constants import D_ALL


def fluid_tail(rho, d, tol=1e-15, kmax=100_000):
    """[s_0, s_1, …] des Fluid-Grenzwerts über die Rekursion s_k = ρ·s_{k−1}^d, bis s_k < tol. Für `d >= D_ALL` (JSQ) gilt im Grenzwert
    s_1 = ρ und s_k = 0 für k ≥ 2: es wartet niemand."""
    if not 0 < rho < 1:
        raise ValueError("ρ muss in (0, 1) liegen")
    if d >= D_ALL:
        return [1.0, rho]
    s = [1.0]
    while s[-1] >= tol and len(s) <= kmax:
        s.append(rho * s[-1] ** d)
    return s


def tail_closed_form(rho, d, k):
    """s_k in geschlossener Form: ρ^((d^k − 1)/(d − 1)) für d ≥ 2, ρ^k für d = 1."""
    if d == 1:
        return rho ** k
    return rho ** ((d ** k - 1) / (d - 1))


def fluid_sojourn(rho, d):
    """Mittlere Verweilzeit (Warten + Abfertigung) im Fluid-Grenzwert in Abfertigungsdauern: W = Σ s_k / ρ (Little)."""
    return sum(fluid_tail(rho, d)[1:]) / rho


def fluid_wait(rho, d):
    """Mittlere Wartezeit im Fluid-Grenzwert in Abfertigungsdauern: W − 1."""
    return max(0.0, fluid_sojourn(rho, d) - 1.0)


def mm1_wait(rho):
    """Mittlere Wartezeit einer M/M/1-Schlange (Abfertigungsdauern): ρ/(1 − ρ). Entspricht d = 1 für beliebiges N."""
    if not 0 < rho < 1:
        raise ValueError("ρ muss in (0, 1) liegen")
    return rho / (1 - rho)


def prob_idle_found(rho, d):
    """Anteil der Lkw, die unter ihren d angesehenen Spuren eine freie finden (Fluid-Grenzwert): 1 − ρ^d; bei JSQ 1."""
    if d >= D_ALL:
        return 1.0
    return 1.0 - rho ** d


def erlang_b(c, a):
    """Erlang-B-Verlustwahrscheinlichkeit über die stabile Rekursion B_k = a·B_{k−1}/(k + a·B_{k−1})."""
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    return b


def erlang_c(c, a):
    """Erlang C: Wahrscheinlichkeit zu warten bei unendlicher Geduld, C = B/(1 − ρ(1 − B)); nur für c > a."""
    rho = a / c
    if rho >= 1:
        raise ValueError("c ≤ a: keine stationäre Verteilung")
    b = erlang_b(c, a)
    return b / (1 - rho * (1 - b))


def pooled_wait(n, rho):
    """Mittlere Wartezeit (Abfertigungsdauern) bei einer gemeinsamen Schlange vor n Spuren (M/M/n): C(n, nρ)/(n(1 − ρ))."""
    return erlang_c(n, n * rho) / (n * (1 - rho))


def improvement_factor(rho, d_from, d_to):
    """Um welchen Faktor die Wartezeit im Fluid-Grenzwert beim Übergang von `d_from` auf `d_to` Auskünfte sinkt."""
    return fluid_wait(rho, d_from) / fluid_wait(rho, d_to)


def to_minutes(x, mean_service_min=3.0):
    """Zeit in Abfertigungsdauern → Minuten."""
    return x * mean_service_min


def finite_gap(sim_wait, fluid_wait_value):
    """Relative Abweichung der Simulation vom Fluid-Grenzwert (sim/fluid − 1); None, wenn der Grenzwert null ist."""
    if fluid_wait_value <= 0 or math.isnan(sim_wait):
        return None
    return sim_wait / fluid_wait_value - 1.0
