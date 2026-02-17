from __future__ import annotations

# This suite is "strong" for project scope: broad deterministic regression tests,
# edge cases, and stress-style checks. CI/fuzz/mutation are a different layer:
# CI runs tests automatically on every change, fuzzing continuously generates new
# random/malformed inputs, and mutation testing alters code to verify test strength.
# Those are recommended hardening steps beyond typical school-project scope.

import random
import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parser import Config, Metadata, ZoneType


def test_parse_metadata_hub_valid() -> None:
    result = Config._parse_metadata(
        "[zone=priority color=green max_drones=3]",
        "hub",
    )

    assert result[Metadata.ZONE] == ZoneType.PRIORITY
    assert result[Metadata.COLOR] == "green"
    assert result[Metadata.MAX_DRONES] == 3


def test_parse_metadata_connection_valid() -> None:
    result = Config._parse_metadata("[max_link_capacity=2]", "connection")

    assert result == {Metadata.MAX_LINK_CAPACITY: 2}


def test_parse_metadata_empty_returns_empty_dict() -> None:
    assert Config._parse_metadata("", "hub") == {}


def test_parse_metadata_rejects_invalid_object() -> None:
    with pytest.raises(
        ValueError,
        match="Object must be 'hub' or 'connection'",
    ):
        Config._parse_metadata("[zone=normal]", "edge")


def test_parse_metadata_rejects_metadata_not_allowed_for_object() -> None:
    with pytest.raises(ValueError, match="metadata not allowed for connection"):
        Config._parse_metadata("[zone=normal]", "connection")


def test_parse_metadata_rejects_invalid_zone_type() -> None:
    with pytest.raises(ValueError, match="invalid zone type"):
        Config._parse_metadata("[zone=fast]", "hub")


def test_parse_metadata_rejects_non_integer_capacity() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        Config._parse_metadata("[max_link_capacity=abc]", "connection")


def test_parse_metadata_rejects_non_positive_integer() -> None:
    with pytest.raises(ValueError, match="must be a positive integer"):
        Config._parse_metadata("[max_drones=0]", "hub")


def test_parse_metadata_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="duplicate metadata key"):
        Config._parse_metadata("[color=red color=blue]", "hub")


def test_parse_metadata_unknown_color_is_preserved() -> None:
    result = Config._parse_metadata("[color=madeupshade]", "hub")
    assert result[Metadata.COLOR] == "madeupshade"


def test_parse_nb_drones_valid_integer() -> None:
    assert Config._parse_nb_drones("5") == 5


def test_parse_nb_drones_valid_with_whitespace() -> None:
    assert Config._parse_nb_drones("  12  ") == 12


def test_parse_nb_drones_rejects_non_integer() -> None:
    with pytest.raises(ValueError, match="invalid integer"):
        Config._parse_nb_drones("abc")


def test_parse_nb_drones_rejects_zero() -> None:
    with pytest.raises(ValueError, match="No drones given in map"):
        Config._parse_nb_drones("0")


def test_parse_nb_drones_rejects_negative() -> None:
    with pytest.raises(ValueError, match="No drones given in map"):
        Config._parse_nb_drones("-3")


def test_parse_hub_valid_minimal() -> None:
    hub = Config._parse_hub("roof1 0 4")

    assert hub.name == "roof1"
    assert hub.x == 0
    assert hub.y == 4
    assert hub.zone == ZoneType.NORMAL
    assert hub.color is None
    assert hub.max_drones == 1


def test_parse_hub_valid_with_metadata() -> None:
    hub = Config._parse_hub("roof1 3 4 [zone=priority color=green max_drones=2]")

    assert hub.name == "roof1"
    assert hub.x == 3
    assert hub.y == 4
    assert hub.zone == ZoneType.PRIORITY
    assert hub.color == "green"
    assert hub.max_drones == 2


def test_parse_hub_rejects_dash_in_name() -> None:
    with pytest.raises(ValueError, match="must not include dashes"):
        Config._parse_hub("roof-1 3 4")


def test_parse_hub_allows_negative_coordinate() -> None:
    hub = Config._parse_hub("roof1 -1 4")

    assert hub.name == "roof1"
    assert hub.x == -1
    assert hub.y == 4
    assert hub.zone == ZoneType.NORMAL
    assert hub.color is None
    assert hub.max_drones == 1


def test_parse_connection_valid_minimal() -> None:
    connection = Config._parse_connection("roof1-goal")

    assert connection.hub1 == "roof1"
    assert connection.hub2 == "goal"
    assert connection.max_link_capacity == 1


def test_parse_connection_valid_with_metadata() -> None:
    connection = Config._parse_connection("roof1-goal [max_link_capacity=2]")

    assert connection.hub1 == "roof1"
    assert connection.hub2 == "goal"
    assert connection.max_link_capacity == 2


def test_parse_connection_rejects_missing_dash() -> None:
    with pytest.raises(ValueError, match="No dash"):
        Config._parse_connection("roof1 goal")


