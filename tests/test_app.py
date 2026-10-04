"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Randwerte, Würfel-Knopf, Permalink-Grenzen, Abschnitte, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import pod_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=600)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_default_run_has_no_exception_and_shows_all_reference_values():
    at = _run()
    _ok(at)
    assert _metric(at, "Ohne Wahl (d = 1, Formel M/M/1)") == "27.00 min"                      # ρ = 0.9: 9 Abfertigungsdauern à 3 min
    assert _metric(at, "Mittlere Wartezeit (Grenzwert für viele Spuren)") == "4.84 min"        # 1.614 Abfertigungsdauern
    assert _metric(at, "Wartezeit-Verhältnis gegenüber d = 1 (Grenzwert)") == "1 : 5.6"
    assert float(_metric(at, "Mittlere Wartezeit (Simulation)").split()[0]) > 0


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["n_select"] == p["n"] and at.session_state["d_select"] == p["d"] and at.session_state["rho_slider"] == p["rho_pct"]
    assert at.metric


def test_jsq_has_no_waiting_in_the_limit_and_shows_a_text_instead_of_a_ratio():
    at = _run(d_select=C.D_ALL)
    _ok(at)
    assert _metric(at, "Mittlere Wartezeit (Grenzwert für viele Spuren)") == "0.00 min"
    assert _metric(at, "Wartezeit-Verhältnis gegenüber d = 1 (Grenzwert)") == "Wartezeit null"


def test_d_one_is_the_baseline_and_needs_no_second_run():
    at = _run(d_select=1)
    _ok(at)
    assert _metric(at, "Wartezeit-Verhältnis gegenüber d = 1 (Grenzwert)") == "1 : 1"
    assert _metric(at, "Mittlere Wartezeit (Grenzwert für viele Spuren)") == _metric(at, "Ohne Wahl (d = 1, Formel M/M/1)")


@pytest.mark.parametrize("kw", [dict(n_select=10, rho_slider=95, d_select=C.D_ALL), dict(n_select=200, rho_slider=50, d_select=5),
                                 dict(n_select=25, rho_slider=70, d_select=3), dict(n_select=100, rho_slider=60, d_select=1),
                                 dict(n_select=10, rho_slider=50, d_select=2)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_more_choices_give_a_shorter_limit_wait_in_the_app():
    wait = lambda at: float(_metric(at, "Mittlere Wartezeit (Grenzwert für viele Spuren)").split()[0])
    assert wait(_run(d_select=1)) > wait(_run(d_select=2)) > wait(_run(d_select=3)) > wait(_run(d_select=5)) > 0


def test_dice_button_changes_the_seed_and_the_simulated_run():
    """Die Kennzahl ist gerundet; deshalb vergleicht der Test die Daten des Diagramms der Schlangenlängen (CI-Erfahrung aus Stück 6)."""
    at = _run()
    old_seed, old = at.session_state["seed_input"], at.get("plotly_chart")[0].proto.spec
    next(b for b in at.button if b.label == "🎲 Neuen Lauf würfeln").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old_seed and at.get("plotly_chart")[0].proto.spec != old


def test_permalink_values_are_clamped_and_snapped():
    at = AppTest.from_file(APP, default_timeout=600)
    at.query_params["n"] = "30"
    at.query_params["rho"] = "87"
    at.query_params["d"] = "4"
    at.run()
    _ok(at)
    assert at.session_state["n_select"] == 25 and at.session_state["rho_slider"] == 85 and at.session_state["d_select"] == 3


def test_permalink_ignores_garbage():
    at = AppTest.from_file(APP, default_timeout=600)
    at.query_params["rho"] = "viel"
    at.query_params["d"] = "nan"
    at.run()
    _ok(at)
    assert at.session_state["rho_slider"] == C.DEFAULT_RHO_PCT and at.session_state["d_select"] == C.DEFAULT_D


def test_charts_sections_and_limits_table_are_present():
    at = _run()
    _ok(at)
    assert len(at.get("plotly_chart")) == 5
    headers = [s.value for s in at.subheader]
    for part in ("Wie viel bringt jede weitere Auskunft", "Ab wie vielen Spuren trägt der Grenzwert", "gemeinsame Schlange noch voraus",
                 "Wo die Annahmen enden"):
        assert any(part in h for h in headers), part
    table = next(m.value for m in at.markdown if "Wer setzt an" in m.value)
    for name in ("Kingman", "Prioritätsklassen", "Erlang B", "Jackson-Netze", "Zeitvariable Ankünfte"):
        assert name in table
    assert "geplant" not in table      # die Linie wird erst vollständig veröffentlicht, kein Status-Zusatz


def test_tables_of_the_choices_and_gap_sections_are_complete():
    at = _run()
    choices = next(m.value for m in at.markdown if m.value.startswith("| Auskünfte d |"))
    for label in ("| 1 |", "| 2 |", "| 3 |", "| 5 |", "| alle (JSQ) |"):
        assert label in choices
    gap = next(m.value for m in at.markdown if m.value.startswith("| d |"))
    for k in C.STUDY_N:
        assert f"{k} Spuren" in gap


def test_seed_control_uses_the_portfolio_wording():
    at = _run()
    assert [n.label for n in at.number_input] == ["Zufalls-Seed"]


def test_related_demos_are_linked_and_footer_is_present():
    at = _run()
    text = " ".join(c.value for c in at.caption)
    for name in ("mmc-queue-demo", "mm1-queue-demo", "erlang-a-demo", "truck-appointment-demo"):
        assert name in text
    assert "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in text


def test_no_sentence_wide_comma_replacement_in_the_app_source():
    """Regressionsschutz: `.replace(",", ".")` auf einem ganzen (verketteten) Satz macht aus Kommas im Fließtext Punkte; Tausender
    nur über `fmt_int`."""
    source = Path(APP).read_text(encoding="utf-8")
    assert '.replace(",", ".")' not in source
