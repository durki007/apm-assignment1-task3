"""
Validate the OCEL 2.0 log against assignment requirements R(i)–R(v) (subtasks d-ii, d-iii).

Run:  poetry run python -m apm_assignment.part1.validate
      # or:  poetry run validate
"""
import sys
import pandas as pd
import pm4py

from apm_assignment.part1.config import DATA_DIR


def _load():
    path = str(DATA_DIR / "log.sqlite")
    ocel = pm4py.read_ocel2_sqlite(path)
    return ocel


def _check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    line = f"  [{status}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)
    return passed


def run_checks(ocel) -> bool:
    print("\n=== Requirement validation ===\n")
    ok = True

    # R(i): ≥ 100 events
    n_events = len(ocel.events)
    ok &= _check("R(i)  ≥ 100 events", n_events >= 100, f"{n_events} events")

    # R(ii): ≥ 3 object types
    n_otypes = ocel.objects["ocel:type"].nunique()
    ok &= _check("R(ii) ≥ 3 object types", n_otypes >= 3, f"{n_otypes} types")

    # R(iii): ≥ 5 event types
    n_etypes = ocel.events["ocel:activity"].nunique()
    ok &= _check("R(iii) ≥ 5 event types", n_etypes >= 5, f"{n_etypes} types")

    # O2O relations
    if not hasattr(ocel, "o2o") or ocel.o2o is None or len(ocel.o2o) == 0:
        _check("R(v)  O2O table present", False, "ocel.o2o is empty")
        return False

    o2o = ocel.o2o.copy()
    # Normalise column names across PM4Py versions
    col_map = {}
    for c in o2o.columns:
        lc = c.lower()
        if "qualifier" in lc:
            col_map[c] = "qualifier"
        elif lc in ("ocel:oid", "ocel:oid_1", "source"):
            col_map[c] = "src"
        elif lc in ("ocel:oid_2", "ocel:oid2", "target"):
            col_map[c] = "tgt"
    o2o.rename(columns=col_map, inplace=True)

    holds     = o2o[o2o["qualifier"] == "holds"]
    belongs_to = o2o[o2o["qualifier"] == "belongs_to"]

    # R(v)a: Passenger ↔ TravelTicket bijection
    pax_ticket_counts = holds.groupby("src").size()
    ticket_pax_counts = holds.groupby("tgt").size()
    va_ok = bool(pax_ticket_counts.eq(1).all() and ticket_pax_counts.eq(1).all())
    ok &= _check(
        "R(v)a one-to-one (Passenger holds TravelTicket)",
        va_ok,
        f"{len(holds)} holds relations, "
        f"max per passenger={pax_ticket_counts.max()}, "
        f"max per ticket={ticket_pax_counts.max()}",
    )

    # R(v)b: Passenger many-to-one GroupBooking
    pax_group_counts  = belongs_to.groupby("src").size()
    group_pax_counts  = belongs_to.groupby("tgt").size()
    vb_single_group = bool(pax_group_counts.eq(1).all())
    vb_has_many     = bool((group_pax_counts > 1).any())
    ok &= _check(
        "R(v)b many-to-one (Passenger belongs_to GroupBooking) — each passenger has 1 group",
        vb_single_group,
        f"max groups per passenger={pax_group_counts.max()}",
    )
    ok &= _check(
        "R(v)b convergence — ≥1 group has >1 passenger",
        vb_has_many,
        f"max passengers per group={group_pax_counts.max()}",
    )

    print()
    print("=== Summary:", "ALL PASSED" if ok else "SOME CHECKS FAILED", "===")
    return ok


def main():
    ocel = _load()
    passed = run_checks(ocel)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
