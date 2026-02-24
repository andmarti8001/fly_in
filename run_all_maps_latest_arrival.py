from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from GraphSolver import GraphSolver
from graph import Graph
from parser import Config


def _map_paths() -> list[Path]:
    return sorted(
        p for p in (ROOT_DIR / "maps").rglob("*.txt")
        if p.is_file()
    )


def main() -> None:
    map_paths = _map_paths()
    failures: list[tuple[str, str]] = []
    no_solution: list[str] = []

    for map_path in map_paths:
        rel_path = map_path.relative_to(ROOT_DIR).as_posix()
        try:
            cfg = Config.from_file(str(map_path))
            for hub in cfg.hubs:
                hub.zone_type = hub.zone

            graph = Graph(None, None)
            base_graph = graph.get_base_graph(cfg)
            t = max(10, len(cfg.hubs) + cfg.nb_drones)
            graph.g = graph.get_expanded_list(base_graph, t)

            solver = GraphSolver(graph, cfg.nb_drones)
            paths = solver.solve()
            if paths is None:
                no_solution.append(rel_path)
                print(f"[NO-SOLUTION] {rel_path}")
                continue

            layer_size = 2 * graph.hub_tot
            latest_arrival = max(path[-1] // layer_size for path in paths)
            print(f"[OK] {rel_path}: latest_arrival={latest_arrival}")
        except Exception as exc:  # pragma: no cover - runner script
            failures.append((rel_path, str(exc)))
            print(f"[FAIL] {rel_path}")
            print(f"       {exc}")

    print()
    print(f"Completed {len(map_paths)} map(s)")
    print(f"Failed: {len(failures)}")
    print(f"No solution: {len(no_solution)}")
    print(f"Solved: {len(map_paths) - len(failures) - len(no_solution)}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
