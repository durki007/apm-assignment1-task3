# Advanced Process Mining — Assignment Part I, Question 3
## Task Description & Technical Specification (Python Implementation)

**Domain assigned:** Public transport (ASEAG / Deutsche Bahn).
**Scenario:** *2036 — Olympic Games in Aachen.*
**Deliverable target:** An object-centric event log `L` in OCEL 2.0 plus all derived
models, validations, figures, and queries required by Question 3 (a)–(g).

This document is the build spec for the Python codebase. It states the process
design, the toolchain, the project layout, and a per-subtask implementation
contract (inputs → processing → outputs) so that each script/notebook can be
written and reviewed independently.

---

## 1. Scope: what is implemented in Python vs. produced manually

Question 3 mixes written analysis, drawn models, and computational artifacts.
The split below is the contract for "what is code."

| Subtask | Nature | Python? | Notes |
|---|---|---|---|
| (a) Naming + behavior write-up | Written | Indirect | Names/values live in `config.py`; the prose goes in the report. |
| (b) E2O / O2O type-level tables | Written | Yes (helper) | `render_tables.py` emits the matrices from the model definition. |
| (c) Normative OC Petri net `N1` | Drawn | Optional | Hand/draw.io is fine; a Graphviz reference can be auto-rendered. |
| (d) Generate `L` (OCEL 2.0) | Computational | **Yes** | `generate_log.py` using `r4pm`. |
| (d-i) Submit `L` | Artifact | **Yes** | `.sqlite` (primary) + `.json` (optional). |
| (d-ii) Show R(i),(ii),(iii) | Validation | **Yes** | `validate.py`. |
| (d-iii) Show R(v)a, R(v)b | Validation | **Yes** | `validate.py`. |
| (d-iv) Flatten to `ot_oa`, discover net | Computational | **Yes** | `flatten_discover.py` (PM4Py). |
| (d-v) Flatten to `ot_sync`, discover net | Computational | **Yes** | `flatten_discover.py` (PM4Py). |
| (d-vi) Synchronization visualization | Figure | **Yes** | `dotted_chart.py` (Matplotlib) — a valid alternative to ProM's Dotted Chart. |
| (e) Discover OCPN `N2` | Computational | **Yes** | `discover_ocpn.py` (PM4Py). |
| (f) OCPQ queries i–iii | Query + screenshot | Partial | Actual deliverable = OCPQ screenshots. `queries.py` implements equivalent checks in Python to design and verify them. |
| (g) Custom OCPQ business query | Query + screenshot | Partial | Same as (f): Python equivalent for verification, OCPQ screenshot for submission. |

> **Important:** subtasks (f) and (g) explicitly require OCPQ screenshots. OCPQ is a
> GUI tool. The Python query module reproduces the same result sets so you can
> (1) develop the logic quickly, and (2) prove the OCPQ output is correct, but the
> screenshots from OCPQ are still mandatory for grading.

---

## 2. Toolchain & environment

### 2.1 Language / runtime
- **Python** `>=3.11,<3.13` (PM4Py and the `r4pm` wheels both support this range; widen only if a wheel is missing on your platform).
- **Dependency management:** **Poetry** (≥1.8).

### 2.2 System dependencies (not pip-installable)
- **Graphviz** (the `dot` binary) — required by PM4Py for Petri-net / OCPN rendering.
  - Debian/Ubuntu: `sudo apt-get install graphviz`
  - macOS: `brew install graphviz`
  - Windows: install Graphviz and add it to `PATH`.

### 2.3 Python dependencies (declared via Poetry)
| Package | Role |
|---|---|
| `r4pm` | Build and serialize the OCEL 2.0 log (subtask d). |
| `pm4py` | OCEL I/O, flattening, Petri-net & OCPN discovery, visualization. |
| `pandas` | Tabular manipulation for validation and queries. |
| `matplotlib` | Dotted-chart synchronization figure (d-vi). |
| `graphviz` | Python binding used by PM4Py viz. |
| `jupyter`, `ipykernel` | Notebooks. |

