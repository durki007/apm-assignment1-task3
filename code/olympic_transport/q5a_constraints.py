"""
Q5a: Check constraints C1, C2, C3 on the version-control OCEL log.

Replaces OCPQ queries with equivalent Python logic.

Run:  poetry run python -m olympic_transport.q5a_constraints
      # or:  poetry run q5a

Constraints:
  C1  Pull before push; only a merge may appear between pull and push.
  C2  After committing to branch b, do not touch another branch until b is pushed.
  C3  A merge consuming two versions of the same file committed by different users
      is a coordination problem.
"""
import sqlite3
from pathlib import Path

import pandas as pd

from olympic_transport.config import DATA_DIR

DB_PATH = DATA_DIR / "version_control.sqlite"


# ── Data loading ────────────────────────────────────────────────────────────

def _load(db: Path = DB_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (events, event_object, object_object) DataFrames."""
    con = sqlite3.connect(str(db))

    # Union the four typed event tables to get a single events table with timestamps.
    events = pd.read_sql_query(
        """
        SELECT e.ocel_id  AS event_id,
               e.ocel_type AS activity,
               COALESCE(ec.ocel_time, em.ocel_time, ep.ocel_time, epu.ocel_time) AS ts
        FROM event e
        LEFT JOIN "event_Commit" ec  ON e.ocel_id = ec.ocel_id
        LEFT JOIN "event_Merge"  em  ON e.ocel_id = em.ocel_id
        LEFT JOIN "event_Pull"   ep  ON e.ocel_id = ep.ocel_id
        LEFT JOIN "event_Push"   epu ON e.ocel_id = epu.ocel_id
        ORDER BY ts
        """,
        con,
    )
    events["ts"] = pd.to_datetime(events["ts"])

    event_obj = pd.read_sql_query(
        """
        SELECT eo.ocel_event_id  AS event_id,
               eo.ocel_object_id AS object_id,
               eo.ocel_qualifier AS qualifier,
               o.ocel_type       AS object_type
        FROM event_object eo
        JOIN object o ON eo.ocel_object_id = o.ocel_id
        """,
        con,
    )

    obj_obj = pd.read_sql_query(
        "SELECT ocel_source_id AS src, ocel_target_id AS tgt, ocel_qualifier AS qualifier "
        "FROM object_object",
        con,
    )

    con.close()
    return events, event_obj, obj_obj


def _event_context(events: pd.DataFrame, event_obj: pd.DataFrame) -> pd.DataFrame:
    """Return a flat table: event_id, activity, ts, user, branch (one row per event×branch)."""
    users = (
        event_obj[event_obj["object_type"] == "users"]
        [["event_id", "object_id"]]
        .rename(columns={"object_id": "user"})
    )
    branches = (
        event_obj[event_obj["object_type"] == "branches"]
        [["event_id", "object_id"]]
        .rename(columns={"object_id": "branch"})
    )
    ctx = (
        events
        .merge(users, on="event_id", how="left")
        .merge(branches, on="event_id", how="left")
        .sort_values("ts")
        .reset_index(drop=True)
    )
    return ctx


# ── C1 ──────────────────────────────────────────────────────────────────────

def check_c1(ctx: pd.DataFrame) -> pd.DataFrame:
    """
    C1: For each (user, branch) pair, every push must be immediately preceded
    (in that pair's event sequence) by a pull or a merge, and the most recent
    pull must be the event two steps back at most (pull → [merge] → push).

    Violation when:
      - A push has no preceding pull on the same (user, branch), OR
      - Between the most-recent pull and the push there is a non-merge event.
    """
    violations = []

    for (user, branch), grp in ctx.dropna(subset=["branch"]).groupby(["user", "branch"]):
        seq = grp.reset_index(drop=True)

        for idx, row in seq.iterrows():
            if row["activity"] != "push":
                continue

            before = seq[seq.index < idx]
            pull_idx = before.index[before["activity"] == "pull"]

            if len(pull_idx) == 0:
                violations.append(
                    dict(user=user, branch=branch, push_event=row["event_id"],
                         reason="push with no preceding pull")
                )
                continue

            last_pull = pull_idx[-1]
            between = seq[(seq.index > last_pull) & (seq.index < idx)]
            bad = between[between["activity"] != "merge"]

            if len(bad) > 0:
                violations.append(
                    dict(user=user, branch=branch, push_event=row["event_id"],
                         reason=f"non-merge event(s) between pull and push: "
                                f"{bad['activity'].tolist()} (events {bad['event_id'].tolist()})")
                )

    return pd.DataFrame(violations) if violations else pd.DataFrame(
        columns=["user", "branch", "push_event", "reason"]
    )


# ── C2 ──────────────────────────────────────────────────────────────────────

def check_c2(ctx: pd.DataFrame) -> pd.DataFrame:
    """
    C2: After a commit to branch b, any event on a different branch is a
    violation until a push to b clears the constraint.

    The 'active branch' is set on the first commit not yet resolved by a push.
    """
    violations = []

    for user, grp in ctx.dropna(subset=["branch"]).groupby("user"):
        seq = grp.sort_values("ts").reset_index(drop=True)
        active: str | None = None   # branch committed to but not yet pushed

        for _, row in seq.iterrows():
            if row["activity"] == "commit":
                if active is None:
                    active = row["branch"]
                elif row["branch"] != active:
                    violations.append(
                        dict(user=user, event_id=row["event_id"],
                             active_branch=active, touched_branch=row["branch"],
                             activity=row["activity"],
                             reason=f"committed to {row['branch']} while {active} not yet pushed")
                    )
            elif row["activity"] == "push" and active is not None and row["branch"] == active:
                active = None   # constraint resolved
            elif active is not None and row["branch"] != active:
                violations.append(
                    dict(user=user, event_id=row["event_id"],
                         active_branch=active, touched_branch=row["branch"],
                         activity=row["activity"],
                         reason=f"{row['activity']} on {row['branch']} while {active} not yet pushed")
                )

    return pd.DataFrame(violations) if violations else pd.DataFrame(
        columns=["user", "event_id", "active_branch", "touched_branch", "activity", "reason"]
    )


# ── C3 ──────────────────────────────────────────────────────────────────────

def check_c3(
    events: pd.DataFrame,
    event_obj: pd.DataFrame,
    obj_obj: pd.DataFrame,
) -> pd.DataFrame:
    """
    C3: A merge event is a coordination problem when it consumes two file-version
    objects that (a) version the same file and (b) were produced (committed) by
    different users.
    """
    # version → file mapping (is_a)
    is_a = obj_obj[obj_obj["qualifier"] == "is_a"][["src", "tgt"]].rename(
        columns={"src": "version_id", "tgt": "file_id"}
    )

    # version → (commit event, user)
    produce = event_obj[event_obj["qualifier"] == "produce"][["event_id", "object_id"]].rename(
        columns={"object_id": "version_id"}
    )
    commit_ids = events[events["activity"] == "commit"]["event_id"]
    produce_commits = produce[produce["event_id"].isin(commit_ids)]

    users_of = (
        event_obj[event_obj["object_type"] == "users"]
        [["event_id", "object_id"]]
        .rename(columns={"object_id": "user"})
    )
    version_user = (
        produce_commits
        .merge(users_of, on="event_id")
        [["version_id", "user"]]
        .drop_duplicates("version_id")
    )

    # merge events and their consumed file-versions
    merge_eids = events[events["activity"] == "merge"]["event_id"]
    consumed = event_obj[
        event_obj["event_id"].isin(merge_eids) &
        (event_obj["qualifier"] == "consume") &
        (event_obj["object_type"] == "file versions")
    ][["event_id", "object_id"]].rename(columns={"object_id": "version_id"})

    consumed = consumed.merge(is_a, on="version_id", how="left")
    consumed = consumed.merge(version_user, on="version_id", how="left")

    violations = []
    for (merge_eid, file_id), grp in consumed.dropna(subset=["file_id"]).groupby(
        ["event_id", "file_id"]
    ):
        users = grp["user"].dropna().unique()
        if len(users) >= 2:
            violations.append(
                dict(merge_event=merge_eid, file=file_id,
                     versions=grp["version_id"].tolist(),
                     users=sorted(users),
                     reason=f"versions of {file_id} committed by {sorted(users)}")
            )

    return pd.DataFrame(violations) if violations else pd.DataFrame(
        columns=["merge_event", "file", "versions", "users", "reason"]
    )


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Loading log from {DB_PATH} …")
    events, event_obj, obj_obj = _load()
    ctx = _event_context(events, event_obj)

    print(f"  {len(events)} events, "
          f"{events['activity'].value_counts().to_dict()}")

    # ── C1 ──
    print("\n=== C1: pull before push; only merge between pull and push ===")
    v1 = check_c1(ctx)
    if v1.empty:
        print("  No violations.")
    else:
        print(f"  {len(v1)} violation(s):")
        print(v1.to_string(index=False))

    # ── C2 ──
    print("\n=== C2: no branch-switching after commit until push ===")
    v2 = check_c2(ctx)
    if v2.empty:
        print("  No violations.")
    else:
        print(f"  {len(v2)} violation(s):")
        print(v2.to_string(index=False))

    # ── C3 ──
    print("\n=== C3: coordination problems (merge of same-file versions by different users) ===")
    v3 = check_c3(events, event_obj, obj_obj)
    if v3.empty:
        print("  No coordination problems found.")
    else:
        print(f"  {len(v3)} coordination problem(s):")
        print(v3.to_string(index=False))


if __name__ == "__main__":
    main()
