"""Vehikel A "Neutral" der LPT-Demo: n Aufträge mit EINER Bearbeitungszeit pⱼ (keine zweite Operation wie in
`johnson-rule-demo`, keine Fristen/Gewichte wie in Stück 1-5) - die Maschinenzahl `m` selbst ist der neue
Parameter dieses Stücks, nicht Teil der Instanz."""

from dataclasses import dataclass

import numpy as np

import lpt_constants as C


@dataclass(frozen=True)
class Instance:
    n: int
    p: np.ndarray
    seed: int


def generate(n, seed, p_min=C.P_MIN, p_max=C.P_MAX):
    rng = np.random.default_rng(seed)
    p = rng.integers(p_min, p_max + 1, size=n).astype(np.int64)
    return Instance(n, p, seed)
