from __future__ import annotations

import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from base_graph import BaseGraph
from models import Connection, Hub
from parser import Config


def test_graph_from_lists_builds_expected_adjacency_for_easy_linear_map() -> None:
    cfg = Config.from_file("maps/easy/01_linear_path.txt")

    graph = BaseGraph.graph_from_lists(cfg.hubs, cfg.connections)

    assert len(graph) == 4
    assert [len(edges) for edges in graph] == [1, 2, 2, 1]


def test_graph_from_lists_rejects_empty_hubs() -> None:
    with pytest.raises(ValueError, match="hubs list must not be empty"):
        BaseGraph.graph_from_lists([], [])


def test_graph_from_lists_rejects_unknown_hub_name_in_connections() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)

    with pytest.raises(ValueError, match="Unknown name found in connection"):
        BaseGraph.graph_from_lists(
            [hub_a, hub_b],
            [Connection("a", "missing")],
        )


def test_graph_from_lists_rejects_non_contiguous_hub_ids() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    _hub_b = Hub("b", 1, 1)
    hub_c = Hub("c", 2, 2)

    with pytest.raises(
        ValueError,
        match="Hub ids must be continuous and start from zero",
    ):
        BaseGraph.graph_from_lists([hub_a, hub_c], [Connection("a", "c")])


def test_graph_from_lists_preserves_link_capacity_on_edges() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)

    graph = BaseGraph.graph_from_lists([hub_a, hub_b], [Connection("a", "b", 7)])

    assert graph[0][0].to_hub == 1
    assert graph[0][0].max_link_capacity == 7
    assert graph[1][0].to_hub == 0
    assert graph[1][0].max_link_capacity == 7
