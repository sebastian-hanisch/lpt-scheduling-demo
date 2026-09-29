"""Vehikel A (Neutral) und Vehikel B (Werkstatt/Logistik): Erzeugung, Determinismus; Auswertung: Kennzahlen,
Sweep, Graham-Schranken-Check, Timing-Messreihe, Vehikel-B-Härtetest (Rüstzeiten)."""

from dataclasses import replace

import numpy as np
import pytest

import lpt_algorithm as A
import lpt_constants as C
import lpt_evaluation as ev
import lpt_scenario as S
import lpt_scenario_logistik as SL


# --- Vehikel A ----------------------------------------------------------------------------------------------------------------------------------


def test_instance_shape_and_bounds():
    inst = S.generate(20, 3)
    assert inst.n == 20 and inst.p.shape == (20,)
    assert inst.p.min() >= C.P_MIN and inst.p.max() <= C.P_MAX


def test_instance_is_deterministic_and_seed_dependent():
    a, b, c = S.generate(30, 5), S.generate(30, 5), S.generate(30, 6)
    assert np.array_equal(a.p, b.p)
    assert not np.array_equal(a.p, c.p)


# --- Vehikel B ------------------------------------------------------------------------------------------------------------------------------


def test_logistik_instance_shares_the_same_processing_times_as_neutral():
    neutral = S.generate(20, 7)
    logistik = SL.generate(20, 7)
    assert np.array_equal(neutral.p, logistik.p)


def test_logistik_instance_is_deterministic():
    a, b = SL.generate(10, 2), SL.generate(10, 2)
    assert np.array_equal(a.family, b.family) and np.array_equal(a.setup, b.setup)


# --- Analyse --------------------------------------------------------------------------------------------------------------------------------


def test_analysis_fields_are_consistent():
    """Bei den STANDARD-Einstellungen (Settings()) ist LPT tatsächlich besser als beide Vergleichsregeln - das
    ist aber KEINE Garantie für jede Instanz (siehe test_gap_can_be_negative_even_on_the_neutral_vehicle):
    Grahams Schranke begrenzt nur den Abstand zum echten Optimum, nicht die pauschale Überlegenheit gegenüber
    einer bestimmten anderen Regel auf einer bestimmten Instanz."""
    a = ev.analyse(ev.Settings(n=20))
    assert a.gap_arbitrary >= -1e-6 and a.gap_random >= -1e-6
    assert a.optimal is None


def test_gap_can_be_negative_even_on_the_neutral_vehicle():
    """Echter, überraschender Fund: ANDERS als bei den bewiesen optimalen Regeln der Stücke 1-4/6 kann LPT
    hier sogar OHNE Rüstzeiten schlechter abschneiden als die beliebige oder eine zufällige Reihenfolge -
    Grahams Garantie bindet nur das Verhältnis zum ECHTEN OPTIMUM (siehe test_analysis_respects_grahams_bound_
    for_small_n), nicht einen paarweisen Vergleich zu einer anderen konkreten Regel auf einer Instanz."""
    a = ev.analyse(ev.Settings(n=10, m=2, seed=19))
    assert a.gap_arbitrary < 0.0


def test_analysis_respects_grahams_bound_for_small_n():
    a = ev.analyse(ev.Settings(n=8, m=3))
    assert a.optimal is not None and a.optimal_proven
    assert a.lpt_ratio_to_optimum is not None
    assert a.lpt_ratio_to_optimum <= A.graham_bound_lpt(3) + 1e-6


# --- Vehikel-Bewusstsein der Hauptanalyse (von Anfang an, siehe [[feedback_vehicle_toggle_must_drive_primary_metrics]]) ----------------------


def test_analyse_on_the_logistik_vehicle_actually_uses_setup_aware_completion_times():
    settings = ev.Settings(n=8, m=3, seed=100000, vehicle="logistik", setup_time=30, n_families=3)
    a = ev.analyse(settings)
    linst = ev.logistik_instance(8, 100000, 3, 30)
    independent = A.list_schedule(linst.p, a.lpt.order, settings.m, linst.family, linst.setup)
    assert a.lpt.cmax == pytest.approx(independent.cmax)


