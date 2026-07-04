"""
Q5b: Flattening-based conformance checking of L^Cameron_1 against OCPN N1.

Run:  poetry run python -m olympic_transport.q5b_conformance
      # or:  poetry run q5b

Steps:
  1. Load L = version_control.sqlite.
  2. Build L1 = view on {branches, users} only.
  3. Build L^Cameron_1 = L1 filtered to Cameron's events, then clean up.
  4. Flatten per object type -> one DataFrame trace per branch / one for Cameron.
  5. Print flattened traces (copy into q5b_conformance.tex tables).
  6. Define N1 subnets (branches and users).
  7. Token-based replay -> fitness.
  8. Alignment-based precision.
  9. Print aggregated results.

Items that still need manual work in the report:
  - N1 figure (screenshot from assignment PDF p.9 -> report2/figures/N1_ocpn.png).
  - Token-replay and alignment tables (copy from this script's output).
  - Prefix automata figures (draw or export from ProM).
  - C1/C2 interpretation paragraphs.
"""

import pandas as pd
import pm4py
from pm4py.objects.ocel.obj import OCEL
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils

from olympic_transport.config import DATA_DIR, ROOT_DIR

DB_PATH = DATA_DIR / "version_control.sqlite"
CAMERON = "Cameron"
FIGURES2_DIR = ROOT_DIR / "report2" / "figures"


# ── helpers ──────────────────────────────────────────────────────────────────


def _place(net: PetriNet, name: str) -> PetriNet.Place:
    p = PetriNet.Place(name)
    net.places.add(p)
    return p


def _trans(net: PetriNet, label, name=None) -> PetriNet.Transition:
    t = PetriNet.Transition(name or label, label)
    net.transitions.add(t)
    return t


def _arc(net, src, tgt):
    petri_utils.add_arc_from_to(src, tgt, net)


def _df_to_log(df: pd.DataFrame) -> pm4py.objects.log.obj.EventLog:
    """Convert a flattened OCEL DataFrame to a PM4Py EventLog."""
    formatted = pm4py.format_dataframe(
        df,
        case_id="case:concept:name",
        activity_key="concept:name",
        timestamp_key="time:timestamp",
    )
    return pm4py.convert_to_event_log(formatted)


# ── Step 1: load ─────────────────────────────────────────────────────────────


def load_ocel() -> pm4py.OCEL:
    return pm4py.read_ocel2_sqlite(str(DB_PATH))


# ── Steps 2 & 3: filter to L^Cameron_1 ──────────────────────────────────────


def build_cameron_l1(ocel: pm4py.OCEL) -> OCEL:
    """
    L^Cameron_1:
      - restrict to object types {branches, users}  (L1)
      - keep only events where Cameron is involved
      - drop objects that no longer appear in any event
    """
    rel = ocel.relations

    keep_types = {"branches", "users"}

    # Events where Cameron is directly involved
    cam_eids = rel[rel["ocel:oid"] == CAMERON]["ocel:eid"].unique()

    # Relations filtered to Cameron's events + kept object types
    rel_c = rel[
        rel["ocel:eid"].isin(cam_eids) & rel["ocel:type"].isin(keep_types)
    ].copy()

    events_c = ocel.events[ocel.events["ocel:eid"].isin(cam_eids)].copy()
    objects_c = ocel.objects[
        ocel.objects["ocel:oid"].isin(rel_c["ocel:oid"].unique())
    ].copy()

    return OCEL(events=events_c, objects=objects_c, relations=rel_c)


# ── Step 4: flatten ──────────────────────────────────────────────────────────


def flatten_log(ocel_c: OCEL, object_type: str) -> pd.DataFrame:
    return pm4py.ocel_flattening(ocel_c, object_type)


# ── Step 5: print traces ─────────────────────────────────────────────────────


def print_traces(df: pd.DataFrame, label: str) -> None:
    print(f"\n  Flattened traces -- {label}")
    print(f"  {'Case':<20} Trace")
    print(f"  {'-' * 20} {'-' * 50}")
    for case_id, grp in df.groupby("case:concept:name", sort=False):
        acts = " -> ".join(grp["concept:name"].tolist())
        print(f"  {str(case_id):<20} {acts}")


# ── Step 6: N1 subnets ───────────────────────────────────────────────────────
#
# N1 (assignment PDF, p.9) models commit(+) -> pull -> [merge?] -> push, loop.
#
# Subnet structure (same for branches and users):
#
#   p_start -[commit]-> p1 -[pull]-> p2 -[merge]-> p3 -[push]-> p_start (loop)
#                                     \--[tau_skip]--/
#
# Initial marking:  p_start = 1
# Final marking:    p_start = 1  (token returns here after each push)
#
# Multiple commits before pull:  modelled by a self-loop on p1 via [commit].
# Because Petri nets require a separate place per arc, this is implemented as:
#   p1 -[commit_more]-> p_extra -[tau_back]-> p1
# which allows any number of additional commits after the first.


