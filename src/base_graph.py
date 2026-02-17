
from __future__ import annotations

from collections import deque

from models import Connection, Hub, ZoneType
from parser import Config

class BaseEdge:
    """ The Base Edge class that is the structure
    for the first most simple adjacency list created
    from the config """
    def __init__(
        self,
        to_hub: int,
        max_link_capacity: int
    ) -> None:
        self.to_hub = to_hub
        self.max_link_capacity = max_link_capacity

class BaseGraph:
    """ first most simple graph after the config taken from the parser
    this graph should prune the blocked hubs and give new ids to the
    remaining hubs. then it should do a bfs search along the graph and
    make sure there is at least one valid path from the start to the exit
    if not return a ValueError """
    def __init__ (self, graph: list[list[BaseEdge]]) -> None:
        self.graph = graph

    @staticmethod
    def graph_from_lists(
        hubs: list[Hub],
        connections: list[Connection]
    ) -> list[list[BaseEdge]]:
        """Build an undirected adjacency list from hubs and connections.

        Each hub is represented by its ``Hub.id`` index in the returned list.
        For every input connection, two ``BaseEdge`` entries are added
        (hub1->hub2 and hub2->hub1) with the same ``max_link_capacity``.

        Raises:
            ValueError: If ``hubs`` is empty, hub ids are not contiguous
                starting from zero, or a connection references an unknown hub.
        """
        if not hubs:
            raise ValueError("hubs list must not be empty")
        hub_map = { hub.name: hub.id for hub in hubs }
        if len(hub_map) != len(hubs):
            raise ValueError("Duplicate hub name found")
        max_hub_id = max(hub_map.values())
        len_hubs = len(hubs)
        if len_hubs != max_hub_id + 1:
            raise ValueError("Hub ids must be continuous and start from zero")
        adjacency_list = [[] for _ in range(len(hubs))]
        try:
            for c in connections:
                hub1_id = hub_map[c.hub1]
                hub2_id = hub_map[c.hub2]
                ml_cap = c.max_link_capacity
                adjacency_list[hub1_id].append(BaseEdge(hub2_id, ml_cap))
                adjacency_list[hub2_id].append(BaseEdge(hub1_id, ml_cap))
        except KeyError as e:
            raise ValueError("Unknown name found in connection") from e

        return adjacency_list

    @staticmethod
    def prune_hub_list(hubs: list[Hub]) -> list[Hub]:
        """ takes a list of hubs and prunes any hub of type ZoneType.BLOCKED
        and then also reindexs the hubs so that the returned pruned list of
        hubs has continuous ids starting from zero """

        pruned_hubs = [
            hub
            for hub in hubs
            if hub.zone != ZoneType.BLOCKED
        ]

        for idx, hub in enumerate(pruned_hubs):
            hub.id = idx

        return pruned_hubs

    @staticmethod
    def prune_connection_list(
            connections: list[Connection],
            hubs: list[Hub]
        ) -> list[Connection]:
        """ takes a list of connections and simply removes connections that
        contains hubs of type ZoneType.BLOCKED and checks by referencing the
        given hubs list """

        allowed_names = {
            hub.name
            for hub in hubs
            if hub.zone != ZoneType.BLOCKED
        }

        return [
            c
            for c in connections
            if c.hub1 in allowed_names and c.hub2 in allowed_names
        ]

    @staticmethod
    def has_solution(
        graph: list[list[BaseEdge]],
        start_hub_id: int = 0,
        end_hub_id: int = 1,
    ) -> bool:
        """ returns true if there is at least one valid path
        in the given adjacency list"""
        if not graph:
            return False
        if start_hub_id < 0 or start_hub_id >= len(graph):
            return False
        if end_hub_id < 0 or end_hub_id >= len(graph):
            return False
        if start_hub_id == end_hub_id:
            return True

        visited = [False] * len(graph)
        queue = deque([start_hub_id])
        visited[start_hub_id] = True

        while queue:
            current = queue.popleft()
            for edge in graph[current]:
                nxt = edge.to_hub
                if nxt == end_hub_id:
                    return True
                if not visited[nxt]:
                    visited[nxt] = True
                    queue.append(nxt)
        return False

    @classmethod
    def from_config(cls, cfg: Config) -> BaseGraph:
        """ takes a config and returns an adjacency list
        and prunes blocked zones and checks that the graph
        has one valid solution """
        pruned_hubs = cls.prune_hub_list(cfg.hubs)
        pruned_connections = cls.prune_connection_list(cfg.connections, pruned_hubs)
        graph = cls.graph_from_lists(pruned_hubs, pruned_connections)

        start_hub_name = cfg.start_hub.name
        end_hub_name = cfg.end_hub.name
        hub_ids = {hub.name: hub.id for hub in pruned_hubs}
        if start_hub_name not in hub_ids or end_hub_name not in hub_ids:
            raise ValueError("start_hub or end_hub missing after pruning")

        if not cls.has_solution(graph, hub_ids[start_hub_name], hub_ids[end_hub_name]):
            raise ValueError("No valid path from start_hub to end_hub")
        return cls(graph)
