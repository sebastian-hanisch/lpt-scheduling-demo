"""Vehikel B "Werkstatt/Logistik": dieselben Aufträge wie Vehikel A (Bearbeitungszeit), zusätzlich eine Familie
je Auftrag und eine feste Rüstzeit beim Familienwechsel - INNERHALB einer Maschine (dieselbe Idee wie in
`spt-scheduling-demo` usw., hier zum ersten Mal auf mehrere parallele Maschinen verteilt: jede Maschine hat ihre
eigene Sequenz und damit ihre eigene Rüstzeit-Historie)."""

from dataclasses import dataclass

import numpy as np

import lpt_constants as C


@dataclass(frozen=True)
class LogistikInstance:
    n: int
    p: np.ndarray
    family: np.ndarray
    setup: np.ndarray
    seed: int


def generate(n, seed, n_families=C.DEFAULT_N_FAMILIES, setup_time=C.DEFAULT_SETUP_TIME, p_min=C.P_MIN, p_max=C.P_MAX):
    rng = np.random.default_rng(seed)
    p = rng.integers(p_min, p_max + 1, size=n).astype(np.int64)
    family = rng.integers(0, n_families, size=n).astype(np.int64)
    setup = np.full((n_families, n_families), setup_time, dtype=np.int64)
    np.fill_diagonal(setup, 0)
    return LogistikInstance(n, p, family, setup, seed)
