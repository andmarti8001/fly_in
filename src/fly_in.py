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
        return self.get_base_id(vertex_id) >= hub_tot

    @staticmethod
    def print_paths(paths: list[list[int]]) -> None:
        if not paths:
            return

        last_arrival_time = max([len(p) for p in paths])
        moves: list[list[str]] = []

        for i, p in enumerate(paths):
            for j in range(0, len(p) - 1):
                curr_id = p[j]
                next_id = p[j + 1]
                if curr_id == next_id:
                    continue
                move = f"D{i}-{self.get_hub_name(curr_id)}
                

                
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
        self.print_paths(solver.solve()))
        if visual_mode:
            self.print_visual(solver.solve())


if __name__ == "__main__":
    FlyIn.print_output(visual_mode=False)
