# Advanced Process Mining — Assignment Part I, Question 3
## Report Specification (LaTeX)

**Deliverable:** the Question 3 portion of `report.pdf`.
**Domain:** Public transport (ASEAG / Deutsche Bahn) — *2036 Olympic Games in Aachen.*
**Companion document:** `APM_Q3_specification.md` (the Python code spec). All design
names, figure filenames, and artifact paths referenced here are defined there and
must match exactly.

This document specifies *how the report is written*, not how the log is generated.
It defines the LaTeX toolchain, the source layout, the preamble, global formatting
conventions, and a per-subtask content contract (what prose, which figures, which
tables, the sentence budget, and the point weight).

> **Note on scope.** The full `report.pdf` must contain the written answers to
> Questions 1, 2, *and* 3. This spec covers the **Question 3 chapter**, designed so
> it can be `\input` into a master `main.tex` that also holds Q1 and Q2.

---

## 1. Authoring principles

1. **Every claim is backed by an artifact.** Each requirement statement (R i–viii)
   and each subtask answer points to a figure, table, or listing produced by the
   code. The report never asserts "the log satisfies R(v)" without showing the
   validation output.
2. **The report and the code share one vocabulary.** Object/event/attribute names
   come from `config.py`. Do not introduce names in prose that the log does not contain.
3. **Respect the assignment's length budgets.** Each subtask states an approximate
   sentence count. Treat these as ceilings, not targets — graders reward precise,
   on-point answers, not volume.
4. **Figures are self-explanatory and annotated.** Every figure has a caption that
   states what it shows and which requirement/subtask it serves, plus on-figure
   annotations where the assignment asks for them (c, d-vi, e).

---

## 2. LaTeX toolchain & build

### 2.1 Engine and build tool
- **Engine:** `pdfLaTeX` (sufficient; switch to `lualatex` only if you need system fonts).
- **Build tool:** `latexmk` (handles multiple passes and `cleveref`/`hyperref` references automatically).
- **Self-contained alternative:** `tectonic` (single binary, fetches packages on demand) if you want zero local TeX-distribution setup.

### 2.2 Build commands
```bash
# from report/
latexmk -pdf main.tex          # -> main.pdf
latexmk -c                     # clean aux files
# self-contained alternative:
tectonic main.tex              # -> main.pdf
```
Copy the resulting `main.pdf` to the archive root as `report.pdf`.

### 2.3 Code-listing backend
- **Default:** `listings` (dependency-free; no shell-escape).
- **Optional upgrade:** `minted` (nicer syntax highlighting, requires `-shell-escape` and Python `Pygments`). If used, build with `latexmk -pdf -shell-escape main.tex`.

### 2.4 Figure formats
- Prefer **PDF** for vector figures (Matplotlib: `savefig("...pdf")`; Graphviz: render to PDF) and **PNG** for raster screenshots (OCPQ).
- For the normative net `N1` drawn in draw.io/OCπ, export to **PDF** (`figures/N1_normative.pdf`).
- Avoid raw `.svg` in `\includegraphics` unless you add the `svg` package and have Inkscape on `PATH`; converting to PDF/PNG up front is simpler.

---

## 3. Report source structure

Keep the LaTeX source in a `report/` directory (sibling to `code/`); the built
`report.pdf` goes to the archive root.

```
report/
├── main.tex                 # master file: \input{preamble} + the Q1/Q2/Q3 chapters
├── preamble.tex             # documentclass, packages, macros (see §4)
├── latexmkrc                # optional build config
├── refs.bib                 # optional: OCEL 2.0, PM4Py, OCPQ, r4pm
├── sections/
│   ├── q3_00_intro.tex      # scenario + domain framing
│   ├── q3_a_design.tex      # (a)
│   ├── q3_b_relations.tex   # (b)
│   ├── q3_c_normative_net.tex   # (c)
│   ├── q3_d_log.tex         # (d) incl. d-i … d-vi
│   ├── q3_e_ocpn.tex        # (e)
│   ├── q3_f_queries.tex     # (f)
│   └── q3_g_custom_query.tex    # (g)
└── figures/                 # copies of the artifacts the report embeds
    ├── N1_normative.pdf
    ├── N_ot_oa.png
    ├── N_ot_sync.png
    ├── N2_ocpn.png
    ├── dotted_chart_sync.png
    ├── ocpq_f_i.png
    ├── ocpq_f_ii.png
    ├── ocpq_f_iii.png
    └── ocpq_g.png
```

