"""LPT (Longest Processing Time first) - eine bewiesene Garantie statt eines Beweises - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der neuen Konzepte-Linie "Klassische Scheduling-Theorie": n Aufträge, EINE Operation je Auftrag,
m identische parallele Maschinen, Ziel ist die maximale Maschinenlast (Cmax) zu minimieren (Pm||Cmax in der
α|β|γ-Notation). LPT (absteigend nach Bearbeitungszeit sortieren, dann greedy der am wenigsten ausgelasteten
Maschine zuweisen) ist NICHT beweisbar optimal - aber Graham (1969) hat eine bewiesene Worst-Case-Garantie
gezeigt: Cmax(LPT) ≤ (4/3 - 1/(3m)) · Cmax(opt). Siehe README für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import lpt_algorithm as A
import lpt_constants as C
from lpt_evaluation import Settings, SWEEP_LABELS, analyse, graham_bound_check, instance, run_config, setup_gap, setup_gap_sweep, sweep, timing_sweep
from lpt_presets import KEPT, apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_chain_seed, randomize_seed, seed_widget, sync_query_params
from lpt_visualization import build_graham_chart, build_jobs_chart, build_load_comparison, build_machine_gantt, build_setup_gap, build_sweep, build_timing

st.set_page_config(page_title="LPT – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _graham_check():
    return graham_bound_check()


@st.cache_data(show_spinner=False)
def _timing(m):
    return timing_sweep(m=m)


@st.cache_data(show_spinner=False)
def _setup_gap_sweep(n, m, n_families):
    return setup_gap_sweep(n=n, m=m, n_families=n_families)


def _fmt_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


def _fmt_pct(x):
    """Vorzeichen-korrekt: `+5.9 %` (Vergleichsregel schlechter als LPT) oder `-x %` (LPT ist keine bewiesen
    optimale Regel - eine Vergleichsregel kann hier auch mal zufällig besser abschneiden)."""
    return f"{x:+.1f} %"


st.title("⚖️ LPT – eine bewiesene Garantie statt eines Beweises")
st.markdown(
    r"""
**n Aufträge, jeder mit EINER Bearbeitungszeit, m IDENTISCHE parallele Maschinen, gesucht ist die Zuordnung, die
die maximale Maschinenlast minimiert** ($Pm||C_{\max}$). **LPT** (Longest Processing Time first): Aufträge
absteigend nach Bearbeitungszeit sortieren, dann jeden Auftrag greedy der aktuell am wenigsten ausgelasteten
Maschine zuweisen. Anders als SPT/EDD/Moore-Hodgson/WSPT/Johnson (Stücke 1-4/6) ist das **nicht beweisbar
optimal** - aber Graham (1969) hat eine **bewiesene Worst-Case-Garantie**: egal welche Instanz, LPT liegt nie
mehr als $\frac{4}{3} - \frac{1}{3m}$ mal über dem echten Optimum. Eine dritte Art von Ergebnis in dieser Linie:
nach "exakter Beweis" (Stück 1-4/6) und "nur Heuristik, keine Garantie" (Stück 5) jetzt "keine Optimalität, aber
eine bewiesene Grenze, wie schlecht es werden kann".
"""
)
st.caption(
    "Siebtes Stück der Konzepte-Linie „Klassische Scheduling-Theorie“ - die zweite neue Dimension: PARALLELE "
    "statt serielle Maschinen. Zwei Vehikel: **Neutral** (Aufträge mit einer Bearbeitungszeit) und "
    "**Werkstatt/Logistik** (dieselben Aufträge, aber in Familien mit Rüstzeit beim Wechsel INNERHALB einer "
    "Maschine) - der Umschalter ist in der Seitenleiste."
)

with st.expander("So funktioniert LPT", expanded=True):
    st.markdown(
        r"""
