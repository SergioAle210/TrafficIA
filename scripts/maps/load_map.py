"""Load a CARLA town from the command line."""

import argparse
import sys

import carla


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 2000
CLIENT_TIMEOUT_SECONDS = 30.0


def short_map_name(map_name: str) -> str:
    """Extract a lowercase map name from CARLA's full map path."""
    return map_name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def parse_args() -> argparse.Namespace:
    """Read the map name requested on the command line."""
    parser = argparse.ArgumentParser(
        description="Carga un mapa en una instancia local de CARLA 0.9.15."
    )
    parser.add_argument("--town", default="Town03", help="Mapa que se cargará.")
    return parser.parse_args()


def main() -> int:
    """Connect to CARLA, load the requested map, and report any connection or loading error."""
    args = parse_args()

    try:
        client = carla.Client(DEFAULT_HOST, DEFAULT_PORT)
        client.set_timeout(CLIENT_TIMEOUT_SECONDS)

        current_world = client.get_world()
        current_map_name = current_world.get_map().name
        if short_map_name(current_map_name) == short_map_name(args.town):
            print(f"Mapa ya activo: {current_map_name}. No se recargará.")
            return 0

        print(f"Cargando mapa: {args.town}")
        world = client.load_world(args.town)
        print("Mapa cargado:", world.get_map().name)
        return 0
    except RuntimeError as error:
        print(
            f"No fue posible cargar {args.town} en CARLA: {error}",
            file=sys.stderr,
        )
        print(
            "Verifica que CarlaUE4.exe esté activo en localhost:2000 y que el mapa exista.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
