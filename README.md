# LPT – eine bewiesene Garantie statt eines Beweises – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-lpt-scheduling-demo.streamlit.app/)**

Siebtes Stück der **Klassische-Scheduling-Theorie-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch
– Operations Research und Machine Learning": $n$ Aufträge mit je EINER Bearbeitungszeit $p_j$, $m$ IDENTISCHE
parallele Maschinen, Ziel ist die maximale Maschinenlast $C_{\max}$ zu minimieren ($Pm||C_{\max}$ in der
α|β|γ-Notation).

**Einordnung in die Linie:** Die zweite neue Dimension - **parallele statt serielle Maschinen** (nach Johnson,
Stück 6: serielle Maschinen). **LPT** (Longest Processing Time first) ist NICHT beweisbar optimal, aber Graham
(1969) hat eine **bewiesene Worst-Case-Garantie** gezeigt: $C_{\max}(\text{LPT}) \le (\frac{4}{3} -
\frac{1}{3m}) \cdot C_{\max}(\text{opt})$. Eine dritte Art von Ergebnis in dieser Linie - nach "exakter Beweis"
(Stück 1-4/6) und "nur Heuristik, keine Garantie" (Stück 5, ATC) jetzt "keine Optimalität, aber eine bewiesene
Grenze, wie schlecht es werden kann".
```
SPT (1||ΣCⱼ, Vertauschungsargument)                                              [Stück 1]
EDD (1||Lmax, dasselbe Beweismuster, andere Zielfunktion)                        [Stück 2]
Moore-Hodgson (1||ΣUⱼ, EDD + gezieltes Streichen)                                [Stück 3]
WSPT / Smith's Rule (1||ΣwⱼCⱼ, verallgemeinert SPT mit Gewichten)                [Stück 4]
ATC (1||ΣwⱼTⱼ, stark NP-schwer - erstes Stück ohne Beweis)                       [Stück 5]
Johnson-Regel (F2||Cmax, erste Erweiterung auf zwei Maschinen)                   [Stück 6]
 └─ LPT (Pm||Cmax, parallele Maschinen, bewiesene Worst-Case-Garantie)           [dieses Stück]
Job Shop (Konvergenzpunkt: Reihenfolge UND serielle UND parallele Maschinen)     [Folgestück]
```

Ergebnis in Kürze: bei 20 Aufträgen auf 3 Maschinen liegt der Cmax-Wert bei derselben Zuweisung ohne
Sortierung im Mittel **5,9 %** und bei einer zufälligen Reihenfolge **6,9 %** über dem von LPT - deutlich kleinere Margen als in Stück 1-5, weil
$C_{\max}$ (wie in Stück 6) nur vom höchstbelasteten Zweig abhängt. **Der zentrale, überraschende Befund dieses
Stücks**: Grahams Garantie bindet nur das Verhältnis zum ECHTEN OPTIMUM, NICHT einen paarweisen Vergleich zu
einer bestimmten anderen Regel auf einer bestimmten Instanz - **LPT kann deshalb sogar OHNE Rüstzeiten
schlechter abschneiden als die beliebige oder eine zufällige Reihenfolge** (gemessen: n=10, m=2, Seed 19, LPT
3,8 % schlechter als ohne Sortierung). Das war bei KEINER der bewiesen optimalen Regeln in Stück 1-4/6 möglich.
**Grahams Schranke selbst wird nie verletzt** (100 % Trefferquote über n=2..9 und m=2..4, CP-SAT-geprüft) - das
ist der eigentliche, unverrückbare Beweis. Auf dem Werkstatt/Logistik-Vehikel wächst der Abstand zum Optimum
zusätzlich mit der Rüstzeit (von **3,9 %** bei 0 Minuten auf **39,6 %** bei 60 Minuten je Familienwechsel).

| Frage | Ergebnis (Mittel über 5 feste Instanzen, Seeds 100000–100004, mit je 3 Ketten-Seeds) |
|---|---|
| Standardfall (20 Aufträge, 3 Maschinen) | ✅ Cmax liegt bei beliebiger Reihenfolge **5,9 %**, bei Zufall **6,9 %** über dem von LPT |
| **Grahams Schranke (n=2..9, m=2..4)** | ✅ **NIE** verletzt - schlechtester beobachteter Fall bei ~91 % der Schranke |
| **LPT kann eine falsche Regel schlagen lassen** | ❌ **Ja, auch ohne Rüstzeiten** (n=10, m=2, Seed 19: -3,7 %) - eine echte Überraschung |
| **Vehikel Werkstatt/Logistik** | ❌ Rüstzeit 0/5/15/30/60 Minuten: **3,9/5,2/9,6/16,6/39,6 %** über dem Optimum |

