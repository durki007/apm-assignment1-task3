# APM Assignment — Python Code (Part I and Part II)

## Setup

```bash
# Install Poetry >= 1.8, then:
cd code
poetry install
```

**System requirement:** [Graphviz](https://graphviz.org/download/) must be installed and `dot` must be on `PATH`.

## Run Part I pipeline (in order)

```bash
poetry run generate          # → data/log.sqlite + data/log.json
poetry run validate          # R(i),(ii),(iii),(v) checks
poetry run discover          # N_ot_oa, N_ot_sync  → models/ + figures/
poetry run ocpn              # N2                  → figures/
poetry run dotted            # dotted chart        → figures/
poetry run queries           # OCPQ equivalents
poetry run jupyter lab       # interactive notebooks
```

## Run Part II checks

```bash
poetry run q3                # GSLPN trace probabilities (a), (b)
poetry run q5a                # C1, C2, C3 constraint checks
poetry run q5b                # Cameron conformance checking
```

## Project layout

```
code/                         ← Poetry project root (run commands here)
  apm_assignment/
    paths.py                  shared paths, used by both part1 and part2
    part1/                    Part I — olympic transport OCEL simulation
      config.py               single source of truth for Part 1 constants
      generate_log.py         subtask d, d-i
      validate.py             subtask d-ii, d-iii
      flatten_discover.py     subtask d-iv, d-v
      discover_ocpn.py        subtask e
      dotted_chart.py         subtask d-vi
      queries.py              subtask f, g (Python equivalents)
      render_tables.py        subtask b (E2O/O2O tables)
    part2/                    Part II — GSLPN + git version-control OCEL
      q3_gslpn.py              GSLPN trace probabilities
      q5a_constraints.py       C1, C2, C3 checks
      q5b_conformance.py       Cameron conformance checking
  notebooks/                  01–06 mirror the Part 1 scripts above
data/                         generated log.sqlite + log.json + version_control.sqlite
models/                       .pnml + .svg outputs
figures/                      .png outputs (Part 1)
```

## Notes

- `r4pm` must be available on PyPI (or installed from source).  Verify before `poetry install`.
- OCPQ screenshots for subtasks (f) and (g) are generated manually at <https://ocpq.aarkue.eu/> by loading `data/log.sqlite`.
