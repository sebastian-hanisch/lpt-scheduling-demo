"""lpt_algorithm: List-Scheduling-Verhalten, Grahams Schranken, CP-SAT gegen unabhängige Brute-Force-
Vollaufzählung (Zuordnung UND Reihenfolge je Maschine, nur für kleine n), Rüstzeit-Variante, Handrechnung."""

import itertools

import numpy as np
import pytest

import lpt_algorithm as A


def _p(seed, n):
    rng = np.random.default_rng(seed)
    return rng.integers(1, 30, size=n).astype(np.int64)


def _brute_force(p, m, family=None, setup=None):
    n = len(p)
    best = None
    for assign in itertools.product(range(m), repeat=n):
        groups = [[] for _ in range(m)]
        for j, k in enumerate(assign):
            groups[k].append(j)
        cmax = 0
        for g in groups:
            if not g:
                continue
            best_g = None
            for perm in itertools.permutations(g):
                t, prev = 0, None
                for j in perm:
                    if family is not None and prev is not None:
                        t += int(setup[prev, family[j]])
                    t += int(p[j])
                    prev = family[j] if family is not None else None
                if best_g is None or t < best_g:
                    best_g = t
            cmax = max(cmax, best_g)
        if best is None or cmax < best:
            best = cmax
    return best


@pytest.mark.parametrize("n,m", [(4, 2), (5, 2), (5, 3), (6, 3)])
def test_cp_sat_matches_brute_force_for_every_seed(n, m):
    """CP-SAT löst Zuordnung UND Reihenfolge je Maschine gemeinsam (Mehrfach-Kreis-Modell) - hier gegen eine
    UNABHÄNGIGE Brute-Force-Vollaufzählung (alle Zuordnungen × alle Permutationen je Maschinengruppe) geprüft."""
    for seed in range(5):
        p = _p(seed, n)
        bf = _brute_force(p, m)
        result, proven = A.solve_exact(p, m, time_limit_seconds=10)
        assert proven
        assert result.cmax == pytest.approx(bf, abs=1e-6)
        assert result.machine.min() >= 0 and result.machine.max() < m


def test_list_schedule_assigns_to_the_least_loaded_machine():
    p = np.array([5, 5, 1])
    order = np.array([0, 1, 2])          # zwei gleich große Aufträge zuerst, dann ein kleiner
    result = A.list_schedule(p, order, 2)
    assert result.machine[0] != result.machine[1]           # je eine eigene Maschine
    assert result.cmax == pytest.approx(6.0)                 # eine Maschine 5, die andere 5+1=6


def test_lpt_order_is_descending_by_processing_time():
    p = np.array([5, 2, 8, 1, 2])
    order = A.lpt_order(p)
    assert p[order].tolist() == sorted(p.tolist(), reverse=True)


def test_arbitrary_order_is_the_identity():
    assert A.arbitrary_order(5).tolist() == [0, 1, 2, 3, 4]


def test_random_order_is_deterministic_given_the_rng_state():
    n = 8
    a = A.random_order(n, np.random.default_rng(0))
    b = A.random_order(n, np.random.default_rng(0))
    assert a.tolist() == b.tolist()
    assert sorted(a.tolist()) == list(range(n))


def test_graham_bounds_formulas():
    assert A.graham_bound_lpt(2) == pytest.approx(4 / 3 - 1 / 6)
    assert A.graham_bound_arbitrary(2) == pytest.approx(1.5)
    assert A.graham_bound_lpt(3) < A.graham_bound_arbitrary(3)   # LPT-Schranke ist immer die engere


def test_lpt_beats_arbitrary_order_on_a_hand_picked_instance():
    """Handrechnung: p = [1, 1, 2], m = 2. Beliebige Reihenfolge (0,1,2): Auftrag 0 (1) -> M0, Auftrag 1 (1) ->
    M1 (Gleichstand mit M0, erste gewinnt... hier M1 da beide 0 sind und argmin die erste Null nimmt - dann
    M0), Auftrag 2 (2) -> die dann am wenigsten ausgelastete Maschine, beide bei 1 -> M0: Cmax = 1+2 = 3. LPT
    sortiert erst den großen Auftrag (2) ein: M0 bekommt ihn, beide kleinen (1,1) verteilen sich auf die freie
    Maschine M1 und die dann noch leichtere - Cmax = 2."""
    p = np.array([1, 1, 2])
    result_lpt = A.lpt(p, 2)
    result_arb = A.list_schedule(p, A.arbitrary_order(len(p)), 2)
    assert result_lpt.cmax == pytest.approx(2.0)
    assert result_arb.cmax == pytest.approx(3.0)
    assert result_lpt.cmax < result_arb.cmax


# --- Mit Rüstzeiten (Vehikel B) --------------------------------------------------------------------------------


def test_lpt_order_at_zero_setup_time_matches_the_neutral_vehicle_exactly():
    """Die richtige Konsistenzprüfung für dieses Stück: LPT ist keine bewiesene Regel (nur bewiesen GUT), der
    Kollaps-Test prüft deshalb NICHT 'trifft LPT das Optimum', sondern nur, dass Vehikel B bei Rüstzeit 0
    strukturell exakt auf Vehikel A zurückfällt (dieselbe Zuordnung, dieselbe Reihenfolge je Maschine)."""
    p = _p(7, 10)
    m = 3
    family = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    setup = np.zeros((2, 2))
    neutral = A.list_schedule(p, A.lpt_order(p), m)
    logistik = A.list_schedule(p, A.lpt_order(p), m, family, setup)
    assert np.array_equal(neutral.machine, logistik.machine)
    assert neutral.cmax == pytest.approx(logistik.cmax)


def test_setup_time_is_only_charged_on_a_family_change_on_the_same_machine():
    p = np.array([2, 2, 2])
    family = np.array([0, 0, 1])
    setup = np.array([[0, 10], [10, 0]])
    order = np.array([0, 1, 2])
    result = A.list_schedule(p, order, 1, family, setup)      # eine Maschine: alle drei nacheinander
    assert result.completion.tolist() == [2, 4, 4 + 10 + 2]


def test_cp_sat_with_setup_matches_independent_brute_force():
    p = _p(11, 6)
    rng = np.random.default_rng(11)
    family = rng.integers(0, 3, size=6)
    setup = np.array([[0, 5, 8], [5, 0, 3], [8, 3, 0]])
    bf = _brute_force(p, 2, family, setup)
    result, proven = A.solve_exact(p, 2, family, setup, time_limit_seconds=10)
    assert proven
    assert result.cmax == pytest.approx(bf, abs=1e-6)


def test_cp_sat_setup_matches_no_setup_when_setup_is_zero():
    p = _p(13, 6)
    family = np.array([0, 1, 0, 1, 0, 1])
    setup0 = np.zeros((2, 2))
    plain, proven1 = A.solve_exact(p, 3, time_limit_seconds=10)
    with_setup, proven2 = A.solve_exact(p, 3, family, setup0, time_limit_seconds=10)
    assert proven1 and proven2
    assert with_setup.cmax == pytest.approx(plain.cmax, abs=1e-6)


def test_ignoring_setup_can_be_worse_than_the_true_optimum():
    p = np.array([1, 1, 10, 10])
    family = np.array([0, 1, 0, 1])
    setup = np.array([[0, 100], [100, 0]])
    lpt_cmax = A.list_schedule(p, A.lpt_order(p), 1, family, setup).cmax
    true_opt, _ = A.solve_exact(p, 1, family, setup, time_limit_seconds=10)
    assert lpt_cmax > true_opt.cmax + 1e-6