> Keep `report/figures/` in sync with the project `figures/` and `models/` outputs.
> A small copy step (or symlink) at build time avoids drift.

---

## 4. Preamble specification

`preamble.tex` (reference):

```latex
\documentclass[11pt,a4paper]{article}

% --- encoding & fonts ---
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}

% --- layout ---
\usepackage[margin=2.5cm]{geometry}
\usepackage{microtype}

% --- math ---
\usepackage{amsmath,amssymb}

% --- figures & tables ---
\usepackage{graphicx}
\usepackage{float}          % [H] placement
\usepackage{booktabs}       % \toprule \midrule \bottomrule
\usepackage{tabularx}       % width-aware tables for E2O/O2O matrices
\usepackage{caption}
\usepackage{subcaption}     % side-by-side figures (e.g. N_ot_oa vs N_ot_sync)
\usepackage{xcolor}

% --- code listings ---
\usepackage{listings}
\lstset{
  basicstyle=\ttfamily\small,
  breaklines=true,
  frame=single,
  columns=fullflexible,
  showstringspaces=false
}

% --- references (load hyperref before cleveref) ---
\usepackage{hyperref}
\usepackage{cleveref}

% --- bibliography (optional) ---
% \usepackage[backend=biber,style=numeric]{biblatex}
% \addbibresource{refs.bib}

% --- project macros: single source of truth for entity names ---
\newcommand{\otPassenger}{\texttt{Passenger}}
\newcommand{\otTicket}{\texttt{TravelTicket}}
\newcommand{\otBooking}{\texttt{GroupBooking}}
\newcommand{\otDeparture}{\texttt{Departure}}
\newcommand{\etBooking}{\texttt{CreateGroupBooking}}
\newcommand{\etIssue}{\texttt{IssueTravelTicket}}
\newcommand{\etAssign}{\texttt{AssignToDeparture}}
\newcommand{\etBoard}{\texttt{BoardViaAccreditationLane}}
\newcommand{\etValidate}{\texttt{ValidateAtPublicGate}}
\newcommand{\etDepart}{\texttt{Depart}}
\newcommand{\etComplete}{\texttt{CompleteJourney}}
\newcommand{\attrFare}{\texttt{fare\_class}}
```

`main.tex` skeleton:

```latex
\input{preamble}
\title{Advanced Process Mining --- Assignment Part I}
\author{Group <GroupID> \\ <Member 1>, <Member 2>, <Member 3>}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

% \section{Question 1: Process Discovery}  \input{sections/q1_...}
% \section{Question 2: Conformance Checking} \input{sections/q2_...}

\section{Question 3: Object-Centric Simulation}
\input{sections/q3_00_intro}
\input{sections/q3_a_design}
\input{sections/q3_b_relations}
\input{sections/q3_c_normative_net}
\input{sections/q3_d_log}
\input{sections/q3_e_ocpn}
\input{sections/q3_f_queries}
\input{sections/q3_g_custom_query}

% \printbibliography   % if using biblatex
\end{document}
```

---

## 5. Global formatting conventions

| Element | Convention |
|---|---|
| Entity names in prose | Use the macros (`\otPassenger`, `\etDepart`, …) so names cannot drift from the code. |
| Figures | `\begin{figure}[H] … \includegraphics[width=...]{figures/<file>} … \caption{…}\label{fig:…}\end{figure}`. State the subtask and requirement in the caption. |
| Side-by-side nets | Use `subcaption` for `N_ot_oa` and `N_ot_sync`, or `N1` vs `N2`, to support direct comparison. |
| Tables | `booktabs` rules only (no vertical lines). E2O/O2O matrices use `tabularx` with an `X` first column. |
| Cross-references | Always `\cref{fig:…}`, `\cref{tab:…}`, `\cref{sec:…}` — never hard-coded numbers. |
| Code/console snippets | `lstlisting`; include only the *relevant* lines (e.g. the validation summary), not entire scripts. The full code lives in `code/`. |
| Requirement labels | Refer to requirements as R(i)…R(viii) consistently; bind each answer to the requirement it discharges. |
| Generated tables | Paste the Markdown emitted by `render_tables.py` converted to `booktabs`, or generate LaTeX directly. |

