"""Copy generated figures from project figures/ and models/ into report/figures/."""
import shutil
from pathlib import Path

REPORT_DIR  = Path(__file__).parent
PROJECT_ROOT = REPORT_DIR.parent

src_dst = [
    (PROJECT_ROOT / "figures" / "N_ot_oa.png",            REPORT_DIR / "figures" / "N_ot_oa.png"),
    (PROJECT_ROOT / "figures" / "N_ot_sync.png",          REPORT_DIR / "figures" / "N_ot_sync.png"),
    (PROJECT_ROOT / "figures" / "N2_ocpn.png",            REPORT_DIR / "figures" / "N2_ocpn.png"),
    (PROJECT_ROOT / "figures" / "dotted_chart_sync.png",  REPORT_DIR / "figures" / "dotted_chart_sync.png"),
]

for src, dst in src_dst:
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Copied {src.name}")
    else:
        print(f"MISSING (run pipeline first): {src}")
