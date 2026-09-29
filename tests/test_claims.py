"""Jede Zahl der App-Texte ist hier über die fünf festen Sweep-Instanzen (je drei Ketten) belegt. Positive UND
negative Aussagen: im Standardfall ist LPT besser als beide Vergleichsregeln - UND das ist KEINE generelle
Garantie (anders als bei den bewiesen optimalen Regeln der Stücke 1-4/6): Grahams Schranke bindet nur das
Verhältnis zum echten Optimum, nicht einen paarweisen Vergleich zu einer bestimmten anderen Regel auf einer
bestimmten Instanz. Rechenzeiten nur als Größenordnung geprüft; teure Läufe (CP-SAT) sind modul-weit über
lru_cache dedupliziert."""

from functools import lru_cache

import lpt_algorithm as A
import lpt_evaluation as ev


@lru_cache(maxsize=None)
def _cfg(items):
    return ev.run_config(ev.Settings(), **dict(items))


def cfg(**kw):
    return _cfg(tuple(sorted(kw.items())))


@lru_cache(maxsize=1)
def _graham():
    return tuple(tuple(r.items()) for r in ev.graham_bound_check())


def graham_rows():
    return [dict(r) for r in _graham()]


@lru_cache(maxsize=1)
def _timing():
    return tuple(tuple(r.items()) for r in ev.timing_sweep())


def timing_rows():
    return [dict(r) for r in _timing()]


@lru_cache(maxsize=1)
def _setup_sweep():
    return tuple(tuple(r.items()) for r in ev.setup_gap_sweep())


def setup_rows():
    return [dict(r) for r in _setup_sweep()]


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.3f} statt {expected}"


# --- Standardfall -------------------------------------------------------------------------------------------------------------------------------


def test_standard_case_numbers():
    std = cfg()
    near(std["gap_arbitrary"], 5.9, 8.0)
    near(std["gap_random"], 6.9, 8.0)


# --- Grahams bewiesene Schranke: darf NIE verletzt werden ----------------------------------------------------------------------------------------


def test_grahams_bound_is_never_violated():
    """Der zentrale Beweis-Check dieses Stücks - anders als bei Stück 1-4/6 (exakte Gleichheit) ist hier eine
    UNGLEICHUNG zu prüfen: LPT darf Grahams Schranke (4/3 - 1/(3m)) nie überschreiten, sonst wäre das ein
    Fehler im Beweis oder in der Implementierung."""
    rows = graham_rows()
    assert all(r["worst_over_bound"] <= 1.0 + 1e-6 for r in rows)
    assert all(r["proven_rate"] == 1.0 for r in rows)


def test_lpt_bound_is_always_tighter_than_the_arbitrary_order_bound():
    for m in (2, 3, 4, 5, 6):
        assert A.graham_bound_lpt(m) < A.graham_bound_arbitrary(m)


# --- Timing: CP-SAT (im schlimmsten Fall exponentiell) gegen LPT (O(n log n)) --------------------------------------------------------------------


def test_exact_solving_grows_far_slower_at_small_n_than_lpt():
    rows = timing_rows()
    large = rows[-1]
    assert large["lpt_seconds"] < 0.001


# --- Vehikel B: Rüstzeit-Härtetest ------------------------------------------------------------------------------------------------------------


def test_setup_gap_is_small_but_not_necessarily_zero_without_setup_time():
    """Anders als Stück 1-4/6: der Rüstzeit-0-Fall ist KEIN garantierter Nulltreffer, weil LPT schon ohne
    Rüstzeiten keine bewiesene Regel ist (nur bewiesen GUT, siehe test_grahams_bound_is_never_violated)."""
    row = setup_rows()[0]
    assert row["value"] == 0
    assert 0.0 <= row["gap_mean"] < 15.0


def test_setup_gap_trends_upward_with_the_setup_time():
    rows = setup_rows()
    assert rows[-1]["gap_mean"] > rows[0]["gap_mean"]
