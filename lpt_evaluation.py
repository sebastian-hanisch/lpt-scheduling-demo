"""Auswertung der LPT-Demo: LPT gegen dieselbe Zuweisung ohne Sortierung ("beliebige Reihenfolge", die falsche
Regel hier) und gegen zufällige Reihenfolgen, gegen CP-SAT als exakte Gegenprobe (nur kleine n), gegen Grahams
bewiesene Worst-Case-Schranken, und das Vehikel-B-Experiment (bleibt LPT nahe am Optimum, sobald Rüstzeiten
dazukommen)."""

import time
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import lpt_algorithm as A
import lpt_constants as C
import lpt_scenario as S
import lpt_scenario_logistik as SL


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    seed: int = C.DEFAULT_SEED
    chain_seed: int = 0
    vehicle: str = C.DEFAULT_VEHICLE
    setup_time: int = C.DEFAULT_SETUP_TIME
    n_families: int = C.DEFAULT_N_FAMILIES


@lru_cache(maxsize=512)
def instance(n, seed):
    return S.generate(n, seed)


@lru_cache(maxsize=512)
def logistik_instance(n, seed, n_families, setup_time):
    return SL.generate(n, seed, n_families=n_families, setup_time=setup_time)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    lpt: object
    arbitrary: object          # die falsche Regel hier: keine Sortierung
    random_mean: float
    random_runs: int
    optimal: object            # None, wenn n > EXACT_MAX_N
    optimal_proven: bool

    @property
    def gap_arbitrary(self):
        return _gap(self.arbitrary.cmax, self.lpt.cmax)

    @property
    def gap_random(self):
        return _gap(self.random_mean, self.lpt.cmax)

    @property
    def lpt_matches_optimum(self):
        return self.optimal is not None and abs(self.lpt.cmax - self.optimal.cmax) < 1e-6

    @property
    def lpt_ratio_to_optimum(self):
        return None if self.optimal is None or self.optimal.cmax <= 1e-9 else self.lpt.cmax / self.optimal.cmax


def _gap(value, baseline):
    if baseline <= 1e-9:
        return 0.0 if value <= 1e-9 else float(value)
    return 100.0 * (value - baseline) / baseline


