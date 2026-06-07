# Olympic Transport OCEL — APM Assignment Part I, Q3

## Setup

```bash
# Install Poetry >= 1.8, then:
cd code
poetry install
```

**System requirement:** [Graphviz](https://graphviz.org/download/) must be installed and `dot` must be on `PATH`.

## Run pipeline (in order)

```bash
poetry run generate          # → data/log.sqlite + data/log.json
poetry run validate          # R(i),(ii),(iii),(v) checks
poetry run discover          # N_ot_oa, N_ot_sync  → models/ + figures/
poetry run ocpn              # N2                  → figures/
poetry run dotted            # dotted chart        → figures/
poetry run queries           # OCPQ equivalents
poetry run jupyter lab       # interactive notebooks
```

## Project layout

```
code/                         ← Poetry project root (run commands here)
  olympic_transport/
    config.py                 single source of truth for all constants
    generate_log.py           subtask d, d-i
    validate.py               subtask d-ii, d-iii
    flatten_discover.py       subtask d-iv, d-v
    discover_ocpn.py          subtask e
    dotted_chart.py           subtask d-vi
    queries.py                subtask f, g (Python equivalents)
    render_tables.py          subtask b (E2O/O2O tables)
  notebooks/                  01–06 mirror the scripts above
data/                         generated log.sqlite + log.json
models/                       .pnml + .svg outputs
figures/                      .png outputs
```

## Notes

- `r4pm` must be available on PyPI (or installed from source).  Verify before `poetry install`.
- OCPQ screenshots for subtasks (f) and (g) are generated manually at <https://ocpq.aarkue.eu/> by loading `data/log.sqlite`.
