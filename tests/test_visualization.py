"""Abbildungen: Formulierungshelfer, gesperrte Achsen, Zahl der Linien, keine nicht-positiven Werte auf Log-Achsen."""

import pod_constants as C
import pod_evaluation as E
import pod_formulas as F
import pod_visualization as V

PRE = E.load_precomputed()


def test_wording_helpers():
    assert [V.d_label(d) for d in C.D_OPTIONS] == ["1", "2", "3", "5", "alle (JSQ)"]
    assert [V.d_name(d) for d in C.D_OPTIONS] == ["d = 1", "d = 2", "d = 3", "d = 5", "alle (JSQ)"]
    assert [V.d_phrase(d) for d in C.D_OPTIONS] == ["eine Schlange", "2 Schlangen", "3 Schlangen", "5 Schlangen", "alle Schlangen"]


def _locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def test_all_charts_lock_their_axes():
    live = E.live_report(10, 0.9, 2, seed=1, customers=6_000)
    figs = [V.build_tail_chart(live["tail_sim"], live["tail_fluid"], live["tail_base_fluid"], 2),
            V.build_snapshot_chart(live["lens"], live["lens_base"], 2), V.build_choices_chart(PRE, 0.9), V.build_gap_chart(PRE, 0.9),
            V.build_pooling_chart(PRE, 50, 0.9)]
    assert all(_locked(f) for f in figs)


def test_tail_chart_drops_zeros_for_the_log_axis_and_skips_the_baseline_for_d_one():
    fig = V.build_tail_chart([1.0, 0.5, 0.0], F.fluid_tail(0.5, 2), F.fluid_tail(0.5, 1), 2)
    assert len(fig.data) == 3 and None in list(fig.data[2].y) and 0.0 not in list(fig.data[2].y)
    assert len(V.build_tail_chart([1.0, 0.5], F.fluid_tail(0.5, 1), F.fluid_tail(0.5, 1), 1).data) == 2


def test_pooling_chart_has_one_bar_per_rule_plus_the_pooled_queue():
    fig = V.build_pooling_chart(PRE, 50, 0.9)
    assert list(fig.data[0].x) == ["d = 1", "d = 2", "d = 3", "d = 5", "alle (JSQ)", "gemeinsame Schlange (Erlang C)"]
    assert all(v > 0 for v in fig.data[0].y)


def test_choices_chart_has_a_line_and_a_marker_trace_per_load():
    assert len(V.build_choices_chart(PRE, 0.9).data) == 2 * len(C.STUDY_RHO)


def test_snapshot_chart_sorts_the_lengths_descending_and_marks_the_baseline():
    fig = V.build_snapshot_chart([1, 3, 2], [0, 5, 1], 2)
    assert list(fig.data[1].y) == [3, 2, 1] and list(fig.data[0].y) == [5, 1, 0]
    assert len(V.build_snapshot_chart([1, 3, 2], [1, 3, 2], 1).data) == 1