---

## 6. Section-by-section content contract

Point weights are from the assignment (Q3 total = 30). Sentence counts are the
assignment's stated budgets.

### `q3_00_intro.tex` — Scenario & domain framing *(no direct points; sets context)*
- 2–3 sentences: the assigned domain (public transport, ASEAG/DB) and the chosen
  process (group booking → ticketing → assignment → boarding → synchronized departure → completion) within the 2036 Aachen Olympics scenario.
- One sentence stating the OCEL 2.0 serialization submitted (`data/log.sqlite`).

### `q3_a_design.tex` — (a) Named entities + behavior **[4 pts]**
**Required content:**
- A short glossary, **~1 sentence per named entity**, covering:
  - 4 object types (`\otPassenger`, `\otTicket`, `\otBooking`, `\otDeparture`).
  - 7 event types (`\etBooking`, `\etIssue`, `\etAssign`, `\etBoard`, `\etValidate`, `\etDepart`, `\etComplete`).
  - 1 attribute `\attrFare` and its 2 values (`accredited`, `standard`).
- A **3–4 sentence** high-level description of process behavior (booking → ticketing → assignment → channel-dependent boarding → synchronized departure → completion).
**Format:** glossary best as three small `booktabs` tables (object types / event types / attribute), each with a one-line "meaning" column. Followed by the behavior paragraph.

### `q3_b_relations.tex` — (b) Type-level relations **[3 pts]**
**Required content:** the two matrices from the assignment schema, **1 sentence per non-empty cell**.
- **E2O table:** rows = event types, columns = object types; fill each related cell with a one-line relation description (e.g. *"records the passengers covered by the booking"*). Mirror §4.4 of the code spec.
- **O2O table:** rows/columns = object types; fill the `Passenger→TravelTicket` (`holds`, one-to-one) and `Passenger→GroupBooking` (`belongs_to`, many-to-one) cells.
**Format:** `tabularx` so wide matrices fit the text width. Source the content from `render_tables.py` to guarantee consistency with the generator.

### `q3_c_normative_net.tex` — (c) Normative OC Petri net N1 **[3 pts]**
**Required content:**
- Embed `figures/N1_normative.pdf` (annotated).
- **~4–5 sentences** explaining intended behavior by reference to transitions
  (the 7 event types), places, and arcs — including the variable (double) arcs for
  the convergent `\otPassenger` flow into `\etDepart`.
**Format:** one `figure[H]` + paragraph. Caption must name the model `$N_1$` and state it is the normative model.

### `q3_d_log.tex` — (d) Log generation & analysis **[total 10 pts across i–vi]**
A subsection per item. Bind each to its requirement.

