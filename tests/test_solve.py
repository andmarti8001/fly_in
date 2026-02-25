from __future__ import annotations

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graph import Edge, Vertex
from models import ZoneType
from solve import GraphSolver


def test_find_path_returns_shortest_chain_from_start_to_end() -> None:
    # Reverse-expanded style graph:
    # 3 -> 1 -> 0 total cost 2 (maps to path 0 -> 1 -> 3)
    # 3 -> 2 -> 0 total cost 3 (maps to path 0 -> 2 -> 3)
    g = [
        Vertex([], 1, ZoneType.START),
        Vertex([Edge(0, 1, 1)], 1, ZoneType.NORMAL),
        Vertex([Edge(0, 1, 1)], 1, ZoneType.NORMAL),
        Vertex([Edge(1, 1, 1), Edge(2, 1, 2)], 1, ZoneType.END),
    ]
    solver = GraphSolver(g, nb_drones=1)

    assert solver.find_path(3) == [0, 1, 3]


def test_find_path_returns_none_when_end_unreachable_from_start() -> None:
    g = [
        Vertex([Edge(1, 1, 1)], 1, ZoneType.START),
        Vertex([], 1, ZoneType.NORMAL),
        Vertex([], 1, ZoneType.END),
    ]
    solver = GraphSolver(g, nb_drones=1)

    assert solver.find_path(2) is None


def test_find_path_rejects_invalid_end_id() -> None:
    g = [Vertex([], 1, ZoneType.START), Vertex([], 1, ZoneType.END)]
    solver = GraphSolver(g, nb_drones=1)

    assert solver.find_path(-1) is None
    assert solver.find_path(99) is None
    assert solver.find_path(0) is None


def test_subtract_cap_reduces_capacity_on_normal_hubs_in_path() -> None:
    g = [
        Vertex([Edge(1, 1, 1)], 5, ZoneType.START),
        Vertex([Edge(2, 2, 1)], 2, ZoneType.NORMAL),
        Vertex([], 5, ZoneType.END),
    ]
    solver = GraphSolver(g, nb_drones=1)

    solver.subtract_cap([0, 1, 2])

    # START/END are skipped by design, normal hub capacity decreases.
    assert g[0].cap == 5
    assert g[1].cap == 1
    assert g[2].cap == 5
    assert g[1].edges[0].cap == 1


def test_subtract_cap_noop_for_empty_path() -> None:
    g = [Vertex([], 2, ZoneType.START), Vertex([], 3, ZoneType.END)]
    solver = GraphSolver(g, nb_drones=1)

    solver.subtract_cap([])

    assert g[0].cap == 2
    assert g[1].cap == 3


def test_solve_returns_paths_when_capacity_allows_all_drones() -> None:
    g = [
        Vertex([], 10, ZoneType.START),
        Vertex([Edge(0, 10, 1)], 2, ZoneType.NORMAL),
        Vertex([Edge(1, 10, 1)], 2, ZoneType.END),
    ]
    solver = GraphSolver(g, nb_drones=2)

    paths = solver.solve()

    assert paths == [[0, 1, 2], [0, 1, 2]]


def test_solve_returns_none_when_not_enough_capacity_for_all_drones() -> None:
    g = [
        Vertex([], 10, ZoneType.START),
        Vertex([Edge(0, 10, 1)], 2, ZoneType.NORMAL),
        Vertex([Edge(1, 10, 1)], 2, ZoneType.END),
    ]
    solver = GraphSolver(g, nb_drones=3)

    assert solver.solve() is None

