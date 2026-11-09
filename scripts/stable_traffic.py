"""Run a small, deterministic Traffic Manager simulation in CARLA 0.9.15."""

import argparse
import math
import random
import sys
from typing import List, Optional

import carla


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 2000
TRAFFIC_MANAGER_PORT = 8000
CLIENT_TIMEOUT_SECONDS = 30.0

SEED = 42
FIXED_DELTA_SECONDS = 0.05
STOPPED_SPEED_KMH = 1.0

EXCLUDED_BLUEPRINT_KEYWORDS = (
    "ambulance",
    "bh",
    "carlacola",
    "crossbike",
    "diamondback",
    "firetruck",
    "fusorosa",
    "harley",
    "kawasaki",
    "sprinter",
    "vespa",
    "yamaha",
)


class ActiveMapMismatchError(Exception):
    """Raised when the active CARLA map differs from the requested validation."""


def positive_int(value: str) -> int:
    """Parse a command-line integer and reject zero or negative values."""
    parsed_value = int(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("el valor debe ser mayor que cero")
    return parsed_value


def parse_args() -> argparse.Namespace:
    """Read the vehicle count and options for the Traffic Manager demonstration."""
    parser = argparse.ArgumentParser(
        description="Ejecuta tráfico estable y reproducible con Traffic Manager."
    )
    parser.add_argument(
        "--town",
        default=None,
        help=(
            "Mapa esperado. Solo valida el mapa activo; no carga ni recarga mapas. "
            "Usa change_map.py para cambiarlo."
        ),
    )
    parser.add_argument(
        "--vehicles",
        type=positive_int,
        default=20,
        help="Cantidad máxima de vehículos que se intentará crear.",
    )
    parser.add_argument(
        "--seconds",
        type=positive_int,
        default=90,
        help="Duración de la simulación en segundos simulados.",
    )
    parser.add_argument(
        "--no-rendering",
        action="store_true",
        help="Desactiva el renderizado para acelerar la simulación.",
    )
    return parser.parse_args()


def speed_kmh(vehicle: carla.Vehicle) -> float:
    """Return a vehicle's current speed in kilometers per hour."""
    velocity = vehicle.get_velocity()
    speed_ms = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    return speed_ms * 3.6


def get_safe_vehicle_blueprints(world: carla.World) -> List[carla.ActorBlueprint]:
    """Filter vehicle models using the demonstration's wheel-count and exclusion rules."""
    vehicle_blueprints = world.get_blueprint_library().filter("vehicle.*")
    safe_blueprints = []

    for blueprint in vehicle_blueprints:
        blueprint_id = blueprint.id.lower()
        if any(keyword in blueprint_id for keyword in EXCLUDED_BLUEPRINT_KEYWORDS):
            continue

        if not blueprint.has_attribute("number_of_wheels"):
            continue

        if int(blueprint.get_attribute("number_of_wheels")) != 4:
            continue

        safe_blueprints.append(blueprint)

    return safe_blueprints


def apply_world_settings(world: carla.World, no_rendering: bool) -> None:
    """Enable fixed-step synchronous simulation with the requested rendering mode."""
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
    settings.no_rendering_mode = no_rendering
    world.apply_settings(settings)


def short_map_name(map_name: str) -> str:
    """Extract a lowercase map name from CARLA's full map path."""
    return map_name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def validate_active_map(world: carla.World, expected_town: Optional[str]) -> None:
    """Confirm the expected map is already loaded without reloading it."""
    current_map_name = world.get_map().name
    print("Mapa activo:", current_map_name)

    if expected_town is None:
        return

    if short_map_name(current_map_name) != short_map_name(expected_town):
        raise ActiveMapMismatchError(
            f"El mapa activo es {current_map_name}, pero se esperaba {expected_town}. "
            f"Ejecuta primero: python .\\scripts\\change_map.py --town {expected_town}"
        )

    print(f"Mapa esperado confirmado: {expected_town}. No se recargará.")


def destroy_existing_vehicles(world: carla.World) -> None:
    """Remove existing vehicle actors from the CARLA world."""
    existing_vehicles = world.get_actors().filter("vehicle.*")
    if existing_vehicles:
        print(f"Eliminando vehículos anteriores: {len(existing_vehicles)}")

    for vehicle in existing_vehicles:
        vehicle.destroy()


def configure_vehicle(
    vehicle: carla.Vehicle, traffic_manager: carla.TrafficManager
) -> None:
    """Enable Traffic Manager control and apply the demonstration's following and traffic-rule settings."""
    vehicle.set_autopilot(True, traffic_manager.get_port())
    traffic_manager.auto_lane_change(vehicle, False)
    traffic_manager.distance_to_leading_vehicle(vehicle, 5.0)
    traffic_manager.vehicle_percentage_speed_difference(vehicle, 30.0)
    traffic_manager.ignore_lights_percentage(vehicle, 0.0)
    traffic_manager.ignore_signs_percentage(vehicle, 0.0)
    traffic_manager.ignore_vehicles_percentage(vehicle, 0.0)
    traffic_manager.ignore_walkers_percentage(vehicle, 0.0)
    traffic_manager.update_vehicle_lights(vehicle, True)


def spawn_vehicles(
    world: carla.World,
    traffic_manager: carla.TrafficManager,
    requested_amount: int,
    vehicles: List[carla.Vehicle],
) -> None:
    """Create vehicles at available spawn points and configure their Traffic Manager control."""
    spawn_points = list(world.get_map().get_spawn_points())
    safe_blueprints = get_safe_vehicle_blueprints(world)

    print("Spawn points disponibles:", len(spawn_points))
    print("Blueprints seguros disponibles:", len(safe_blueprints))

    if not spawn_points:
        raise RuntimeError("El mapa no tiene spawn points disponibles.")
    if not safe_blueprints:
        raise RuntimeError("No se encontraron blueprints seguros de cuatro ruedas.")

    random.shuffle(spawn_points)
    amount = min(requested_amount, len(spawn_points))
    print(f"Creando hasta {amount} vehículos de forma progresiva...")

    for spawn_point in spawn_points[:amount]:
        blueprint = random.choice(safe_blueprints)

        if blueprint.has_attribute("color"):
            colors = blueprint.get_attribute("color").recommended_values
            if colors:
                blueprint.set_attribute("color", random.choice(colors))

        if blueprint.has_attribute("role_name"):
            blueprint.set_attribute("role_name", "autopilot")

        vehicle = world.try_spawn_actor(blueprint, spawn_point)
        if vehicle is None:
            continue

        vehicles.append(vehicle)
        configure_vehicle(vehicle, traffic_manager)
        world.tick()


def print_metrics(vehicles: List[carla.Vehicle], elapsed_seconds: float) -> None:
    """Print the current average speed and number of stopped vehicles."""
    speeds = [speed_kmh(vehicle) for vehicle in vehicles if vehicle.is_alive]
    average_speed = sum(speeds) / len(speeds) if speeds else 0.0
    stopped_vehicles = sum(speed < STOPPED_SPEED_KMH for speed in speeds)

    print(
        f"t={elapsed_seconds:6.1f}s | "
        f"vehículos={len(speeds):3d} | "
        f"velocidad_promedio={average_speed:6.2f} km/h | "
        f"detenidos={stopped_vehicles:3d}"
    )


def destroy_created_vehicles(
    world: carla.World, vehicles: List[carla.Vehicle]
) -> None:
    """Destroy the demonstration's surviving vehicles and finish their cleanup."""
    print(f"Eliminando vehículos creados: {len(vehicles)}")
    for vehicle in vehicles:
        if vehicle is not None and vehicle.is_alive:
            vehicle.destroy()

    if vehicles:
        world.tick()


def run_simulation(args: argparse.Namespace) -> None:
    """Run the Traffic Manager demonstration with synchronous updates and restore settings during cleanup."""
    random.seed(SEED)

    client = carla.Client(DEFAULT_HOST, DEFAULT_PORT)
    client.set_timeout(CLIENT_TIMEOUT_SECONDS)

    world: Optional[carla.World] = None
    traffic_manager: Optional[carla.TrafficManager] = None
    original_settings = None
    world_was_configured = False
    traffic_manager_is_synchronous = False
    vehicles = []

    try:
        print(f"Conectando a CARLA en {DEFAULT_HOST}:{DEFAULT_PORT}")
        world = client.get_world()
        validate_active_map(world, args.town)
        original_settings = world.get_settings()

        apply_world_settings(world, args.no_rendering)
        world_was_configured = True

        traffic_manager = client.get_trafficmanager(TRAFFIC_MANAGER_PORT)
        traffic_manager.set_synchronous_mode(True)
        traffic_manager_is_synchronous = True
        traffic_manager.set_random_device_seed(SEED)
        traffic_manager.set_global_distance_to_leading_vehicle(5.0)

        destroy_existing_vehicles(world)
        world.tick()

        print("Mapa actual:", world.get_map().name)
        spawn_vehicles(world, traffic_manager, args.vehicles, vehicles)

        print(f"Vehículos creados: {len(vehicles)} de {args.vehicles} solicitados")
        print("Modo síncrono: activo")
        print(f"Delta fijo: {FIXED_DELTA_SECONDS:.2f} s")
        print(f"No-rendering: {args.no_rendering}")
        print(f"Duración: {args.seconds} segundos simulados")

        total_frames = int(args.seconds / FIXED_DELTA_SECONDS)
        frames_per_report = int(1.0 / FIXED_DELTA_SECONDS)

        for frame in range(1, total_frames + 1):
            world.tick()
            if frame % frames_per_report == 0:
                print_metrics(vehicles, frame * FIXED_DELTA_SECONDS)

    finally:
        if world is not None and world_was_configured:
            try:
                destroy_created_vehicles(world, vehicles)
            except RuntimeError as cleanup_error:
                print(
                    f"Advertencia al eliminar vehículos: {cleanup_error}",
                    file=sys.stderr,
                )

        if traffic_manager is not None and traffic_manager_is_synchronous:
            try:
                traffic_manager.set_synchronous_mode(False)
            except RuntimeError as cleanup_error:
                print(
                    f"Advertencia al restaurar Traffic Manager: {cleanup_error}",
                    file=sys.stderr,
                )

        if (
            world is not None
            and original_settings is not None
            and world_was_configured
        ):
            try:
                world.apply_settings(original_settings)
                print("Configuración original del mundo restaurada.")
            except RuntimeError as cleanup_error:
                print(
                    f"Advertencia al restaurar el mundo: {cleanup_error}",
                    file=sys.stderr,
                )


def main() -> int:
    """Read demonstration options, start the simulation, and report interruptions or runtime errors."""
    args = parse_args()

    try:
        run_simulation(args)
        print("Simulación finalizada correctamente.")
        return 0
    except KeyboardInterrupt:
        print("Simulación interrumpida por el usuario; se ejecutó la limpieza.")
        return 130
    except ActiveMapMismatchError as error:
        print(f"Error de mapa: {error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"Error de CARLA: {error}", file=sys.stderr)
        print(
            "Verifica que CarlaUE4.exe esté activo en localhost:2000 y que el mapa exista.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
