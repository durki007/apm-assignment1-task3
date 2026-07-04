"""
Build and export the OCEL 2.0 log using r4pm (subtask d, d-i).

Run:  poetry run python -m olympic_transport.generate_log
      # or:  poetry run generate
"""
import random
from datetime import datetime, timedelta

import r4pm
import r4pm.bindings as b
from r4pm.bindings.bindings.slim_ocel_bindings import OCELTypeAttribute

from olympic_transport.config import (
    DATA_DIR, SEED,
    OBJECT_TYPES, EVENT_TYPES,
    FARE_CLASSES, CROSSOVER_PROB, OA_NAME,
    N_BOOKINGS, PASSENGERS_PER_BOOKING_RANGE, N_DEPARTURES,
    ET_X1, ET_X2,
)


# ── helpers ────────────────────────────────────────────────────────────────

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_population(rng: random.Random):
    """Return groups, passengers, tickets, departure→passengers mapping."""
    groups = [f"GB_{i:03d}" for i in range(N_BOOKINGS)]

    passengers: list[tuple[str, str, str]] = []  # (pid, fare_class, gid)
    for gid in groups:
        n = rng.randint(*PASSENGERS_PER_BOOKING_RANGE)
        for _ in range(n):
            pid = f"P_{len(passengers):04d}"
            fare = rng.choice(FARE_CLASSES)
            passengers.append((pid, fare, gid))

    tickets = [(f"T_{i:04d}", p[1]) for i, p in enumerate(passengers)]
    passenger_ticket = {p[0]: t[0] for p, t in zip(passengers, tickets)}

    # Assign passengers to departures (round-robin after shuffle)
    departures = [f"D_{i:03d}" for i in range(N_DEPARTURES)]
    pax_ids = [p[0] for p in passengers]
    rng.shuffle(pax_ids)
    dep_passengers: dict[str, list[str]] = {d: [] for d in departures}
    for i, pid in enumerate(pax_ids):
        dep_passengers[departures[i % N_DEPARTURES]].append(pid)

    return groups, passengers, tickets, passenger_ticket, departures, dep_passengers


def _build_timestamps(rng: random.Random, groups, passengers, departures, dep_passengers):
    """Return all timestamp dicts needed by the generator."""
    BASE = datetime(2036, 7, 15, 8, 0, 0)
    DEP_BASE = datetime(2036, 7, 15, 14, 0, 0)

    group_time   = {gid: BASE + timedelta(minutes=10 * i) for i, gid in enumerate(groups)}
    ticket_time  = {p[0]: group_time[p[2]] + timedelta(minutes=5) for p in passengers}
    dep_time     = {did: DEP_BASE + timedelta(minutes=30 * i) for i, did in enumerate(departures)}
    assign_time  = {did: dep_time[did] - timedelta(minutes=15) for did in departures}

    board_time: dict[str, datetime] = {}
    for did in departures:
        for j, pid in enumerate(dep_passengers[did]):
            board_time[pid] = dep_time[did] - timedelta(minutes=10) + timedelta(minutes=j)

    complete_time: dict[str, datetime] = {}
    for did in departures:
        for pid in dep_passengers[did]:
            complete_time[pid] = dep_time[did] + timedelta(minutes=rng.randint(60, 90))

    return group_time, ticket_time, dep_time, assign_time, board_time, complete_time


# ── main builder ───────────────────────────────────────────────────────────

