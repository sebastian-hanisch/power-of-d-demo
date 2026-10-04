"""Ereignisdiskrete Simulation von N Spuren mit je eigener Schlange (FIFO) und der Wahlregel „d Schlangen ansehen, in die kürzeste
einreihen“ (JSQ(d), Power-of-d-Choices). Ankünfte: Poisson mit Rate N·ρ, Abfertigung exponentiell mit Mittel 1.

Aufbau nach Einheiten (kein versteckter Zustand): `choose_queue` (die Wahlregel, Zufall nur über den übergebenen Strom), `start_service`,
`handle_arrival`, `handle_departure`, `advance_clock` (Zeitintegrale), `simulate` (Ereignisschleife). Zufall nur über übergebene
`SplitMix64`-Ströme (Zwischenankunft, Wahl, Abfertigung). Je Spur hält eine Warteschlange die Ankunftszeiten ihrer Lkw; der vorderste
wird abgefertigt. Gemessen wird nach einer Einschwingphase (die ersten `warm_fraction` der Lkw): Zeitmittel des Anteils s_k der Spuren
mit mindestens k Lkw, mittlere Wartezeit der abgefertigten Lkw, Anteil der Lkw, die eine freie Spur finden, und die Zeitintegrale für
den Gegenbeweis über das Gesetz von Little."""

import heapq
import math
from collections import deque
from dataclasses import dataclass, field

_MASK = (1 << 64) - 1


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def expovariate(self, rate):
        """Exponentiell mit Mittel 1/rate (Inversion; 1 − u liegt in (0, 1], der Logarithmus ist endlich)."""
        return -math.log(1.0 - self.uniform()) / rate


def streams(seed):
    """Die drei Zufallsströme eines Laufs: Zwischenankunft, Wahl der Schlangen, Abfertigung."""
    return SplitMix64(seed), SplitMix64(seed + 7_777_777), SplitMix64(seed + 15_555_555)


def choose_queue(lens, d, rng):
    """Wahlregel: `d` Schlangen zufällig mit Zurücklegen ansehen, die kürzeste nehmen (bei Gleichstand die zuerst angesehene).
    `d >= len(lens)` heißt: alle ansehen und unter den kürzesten zufällig wählen (JSQ)."""
    n = len(lens)
    if d >= n:
        shortest = min(lens)
        candidates = [i for i in range(n) if lens[i] == shortest]
        return candidates[int(rng.uniform() * len(candidates))]
    best = int(rng.uniform() * n)
    for _ in range(d - 1):
        i = int(rng.uniform() * n)
        if lens[i] < lens[best]:
            best = i
    return best


@dataclass
class Gate:
    """Zustand eines Laufs: Schlangenlängen, Ankunftszeiten je Spur, Abgangsliste, Uhr und alle Zähler."""
    n: int
    lens: list
    jobs: list                                   # je Spur eine deque mit den Ankunftszeiten (vorderster wird abgefertigt)
    cnt: list                                    # cnt[k] = Zahl der Spuren mit mindestens k Lkw (cnt[0] = n)
    departures: list = field(default_factory=list)     # Heap aus (Abgangszeit, Spur)
    clock: float = 0.0
    measuring: bool = False
    t_start: float = 0.0                         # Beginn der Messung
    arrivals: int = 0                            # Ankünfte seit Messbeginn
    found_idle: int = 0                          # davon: reihen sich in eine leere Spur ein
    area_jobs: float = 0.0                       # ∫ Zahl der Lkw im System dt
    area_busy: float = 0.0                       # ∫ Zahl der beschäftigten Spuren dt
    level_area: list = field(default_factory=list)     # ∫ cnt[k] dt
    wait_sum: float = 0.0                        # Summe der Wartezeiten der seit Messbeginn begonnenen Abfertigungen
    wait_n: int = 0
    sojourn_sum: float = 0.0                     # Summe der Verweilzeiten der seit Messbeginn fertigen Lkw
    completed: int = 0
    total_jobs: int = 0


def new_gate(n):
    return Gate(n=n, lens=[0] * n, jobs=[deque() for _ in range(n)], cnt=[n])


def advance_clock(g, t_new):
    """Zeit auf `t_new` vorrücken und (in der Messung) die Zeitintegrale fortschreiben."""
    dt = t_new - g.clock
    if g.measuring and dt > 0:
        g.area_jobs += g.total_jobs * dt
        g.area_busy += g.cnt[1] * dt if len(g.cnt) > 1 else 0.0
        la = g.level_area
        while len(la) < len(g.cnt):
            la.append(0.0)
        for k in range(1, len(g.cnt)):
            la[k] += g.cnt[k] * dt
    g.clock = t_new


