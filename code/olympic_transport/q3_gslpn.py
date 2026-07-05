"""
Q3: Trace-probability computation for the GSLPN on p.6 of the assignment PDF.

Run:  poetry run python -m olympic_transport.q3_gslpn
      # or:  poetry run q3

The net (places p0..p10, transitions t0..t11) is entered by hand below from
the figure. Semantics follow the lecture's embedded-DTMC construction for
GSLPNs, extended from SLPNs:
  - A transition is enabled iff its input places all hold a token (the net
    is 1-safe here, so a marking is just the set of places with a token).
  - Immediate transitions have priority over timed ones: if any enabled
    transition is immediate, only immediate transitions may fire next.
  - Among the competing (immediate or, if none, timed) transitions, the
    probability of a given one firing next is its weight over the sum of
    the competing weights.

Both questions are answered on the product of the marking graph with a
"how much of sigma has been matched so far" counter, pruning any transition
whose visible label would not extend that match (that probability mass
simply isn't part of P(sigma)):
  (a) the single highest-probability path is the max-product path to the
      accepting state -- found with a Dijkstra variant that maximizes a
      product of probabilities instead of minimizing a sum of costs (valid
      here because every edge weight is a probability in (0, 1], so cycles
      can never improve on a loop-free path).
  (b) P(sigma) is the total probability of ever reaching the accepting
      state, i.e. the solution of the absorption-probability linear system
      of the embedded DTMC (needed because of the silent t9-loop, which
      admits infinitely many equally-matching paths).
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, FrozenSet, List, Optional, Tuple

import graphviz

from olympic_transport.config import ROOT_DIR

FIGURES2_DIR = ROOT_DIR / "report2" / "figures"

Marking = FrozenSet[str]
State = Tuple[Marking, int]  # (marking, number of SIGMA letters matched so far)


@dataclass(frozen=True)
class Transition:
    name: str
    immediate: bool
    weight: Fraction
    label: Optional[str]  # visible label, or None if silent (tau)
    pre: FrozenSet[str]
    post: Tuple[str, ...]


def _t(name, immediate, weight, label, pre, post) -> Transition:
    return Transition(name, immediate, Fraction(weight), label, frozenset(pre), tuple(post))


# ── Net definition (from the GSLPN figure, assignment PDF p.6) ──────────────

TRANSITIONS: Dict[str, Transition] = {
    t.name: t
    for t in [
        _t("t0", False, 2, "a", ["p0"], ["p1", "p2"]),
        _t("t1", True, 2, "b", ["p1"], ["p5"]),
        _t("t2", True, 3, None, ["p1"], ["p5"]),
        _t("t3", False, 4, "d", ["p2"], ["p3"]),
        _t("t4", False, 1, "e", ["p3"], ["p4"]),
        _t("t5", False, Fraction(3, 2), None, ["p5"], ["p9"]),
        _t("t6", True, 1, None, ["p6", "p4"], ["p7"]),
        _t("t7", False, 1, "f", ["p7"], ["p8"]),
        _t("t8", True, 2, None, ["p6", "p4"], ["p1", "p2"]),
        _t("t9", True, 3, None, ["p9"], ["p1"]),
        _t("t10", True, 1, None, ["p9"], ["p10"]),
        _t("t11", False, 2, "c", ["p10"], ["p6"]),
    ]
}

INITIAL_MARKING: Marking = frozenset({"p0"})
SIGMA: Tuple[str, ...] = ("a", "d", "c", "e", "f")


# ── Net rendering (visual check against the figure; saved for the report) ──

def render_net(name: str = "gslpn_net") -> str:
    """Draw the encoded net with the same legend as the assignment figure:
    plain box = timed, thick-bordered box = immediate, grey box = tau+timed,
    black box = tau+immediate. Saved to report2/figures/<name>.png."""
    dot = graphviz.Digraph(name, format="png")
    dot.attr(rankdir="LR", nodesep="0.35", ranksep="0.55")
    dot.attr("node", fontsize="11")
    dot.attr("edge", arrowsize="0.7")

    places = sorted(
        {p for t in TRANSITIONS.values() for p in t.pre}
        | {p for t in TRANSITIONS.values() for p in t.post},
        key=lambda p: int(p[1:]),
    )
    for p in places:
        label = "•" if p in INITIAL_MARKING else ""
        dot.node(p, shape="circle", label=label, width="0.35", fixedsize="true", xlabel=p)

    for tname, t in sorted(TRANSITIONS.items(), key=lambda kv: int(kv[0][1:])):
        attrs = dict(shape="box", label=t.label or "", width="0.4", height="0.35")
        if t.immediate and t.label is None:
            attrs.update(style="filled", fillcolor="black", fontcolor="white")
        elif t.immediate:
            attrs.update(penwidth="2.5")
        elif t.label is None:
            attrs.update(style="filled", fillcolor="gray75")
        dot.node(tname, xlabel=f"{tname}, w={t.weight}", **attrs)
        for p in t.pre:
            dot.edge(p, tname)
        for p in t.post:
            dot.edge(tname, p)

    FIGURES2_DIR.mkdir(parents=True, exist_ok=True)
    out_base = str(FIGURES2_DIR / name)
    dot.render(out_base, cleanup=True)
    return out_base + ".png"


# ── Marking-graph semantics ─────────────────────────────────────────────────

def enabled(marking: Marking) -> List[Transition]:
    return [t for t in TRANSITIONS.values() if t.pre <= marking]


def race(marking: Marking) -> Dict[str, Fraction]:
    """Firing probabilities at `marking` under GSPN race semantics: immediate
    transitions preempt timed ones; the winning class races by weight."""
    en = enabled(marking)
    if not en:
        return {}
    pool = [t for t in en if t.immediate] or en
    total = sum((t.weight for t in pool), Fraction(0))
    return {t.name: t.weight / total for t in pool}


def fire(marking: Marking, t: Transition) -> Marking:
    return (marking - t.pre) | set(t.post)


# ── Product automaton: marking x (letters of SIGMA matched so far) ─────────

def step_edges(state: State) -> List[Tuple[str, Fraction, State]]:
    """Outgoing (transition, probability, next-state) edges from `state`
    that are consistent with eventually projecting onto SIGMA. A transition
    whose visible label doesn't extend the current match is dropped -- that
    branch can never contribute to P(sigma)."""
    marking, idx = state
    edges = []
    for name, p in race(marking).items():
        t = TRANSITIONS[name]
        if t.label is None:
            edges.append((name, p, (fire(marking, t), idx)))
        elif idx < len(SIGMA) and t.label == SIGMA[idx]:
            edges.append((name, p, (fire(marking, t), idx + 1)))
        # else: firing t here would add a wrong/extra visible label -> prune
    return edges


def build_graph(start: State) -> Dict[State, List[Tuple[str, Fraction, State]]]:
    graph: Dict[State, List[Tuple[str, Fraction, State]]] = {}
    stack = [start]
    while stack:
        s = stack.pop()
        if s in graph:
            continue
        edges = step_edges(s)
        graph[s] = edges
        for _, _, s2 in edges:
            if s2 not in graph:
                stack.append(s2)
    return graph


START: State = (INITIAL_MARKING, 0)
ACCEPT: State = (frozenset({"p8"}), len(SIGMA))


# ── (a) Highest-probability single path (max-product Dijkstra) ─────────────

def most_probable_path(
    graph: Dict[State, List[Tuple[str, Fraction, State]]],
    start: State,
    accept: State,
) -> Tuple[Fraction, List[Tuple[str, State, Fraction]]]:
    """Return (P(best path), [(transition, marking-reached, step-prob), ...]).

    Maximizing a product of probabilities in (0, 1] is equivalent to a
    shortest-path problem (take -log of each weight), so Dijkstra's
    greedy correctness applies directly: once a state is popped with its
    best-known probability, no later (necessarily smaller-or-equal-factor)
    relaxation can improve it, even though the graph has a cycle.
    """
    best: Dict[State, Fraction] = {start: Fraction(1)}
    prev: Dict[State, Tuple[State, str, Fraction]] = {}
    counter = 0
    pq: List[Tuple[Fraction, int, State]] = [(Fraction(-1), counter, start)]
    settled: set = set()

    while pq:
        neg_p, _, s = heapq.heappop(pq)
        if s in settled:
            continue
        settled.add(s)
        p = -neg_p
        if s == accept:
            break
        for name, step_p, s2 in graph.get(s, []):
            cand = p * step_p
            if s2 not in best or cand > best[s2]:
                best[s2] = cand
                prev[s2] = (s, name, step_p)
                counter += 1
                heapq.heappush(pq, (-cand, counter, s2))

    if accept not in best:
        return Fraction(0), []

    steps: List[Tuple[str, State, Fraction]] = []
    s = accept
    while s in prev:
        p_state, name, step_p = prev[s]
        steps.append((name, s, step_p))
        s = p_state
    steps.reverse()
    return best[accept], steps


# ── (b) Total probability of matching SIGMA (absorption probabilities) ─────

def solve_linear(matrix: List[List[Fraction]], rhs: List[Fraction]) -> List[Fraction]:
    """Exact Gaussian elimination with partial pivoting over Fraction."""
    n = len(matrix)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot = next((r for r in range(col, n) if a[r][col] != 0), None)
        if pivot is None:
            continue
        a[col], a[pivot] = a[pivot], a[col]
        pv = a[col][col]
        a[col] = [x / pv for x in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0:
                factor = a[r][col]
                a[r] = [x - factor * y for x, y in zip(a[r], a[col])]

    return [a[i][n] for i in range(n)]


def probability_of_sigma(graph: Dict[State, List[Tuple[str, Fraction, State]]], start: State, accept: State) -> Fraction:
    """P(sigma) = absorption probability into `accept` in the embedded DTMC
    restricted to sigma-consistent transitions:  x_s = sum_edges p * x_s' ,
    x_accept = 1, and any other state with no outgoing edges has x_s = 0.
    """
    states = [s for s in graph if s != accept]
    index = {s: i for i, s in enumerate(states)}
    n = len(states)

    matrix = [[Fraction(0)] * n for _ in range(n)]
    rhs = [Fraction(0) for _ in range(n)]

    for s in states:
        i = index[s]
        matrix[i][i] = Fraction(1)
        for _, p, s2 in graph[s]:
            if s2 == accept:
                rhs[i] += p
            else:
                matrix[i][index[s2]] -= p

    solution = solve_linear(matrix, rhs)
    return solution[index[start]] if start in index else Fraction(1)


# ── Reporting ────────────────────────────────────────────────────────────

def _fmt_marking(m: Marking) -> str:
    return "{" + ", ".join(sorted(m, key=lambda p: int(p[1:]))) + "}"


def main() -> None:
    png_path = render_net()
    print(f"Net figure saved to {png_path}")

    graph = build_graph(START)
    print(f"Reachable (marking, matched-prefix) states consistent with sigma = {SIGMA}: {len(graph)}")

    print("\n=== (a) Highest-probability path projecting onto sigma ===")
    prob_a, steps = most_probable_path(graph, START, ACCEPT)
    trace_so_far: List[str] = []
    marking = INITIAL_MARKING
    print(f"  0  <>  M0 = {_fmt_marking(marking)}")
    for i, (name, (new_marking, idx), step_p) in enumerate(steps, start=1):
        t = TRANSITIONS[name]
        if t.label is not None:
            trace_so_far.append(t.label)
        print(
            f"  {i}  <{','.join(trace_so_far)}>  "
            f"M{i} = {_fmt_marking(new_marking)}  "
            f"fired {name} ({'immediate' if t.immediate else 'timed'}, w={t.weight})  "
            f"p={step_p} = {float(step_p):.4f}"
        )
        marking = new_marking
    print(f"  P(best path) = {prob_a}  =  {float(prob_a):.6f}")

    print("\n=== (b) P(sigma) -- total probability over all matching paths ===")
    prob_b = probability_of_sigma(graph, START, ACCEPT)
    print(f"  P(sigma) = {prob_b}  =  {float(prob_b):.6f}")


if __name__ == "__main__":
    main()