def build_locel():
    rng = random.Random(SEED)
    locel = b.locel_new()

    # ── 1. Declare types ──────────────────────────────────────────────────
    for et in EVENT_TYPES:
        b.locel_add_event_type(locel, et, [])

    for ot in OBJECT_TYPES:
        attrs: list[OCELTypeAttribute] = [{"name": OA_NAME, "type": "string"}] if ot == "TravelTicket" else []
        b.locel_add_object_type(locel, ot, attrs)

    # ── 2. Generate population & timestamps ───────────────────────────────
    (groups, passengers, tickets,
     passenger_ticket, departures, dep_passengers) = _build_population(rng)

    (group_time, ticket_time, dep_time,
     assign_time, board_time, complete_time) = _build_timestamps(
        rng, groups, passengers, departures, dep_passengers)

    passenger_fare  = {p[0]: p[1] for p in passengers}
    passenger_group = {p[0]: p[2] for p in passengers}

    group_passengers: dict[str, list[str]] = {}
    for pid, _, gid in passengers:
        group_passengers.setdefault(gid, []).append(pid)

    # ── 3. Add objects (all before any relationship) ──────────────────────
    for gid in groups:
        b.locel_add_object(locel, "GroupBooking", gid)

    for did in departures:
        b.locel_add_object(locel, "Departure", did)

    for pid, _, _ in passengers:
        b.locel_add_object(locel, "Passenger", pid)

    for tid, fare in tickets:
        history = [[("1970-01-01T00:00:00Z", fare)]]
        b.locel_add_object(locel, "TravelTicket", tid, history)

    # ── 4. Add events ─────────────────────────────────────────────────────
    _eid = [0]
    def next_eid():
        _eid[0] += 1
        return f"E_{_eid[0]:04d}"

    cb_eids: dict[str, str]          = {}   # gid -> eid
    it_eids: dict[str, str]          = {}   # pid -> eid
    atd_eids: dict[str, str]         = {}   # did -> eid
    board_eids: dict[str, tuple]     = {}   # pid -> (eid, activity)
    depart_eids: dict[str, str]      = {}   # did -> eid
    cj_eids: dict[str, str]          = {}   # pid -> eid

    for gid in groups:
        eid = next_eid()
        cb_eids[gid] = eid
        b.locel_add_event(locel, "CreateGroupBooking", _iso(group_time[gid]), eid, [])

    for pid, _, _ in passengers:
        eid = next_eid()
        it_eids[pid] = eid
        b.locel_add_event(locel, "IssueTravelTicket", _iso(ticket_time[pid]), eid, [])

    for did in departures:
        eid = next_eid()
        atd_eids[did] = eid
        b.locel_add_event(locel, "AssignToDeparture", _iso(assign_time[did]), eid, [])

    for pid, fare, _ in passengers:
        eid = next_eid()
        if fare == "accredited":
            activity = ET_X1 if rng.random() > CROSSOVER_PROB else ET_X2
        else:
            activity = ET_X2 if rng.random() > CROSSOVER_PROB else ET_X1
        board_eids[pid] = (eid, activity)
        b.locel_add_event(locel, activity, _iso(board_time[pid]), eid, [])

    for did in departures:
        eid = next_eid()
        depart_eids[did] = eid
        b.locel_add_event(locel, "Depart", _iso(dep_time[did]), eid, [])

    for pid, _, _ in passengers:
        eid = next_eid()
        cj_eids[pid] = eid
        b.locel_add_event(locel, "CompleteJourney", _iso(complete_time[pid]), eid, [])

    # ── 5. Add E2O relations ──────────────────────────────────────────────
    def ev(eid): return b.locel_get_ev_by_id(locel, eid)
    def ob(oid): return b.locel_get_ob_by_id(locel, oid)

    # CreateGroupBooking -> GroupBooking + all Passengers in group
    for gid in groups:
        e = ev(cb_eids[gid])
        b.locel_add_e2o(locel, e, ob(gid), "")
        for pid in group_passengers.get(gid, []):
            b.locel_add_e2o(locel, e, ob(pid), "")

    # IssueTravelTicket -> Passenger + TravelTicket
    for pid, _, _ in passengers:
        e = ev(it_eids[pid])
        b.locel_add_e2o(locel, e, ob(pid), "")
        b.locel_add_e2o(locel, e, ob(passenger_ticket[pid]), "")

    # AssignToDeparture -> Departure + all Passengers in batch
    for did in departures:
        e = ev(atd_eids[did])
        b.locel_add_e2o(locel, e, ob(did), "")
        for pid in dep_passengers[did]:
            b.locel_add_e2o(locel, e, ob(pid), "")

    # Boarding -> Passenger + TravelTicket
    for pid, _, _ in passengers:
        eid, _ = board_eids[pid]
        e = ev(eid)
        b.locel_add_e2o(locel, e, ob(pid), "")
        b.locel_add_e2o(locel, e, ob(passenger_ticket[pid]), "")

    # Depart -> Departure + all Passengers in batch (same set as AssignToDeparture)
    for did in departures:
        e = ev(depart_eids[did])
        b.locel_add_e2o(locel, e, ob(did), "")
        for pid in dep_passengers[did]:
            b.locel_add_e2o(locel, e, ob(pid), "")

    # CompleteJourney -> Passenger
    for pid, _, _ in passengers:
        e = ev(cj_eids[pid])
        b.locel_add_e2o(locel, e, ob(pid), "")

    # ── 6. Add O2O relations ──────────────────────────────────────────────
    for pid, _, _ in passengers:
        b.locel_add_o2o(locel, ob(pid), ob(passenger_ticket[pid]), "holds")
        b.locel_add_o2o(locel, ob(pid), ob(passenger_group[pid]), "belongs_to")

    return locel


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    locel = build_locel()
    sqlite_path = str(DATA_DIR / "log.sqlite")
    json_path   = str(DATA_DIR / "log.json")
    r4pm.export_item(locel, sqlite_path)
    r4pm.export_item(locel, json_path)
    print(f"Exported → {sqlite_path}")
    print(f"Exported → {json_path}")


if __name__ == "__main__":
    main()
