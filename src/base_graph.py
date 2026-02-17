
from __future__ import annotations

from parser import Config
from models import Connection, Hub

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
        pass

    @staticmethod
    def prune_connection_list(
            connections: list[Connection],
            hubs: list[Hub]
        ) -> list[Connection]:
        """ takes a list of connections and simply removes connections that
        contains hubs of type ZoneType.BLOCKED and checks by referencing the
        given hubs list """

        
        
