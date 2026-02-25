from __future__ import annotations

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from solve import GraphSolver
from graph import Edge, Vertex
from models import ZoneType


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

    path = solver.find_path(3)

    assert path == [0, 1, 3]


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