def build_n1_subnet(name: str) -> tuple:
    net = PetriNet(name)

    p_start = _place(net, "p_start")
    p_end = _place(net, "p_end")
    p_1 = _place(net, "p1")
    p_2 = _place(net, "p2")
    p_3 = _place(net, "p3")
    p_4 = _place(net, "p4")
    p_5 = _place(net, "p5")

    t_commit = _trans(net, "commit")
    t_pull = _trans(net, "pull")
    t_merge = _trans(net, "merge")
    t_push = _trans(net, "push")
    t_1 = _trans(net, None, "tau_1")
    t_2 = _trans(net, None, "tau_2")
    t_3 = _trans(net, None, "tau_3")
    t_4 = _trans(net, None, "tau_4")
    t_5 = _trans(net, None, "tau_5")

    _arc(net, p_start, t_1)
    _arc(net, t_1, p_1)
    _arc(net, p_1, t_commit)
    _arc(net, t_commit, p_2)
    _arc(net, p_2, t_2)
    _arc(net, t_2, p_1)
    _arc(net, p_2, t_pull)
    _arc(net, t_pull, p_3)
    _arc(net, p_3, t_merge)
    _arc(net, t_merge, p_4)
    _arc(net, p_3, t_3)
    _arc(net, t_3, p_4)
    _arc(net, p_4, t_push)
    _arc(net, t_push, p_5)
    _arc(net, p_5, t_4)
    _arc(net, t_4, p_1)
    _arc(net, p_5, t_5)
    _arc(net, t_5, p_end)

    im = Marking({p_start: 1})
    fm = Marking({p_end: 1})  # final = back at start after last push
    return net, im, fm


def save_n1_subnet_figure(net: PetriNet, im: Marking, fm: Marking) -> str:
    """Render the N1 subnet used for replay/precision, for visual verification
    against the accepting OCPN N1 given in the assignment (PDF p.9)."""
    FIGURES2_DIR.mkdir(parents=True, exist_ok=True)
    png_path = str(FIGURES2_DIR / "n1_subnet_model.png")
    pm4py.save_vis_petri_net(net, im, fm, png_path)
    return png_path


# ── Step 7: token replay ──────────────────────────────────────────────────────


def run_token_replay(log, net, im, fm, label: str) -> float:
    """Run token-based replay and print a per-trace table. Returns average fitness."""
    results = pm4py.conformance_diagnostics_token_based_replay(log, net, im, fm)

    print(f"\n  Token-based replay -- {label}")
    hdr = f"  {'Case':<20} {'Fit':>5} {'Fitness':>8} {'Consumed':>9} {'Produced':>9} {'Missing':>8} {'Remain':>7}"
    print(hdr)
    print(f"  {'-' * 70}")
    fitnesses = []
    for trace, r in zip(log, results):
        case_id = trace.attributes.get("concept:name", "?")
        fit = "YES" if r["trace_is_fit"] else "NO"
        fitness = r["trace_fitness"]
        fitnesses.append(fitness)
        print(
            f"  {str(case_id):<20} {fit:>5} {fitness:>8.4f} "
            f"{r['consumed_tokens']:>9} {r['produced_tokens']:>9} "
            f"{r['missing_tokens']:>8} {r['remaining_tokens']:>7}"
        )
    avg = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
    print(f"  {'AVERAGE':<20} {'':>5} {avg:>8.4f}")
    return avg


# ── Step 8: precision ─────────────────────────────────────────────────────────


def run_precision(log, net, im, fm, label: str) -> float:
    """Compute alignment-based precision. Falls back to token-based on failure."""
    print(f"\n  Precision -- {label}")
    try:
        prec = pm4py.precision_alignments(log, net, im, fm)
        print(f"  Alignment-based precision: {prec:.4f}")
        return prec
    except Exception as e1:
        print(f"  [alignment precision failed: {e1}]")
        try:
            prec = pm4py.precision_token_based_replay(log, net, im, fm)
            print(f"  Token-based precision (fallback): {prec:.4f}")
            return prec
        except Exception as e2:
            print(f"  [token precision also failed: {e2}]")
            return float("nan")


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    sep = "=" * 60
    print(sep)
    print("Q5b: Flattening-based conformance checking for Cameron")
    print(sep)

    # Load
    print("\n[1] Loading OCEL log ...")
    ocel = load_ocel()
    print(f"    {len(ocel.events)} events total")

    # Filter
    print(f"\n[2] Building L^Cameron_1 (branches + users, Cameron only) ...")
    ocel_c = build_cameron_l1(ocel)
    print(f"    {len(ocel_c.events)} events for Cameron")

    # Flatten
    print("\n[3] Flattening ...")
    df_branches = flatten_log(ocel_c, "branches")
    df_users = flatten_log(ocel_c, "users")

    print_traces(df_branches, "branches")
    print_traces(df_users, "users")

    log_branches = _df_to_log(df_branches)
    log_users = _df_to_log(df_users)

    # Build N1 subnets
    net_b, im_b, fm_b = build_n1_subnet("N1_branches")
    net_u, im_u, fm_u = build_n1_subnet("N1_users")

    png_path = save_n1_subnet_figure(net_b, im_b, fm_b)
    print(f"\n[4] Saved N1 subnet model figure -> {png_path}")

    # Token replay
    print("\n" + "-" * 60)
    avg_fit_b = run_token_replay(log_branches, net_b, im_b, fm_b, "branches subnet")
    avg_fit_u = run_token_replay(log_users, net_u, im_u, fm_u, "users subnet")
    avg_fitness = (avg_fit_b + avg_fit_u) / 2
    print(f"\n  AVERAGE FITNESS (both subnets): {avg_fitness:.4f}")

    # Precision
    print("\n" + "-" * 60)
    prec_b = run_precision(log_branches, net_b, im_b, fm_b, "branches subnet")
    prec_u = run_precision(log_users, net_u, im_u, fm_u, "users subnet")
    avg_prec = (prec_b + prec_u) / 2
    print(f"\n  AVERAGE PRECISION (both subnets): {avg_prec:.4f}")

    # Summary
    print("\n" + sep)
    print("SUMMARY")
    print(sep)
    print(f"  Average token-based replay fitness : {avg_fitness:.4f}")
    print(f"  Average alignment-based precision  : {avg_prec:.4f}")
    print()
    print("Copy the trace tables and replay tables above into")
    print("report2/sections/q5b_conformance.tex at the TODO locations.")


if __name__ == "__main__":
    main()
