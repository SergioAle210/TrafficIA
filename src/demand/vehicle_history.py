"""Per-vehicle destination history and reproducible 80/20 selection.

Destination recurrence is learned from completed visits.  No destination has
an intrinsic routine/exploration label or a user-authored probability weight.
"""

from __future__ import annotations

import csv
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from src.demand.destinations import Destination
from src.project_paths import project_path


ROUTINE = "routine"
EXPLORATION = "exploration"


@dataclass(frozen=True)
class HistoryEvent:
    vehicle_id: str
    sequence: int
    destination_id: str
    source: str


@dataclass(frozen=True)
class DestinationDecision:
    destination: Destination
    selection_class: str
    visit_count_before: int
    candidate_count: int


class VehicleHistory:
    """Ordered visits and derived counts for one logical vehicle."""

    def __init__(self, vehicle_id: str, events: Iterable[HistoryEvent] = ()) -> None:
        """Load one vehicle's ordered visits, count destinations, and reject duplicate sequence numbers."""
        self.vehicle_id = vehicle_id
        self.events: List[HistoryEvent] = []
        self.counts: Counter = Counter()
        for event in sorted(events, key=lambda item: item.sequence):
            if event.vehicle_id != vehicle_id:
                raise ValueError("El evento pertenece a otro vehículo: {0}".format(event.vehicle_id))
            self.events.append(event)
            self.counts[event.destination_id] += 1
        sequences = [event.sequence for event in self.events]
        if len(sequences) != len(set(sequences)):
            raise ValueError("El historial de {0} contiene secuencias duplicadas.".format(vehicle_id))
        self._next_sequence = max(sequences, default=0) + 1

    @classmethod
    def from_csv(
        cls, path: Path, vehicle_id: str, allowed_destination_ids: Set[str]
    ) -> "VehicleHistory":
        """Read one vehicle's history from CSV and check that all destinations exist."""
        if not path.is_file():
            path = project_path(path)
        if not path.is_file():
            raise FileNotFoundError("No existe el historial dummy: {0}".format(path))
        events: List[HistoryEvent] = []
        with path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            required = {"vehicle_id", "sequence", "destination_id", "source"}
            missing = sorted(required - set(reader.fieldnames or []))
            if missing:
                raise ValueError(
                    "Faltan columnas en {0}: {1}".format(path, ", ".join(missing))
                )
            for row in reader:
                if row["vehicle_id"].strip() != vehicle_id:
                    continue
                destination_id = row["destination_id"].strip()
                if destination_id not in allowed_destination_ids:
                    raise ValueError(
                        "El historial de {0} referencia un destino inexistente: {1}".format(
                            vehicle_id, destination_id
                        )
                    )
                events.append(
                    HistoryEvent(
                        vehicle_id=vehicle_id,
                        sequence=int(row["sequence"]),
                        destination_id=destination_id,
                        source=row["source"].strip() or "dummy",
                    )
                )
        if not events:
            raise ValueError("No hay historial dummy para {0} en {1}.".format(vehicle_id, path))
        return cls(vehicle_id, events)

    def record(self, destination_id: str, source: str = "simulation") -> HistoryEvent:
        """Append a visit and update this vehicle's destination counts."""
        event = HistoryEvent(
            vehicle_id=self.vehicle_id,
            sequence=self._next_sequence,
            destination_id=destination_id,
            source=source,
        )
        self._next_sequence += 1
        self.events.append(event)
        self.counts[destination_id] += 1
        return event

    def routine_ids(self, maximum: int) -> List[str]:
        """Return the most visited destination IDs, breaking ties by ID."""
        if maximum <= 0:
            raise ValueError("routine_destination_count debe ser positivo.")
        ranked = sorted(self.counts.items(), key=lambda item: (-item[1], item[0]))
        return [destination_id for destination_id, count in ranked if count > 0][:maximum]


def _count_weighted_choice(
    candidates: Sequence[Destination], history: VehicleHistory, rng: random.Random
) -> Destination:
    """Choose a destination with probability proportional to this vehicle's previous visits."""
    total = sum(history.counts[item.destination_id] for item in candidates)
    if total <= 0:
        return rng.choice(list(candidates))
    threshold = rng.random() * total
    cumulative = 0
    for destination in candidates:
        cumulative += history.counts[destination.destination_id]
        if threshold < cumulative:
            return destination
    return candidates[-1]


