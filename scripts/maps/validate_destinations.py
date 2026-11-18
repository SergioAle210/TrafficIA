"""Validate that every configured destination is reachable in the active CARLA map."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.demand.destinations import load_destinations
from src.navigation.route_planner import (
    build_global_route_planner,
    configure_carla_agents,
    plan_route,
    route_distance_m,
)
from src.simulation.trip_runner import resolve_destination_location


def parse_args() -> argparse.Namespace:
    """Read the map, origin, catalog, and CARLA API options for destination validation."""
    parser = argparse.ArgumentParser(
        description="Valida referencias y rutas desde un origen hacia todos los destinos."
    )
    parser.add_argument("--town", default="Town01")
    parser.add_argument(
        "--destinations",
        type=Path,
        default=PROJECT_ROOT / "data" / "input" / "catalogs" / "Town01" / "destinations_config.csv",
    )
    parser.add_argument("--origin-id", default="T01_133")
    parser.add_argument("--sampling-resolution", type=float, default=2.0)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--carla-pythonapi",
        type=Path,
        help="Carpeta de CARLA que contiene agents.",
    )
    return parser.parse_args()


def short_map_name(name: str) -> str:
    """Extract a lowercase map name from CARLA's full map path."""
    return name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def main() -> int:
    """Check destination references and planned routes from the selected origin on the active map."""
    args = parse_args()
    try:
        import carla

        configure_carla_agents(
            carla, str(args.carla_pythonapi) if args.carla_pythonapi else None
        )
        client = carla.Client(args.host, args.port)
        client.set_timeout(30.0)
        world = client.get_world()
        carla_map = world.get_map()
        if short_map_name(carla_map.name) != short_map_name(args.town):
            raise RuntimeError(
                "El mapa activo es {0}; se esperaba {1}.".format(carla_map.name, args.town)
            )
        destinations = load_destinations(args.destinations, carla_map.name)
        by_id = {destination.destination_id: destination for destination in destinations}
        if args.origin_id not in by_id:
            raise ValueError("El origen no existe en el catálogo: {0}".format(args.origin_id))

        planner = build_global_route_planner(carla_map, args.sampling_resolution)
        origin = resolve_destination_location(carla, carla_map, by_id[args.origin_id])
        failures = []
        route_lengths = []
        for destination in destinations:
            if destination.destination_id == args.origin_id:
                continue
            try:
                location = resolve_destination_location(carla, carla_map, destination)
                route = plan_route(planner, origin, location)
                length_m = route_distance_m(route)
                route_lengths.append((destination.destination_id, length_m))
                print("OK {0}: {1:.1f} m".format(destination.destination_id, length_m))
            except (RuntimeError, ValueError) as error:
                failures.append((destination.destination_id, str(error)))
                print("ERROR {0}: {1}".format(destination.destination_id, error))

        print(
            "Resumen: {0} rutas válidas, {1} fallidas desde {2}.".format(
                len(route_lengths), len(failures), args.origin_id
            )
        )
        if route_lengths:
            longest = max(route_lengths, key=lambda item: item[1])
            print("Ruta más larga: {0} ({1:.1f} m).".format(longest[0], longest[1]))
        return 1 if failures else 0
    except (FileNotFoundError, ModuleNotFoundError, RuntimeError, ValueError) as error:
        print("Error de validación: {0}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
