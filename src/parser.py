# andmarti
#
# NOTE assignment text says hub coordinates should be positive integers.
# However, several provided school map files include negative coordinates.
# This parser intentionally accepts negative hub coordinates to stay compatible
# with those official provided maps.

from __future__ import annotations

from typing import Any
from models import Connection, Hub, Metadata, ZoneType


class Config:
    def __init__(
            self,
            nb_drones: int,
            start_hub: Hub,
            end_hub: Hub,
            hubs: list[Hub],
            connections: list[Connection],
            ) -> None:
        self.nb_drones = nb_drones
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.hubs = hubs
        self.connections = connections

    @staticmethod
    def _validate_names(cfg: Config) -> Config:
        """ checks that all hubs have unique names and that
        all connections have valid names """
        names_set = set()

        names_list = [
                hub.name
                for hub in cfg.hubs
                ]

        for name in names_list:
            if name in names_set:
                raise ValueError("Duplicate name found for hub")
            names_set.add(name)

        connection_names = [
                connection.hub1
                for connection in cfg.connections
                ]
        connection_names += [
                connection.hub2
                for connection in cfg.connections
                ]

        for name in connection_names:
            if name not in names_set:
                raise ValueError("Invalid name found in connections")

        return cfg

    @classmethod
    def from_file(cls, filename: str) -> Config:
        """Parse a config map file and return a populated ``Config``.

        Expected directives:
        - ``nb_drones: <positive_integer>`` (single occurrence)
        - ``start_hub: ...`` (single occurrence)
        - ``end_hub: ...`` (single occurrence)
        - ``hub: ...`` (zero or more)
        - ``connection: ...`` (zero or more)

        Validation performed here:
        - Ignores blank lines and comment lines starting with ``#``.
        - Requires ``:`` on every non-comment directive line.
        - Rejects unknown directive keys.
        - Rejects duplicate directives for no-duplicate keys.
        - Ensures required directives exist before constructing ``Config``.

        Per-directive semantic validation is delegated to:
        ``_parse_nb_drones``, ``_parse_hub``, and ``_parse_connection``.
        """
        Hub.reset_next_id()
        try:
            all_keys: dict[str, dict[str, Any]] = {
                "nb_drones": {
                    "func": cls._parse_nb_drones,
                    "no_dup": True,
                    "required": True,
                    "val": None,
                },
                "start_hub": {
                    "func": cls._parse_hub,
                    "no_dup": True,
                    "required": True,
                    "val": None,
                },
                "end_hub": {
                    "func": cls._parse_hub,
                    "no_dup": True,
                    "required": True,
                    "val": None,
                },
                "hub": {
                    "func": cls._parse_hub,
                    "no_dup": False,
                    "required": False,
                    "val": [],
                },
                "connection": {
                    "func": cls._parse_connection,
                    "no_dup": False,
                    "required": False,
                    "val": [],
                },
            }

            no_dup: set[str] = set()
            with open(filename, 'r', encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line == "":
                        continue
                    elif line[0] == '#':
                        continue
                    if ":" not in line:
                        raise ValueError("No ':' character in line")
                    key, value_str = line.split(":", 1)
                    key = key.strip()
                    if key not in all_keys:
                        err_str = "Key must be 'nb_drones', "
                        err_str += "'start_hub', 'end_hub', 'hub', "
                        err_str += "or 'connection'"
                        raise ValueError(err_str)
                    if key in no_dup:
                        raise ValueError(f"{key} must not have duplicate configs")
                    if all_keys[key]["no_dup"]:
                        no_dup.add(key)
                    if key in {"start_hub", "end_hub"}:
                        hub = all_keys[key]["func"](value_str, key)
                        all_keys["hub"]["val"].append(hub)
                        all_keys[key]["val"] = hub
                    elif key in {"hub", "connection"}:
                        parser_func = all_keys[key]["func"]
                        all_keys[key]["val"].append(parser_func(value_str))
                    else:
                        all_keys[key]["val"] = all_keys[key]["func"](value_str)

            missing: list[str] = [
                req_key
                for req_key, req_config in all_keys.items()
                if req_config["required"] and req_config["val"] is None
            ]
            if missing:
                missing_str = ", ".join(missing)
                raise ValueError(f"missing required config(s): {missing_str}")

            return Config._validate_names(cls(
                all_keys['nb_drones']['val'],
                all_keys['start_hub']['val'],
                all_keys['end_hub']['val'],
                all_keys['hub']['val'],
                all_keys['connection']['val'],
            ))
        finally:
            Hub.reset_next_id()

    @staticmethod
    def _parse_metadata(
        metadata_token: str,
        obj: str,
    ) -> dict[Metadata, ZoneType | str | int]:
        """ takes a str (ex: " [zone=priority color=green max_drones=3] ")
        and also the object whose metadata that will be parsed. Validates
        Metadata and ZoneType for ZONE, string value for COLOR, and a
        positive integer for MAX_DRONES and MAX_LINK_CAPACITY"""
        token: str = metadata_token.strip()
        parsed: dict[Metadata, ZoneType | str | int] = {}

        if not (obj == "hub"
                or obj == "connection"):
            raise ValueError("Object must be 'hub' or 'connection'")

        if obj == "hub":
            valid_metadata: set[Metadata] = {
                Metadata.ZONE,
                Metadata.COLOR,
                Metadata.MAX_DRONES,
            }
        else:
            valid_metadata: set[Metadata] = {
                Metadata.MAX_LINK_CAPACITY,
            }

        if token == "":
            return parsed

        if not token.startswith("[") or not token.endswith("]"):
            raise ValueError("metadata must be enclosed in []")

        raw_items: str = token[1:-1].strip()
        if raw_items == "":
            return parsed

        for item in raw_items.split():
            key_str: str
            value_str: str

            if "=" not in item:
                raise ValueError("metadata item must be in key=value format")

            key_str, value_str = item.split("=", 1)
            key_str = key_str.strip()
            value_str = value_str.strip()

            if key_str == "" or value_str == "":
                raise ValueError("metadata key and value must be non-empty")
            try:
                key = Metadata(key_str)
            except ValueError as e:
                raise ValueError(f"unsupported metadata key: {key_str}") from e
            if key not in valid_metadata:
                raise ValueError(
                    f"metadata not allowed for {obj}: {key.value}"
                )
            if key in parsed:
                raise ValueError(f"duplicate metadata key: {key.value}")

            if key == Metadata.ZONE:
                try:
                    parsed[key] = ZoneType(value_str)
                except ValueError as e:
                    raise ValueError(
                        f"invalid zone type: {value_str}"
                    ) from e
                continue
            elif key == Metadata.COLOR:
                parsed[key] = value_str
                continue
            elif (key == Metadata.MAX_DRONES
                    or key == Metadata.MAX_LINK_CAPACITY):
                try:
                    value = int(value_str)
                except ValueError as e:
                    raise ValueError(
                        f"metadata {key.value} must be an integer"
                    ) from e

                if value < 1:
                    raise ValueError(
                        f"metadata {key.value} must be a positive integer"
                    )
            parsed[key] = value

        return parsed

    @staticmethod
    def _parse_int(int_str: str) -> int:
        try:
            num = int(int_str)
        except ValueError as e:
            raise ValueError("value_str is an invalid integer") from e
        return num

    @staticmethod
    def _parse_name(name: str) -> str:
        if "-" in name:
            raise ValueError("Name must not include dashes (-)")
        name = name.strip()
        if name == "":
            raise ValueError("Name must not be an empty string")
        return name

    @staticmethod
    def _parse_nb_drones(value_str: str) -> int:
        """Parse and validate the ``nb_drones`` directive payload.

        Validation outline:
        - Trim whitespace.
        - Ensure value is an integer.
        - Ensure value is strictly positive (>= 1).
        - Raise ``ValueError`` on malformed or invalid value.
        """
        nb_drones = Config._parse_int(value_str.strip())
        if nb_drones < 1:
            raise ValueError("No drones given in map")
        return nb_drones

    @staticmethod
    def _parse_hub(value_str: str, s_or_e: str | None = None) -> Hub:
        """Parse and validate a ``start_hub``, ``end_hub``, or ``hub`` payload.
        s_or_e is short for start or end to fit the flake8 standard
        Validation outline:
        - Expect ``<name> <x> <y> [metadata]`` format.
        - Ensure name is non-empty and does not contain ``-``.
        - Ensure ``x`` and ``y`` are integers.
        - Parse optional metadata block with ``_parse_metadata(..., "hub")``.
        - Validate metadata keys and value types (zone/color/max_drones).
        - Raise ``ValueError`` on malformed payload or invalid values.
        """
        params = value_str.strip().split(" ", 3)
        if len(params) < 3:
            err_str = "Invalid number of params. "
            err_str += "usage: hub: <name> <x> <y> [metadata]"
            raise ValueError(err_str)
        if len(params) == 3:
            return Hub(
                Config._parse_name(params[0]),
                Config._parse_int(params[1]),
                Config._parse_int(params[2]),
                ZoneType.NORMAL if s_or_e is None else ZoneType(s_or_e)
                )
        metadata = Config._parse_metadata(params[3], 'hub')
        zone = ZoneType.NORMAL if s_or_e is None else ZoneType(s_or_e)
        if s_or_e and Metadata.ZONE in metadata:
            raise ValueError("Duplicate zones inputted")
        zone = metadata.get(Metadata.ZONE, zone)
        color = metadata.get(Metadata.COLOR)
        max_drones = metadata.get(Metadata.MAX_DRONES, 1)
        return Hub(
            Config._parse_name(params[0]),
            Config._parse_int(params[1]),
            Config._parse_int(params[2]),
            zone,
            color,
            max_drones
            )

    @staticmethod
    def _parse_connection(value_str: str) -> Connection:
        """Parse and validate a ``connection`` directive payload.

        Validation outline:
        - Expect ``<name1>-<name2> [metadata]`` format.
        - Ensure both endpoint names are non-empty and distinct.
        - Parse optional metadata block with
          ``_parse_metadata(..., "connection")``.
        - Validate metadata keys and value types (max_link_capacity).
        - Raise ``ValueError`` on malformed payload or invalid values.
        """
        value_str = value_str.strip()
        if value_str == "":
            raise ValueError("Value string is an empty string")
        params = value_str.split(" ", 1)
        endpoints = params[0].split("-", 1)
        if len(endpoints) != 2:
            raise ValueError("No dash (-) present in connection endpoints")
        if len(params) == 2:
            metadata = Config._parse_metadata(params[1], "connection")
            if not metadata:
                raise ValueError("Empty Metadata")
            max_lc = metadata[Metadata.MAX_LINK_CAPACITY]
        else:
            max_lc = 1
        name1 = Config._parse_name(endpoints[0])
        name2 = Config._parse_name(endpoints[1])
        if name1 == name2:
            err_str = "Connection cannot have same source and destination"
            raise ValueError(err_str)
        return Connection(
            name1,
            name2,
            max_lc
            )

    def print_hubs(self) -> None:
        """Print all hubs line-by-line with a colored status message."""
        Config.print_in_box("Printing hubs")
        for idx, hub in enumerate(self.hubs):
            hub.print()
            if idx < len(self.hubs) - 1:
                print()

    def print_connections(self) -> None:
        """Print all connections line-by-line with a colored status message."""
        Config.print_in_box("Printing connections")
        for idx, connection in enumerate(self.connections):
            connection.print()
            if idx < len(self.connections) - 1:
                print()

    def print(self) -> None:
        """Print all Config attributes with colored section headers."""
        print("\033[95m[CONFIG]\033[0m Printing full configuration")
        print()
        Config.print_in_box("nb_drones")
        print(self.nb_drones)
        print()
        Config.print_in_box("start_hub")
        self.start_hub.print()
        print()
        Config.print_in_box("end_hub")
        self.end_hub.print()
        print()
        self.print_hubs()
        print()
        self.print_connections()

    @staticmethod
    def print_in_box(title: str) -> None:
        """Print a title wrapped in an '=' character box."""
        border = "=" * (len(title) + 4)
        print(border)
        print(f"= {title} =")
        print(border)