1. **Sortieren.** Alle Aufträge absteigend nach Bearbeitungszeit ordnen.
2. **Zuweisen.** Jeden Auftrag der Reihe nach der Maschine geben, die gerade am wenigsten zu tun hat ("List Scheduling", Graham 1966).
3. **Warum die Sortierung hilft.** Ohne Sortierung (beliebige Reihenfolge) gilt nur Grahams schwächere Schranke $2 - \frac{1}{m}$; MIT der LPT-Sortierung verbessert sich das auf $\frac{4}{3} - \frac{1}{3m}$ (Graham 1969) - **derselbe Zuweisungs-Algorithmus**, nur die Reihenfolge der Eingabe ändert sich.
4. **Die Grenze der Annahme.** LPT kennt keine Rüstzeiten. Das Vehikel „Werkstatt/Logistik“ prüft, was passiert, wenn ein Familienwechsel auf derselben Maschine zusätzlich Zeit kostet.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(C.PRESETS.keys())
cols = st.columns(len(preset_names))
for col, name in zip(cols, preset_names):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name], key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_jobs = st.slider("Aufträge", *bounds("n_slider"), key="n_slider", step=C.N_STEP,
                        help=f"Anzahl der Aufträge. Bis {C.EXACT_MAX_N} löst CP-SAT Zuordnung und Reihenfolge exakt mit.")
    m_machines = st.slider("Maschinen", *bounds("m_slider"), key="m_slider",
                            help="Anzahl der identischen parallelen Maschinen - zum ersten Mal in dieser Linie ein eigener Regler.")
    vehicle = st.radio("Vehikel", list(C.VEHICLE_LABELS), key="vehicle_radio", format_func=lambda k: C.VEHICLE_LABELS[k],
                        help="Neutral: nur Bearbeitungszeiten. Werkstatt/Logistik: dieselben Aufträge, zusätzlich in Familien mit Rüstzeit beim Wechsel auf derselben Maschine.")
    if vehicle == "logistik":
        seed_widget("setup_time_slider")
        setup_time = st.slider("Rüstzeit je Familienwechsel (Minuten)", *bounds("setup_time_slider"), key="setup_time_slider",
                                help="0 Minuten kollabiert strukturell exakt zum neutralen Vehikel (siehe Test/Messreihe).")
        st.session_state[KEPT["setup_time_slider"]] = setup_time
        seed_widget("n_families_slider")
        n_families = st.slider("Auftragsfamilien", *bounds("n_families_slider"), key="n_families_slider",
                                help="Weniger Familien bei gleicher Auftragszahl bedeutet mehr Wechsel und damit mehr Rüstzeit insgesamt.")
        st.session_state[KEPT["n_families_slider"]] = n_families
    else:
        setup_time = int(st.session_state.get(KEPT["setup_time_slider"], C.DEFAULT_SETUP_TIME))
        n_families = int(st.session_state.get(KEPT["n_families_slider"], C.DEFAULT_N_FAMILIES))
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed für die Bearbeitungszeiten.")
    chain_seed = st.number_input("Zufalls-Seed der Kette", *bounds("chain_seed_input"), key="chain_seed_input", step=1,
                                  help="Steuert nur die zufällige Vergleichs-Reihenfolge - LPT selbst ist deterministisch (kein Zufall im Kern).")
    st.button("🎲 Neue Kette würfeln", width="stretch", on_click=randomize_chain_seed, help="Würfelt einen neuen Seed für die Zufalls-Vergleichsreihenfolge.")

sync_query_params({"n_slider": int(n_jobs), "m_slider": int(m_machines), "seed_input": int(seed), "chain_seed_input": int(chain_seed),
                    "vehicle_radio": vehicle, "setup_time_slider": int(setup_time), "n_families_slider": int(n_families)})

settings = Settings(int(n_jobs), int(m_machines), int(seed), int(chain_seed), vehicle=vehicle, setup_time=int(setup_time), n_families=int(n_families))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst = a.inst
p = inst.p
data_key = settings

# --- LPT in Aktion ---------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 LPT in Aktion")
STEP_LABELS = {1: "1 · Aufträge", 2: "2 · Einplanen", 3: "3 · Ergebnis"}
if "lpt_step" not in st.session_state or st.session_state.get("lpt_step_owner") != data_key:
    st.session_state["lpt_step"] = 1
    st.session_state["lpt_step_owner"] = data_key
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="lpt_step", format_func=lambda s: STEP_LABELS[s])

if step == 2:
    it_col, itplay_col = st.columns([5, 2])
    with it_col:
        upto = st.slider("Eingeplante Aufträge", 1, int(n_jobs), value=int(n_jobs), key="lpt_upto")
else:
    upto = int(n_jobs)

