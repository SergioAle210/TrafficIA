"""Destination configuration and reproducible selection utilities.

This module is intentionally independent from the CARLA Python API so that the
CSV validation and stochastic selection can be unit tested without a simulator.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


ROUTINE_CLASS = "routine"
EXPLORATION_CLASS = "exploration"
VALID_FREQUENCY_CLASSES = (ROUTINE_CLASS, EXPLORATION_CLASS)


@dataclass(frozen=True)
class Destination:
    """A logical destination and the road reference used to reach it."""

    destination_id: str
    destination_name: str
    map_name: str
    category: str
    frequency_class: str
    weight: float
    enabled: bool
    reference_type: str
    spawn_point_index: Optional[int]
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    road_id: Optional[int]
    lane_id: Optional[int]
    description: str


def _normalise_map_name(map_name: str) -> str:
    return map_name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def _optional_int(value: str) -> Optional[int]:
    return int(value) if value and value.strip() else None


def _optional_float(value: str) -> Optional[float]:
    return float(value) if value and value.strip() else None


def _enabled(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "si", "sí")


def load_destinations(path: Path, active_map_name: str) -> List[Destination]:
    """Load enabled destinations for the active map and validate their schema."""

    required = {
        "destination_id",
        "destination_name",
        "map",
        "category",
        "frequency_class",
        "weight",
        "enabled",
        "reference_type",
        "spawn_point_index",
        "x",
        "y",
        "z",
        "road_id",
        "lane_id",
    }
    if not path.is_file():
        raise FileNotFoundError("No existe la configuración de destinos: {0}".format(path))

    destinations = []
    seen_ids = set()
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(required - fieldnames)
        if missing:
            raise ValueError("Faltan columnas en {0}: {1}".format(path, ", ".join(missing)))

        for row in reader:
            if not _enabled(row["enabled"]):
                continue
            if _normalise_map_name(row["map"]) != _normalise_map_name(active_map_name):
                continue
            destination_id = row["destination_id"].strip()
            if not destination_id or destination_id in seen_ids:
                raise ValueError("destination_id vacío o duplicado: {0}".format(destination_id))
            seen_ids.add(destination_id)
            frequency_class = row["frequency_class"].strip().lower()
            if frequency_class not in VALID_FREQUENCY_CLASSES:
                raise ValueError(
                    "Clase de frecuencia inválida para {0}: {1}".format(
                        destination_id, frequency_class
                    )
                )
            weight = float(row["weight"])
            if weight <= 0.0:
                raise ValueError("El peso debe ser positivo para {0}".format(destination_id))
            reference_type = row["reference_type"].strip().lower()
            spawn_index = _optional_int(row["spawn_point_index"])
            coordinates = (_optional_float(row["x"]), _optional_float(row["y"]), _optional_float(row["z"]))
            if reference_type == "spawn_point" and spawn_index is None:
                raise ValueError("{0} requiere spawn_point_index".format(destination_id))
            if reference_type == "coordinates" and any(value is None for value in coordinates):
                raise ValueError("{0} requiere x, y y z".format(destination_id))
            if reference_type not in ("spawn_point", "coordinates"):
                raise ValueError("reference_type inválido para {0}".format(destination_id))
            destinations.append(
                Destination(
                    destination_id=destination_id,
                    destination_name=row["destination_name"].strip(),
                    map_name=row["map"].strip(),
                    category=row["category"].strip(),
                    frequency_class=frequency_class,
                    weight=weight,
                    enabled=True,
                    reference_type=reference_type,
                    spawn_point_index=spawn_index,
                    x=coordinates[0],
                    y=coordinates[1],
                    z=coordinates[2],
                    road_id=_optional_int(row["road_id"]),
                    lane_id=_optional_int(row["lane_id"]),
                    description=row.get("description", "").strip(),
                )
            )

    if len(destinations) < 2:
        raise ValueError("Se requieren al menos dos destinos habilitados para el mapa activo.")
    for frequency_class in VALID_FREQUENCY_CLASSES:
        if not any(item.frequency_class == frequency_class for item in destinations):
            raise ValueError("Falta al menos un destino de clase {0}".format(frequency_class))
    return destinations


def weighted_choice(destinations: Sequence[Destination], rng: random.Random) -> Destination:
    """Select one item by normalized positive weights without NumPy."""

    if not destinations:
        raise ValueError("No hay destinos elegibles.")
    total_weight = sum(item.weight for item in destinations)
    threshold = rng.random() * total_weight
    cumulative = 0.0
    for destination in destinations:
        cumulative += destination.weight
        if threshold < cumulative:
            return destination
    return destinations[-1]


def select_destination(
    destinations: Iterable[Destination],
    current_destination_id: Optional[str],
    routine_probability: float,
    rng: random.Random,
) -> Destination:
    """Choose class first (routine/exploration), then a weighted destination.

    The current conceptual location is excluded.  If the sampled class has no
    eligible destination, the other class is used rather than choosing the
    current destination or failing silently.
    """

    if not 0.0 <= routine_probability <= 1.0:
        raise ValueError("routine_probability debe estar entre 0 y 1.")
    eligible = [item for item in destinations if item.destination_id != current_destination_id]
    if not eligible:
        raise ValueError("No existe un destino distinto de la ubicación actual.")
    selected_class = ROUTINE_CLASS if rng.random() < routine_probability else EXPLORATION_CLASS
    class_candidates = [item for item in eligible if item.frequency_class == selected_class]
    if not class_candidates:
        class_candidates = [item for item in eligible if item.frequency_class != selected_class]
    return weighted_choice(class_candidates, rng)
