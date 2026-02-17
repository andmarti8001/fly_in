from __future__ import annotations

import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from base_graph import BaseGraph
from models import Connection, Hub, ZoneType
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


def test_prune_hub_list_removes_blocked_and_reindexes() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    _hub_b = Hub("b", 1, 1, zone=ZoneType.BLOCKED)
    hub_c = Hub("c", 2, 2, zone=ZoneType.PRIORITY)

    pruned = BaseGraph.prune_hub_list([hub_a, _hub_b, hub_c])

    assert [hub.name for hub in pruned] == ["a", "c"]
    assert [hub.id for hub in pruned] == [0, 1]


def test_prune_connection_list_removes_connections_touching_blocked_hubs() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.BLOCKED)
    hub_c = Hub("c", 2, 2, zone=ZoneType.NORMAL)

    connections = [
        Connection("a", "b"),
        Connection("b", "c"),
        Connection("a", "c"),
    ]

    pruned = BaseGraph.prune_connection_list(connections, [hub_a, hub_b, hub_c])

    assert len(pruned) == 1
    assert pruned[0].hub1 == "a"
    assert pruned[0].hub2 == "c"


# round 2 hardening
def test_round2_prune_hub_list_mutates_original_hub_ids() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.BLOCKED)
    hub_c = Hub("c", 2, 2, zone=ZoneType.NORMAL)

    BaseGraph.prune_hub_list([hub_a, hub_b, hub_c])

    assert hub_a.id == 0
    assert hub_c.id == 1


def test_round2_graph_from_lists_rejects_duplicate_hub_names() -> None:
    Hub.reset_next_id()
    hub_a = Hub("dup", 0, 0)
    hub_b = Hub("dup", 1, 1)

    with pytest.raises(ValueError, match="Duplicate hub name"):
        BaseGraph.graph_from_lists([hub_a, hub_b], [])


def test_round2_graph_from_lists_keeps_duplicate_connections() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)
    conns = [
        Connection("a", "b", 2),
        Connection("a", "b", 3),
    ]

    graph = BaseGraph.graph_from_lists([hub_a, hub_b], conns)

    assert len(graph[0]) == 2
    assert len(graph[1]) == 2
    assert [edge.max_link_capacity for edge in graph[0]] == [2, 3]


def test_round2_graph_from_lists_keeps_self_loop_as_two_undirected_entries() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)

    graph = BaseGraph.graph_from_lists([hub_a], [Connection("a", "a", 5)])

    assert len(graph) == 1
    assert len(graph[0]) == 2
    assert graph[0][0].to_hub == 0
    assert graph[0][1].to_hub == 0
    assert graph[0][0].max_link_capacity == 5
    assert graph[0][1].max_link_capacity == 5


def test_round2_prune_then_build_graph_integration() -> None:
    Hub.reset_next_id()
    hub_s = Hub("s", 0, 0, zone=ZoneType.START)
    hub_b = Hub("b", 1, 1, zone=ZoneType.BLOCKED)
    hub_x = Hub("x", 2, 2, zone=ZoneType.NORMAL)
    hub_e = Hub("e", 3, 3, zone=ZoneType.END)
    connections = [
        Connection("s", "b"),
        Connection("b", "x"),
        Connection("s", "x", 2),
        Connection("x", "e", 4),
    ]

    pruned_hubs = BaseGraph.prune_hub_list([hub_s, hub_b, hub_x, hub_e])
    pruned_connections = BaseGraph.prune_connection_list(connections, pruned_hubs)
    graph = BaseGraph.graph_from_lists(pruned_hubs, pruned_connections)

    assert [hub.name for hub in pruned_hubs] == ["s", "x", "e"]
    assert [len(edges) for edges in graph] == [1, 2, 1]
    assert graph[0][0].to_hub == 1
    assert graph[0][0].max_link_capacity == 2
