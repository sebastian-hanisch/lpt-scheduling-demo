"""Konstanten der LPT-Demo: beide Vehikel (Neutral, Werkstatt/Logistik), Regler, Messreihen-Seeds."""

N_MIN, N_MAX, DEFAULT_N, N_STEP = 2, 60, 20, 1
SEED_MAX = 999999
DEFAULT_SEED = 55
SWEEP_SEEDS = tuple(range(100000, 100005))
SWEEP_CHAINS = 3

# Maschinen (zum ersten Mal in dieser Linie ein eigener Regler - parallele statt serielle Maschinen)
M_MIN, M_MAX, DEFAULT_M = 2, 6, 3

# Bearbeitungszeiten
P_MIN, P_MAX = 1, 100

# CP-SAT exakte Gegenprobe: praktisches Limit für eine live nutzbare Demo (gemessen, siehe README) - stark
# NP-schwer sobald Rüstzeiten UND wenige Maschinen zusammenkommen (mehr Aufträge je Maschine = schwerere
# Sequenzierung), deshalb wie Stück 5 durch die Härte selbst begrenzt, nicht durch n!.
EXACT_MAX_N = 9
EXACT_SWEEP_N = (2, 3, 4, 5, 6, 7, 8, 9)
EXACT_TIME_LIMIT_SECONDS = 15.0

# --- Vehikel B "Werkstatt/Logistik" ---------------------------------------------------------------------------
N_FAMILIES_MIN, N_FAMILIES_MAX, DEFAULT_N_FAMILIES = 2, 6, 3
SETUP_TIME_MIN, SETUP_TIME_MAX, DEFAULT_SETUP_TIME = 0, 60, 15

VEHICLE_LABELS = {"neutral": "Neutral", "logistik": "Werkstatt/Logistik"}
DEFAULT_VEHICLE = "neutral"


def _preset(n=DEFAULT_N, m=DEFAULT_M, vehicle=DEFAULT_VEHICLE, setup_time=DEFAULT_SETUP_TIME, n_families=DEFAULT_N_FAMILIES):
    return {"n": n, "m": m, "seed": DEFAULT_SEED, "chain_seed": 0, "vehicle": vehicle, "setup_time": setup_time, "n_families": n_families}


PRESETS = {
    "Standardfall (Voreinstellung)": _preset(),
    "Kleine Instanz (CP-SAT sichtbar)": _preset(n=EXACT_MAX_N),
    "Große Instanz (Skalierung)": _preset(n=N_MAX),
    "Werkstatt/Logistik-Vehikel": _preset(vehicle="logistik"),
    "Hohe Rüstlast (Werkstatt)": _preset(vehicle="logistik", setup_time=SETUP_TIME_MAX),
}
# Werte in PRESET_HELP nach der Messreihe (lpt_evaluation.run_config) final eingetragen.
PRESET_HELP = {
    "Standardfall (Voreinstellung)": f"{DEFAULT_N} Aufträge auf {DEFAULT_M} Maschinen: LPT misst sich gegen dieselbe Zuweisung OHNE Sortierung und gegen Zufall.",
    "Kleine Instanz (CP-SAT sichtbar)": f"{EXACT_MAX_N} Aufträge: hier löst CP-SAT (OR-Tools) Zuordnung UND Reihenfolge je Maschine exakt mit.",
    "Große Instanz (Skalierung)": f"{N_MAX} Aufträge: LPT bleibt schnell (O(n log n)), eine exakte Lösung wäre bei dieser Größe aussichtslos.",
    "Werkstatt/Logistik-Vehikel": "Dieselben Aufträge, aber in Familien mit Rüstzeit beim Wechsel INNERHALB einer Maschine - LPT kennt diese Rüstzeiten nicht.",
    "Hohe Rüstlast (Werkstatt)": f"Rüstzeit {SETUP_TIME_MAX} Minuten je Familienwechsel: der Abstand zwischen LPT und dem echten Optimum wächst.",
}
