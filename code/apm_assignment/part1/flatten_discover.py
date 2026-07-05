"""
Flatten the OCEL to two object types and discover Petri nets (subtasks d-iv, d-v).

Run:  poetry run python -m apm_assignment.part1.flatten_discover
      # or:  poetry run discover
"""
import pm4py

from apm_assignment.part1.config import DATA_DIR, MODELS_DIR, FIGURES_DIR, OT_OA, OT_SYNC


def _process(ocel, object_type: str, name: str):
    print(f"\n--- Flattening to object type: {object_type} ({name}) ---")

    flat = pm4py.ocel_flattening(ocel, object_type)
    print(f"  Flat log: {len(flat)} traces")

    net, im, fm = pm4py.discover_petri_net_inductive(flat)

    pnml_path = str(MODELS_DIR / f"{name}.pnml")
    png_path  = str(FIGURES_DIR / f"{name}.png")

    pm4py.write_pnml(net, im, fm, pnml_path)
    pm4py.save_vis_petri_net(net, im, fm, png_path)

    print(f"  Saved model  → {pnml_path}")
    print(f"  Saved figure → {png_path}")

    transitions = [t.label for t in net.transitions if t.label]
    print(f"  Visible transitions: {transitions}")

    return net, im, fm


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    ocel = pm4py.read_ocel2_sqlite(str(DATA_DIR / "log.sqlite"))

    # d-iv: flatten to TravelTicket (ot_oa) — expect XOR split Board vs Validate
    _process(ocel, OT_OA, "N_ot_oa")

    # d-v: flatten to Passenger (ot_sync) — expect AssignToDeparture directly precedes Depart
    _process(ocel, OT_SYNC, "N_ot_sync")


if __name__ == "__main__":
    main()