- **(d-i) Submit L [1 pt].** One sentence stating `data/log.sqlite` (OCEL 2.0) is submitted; reference the serialization format.
- **(d-ii) R(i),(ii),(iii) satisfied [1 pt].** Paste the `validate.py` summary (event count, #object types, #event types) as an `lstlisting` or a small `booktabs` table; one sentence confirming each threshold (≥100, ≥3, ≥5).
- **(d-iii) R(v)a, R(v)b satisfied [1 pt].** Show the validation output proving the
  `holds` bijection (one-to-one) and the `belongs_to` many-to-one (with at least one
  booking covering >1 passenger). One sentence per relation.
- **(d-iv) Flatten to `ot_oa` + discover net [2 pts].** Embed `figures/N_ot_oa.png`
  (the net discovered on the `\otTicket`-flattened log). **~1 sentence** stating that
  the XOR split between `\etBoard` and `\etValidate` after `\etIssue` reflects the
  R(vii) data-driven choice on `\attrFare`.
- **(d-v) Flatten to `ot_sync` + discover net [2 pts].** Embed `figures/N_ot_sync.png`
  (the net on the `\otPassenger`-flattened log). **~1 sentence** stating that
  `\etAssign` directly preceding `\etDepart` reflects the R(viii-a) precedence constraint.
- **(d-vi) Synchronization visualization [3 pts].** Embed `figures/dotted_chart_sync.png`
  (annotated). **~2–3 sentences** interpreting that each `\etDepart` event features
  the same `\otPassenger` set as a preceding `\etAssign` event (R viii-a).
**Format suggestion:** put `N_ot_oa` and `N_ot_sync` side by side with `subcaption`.

### `q3_e_ocpn.tex` — (e) Discovered OCPN N2 **[3 pts]**
**Required content:**
- Embed `figures/N2_ocpn.png` (annotated).
- For each deviation of `$N_2$` from the normative `$N_1$`, **~1–2 sentences**
  explaining it — and frame remaining deviations as either acceptable (allowed but
  unplanned control flow) or as artifacts of the discovery algorithm (silent
  transitions, variant arcs, filtering).
**Format:** `figure[H]` + one short paragraph per deviation. Optionally a `subcaption` pairing `N_1` and `N_2`.

### `q3_f_queries.tex` — (f) OCPQ queries **[total 5 pts]**
For each query: state the concrete entity names and any threshold, embed the OCPQ
screenshot, and report the result (count + interpretation).
- **(f-i) [1 pt].** Pick `c = "accredited"`. *Find all `\otTicket` objects with `\attrFare` = c.* Embed `figures/ocpq_f_i.png`; state the result count.
- **(f-ii) [2 pts].** Extend f-i: `\otTicket` with `\attrFare` = c, related to **exactly one** `\etBoard` event, and **no** `\etValidate` event. Embed `figures/ocpq_f_ii.png`.
- **(f-iii) [2 pts].** Pick a threshold `k ≥ 1` (state it). *Find all `\otBooking` objects related via O2O to more than k `\otPassenger` objects.* Embed `figures/ocpq_f_iii.png`.
**Format:** a short subsection per query, each ending with one sentence interpreting the result. Optionally note that the same result sets are reproduced by `queries.py`.

### `q3_g_custom_query.tex` — (g) Custom business query **[2 pts]**
**Required content:**
- State the business question and **~1–2 sentences** explaining its purpose,
  referring to the concrete event/object types involved.
- Embed `figures/ocpq_g.png` (executed query) and report the result.
**Example:** *"Which `\etDepart` events carry more than N standard-fare passengers?"*
— useful for capacity planning of public-gate throughput vs. accreditation lanes.

---

## 7. Required-artifacts checklist

The report cannot be completed until these exist (all produced by the code in
`APM_Q3_specification.md`). Tick before submitting.

| Artifact | Subtask | Produced by | Embedded as |
|---|---|---|---|
| `data/log.sqlite` | d-i | `generate_log.py` | referenced (not embedded) |
| validation summary (counts, R v) | d-ii, d-iii | `validate.py` | `lstlisting` / table |
| `figures/N1_normative.pdf` | c | manual (draw.io/OCπ) | figure |
| `figures/N_ot_oa.png` | d-iv | `flatten_discover.py` | figure |
| `figures/N_ot_sync.png` | d-v | `flatten_discover.py` | figure |
| `figures/dotted_chart_sync.png` | d-vi | `dotted_chart.py` | figure |
| `figures/N2_ocpn.png` | e | `discover_ocpn.py` | figure |
| `figures/ocpq_f_i.png` … `ocpq_g.png` | f, g | OCPQ (GUI) | figures |
| E2O / O2O matrices | b | `render_tables.py` | tables |

---

## 8. Points-to-section map (prioritization)

| Section | Points |
|---|---|
| (a) Design | 4 |
| (b) Relations | 3 |
| (c) Normative net N1 | 3 |
| (d) Log generation & analysis (i–vi) | 10 |
| (e) Discovered OCPN N2 | 3 |
| (f) OCPQ queries (i–iii) | 5 |
| (g) Custom query | 2 |
| **Total** | **30** |

The single largest block is (d) at 10 points; it depends entirely on `data/log.sqlite`
existing, so the report's (d)–(g) sections cannot be written until the code pipeline
has run.

---

## 9. Submission notes

- The built PDF goes to the archive root as `report.pdf`; it must contain Q1, Q2,
  and Q3. This spec governs the Q3 chapter only.
- All figures referenced in the report must also be present as **separate files**
  in the archive's `figures/` directory (per the assignment's deliverable rules),
  not only embedded in the PDF.
- Keep entity names, thresholds (`c`, `k`, `N`), and figure filenames identical
  between the report, `config.py`, and the OCPQ screenshots.
- If you use `biblatex`, cite at minimum: the OCEL 2.0 standard, PM4Py, OCPQ, and
  r4pm; otherwise a short footnote with URLs is acceptable.