## Was die Demo zeigt

1. **LPT in Aktion** (Schritt-Slider): **Aufträge** (Bearbeitungszeit) → **Einplanen** (Regler "eingeplante
   Aufträge", Gantt mit einer Zeile JE MASCHINE) → **Ergebnis** (Endlast je Maschine, LPT gegen beliebige
   Reihenfolge).
2. **Was die Sortierung bringt:** LPT, beliebige Reihenfolge (falsche Regel hier), zufällige Reihenfolge,
   CP-SAT-Gegenprobe (n ≤ 9, mit Beweis-Status); auf dem Werkstatt/Logistik-Vehikel zusätzlich Rüstzeiten
   INNERHALB jeder Maschine.
3. **📐 Sweep** über die Anzahl der Aufträge ODER über die Maschinenzahl - zum ersten Mal in dieser Linie ein
   eigener Sweep-Parameter für die Maschinenzahl.
4. **🔬 Experimente auf Abruf:** hält Grahams bewiesene Schranke (der Beweis-Check dieses Stücks - eine
   UNGLEICHUNG, keine Gleichheit); Rechenzeit CP-SAT (Zeitlimit) gegen LPT (O(n log n)); Rüstzeit-Härtetest.
5. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an" (sequenzabhängige Rüstzeiten, identische
   Maschinen, eine Operation je Auftrag) mit Verweis auf den Job Shop als Folgestück.

Regler: Aufträge (2–60), **Maschinen** (2–6, neu in diesem Stück), **Vehikel** (Neutral/Werkstatt-Logistik – bei
Werkstatt zusätzlich Rüstzeit und Anzahl Familien), Seed der Instanz (+ 🎲), Seed der Kette (+ 🎲).

## Die zwei Vehikel (gelten für die ganze Linie)

- **Neutral** (`lpt_scenario.py`): $n$ Aufträge mit EINER Bearbeitungszeit $p_j \sim U(1, 100)$ - keine zweite
  Operation wie in Stück 6, keine Fristen/Gewichte wie in Stück 1-5. Die Maschinenzahl $m$ ist ein eigener
  Regler, nicht Teil der Instanz.
- **Werkstatt/Logistik** (`lpt_scenario_logistik.py`): dieselben Bearbeitungszeiten, aber jeder Auftrag gehört
  zu einer Familie; ein Familienwechsel kostet eine feste Rüstzeit - zum ersten Mal INNERHALB einer von mehreren
  PARALLELEN Maschinen (jede Maschine hat ihre eigene Sequenz und damit ihre eigene Rüstzeit-Historie). Rüstzeit
  0 kollabiert strukturell exakt zum neutralen Vehikel (per Test belegt: identische Zuordnung UND Reihenfolge).

## Modell und Verfahren

- **Instanz** (`lpt_scenario.py`, `lpt_scenario_logistik.py`): Bearbeitungszeiten, Familien und Rüstzeit-Matrix.
- **List Scheduling / LPT** (`lpt_algorithm.py`): Aufträge in gegebener Reihenfolge greedy der am wenigsten
  ausgelasteten Maschine zuweisen, $O(n \log n)$ für die LPT-Sortierung selbst. Dazu Grahams beide Schranken
  (`graham_bound_lpt`, `graham_bound_arbitrary`) und die Rüstzeit-Variante.
- **CP-SAT** (`lpt_algorithm.solve_exact`): ein Mehrfach-Kreis-Modell ("multiple circuit", die VRP-Variante von
  OR-Tools) - EIN gemeinsames Depot, bis zu $m$ Rundreisen (eine je Maschine), optimiert Zuordnung UND
  Reihenfolge je Maschine GEMEINSAM. Gegen unabhängige Brute-Force-Vollaufzählung (alle Zuordnungen × alle
  Permutationen je Maschinengruppe) verifiziert.
- **Auswertung** (`lpt_evaluation.py`): Kennzahlen, Sweep (über Aufträge ODER Maschinen), Graham-Schranken-Check,
  Timing-Messreihe, Rüstzeit-Härtetest.

## Was nicht funktioniert hat / Grenzen