view_slot = st.empty()
with view_slot.container():
    if step == 1:
        st.markdown(f"**{n_jobs} Aufträge, unsortiert** (Bearbeitungszeit in Minuten)")
        st.plotly_chart(build_jobs_chart(p), width="stretch", key="s1_jobs")
    elif step == 2:
        st.markdown(f"**LPT-Zuordnung nach {upto} von {n_jobs} eingeplanten Aufträgen**")
        st.plotly_chart(build_machine_gantt(p, a.lpt.machine, a.lpt.completion, int(m_machines), upto=upto), width="stretch", key=f"s2_sched_{upto}")
        st.caption(f"Höchste Maschinenlast bisher: {_fmt_int(a.lpt.completion[np.argsort(a.lpt.completion)[:upto]].max() if upto else 0)}")
    else:
        st.markdown("**Endlast je Maschine: LPT gegen dieselbe Zuweisung ohne Sortierung**")
        st.plotly_chart(build_load_comparison(a.lpt.loads, a.arbitrary.loads), width="stretch", key="s3_loads")

if step == 1:
    st.caption(f"Bearbeitungszeiten zwischen {int(p.min())} und {int(p.max())} Minuten (Seed {seed}).")
elif step == 2:
    gap_note = " Lücken sind Rüstzeit bei einem Familienwechsel auf derselben Maschine." if vehicle == "logistik" else ""
    st.caption(f"Jede Zeile ist eine Maschine, jeder Balken ein Auftrag.{gap_note}")
else:
    st.caption(f"LPT: Cmax {_fmt_int(a.lpt.cmax)}. Beliebige Reihenfolge: {_fmt_int(a.arbitrary.cmax)} (Differenz {_fmt_pct(a.gap_arbitrary)}). Die gestrichelten Linien markieren jeweils die höchste Last (= Cmax).")

st.markdown("---")

# --- Ergebnis -------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was die Sortierung bringt")
vehicle_note = " Auf dem Werkstatt/Logistik-Vehikel zählt die Rüstzeit auf derselben Maschine mit - LPT kennt sie nicht, alle Zahlen hier berücksichtigen sie trotzdem." if vehicle == "logistik" else ""
st.caption(f"**Abstand:** Cmax einer Zuweisung gegenüber LPT in Prozent - kann negativ werden, LPT ist keine bewiesen optimale Regel, nur eine bewiesen GUTE.{vehicle_note}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("LPT (Cmax)", _fmt_int(a.lpt.cmax), help="Die Zielgröße: maximale Maschinenlast in LPT-Zuordnung, auf dem gewählten Vehikel.")
m2.metric("beliebige Reihenfolge", _fmt_pct(a.gap_arbitrary), delta_color="off", help="Dieselbe Greedy-Zuweisung, aber ohne die LPT-Sortierung - dafür gilt nur Grahams schwächere Schranke (2 - 1/m).")
m3.metric(f"Zufällige Reihenfolge (Mittel über {a.random_runs})", _fmt_pct(a.gap_random), delta_color="off", help="Mittel über mehrere zufällige Einplanungsreihenfolgen derselben Instanz.")
if a.optimal is not None and a.optimal_proven:
    m4.metric("CP-SAT (exakte Gegenprobe)", "trifft LPT exakt" if a.lpt_matches_optimum else f"{a.lpt_ratio_to_optimum:.3f}× Optimum", delta_color="off",
              help="OR-Tools CP-SAT hat Zuordnung UND Reihenfolge je Maschine für diese Instanz bewiesen exakt gelöst.")
elif a.optimal is not None:
    m4.metric("CP-SAT", "Zeitlimit erreicht", delta_color="off", help="CP-SAT hat innerhalb des Zeitlimits keine bewiesen optimale Lösung gefunden.")
else:
    m4.metric("CP-SAT", f"erst ab n ≤ {C.EXACT_MAX_N}", delta_color="off", help="Bei dieser Größe wäre eine exakte Lösung aussichtslos - siehe das Timing-Experiment unten.")

bound = A.graham_bound_lpt(int(m_machines))
if a.optimal is not None and a.optimal_proven and a.lpt_ratio_to_optimum is not None and a.lpt_ratio_to_optimum > bound + 1e-6:
    st.error(f"⚠️ LPT verletzt Grahams bewiesene Schranke ({a.lpt_ratio_to_optimum:.3f} > {bound:.3f}) - das wäre ein Fehler im Beweis oder in der Implementierung, bitte melden.")
elif a.gap_arbitrary < 0 or a.gap_random < 0:
    worse_than = "die beliebige Reihenfolge" if a.gap_arbitrary < 0 else "eine zufällige Reihenfolge"
    worst_gap = min(a.gap_arbitrary, a.gap_random)
    vehicle_hint = " (hier zusätzlich durch Rüstzeiten, die Graham nicht kennt)" if vehicle == "logistik" else ""
    st.warning(f"⚠️ LPT schneidet hier sogar schlechter ab als {worse_than}: {abs(worst_gap):.1f} % mehr{vehicle_hint}. Kein Fehler - Grahams Garantie begrenzt den Abstand zum ECHTEN OPTIMUM (siehe CP-SAT-Feld oben), nicht den Abstand zu einer bestimmten anderen Regel auf genau dieser Instanz. Das kann auch OHNE Rüstzeiten vorkommen - anders als bei den bewiesen optimalen Regeln in Stück 1-4/6.")
else:
    tail = " (auch mit Rüstzeiten - bei dieser Instanz trifft LPT trotzdem das Optimum, das ist nicht garantiert)" if vehicle == "logistik" and a.optimal is not None and a.lpt_matches_optimum else ""
    st.success(f"✅ LPT ist {a.gap_arbitrary:.1f} % besser als dieselbe Zuweisung ohne Sortierung und {a.gap_random:.1f} % besser als eine zufällige Reihenfolge{tail}.")

st.markdown("---")

# --- Sweeps -----------------------------------------------------------------------------------------------------------------------------

st.subheader("📐 Wie stark hängt der Vorsprung von der Instanz ab?")
sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda k: SWEEP_LABELS[k], key="sweep_select")
if st.button("Sweep über 5 feste Instanzen berechnen (dauert wenige Sekunden)", key="sweep_start"):
    st.session_state["sweep_done"] = st.session_state.get("sweep_done", set()) | {sweep_param}
