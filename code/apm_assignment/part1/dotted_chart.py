"""
Synchronization dotted chart showing AssignToDeparture → Depart per Passenger (subtask d-vi).

Run:  poetry run python -m apm_assignment.part1.dotted_chart
      # or:  poetry run dotted
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pm4py

from apm_assignment.part1.config import DATA_DIR, FIGURES_DIR, ET_GROUP, ET_SYNC


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    ocel = pm4py.read_ocel2_sqlite(str(DATA_DIR / "log.sqlite"))

    # Join events with their related Passenger objects
    events = ocel.events.copy()
    relations = ocel.relations.copy()

    # Normalise column names
    act_col = next(c for c in events.columns if "activity" in c.lower())
    ts_col  = next(c for c in events.columns if "timestamp" in c.lower())
    eid_col = next(c for c in events.columns if c.lower() in ("ocel:eid", "event_id"))

    ot_col  = next((c for c in relations.columns if "type" in c.lower() and "object" in c.lower()), None)
    if ot_col is None:
        ot_col = next((c for c in relations.columns if c.lower() in ("ocel:type", "object_type")), "ocel:type")

    rel_eid_col = next(c for c in relations.columns if c.lower() in ("ocel:eid", "event_id"))
    rel_oid_col = next(c for c in relations.columns if c.lower() in ("ocel:oid", "object_id"))

    # Filter to synchronization events and Passenger objects
    sync_activities = [ET_GROUP, ET_SYNC]
    ev_sync = events[events[act_col].isin(sync_activities)][[eid_col, act_col, ts_col]]

    pax_rels = relations[
        (relations[ot_col] == "Passenger")
    ][[rel_eid_col, rel_oid_col]]

    merged = ev_sync.merge(pax_rels, left_on=eid_col, right_on=rel_eid_col)
    merged[ts_col] = pd.to_datetime(merged[ts_col], utc=True)

    # Determine departure order for each passenger from their Depart event
    depart_ts = merged[merged[act_col] == ET_SYNC].groupby(rel_oid_col)[ts_col].min()
    merged["dep_ts"] = merged[rel_oid_col].map(depart_ts)
    merged = merged.sort_values(["dep_ts", rel_oid_col])

    passengers_ordered = merged[rel_oid_col].unique().tolist()
    pax_idx = {p: i for i, p in enumerate(passengers_ordered)}

    # Plot
    fig, ax = plt.subplots(figsize=(12, max(6, len(passengers_ordered) * 0.25)))

    colors  = {ET_GROUP: "#2196F3", ET_SYNC: "#F44336"}
    markers = {ET_GROUP: "^", ET_SYNC: "o"}
    labels  = {ET_GROUP: "AssignToDeparture", ET_SYNC: "Depart"}

    for activity in sync_activities:
        subset = merged[merged[act_col] == activity]
        xs = subset[ts_col]
        ys = subset[rel_oid_col].map(pax_idx)
        ax.scatter(xs, ys,
                   c=colors[activity], marker=markers[activity],
                   label=labels[activity], s=40, alpha=0.85, zorder=3)

    ax.set_yticks(range(len(passengers_ordered)))
    ax.set_yticklabels(passengers_ordered, fontsize=6)
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Passenger")
    ax.set_title(
        "Synchronization dotted chart\n"
        "Each Depart event shares its exact Passenger set with the preceding AssignToDeparture"
    )
    ax.legend(loc="upper left")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()

    out_path = str(FIGURES_DIR / "dotted_chart_sync.png")
    fig.savefig(out_path, dpi=150)
    print(f"Saved figure → {out_path}")
    plt.close(fig)


if __name__ == "__main__":
    main()
