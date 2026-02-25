import sys

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
    ) -> list[list[str]] | None:
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
        for i, p in enumerate(paths):
            for j in range(0, len(p) - 1):
                curr_id = self.get_base_id(p[j], hub_tot)
                next_id = self.get_base_id(p[j + 1], hub_tot)
                if (curr_id < 0 or upper_limit <= curr_id
                    or curr_id < 0 or upper_limit <= curr_id):
                    return None
                if curr_id == next_id:
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
                move = f"D{next_id}-{zone}"
                breakpoint()
                moves[i].append(move)
        print(moves)
        return moves
                
    def normalize_paths(
            self, paths: list[list[int]], hub_tot: int) -> None:
        for p in paths:
            for n in p:
                n = self.get_base_id(n, hub_tot)
                
    def print_output(self, visual_mode: bool = False) -> None:
        if len(sys.argv) != 2:
            print(f"Usage: {sys.argv[0]} <map_file>")
            return

        filename = sys.argv[1]
        cfg = Config.from_file(filename)
        
        graph = Graph(None, None)
        base_graph = graph.get_base_graph(cfg)
        r_expand = graph.get_r_expanded_list(base_graph, 50)
        solver = GraphSolver(r_expand, len(cfg.hubs))
        paths = solver.solve()
        self.normalize_paths(paths, len(cfg.hubs))
        print(self.get_moves(solver.solve(), len(cfg.hubs), cfg))
#        if visual_mode:
#            self.print_visual(solver.solve())


if __name__ == "__main__":
    fly_in = FlyIn()
    fly_in.print_output(visual_mode=False)