if sweep_param in st.session_state.get("sweep_done", set()):
    rows_sweep = _sweep(sweep_param, Settings())
    st.plotly_chart(build_sweep(rows_sweep, SWEEP_LABELS[sweep_param]), width="stretch", key="sweep_chart")
    st.caption("Mittel über 5 feste Instanzen (Seeds 100000–100004) mit je drei Zufalls-Ketten für die Vergleichsreihenfolge.")

st.markdown("---")

# --- Experimente ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Hält Grahams bewiesene Schranke wirklich?")
if st.button("CP-SAT über n = 2 bis 9 und mehrere Maschinenzahlen berechnen (dauert etwa 10 Sekunden)", key="graham_start"):
    st.session_state["graham_on"] = True
if st.session_state.get("graham_on"):
    rows_g = _graham_check()
    st.plotly_chart(build_graham_chart(rows_g, min(int(m_machines), 4)), width="stretch", key="graham_chart")
    st.caption("Schlechtestes beobachtetes Verhältnis LPT/Optimum über 5 feste Instanzen je Größe, gegen Grahams bewiesene Schranke 4/3 - 1/(3m). Jeder Punkt ÜBER der Schranke wäre ein Fehler im Beweis oder in der Implementierung - anders als bei Stück 1-4/6 ist hier keine 100-%-Trefferquote zu erwarten, aber die Schranke darf NIE überschritten werden.")

st.markdown("---")

st.subheader("🔬 Wie teuer ist eine exakte Lösung wirklich?")
if st.button("Rechenzeit für n = 2 bis 9 messen (dauert etwa 1 Sekunde)", key="timing_start"):
    st.session_state["timing_on"] = True
if st.session_state.get("timing_on"):
    rows_t = _timing(int(m_machines))
    st.plotly_chart(build_timing(rows_t), width="stretch", key="timing_chart")
    last = rows_t[-1]
    st.caption(f"Bei {last['value']} Aufträgen braucht CP-SAT bereits {last['exact_seconds']*1000:.0f} ms, LPT {last['lpt_seconds']*1000:.3f} ms.")

st.markdown("---")

st.subheader("🔬 Werkstatt/Logistik: bleibt LPT gut, wenn Rüstzeiten dazukommen?")
if st.button("Rüstzeit von 0 bis 60 Minuten durchfahren (dauert wenige Sekunden)", key="setup_start"):
    st.session_state["setup_on"] = True
