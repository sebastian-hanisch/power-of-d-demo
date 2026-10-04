"""JEDE Zahl aus README und App-Texten wird hier nachgerechnet: Formelwerte exakt, Studien-Zahlen aus der vorgerechneten Datei (4 Läufe à
800 000 Lkw je Zelle). Die Datei ist fest; ändern sich die Zahlen nach einer neuen Rechnung, müssen README und Hilfetexte nachgezogen
werden. Wartezeiten in Minuten bei 3 min mittlerer Abfertigung."""

import pytest

import pod_constants as C
import pod_evaluation as E
import pod_formulas as F

PRE = E.load_precomputed()


def cell(n, rho, d):
    return E.study_cell(PRE, n, rho, d)


def minutes(x):
    return 3 * x


def test_limit_improvement_factors_quoted_in_readme():
    """README (Grenzwert, exakt): Wartezeit von d = 1 auf 2 sinkt um den Faktor 4.22 / 5.58 / 7.97 (ρ = 80 / 90 / 95 %), von 2 auf 3 um
    1.63 / 1.57 / 1.55, von 3 auf 5 um 1.77 / 1.62 / 1.55; bei ρ = 90 % in Minuten 27.0 / 4.8 / 3.1 / 1.9 für d = 1, 2, 3, 5."""
    rhos = (0.8, 0.9, 0.95)
    assert [round(F.improvement_factor(r, 1, 2), 2) for r in rhos] == [4.22, 5.58, 7.97]
    assert [round(F.improvement_factor(r, 2, 3), 2) for r in rhos] == [1.63, 1.57, 1.55]
    assert [round(F.improvement_factor(r, 3, 5), 2) for r in rhos] == [1.77, 1.62, 1.55]
    assert [round(minutes(F.fluid_wait(0.9, d)), 1) for d in (1, 2, 3, 5)] == [27.0, 4.8, 3.1, 1.9]
    assert round(minutes(F.fluid_wait(0.95, 1)), 1) == 57.0 and round(minutes(F.fluid_wait(0.8, 1)), 1) == 12.0


def test_simulation_with_200_lanes_reproduces_the_limit_factors():
    """README: Simulation mit 200 Spuren, Faktor von d = 1 auf 2: 4.21 / 5.53 / 7.71; von 2 auf 3: 1.63 / 1.58 / 1.54."""
    rhos = (0.8, 0.9, 0.95)
    assert [round(cell(200, r, 1)["wait"] / cell(200, r, 2)["wait"], 2) for r in rhos] == pytest.approx([4.21, 5.53, 7.71], abs=0.005)
    assert [round(cell(200, r, 2)["wait"] / cell(200, r, 3)["wait"], 2) for r in rhos] == pytest.approx([1.63, 1.58, 1.54], abs=0.005)


def test_d_one_is_mm1_in_every_cell():
    """README: Ohne Wahl (d = 1) stimmt die Simulation für jedes N mit M/M/1 überein: Abweichung −4.7 % bis +1.4 % (Rauschen, im Mittel
    ohne Richtung)."""
    gaps = [100 * (cell(n, r, 1)["wait"] / F.mm1_wait(r) - 1) for n in C.STUDY_N for r in C.STUDY_RHO]
    assert (round(min(gaps), 1), round(max(gaps), 1)) == pytest.approx((-4.7, 1.4), abs=0.051)


