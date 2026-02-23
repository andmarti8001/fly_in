from __future__ import annotations

import heapq
from math import inf

from graph import Graph
from models import ZoneType


class GraphSolver:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones

    def find_path(self, sink_id: int) -> list[int] | None:
        """Return one lowest-cost path from start node 0 to sink_id.

        Uses reverse Dijkstra:
        - Build a temporary reversed adjacency list from self.graph.g.
        - Run Dijkstra from sink_id on the reversed graph.
        - Reconstruct the path from node 0 to sink_id.
        """
        nodes = self.graph.g
        n = len(nodes)
        start_id = 0

        if n == 0:
            return None
        if sink_id < 0 or sink_id >= n:
            return None
        if start_id == sink_id:
            return [start_id]

        reverse_adj: list[list[tuple[int, float]]] = [[] for _ in range(n)]
        for from_id, vertex in enumerate(nodes):
            if vertex.cap <= 0:
                continue
            for edge in vertex.edges:
                if edge.cap <= 0:
                    continue
                to_id = edge.to_hub
                if 0 <= to_id < n:
                    reverse_adj[to_id].append((from_id, float(edge.weight)))

        dist = [inf] * n
        prev: list[int | None] = [None] * n
        dist[sink_id] = 0.0
        pq: list[tuple[float, int]] = [(0.0, sink_id)]

        while pq:
            curr_dist, curr = heapq.heappop(pq)
            if curr_dist != dist[curr]:
                continue
            if curr == start_id:
                break
            for pred, w in reverse_adj[curr]:
                cand = curr_dist + w
                if cand < dist[pred]:
                    dist[pred] = cand
                    prev[pred] = curr
                    heapq.heappush(pq, (cand, pred))

        if dist[start_id] == inf:
            return None

        path: list[int] = [start_id]
        curr = start_id
        while curr != sink_id:
            nxt = prev[curr]
            if nxt is None:
                return None
            path.append(nxt)
            curr = nxt
        return path

    def subtract_cap(self, path: list[int]) -> None:
        """Consume one unit of capacity along a selected path."""
        if not path:
            return

        # Consume vertex capacities where finite/positive.
        for node_id in path:
            if 0 <= node_id < len(self.graph.g) and self.graph.g[node_id].cap > 0:
                self.graph.g[node_id].cap -= 1

        # Consume one unit from each directed edge used in the path.
        for from_id, to_id in zip(path, path[1:]):
            if not (0 <= from_id < len(self.graph.g)):
                continue
            for edge in self.graph.g[from_id].edges:
                if edge.to_hub == to_id and edge.cap > 0:
                    edge.cap -= 1
                    break

    def solve(self) -> list[list[int]] | None:
        """Solve and return one path per drone when possible."""
        paths: list[list[int]] = []
        list_of_sinks = [
            i
            for i, sink in enumerate(self.graph.g)
            if sink.zone_type == ZoneType.END
        ]
        for sink_id in list_of_sinks:
            while len(paths) < self.nb_drones and self.graph.g[sink_id].cap > 0:
                path = self.find_path(sink_id)
                if path is None:
                    break
                paths.append(path)
                self.subtract_cap(path)
            if len(paths) == self.nb_drones:
                return paths
        return None

    def print_paths(self, paths: list[list[int]]) -> None:
        for i, path in enumerate(paths):
            print(f"Drone {i}: {' -> '.join(str(v) for v in path)}")
