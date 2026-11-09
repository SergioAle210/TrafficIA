"""Run one or more CARLA vehicles through successive planned trips."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.trip_runner import TripSimulation, TripSimulationConfig


def parse_args(parser=None) -> argparse.Namespace:
    """Read simulation, destination, history, and recording options from the command line."""
    parser = parser or argparse.ArgumentParser(
        description="Ejecuta viajes sucesivos de uno o más vehículos con rutas explícitas."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "trips" / "single_vehicle_trip.json",
        help="Archivo JSON de configuración de la corrida.",
    )
    parser.add_argument("--town", help="Sobrescribe el mapa esperado del JSON.")
    parser.add_argument("--seed", type=int, help="Sobrescribe la semilla del JSON.")
    parser.add_argument("--seconds", type=float, help="Sobrescribe la duración simulada.")
    parser.add_argument("--blocked-policy", choices=("terminate", "keep_trip"),
                        help="Terminar el viaje o conservar destino al superar el umbral de detención.")
    parser.add_argument("--max-trip-seconds", type=float,
                        help="Límite por viaje en segundos simulados; 0 lo desactiva hasta el fin de corrida.")
    parser.add_argument(
        "--scenario",
        choices=("random_baseline", "history_80_20"),
        help="Sobrescribe destination_selection_mode del JSON antes de validarlo.",
    )
    parser.add_argument(
        "--history-in",
        type=Path,
        help=(
            "Historial de entrada para los vehículos configurados. Puede ser el dummy inicial o "
            "vehicle_history.csv de una corrida anterior."
        ),
    )
    parser.add_argument(
        "--carla-pythonapi",
        type=Path,
        help=(
            "Carpeta de CARLA que contiene agents; normalmente "
            "C:\\CARLA\\WindowsNoEditor\\PythonAPI\\carla."
        ),
    )
    parser.add_argument(
        "--no-rendering",
        action="store_true",
        help="Desactiva el renderizado sin cambiar modo síncrono ni delta fijo.",
    )
    parser.add_argument(
        "--controller-distance-ratio", type=float,
        help="Factor de velocidad del descarte de waypoints; 0.5 reproduce el valor anterior de CARLA.",
    )
    parser.add_argument(
        "--navigation-diagnostics", action="store_true",
        help="Guarda el plan completo y el objetivo/control de cada frame en dos CSV adicionales.",
    )
    parser.add_argument(
        "--simulation-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=1,
        help="Objetivo de ritmo de reloj real; no modifica el tiempo simulado ni la física.",
    )
    return parser.parse_args()


def configuration_from_args(args: argparse.Namespace) -> TripSimulationConfig:
    """Apply CLI inputs before validating the effective scenario configuration."""

    overrides = {}
    if getattr(args, "blocked_policy", None) is not None:
        overrides["blocked_policy"] = args.blocked_policy
    if args.town:
        overrides["town"] = args.town
    if args.seed is not None:
        overrides["seed"] = args.seed
    if args.seconds is not None:
        overrides["duration_seconds"] = args.seconds
    if getattr(args, "max_trip_seconds", None) is not None:
        overrides["max_trip_time_seconds"] = args.max_trip_seconds if args.max_trip_seconds != 0 else None
    if args.scenario is not None:
        overrides["destination_selection_mode"] = args.scenario
    if args.history_in is not None:
        overrides["vehicle_history_config"] = str(args.history_in.resolve())
    if args.no_rendering:
        overrides["no_rendering_mode"] = True
    if getattr(args, "navigation_diagnostics", False):
        overrides["navigation_diagnostics_enabled"] = True
    if getattr(args, "controller_distance_ratio", None) is not None:
        overrides["controller_distance_ratio"] = args.controller_distance_ratio
    config = TripSimulationConfig.from_json(args.config, overrides=overrides)
    if config.destination_selection_mode == "random_baseline" and args.history_in is not None:
        raise ValueError("--history-in no se puede combinar con random_baseline; no utiliza historial de entrada.")
    return config


def main() -> int:
    """Validate the selected configuration, run the trip simulation, and report its output or error."""
    args = parse_args()
    try:
        config = configuration_from_args(args)
        output_directory = TripSimulation(
            config, PROJECT_ROOT, args.simulation_speed, str(args.carla_pythonapi)
            if args.carla_pythonapi else None
        ).run()
        print("Salida guardada en: {0}".format(output_directory))
        return 0
    except ModuleNotFoundError as error:
        if error.name == "carla":
            print(
                "Error: la Python API de CARLA 0.9.15 no está disponible en este intérprete. "
                "Ejecuta con el entorno o .egg incluido en PythonAPI/carla/dist.",
                file=sys.stderr,
            )
            return 1
        if error.name == "networkx":
            print(
                "Error: falta networkx, dependencia de GlobalRoutePlanner. Ejecuta: "
                "python -m pip install -r .\\requirements.txt",
                file=sys.stderr,
            )
            return 1
        if error.name == "shapely":
            print(
                "Error: falta shapely, dependencia de BasicAgent. Ejecuta: "
                "python -m pip install -r .\\requirements.txt",
                file=sys.stderr,
            )
            return 1
        print("Error de dependencia CARLA: {0}".format(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Simulación detenida con Ctrl+C; se ejecutó la limpieza de actores y sensores.")
        return 130
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("Error de simulación: {0}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
