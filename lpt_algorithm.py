"""LPT (Longest Processing Time first) für Pm||Cmax: n Aufträge, EINE Operation je Auftrag, m IDENTISCHE
parallele Maschinen, Ziel ist die maximale Maschinenlast (Cmax) zu minimieren. Anders als Stück 1-4/6 gibt es
HIER keine beweisbar optimale Regel - aber anders als Stück 5 (ATC, keinerlei Garantie) hat List Scheduling
eine BEWIESENE Worst-Case-Garantie (Graham 1966/1969):

- Beliebige Reihenfolge, greedy der am wenigsten ausgelasteten Maschine zugewiesen ("List Scheduling"):
  Cmax ≤ (2 - 1/m) · Cmax(opt)                                                          [Graham 1966]
- DIESELBE Zuweisung, aber Aufträge vorher absteigend nach Bearbeitungszeit sortiert ("LPT"):
  Cmax ≤ (4/3 - 1/(3m)) · Cmax(opt)                                                      [Graham 1969]

Die Sortierung allein verbessert die bewiesene Garantie - das ist der Kern dieses Stücks.

Hier zusätzlich: CP-SAT (OR-Tools) als exakter Löser für die Gegenprobe - ein Mehrfach-Kreis-Modell
("multiple circuit", die VRP-Variante von `johnson-rule-demo`s Kreis-Modell: ein Depot-Knoten, bis zu m
Rundreisen, eine je Maschine), das Rüstzeiten beim Familienwechsel INNERHALB einer Maschine gleich mit
abbildet: bei Rüstzeit 0 (neutrales Vehikel) kollabiert es exakt zum rüstzeitfreien Fall."""

import os
from dataclasses import dataclass

import numpy as np
from ortools.sat.python import cp_model

NUM_SEARCH_WORKERS = min(8, os.cpu_count() or 1)  # NIE hart auf eine Zahl setzen - siehe project memory
# (weighted-tardiness-demo brach auf einem 4-Kern-CI-Runner durch Oversubscription bei hart kodierten 8 Workern)


@dataclass
class Result:
    order: np.ndarray          # die verwendete Bearbeitungsreihenfolge (List-Scheduling-Eingabe)
    machine: np.ndarray        # Maschine je Auftrag (0..m-1)
    completion: np.ndarray     # Fertigstellungszeit je Auftrag AUF SEINER Maschine
    loads: np.ndarray          # Endlast je Maschine (Länge m)
    cmax: float                # Zielgröße: max(loads)


def list_schedule(p, order, m, family=None, setup=None):
    """List Scheduling (Graham): Aufträge in der gegebenen Reihenfolge nacheinander der Maschine mit der
    aktuell KLEINSTEN Last zuweisen. `order` bestimmt die Regel: absteigend nach p = LPT, unverändert = die
    falsche Regel hier ("beliebige Reihenfolge"), zufällig gemischt = Zufalls-Baseline. Mit Familien/Rüstzeit
    (Vehikel B) kostet ein Familienwechsel AUF DERSELBEN MASCHINE zusätzliche Zeit, bevor der nächste Auftrag
    auf dieser Maschine beginnt - das macht zum ersten Mal in dieser Linie auch die Reihenfolge INNERHALB einer
    Maschine relevant, nicht nur die Zuordnung."""
    order = np.asarray(order)
    n = len(order)
    loads = np.zeros(m, dtype=np.float64)
    last_family = [None] * m
    machine = np.empty(n, dtype=np.int64)
    completion = np.empty(n, dtype=np.float64)
    for j in order:
        k = int(np.argmin(loads))
        s = float(setup[last_family[k], family[j]]) if family is not None and last_family[k] is not None else 0.0
        loads[k] += s + float(p[j])
        completion[j] = loads[k]
        machine[j] = k
        if family is not None:
            last_family[k] = family[j]
    return Result(order, machine, completion, loads, float(loads.max()))


def lpt_order(p):
    """LPT: absteigend nach Bearbeitungszeit - stabile Sortierung für reproduzierbare Gleichstände."""
    return np.argsort(-np.asarray(p), kind="stable")


def lpt(p, m, family=None, setup=None):
    return list_schedule(p, lpt_order(p), m, family, setup)


