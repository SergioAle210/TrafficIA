"""Run-scoped CSV writers for trajectories, trips, events, and summary metrics."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List

from src.navigation_diagnostics import ARRIVAL_FIELDS, CONTROL_FIELDS, ROUTE_FIELDS


TRIP_FIELDS = [
    "run_id", "vehicle_id", "trip_id", "seed", "origin_id", "origin_name",
    "origin_x", "origin_y", "origin_z", "destination_id", "destination_name",
    "destination_category", "frequency_class", "selection_class",
    "history_visit_count_before", "selection_candidate_count", "departure_sim_time_s",
    "arrival_sim_time_s", "travel_time_s", "distance_traveled_m",
    "average_speed_mps", "average_speed_kmh", "collision_count",
    "lane_invasion_count", "status", "end_sim_time_s", "stopped_time_s",
    "max_trip_time_seconds", "termination_reason",
]
HISTORY_FIELDS = [
    "run_id", "vehicle_id", "sequence", "destination_id", "source", "trip_id",
    "completed_sim_time_s",
]
TRAJECTORY_FIELDS = [
    "run_id", "vehicle_id", "trip_id", "frame", "simulation_time_s", "x", "y",
    "z", "speed_mps", "speed_kmh", "acceleration_mps2", "road_id", "lane_id",
    "distance_traveled_m",
]
EVENT_FIELDS = [
    "run_id", "vehicle_id", "trip_id", "frame", "simulation_time_s", "event_type",
    "other_actor_id", "x", "y", "z", "details",
]
METRICS_FIELDS = [
    "run_id", "vehicle_count", "trips_started", "trips_completed", "trips_incomplete",
    "simulation_duration_s", "total_distance_traveled_m", "aggregate_average_speed_mps",
    "aggregate_average_speed_kmh", "total_collisions", "total_lane_invasions",
    "observed_destination_distribution", "total_observed_distance_m", "total_vehicle_time_s",
]


class RunLogger:
    """Own the output files so simulation logic never writes CSV directly."""

    def __init__(self, output_directory: Path) -> None:
        output_directory.mkdir(parents=True, exist_ok=False)
        self.output_directory = output_directory
        self._files: List[object] = []
        self._trip_writer = self._create_writer("trips_log.csv", TRIP_FIELDS)
        self._trajectory_writer = self._create_writer("trajectory_log.csv", TRAJECTORY_FIELDS)
        self._event_writer = self._create_writer("events_log.csv", EVENT_FIELDS)
        self._metrics_writer = self._create_writer("metrics_summary.csv", METRICS_FIELDS)
        self._history_writer = self._create_writer("vehicle_history.csv", HISTORY_FIELDS)
        self._route_writer = None
        self._control_writer = None
        self._arrival_writer = None

    def _create_writer(self, file_name: str, fieldnames: Iterable[str]) -> csv.DictWriter:
        csv_file = (self.output_directory / file_name).open("w", newline="", encoding="utf-8")
        self._files.append(csv_file)
        writer = csv.DictWriter(csv_file, fieldnames=list(fieldnames))
        writer.writeheader()
        return writer

    def write_trip(self, row: Dict[str, object]) -> None:
        self._trip_writer.writerow(row)

    def write_trajectory(self, row: Dict[str, object]) -> None:
        self._trajectory_writer.writerow(row)

    def write_event(self, row: Dict[str, object]) -> None:
        self._event_writer.writerow(row)

    def write_metrics(self, row: Dict[str, object]) -> None:
        self._metrics_writer.writerow(row)

    def write_history(self, row: Dict[str, object]) -> None:
        self._history_writer.writerow(row)

    def write_route(self, row: Dict[str, object]) -> None:
        if self._route_writer is None:
            self._route_writer = self._create_writer("route_log.csv", ROUTE_FIELDS)
        self._route_writer.writerow(row)

    def write_control(self, row: Dict[str, object]) -> None:
        if self._control_writer is None:
            self._control_writer = self._create_writer("control_log.csv", CONTROL_FIELDS)
        self._control_writer.writerow(row)

    def close(self) -> None:
        for csv_file in self._files:
            csv_file.close()
        self._files = []

    def write_arrival(self, row: Dict[str, object]) -> None:
        if self._arrival_writer is None:
            self._arrival_writer = self._create_writer("arrival_log.csv", ARRIVAL_FIELDS)
        self._arrival_writer.writerow(row)
