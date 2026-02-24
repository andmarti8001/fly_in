from __future__ import annotations

from heapq import heappush, heappop

from graph import Graph
from models import ZoneType


class GraphSolver:
    def __init__(self, graph: list[Vertex], nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.inf = 10000000

    def find_path(self, end_id: int) -> list[int] | None:
        """Return the shortest path from given end_id
        to the start node at t(0).
        """
        graph = self.graph
        num_v = len(graph)
        start_id = 0

        # input errors
        if (num_v < 1 or end_id == start_id):
            return None
        if (end_id < 0 or num_id <= end_id):
            return None

        distances = [self.inf] * num_v
        distances[end_id] = 0
        last_visited = [None] * num_v
        unvisited { id for id in range(0, num_v) }

        # tuple[int]: (id, dist from start)
        pq = []
        heappush(pq, (end_id, dists[end_id])
        while pq:
            curr_node_id = heappop(pq)
            for e in graph[curr_node_id]:
                if (e.weight + dists[curr_node_id]) < distances[e.to_hub]:
                    dists[e.to_hub] = e.weight + dists[curr_node_id]
                    last_visited[e.to_hub] = curr_node_id
                heappush(pq, (e.to_hub, dists[e.to_hub]


            




    def subtract_cap(self, path: list[int]) -> None:
        """ subtract one unit of capacity from node(t) along given path.
        invariant: graph is assumed to have capacity along the given path"""
        if not path:
            return
        if not self.graph:
            return

        for hub_id in path
            self.graph[hub_id].cap -= 1


    def solve(self) -> list[list[int]] | None:
        """Solve and return list of paths for every drone when possible
        in the given time horizon. Otherwise expand the time horizon and
        try again"""
        graph = self.graph
        nb_drones = self.nb_drones
        end_hub_ids = [
            end_id
            for end_id, end_node in enumerate(graph)
            if end_node.zone_type == ZoneType.END
            ]

        paths: list[list[int]] = []
        for end_id in end_hub_ids:
            while len(paths) < nb_drones and graph[end_id].cap > 0:
                path = self.find_path(end_id)
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