def analyse(settings, random_draws=20):
    """Wertet LPT auf dem gewählten Vehikel aus - Neutral oder Werkstatt/Logistik (Rüstzeit beim
    Familienwechsel INNERHALB einer Maschine zählt mit). Von Anfang an vehikel-bewusst gebaut (Lehre aus
    Stück 1-6 dieser Linie)."""
    if settings.vehicle == "logistik":
        inst = logistik_instance(settings.n, settings.seed, settings.n_families, settings.setup_time)
        p, family, setup = inst.p, inst.family, inst.setup

        def ev(order):
            return A.list_schedule(p, order, settings.m, family, setup)

        optimal, proven = (A.solve_exact(p, settings.m, family, setup, C.EXACT_TIME_LIMIT_SECONDS)
                            if settings.n <= C.EXACT_MAX_N else (None, False))
    else:
        inst = instance(settings.n, settings.seed)
        p = inst.p

        def ev(order):
            return A.list_schedule(p, order, settings.m)

        optimal, proven = (A.solve_exact(p, settings.m, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
                            if settings.n <= C.EXACT_MAX_N else (None, False))

    lpt = ev(A.lpt_order(p))
    arbitrary = ev(A.arbitrary_order(settings.n))
    rng = np.random.default_rng(settings.chain_seed)
    random_totals = [ev(A.random_order(settings.n, rng)).cmax for _ in range(random_draws)]
    return Analysis(settings, inst, lpt, arbitrary, float(np.mean(random_totals)), random_draws, optimal, proven)


# --- Sweeps und Tabellen -----------------------------------------------------------------------------------------------------------------------


def _mean(rows, key):
    return float(np.mean([r[key] for r in rows]))


def run_config(base, seeds=C.SWEEP_SEEDS, chains=C.SWEEP_CHAINS, **changes):
    s0 = replace(base, **changes)
    rows = []
    for seed in seeds:
        for ch in range(chains):
            a = analyse(replace(s0, seed=seed, chain_seed=ch))
            rows.append({"gap_arbitrary": a.gap_arbitrary, "gap_random": a.gap_random})
    out = {k: _mean(rows, k) for k in rows[0]}
    out["n_runs"] = len(rows)
    return out


SWEEP_VALUES = {"n": (2, 5, 10, 20, 40, 60), "m": (2, 3, 4, 5, 6)}
SWEEP_LABELS = {"n": "Aufträge", "m": "Maschinen"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def graham_bound_check(ns=C.EXACT_SWEEP_N, ms=(2, 3, 4), seeds=C.SWEEP_SEEDS):
    """Der zentrale Beweis-Check dieses Stücks: ANDERS als Stück 1-4/6 (exakte Gleichheit gegen die
    Vollaufzählung) prüfen wir hier eine UNGLEICHUNG - trifft LPT jemals Grahams bewiesene Schranke
    (4/3 - 1/(3m)) NICHT, wäre das ein Fehler im Beweis oder in der Implementierung. Zusätzlich der Anteil
    bewiesener CP-SAT-Läufe und wie nah der schlechteste beobachtete Fall an die Schranke herankommt."""
    rows = []
    for n in ns:
        for m in ms:
            bound = A.graham_bound_lpt(m)
            worst_ratio, proven_count = 0.0, 0
            for seed in seeds:
                inst = instance(n, seed)
                opt, proven = A.solve_exact(inst.p, m, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
                if proven and opt.cmax > 1e-9:
                    proven_count += 1
                    ratio = A.lpt(inst.p, m).cmax / opt.cmax
                    worst_ratio = max(worst_ratio, ratio)
            rows.append({"n": n, "m": m, "bound": bound, "worst_ratio": worst_ratio,
                         "worst_over_bound": worst_ratio / bound if bound > 0 else 0.0, "proven_rate": proven_count / len(seeds)})
    return rows


def timing_sweep(ns=C.EXACT_SWEEP_N, m=C.DEFAULT_M, seed=C.DEFAULT_SEED):
    """Gemessene Rechenzeit: CP-SAT (Zeitlimit, im schlimmsten Fall exponentiell) gegen LPT (O(n log n))."""
    rows = []
    for n in ns:
        inst = instance(n, seed)
        t0 = time.perf_counter()
        A.solve_exact(inst.p, m, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
        t_exact = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(100):
            A.lpt(inst.p, m)
        t_lpt = (time.perf_counter() - t0) / 100
        rows.append({"value": n, "exact_seconds": t_exact, "lpt_seconds": t_lpt})
    return rows


def setup_gap(n=8, m=C.DEFAULT_M, seeds=C.SWEEP_SEEDS, n_families=C.DEFAULT_N_FAMILIES, setup_time=C.DEFAULT_SETUP_TIME):
    """Vehikel-B-Härtetest: LPT (kennt keine Rüstzeiten) gegen die echte Optimallösung MIT Rüstzeiten
    (CP-SAT, deshalb kleines n). Der Abstand ist eine echte Messfrage, kein behaupteter Befund."""
    gaps = []
    for seed in seeds:
        linst = SL.generate(n, seed, n_families=n_families, setup_time=setup_time)
        lpt_result = A.list_schedule(linst.p, A.lpt_order(linst.p), m, linst.family, linst.setup)
        opt, proven = A.solve_exact(linst.p, m, linst.family, linst.setup, C.EXACT_TIME_LIMIT_SECONDS)
        if proven:
            gaps.append(_gap(lpt_result.cmax, opt.cmax))
    return {"gap_mean": float(np.mean(gaps)), "gap_min": float(np.min(gaps)), "gap_max": float(np.max(gaps)), "n_runs": len(gaps)}


def setup_gap_sweep(setup_times=(0, 5, 15, 30, 60), n=8, m=C.DEFAULT_M, seeds=C.SWEEP_SEEDS, n_families=C.DEFAULT_N_FAMILIES):
    return [{"value": s, **setup_gap(n=n, m=m, seeds=seeds, n_families=n_families, setup_time=s)} for s in setup_times]