### 2.4 `pyproject.toml` (Poetry) — reference
```toml
[tool.poetry]
name = "olympic-transport-ocel"
version = "0.1.0"
description = "APM Assignment Part I, Q3 — object-centric event data simulation (public transport)."
authors = ["Group <GroupID>"]
readme = "README.md"
packages = [{ include = "olympic_transport" }]

[tool.poetry.dependencies]
python = ">=3.11,<3.13"
r4pm = "*"
pm4py = "*"
pandas = "*"
matplotlib = "*"
graphviz = "*"

[tool.poetry.group.dev.dependencies]
jupyter = "*"
ipykernel = "*"

[tool.poetry.scripts]
generate = "olympic_transport.generate_log:main"
validate = "olympic_transport.validate:main"
discover = "olympic_transport.flatten_discover:main"
ocpn = "olympic_transport.discover_ocpn:main"
dotted = "olympic_transport.dotted_chart:main"
queries = "olympic_transport.queries:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

> Pin exact versions in `poetry.lock` once the build works (`poetry lock`), and
> commit the lockfile so the result is reproducible.

### 2.5 Setup commands
```bash
poetry install
poetry run python -m olympic_transport.generate_log     # produces data/log.sqlite
poetry run python -m olympic_transport.validate          # R(i),(ii),(iii),(v) checks
poetry run python -m olympic_transport.flatten_discover  # N_ot_oa, N_ot_sync
poetry run python -m olympic_transport.discover_ocpn     # N2
poetry run python -m olympic_transport.dotted_chart      # synchronization figure
poetry run python -m olympic_transport.queries           # Python equivalents of OCPQ queries
poetry run jupyter lab                                    # interactive notebooks
```

---

## 3. Project structure

Matches the archive layout required by the assignment, with all code under `code/`.

```
assignment_Part1_<GroupID>/
├── report.pdf
├── data/
│   ├── log.sqlite                 # OCEL 2.0 (primary deliverable, d-i)
│   └── log.json                   # OCEL 2.0 (optional alternate serialization)
├── models/
│   ├── N1_normative.svg           # hand/draw.io (c)  [+ optional Graphviz ref]
│   ├── N_ot_oa.pnml               # discovered net on ticket-flattened log (d-iv)
│   ├── N_ot_sync.pnml             # discovered net on passenger-flattened log (d-v)
│   └── N2_ocpn.svg                # discovered OC Petri net (e)
├── figures/
│   ├── N_ot_oa.png
│   ├── N_ot_sync.png
│   ├── N2_ocpn.png
│   ├── dotted_chart_sync.png      # (d-vi)
│   └── ocpq_*.png                 # OCPQ query screenshots (f, g)
└── code/
    ├── pyproject.toml
    ├── poetry.lock
    ├── README.md
    ├── olympic_transport/
    │   ├── __init__.py
    │   ├── config.py              # design constants (single source of truth)
    │   ├── generate_log.py        # (d)  build + export OCEL 2.0 with r4pm
    │   ├── validate.py            # (d-ii, d-iii)  requirement checks
    │   ├── flatten_discover.py    # (d-iv, d-v)  flatten + Petri-net discovery
    │   ├── discover_ocpn.py       # (e)  OCPN discovery (N2)
    │   ├── dotted_chart.py        # (d-vi)  synchronization visualization
    │   ├── queries.py             # (f, g)  Python equivalents of OCPQ queries
    │   └── render_tables.py       # (b)  emit E2O/O2O tables from the model
    └── notebooks/
        ├── 01_generate.ipynb
        ├── 02_validate.ipynb
        ├── 03_flatten_discover.ipynb
        ├── 04_ocpn_n2.ipynb
        ├── 05_dotted_chart.ipynb
        └── 06_queries.ipynb
