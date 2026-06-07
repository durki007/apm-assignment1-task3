"""
Discover the object-centric Petri net N2 (subtask e).

Run:  poetry run python -m olympic_transport.discover_ocpn
      # or:  poetry run ocpn
"""
import pm4py

from olympic_transport.config import DATA_DIR, MODELS_DIR, FIGURES_DIR


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    ocel = pm4py.read_ocel2_sqlite(str(DATA_DIR / "log.sqlite"))

    ocpn = pm4py.discover_oc_petri_net(ocel)

    svg_path = str(MODELS_DIR / "N2_ocpn.svg")
    png_path = str(FIGURES_DIR / "N2_ocpn.png")

    pm4py.save_vis_ocpn(ocpn, png_path)
    print(f"Saved figure → {png_path}")

    # Also try SVG export if the PM4Py version supports it
    try:
        pm4py.save_vis_ocpn(ocpn, svg_path)
        print(f"Saved model  → {svg_path}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