- **Vorab-Annahme: "LPT ist auf dem neutralen Vehikel immer mindestens so gut wie die falschen Regeln" (wie bei
  Stück 1-4/6)** - **widerlegt, und zwar deutlich häufiger als erwartet** (~3,6 % der getesteten Kombinationen
  aus n, m und Seed): Grahams Garantie ist eine Schranke gegenüber dem ECHTEN OPTIMUM, keine paarweise
  Dominanz-Garantie gegenüber einer bestimmten anderen Regel auf einer bestimmten Instanz. Das ist KEIN Fehler,
  sondern der Kern dessen, was "bewiesene Worst-Case-Garantie" von "bewiesene Optimalität" unterscheidet - aber
  die App-Anzeige musste dafür von Anfang an vorzeichenkorrekt und mit einer ehrlichen Erklärung gebaut werden
  (Lehren aus `wspt-demo`/`weighted-tardiness-demo`/`johnson-rule-demo` direkt übernommen).
- **Grahams Schranke SELBST wird nie verletzt** - das ist der tatsächliche, unverrückbare Beweis-Check dieses
  Stücks (100 % über n=2..9, m=2..4, CP-SAT-geprüft), nicht die (hier gar nicht geltende) Aussage "LPT schlägt
  jede andere Regel immer".
- **Der Rüstzeit-0-Fall ist KEIN Nulltest mehr** (wie schon bei ATC/Johnson): LPT hat bereits ohne Rüstzeiten
  einen Gap zum Optimum. Die korrekte Konsistenzprüfung ist strukturell (identische Zuordnung UND Reihenfolge
  bei Rüstzeit 0), nicht "trifft LPT das Optimum".
- **CP-SAT ist nur bis $n \approx 9$ praktikabel** - mit Rüstzeiten und wenigen Maschinen (ein Auftrags-Cluster
  je Maschine wird größer) schwerer als ohne, aber insgesamt deutlich schneller lösbar als Stück 5 (ATC).
- **Synthetische Instanzen:** Bearbeitungszeiten gleichverteilt, alle Maschinen identisch, jeder Auftrag genau
  eine Operation.

## Verifikation

- **CP-SAT gegen unabhängige Brute-Force-Vollaufzählung** (mit und ohne Rüstzeiten): für n = 4 bis 6 über
  mehrere Seeds stimmt das Mehrfach-Kreis-Modell exakt mit einer unabhängigen Vollaufzählung aller Zuordnungen ×
  Permutationen überein.
- **Struktureller Konsistenz-Test**: LPTs Zuordnung UND Reihenfolge bei Rüstzeit 0 sind identisch mit dem
  neutralen Vehikel.
- **Handrechnung:** eine kleine Instanz ($p = [1,1,2]$, $m=2$) bestätigt von Hand, dass LPT (Cmax 2) die
  beliebige Reihenfolge (Cmax 3) schlägt, weil der große Auftrag zuerst auf eine eigene Maschine kommt.
- **Alle Zahlen der App-Texte sind als Tests hinterlegt** (Standardfall, Graham-Schranken-Check, Rüstzeit-
  Härtetest; positive **und** negative Aussagen inklusive des Falls, in dem LPT schlechter als eine falsche
  Regel abschneidet - auch ohne Rüstzeiten); alle 5 Presets geprüft; AppTest-Rauchtests (Voreinstellung, jedes
  Preset, jeder Schritt auf beiden Vehikeln, Würfel-Knöpfe, Permalink-Grenzen inkl. ungültigem Vehikel,
  Extremwerte, Experimente auf Abruf, Footer, korrekt formatierte negative Prozent-Abstände); eigener Test für
  die ausblendbaren Regler (kein verwaister Widget-Zustand nach Permalink/Preset - von Anfang an eingebaut).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Schritte, Ergebnis, 📐 Sweep, 🔬 Experimente, 🚧 Grenzen, Mathe |
| `lpt_algorithm.py` | List Scheduling/LPT, Graham-Schranken, CP-SAT (Mehrfach-Kreis-Modell) |
| `lpt_scenario.py` | Vehikel Neutral |
| `lpt_scenario_logistik.py` | Vehikel Werkstatt/Logistik (Familien, Rüstzeit-Matrix) |
| `lpt_constants.py` | Konstanten, Presets |
| `lpt_evaluation.py` | Kennzahlen, Sweep, Graham-Schranken-Check, Timing-Messreihe, Rüstzeit-Härtetest |
| `lpt_presets.py`, `lpt_visualization.py` | Permalink/Presets (inkl. `seed_widget`/`KEPT` für ausblendbare Regler), Plotly-Figuren (ein Trace je Maschine, achsengesperrt) |
| `tests/` | CP-SAT gegen Vollaufzählung, Szenario und Auswertung, Aussagen der App, Presets, versteckter Widget-Zustand, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Scheduling-Theorie: SPT bis RCPSP](https://sebastianhanisch.net/konzepte-klassische-scheduling-theorie.html).
