from __future__ import annotations

import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graph import Graph, Vertex
from models import Connection, Hub, ZoneType
from parser import Config


@pytest.fixture(autouse=True)
def _reset_hub_ids() -> None:
    Hub.reset_next_id()
    yield
    Hub.reset_next_id()


def _cfg_with_zone_type_attr(
    hubs: list[Hub],
    connections: list[Connection],
) -> Config:
    for hub in hubs:
        # graph.py currently reads `hub.zone_type`; mirror parsed-zone value here.
        hub.zone_type = hub.zone
    return Config(
        nb_drones=1,
        start_hub=hubs[0],
        end_hub=hubs[-1],
        hubs=hubs,
        connections=connections,
    )


def test_id_helpers_map_indices_across_layers() -> None:
    graph = Graph(None, 4)

    assert graph.get_base_id(0) == 0
    assert graph.get_base_id(7) == 7
    assert graph.get_base_id(8) == 0
    assert graph.get_r_id(3) == 7
    assert graph.get_id_time(6, 3) == 30
    assert graph.is_transit(3) is False
    assert graph.is_transit(4) is True
    assert graph.is_transit(11) is False


def test_get_base_graph_builds_base_and_transit_vertices() -> None:
    hub_s = Hub("s", 0, 0, zone=ZoneType.NORMAL, max_drones=3)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED, max_drones=2)
    hub_p = Hub("p", 2, 2, zone=ZoneType.PRIORITY, max_drones=5)
    cfg = _cfg_with_zone_type_attr(
        [hub_s, hub_r, hub_p],
        [
            Connection("s", "r", 4),
            Connection("r", "p", 2),
            Connection("s", "p", 3),
        ],
    )

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)

    assert len(base_graph) == 6
    assert all(isinstance(v, Vertex) for v in base_graph)

    assert base_graph[0].zone_type == ZoneType.NORMAL
    assert base_graph[1].zone_type == ZoneType.RESTRICTED
    assert base_graph[2].zone_type == ZoneType.PRIORITY

    assert base_graph[graph.get_r_id(0)].cap == 0
    assert base_graph[graph.get_r_id(2)].cap == 0
    assert base_graph[graph.get_r_id(1)].cap == 2
    assert base_graph[graph.get_r_id(1)].zone_type == ZoneType.RESTRICTED


def test_get_base_graph_routes_restricted_destinations_via_transit() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED)
    hub_b = Hub("b", 2, 2, zone=ZoneType.NORMAL)
    cfg = _cfg_with_zone_type_attr(
        [hub_a, hub_r, hub_b],
        [
            Connection("a", "r", 9),
            Connection("b", "r", 7),
        ],
    )

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)

    edges_from_a = base_graph[hub_a.id].edges
    edges_from_b = base_graph[hub_b.id].edges
    transit_edges = base_graph[graph.get_r_id(hub_r.id)].edges

    assert [(e.to_hub, e.cap, e.weight) for e in edges_from_a] == [
        (graph.get_r_id(hub_r.id), 9, 1),
    ]
    assert [(e.to_hub, e.cap, e.weight) for e in edges_from_b] == [
        (graph.get_r_id(hub_r.id), 7, 1),
    ]
    assert [(e.to_hub, e.cap, e.weight) for e in transit_edges] == [
        (hub_r.id, 9, 1),
        (hub_r.id, 7, 1),
    ]


def test_get_base_graph_raises_on_non_contiguous_hub_ids() -> None:
    hub_a = Hub("a", 0, 0)
    _hub_b = Hub("b", 1, 1)
    hub_c = Hub("c", 2, 2)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_c], [])

    graph = Graph(None, None)

    with pytest.raises(ValueError, match="Parsing error"):
        graph.get_base_graph(cfg)


def test_get_expanded_list_adds_wait_edge_for_base_nodes_only() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.NORMAL)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_b], [Connection("a", "b", 3)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    expanded = graph.get_expanded_list(base_graph, 2)

    a_t0 = expanded[graph.get_id_time(hub_a.id, 0)]
    wait_targets = [e.to_hub for e in a_t0.edges if e.cap == graph.inf and e.weight == 0]
    assert wait_targets == [graph.get_id_time(hub_a.id, 1)]


def test_get_expanded_list_enforces_no_wait_on_transit_nodes() -> None:
    hub_n = Hub("n", 0, 0, zone=ZoneType.NORMAL)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED)
    cfg = _cfg_with_zone_type_attr([hub_n, hub_r], [Connection("n", "r", 5)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    expanded = graph.get_expanded_list(base_graph, 2)

    transit_id = graph.get_r_id(hub_r.id)
    transit_t0 = expanded[graph.get_id_time(transit_id, 0)]

    assert transit_t0.cap > 0
    assert all(not (e.cap == graph.inf and e.weight == 0) for e in transit_t0.edges)


def test_get_expanded_list_last_layer_has_no_outgoing_edges() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.RESTRICTED)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_b], [Connection("a", "b", 2)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    t = 3
    expanded = graph.get_expanded_list(base_graph, t)

    last_layer = t - 1
    for j in range(0, 2 * graph.hub_tot):
        vert = expanded[graph.get_id_time(j, last_layer)]
        assert vert.edges == []
