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


def test_get_r_expanded_list_adds_reverse_wait_for_base_nodes_only() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_r], [Connection("a", "r", 5)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    reverse_expanded = graph.get_r_expanded_list(base_graph, 2)

    # Base node at t=1 should have reverse wait edge to t=0.
    a_t1 = reverse_expanded[graph.get_id_time(hub_a.id, 1)]
    assert (graph.get_id_time(hub_a.id, 0), graph.inf, 0) in [
        (e.to_hub, e.cap, e.weight) for e in a_t1.edges
    ]

    # Transit node at t=1 should not get reverse wait edge.
    transit_id = graph.get_r_id(hub_r.id)
    tr_t1 = reverse_expanded[graph.get_id_time(transit_id, 1)]
    assert (graph.get_id_time(transit_id, 0), graph.inf, 0) not in [
        (e.to_hub, e.cap, e.weight) for e in tr_t1.edges
    ]


def test_get_r_expanded_list_adds_reverse_movement_edges() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.NORMAL)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_b], [Connection("a", "b", 3)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    reverse_expanded = graph.get_r_expanded_list(base_graph, 2)

    # Forward edge a->b at layer 0 implies reverse edge b@1 -> a@0.
    b_t1 = reverse_expanded[graph.get_id_time(hub_b.id, 1)]
    assert (graph.get_id_time(hub_a.id, 0), 3, 1) in [
        (e.to_hub, e.cap, e.weight) for e in b_t1.edges
    ]


def test_get_r_expanded_list_preserves_vertex_count_and_caps() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.START, max_drones=4)
    hub_b = Hub("b", 1, 1, zone=ZoneType.END, max_drones=2)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_b], [Connection("a", "b", 2)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    t = 3
    reverse_expanded = graph.get_r_expanded_list(base_graph, t)

    assert len(reverse_expanded) == t * 2 * graph.hub_tot
    assert reverse_expanded[graph.get_id_time(hub_a.id, 2)].cap == 4
    assert reverse_expanded[graph.get_id_time(hub_b.id, 2)].cap == 2


# round2 get_r_expanded_list hardening
def test_round2_get_r_expanded_list_t1_has_no_reverse_edges() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_b = Hub("b", 1, 1, zone=ZoneType.NORMAL)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_b], [Connection("a", "b", 2)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    reverse_expanded = graph.get_r_expanded_list(base_graph, 1)

    assert len(reverse_expanded) == 2 * graph.hub_tot
    assert all(v.edges == [] for v in reverse_expanded)


def test_round2_get_r_expanded_list_skips_vertices_with_non_positive_cap() -> None:
    hub_a = Hub("a", 0, 0, zone=ZoneType.NORMAL)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED, max_drones=1)
    cfg = _cfg_with_zone_type_attr([hub_a, hub_r], [Connection("a", "r", 4)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    reverse_expanded = graph.get_r_expanded_list(base_graph, 2)

    # Non-restricted transit placeholder has cap=0, so no outgoing reverse edges.
    placeholder_id = graph.get_r_id(hub_a.id)
    placeholder_t1 = reverse_expanded[graph.get_id_time(placeholder_id, 1)]
    assert placeholder_t1.cap == 0
    assert placeholder_t1.edges == []


def test_round2_get_r_expanded_list_adds_reverse_edge_into_restricted_transit() -> None:
    hub_n = Hub("n", 0, 0, zone=ZoneType.NORMAL)
    hub_r = Hub("r", 1, 1, zone=ZoneType.RESTRICTED)
    cfg = _cfg_with_zone_type_attr([hub_n, hub_r], [Connection("n", "r", 6)])

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)
    reverse_expanded = graph.get_r_expanded_list(base_graph, 2)

    # Forward n@0 -> r_transit@1 becomes reverse r_transit@1 -> n@0.
    r_transit_id = graph.get_r_id(hub_r.id)
    transit_t1 = reverse_expanded[graph.get_id_time(r_transit_id, 1)]
    assert (graph.get_id_time(hub_n.id, 0), 6, 1) in [
        (e.to_hub, e.cap, e.weight) for e in transit_t1.edges
    ]
