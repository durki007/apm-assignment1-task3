"""
Python equivalents of the OCPQ queries (subtasks f-i, f-ii, f-iii, g).

These verify the logic before/after building the OCPQ node trees.
OCPQ screenshots remain the submitted artifact.

Run:  poetry run python -m olympic_transport.queries
      # or:  poetry run queries
"""
import pandas as pd
import pm4py

from olympic_transport.config import DATA_DIR, OA_NAME, ET_X1, ET_X2

# Query parameters
C = "accredited"   # (f-i, f-ii) fare_class value of interest
K = 2              # (f-iii) group size threshold


def _load():
    ocel = pm4py.read_ocel2_sqlite(str(DATA_DIR / "log.sqlite"))
    return ocel


def _get_ticket_attributes(ocel) -> pd.DataFrame:
    """Return DataFrame with columns [oid, fare_class] for TravelTicket objects."""
    objs = ocel.objects
    type_col = next(c for c in objs.columns if "type" in c.lower())
    oid_col  = next(c for c in objs.columns if c.lower() in ("ocel:oid", "object_id", "oid"))

    tickets = objs[objs[type_col] == "TravelTicket"].copy()

    # Object attributes may be in a separate table or as extra columns
    fare_col = None
    for c in tickets.columns:
        if OA_NAME in c.lower():
            fare_col = c
            break

    if fare_col is None and hasattr(ocel, "object_changes"):
        # PM4Py stores attribute history in object_changes
        oc = ocel.object_changes.copy()
        oc_oid = next(c for c in oc.columns if "oid" in c.lower())
        oc_attr = next((c for c in oc.columns if "attr" in c.lower() or "name" in c.lower()), None)
        oc_val  = next((c for c in oc.columns if "value" in c.lower()), None)
        if oc_attr and oc_val:
            fare_data = oc[oc[oc_attr] == OA_NAME][[oc_oid, oc_val]].drop_duplicates(oc_oid)
            fare_data = fare_data.rename(columns={oc_oid: "oid", oc_val: "fare_class"})
            return fare_data

    if fare_col:
        result = tickets[[oid_col, fare_col]].rename(columns={oid_col: "oid", fare_col: "fare_class"})
    else:
        # Fallback: try ocel.object_attribute_values or similar
        result = tickets[[oid_col]].rename(columns={oid_col: "oid"})
        result["fare_class"] = None

    return result.reset_index(drop=True)


def _get_ticket_events(ocel) -> pd.DataFrame:
    """Return DataFrame [ticket_oid, activity] for boarding-related events."""
    rels = ocel.relations.copy()
    evts = ocel.events.copy()

    act_col     = next(c for c in evts.columns if "activity" in c.lower())
    eid_col     = next(c for c in evts.columns if c.lower() in ("ocel:eid", "event_id"))
    rel_eid_col = next(c for c in rels.columns if c.lower() in ("ocel:eid", "event_id"))
    rel_oid_col = next(c for c in rels.columns if c.lower() in ("ocel:oid", "object_id"))
    ot_col      = next(
        (c for c in rels.columns if "type" in c.lower() and "object" in c.lower()),
        next((c for c in rels.columns if c.lower() in ("ocel:type", "object_type")), None),
    )

    boarding = [ET_X1, ET_X2]
    ev_board = evts[evts[act_col].isin(boarding)][[eid_col, act_col]]

    if ot_col:
        ticket_rels = rels[rels[ot_col] == "TravelTicket"][[rel_eid_col, rel_oid_col]]
    else:
        ticket_rels = rels[[rel_eid_col, rel_oid_col]]

    merged = ticket_rels.merge(ev_board, left_on=rel_eid_col, right_on=eid_col)
    return merged[[rel_oid_col, act_col]].rename(columns={rel_oid_col: "oid", act_col: "activity"})


def _get_o2o_belongs_to(ocel) -> pd.DataFrame:
    """Return DataFrame [passenger_oid, group_oid] for belongs_to O2O relations."""
    o2o = ocel.o2o.copy()
    q_col  = next(c for c in o2o.columns if "qualifier" in c.lower())
    src_col = next(c for c in o2o.columns if c.lower() in ("ocel:oid", "ocel:oid_1", "src", "source"))
    tgt_col = next(c for c in o2o.columns if c.lower() in ("ocel:oid_2", "ocel:oid2", "tgt", "target") and c != src_col)

    bt = o2o[o2o[q_col] == "belongs_to"][[src_col, tgt_col]]
    return bt.rename(columns={src_col: "passenger_oid", tgt_col: "group_oid"}).reset_index(drop=True)


# ── Queries ────────────────────────────────────────────────────────────────

def query_fi(ocel) -> pd.DataFrame:
    """f-i: All TravelTicket objects with fare_class == C."""
    tickets = _get_ticket_attributes(ocel)
    result = tickets[tickets["fare_class"] == C][["oid"]].reset_index(drop=True)
    return result