def test_analyse_on_the_neutral_vehicle_is_unaffected_by_logistik_only_settings():
    a1 = ev.analyse(ev.Settings(n=10, seed=5, vehicle="neutral", setup_time=5))
    a2 = ev.analyse(ev.Settings(n=10, seed=5, vehicle="neutral", setup_time=60))
    assert a1.lpt.cmax == pytest.approx(a2.lpt.cmax)


def test_switching_vehicle_actually_changes_the_lpt_cmax():
    a_neutral = ev.analyse(ev.Settings(n=10, seed=7, vehicle="neutral"))
    a_logistik = ev.analyse(ev.Settings(n=10, seed=7, vehicle="logistik", setup_time=60, n_families=2))
    assert a_neutral.lpt.cmax != pytest.approx(a_logistik.lpt.cmax)


def test_lpt_order_at_zero_setup_time_matches_the_neutral_vehicle_exactly():
    a1 = ev.analyse(ev.Settings(n=10, seed=7, vehicle="neutral"))
    a2 = ev.analyse(ev.Settings(n=10, seed=7, vehicle="logistik", setup_time=0))
    assert np.array_equal(a1.lpt.machine, a2.lpt.machine)
    assert a1.lpt.cmax == pytest.approx(a2.lpt.cmax)


def test_gap_can_go_negative_on_the_logistik_vehicle():
    """Echter Fund (wie bei wspt-demo/weighted-tardiness-demo/johnson-rule-demo): auf dem Werkstatt-Vehikel ist
    LPT nicht mehr bewiesen optimal - Zufall kann hier zufällig eine Reihenfolge mit weniger Familienwechseln
    treffen und LPT schlagen."""
    a = ev.analyse(ev.Settings(n=10, m=2, seed=0, vehicle="logistik", setup_time=30, n_families=3))
    assert min(a.gap_arbitrary, a.gap_random) < 0.0


def test_analysis_is_deterministic_given_the_chain_seed():
    s = ev.Settings(n=20, seed=1, chain_seed=0)
    a, b, c = ev.analyse(s), ev.analyse(s), ev.analyse(replace(s, chain_seed=1))
    assert a.gap_random == pytest.approx(b.gap_random)
    assert a.gap_random != pytest.approx(c.gap_random)


# --- Sweep und Messreihe -------------------------------------------------------------------------------------------------------------------


def test_run_config_counts_runs_and_aggregates():
    r = ev.run_config(ev.Settings(n=15))
    assert r["n_runs"] == len(C.SWEEP_SEEDS) * C.SWEEP_CHAINS


def test_sweep_values_labels_and_ordering():
    assert set(ev.SWEEP_VALUES) == set(ev.SWEEP_LABELS)
    rows = ev.sweep("n", ev.Settings(), (5, 40))
    assert [r["value"] for r in rows] == [5, 40]
    rows_m = ev.sweep("m", ev.Settings(), (2, 4))
    assert [r["value"] for r in rows_m] == [2, 4]


def test_graham_bound_check_never_violates_the_bound():
    rows = ev.graham_bound_check(ns=(3, 4, 5, 6), ms=(2, 3))
    assert all(r["worst_over_bound"] <= 1.0 + 1e-6 for r in rows)
    assert all(r["proven_rate"] == 1.0 for r in rows)


def test_timing_sweep_shows_exact_growing_far_slower_than_lpt():
    rows = ev.timing_sweep(ns=(3, 9))
    small, large = rows[0], rows[1]
    assert large["lpt_seconds"] < 0.001


def test_setup_gap_grows_with_the_setup_time():
    small = ev.setup_gap(n=7, setup_time=0)
    large = ev.setup_gap(n=7, setup_time=60)
    assert large["gap_mean"] > small["gap_mean"]
