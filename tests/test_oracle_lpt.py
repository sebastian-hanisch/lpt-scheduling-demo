"""Orakel-Test: List Scheduling/LPT gegen eine unabhängige Heap-Implementierung, das exakte Optimum gegen eine
Teilmengen-DP (kürzeste Einzelmaschinen-Folge je Teilmenge, dann Aufteilung auf m Maschinen) und Grahams
Schranken gegen dieses Optimum."""

import heapq
import random

import numpy as np

import lpt_algorithm as A


def _ls_heap(p, order, m, fam=None, setup=None):
    heap = [(0, k) for k in range(m)]
    heapq.heapify(heap)
    last = [None] * m
    for j in order:
        load, k = heapq.heappop(heap)
        s = int(setup[last[k]][fam[j]]) if fam is not None and last[k] is not None else 0
        load += s + int(p[j])
        last[k] = fam[j] if fam is not None else None
        heapq.heappush(heap, (load, k))
    return max(load for load, _ in heap)


def _opt_dp(p, m, fam=None, setup=None):
    n = len(p)
    inf = 10 ** 9
    dp = [[inf] * n for _ in range(1 << n)]
    for j in range(n):
        dp[1 << j][j] = int(p[j])
    for mask in range(1, 1 << n):
        for last in range(n):
            v = dp[mask][last]
            if v >= inf:
                continue
            for j in range(n):
                if mask >> j & 1:
                    continue
                s = int(setup[fam[last]][fam[j]]) if fam is not None else 0
                nm = mask | 1 << j
                dp[nm][j] = min(dp[nm][j], v + s + int(p[j]))
    cost = [0] + [min(dp[mask]) for mask in range(1, 1 << n)]
    best = cost[:]
    full = (1 << n) - 1
    for _ in range(m - 1):
        nb = best[:]
        for mask in range(1, full + 1):
            sub = mask
            while sub:
                nb[mask] = min(nb[mask], max(cost[sub], best[mask ^ sub]))
                sub = (sub - 1) & mask
        best = nb
    return best[full]


def test_list_scheduling_and_lpt_match_heap_reference_and_graham_bounds():
    rng = random.Random(3)
    for _ in range(150):
        n = rng.randint(1, 8)
        m = rng.randint(1, 4)
        hi = rng.choice([2, 4, 100])
        p = np.array([rng.randint(1, hi) for _ in range(n)])
        ref_order = sorted(range(n), key=lambda j: (-p[j], j))
        assert A.lpt_order(p).tolist() == ref_order
        lpt = A.list_schedule(p, A.lpt_order(p), m)
        assert lpt.cmax == _ls_heap(p, ref_order, m)
        assert lpt.loads.sum() == p.sum()
        opt = _opt_dp(p, m)
        assert lpt.cmax <= A.graham_bound_lpt(m) * opt + 1e-9
        assert A.list_schedule(p, A.arbitrary_order(n), m).cmax <= A.graham_bound_arbitrary(m) * opt + 1e-9


def test_cp_sat_optimum_equals_subset_dp_with_and_without_setup():
    rng = random.Random(5)
    for it in range(14):
        n = rng.randint(2, 6)
        m = rng.randint(2, 3)
        p = np.array([rng.randint(1, 30) for _ in range(n)])
        if it % 2:
            fam = np.array([rng.randint(0, 2) for _ in range(n)])
            s = rng.choice([5, 40])
            setup = np.array([[0 if a == b else s for b in range(3)] for a in range(3)])
            res, proven = A.solve_exact(p, m, fam, setup, 10)
            opt = _opt_dp(p, m, fam, setup)
            assert A.list_schedule(p, A.lpt_order(p), m, fam, setup).cmax == _ls_heap(p, A.lpt_order(p), m, fam, setup)
        else:
            res, proven = A.solve_exact(p, m, time_limit_seconds=10)
            opt = _opt_dp(p, m)
        assert proven and res.cmax == opt