```

---

## 4. Process design (the domain model)

This is the single source of truth; encode it in `config.py`. The key design
choice is that the **attribute-carrying type** (R vi) and the **synchronizing
type** (R viii) are *different*, so the two flattened nets in (d-iv) and (d-v)
expose different phenomena.

### 4.1 Object types (4 — satisfies R(ii) ≥ 3)
| Object type | Meaning | Roles |
|---|---|---|
| `Passenger` | An individual traveler (athlete, official, or spectator). | `ot_paired1`, `ot_child`, `ot_sync` |
| `TravelTicket` | A ticket issued to exactly one passenger. Holds attribute `fare_class`. | `ot_paired2`, `ot_oa` |
| `GroupBooking` | One reservation covering many passengers (delegation / fan group). | `ot_parent` |
| `Departure` | A scheduled shuttle/train run binding a batch of passengers. | synchronization context |

### 4.2 Object attribute (R vi)
- `ot_oa = TravelTicket`
- `oa = fare_class`, **static**, **categorical**, domain `{"accredited", "standard"}` (≥ 2 labels).
- Semantics: accredited persons (athletes/officials) vs. standard ticket holders (spectators).

### 4.3 Event types (7 — satisfies R(iii) ≥ 5)
| Event type | Meaning | Special role |
|---|---|---|
| `CreateGroupBooking` | A group reservation is opened for a set of passengers. | |
| `IssueTravelTicket` | A ticket is issued to one passenger. | |
| `AssignToDeparture` | A departure is assigned a set of passengers. | `et_group` (R viii) |
| `BoardViaAccreditationLane` | An accredited passenger boards via the accreditation lane. | `et_x1` (R vii) |
| `ValidateAtPublicGate` | A standard passenger validates at the public gate. | `et_x2` (R vii) |
| `Depart` | The departure leaves with its assigned passengers. | `et_sync` (R viii) |
| `CompleteJourney` | A passenger completes the journey. | |

### 4.4 E2O relations (which event type touches which object type)
| Event type | Passenger | TravelTicket | GroupBooking | Departure |
|---|---|---|---|---|
| `CreateGroupBooking` | ✓ (all in group) | | ✓ | |
| `IssueTravelTicket` | ✓ | ✓ | | |
| `AssignToDeparture` | ✓ (all in batch) | | | ✓ |
| `BoardViaAccreditationLane` | ✓ | ✓ | | |
| `ValidateAtPublicGate` | ✓ | ✓ | | |
| `Depart` | ✓ (all in batch) | | | ✓ |
| `CompleteJourney` | ✓ | | | |

Every event type touches ≥1 object and every object type is touched by ≥1 event
type ⇒ **R(iv)** holds.

### 4.5 O2O relations (R v)
| Source object | → Target object | Qualifier | Cardinality | Requirement |
|---|---|---|---|---|
| `Passenger` | `TravelTicket` | `holds` | one-to-one | **R(v)a** (`ot_paired1`↔`ot_paired2`) |
| `Passenger` | `GroupBooking` | `belongs_to` | many-to-one (parent has many children) | **R(v)b** (`ot_parent`→`ot_child`) |

### 4.6 Data-driven decision (R vii)
Each `TravelTicket` (`ot_oa`) participates in **exactly one** of
`BoardViaAccreditationLane` (`et_x1`) or `ValidateAtPublicGate` (`et_x2`), never
both, with the choice driven by `fare_class`:
- `accredited` → `BoardViaAccreditationLane` with high probability (e.g. 0.9), else the other.
- `standard` → `ValidateAtPublicGate` with high probability (e.g. 0.9), else the other.

(Probabilistic dependence is explicitly allowed; keep a small cross-over rate so
the dependence is statistical, not deterministic.)

### 4.7 Batch synchronization (R viii)
- `et_group = AssignToDeparture`, `et_sync = Depart`, `ot_sync = Passenger`.
- For every `Departure d`: a single `AssignToDeparture` event lists passenger set
  `S(d)`, and a single later `Depart` event lists the **same** set `S(d)`.
  Both events also relate to `d`. ⇒ precedence + synchronization (**R viii-a**).
- At least one departure has `|S(d)| > 1` (groups travel together) ⇒ convergence
  (**R viii-b**).

### 4.8 Per-passenger event ordering (timestamps)
```
CreateGroupBooking  <  IssueTravelTicket  <  AssignToDeparture
                    <  (BoardViaAccreditationLane | ValidateAtPublicGate)
                    <  Depart  <  CompleteJourney
