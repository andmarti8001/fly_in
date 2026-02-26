# andmarti

import sys

from graph import Graph
from parser import Config
from models import ZoneType
from solve import GraphSolver


class FlyIn:
    @staticmethod
    def get_base_id(vertex_id: int, hub_tot: int) -> int:
        """Return the time(0) index of any id at any time(t). """
        return vertex_id % (2 * hub_tot)

    @staticmethod
    def get_r_id(vertex_id: int, hub_tot: int) -> int:
        """Return the transit-partner id for a restricted node."""
        return vertex_id + hub_tot

    def get_id_time(self, vertex_id: int, t: int, hub_tot: int) -> int:
        """Map a base vertex to its time-t partner """
        return t * (2 * hub_tot) + self.get_base_id(vertex_id, hub_tot)

    def get_base_restrict_from_transit(
            self, transit_id: int, hub_tot: int) -> int:
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
        cfg: Config,
        verbose: bool = False
    ) -> list[list[str | None]]:
        """ returns a list of moves from the given path
        in D<ID>-<zone/connection> format. a move is added
        to the list when a drone changes positions and
        waiting is not added to the moves list.

        expected input is a normalized graph with id ranges
        between 0 and 2 * hub_total. so yeah """
        if not paths:
            raise ValueError("Paths not inputted")
        upper_limit = 2 * hub_tot
        moves: list[list[str | None]] = [[] for _ in range(0, len(paths))]
        for i, p in enumerate(paths):
            for j in range(0, len(p) - 1):
                curr_id = self.get_base_id(p[j], hub_tot)
                next_id = self.get_base_id(p[j + 1], hub_tot)
                if (curr_id < 0 or upper_limit <= curr_id
                        or curr_id < 0 or upper_limit <= curr_id):
                    raise ValueError("index out of range")
                if curr_id == next_id:
                    moves[i].append(None)
                    continue
                # set zone
                if self.is_transit(next_id, hub_tot):
                    even_next_id = p[j + 2]
                    if not even_next_id:
                        raise ValueError("should have restricted node")
                    zone = f"{self.get_base_id(curr_id, hub_tot)}-"
                    zone += f"{self.get_base_id(even_next_id, hub_tot)}"
                else:
                    zone = f"{self.get_base_id(next_id, hub_tot)}"
                move = f"D{i + 1}-{zone}"
                moves[i].append(move)

        return moves

    @staticmethod
    def print_moves(
        moves: list[list[str | None]],
        verbose: bool = False
    ) -> None:
        if verbose:
            print("************************************************")
            print("OUTPUTOUTPUTOUTPUTOUTPUTOUTPUTOUTPUTOUTPUTOUTPUT")
            print("************************************************")
        most_moves = len(max(moves, key=lambda m: len(m)))
        turns: list[list[str | None]] = [[] for _ in range(0, most_moves)]
        for i in range(0, most_moves):
            for j in range(0, len(moves)):
                # will indexError and this is a issue
                try:
                    if moves[j][i] is None:
                        continue
                    turns[i].append(moves[j][i])
                except Exception:
                    pass

        for turn in turns:
            for drone in turn:
                print(drone, end="")
                if drone != turn[-1]:
                    print(", ", end="")
            print()

    @staticmethod
    def print_oc(oc: int) -> None:
        print(f"current occupancy: {oc}")

    @staticmethod
    def print_oc_transit(oc: int) -> None:
        print(f"current in-transit occupancy: {oc}")

    def print_states(
        self,
        paths: list[list[int]],
        cfg: Config,
        verbose: bool = False
    ) -> None:
        if verbose:
            print("*********************************************")
            print("VISUALIZEVISUALIZEVISUALIZEVISUALIZEVISUALIZE")
            print("*********************************************")
        # positions... poss pronounced ('pah' 'zez')
        poss: list[int] = [p for path in paths for p in path]
        max_moves = len(max(paths, key=lambda p: len(p))) - 1
        hub_tot = len(cfg.hubs)
        total_arrived = 0
        print()
        for i in range(0, max_moves + 1):
            print("==================")
            print(f"== TURN #: {i} ==")
            print("==================")
            print()
            if i == 0:
                cfg.hubs[0].short_print()
                self.print_oc(cfg.nb_drones)
                print()
                continue
            elif i == max_moves:
                cfg.hubs[-1].short_print()
                self.print_oc(cfg.nb_drones)
            else:
                for hub in cfg.hubs:
                    if poss.count(self.get_id_time(hub.id, i, hub_tot)) == 0:
                        continue
                    hub.short_print()
                    if hub.zone_type == ZoneType.RESTRICTED:
                        self.print_oc_transit(
                            poss.count(self.get_r_id(
                                            self.get_id_time(
                                                hub.id, i, hub_tot),
                                            hub_tot)))
                    # end has to add up all the ends up until time t
                    # because the paths end even though the drones remain
                    if hub.zone_type == ZoneType.END:
                        total_arrived += poss.count(
                                self.get_id_time(hub.id, i, hub_tot))
                        self.print_oc(total_arrived)
                    else:
                        self.print_oc(
                            poss.count(self.get_id_time(hub.id, i, hub_tot)))

                    print()

    def print_output(self, visual_mode: bool = False) -> None:
        if not (len(sys.argv) == 2
                or len(sys.argv) == 3):
            print(f"Usage: {sys.argv[0]} <flags> <map_file>")
            print("--visual : outputs the states of each zone with a drone")
            return

        if (len(sys.argv) == 3
                and sys.argv[1] != "--visual"):
            print("Incorrect Flag")
            print(f"Usage: {sys.argv[0]} <flags> <map_file>")
            print("--visual : outputs the states of each zone with a drone")
            return

        # get config
        if len(sys.argv) == 3:
            filename = sys.argv[2]
        else:
            filename = sys.argv[1]
        cfg = Config.from_file(filename)

        # get base_graph
        graph = Graph(None, None)
        try:
            base_graph = graph.get_base_graph(cfg)
        except Exception as e:
            print(e)
            return

        # time expand and solve
        # 42 is OUR lucky number
        t = 42
        while True:
            try:
                r_expand = graph.get_r_expanded_list(base_graph, t)
                solver = GraphSolver(r_expand, cfg.nb_drones)
                paths = solver.solve()
                if not paths:
                    t += 10
                    continue
                break
            except Exception:
                t += 10

        # format and print per subject guidelines
        moves = self.get_moves(paths, len(cfg.hubs), cfg)
        self.print_moves(moves)

        # visual representation
        if sys.argv[1] == "--visual":
            self.print_states(paths, cfg)


if __name__ == "__main__":
    try:
        fly_in = FlyIn()
        fly_in.print_output(visual_mode=True)
    except Exception as e:
        print(e)