def test_parse_connection_rejects_same_endpoints() -> None:
    with pytest.raises(ValueError, match="same source and destination"):
        Config._parse_connection("roof1-roof1")


def test_parse_connection_rejects_dash_in_name() -> None:
    with pytest.raises(ValueError, match="must not include dashes"):
        Config._parse_connection("roof-1-goal")


# 2nd round inspection: additional regression tests (expected to fail today)
# note: negative coordinates are intentionally accepted (spec drift).
def test_round2_parse_connection_empty_metadata_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Empty Metadata"):
        Config._parse_connection("roof1-goal []")


def test_round2_parse_hub_missing_fields_raises_value_error() -> None:
    with pytest.raises(ValueError):
        Config._parse_hub("roof1 1")


def test_round2_parse_hub_allows_negative_coordinates_spec_drift() -> None:
    hub = Config._parse_hub("roof1 -1 4")
    assert hub.x == -1


def test_round2_parse_metadata_preserves_unknown_color_string() -> None:
    result = Config._parse_metadata("[color=madeupshade]", "hub")
    assert result[Metadata.COLOR] == "madeupshade"


def test_round2_from_file_rejects_connection_to_undefined_hub(
    tmp_path: Path,
) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "end_hub: goal 1 1",
            "connection: start-missing",
        ]
    )
    config_path = tmp_path / "invalid_undefined_connection.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError):
        Config.from_file(str(config_path))


# 3rd round inspection: deeper edge-case coverage
def test_round3_parse_hub_metadata_out_of_order_is_valid() -> None:
    hub = Config._parse_hub("roof1 1 2 [max_drones=4 color=blue zone=priority]")

    assert hub.name == "roof1"
    assert hub.x == 1
    assert hub.y == 2
    assert hub.zone == ZoneType.PRIORITY
    assert hub.color == "blue"
    assert hub.max_drones == 4


def test_round3_parse_connection_rejects_empty_left_endpoint() -> None:
    with pytest.raises(ValueError, match="empty string"):
        Config._parse_connection("-goal")


def test_round3_parse_connection_rejects_empty_right_endpoint() -> None:
    with pytest.raises(ValueError, match="empty string"):
        Config._parse_connection("start-")


def test_round3_parse_hub_rejects_unbracketed_metadata() -> None:
    with pytest.raises(ValueError, match="metadata must be enclosed in"):
        Config._parse_hub("roof1 1 2 zone=normal")


def test_round3_from_file_rejects_duplicate_name_start_and_hub(
    tmp_path: Path,
) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: same 0 0",
            "hub: same 1 1",
            "end_hub: goal 2 2",
        ]
    )
    config_path = tmp_path / "invalid_duplicate_start_hub_name.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate name"):
        Config.from_file(str(config_path))


def test_round3_from_file_rejects_duplicate_name_start_and_end(
    tmp_path: Path,
) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 1",
            "start_hub: same 0 0",
            "end_hub: same 2 2",
        ]
    )
    config_path = tmp_path / "invalid_duplicate_start_end_name.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate name"):
        Config.from_file(str(config_path))


# 4th round inspection: larger edge-case suite for parser hardening
def test_round4_parse_metadata_allows_extra_whitespace() -> None:
    result = Config._parse_metadata(
        "[  zone=normal   color=green   max_drones=4  ]",
        "hub",
    )
    assert result[Metadata.ZONE] == ZoneType.NORMAL
    assert result[Metadata.COLOR] == "green"
    assert result[Metadata.MAX_DRONES] == 4


def test_round4_parse_metadata_rejects_missing_equals() -> None:
    with pytest.raises(ValueError, match="key=value"):
        Config._parse_metadata("[zone priority]", "hub")


def test_round4_parse_hub_rejects_non_integer_coordinate() -> None:
    with pytest.raises(ValueError, match="invalid integer"):
        Config._parse_hub("roof1 a 4")


def test_round4_parse_hub_rejects_non_integer_max_drones() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        Config._parse_hub("roof1 1 2 [max_drones=abc]")


def test_round4_parse_connection_rejects_unbracketed_metadata() -> None:
    with pytest.raises(ValueError, match="metadata must be enclosed in"):
        Config._parse_connection("roof1-goal max_link_capacity=2")


def test_round4_parse_connection_rejects_zero_capacity() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        Config._parse_connection("roof1-goal [max_link_capacity=0]")


def test_round4_from_file_accepts_comments_and_blank_lines(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "# comment line",
            "",
            "nb_drones: 2",
            "",
            "start_hub: start 0 0",
            "hub: mid 1 1",
            "end_hub: goal 2 2",
            "connection: start-mid",
            "connection: mid-goal",
            "",
        ]
    )
    config_path = tmp_path / "valid_with_comments.txt"
    config_path.write_text(config_content, encoding="utf-8")

    cfg = Config.from_file(str(config_path))
    assert cfg.nb_drones == 2
    assert cfg.start_hub.name == "start"
    assert cfg.start_hub.zone == ZoneType.START
    assert cfg.end_hub.name == "goal"
    assert cfg.end_hub.zone == ZoneType.END
    assert len(cfg.hubs) == 3
    assert len(cfg.connections) == 2


