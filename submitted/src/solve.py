# andmarti

from __future__ import annotations

from heapq import heappop, heappush
from math import inf
from graph import Vertex
from models import ZoneType


class GraphSolver:
    def __init__(self, graph: list[Vertex], nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones

    def find_path(self, end_id: int) -> list[int] | None:
        """Return the shortest path from start to given end_id
        Runs dijkstra through a reverse time expanded adjacency list
        but returns the steps of the path from t(0) to t(arrival @ end_id)
        """
        graph = self.graph
        num_v = len(graph)
        start_id = 0

        # input errors
        if (num_v < 1 or end_id == start_id):
            return None
        if (end_id < 0 or num_v <= end_id):
            return None

        dists = [inf] * num_v
        dists[end_id] = 0
        last_visited: list[int | None] = [None] * num_v
        last_visited[end_id] = None

        # tuple[int]: (dist from start, id)
        # heapq does priority queue functions on the first element
        # and if there is a tie continues along the given tuple
        pq: list[tuple[float | int, int]] = []
        heappush(pq, (dists[end_id], end_id))
        while pq:
            curr_node_id = heappop(pq)[1]
            if graph[curr_node_id].cap <= 0:
                continue
            for e in graph[curr_node_id].edges:
                if e.cap <= 0:
                    continue
                if (e.weight + dists[curr_node_id]) < dists[e.to_hub]:
                    dists[e.to_hub] = e.weight + dists[curr_node_id]
                    last_visited[e.to_hub] = curr_node_id
                    heappush(pq, (dists[e.to_hub], e.to_hub))
        if last_visited[start_id] is None:
            return None
        curr: int | None = start_id
        path = []
        while curr is not None:
            path.append(curr)
            curr = last_visited[curr]
        if len(path) == 0:
            return None
        return path

    def subtract_cap(self, path: list[int]) -> None:
        """ Subtract one unit of capacity from nodes and connections
        along given path.

        invariants: start and end have infinite capacity
        """
        graph = self.graph
        if not path:
            return
        if not graph:
            return

        for i in range(0, len(path)):
            hub_id = path[i]
            if i == len(path) - 1:
                next_hub_id = None
            else:
                next_hub_id = path[i + 1]

            zone_type = graph[hub_id].zone_type
            if (zone_type == ZoneType.START
                    or zone_type == ZoneType.END):
                continue
            if graph[hub_id].cap > 0:
                graph[hub_id].cap -= 1
            if next_hub_id is None:
                continue
            for e in graph[hub_id].edges:
                if (e.to_hub == next_hub_id and e.cap > 0):
                    e.cap -= 1
                    break

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