def start_service(g, server, svc_rng):
    """Der vorderste Lkw der Spur beginnt seine Abfertigung (Wartezeit = jetzt − Ankunft), der Abgang wird eingeplant."""
    arrival = g.jobs[server][0]
    if g.measuring:
        g.wait_sum += g.clock - arrival
        g.wait_n += 1
    heapq.heappush(g.departures, (g.clock + svc_rng.expovariate(1.0), server))


def handle_arrival(g, d, choice_rng, svc_rng):
    """Ein Lkw kommt an: Schlange wählen, einreihen; war die Spur leer, beginnt die Abfertigung sofort."""
    server = choose_queue(g.lens, d, choice_rng)
    was_empty = g.lens[server] == 0
    if g.measuring:
        g.arrivals += 1
        if was_empty:
            g.found_idle += 1
    g.jobs[server].append(g.clock)
    g.lens[server] += 1
    g.total_jobs += 1
    k = g.lens[server]
    if k >= len(g.cnt):
        g.cnt.append(0)
    g.cnt[k] += 1
    if was_empty:
        start_service(g, server, svc_rng)


def handle_departure(g, server, svc_rng):
    """Der Lkw an der Spitze der Spur ist fertig; der nächste in der Spur beginnt."""
    arrival = g.jobs[server].popleft()
    if g.measuring:
        g.sojourn_sum += g.clock - arrival
        g.completed += 1
    k = g.lens[server]
    g.cnt[k] -= 1
    g.lens[server] -= 1
    g.total_jobs -= 1
    if g.lens[server] > 0:
        start_service(g, server, svc_rng)


def start_measurement(g):
    g.measuring = True
    g.t_start = g.clock


@dataclass
class SimResult:
    n: int
    rho: float
    d: int
    horizon: float                 # Länge des ausgewerteten Zeitraums (Abfertigungsdauern)
    arrivals: int
    found_idle: int
    mean_wait: float               # mittlere Wartezeit der abgefertigten Lkw (Abfertigungsdauern)
    tail: list                     # tail[k] = Zeitmittel des Anteils der Spuren mit mindestens k Lkw (tail[0] = 1)
    mean_jobs: float               # Zeitmittel der Zahl der Lkw im System
    utilisation: float             # Zeitmittel des Anteils beschäftigter Spuren

    def idle_found_fraction(self):
        return self.found_idle / self.arrivals if self.arrivals else float("nan")

    def little_sojourn(self):
        """Mittlere Verweilzeit nach Little: L/λ, mit der tatsächlich beobachteten Ankunftsrate."""
        return self.mean_jobs * self.horizon / self.arrivals if self.arrivals else float("nan")


def simulate(n, rho, d, n_customers, seed, warm_fraction=0.2, rngs=None, return_gate=False):
    """Ein Lauf über `n_customers` Ankünfte; die ersten `warm_fraction` davon werden nicht ausgewertet (Start mit leerem Gate).
    `return_gate=True` gibt zusätzlich den Endzustand zurück (für die Gegenproben über Little)."""
    gap_rng, choice_rng, svc_rng = rngs if rngs is not None else streams(seed)
    g = new_gate(n)
    warm = int(warm_fraction * n_customers)
    next_arrival = gap_rng.expovariate(n * rho)
    if warm == 0:
        start_measurement(g)
    for i in range(n_customers):
        while g.departures and g.departures[0][0] < next_arrival:
            t, server = heapq.heappop(g.departures)
            advance_clock(g, t)
            handle_departure(g, server, svc_rng)
        advance_clock(g, next_arrival)
        if i == warm and not g.measuring:
            start_measurement(g)
        handle_arrival(g, d, choice_rng, svc_rng)
        next_arrival = g.clock + gap_rng.expovariate(n * rho)
    result = _result(g, n, rho, d)
    return (result, g) if return_gate else result


def _result(g, n, rho, d):
    horizon = g.clock - g.t_start
    tail = [1.0] + [(g.level_area[k] / (n * horizon) if horizon > 0 and k < len(g.level_area) else 0.0) for k in range(1, 40)]
    while len(tail) > 2 and tail[-1] == 0.0:
        tail.pop()
    return SimResult(n=n, rho=rho, d=d, horizon=horizon, arrivals=g.arrivals, found_idle=g.found_idle,
                     mean_wait=g.wait_sum / g.wait_n if g.wait_n else float("nan"), tail=tail,
                     mean_jobs=g.area_jobs / horizon if horizon > 0 else float("nan"),
                     utilisation=g.area_busy / (n * horizon) if horizon > 0 else float("nan"))
