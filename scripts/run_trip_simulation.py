"""Run one or more CARLA vehicles through successive planned trips."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.trip_runner import TripSimulation, TripSimulationConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ejecuta viajes sucesivos de uno o más vehículos con rutas explícitas."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "config" / "single_vehicle_trip.json",
        help="Archivo JSON de configuración de la corrida.",
    )
    parser.add_argument("--town", help="Sobrescribe el mapa esperado del JSON.")
    parser.add_argument("--seed", type=int, help="Sobrescribe la semilla del JSON.")
    parser.add_argument("--seconds", type=float, help="Sobrescribe la duración simulada.")
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
        "--simulation-speed",
        type=int,
        choices=(1, 2, 3, 4, 5),
        default=1,
        help="Objetivo de ritmo de reloj real; no modifica el tiempo simulado ni la física.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = TripSimulationConfig.from_json(args.config)
    if args.town:
        config.town = args.town
    if args.seed is not None:
        config.seed = args.seed
    if args.seconds is not None:
        config.duration_seconds = args.seconds
    if args.history_in is not None:
        config.vehicle_history_config = str(args.history_in.resolve())
    if args.no_rendering:
        config.no_rendering_mode = True
    config.validate()
    try:
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
        print("Simulación detenida con Ctrl+C; actores y sensores eliminados.")
        return 130
    except (RuntimeError, ValueError, FileNotFoundError) as error:
        print("Error de simulación: {0}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