def arbitrary_order(n):
    """Die falsche Regel hier: KEINE Sortierung - Aufträge in der Reihenfolge zugewiesen, in der sie erzeugt
    wurden. Immer noch List Scheduling (greedy der am wenigsten ausgelasteten Maschine), aber ohne die
    LPT-Sortierung gilt nur Grahams schwächere Schranke von 1966 (2 - 1/m) statt 4/3 - 1/(3m)."""
    return np.arange(n)


def random_order(n, rng):
    order = np.arange(n)
    rng.shuffle(order)
    return order


def graham_bound_lpt(m):
    return 4.0 / 3.0 - 1.0 / (3.0 * m)


def graham_bound_arbitrary(m):
    return 2.0 - 1.0 / m


# --- CP-SAT (exakte Gegenprobe, ein Modell für beide Vehikel) ---------------------------------------------------


def solve_exact(p, m, family=None, setup=None, time_limit_seconds=15.0):
    """Gemeinsame Optimierung von Zuordnung UND Reihenfolge je Maschine als Mehrfach-Kreis-Modell ("multiple
    circuit", die VRP-Variante): Knoten 0 ist ein gemeinsames Depot, bis zu m Rundreisen (eine je Maschine)
    starten und enden dort. `AddMultipleCircuit` erzwingt: jeder Auftrags-Knoten hat genau einen Vorgänger und
    Nachfolger, das Depot hat gleich viele ein- wie ausgehende Bögen (= Anzahl benutzter Maschinen); eine
    Nebenbedingung begrenzt das auf höchstens m. Zeitvariable je Auftrag wird nur auf dem benutzten Bogen scharf
    gemacht (reified `>=`, wie in `johnson-rule-demo`) - keine zweite Konstruktion für den rüstzeitfreien Fall
    nötig, `setup` ist dort einfach eine Nullmatrix.

    Rückgabe: (Result oder None, proven: bool)."""
    n = len(p)
    if family is None:
        family = np.zeros(n, dtype=np.int64)
        setup = np.zeros((1, 1), dtype=np.int64)
    horizon = int(np.sum(p)) + int(np.max(setup)) * n + 1

    model = cp_model.CpModel()
    time_vars = [model.NewIntVar(0, horizon, f"time_{j}") for j in range(n)]
    arcs = []
    depot_out = []
    for j in range(n):
        lit = model.NewBoolVar(f"a0_{j}")
        arcs.append((0, j + 1, lit))
        depot_out.append(lit)
        model.Add(time_vars[j] >= int(p[j])).OnlyEnforceIf(lit)
        lit_back = model.NewBoolVar(f"a{j}_0")
        arcs.append((j + 1, 0, lit_back))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            lit = model.NewBoolVar(f"a{i}_{j}")
            arcs.append((i + 1, j + 1, lit))
            s = int(setup[family[i], family[j]])
            model.Add(time_vars[j] >= time_vars[i] + int(p[j]) + s).OnlyEnforceIf(lit)
    model.AddMultipleCircuit(arcs)
    model.Add(sum(depot_out) <= m)

    cmax = model.NewIntVar(0, horizon, "cmax")
    model.AddMaxEquality(cmax, time_vars)
    model.Minimize(cmax)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = NUM_SEARCH_WORKERS
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False

    times = np.array([solver.Value(v) for v in time_vars], dtype=np.float64)
    machine = _reconstruct_machines(n, m, arcs, solver)
    loads = np.zeros(m, dtype=np.float64)
    for j in range(n):
        loads[machine[j]] = max(loads[machine[j]], times[j])
    result = Result(np.argsort(times), machine, times, loads, float(solver.Value(cmax)))
    return result, status == cp_model.OPTIMAL


def _reconstruct_machines(n, m, arcs, solver):
    """Liest die gewählten Depot-Ausgänge und folgt jedem Pfad, um jedem Auftrag seine Maschine zuzuordnen."""
    out_arcs = {}
    for (i, j, lit) in arcs:
        if solver.Value(lit):
            out_arcs[i] = j
    machine = np.full(n, -1, dtype=np.int64)
    k = 0
    node = out_arcs.get(0)
    visited_depot_exits = 0
    # Depot kann mehrere ausgehende Bögen haben - jede eigene Rundreise verfolgen
    starts = [j for (i, j, lit) in arcs if i == 0 and solver.Value(lit)]
    for start in starts:
        node = start
        while node != 0:
            machine[node - 1] = k
            node = out_arcs[node]
        k += 1
    return machine
