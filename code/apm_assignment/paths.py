"""Shared filesystem paths, used by both part1 and part2."""
import os
from pathlib import Path


# ── Graphviz PATH fix (Windows) ────────────────────────────────────────────
# dot.exe is often installed but not on PATH; probe common locations and add.
def _add_graphviz_to_path() -> None:
    import shutil
    if shutil.which("dot"):
        return
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Graphviz" / "bin",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Graphviz" / "bin",
        Path(r"C:\Program Files\Graphviz\bin"),
        Path(r"C:\Graphviz\bin"),
    ]
    for p in candidates:
        if (p / "dot.exe").exists():
            os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
            break


_add_graphviz_to_path()

# ── Paths ──────────────────────────────────────────────────────────────────
_PACKAGE_DIR = Path(__file__).parent            # code/apm_assignment/
_CODE_DIR    = _PACKAGE_DIR.parent              # code/
ROOT_DIR     = _CODE_DIR.parent                 # project root (g:/apm/)

DATA_DIR     = ROOT_DIR / "data"
MODELS_DIR   = ROOT_DIR / "models"
FIGURES_DIR  = ROOT_DIR / "figures"
FIGURES2_DIR = ROOT_DIR / "report2" / "figures"
