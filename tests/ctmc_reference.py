"""Unabhängige Referenz: stationäre Verteilung des JSQ(d)-Systems mit N Spuren als abgeschnittene Markov-Kette über die Vektoren der
Schlangenlängen (jede Länge höchstens `cap`), gelöst als lineares Gleichungssystem (scipy.sparse). Die Übergangsraten der Wahlregel
entstehen durch Aufzählen aller N^d geordneten Stichproben (d < N) oder, für d ≥ N, gleichverteilt unter den kürzesten Schlangen.
Hat nichts mit der Simulation zu tun (kein Zufall, keine Ereignisliste)."""

import itertools

import numpy as np
from scipy.sparse import diags, lil_matrix
from scipy.sparse.linalg import spsolve


def policy_probabilities(lens, d):
    """P(Lkw reiht sich in Spur i ein) für den Längenvektor `lens`."""
    n = len(lens)
    p = [0.0] * n
    if d >= n:
        shortest = min(lens)
        winners = [i for i in range(n) if lens[i] == shortest]
        for i in winners:
            p[i] = 1.0 / len(winners)
        return p
    for sample in itertools.product(range(n), repeat=d):
        best = sample[0]
        for i in sample[1:]:
            if lens[i] < lens[best]:
                best = i
        p[best] += 1.0 / n ** d
    return p


def exact_mean_wait(n, rho, d, cap):
    """Mittlere Wartezeit (Abfertigungsdauern, Abfertigung Mittel 1) aus der stationären Verteilung und Little: Wq = L/(nρ) − 1."""
    states = list(itertools.product(range(cap + 1), repeat=n))
    index = {s: i for i, s in enumerate(states)}
    q = lil_matrix((len(states), len(states)))
    for s, i in index.items():
        probs = policy_probabilities(s, d)
        for j in range(n):
            if probs[j] > 0 and s[j] < cap:
                t = list(s)
                t[j] += 1
                q[i, index[tuple(t)]] += n * rho * probs[j]
        for j in range(n):
            if s[j] > 0:
                t = list(s)
                t[j] -= 1
                q[i, index[tuple(t)]] += 1.0
    q = q.tocsr()
    out = np.asarray(q.sum(axis=1)).ravel()
    gen = (q - diags(out)).T.tolil()
    gen[0, :] = 1.0                                   # Normierung ersetzt eine Gleichung
    b = np.zeros(len(states))
    b[0] = 1.0
    pi = spsolve(gen.tocsr(), b)
    mean_jobs = float(sum(pi[i] * sum(s) for s, i in index.items()))
    return mean_jobs / (n * rho) - 1.0
