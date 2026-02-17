from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parser import Config


MAP_PATHS: tuple[str, ...] = (
    "maps/easy/01_linear_path.txt",
    "maps/easy/02_simple_fork.txt",
    "maps/easy/03_basic_capacity.txt",
    "maps/medium/01_dead_end_trap.txt",
    "maps/medium/02_circular_loop.txt",
    "maps/medium/03_priority_puzzle.txt",
    "maps/hard/01_maze_nightmare.txt",
    "maps/hard/02_capacity_hell.txt",
    "maps/hard/03_ultimate_challenge.txt",
    "maps/challenger/01_the_impossible_dream.txt",
)


def main() -> None:
    failures: list[tuple[str, str]] = []

    for rel_path in MAP_PATHS:
        map_path = ROOT_DIR / rel_path
        try:
            Config.from_file(str(map_path))
        except Exception as exc:  # pragma: no cover - runner script
            failures.append((rel_path, str(exc)))
            print(f"[FAIL] {rel_path}")
            print(f"       {exc}")
        else:
            print(f"[OK]   {rel_path}")

    print()
    print(f"Completed {len(MAP_PATHS)} map(s)")
    print(f"Passed: {len(MAP_PATHS) - len(failures)}")
    print(f"Failed: {len(failures)}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
