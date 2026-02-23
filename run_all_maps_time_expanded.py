from __future__ import annotations

import sys
import time
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
    total_time_s = 0.0

    for map_path in map_paths:
        rel_path = map_path.relative_to(ROOT_DIR).as_posix()
        started = time.perf_counter()
        try:
            cfg = Config.from_file(str(map_path))
            for hub in cfg.hubs:
                # Graph currently reads `hub.zone_type`.
                hub.zone_type = hub.zone
            graph = Graph(None, None)
            base_graph = graph.get_base_graph(cfg)
            # Use hub count as time horizon to stress multi-layer expansion.
            t = max(1, len(cfg.hubs))
            _ = graph.get_expanded_list(base_graph, t)
        except Exception as exc:  # pragma: no cover - runner script
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            failures.append((rel_path, str(exc)))
            print(f"[FAIL] {rel_path} ({elapsed_ms:.3f} ms)")
            print(f"       {exc}")
        else:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            total_time_s += elapsed_ms / 1000.0
            print(f"[OK]   {rel_path} ({elapsed_ms:.3f} ms)")

    print()
    print(f"Completed {len(map_paths)} map(s)")
    print(f"Passed: {len(map_paths) - len(failures)}")
    print(f"Failed: {len(failures)}")
    print(f"Total expansion time: {total_time_s * 1000.0:.3f} ms")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
