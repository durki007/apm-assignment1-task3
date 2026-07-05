"""
Emit E2O and O2O relation tables as Markdown (subtask b).

Run:  poetry run python -m apm_assignment.part1.render_tables
"""
from apm_assignment.part1.config import OBJECT_TYPES, EVENT_TYPES, E2O_SPEC, O2O_SPEC


def render_e2o() -> str:
    header = "| Event type | " + " | ".join(OBJECT_TYPES) + " |"
    sep    = "|" + "---|" * (len(OBJECT_TYPES) + 1)
    rows = []
    for et in EVENT_TYPES:
        covered = E2O_SPEC.get(et, [])
        cells = ["✓" if ot in covered else "" for ot in OBJECT_TYPES]
        rows.append(f"| `{et}` | " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


def render_o2o() -> str:
    header = "| Source | Qualifier | Target | Cardinality |"
    sep    = "|---|---|---|---|"
    rows = [
        f"| `{src}` | `{qual}` | `{tgt}` | {card} |"
        for src, qual, tgt, card in O2O_SPEC
    ]
    return "\n".join([header, sep] + rows)


def main():
    print("## E2O type-level relations\n")
    print(render_e2o())
    print("\n## O2O type-level relations\n")
    print(render_o2o())


if __name__ == "__main__":
    main()