def select_from_history(
    destinations: Iterable[Destination],
    history: VehicleHistory,
    current_destination_id: Optional[str],
    routine_probability: float,
    routine_destination_count: int,
    rng: random.Random,
) -> DestinationDecision:
    """Select 80/20 from personal recurrence, never from manual weights.

    Routine candidates are the vehicle's most visited destinations. Exploration
    first uses destinations never visited by this vehicle; after that pool is
    exhausted it uses the remaining low-frequency destinations.
    """

    if not 0.0 <= routine_probability <= 1.0:
        raise ValueError("routine_probability debe estar entre 0 y 1.")
    eligible = sorted(
        (item for item in destinations if item.destination_id != current_destination_id),
        key=lambda item: item.destination_id,
    )
    if not eligible:
        raise ValueError("No existe un destino distinto de la ubicación actual.")

    routine_id_set = set(history.routine_ids(routine_destination_count))
    routine_candidates = [item for item in eligible if item.destination_id in routine_id_set]
    remaining_candidates = [item for item in eligible if item.destination_id not in routine_id_set]
    novel_candidates = [
        item for item in remaining_candidates if history.counts[item.destination_id] == 0
    ]

    wants_routine = rng.random() < routine_probability
    if wants_routine and routine_candidates:
        selected_class = ROUTINE
        candidates = routine_candidates
        destination = _count_weighted_choice(candidates, history, rng)
    else:
        candidates = novel_candidates or remaining_candidates
        if candidates:
            selected_class = EXPLORATION
            destination = rng.choice(candidates)
        else:
            selected_class = ROUTINE
            candidates = routine_candidates or eligible
            destination = _count_weighted_choice(candidates, history, rng)

    return DestinationDecision(
        destination=destination,
        selection_class=selected_class,
        visit_count_before=history.counts[destination.destination_id],
        candidate_count=len(candidates),
    )


def generate_dummy_events(
    destinations: Sequence[Destination],
    vehicle_ids: Sequence[str],
    history_length: int,
    routine_destination_count: int,
    routine_probability: float,
    seed: int,
) -> List[HistoryEvent]:
    """Generate personal bootstrap histories from one shared deterministic rule."""

    if history_length < routine_destination_count:
        raise ValueError("history_length debe cubrir todos los destinos rutinarios iniciales.")
    if routine_destination_count <= 0:
        raise ValueError("routine_destination_count debe ser positivo.")
    if not 0.0 <= routine_probability <= 1.0:
        raise ValueError("routine_probability debe estar entre 0 y 1.")
    ordered = sorted(destinations, key=lambda item: item.destination_id)
    if len(ordered) <= routine_destination_count:
        raise ValueError("Se requieren destinos adicionales para permitir exploración.")

    categories = sorted({item.category for item in ordered})
    events: List[HistoryEvent] = []
    for vehicle_index, vehicle_id in enumerate(vehicle_ids):
        rng = random.Random(seed + vehicle_index * 1_000_003)
        anchors: List[Destination] = []
        for category in categories:
            category_options = [item for item in ordered if item.category == category]
            if category_options and len(anchors) < routine_destination_count:
                anchors.append(rng.choice(category_options))
        remaining = [item for item in ordered if item not in anchors]
        while len(anchors) < routine_destination_count:
            selected = rng.choice(remaining)
            remaining.remove(selected)
            anchors.append(selected)

        sequence_destinations = list(anchors)
        previous = anchors[-1]
        while len(sequence_destinations) < history_length:
            pool = anchors if rng.random() < routine_probability else remaining
            candidates = [item for item in pool if item.destination_id != previous.destination_id]
            if not candidates:
                candidates = [item for item in ordered if item.destination_id != previous.destination_id]
            selected = rng.choice(candidates)
            sequence_destinations.append(selected)
            previous = selected

        events.extend(
            HistoryEvent(vehicle_id, sequence, destination.destination_id, "dummy")
            for sequence, destination in enumerate(sequence_destinations, start=1)
        )
    return events


def write_history_csv(path: Path, events: Iterable[HistoryEvent]) -> None:
    """Save vehicle visits to CSV, creating the parent directory when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=["vehicle_id", "sequence", "destination_id", "source"]
        )
        writer.writeheader()
        for event in events:
            writer.writerow(
                {
                    "vehicle_id": event.vehicle_id,
                    "sequence": event.sequence,
                    "destination_id": event.destination_id,
                    "source": event.source,
                }
            )
