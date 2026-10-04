import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ScriptedRng:
    """Liefert vorgegebene Werte statt Zufall (Mini-Instanzen von Hand gerechnet). `expovariate(rate)` ignoriert die Rate und gibt der
    Reihe nach die Werte zurück, `uniform()` ebenso aus einer eigenen Liste."""

    def __init__(self, exp_values=(), uniform_values=()):
        self.exp_values, self.uniform_values = list(exp_values), list(uniform_values)
        self.n_exp = self.n_uniform = 0

    def expovariate(self, rate):
        v = self.exp_values[self.n_exp]
        self.n_exp += 1
        return v

    def uniform(self):
        v = self.uniform_values[self.n_uniform]
        self.n_uniform += 1
        return v


@pytest.fixture
def jsq_mini_streams():
    """2 Spuren, JSQ (d = 2 ≥ n), vier Lkw. Zwischenankünfte 1.0 / 0.5 / 0.3 / 0.7 (Ankünfte bei 1.0, 1.5, 1.8, 2.5; die fünfte Zeit wird
    gezogen, aber nicht gebraucht), Abfertigungen 3.0 / 0.5 / 0.2 / 0.4, Wahl-Zufall 0.0 / 0.0 / 0.5 / 0.0.
    Von Hand: Lkw 1 → Spur 0 (leer, Abgang 4.0); Lkw 2 → Spur 1 (Abgang 2.0); Lkw 3 findet beide belegt, unter den kürzesten
    (Spuren 0 und 1) wählt 0.5 die Spur 1 (Index 1), wartet bis 2.0 (Wartezeit 0.2), Abgang 2.2; Lkw 4 (2.5) findet Spur 1 leer."""
    return (ScriptedRng(exp_values=[1.0, 0.5, 0.3, 0.7, 100.0]), ScriptedRng(uniform_values=[0.0, 0.0, 0.5, 0.0]),
            ScriptedRng(exp_values=[3.0, 0.5, 0.2, 0.4]))
