import sys

from heapq import heappop, heappush 
from graph import Graph
from parser import Config
from solve import GraphSolver

class FlyIn:
    @staticmethod
    def get_base_id(vertex_id: int, hub_tot: int) -> int:
        """Return the time(0) index of any id at any time(t). """
        return vertex_id % (2 * hub_tot)

    def get_base_restrict_from_transit(transit_id: int, hub_tot: int) -> int:
        """ return the id of the original base restricted hub id for
        the given transit_id at any time(t)
        """
        return self.get_base_id(transit_id, hub_tot) - hub_tot

    def is_transit(self, vertex_id: int, hub_tot: int) -> bool:
        """Return True if vertex_id points to the transit half of a layer."""
        return self.get_base_id(vertex_id, hub_tot) >= hub_tot

    def get_moves(
        self,
        paths: list[list[int]],
        hub_tot: int,
        cfg: Config
        ) -> tuple[list[list[str | None]], list[list[int]]] | None:
        """ returns a list of moves from the given path
        in D<ID>-<zone/connection> format. a move is added
        to the list when a drone changes positions and
        waiting is not added to the moves list.

        expected input is a normalized graph with id ranges
        between 0 and 2 * hub_total. so yeah """
        if not paths:
            return
        upper_limit = 2 * hub_tot
        last_arrival_time = max([len(p) for p in paths])
        moves: list[list[str]] = [[] for _ in range(0, len(paths))]
        moves_hubs: list[list[int]] = [[] for _ in range(0, len(paths))]
        for i, p in enumerate(paths):
            for j in range(0, len(p) - 1):
                curr_id = self.get_base_id(p[j], hub_tot)
                next_id = self.get_base_id(p[j + 1], hub_tot)
                if (curr_id < 0 or upper_limit <= curr_id
                    or curr_id < 0 or upper_limit <= curr_id):
                    return None
                if curr_id == next_id:
                    moves[i].append(None)
                    moves_hubs[i].append(curr_id)
                    continue
                # set zone
                if self.is_transit(next_id, hub_tot):
                    even_next_id = p[j + 2]
                    if not even_next_id:
                        return None
                    zone = f"{self.get_base_id(curr_id, hub_tot)}-"
                    zone += f"{self.get_base_id(even_next_id, hub_tot)}"
                else:
                    zone = f"{self.get_base_id(next_id, hub_tot)}"
                zone_hub = self.get_base_id(curr_id, hub_tot)
                move = f"D{i + 1}-{zone}"
                moves[i].append(move)
                moves_hubs[i].append(zone_hub)

        return moves, moves_hubs
   
    @staticmethod
    def print_moves(moves: list[list[str | None]]) -> None:
        most_moves = len(max(moves, key=lambda m: len(m)))
        turns = [[] for _ in range(0, most_moves)]
        for i in range(0, most_moves): 
            for j in range(0, len(moves)):
                # will indexError and this is a issue
                try:
                    if moves[j][i] is None:
                        continue
                    turns[i].append(moves[j][i])
                except:
                    pass

        for turn in turns:
            for drone in turn:
                print(drone, end="")
                if drone != turn[-1]:
                    print(", ", end="")
            print()


    @staticmethod
    def print_moves_hub(moves_hub: list[list[int]], cfg: Config) -> None:
        # initial state
        print("=======================================")
        print("TURN#: 0")
        print("=======================================")
        cfg.hubs[0].print()
        print("=======================================")
        print(f"Current Occupancy: {cfg.nb_drones}")
        print("=======================================")
       
        # moves_hubs to moves by turn without drones IDs
        # cause whatever
        most_moves = len(max(moves_hub, key=lambda m: len(m)))
        turns = [[] for _ in range(0, most_moves)]
        for i in range(0, most_moves): 
            for j in range(0, len(moves_hub)):
                # will indexError and this is a issue
                # fix later
                try:
                    if moves_hub[j][i] is None:
                        continue
                    turns[i].append(moves_hub[j][i])
                except:
                    pass
        breakpoint()
        turn_pq = []
        for num_turn, turn in enumerate(turns):
            print()
            print("=======================================")
            print(f"TURN#: {num_turn + 1}")
            print("=======================================")
            hubs = { hub for hub in turn }
            for hub in hubs:
                heappush(turn_pq, (hub, len([h 
                    for h in turn if (h == hub and h is not None)])))
            while turn_pq:
                h = heappop(turn_pq)
                hub_id = h[0]
                cap = h[1]
                cfg.hubs[hub_id].print()
                print("=======================================")
                print(f"Current Occupancy: {cap}")
                print("=======================================")
            

    def print_output(self, visual_mode: bool = False) -> None:
        if len(sys.argv) != 2:
            print(f"Usage: {sys.argv[0]} <map_file>")
            return

        filename = sys.argv[1]
        cfg = Config.from_file(filename)
        
            
        graph = Graph(None, None)
        base_graph = graph.get_base_graph(cfg)
        r_expand = graph.get_r_expanded_list(base_graph, 50)
        solver = GraphSolver(r_expand, cfg.nb_drones)
        paths = solver.solve()
        moves_tup = self.get_moves(paths, len(cfg.hubs), cfg)
        moves = moves_tup[0]
        moves_hubs= moves_tup[1]
        self.print_moves(moves)
        if visual_mode:
            self.print_moves_hub(moves_hubs, cfg)


if __name__ == "__main__":
    fly_in = FlyIn()
    fly_in.print_output(visual_mode=True)