if st.session_state.get("setup_on"):
    rows_s = _setup_gap_sweep(min(int(n_jobs), C.EXACT_MAX_N), int(m_machines), int(n_families))
    st.plotly_chart(build_setup_gap(rows_s), width="stretch", key="setup_chart")
    st.caption("LPT sortiert weiterhin nur nach Bearbeitungszeit und ignoriert die Rüstzeit beim Familienwechsel; verglichen mit der echten Optimallösung MIT Rüstzeiten (CP-SAT, deshalb kleine Instanz). Anders als bei Stück 1-4/6: der Abstand bei Rüstzeit 0 ist NICHT automatisch null - LPT ist schon ohne Rüstzeiten keine bewiesen optimale Regel (siehe 🚧 unten).")

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Rüstzeiten sind nicht sequenzabhängig** | Sobald ein Familienwechsel auf derselben Maschine zusätzlich Zeit kostet (Vehikel „Werkstatt/Logistik“), gilt Grahams Garantie nicht mehr - der Abstand zum echten Optimum wächst mit der Rüstzeit (siehe Experiment oben), und LPT kann im Einzelfall sogar schlechter als die falsche Regel abschneiden. | Kein direkter Nachfolger in dieser Linie |
| **Alle Maschinen sind identisch** | Mit unterschiedlich schnellen Maschinen (Qm) oder auftragsabhängigen Zeiten je Maschine (Rm) ändert sich die Zuordnungsfrage komplett - LPT in dieser einfachen Form ist dafür nicht mehr definiert. | Kein direkter Nachfolger in dieser Linie |
| **Jeder Auftrag braucht nur eine Operation** | Sobald Aufträge mehrere Operationen auf unterschiedlichen Maschinen in unterschiedlicher Reihenfolge brauchen, wird daraus ein Job Shop - Zuordnung UND Reihenfolge UND Maschinenwahl zugleich. | **Job Shop** (Folgestück) |
"""
)
st.caption(
    "Siebtes Stück der Linie „Klassische Scheduling-Theorie“: die zweite neue Dimension (parallele Maschinen). "
    "Konvergenzpunkt der Linie ist der **Job Shop** (Folgestück): Reihenfolge (Stück 1-5), serielle Maschinen "
    "(Stück 6) und parallele Maschinen (dieses Stück) kommen dort zusammen."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem** ($Pm||C_{\max}$): $n$ Aufträge mit Bearbeitungszeit $p_j$, $m$ identische parallele Maschinen.
Gesucht: eine Zuordnung der Aufträge zu Maschinen, die $C_{\max} = \max_k \sum_{j \in \text{Maschine } k} p_j$
minimiert.

**List Scheduling (Graham 1966).** Aufträge in BELIEBIGER Reihenfolge nacheinander der aktuell am wenigsten
ausgelasteten Maschine zuweisen: $C_{\max} \le (2 - \frac{1}{m}) \cdot C_{\max}^{\text{opt}}$.

**LPT (Graham 1969).** Dieselbe Zuweisung, aber Aufträge vorher ABSTEIGEND nach $p_j$ sortiert:
$C_{\max} \le (\frac{4}{3} - \frac{1}{3m}) \cdot C_{\max}^{\text{opt}}$ - eine engere Garantie allein durch die
Sortierung, ohne den Zuordnungs-Algorithmus selbst zu ändern.

**Warum die Sortierung hilft (Beweisskizze).** Sei $j^*$ der Auftrag, der zuletzt fertig wird. Jede Maschine war
bis zu diesem Zeitpunkt beschäftigt, also $C_{\max} \le \bar C + p_{j^*}$ mit $\bar C$ = mittlere Last vor
$j^*$s Zuweisung, und $\bar C \le C_{\max}^{\text{opt}} \cdot \frac{m-1}{m}$. Bei LPT ist $p_{j^*}$ klein (spät
sortiert), was die Schranke verbessert - bei beliebiger Reihenfolge kann $p_{j^*}$ selbst schon fast
$C_{\max}^{\text{opt}}$ groß sein.

**CP-SAT-Modell** (`solve_exact`): ein Mehrfach-Kreis-Modell ("multiple circuit", VRP-Variante) über einen
gemeinsamen Depot-Knoten und bis zu $m$ Rundreisen - optimiert Zuordnung UND Reihenfolge je Maschine gemeinsam;
bei Rüstzeit 0 kollabiert es exakt zum rüstzeitfreien Fall.

**Kennzahl.** Abstand zu LPT $= 100 \cdot (C_{\max} - C_{\max}^{\text{LPT}}) / C_{\max}^{\text{LPT}}$ - kann
negativ werden. Für $n \le 9$ zusätzlich CP-SAT als exakte Gegenprobe.

Implementiert in `lpt_algorithm.py` (List Scheduling, Graham-Schranken, CP-SAT), `lpt_scenario.py`/
`lpt_scenario_logistik.py` (die zwei Vehikel), `lpt_evaluation.py` (Kennzahlen, Sweep, Graham-Schranken-Check,
Timing-Messreihe, Rüstzeit-Härtetest).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
