# Power-of-d-Choices – welche Schlange? (Streamlit-Demo)

**[→ Demo live ausprobieren](https://sebastianhanisch-power-of-d-demo.streamlit.app/)**

Interaktive Demo zur **Wahl der Schlange an einem Gate mit je einer Schlange je Spur**. **Siebtes Stück der Konzepte-Linie
„Warteschlangentheorie und Simulation“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und
Machine Learning): ein Verfahren, ein wachsendes Beispiel, jedes Folgestück hebt genau eine Annahme auf.

Stück 3 ([mmc-queue-demo](https://github.com/sebastian-hanisch/mmc-queue-demo)) ließ alle Lkw in **einer gemeinsamen Schlange** warten,
das beste Ergebnis, das ein Gate mit gleichen Spuren erreichen kann. Hier hat **jede Spur ihre eigene Schlange**, und der Lkw muss sich
entscheiden. Zufällig zu wählen ist der Fall von [mm1-queue-demo](https://github.com/sebastian-hanisch/mm1-queue-demo) (Stück 1), je Spur
eine M/M/1-Schlange. Alle Schlangen anzusehen ist teuer. **Power-of-d-Choices** sieht sich nur **d zufällig gewählte Schlangen** an und nimmt
die kürzeste.

## Kernfrage

Wie viel bringt jede weitere Auskunft (d = 1, 2, 3, 5, alle), ab wie vielen Spuren trägt der Fluid-Grenzwert, und wie weit bleibt
die gemeinsame Schlange vorn?

## Modell und Methodik

- **Gate:** N Spuren (10 bis 200) mit je einer FIFO-Schlange, Ankunftsrate N·ρ (Poisson), exponentielle Abfertigung mit 3 min Mittel,
  Auslastung ρ je Spur (50 bis 95 %).
- **Wahlregel:** d Spuren zufällig **mit Zurücklegen** ziehen, die kürzeste Schlange nehmen (bei Gleichstand die zuerst gezogene).
  **d = 1** ist zufällige Zuteilung, **alle** (JSQ, *Join the Shortest Queue*) nimmt die kürzeste aller Schlangen, bei Gleichstand zufällig.
- **Fluid-Grenzwert** (`pod_formulas.py`): Anteil sₖ der Spuren mit mindestens k Lkw, sₖ = ρ·sₖ₋₁ᵈ, in geschlossener Form
  ρ^((dᵏ−1)/(d−1)) für d ≥ 2 und ρᵏ für d = 1; mittlere Verweilzeit W = Σ sₖ / ρ nach Little, Wartezeit W − 1. Für d ≥ 2 fällt der
  Schwanz **doppelt exponentiell**, für d = 1 nur exponentiell. Alle Wartezeiten dieser Demo sind **Wartezeiten** (ohne Abfertigung).
- **Simulation** (`pod_simulation.py`): Ereignisse Ankunft und Abgang (Abgänge in einem Heap), je Spur eine Warteschlange der
  Ankunftszeiten, SplitMix64 mit getrennten Strömen für Zwischenankunft, Wahl und Abfertigung; die ersten 20 % der Lkw werden nicht
  ausgewertet. Gemessen werden Wartezeit je begonnener Abfertigung, Zeitmittel der Anteile sₖ und der Anteil der Lkw, die eine freie Spur finden.
- **Gegenproben:** (1) das Gesetz von Little gilt entlang jedes Pfades **exakt** (Verweilzeiten und Wartezeiten); (2) für N = 2 und 3 stimmen
  die Mittel mit der **gelösten Markov-Kette** über alle Längenvektoren überein (unabhängige Referenz, `tests/ctmc_reference.py`, mit
  Aufzählen der Wahlregel; alle vier Fälle innerhalb von etwa einem Standardfehler); (3) eine von Hand gerechnete Mini-Instanz (zwei Spuren, vier Lkw);
  (4) eine Spur: jede Regel ist M/M/1.
- **Vorgerechnete Studie** (`generate_precomputed.py` → `precomputed_sweep.json`, rund fünf Minuten parallel): 3 Spurzahlen (10, 50, 200) ×
  3 Auslastungen (80, 90, 95 %) × 5 Wahlregeln (d = 1, 2, 3, 5, alle), je 4 Läufe à 800 000 Lkw. Live läuft ein Lauf mit 100 000 Lkw.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Wartezeiten in Minuten bei 3 min mittlerer Abfertigung.

| Frage | Befund |
|---|---|
| Wie viel bringt die zweite Auskunft? | Im Grenzwert sinkt die Wartezeit von d = 1 auf d = 2 um den Faktor **4.22 / 5.58 / 7.97** (Auslastung 80 / 90 / 95 %). Bei 90 %: 27.0 → 4.8 min. Simulation mit 200 Spuren: 4.21 / 5.53 / 7.71. |
| Und die dritte, die fünfte? | Von d = 2 auf 3 nur noch **1.63 / 1.57 / 1.55**, von 3 auf 5 **1.77 / 1.62 / 1.55**. Bei 90 %: 4.8 → 3.1 → 1.9 min. Die erste zusätzliche Auskunft ist die wichtigste; danach bleibt es bei Faktoren um 1.6 (1.55 bis 1.77), und der Sprung von d = 1 auf 2 wächst mit der Auslastung, die späteren Schritte nicht. |
| Wie verändert sich der Schwanz? | 200 Spuren, Auslastung 90 %, Anteil der Spuren mit mindestens 4 Lkw: d = 1 **66.0 %**, d = 2 **21.8 %**, d = 3 **2.1 %** (Grenzwert 65.6 / 20.6 / 1.5 %), d = 5 praktisch null (0.002 %). |
| Stimmt d = 1 mit M/M/1? | Ja, für jede Spurzahl: Abweichung der Simulation −4.7 % bis +1.4 % (Rauschen, ohne Richtung). |
| Wie viele Lkw finden eine freie Spur? | 1 − ρ^d: bei 200 Spuren stimmt die Simulation auf einen Prozentpunkt (d = 1, 2, 3, 5). |
| Ab wie vielen Spuren trägt der Grenzwert? | Die Simulation liegt **immer über** dem Grenzwert, mit 200 Spuren höchstens **+5.5 %**. Mit 50 Spuren: d = 2 +4.2 bis +8.6 %, d = 5 +13.8 bis +22.8 %. Mit 10 Spuren: d = 2 **+23 bis +48 %**, d = 5 **+76 bis +140 %**. Die Abweichung wächst mit d und mit der Auslastung (bei 10 und 50 Spuren in jeder Zelle). |
| Wie weit ist die gemeinsame Schlange voraus? | Auch mit voller Auskunft (JSQ) bleibt die Wartezeit **in allen neun Zellen** über der gemeinsamen Schlange (Verhältnis 1.22 bis 10.27); bei 90 %: **1.34** (10 Spuren), **2.36** (50), **4.38** (200). Das Verhältnis wächst mit N, weil die gemeinsame Schlange mit N fast auf null fällt; der absolute Abstand schrumpft dabei mit N (bei 90 %: 0.7 min bei 10 Spuren, 0.3 min bei 50, 0.05 min bei 200). |
| Absolute Zahlen? | 50 Spuren, 90 %: d = 1 **27.1 min**, d = 2 **5.1**, d = 3 3.4, d = 5 2.2, alle **0.5**, gemeinsame Schlange **0.2 min**. 10 Spuren, d = 2: **6.5 min** gegen 4.8 min im Grenzwert (+34 %), gemeinsame Schlange 2.0 min. 200 Spuren, 95 %: 55.8 / 7.2 / 4.7 / 3.1 / 0.3 min. |
| Wie verlässlich sind die Zahlen? | Der größte relative Standardfehler einer Zelle beträgt 5.6 % (Mittel aus 4 Läufen), die meisten liegen unter 2 %. |

## Befunde und Korrekturen gegenüber der Vorab-Messreihe

- **Faktoren der Vorab-Messreihe betrafen die Verweilzeit, nicht die Wartezeit.** Ich hatte „3.7- bis 5.9-fach“ für d = 1 auf 2 und
  „nur noch 23 %“ für d = 2 auf 3 angegeben. Das waren Verhältnisse der Verweilzeit (inklusive der Abfertigung, die sich nicht ändert).
  Für die Wartezeit, die Lkw tatsächlich spüren, sind es **5.6- bis 8.0-fach** und **−36 %** (Faktor 1.57 bei 90 %). Alle Zahlen dieser Demo
  sind Wartezeiten.
- **Die „+23 % bei 10 Spuren“ der Vorab-Messreihe** waren ebenfalls auf die Verweilzeit bezogen; für die Wartezeit sind es bei d = 2
  und 90 % **+34 %**.
- **Die Fluid-Referenz der Vorab-Messreihe war bei k = 12 abgeschnitten** und gab für d = 1 den Wert 6.86 statt 10 an (Summe zu früh
  abgebrochen); die Referenz läuft jetzt bis 10⁻¹⁵. Dass die Simulation bei d = 1 unter dem Formelwert lag, war Rauschen und Einschwingen kurzer Läufe.
- **Der Standardlauf der App ist untypisch.** Mit Seed 35 und 100 000 Lkw beträgt die tatsächliche Auslastung 91.3 % statt 90 %, und nur
  16.4 % der Lkw finden eine freie Spur (Grenzwert 19.0 %). Über die Seeds 35 bis 40 liegt die tatsächliche Auslastung zwischen 89.1 und 91.3 %.
  Die App zeigt die tatsächliche Auslastung des Laufs an; maßgeblich ist die Studie mit je 4 Läufen à 800 000 Lkw.
- **Bei 200 Spuren liegen d = 2 und d = 3 im Rauschen** (+2.2 gegen +1.5 % bei 90 %); die Reihenfolge „Abweichung wächst mit d“ gilt nur bei 10 und 50 Spuren.

## Ehrliche Grenzen

- Die Auskunft ist sofort und exakt. Veraltete Auskünfte (Herdenverhalten: viele Lkw wählen dieselbe „kürzeste“ Schlange) und die Kosten
  jeder Nachfrage sind nicht Teil der Rechnung.
- Gezogen wird **mit Zurücklegen**: bei kleinem N wird manchmal dieselbe Spur zweimal angesehen. Ziehen ohne Zurücklegen ist nicht gerechnet.
- Exponentielle Abfertigung, gleiche Spuren, keine Umstiege zwischen Schlangen, unendliche Schlange, konstante Last.
- Der Fluid-Grenzwert ist nur der Bezug; die Demo zeigt, dass er für kleine Gates deutlich zu optimistisch ist, rechnet aber keine
  verbesserte Näherung (etwa mit Korrekturtermen für endliches N).
- Der Live-Lauf ist kurz und streut, bei hoher Auslastung und d = 1 um Zehntel des Wertes; die Studie mittelt vier lange Läufe. Die Studie
  deckt nur 10, 50, 200 Spuren, 80, 90, 95 % und d = 1, 2, 3, 5, alle ab; die App zeigt für andere Werte die nächste Zelle und sagt es.

## Verwandte Demos im Portfolio

- [`mmc-queue-demo`](https://github.com/sebastian-hanisch/mmc-queue-demo) (Stück 3): eine gemeinsame Schlange, der Grenzfall dieser Demo.
- [`mm1-queue-demo`](https://github.com/sebastian-hanisch/mm1-queue-demo) (Stück 1): eine Spur, die Schlange bei d = 1.
- [`erlang-a-demo`](https://github.com/sebastian-hanisch/erlang-a-demo) (Stück 4): gemeinsame Schlange mit Abwanderung.
- [`truck-appointment-demo`](https://github.com/sebastian-hanisch/truck-appointment-demo): Terminvergabe für Lkw; dort planen Termine die
  Ankünfte, hier wählen die Lkw ihre Schlange.

## Bewusst nicht umgesetzt

Jede dieser Annahmen hebt ein Folgestück der Linie auf:

| Annahme | Folgestück |
|---|---|
| Exponentielle Abfertigung, gleiche Spuren | M/G/1, Kingman-Näherung |
| Alle Lkw gleich wichtig | Prioritätsklassen |
| Unbegrenzte Schlange | M/M/c/c (Erlang B) |
| Konstante Ankunftsrate | [Zeitvariable Ankünfte](https://github.com/sebastian-hanisch/time-varying-arrivals-demo) |
| Ein Gate | Jackson-Netze |

Kein Folgestück: veraltete Auskünfte und Kosten der Nachfrage, Umstiege zwischen Schlangen.

## Tests

122 Tests, rund 2 Minuten: Fluid-Rekursion von Hand und gegen die geschlossene Form, d = 1 gleich M/M/1, Doppel-Exponential-Verhalten, Erlang C
gegen die Summenformel, die Wahlregel einzeln (Gleichstände, Zurücklegen, JSQ), eine von Hand gerechnete Mini-Instanz (Ankunftszeiten, Wartezeit,
alle Zeitintegrale), das Gesetz von Little als exakte Pfad-Identität, Invarianten des Zustands, gleicher Seed gleiches Ergebnis, die gelöste
Markov-Kette (N = 2 und 3, auch der Pfad mit Stichprobenwahl) gegen die Simulation, Vollständigkeit der vorgerechneten Datei, Presets und
Permalink, Diagramme (gesperrte Achsen), AppTest-Rauchtests, der Smoke-Test der Portfolio-Vorlage (Schaltflächen, Regler an den Grenzen), ein Quelltext-Test gegen Satz-Komma-Fehler und `test_claims.py` für jede Zahl
dieser README.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `pod_formulas.py` | Fluid-Grenzwert, M/M/1, Erlang C |
| `pod_simulation.py` | Wahlregel, Ereignisschleife, Zeitintegrale |
| `pod_evaluation.py` | Live-Lauf, Studienzelle, Laden |
| `generate_precomputed.py` | rechnet die Studie vor → `precomputed_sweep.json` |
| `pod_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `pod_presets.py`, `pod_constants.py` | Presets, Permalink, Grenzen |
| `tests/` | siehe oben; `ctmc_reference.py` ist die unabhängige Markov-Kette |

## Literatur

- Vvedenskaya, N. D., Dobrushin, R. L., Karpelevich, F. I. (1996): Queueing system with selection of the shortest of two queues: an asymptotic
  approach. *Problems of Information Transmission* 32(1), 15–27 (Grenzwert für viele Spuren, Schwanz fällt überexponentiell).
- Mitzenmacher, M. (2001): The power of two choices in randomized load balancing. *IEEE Transactions on Parallel and Distributed Systems*
  (Fluid-Gleichungen des „Supermarkt-Modells“; d = 2 verbessert die Wartezeit gegenüber d = 1 exponentiell, d = 3 gegenüber d = 2 nur um einen
  konstanten Faktor).

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests/ -v`. Studie neu rechnen: `python generate_precomputed.py`.

Gebaut mit Streamlit und Plotly.
