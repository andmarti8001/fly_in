from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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

    for map_path in map_paths:
        rel_path = map_path.relative_to(ROOT_DIR).as_posix()
        try:
            cfg = Config.from_file(str(map_path))
            # Graph.get_base_graph currently reads `hub.zone_type`.
            # Parsed Hub exposes `zone`; mirror it for compatibility.
            for hub in cfg.hubs:
                hub.zone_type = hub.zone
            graph = Graph(None, None)
            _ = graph.get_base_graph(cfg)
        except Exception as exc:  # pragma: no cover - runner script
            failures.append((rel_path, str(exc)))
            print(f"[FAIL] {rel_path}")
            print(f"       {exc}")
        else:
            print(f"[OK]   {rel_path}")

    print()
    print(f"Completed {len(map_paths)} map(s)")
    print(f"Passed: {len(map_paths) - len(failures)}")
    print(f"Failed: {len(failures)}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