```
`AssignToDeparture` and `Depart` are emitted **once per departure** (one event
each, listing the whole batch); the other events are **per passenger**.

### 4.9 Sizing (satisfies R(i) ≥ 100 events with margin)
| Parameter | Value | Events contributed |
|---|---|---|
| Group bookings | 12 | 12 × `CreateGroupBooking` = 12 |
| Passengers (2–5 per booking) | ~36 | 36 `IssueTravelTicket` + 36 boarding + 36 `CompleteJourney` = 108 |
| Departures | ~10 | 10 × (`AssignToDeparture` + `Depart`) = 20 |
| **Total** | | **≈ 140 events** |

Use a fixed RNG seed so the log (and therefore every downstream figure) is
reproducible.

---

## 5. Module specifications (implementation contracts)

### 5.1 `config.py` — design constants
**Purpose:** single source of truth for all names, the attribute domain, sizing,
probabilities, the RNG seed, and file paths.
**Exposes (suggested):**
- `OBJECT_TYPES`, `EVENT_TYPES` (lists of the names in §4).
- `FARE_CLASSES = ["accredited", "standard"]`.
- `CROSSOVER_PROB = 0.1`.
- Sizing: `N_BOOKINGS`, `PASSENGERS_PER_BOOKING_RANGE`, `N_DEPARTURES`.
- `SEED = 42`.
- Path constants for `data/`, `models/`, `figures/`.
- The E2O and O2O specification as data structures (so `render_tables.py` and the
  generator both read from it).

### 5.2 `generate_log.py` — build & export the OCEL (d, d-i)
**Library:** `r4pm` (`import r4pm`, `import r4pm.bindings as b`).
**Processing:**
1. `locel = b.locel_new()`.
2. Declare event types with `b.locel_add_event_type(locel, name, attrs)` and object
   types with `b.locel_add_object_type(locel, name, attrs)`.
   `TravelTicket` declares attribute `{"name": "fare_class", "type": "string"}`.
3. Generate the population: bookings → passengers (assign each a `fare_class`),
   one ticket per passenger, assignment of passengers to departures.
4. Add objects with `b.locel_add_object(locel, type, id[, history])`. For the
   **static** `fare_class`, encode a single time-indexed entry at the UNIX epoch:
   `history = [[("1970-01-01T00:00:00Z", fare_class_value)]]`.
5. Add events with `b.locel_add_event(locel, event_type, timestamp_iso, id, attr_values)`
   following the ordering in §4.8; emit `AssignToDeparture`/`Depart` once per
   departure with the full batch.
6. Add relationships:
   - E2O: `b.locel_add_e2o(locel, b.locel_get_ev_by_id(locel, eid), b.locel_get_ob_by_id(locel, oid), qualifier)`.
   - O2O: `b.locel_add_o2o(locel, src_ref, tgt_ref, qualifier)` for `holds` and `belongs_to`.
   - Order requirement: every event/object must be added before any relationship that references it.
7. Export: `r4pm.export_item(locel, str(DATA_DIR / "log.sqlite"))` and optionally
   `"log.json"`. The extension selects the OCEL 2.0 serialization.

**Outputs:** `data/log.sqlite` (+ optional `data/log.json`).

### 5.3 `validate.py` — requirement checks (d-ii, d-iii)
**Library:** `pm4py` (load) + `pandas`.
**Load:** `ocel = pm4py.read_ocel2_sqlite("data/log.sqlite")`.
**Checks → printed report + assertions:**
- **R(i):** `len(ocel.events) >= 100`.
- **R(ii):** number of distinct object types `>= 3`.
- **R(iii):** number of distinct event types `>= 5`.
- **R(v)a (one-to-one):** over the `holds` O2O relation, assert each `Passenger`
  maps to exactly one `TravelTicket` and each `TravelTicket` maps back to exactly
  one `Passenger` (bijection).
- **R(v)b (one-to-many):** over `belongs_to`, assert each `Passenger` has exactly
  one `GroupBooking`, and that at least one `GroupBooking` has > 1 `Passenger`
  (demonstrates the "many" side).

**Outputs:** console table of pass/fail per requirement; non-zero exit on failure.
Capture this output for the report (R(i)/(ii)/(iii) and R(v) evidence).

### 5.4 `flatten_discover.py` — flattened Petri nets (d-iv, d-v)
**Library:** `pm4py`.
**Processing (for each target object type):**
- `flat = pm4py.ocel_flattening(ocel, object_type)`.
- `net, im, fm = pm4py.discover_petri_net_inductive(flat)`.
- Save model: `pm4py.write_pnml(net, im, fm, models/<name>.pnml)`.
- Save figure: `pm4py.save_vis_petri_net(net, im, fm, figures/<name>.png)`.
- **(d-iv)** target = `TravelTicket` (`ot_oa`) → `N_ot_oa`. Expected shape:
  `IssueTravelTicket` followed by an **XOR split** into
  `BoardViaAccreditationLane` vs. `ValidateAtPublicGate` — this is the visible
  reflection of the R(vii) data-driven choice.
- **(d-v)** target = `Passenger` (`ot_sync`) → `N_ot_sync`. Expected shape: a
  sequence in which `AssignToDeparture` directly **precedes** `Depart` — the
  visible reflection of the R(viii-a) precedence constraint.

**Outputs:** `models/N_ot_oa.pnml`, `models/N_ot_sync.pnml`,
`figures/N_ot_oa.png`, `figures/N_ot_sync.png`.
For the report: one sentence each on how the XOR (d-iv) and the precedence (d-v)
appear in the discovered nets.

> Function names can shift slightly between PM4Py versions (e.g. flattening and
> visualization helpers). Verify against the installed version and adjust; keep
> the lockfile pinned once it works.

### 5.5 `discover_ocpn.py` — object-centric Petri net N2 (e)
**Library:** `pm4py`.
**Processing:**
- `ocpn = pm4py.discover_oc_petri_net(ocel)`.
- `pm4py.save_vis_ocpn(ocpn, figures/N2_ocpn.png)` (and/or export to `models/`).
**Outputs:** `figures/N2_ocpn.png`, `models/N2_ocpn.svg`.
For the report: compare `N2` to the normative `N1` from (c) and explain any
deviation (1–2 sentences each), e.g. silent transitions or variant arcs
introduced by the discovery algorithm, or allowed-but-unplanned control flow.

### 5.6 `dotted_chart.py` — synchronization figure (d-vi)
**Library:** `matplotlib` + `pandas` (a valid alternative to ProM's Dotted Chart;
ProM remains an option if you prefer a screenshot from there).
**Processing:**
1. From `ocel.relations`, extract `AssignToDeparture` and `Depart` events with
   their `Passenger` objects and timestamps.
2. Plot a dotted chart: x = timestamp, y = passenger (grouped/sorted by their
   `Departure`), one marker style/color for `AssignToDeparture` and another for
   `Depart`.
3. Annotate so the reader can see that, per departure, the set of passengers under
   the `Depart` marker column is identical to the set under the preceding
   `AssignToDeparture` column.
**Output:** `figures/dotted_chart_sync.png`.
For the report: 2–3 sentences interpreting that each `Depart` event shares its
exact passenger set with a preceding `AssignToDeparture` event (R viii-a).

### 5.7 `queries.py` — Python equivalents of the OCPQ queries (f, g)
**Library:** `pm4py` + `pandas`. **These verify/develop the queries; OCPQ
screenshots remain the submitted artifact.**
Implement, parameterized by the chosen label `c` and threshold `k`:
- **(f-i)** All `TravelTicket` objects with `fare_class == c` (pick e.g. `c = "accredited"`).
- **(f-ii)** All `TravelTicket` objects such that: `fare_class == c`, related to
  **exactly one** `BoardViaAccreditationLane` event, and **zero**
  `ValidateAtPublicGate` events.
- **(f-iii)** All `GroupBooking` objects related (via the `belongs_to` O2O) to
  **more than `k`** `Passenger` objects (state your chosen `k ≥ 1`).
- **(g)** One custom business query — e.g. *"Which `Depart` events carry more than
  N standard-fare passengers?"* or *"Which accredited passengers never produced a
  `CompleteJourney` event?"* Print the result set and explain the business value.
**Output:** printed result tables (counts + IDs) used to confirm the OCPQ screenshots.

### 5.8 `render_tables.py` — type-level relation tables (b)
**Purpose:** emit the E2O and O2O matrices (as Markdown) directly from the
`config.py` specification, so the report's tables cannot drift from the generator.
**Output:** Markdown printed to stdout / written to a file for paste-in.

---

## 6. Manual / non-Python deliverables (for completeness)

| Subtask | Deliverable | Tool |
|---|---|---|
| (a) | Named entities + 3–4 sentence behavior description | Report prose (names from `config.py`). |
| (c) | Annotated normative OC Petri net `N1` | draw.io / OCπ / by hand. Transitions = the 7 event types; double (variable) arcs for the convergent `Passenger` flow into `Depart`. |
| (f-i, f-ii, f-iii), (g) | Executed-query **screenshots** | OCPQ (`https://ocpq.aarkue.eu/`). Load `data/log.sqlite`; build each query as a node tree; verify the result table matches `queries.py`. |

