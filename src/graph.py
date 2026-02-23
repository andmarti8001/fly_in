
from __future__ import annotations

from collections import deque

from models import Connection, Hub, ZoneType
from parser import Config

class Vertex:
    def __init__(self, edges: list[Edge] | None, cap: int,
                 zone_type: ZoneType = ZoneType.NORMAL) -> None:
        self.edges = [] if edges is None else edges
        self.cap = cap
        self.zone_type = zone_type

class Edge:
    def __init__(self, to_hub: int, cap: int, weight: int) -> None:
        self.to_hub = to_hub
        self.cap = cap
        self.weight = weight

class Graph:
    def __init__(self, g: list[Vertex] | None, hub_tot: int | None) -> None:
        self.g: list[Vertex] = [] if g is None else g
        self.hub_tot: int = 0 if hub_tot is None else hub_tot
        self.inf: int = 1000000

    # ===============
    # ===   IDS   ===
    # ===============

    # ID schema
    # [t(0)  : [vertices][r_vertices]]
    # [t(1)  : [vertices][r_vertices]]
    # [t(2)  : [vertices][r_vertices]]
    # [t(...): [vertices][r_vertices]]
    # [t(n)  : [vertices][r_vertices]]
    def get_base_id(self, vertex_id: int) -> int:
        """Return the time(0) index of any id at any time(t). """
        return vertex_id % (2 * self.hub_tot)

    def get_r_id(self, vertex_id: int) -> int:
        """Return the transit-partner id for a restricted node."""
        return vertex_id + self.hub_tot

    def get_id_time(self, vertex_id: int, t: int) -> int:
        """Map a base vertex to its time-t partner """
        return t * (2 * self.hub_tot) + self.get_base_id(vertex_id)

    def is_transit(self, vertex_id: int) -> bool:
        """Return True if vertex_id points to the transit half of a layer."""
        return self.get_base_id(vertex_id) >= self.hub_tot

    # I did this in O(H * C) time but if I instantiated all the vertices in line 14-23
    # and added the connections as I went it would be O(H + 2C + restricted hubs)
    # but I tested and don't want to rewrite. all the example maps run in milliseconds
    def get_base_graph(self, cfg: Config) -> list[Vertex]:
        """Build the pre-time-expansion adjacency structure from parsed config.

        Layout invariant:
        - Base hub vertex i is stored at index i.
        - Transit partner for hub i is stored at index self.get_r_id(i).
        - Transit vertices are created only for restricted hubs.
        - Non-restricted hubs use a placeholder transit vertex: Vertex(None, 0).
        """
        self.hub_tot = len(cfg.hubs)
        base_graph = [[] for _ in range(0, 2 * self.hub_tot)]
        hub_dict = { hub.name: hub.id for hub in cfg.hubs }

        for i, hub in enumerate(cfg.hubs):
            if hub.id != i:
                raise ValueError("Parsing error")
            if hub.zone_type == ZoneType.RESTRICTED:
                base_graph[self.get_r_id(i)] = Vertex(
                        None,
                        hub.max_drones,
                        ZoneType.RESTRICTED)
            else:
                base_graph[self.get_r_id(i)] = Vertex(None, 0)

        for i, hub in enumerate(cfg.hubs):
            edges: list[Edge] = []
            cap = hub.max_drones
            for c in cfg.connections: 

                if hub.name == c.hub1:
                    h_id = hub_dict[c.hub2]
                elif hub.name == c.hub2:
                    h_id = hub_dict[c.hub1]
                else:
                    continue

                curr_dest = cfg.hubs[h_id].zone_type
                if curr_dest == ZoneType.RESTRICTED:
                    # set transit to restricted
                    transit_edges = base_graph[self.get_r_id(h_id)].edges
                    transit_edges.append(Edge(h_id, c.max_link_capacity, 1))
                    # add edge to edges to transit
                    edges.append(Edge(
                        self.get_r_id(h_id), c.max_link_capacity, 1))
                elif curr_dest == ZoneType.PRIORITY:
                    edges.append(Edge(h_id, c.max_link_capacity, 0.8))
                # if zone_type is NORMAL, START, or END
                else:
                    edges.append(Edge(h_id, c.max_link_capacity, 1))
            base_graph[i] = Vertex(edges, cap, hub.zone_type)

        return base_graph
            
                    
    def get_expanded_list(self, base_graph: list[Vertex], t: int) -> list[Vertex]:
        """Build the time-expanded graph over t layers.

        For each time layer i:
        - Base vertices (non-transit) get a wait edge to layer i+1.
        - All movement edges are copied to layer i+1 with same cap/weight.
        - Final layer stores vertices with no outgoing edges.

        Constraint:
        - Transit vertices have a no-wait rule: they never receive wait edges.
        """
        expanded_size = t * 2 * self.hub_tot
        expanded: list[Vertex] = [Vertex(None, 0) for _ in range(0, expanded_size)]

        for i in range(0, t):
            for j, vert in enumerate(base_graph):
                if i == t - 1:
                    expanded[self.get_id_time(j, i)] = Vertex(None, vert.cap)
                    continue
                if vert.cap <= 0:
                    continue
                edges: list[Edge] = []
                if not self.is_transit(j):
                    edges.append(Edge(
                            self.get_id_time(j, i + 1),
                            self.inf,
                            0))
                for e in vert.edges:
                    edges.append(Edge(
                        self.get_id_time(e.to_hub, i + 1),
                        e.cap,
                        e.weight))
                expanded[self.get_id_time(j, i)] = Vertex(edges, vert.cap)

        return expanded
