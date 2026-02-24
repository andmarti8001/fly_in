from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graph import Graph
from parser import Config


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        script_name = Path(sys.argv[0]).name
        msg = (
            f"Usage: {script_name} <relative_map_path> [t]\n"
            "Example: print_time_expanded_graph.py maps/easy/01_linear_path.txt 4"
        )
        raise SystemExit(msg)

    rel_map_path = sys.argv[1]
    map_path = (ROOT_DIR / rel_map_path).resolve()

    if ROOT_DIR not in map_path.parents and map_path != ROOT_DIR:
        raise ValueError("Map path must be relative to project root")
    if not map_path.is_file():
        raise FileNotFoundError(f"Map file not found: {rel_map_path}")

    cfg = Config.from_file(str(map_path))
    for hub in cfg.hubs:
        # graph.py currently expects `zone_type`.
        hub.zone_type = hub.zone

    graph = Graph(None, None)
    base_graph = graph.get_base_graph(cfg)

    if len(sys.argv) == 3:
        t = int(sys.argv[2])
        if t < 1:
            raise ValueError("t must be >= 1")
    else:
        t = max(1, len(cfg.hubs))

    expanded = graph.get_expanded_list(base_graph, t)
    graph.print_expanded_graph(expanded, t)


if __name__ == "__main__":
    main()