def test_limit_gap_shrinks_with_the_number_of_lanes_and_grows_with_d_and_load():
    """README: Abweichung der simulierten Wartezeit vom Grenzwert (immer nach oben; wächst mit d und ρ, bei 200 Spuren liegen d = 2 und 3 im Rauschen): 200 Spuren höchstens +5.5 %; 50 Spuren d = 2: +4.2 bis
    +8.6 %, d = 5: +13.8 bis +22.8 %; 10 Spuren d = 2: +23 bis +48 %, d = 5: +76 bis +140 %."""
    def gap(n, r, d):
        return 100 * (cell(n, r, d)["wait"] / F.fluid_wait(r, d) - 1)
    rhos = C.STUDY_RHO
    assert round(max(gap(200, r, d) for r in rhos for d in (2, 3, 5)), 1) == pytest.approx(5.5, abs=0.051)
    assert [round(gap(50, r, 2), 1) for r in rhos] == pytest.approx([4.2, 5.4, 8.6], abs=0.051)
    assert [round(gap(50, r, 5), 1) for r in rhos] == pytest.approx([13.8, 18.3, 22.8], abs=0.051)
    assert [round(gap(10, r, 2)) for r in rhos] == [23, 34, 48] and [round(gap(10, r, 5)) for r in rhos] == [76, 92, 140]
    for n_small, n_big in ((10, 50), (50, 200)):
        for r in rhos:
            for d in (2, 3, 5):
                assert gap(n_small, r, d) > gap(n_big, r, d), (n_small, r, d)
    for n in C.STUDY_N:                                  # mit der Auslastung wächst die Abweichung in jeder Zelle
        for d in (2, 3, 5):
            if n < 200:
                assert gap(n, 0.8, d) < gap(n, 0.9, d) < gap(n, 0.95, d), (n, d)
    for n in (10, 50):                                   # bei 200 Spuren liegen d = 2 und 3 im Rauschen (+2.2 gegen +1.5 % bei ρ = 90 %)
        for r in rhos:
            assert gap(n, r, 2) < gap(n, r, 3) < gap(n, r, 5), (n, r)


def test_tail_of_the_queue_lengths_quoted_in_readme():
    """README (200 Spuren, ρ = 90 %): Anteil der Spuren mit mindestens 4 Lkw: d = 1 66.0 %, d = 2 21.8 %, d = 3 2.1 % (Grenzwert 65.6 /
    20.6 / 1.5 %), d = 5 praktisch null (0.002 %)."""
    got = [round(100 * cell(200, 0.9, d)["tail"][3], 1) for d in (1, 2, 3)]
    assert got == pytest.approx([66.0, 21.8, 2.1], abs=0.051)
    assert [round(100 * F.fluid_tail(0.9, d)[4], 1) for d in (1, 2, 3)] == pytest.approx([65.6, 20.6, 1.5], abs=0.051)
    assert round(100 * cell(200, 0.9, 5)["tail"][3], 3) == pytest.approx(0.002, abs=0.0005)


def test_free_lane_share_matches_one_minus_rho_to_the_d_for_large_gates():
    """README: Anteil der Lkw mit freier Spur stimmt bei 200 Spuren auf einen Prozentpunkt mit 1 − ρ^d überein (d = 1, 2, 3, 5)."""
    for r in C.STUDY_RHO:
        for d in (1, 2, 3, 5):
            assert abs(cell(200, r, d)["idle"] - F.prob_idle_found(r, d)) < 0.0101, (r, d)


def test_jsq_stays_behind_the_pooled_queue_and_the_ratio_grows_with_n():
    """README: Auch bei Kenntnis aller Schlangen (JSQ) bleibt die Wartezeit über der gemeinsamen Schlange in allen neun Zellen
    (Verhältnis 1.22 bis 10.27); bei ρ = 90 %: 1.34 (10 Spuren), 2.36 (50), 4.38 (200)."""
    ratios = {(n, r): cell(n, r, C.D_ALL)["wait"] / F.pooled_wait(n, r) for n in C.STUDY_N for r in C.STUDY_RHO}
    assert all(v > 1 for v in ratios.values())
    assert (round(min(ratios.values()), 2), round(max(ratios.values()), 2)) == pytest.approx((1.22, 10.27), abs=0.0051)
    assert [round(ratios[(n, 0.9)], 2) for n in C.STUDY_N] == pytest.approx([1.34, 2.36, 4.38], abs=0.0051)
    for r in C.STUDY_RHO:                                                          # Verhältnis wächst mit N, der absolute Abstand schrumpft
        assert ratios[(10, r)] < ratios[(50, r)] < ratios[(200, r)]
        diffs = [cell(n, r, C.D_ALL)["wait"] - F.pooled_wait(n, r) for n in C.STUDY_N]
        assert diffs[0] > diffs[1] > diffs[2] > 0
    diffs90 = [round(minutes(cell(n, 0.9, C.D_ALL)["wait"] - F.pooled_wait(n, 0.9)), 2) for n in C.STUDY_N]
    assert diffs90 == pytest.approx([0.7, 0.3, 0.05], abs=0.03)                    # README: 0.7 / 0.3 / 0.05 min


