"""Generate deterministic input configuration CSV files for future phases."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.destinations import load_destinations
from src.vehicle_history import generate_dummy_events, write_history_csv


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "input"


ZONES: List[Dict[str, object]] = [
    {
        "zone_id": "Z_RES_01",
        "zone_name": "Zona residencial norte",
        "category": "residencial",
        "spawn_indices": "0;1;2;3;4",
        "description": "Zona de origen residencial con baja concentración de actividad comercial.",
    },
    {
        "zone_id": "Z_RES_02",
        "zone_name": "Zona residencial sur",
        "category": "residencial",
        "spawn_indices": "5;6;7;8;9",
        "description": "Zona residencial alternativa para distribuir orígenes.",
    },
    {
        "zone_id": "Z_COM_01",
        "zone_name": "Zona comercial principal",
        "category": "comercial",
        "spawn_indices": "10;11;12;13;14",
        "description": "Destino comercial frecuente con alta atracción de viajes.",
    },
    {
        "zone_id": "Z_COM_02",
        "zone_name": "Zona comercial secundaria",
        "category": "comercial",
        "spawn_indices": "15;16;17;18",
        "description": "Destino comercial no frecuente o de menor atracción.",
    },
    {
        "zone_id": "Z_SER_01",
        "zone_name": "Zona de servicios",
        "category": "servicios",
        "spawn_indices": "19;20;21;22",
        "description": "Zona asociada a servicios urbanos como hospital, banco o trámites.",
    },
    {
        "zone_id": "Z_EDU_01",
        "zone_name": "Zona educativa",
        "category": "educativo",
        "spawn_indices": "23;24;25;26",
        "description": "Zona de destino frecuente asociada a estudios o trabajo académico.",
    },
]


DESTINATIONS: List[Dict[str, object]] = [
    {
        "destination_id": "D_COM_01",
        "zone_id": "Z_COM_01",
        "destination_name": "Centro comercial principal",
        "category": "comercial",
        "frequency_class": "frecuente",
        "weight": 0.25,
        "description": "Destino frecuente asociado a compras y actividad comercial.",
    },
    {
        "destination_id": "D_EDU_01",
        "zone_id": "Z_EDU_01",
        "destination_name": "Universidad o centro educativo",
        "category": "educativo",
        "frequency_class": "frecuente",
        "weight": 0.20,
        "description": "Destino frecuente asociado a movilidad recurrente.",
    },
    {
        "destination_id": "D_SER_01",
        "zone_id": "Z_SER_01",
        "destination_name": "Hospital o servicios principales",
        "category": "servicios",
        "frequency_class": "frecuente",
        "weight": 0.15,
        "description": "Destino frecuente asociado a servicios esenciales.",
    },
    {
        "destination_id": "D_RES_01",
        "zone_id": "Z_RES_01",
        "destination_name": "Retorno residencial norte",
        "category": "residencial",
        "frequency_class": "frecuente",
        "weight": 0.10,
        "description": "Destino frecuente de retorno a zona residencial.",
    },
    {
        "destination_id": "D_RES_02",
        "zone_id": "Z_RES_02",
        "destination_name": "Retorno residencial sur",
        "category": "residencial",
        "frequency_class": "frecuente",
        "weight": 0.10,
        "description": "Destino frecuente de retorno a zona residencial alternativa.",
    },
    {
        "destination_id": "D_COM_02",
        "zone_id": "Z_COM_02",
        "destination_name": "Comercio secundario",
        "category": "comercial",
        "frequency_class": "no_frecuente",
        "weight": 0.07,
        "description": "Destino comercial menos visitado.",
    },
    {
        "destination_id": "D_SER_02",
        "zone_id": "Z_SER_01",
        "destination_name": "Banco o trámite ocasional",
        "category": "servicios",
        "frequency_class": "no_frecuente",
        "weight": 0.05,
        "description": "Destino de servicios con menor frecuencia.",
    },
    {
        "destination_id": "D_REC_01",
        "zone_id": "Z_COM_02",
        "destination_name": "Destino recreativo ocasional",
        "category": "recreativo",
        "frequency_class": "no_frecuente",
        "weight": 0.04,
        "description": "Destino de exploración o recreación.",
    },
    {
        "destination_id": "D_SER_03",
        "zone_id": "Z_SER_01",
        "destination_name": "Gasolinera o servicio rápido",
        "category": "servicios",
        "frequency_class": "no_frecuente",
        "weight": 0.03,
        "description": "Destino ocasional de corta duración.",
    },
    {
        "destination_id": "D_MISC_01",
        "zone_id": "Z_COM_02",
        "destination_name": "Destino misceláneo",
        "category": "miscelaneo",
        "frequency_class": "no_frecuente",
        "weight": 0.01,
        "description": "Destino poco frecuente para conservar variabilidad.",
    },
]


DEMAND_PROFILES: List[Dict[str, object]] = [
    {
        "profile_id": "low_demand",
        "description": "Nivel bajo de demanda para pruebas iniciales.",
        "vehicles": 20,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 2.0,
    },
    {
        "profile_id": "medium_demand",
        "description": "Nivel medio de demanda para pruebas de estabilidad.",
        "vehicles": 40,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 1.5,
    },
    {
        "profile_id": "high_demand",
        "description": "Nivel alto de demanda para evaluación comparativa.",
        "vehicles": 70,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 1.0,
    },
]


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No hay filas para escribir en {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_destination_weights(destinations: List[Dict[str, object]]) -> None:
    total_weight = sum(float(row["weight"]) for row in destinations)
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            "La suma de pesos de destinos debe ser 1.0, "
            f"pero actualmente es {total_weight:.6f}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera los CSV dummy de configuración del proyecto."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directorio donde se crearán los CSV de entrada.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semilla del historial dummy.")
    parser.add_argument(
        "--vehicles", type=int, default=1, help="Cantidad de historiales individuales a generar."
    )
    parser.add_argument(
        "--history-length", type=int, default=30, help="Visitas previas por vehículo."
    )
    parser.add_argument(
        "--routine-destinations", type=int, default=3,
        help="Cantidad de destinos recurrentes iniciales por vehículo.",
    )
    parser.add_argument(
        "--routine-probability", type=float, default=0.8,
        help="Proporción de visitas dummy hacia los destinos personales recurrentes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir

    validate_destination_weights(DESTINATIONS)

    output_files = (
        (output_dir / "zones_config.csv", ZONES),
        (output_dir / "destinations_config.csv", DESTINATIONS),
        (output_dir / "demand_profiles.csv", DEMAND_PROFILES),
    )

    for path, rows in output_files:
        write_csv(path, rows)

    print("Datos dummy generados correctamente:")
    for path, _ in output_files:
        print(f"- {path}")

    town01_catalog_path = output_dir / "Town01" / "destinations_config.csv"
    town01_destinations = load_destinations(town01_catalog_path, "Town01")
    vehicle_ids = ["vehicle_{0:03d}".format(index) for index in range(1, args.vehicles + 1)]
    history_events = generate_dummy_events(
        destinations=town01_destinations,
        vehicle_ids=vehicle_ids,
        history_length=args.history_length,
        routine_destination_count=args.routine_destinations,
        routine_probability=args.routine_probability,
        seed=args.seed,
    )
    history_path = output_dir / "Town01" / "vehicle_history_dummy.csv"
    write_history_csv(history_path, history_events)
    print(f"- {history_path}")


if __name__ == "__main__":
    main()