def test_round4_from_file_rejects_unknown_key(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 2",
            "start_hub: start 0 0",
            "end_hub: goal 1 1",
            "portal: p1 3 3",
        ]
    )
    config_path = tmp_path / "invalid_unknown_key.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Key must be"):
        Config.from_file(str(config_path))


def test_round4_from_file_rejects_missing_colon(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 2",
            "start_hub start 0 0",
            "end_hub: goal 1 1",
        ]
    )
    config_path = tmp_path / "invalid_missing_colon.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="No ':' character in line"):
        Config.from_file(str(config_path))


def test_round4_from_file_rejects_duplicate_start_hub_line(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 2",
            "start_hub: start 0 0",
            "start_hub: start2 1 1",
            "end_hub: goal 2 2",
        ]
    )
    config_path = tmp_path / "invalid_duplicate_start_hub_line.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="start_hub must not have duplicate"):
        Config.from_file(str(config_path))


def test_round4_from_file_rejects_missing_required_end_hub(tmp_path: Path) -> None:
    config_content = "\n".join(
        [
            "nb_drones: 2",
            "start_hub: start 0 0",
            "hub: mid 1 1",
        ]
    )
    config_path = tmp_path / "invalid_missing_end_hub.txt"
    config_path.write_text(config_content, encoding="utf-8")

    with pytest.raises(ValueError, match="missing required config"):
        Config.from_file(str(config_path))


# 5th round inspection: mutation-style + fuzz/property + stress tests
def test_round5_mutation_boundary_nb_drones_one_is_valid() -> None:
    assert Config._parse_nb_drones("1") == 1


def test_round5_mutation_boundary_max_drones_one_is_valid() -> None:
    metadata = Config._parse_metadata("[max_drones=1]", "hub")
    assert metadata[Metadata.MAX_DRONES] == 1


def test_round5_mutation_connection_capacity_one_is_valid() -> None:
    conn = Config._parse_connection("a-b [max_link_capacity=1]")
    assert conn.max_link_capacity == 1


def test_round5_property_parse_nb_drones_random_values() -> None:
    rng = random.Random(20260217)
    for _ in range(120):
        val = rng.randint(-2000, 2000)
        token = str(val)
        if val >= 1:
            assert Config._parse_nb_drones(token) == val
        else:
            with pytest.raises(ValueError):
                Config._parse_nb_drones(token)


def test_round5_property_parse_hub_random_coords_roundtrip() -> None:
    rng = random.Random(424242)
    for i in range(80):
        x = rng.randint(-500, 500)
        y = rng.randint(-500, 500)
        hub = Config._parse_hub(f"h{i} {x} {y}")
        assert hub.name == f"h{i}"
        assert hub.x == x
        assert hub.y == y
        assert hub.zone == ZoneType.NORMAL
        assert hub.max_drones == 1


def test_round5_property_parse_metadata_random_unknown_colors_preserved() -> None:
    rng = random.Random(777)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(60):
        size = rng.randint(6, 14)
        color = "".join(rng.choice(alphabet) for _ in range(size))
        result = Config._parse_metadata(f"[color={color}]", "hub")
        assert result[Metadata.COLOR] == color


def test_round5_stress_from_file_large_generated_map(tmp_path: Path) -> None:
    hub_count = 250
    lines = [
        "nb_drones: 25",
        "start_hub: start 0 0 [color=green]",
    ]
    for idx in range(hub_count):
        lines.append(f"hub: h{idx} {idx} {-idx} [color=blue]")
    lines.append("end_hub: goal 999 -999 [color=red]")
    lines.append("connection: start-h0")
    for idx in range(hub_count - 1):
        lines.append(f"connection: h{idx}-h{idx + 1}")
    lines.append(f"connection: h{hub_count - 1}-goal [max_link_capacity=2]")

    config_path = tmp_path / "stress_large_generated_map.txt"
    config_path.write_text("\n".join(lines), encoding="utf-8")

    cfg = Config.from_file(str(config_path))
    assert cfg.nb_drones == 25
    assert cfg.start_hub.name == "start"
    assert cfg.start_hub.zone == ZoneType.START
    assert cfg.end_hub.name == "goal"
    assert cfg.end_hub.zone == ZoneType.END
    assert len(cfg.hubs) == hub_count + 2
    assert len(cfg.connections) == hub_count + 1


def test_parse_start_hub_with_metadata_keeps_start_zone() -> None:
    hub = Config._parse_hub("start 0 0 [color=green max_drones=9]", "start_hub")
    assert hub.zone == ZoneType.START
    assert hub.color == "green"
    assert hub.max_drones == 9


def test_parse_end_hub_rejects_duplicate_zone_input() -> None:
    with pytest.raises(ValueError, match="Duplicate zones inputted"):
        Config._parse_hub("goal 1 1 [zone=priority]", "end_hub")