def test_absolute_waits_quoted_in_readme_and_presets():
    """README/Presets (50 Spuren, ρ = 90 %): d = 1 27.1 min, d = 2 5.1, d = 3 3.4, d = 5 2.2, JSQ 0.5, gemeinsam 0.2; 10 Spuren d = 2: 6.5 min
    gegen 4.8 min im Grenzwert (+34 %), gemeinsam 2.0 min; 200 Spuren, ρ = 95 %: 55.8 / 7.2 / 4.7 / 3.1 / 0.3 min."""
    assert [round(minutes(cell(50, 0.9, d)["wait"]), 1) for d in C.STUDY_D] == pytest.approx([27.1, 5.1, 3.4, 2.2, 0.5], abs=0.0001)
    assert round(minutes(F.pooled_wait(50, 0.9)), 1) == 0.2
    assert format(minutes(cell(10, 0.9, 2)["wait"]), ".1f") == "6.5" and format(minutes(F.fluid_wait(0.9, 2)), ".1f") == "4.8"
    assert round(100 * (cell(10, 0.9, 2)["wait"] / F.fluid_wait(0.9, 2) - 1)) == 34 and round(minutes(F.pooled_wait(10, 0.9)), 1) == 2.0
    assert [round(minutes(cell(200, 0.95, d)["wait"]), 1) for d in C.STUDY_D] == pytest.approx([55.8, 7.2, 4.7, 3.1, 0.3], abs=0.0001)


def test_preset_help_numbers():
    """PRESET_HELP: jede Zahl aus den vier Texten (siehe pod_constants)."""
    m = lambda n, r, d: format(minutes(cell(n, r, d)["wait"]), ".1f")
    h = C.PRESET_HELP
    assert all(x in h["Eine Wahl genügt (d = 2)"] for x in (m(50, 0.9, 1), m(50, 0.9, 2), m(50, 0.9, C.D_ALL)))
    assert format(minutes(F.pooled_wait(50, 0.9)), ".1f") == "0.2" and "0.2 min" in h["Eine Wahl genügt (d = 2)"]
    assert m(10, 0.9, 2) in h["Kleines Gate (10 Spuren)"] and "4.8 min" in h["Kleines Gate (10 Spuren)"] and "34 %" in h["Kleines Gate (10 Spuren)"]
    assert "2.0 min" in h["Kleines Gate (10 Spuren)"]
    assert m(50, 0.9, C.D_ALL) in h["Volle Auskunft (JSQ)"] and m(50, 0.9, 2) in h["Volle Auskunft (JSQ)"] and "2.4-mal" in h["Volle Auskunft (JSQ)"]
    assert round(cell(50, 0.9, C.D_ALL)["wait"] / F.pooled_wait(50, 0.9), 1) == 2.4
    assert all(x in h["Hohe Auslastung (95 %)"] for x in (m(200, 0.95, 1), m(200, 0.95, 2), m(200, 0.95, C.D_ALL)))


def test_noise_level_of_the_study_quoted_in_readme():
    """README: Der größte relative Standardfehler einer Zelle beträgt 5.6 % (Mittel aus 4 Läufen), meist unter 2 %."""
    rel = [x["wait_se"] / x["wait"] for x in PRE["study"]]
    assert round(100 * max(rel), 1) == 5.6
    assert sum(1 for r in rel if r < 0.02) >= 0.7 * len(rel)


def test_default_live_run_has_a_realized_load_above_the_nominal_one():
    """README/App-Hinweis: Der Standard-Live-Lauf (50 Spuren, ρ = 90 %, d = 2, Seed 35, 100 000 Lkw) hat eine tatsächliche Auslastung von
    91.3 % und findet bei 16.4 % der Lkw eine freie Spur (Grenzwert 19.0 %); über die Seeds 35 bis 40 liegt die Auslastung zwischen 89.1 und 91.3 %."""
    live = E.live_report(50, 0.9, 2, seed=35)
    assert live["sim"].utilisation == pytest.approx(0.913, abs=0.0006) and live["idle_sim"] == pytest.approx(0.164, abs=0.0006)
    assert round(100 * live["idle_fluid"], 1) == 19.0
    utils = [E.live_report(50, 0.9, 2, seed=s)["sim"].utilisation for s in range(35, 41)]
    assert (round(100 * min(utils), 1), round(100 * max(utils), 1)) == pytest.approx((89.1, 91.3), abs=0.06)
