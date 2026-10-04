"""Presets: Vollständigkeit, gültige Werte, Permalink-Konstanten."""

import pytest

import pod_constants as C
import pod_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER) and len(C.PRESETS) == 4
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for preset in C.PRESETS.values():
        assert preset["n"] in C.N_OPTIONS and C.RHO_PCT_MIN <= preset["rho_pct"] <= C.RHO_PCT_MAX and preset["d"] in C.D_OPTIONS
        assert P.snap_rho(preset["rho_pct"]) == preset["rho_pct"]
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(preset[key])


def test_preset_names_state_the_values_they_set():
    assert C.PRESETS["Eine Wahl genügt (d = 2)"]["d"] == 2 and C.PRESETS["Kleines Gate (10 Spuren)"]["n"] == 10
    assert C.PRESETS["Volle Auskunft (JSQ)"]["d"] == C.D_ALL and C.PRESETS["Hohe Auslastung (95 %)"]["rho_pct"] == 95


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Eine Wahl genügt (d = 2)"]
    assert (p["n"], p["rho_pct"], p["d"], p["seed"]) == (C.DEFAULT_N, C.DEFAULT_RHO_PCT, C.DEFAULT_D, C.DEFAULT_SEED)


def test_bounds_and_url_params():
    assert P.bounds("seed_input") == (0, C.SEED_MAX) and P.bounds("n_select") == (10, 200)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


@pytest.mark.parametrize("key,value,expected", [("n_select", 30, 25), ("n_select", 76, 100), ("n_select", 5, 10), ("n_select", 150, 100),
                                                ("d_select", 4, 3), ("d_select", 40, 5), ("d_select", 500, 5), ("d_select", 700, C.D_ALL)])
def test_option_regulators_snap_to_the_nearest_option(key, value, expected):
    assert P.snap_to_option(key, value) == expected


@pytest.mark.parametrize("value,expected", [(50, 50), (52, 50), (53, 55), (87, 85), (88, 90), (99, 95), (10, 50), (-5, 50)])
def test_utilisation_snaps_to_the_step_inside_the_bounds(value, expected):
    assert P.snap_rho(value) == expected


def test_formatters():
    assert C.fmt_int(150000) == "150.000" and C.fmt_pct(0.2) == "20 %" and C.fmt_pct(0.0898, 1) == "9.0 %"
