
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
                    edges.append(Edge(h_id, c.max_link_capacity, 0.99))
                # if zone_type is NORMAL, START, or END
                else:
                    edges.append(Edge(h_id, c.max_link_capacity, 1))
            base_graph[i] = Vertex(edges, cap, hub.zone_type)

        return base_graph
            
                    
    def get_r_expanded_list(self, base_graph: list[Vertex], t: int) -> list[Vertex]:
        """Build the reverse time-expanded graph over t layers.

        reverse meaning that the adjacency list goes backwards through time.
        this is useful because you can trace the shortest path from the end
        node, which avoids dead ends and cycles without pruning
        
        waiting constraint: transit-partners of restricted nodes can not
        wait. once entered the move is fully committed. 
        """
        expanded_size = t * 2 * self.hub_tot
        expanded: list[Vertex] = [
                    Vertex(None, vert.cap, vert.zone_type)
                    for i in range(0, t)
                    for vert in base_graph
                    ]

        for i in range(0, t):
            for j, vert in enumerate(base_graph):
                if not self.is_transit(get_id_time(j, i))
                    # wait connection but reverse
                    expanded[get_id_time(j, i + 1)].edges.append(
                            Edge(get_id_time(j, i),
                            self.inf,
                            0))
                for e in vert.edges:
                    expanded[get_id_time(j, i + 1)].edges.append(
                            Edge(get_id_time(j, i),
                            e.cap,
                            e.weight))

        return expanded

    @staticmethod
    def _fmt_edges(edges: list[Edge]) -> str:
        if not edges:
            return "[]"
        joined = ", ".join(
            f"{e.to_hub}(cap={e.cap},w={e.weight})"
            for e in edges
        )
        return f"[{joined}]"

    def print_base_graph(self, base_graph: list[Vertex] | None = None) -> None:
        """Print the base adjacency structure ([base][transit])."""
        graph_data = self.g if base_graph is None else base_graph
        print("Base Graph")
        print(f"hub_tot={self.hub_tot}, vertices={len(graph_data)}")
        for idx, vert in enumerate(graph_data):
            role = "base" if idx < self.hub_tot else "transit"
            print(
                f"[{idx:>3}] {role:<7} cap={vert.cap:<3} "
                f"zone={vert.zone_type.value:<10} edges={self._fmt_edges(vert.edges)}"
            )

    def print_expanded_graph(self, expanded_graph: list[Vertex], t: int) -> None:
        """Print the time-expanded graph layer by layer."""
        print("Time Expanded Graph")
        print(f"t={t}, hub_tot={self.hub_tot}, vertices={len(expanded_graph)}")
        for layer in range(0, t):
            print(f"Layer {layer}")
            for local_id in range(0, 2 * self.hub_tot):
                idx = self.get_id_time(local_id, layer)
                vert = expanded_graph[idx]
                role = "base" if local_id < self.hub_tot else "transit"
                print(
                    f"  [{idx:>3}] local={local_id:<3} {role:<7} cap={vert.cap:<3} "
                    f"edges={self._fmt_edges(vert.edges)}"
                )
