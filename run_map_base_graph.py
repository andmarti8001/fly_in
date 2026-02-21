from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from base_graph import BaseGraph
from parser import Config


def main() -> None:
    if len(sys.argv) != 2:
        script_name = Path(sys.argv[0]).name
        msg = (
            f"Usage: {script_name} <relative_map_path>\n"
            "Example: run_map_base_graph.py maps/easy/01_linear_path.txt"
        )
        raise SystemExit(msg)

    rel_map_path = sys.argv[1]
    map_path = (ROOT_DIR / rel_map_path).resolve()

    if ROOT_DIR not in map_path.parents and map_path != ROOT_DIR:
        raise ValueError("Map path must be relative to project root")
    if not map_path.is_file():
        raise FileNotFoundError(f"Map file not found: {rel_map_path}")

    config = Config.from_file(str(map_path))
    base_graph = BaseGraph.from_config(config)
    base_graph.print()


if __name__ == "__main__":
    main()