---

## 7. Build / run pipeline (dependency order)

The critical path is **design → generate → everything else**; nothing downstream
can run before `data/log.sqlite` exists and passes validation.

```
config.py  (design constants)
    │
    ▼
generate_log.py ──▶ data/log.sqlite (+ log.json)
    │
    ├──▶ validate.py            (R i, ii, iii, v)         → report evidence
    ├──▶ flatten_discover.py    (N_ot_oa, N_ot_sync)      → models/ + figures/
    ├──▶ discover_ocpn.py       (N2)                      → figures/ (compare to N1)
    ├──▶ dotted_chart.py        (synchronization figure)  → figures/
    └──▶ queries.py             (verify f, g)             → OCPQ screenshots
```

---

## 8. Requirement traceability matrix

| Req | Statement (abbrev.) | Satisfied by | Verified in |
|---|---|---|---|
| R(i) | ≥ 100 events | Sizing §4.9 | `validate.py` |
| R(ii) | ≥ 3 object types | 4 object types §4.1 | `validate.py` |
| R(iii) | ≥ 5 event types | 7 event types §4.3 | `validate.py` |
| R(iv) | E2O coverage both ways | §4.4 | inspection / `validate.py` |
| R(v)a | one-to-one | `Passenger holds TravelTicket` §4.5 | `validate.py` (bijection) |
| R(v)b | one-to-many | `Passenger belongs_to GroupBooking` §4.5 | `validate.py` |
| R(vi) | static categorical attribute | `fare_class` on `TravelTicket` §4.2 | generator + `validate.py` |
| R(vii) | data-driven XOR | board vs. validate by `fare_class` §4.6 | `flatten_discover.py` (d-iv) |
| R(viii)a | precedence + synchronization | `AssignToDeparture` → `Depart`, same set §4.7 | `dotted_chart.py`, `flatten_discover.py` (d-v) |
| R(viii)b | convergence | ≥1 departure with >1 passenger §4.7 | `validate.py` |

---

## 9. Risks & notes

- **`r4pm` attribute history is time-indexed.** A "static" attribute is a
  single epoch-stamped entry; do not write multiple values or the attribute stops
  being static (breaks R vi).
- **Synchronization is fragile in the generator.** Emit one `AssignToDeparture`
  and one `Depart` per departure over the *identical* passenger set. If you build
  the two sets independently they may diverge and silently break R(viii-a).
- **PM4Py API drift.** Flattening, discovery, and visualization helper names vary
  by version. Confirm against your installed version; pin via `poetry.lock`.
- **Graphviz must be on `PATH`** for any net/OCPN rendering to succeed.
- **OCPQ is mandatory for (f)/(g).** The Python query module is a development and
  verification aid, not a substitute for the required screenshots.
- **Reproducibility.** Fix the RNG seed in `config.py`; regenerating the log must
  reproduce every figure and query result.