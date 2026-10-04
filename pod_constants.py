"""Konstanten der Demo zu Power-of-d-Choices: Regler, Voreinstellungen, Studien-Achsen. Zeiteinheit der Rechnung ist die mittlere
Abfertigungsdauer (= 1); angezeigt werden Minuten bei 3 min Mittel."""


def fmt_int(n):
    """Ganzzahl mit Punkt als Tausendertrenner (10000 -> 10.000)."""
    return f"{n:,}".replace(",", ".")


def fmt_pct(x, digits=0):
    """Anteil als Prozent mit Leerzeichen (0.086 -> "9 %", mit digits=1 "8.6 %")."""
    return f"{x:.{digits}%}".replace("%", " %")


MEAN_SERVICE_MIN = 3.0                               # mittlere Abfertigungsdauer je Spur (Minuten)
D_ALL = 1000                                         # Sinnbild für „alle Schlangen ansehen“ (JSQ, Join the Shortest Queue)

N_OPTIONS = (10, 25, 50, 100, 200)                   # Zahl der Spuren
DEFAULT_N = 50
RHO_PCT_MIN, RHO_PCT_MAX, RHO_PCT_STEP, DEFAULT_RHO_PCT = 50, 95, 5, 90   # Auslastung je Spur in Prozent
D_OPTIONS = (1, 2, 3, 5, D_ALL)                      # so viele Schlangen schaut sich jeder Lkw an
DEFAULT_D = 2
SEED_MAX = 999999
DEFAULT_SEED = 35

LIVE_CUSTOMERS = 100_000                             # Lkw je Live-Lauf
WARMUP_FRACTION = 0.2                                # erster Anteil der Lkw eines Laufs wird nicht ausgewertet

# Vorgerechnete Studie (generate_precomputed.py)
STUDY_N = (10, 50, 200)
STUDY_RHO = (0.8, 0.9, 0.95)
STUDY_D = D_OPTIONS
STUDY_CUSTOMERS = 800_000                            # Lkw je Wiederholung
STUDY_REPS = 4                                       # unabhängige Wiederholungen je Zelle
TAIL_LEVELS = 8                                      # Anteile s_1 … s_8 (Spuren mit mindestens k Lkw) werden festgehalten

PRESET_ORDER = ("Eine Wahl genügt (d = 2)", "Kleines Gate (10 Spuren)", "Volle Auskunft (JSQ)", "Hohe Auslastung (95 %)")


def _preset(n=DEFAULT_N, rho_pct=DEFAULT_RHO_PCT, d=DEFAULT_D):
    return {"n": n, "rho_pct": rho_pct, "d": d, "seed": DEFAULT_SEED}


PRESETS = {
    "Eine Wahl genügt (d = 2)": _preset(),
    "Kleines Gate (10 Spuren)": _preset(n=10),
    "Volle Auskunft (JSQ)": _preset(d=D_ALL),
    "Hohe Auslastung (95 %)": _preset(n=200, rho_pct=95),
}
# Zahlen aus der vorgerechneten Studie (je 4 Läufe à 800 000 Lkw, 3 min mittlere Abfertigung); tests/test_claims.py rechnet sie nach
PRESET_HELP = {
    "Eine Wahl genügt (d = 2)": "50 Spuren, Auslastung 90 %: zufällige Zuteilung 27.1 min Wartezeit, zwei Auskünfte 5.1 min, alle Schlangen 0.5 min, eine gemeinsame Schlange 0.2 min.",
    "Kleines Gate (10 Spuren)": "10 Spuren, Auslastung 90 %, d = 2: 6.5 min statt 4.8 min im Grenzwert für viele Spuren (34 % länger); eine gemeinsame Schlange 2.0 min.",
    "Volle Auskunft (JSQ)": "50 Spuren, Auslastung 90 %: alle Schlangen ansehen 0.5 min, zwei Auskünfte 5.1 min; die gemeinsame Schlange (0.2 min) bleibt 2.4-mal besser.",
    "Hohe Auslastung (95 %)": "200 Spuren, Auslastung 95 %: zufällige Zuteilung 55.8 min, zwei Auskünfte 7.2 min, alle Schlangen 0.3 min.",
}