def query_fii(ocel) -> pd.DataFrame:
    """f-ii: TravelTickets where fare_class == C, related to exactly 1 BoardViaAccreditationLane
    and 0 ValidateAtPublicGate events."""
    tickets = _get_ticket_attributes(ocel)
    ticket_events = _get_ticket_events(ocel)

    board_counts = (
        ticket_events[ticket_events["activity"] == ET_X1]
        .groupby("oid").size().rename("n_board")
    )
    validate_counts = (
        ticket_events[ticket_events["activity"] == ET_X2]
        .groupby("oid").size().rename("n_validate")
    )

    base = tickets[tickets["fare_class"] == C][["oid"]].set_index("oid")
    base = base.join(board_counts, how="left").join(validate_counts, how="left")
    base = base.fillna(0)

    result = base[(base["n_board"] == 1) & (base["n_validate"] == 0)].reset_index()
    return result[["oid"]]


def query_fiii(ocel, k: int = K) -> pd.DataFrame:
    """f-iii: All GroupBooking objects related (via belongs_to) to more than k Passengers."""
    belongs = _get_o2o_belongs_to(ocel)
    group_counts = belongs.groupby("group_oid").size().rename("n_passengers").reset_index()
    result = group_counts[group_counts["n_passengers"] > k]
    return result.reset_index(drop=True)


def query_g(ocel) -> pd.DataFrame:
    """g: Which Depart events carry more than 2 standard-fare passengers?

    Business value: dispatchers can flag large standard-fare batches for
    extra gate staff, since standard passengers use the public validation
    lane which can create queues.
    """
    rels  = ocel.relations.copy()
    evts  = ocel.events.copy()
    tickets = _get_ticket_attributes(ocel)

    act_col     = next(c for c in evts.columns if "activity" in c.lower())
    eid_col     = next(c for c in evts.columns if c.lower() in ("ocel:eid", "event_id"))
    rel_eid_col = next(c for c in rels.columns if c.lower() in ("ocel:eid", "event_id"))
    rel_oid_col = next(c for c in rels.columns if c.lower() in ("ocel:oid", "object_id"))
    ot_col      = next(
        (c for c in rels.columns if "type" in c.lower() and "object" in c.lower()),
        next((c for c in rels.columns if c.lower() in ("ocel:type", "object_type")), None),
    )

    # Depart events
    depart_eids = evts[evts[act_col] == "Depart"][[eid_col]]

    # Passengers in each Depart event
    if ot_col:
        pax_rels = rels[rels[ot_col] == "Passenger"][[rel_eid_col, rel_oid_col]]
    else:
        pax_rels = rels[[rel_eid_col, rel_oid_col]]

    dep_pax = depart_eids.merge(pax_rels, left_on=eid_col, right_on=rel_eid_col)
    dep_pax = dep_pax.rename(columns={rel_oid_col: "passenger_oid"})

    # Ticket fare for each passenger via O2O holds
    o2o = ocel.o2o.copy()
    q_col   = next(c for c in o2o.columns if "qualifier" in c.lower())
    src_col = next(c for c in o2o.columns if c.lower() in ("ocel:oid", "ocel:oid_1", "src", "source"))
    tgt_col = next(c for c in o2o.columns if c.lower() in ("ocel:oid_2", "ocel:oid2", "tgt", "target") and c != src_col)

    holds = o2o[o2o[q_col] == "holds"][[src_col, tgt_col]].rename(
        columns={src_col: "passenger_oid", tgt_col: "ticket_oid"}
    )
    ticket_fare = tickets.rename(columns={"oid": "ticket_oid"})

    dep_pax = dep_pax.merge(holds, on="passenger_oid", how="left")
    dep_pax = dep_pax.merge(ticket_fare, on="ticket_oid", how="left")

    standard_counts = (
        dep_pax[dep_pax["fare_class"] == "standard"]
        .groupby(eid_col).size().rename("n_standard")
    )

    result = standard_counts[standard_counts > 2].reset_index()
    result.columns = ["depart_eid", "n_standard_passengers"]
    return result


# ── main ───────────────────────────────────────────────────────────────────

def main():
    ocel = _load()

    print(f"\n=== (f-i) TravelTickets with fare_class == '{C}' ===")
    r1 = query_fi(ocel)
    print(r1.to_string(index=False))
    print(f"  Count: {len(r1)}")

    print(f"\n=== (f-ii) TravelTickets fare_class=='{C}', 1× Board, 0× Validate ===")
    r2 = query_fii(ocel)
    print(r2.to_string(index=False))
    print(f"  Count: {len(r2)}")

    print(f"\n=== (f-iii) GroupBookings with > {K} Passengers ===")
    r3 = query_fiii(ocel)
    print(r3.to_string(index=False))
    print(f"  Count: {len(r3)}")

    print("\n=== (g) Depart events with > 2 standard-fare passengers ===")
    r4 = query_g(ocel)
    print(r4.to_string(index=False))
    print(f"  Count: {len(r4)}")


if __name__ == "__main__":
    main()
