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


def test_round2_has_solution_true_for_connected_graph() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)
    hub_c = Hub("c", 2, 2)
    graph = BaseGraph.graph_from_lists(
        [hub_a, hub_b, hub_c],
        [Connection("a", "c"), Connection("c", "b")],
    )

    assert BaseGraph.has_solution(graph, 0, 1) is True


def test_round2_has_solution_false_for_disconnected_graph() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)
    graph = BaseGraph.graph_from_lists([hub_a, hub_b], [])

    assert BaseGraph.has_solution(graph, 0, 1) is False


def test_round2_from_config_builds_graph_when_path_exists() -> None:
    cfg = Config.from_file("maps/easy/01_linear_path.txt")

    base_graph = BaseGraph.from_config(cfg)

    assert isinstance(base_graph, BaseGraph)
    assert len(base_graph.graph) == 4


def test_round2_from_config_raises_when_no_path_exists(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "end_hub: end 2 2",
            "hub: mid 1 1 [zone=blocked]",
            "connection: start-mid",
            "connection: mid-end",
        ]
    )
    config_path = tmp_path / "no_path_after_prune.txt"
    config_path.write_text(config_content, encoding="utf-8")
    cfg = Config.from_file(str(config_path))

    with pytest.raises(ValueError, match="No valid path from start_hub to end_hub"):
        BaseGraph.from_config(cfg)


# round 3 hardening
def test_round3_has_solution_empty_graph_is_false() -> None:
    assert BaseGraph.has_solution([]) is False


def test_round3_has_solution_out_of_range_indices_are_false() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    hub_b = Hub("b", 1, 1)
    graph = BaseGraph.graph_from_lists([hub_a, hub_b], [Connection("a", "b")])

    assert BaseGraph.has_solution(graph, -1, 1) is False
    assert BaseGraph.has_solution(graph, 0, 10) is False


def test_round3_has_solution_same_start_and_end_is_true() -> None:
    Hub.reset_next_id()
    hub_a = Hub("a", 0, 0)
    graph = BaseGraph.graph_from_lists([hub_a], [])

    assert BaseGraph.has_solution(graph, 0, 0) is True


def test_round3_from_config_raises_when_start_hub_blocked(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "end_hub: end 2 2",
            "hub: mid 1 1",
            "connection: start-mid",
            "connection: mid-end",
        ]
    )
    config_path = tmp_path / "blocked_start_hub.txt"
    config_path.write_text(config_content, encoding="utf-8")
    cfg = Config.from_file(str(config_path))
    cfg.start_hub.zone = ZoneType.BLOCKED

    with pytest.raises(ValueError, match="start_hub or end_hub missing after pruning"):
        BaseGraph.from_config(cfg)


def test_round3_from_config_raises_when_end_hub_blocked(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "end_hub: end 2 2",
            "hub: mid 1 1",
            "connection: start-mid",
            "connection: mid-end",
        ]
    )
    config_path = tmp_path / "blocked_end_hub.txt"
    config_path.write_text(config_content, encoding="utf-8")
    cfg = Config.from_file(str(config_path))
    cfg.end_hub.zone = ZoneType.BLOCKED

    with pytest.raises(ValueError, match="start_hub or end_hub missing after pruning"):
        BaseGraph.from_config(cfg)


def test_round3_from_config_keeps_capacity_after_pruning(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: s 0 0",
            "end_hub: e 3 3",
            "hub: b 1 1 [zone=blocked]",
            "hub: x 2 2",
            "connection: s-b [max_link_capacity=9]",
            "connection: b-e [max_link_capacity=8]",
            "connection: s-x [max_link_capacity=4]",
            "connection: x-e [max_link_capacity=6]",
        ]
    )
    config_path = tmp_path / "capacity_after_prune.txt"
    config_path.write_text(config_content, encoding="utf-8")
    cfg = Config.from_file(str(config_path))

    base_graph = BaseGraph.from_config(cfg)
    graph = base_graph.graph

    assert len(graph) == 3
    assert [len(edges) for edges in graph] == [1, 1, 2]
    assert graph[0][0].to_hub == 2
    assert graph[0][0].max_link_capacity == 4
