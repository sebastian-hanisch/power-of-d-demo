"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).
Alle Regler sind immer sichtbar - es gibt keinen ausblendbaren Regler (also auch kein KEPT-Muster)."""

import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import pod_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_select": SettingSpec("n", int, C.DEFAULT_N, C.N_OPTIONS[0], C.N_OPTIONS[-1]),
    "rho_slider": SettingSpec("rho", int, C.DEFAULT_RHO_PCT, C.RHO_PCT_MIN, C.RHO_PCT_MAX),
    "d_select": SettingSpec("d", int, C.DEFAULT_D, C.D_OPTIONS[0], C.D_OPTIONS[-1]),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"n": "n_select", "rho_pct": "rho_slider", "d": "d_select", "seed": "seed_input"}
OPTIONS = {"n_select": C.N_OPTIONS, "d_select": C.D_OPTIONS}       # Regler, die nur feste Stufen kennen


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def snap_to_option(state_key, value):
    """Regler mit festen Stufen: ein Permalink-Wert dazwischen rastet auf die nächste Stufe ein (bei Gleichstand auf die kleinere)."""
    return min(OPTIONS[state_key], key=lambda o: (abs(o - value), o))


def snap_rho(value):
    """Die Auslastung rastet auf das nächste Vielfache der Schrittweite (5 Prozentpunkte) innerhalb der Grenzen ein."""
    snapped = round(value / C.RHO_PCT_STEP) * C.RHO_PCT_STEP
    return int(min(C.RHO_PCT_MAX, max(C.RHO_PCT_MIN, snapped)))


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if value != value:                     # NaN
                    continue
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                if state_key in OPTIONS:
                    value = snap_to_option(state_key, value)
                if state_key == "rho_slider":
                    value = snap_rho(value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
