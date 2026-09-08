"""Multi-vehicle, successive origin-destination trip simulation for CARLA 0.9.15."""

from __future__ import annotations

import json
import math
import random
import threading
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.destinations import Destination, load_destinations, select_destination
from src.route_planner import (
    build_basic_agent,
    build_global_route_planner,
    configure_carla_agents,
    plan_route,
    route_distance_m,
    validate_route_start,
)
from src.run_logger import RunLogger
from src.vehicle_history import (
    DestinationDecision,
    VehicleHistory,
    select_from_history,
)


EXCLUDED_BLUEPRINT_KEYWORDS = (
    "ambulance", "bh", "carlacola", "crossbike", "diamondback", "firetruck",
    "fusorosa", "harley", "kawasaki", "sprinter", "vespa", "yamaha",
)


@dataclass
class TripSimulationConfig:
    town: str
    seed: int
    duration_seconds: float
    fixed_delta_seconds: float
    no_rendering_mode: bool
    initial_spawn_point_index: int
    initial_spawn_fallback_enabled: bool
    destinations_config: str
    output_root: str
    destination_selection_mode: str
    destination_cycle_order: List[str]
    vehicle_history_config: str
    routine_destination_count: int
    required_destination_categories: List[str]
    routine_probability: float
    exploration_probability: float
    arrival_threshold_m: float
    destination_dwell_time_seconds: float
    max_trip_time_seconds: float
    blocked_speed_threshold_mps: float
    blocked_time_threshold_seconds: float
    trajectory_sampling_interval_seconds: float
    route_sampling_resolution_m: float
    route_origin_validation_tolerance_m: float
    initial_spawn_validation_tolerance_m: float
    target_speed_kmh: float
    vehicle_blueprint_filter: str
    vehicle_count: int = 1
    initial_spawn_point_indices: List[int] = field(default_factory=list)
    host: str = "localhost"
    port: int = 2000
    client_timeout_seconds: float = 30.0

    @classmethod
    def from_json(cls, path: Path) -> "TripSimulationConfig":
        with path.open("r", encoding="utf-8") as config_file:
            payload = json.load(config_file)
        payload.setdefault("vehicle_count", 1)
        payload.setdefault(
            "initial_spawn_point_indices",
            [payload["initial_spawn_point_index"]] if "initial_spawn_point_index" in payload else [],
        )
        required = {
            "town", "seed", "duration_seconds", "fixed_delta_seconds", "no_rendering_mode",
            "initial_spawn_point_index", "initial_spawn_fallback_enabled", "destinations_config", "output_root",
            "destination_selection_mode", "destination_cycle_order",
            "vehicle_history_config", "routine_destination_count",
            "required_destination_categories",
            "routine_probability", "exploration_probability", "arrival_threshold_m",
            "destination_dwell_time_seconds", "max_trip_time_seconds",
            "blocked_speed_threshold_mps", "blocked_time_threshold_seconds",
            "trajectory_sampling_interval_seconds", "route_sampling_resolution_m",
            "route_origin_validation_tolerance_m", "initial_spawn_validation_tolerance_m",
            "target_speed_kmh", "vehicle_blueprint_filter",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError("Faltan parámetros en {0}: {1}".format(path, ", ".join(missing)))
        config = cls(**payload)
        config.validate()
        return config

    def validate(self) -> None:
        spawn_point_indices = self.resolved_spawn_point_indices()
        if self.vehicle_count <= 0:
            raise ValueError("vehicle_count debe ser positivo.")
        if len(spawn_point_indices) != self.vehicle_count:
            raise ValueError(
                "initial_spawn_point_indices debe contener exactamente vehicle_count elementos."
            )
        if len(set(spawn_point_indices)) != len(spawn_point_indices):
            raise ValueError("initial_spawn_point_indices no puede contener índices repetidos.")
        if any(index < 0 for index in spawn_point_indices):
            raise ValueError("Los índices de initial_spawn_point_indices no pueden ser negativos.")
        if spawn_point_indices[0] != self.initial_spawn_point_index:
            raise ValueError(
                "initial_spawn_point_index debe coincidir con el primer elemento de "
                "initial_spawn_point_indices."
            )
        if abs((self.routine_probability + self.exploration_probability) - 1.0) > 1e-9:
            raise ValueError("routine_probability + exploration_probability debe sumar 1.0.")
        positive_values = {
            "duration_seconds": self.duration_seconds,
            "fixed_delta_seconds": self.fixed_delta_seconds,
            "arrival_threshold_m": self.arrival_threshold_m,
            "max_trip_time_seconds": self.max_trip_time_seconds,
            "blocked_time_threshold_seconds": self.blocked_time_threshold_seconds,
            "trajectory_sampling_interval_seconds": self.trajectory_sampling_interval_seconds,
            "route_sampling_resolution_m": self.route_sampling_resolution_m,
            "route_origin_validation_tolerance_m": self.route_origin_validation_tolerance_m,
            "initial_spawn_validation_tolerance_m": self.initial_spawn_validation_tolerance_m,
            "target_speed_kmh": self.target_speed_kmh,
        }
        invalid = [name for name, value in positive_values.items() if value <= 0.0]
        if invalid:
            raise ValueError("Estos parámetros deben ser positivos: {0}".format(", ".join(invalid)))
        if self.destination_dwell_time_seconds < 0.0:
            raise ValueError("destination_dwell_time_seconds no puede ser negativo.")
        if self.destination_selection_mode not in {"stochastic", "cyclic", "history_80_20"}:
            raise ValueError(
                "destination_selection_mode debe ser 'stochastic', 'cyclic' o 'history_80_20'."
            )
        if self.routine_destination_count <= 0:
            raise ValueError("routine_destination_count debe ser positivo.")
        if len(self.required_destination_categories) != 3 or (
            len(set(self.required_destination_categories)) != 3
        ):
            raise ValueError("required_destination_categories debe contener exactamente tres categorías.")
        if self.destination_selection_mode == "history_80_20" and not self.vehicle_history_config:
            raise ValueError("vehicle_history_config es obligatorio para history_80_20.")
        if self.destination_selection_mode == "cyclic":
            if len(self.destination_cycle_order) < 2:
                raise ValueError("destination_cycle_order debe contener al menos dos destinos.")
            if len(set(self.destination_cycle_order)) != len(self.destination_cycle_order):
                raise ValueError("destination_cycle_order no puede repetir destinos en una vuelta.")

    def resolved_spawn_point_indices(self) -> List[int]:
        """Return the explicit list while preserving legacy one-vehicle configs."""

        return list(self.initial_spawn_point_indices or [self.initial_spawn_point_index])


@dataclass
class ActiveTrip:
    trip_number: int
    origin_id: str
    origin_name: str
    origin_location: Any
    destination: Destination
    destination_location: Any
    departure_time_s: float
    last_location: Any
    last_moving_time_s: float
    agent: Any
    planned_route_distance_m: float
    selection_class: str
    history_visit_count_before: int
    selection_candidate_count: int
    distance_traveled_m: float = 0.0
    collision_count: int = 0
    lane_invasion_count: int = 0
    last_trajectory_sample_time_s: Optional[float] = None

    @property
    def trip_id(self) -> str:
        return "trip_{0:03d}".format(self.trip_number)


class EventCollector:
    """Buffer sensor callbacks so CSV writes happen in the simulation loop."""

    def __init__(self) -> None:
        self._events: List[Dict[str, object]] = []
        self._lock = threading.Lock()

    def _append(self, event_type: str, event: Any, other_actor_id: object, details: str) -> None:
        location = event.transform.location
        record = {
            "frame": event.frame,
            "simulation_time_s": event.timestamp,
            "event_type": event_type,
            "other_actor_id": other_actor_id,
            "x": location.x,
            "y": location.y,
            "z": location.z,
            "details": details,
        }
        with self._lock:
            self._events.append(record)

    def collision(self, event: Any) -> None:
        impulse = event.normal_impulse
        details = "normal_impulse=({0:.3f},{1:.3f},{2:.3f})".format(
            impulse.x, impulse.y, impulse.z
        )
        self._append("collision", event, event.other_actor.id, details)

    def lane_invasion(self, event: Any) -> None:
        markings = ";".join(str(marking.type) for marking in event.crossed_lane_markings)
        self._append("lane_invasion", event, "", "crossed_lane_markings={0}".format(markings))

    def drain(self) -> List[Dict[str, object]]:
        with self._lock:
            events = self._events
            self._events = []
        return events


@dataclass
class VehicleState:
    """All mutable simulation state owned by one logical vehicle."""

    vehicle_id: str
    requested_spawn_point_index: int
    rng: random.Random
    actor_rng: random.Random
    vehicle_history: VehicleHistory
    actor: Any = None
    sensors: List[Any] = field(default_factory=list)
    event_collector: EventCollector = field(default_factory=EventCollector)
    active_trip: Optional[ActiveTrip] = None
    current_destination_id: Optional[str] = None
    current_location_id: str = "INITIAL_POSITION"
    current_location_name: str = "Initial spawn point"
    next_trip_number: int = 1
    dwell_started_time_s: Optional[float] = None
    completed_trips: int = 0
    trips_started: int = 0
    destination_counts: Counter = field(default_factory=Counter)
    total_collisions: int = 0
    total_lane_invasions: int = 0
    total_distance_traveled_m: float = 0.0
    total_trip_duration_s: float = 0.0
    actual_initial_spawn_point_index: Optional[int] = None
    actual_initial_spawn_location: Optional[Dict[str, float]] = None
    initial_spawn_position_error_m: Optional[float] = None
    destination_cycle_index: int = 0
    initial_history_counts: Dict[str, int] = field(default_factory=dict)


def speed_mps(vector: Any) -> float:
    return math.sqrt(vector.x ** 2 + vector.y ** 2 + vector.z ** 2)


def safe_vehicle_blueprints(world: Any, blueprint_filter: str) -> List[Any]:
    blueprints = []
    for blueprint in world.get_blueprint_library().filter(blueprint_filter):
        if any(keyword in blueprint.id.lower() for keyword in EXCLUDED_BLUEPRINT_KEYWORDS):
            continue
        if blueprint.has_attribute("number_of_wheels") and int(blueprint.get_attribute("number_of_wheels")) != 4:
            continue
        blueprints.append(blueprint)
    if not blueprints:
        raise RuntimeError("No se encontraron blueprints vehiculares seguros.")
    return sorted(blueprints, key=lambda item: item.id)


def driving_transform_from_spawn_point(carla_module: Any, carla_map: Any, spawn_point: Any) -> Optional[Any]:
    """Project a nominal spawn point onto the nearest drivable lane center."""

    waypoint = carla_map.get_waypoint(
        spawn_point.location,
        project_to_road=True,
        lane_type=carla_module.LaneType.Driving,
    )
    if waypoint is None:
        return None
    location = waypoint.transform.location
    return carla_module.Transform(
        carla_module.Location(x=location.x, y=location.y, z=location.z + 0.5),
        waypoint.transform.rotation,
    )


def validate_initial_spawn_location(
    actual_location: Any, expected_location: Any, tolerance_m: float
) -> float:
    """Reject stale/default actor state before the first route is planned."""

    distance_m = actual_location.distance(expected_location)
    if distance_m > tolerance_m:
        raise RuntimeError(
            "La posición sincronizada del vehículo está a {0:.2f} m del spawn esperado; "
            "máximo permitido: {1:.2f} m. No se calculará una ruta con un origen inválido.".format(
                distance_m, tolerance_m
            )
        )
    return distance_m


def spawn_vehicle_at_first_available_point(
    world: Any,
    blueprint: Any,
    carla_module: Any,
    carla_map: Any,
    spawn_points: List[Any],
    preferred_index: int,
    allow_fallback: bool,
    vehicle_id: str = "vehicle_001",
) -> tuple[Any, int]:
    """Spawn on a projected driving lane, trying points in deterministic order."""

    if preferred_index < 0 or preferred_index >= len(spawn_points):
        raise ValueError("initial_spawn_point_index no existe en el mapa activo.")
    candidate_indices = [preferred_index]
    if allow_fallback:
        candidate_indices += [
            index for index in range(len(spawn_points)) if index != preferred_index
        ]
    for index in candidate_indices:
        driving_transform = driving_transform_from_spawn_point(
            carla_module, carla_map, spawn_points[index]
        )
        if driving_transform is None:
            continue
        vehicle = world.try_spawn_actor(blueprint, driving_transform)
        if vehicle is not None:
            return vehicle, index
    if allow_fallback:
        raise RuntimeError(
            "No se pudo crear {0} en ningún spawn point del mapa activo.".format(vehicle_id)
        )
    raise RuntimeError(
        "No se pudo crear {0} en el spawn point fijo {1}. "
        "Revisa initial_spawn_point_indices en la configuración "
        "o activa initial_spawn_fallback_enabled.".format(vehicle_id, preferred_index)
    )


def resolve_destination_location(carla_module: Any, carla_map: Any, destination: Destination) -> Any:
    if destination.reference_type == "spawn_point":
        spawn_points = carla_map.get_spawn_points()
        index = destination.spawn_point_index
        if index is None or index < 0 or index >= len(spawn_points):
            raise ValueError(
                "spawn_point_index inválido para {0}: {1}; el mapa tiene {2} puntos.".format(
                    destination.destination_id, index, len(spawn_points)
                )
            )
        location = spawn_points[index].location
    else:
        location = carla_module.Location(x=destination.x, y=destination.y, z=destination.z)
    waypoint = carla_map.get_waypoint(
        location, project_to_road=True, lane_type=carla_module.LaneType.Driving
    )
    if waypoint is None:
        raise ValueError("No hay waypoint vial accesible para {0}.".format(destination.destination_id))
    if destination.road_id is not None and waypoint.road_id != destination.road_id:
        raise ValueError("road_id no coincide para {0}.".format(destination.destination_id))
    if destination.lane_id is not None and waypoint.lane_id != destination.lane_id:
        raise ValueError("lane_id no coincide para {0}.".format(destination.destination_id))
    return waypoint.transform.location


def validate_destinations_on_map(
    carla_module: Any, carla_map: Any, destinations: List[Destination]
) -> None:
    """Resolve every configured reference before actors or sensors are created."""

    for destination in destinations:
        try:
            resolve_destination_location(carla_module, carla_map, destination)
        except ValueError as error:
            raise ValueError(
                "Destino inválido {0}: {1}".format(destination.destination_id, error)
            )


class TripSimulation:
    """Orchestrate reusable vehicles and their independent successive trips."""

    def __init__(
        self,
        config: TripSimulationConfig,
        project_root: Path,
        simulation_speed: int,
        carla_pythonapi: Optional[str] = None,
    ) -> None:
        if simulation_speed not in (1, 2, 3, 4, 5):
            raise ValueError("simulation_speed debe ser un entero entre 1 y 5.")
        config.validate()
        self.config = config
        self.project_root = project_root
        self.simulation_speed = simulation_speed
        self.carla_pythonapi = carla_pythonapi
        self.run_id = "{0}_trip_seed_{1}_{2}".format(
            config.town.lower(), config.seed, datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        )
        self.vehicle_states = []
        for vehicle_index, spawn_point_index in enumerate(
            config.resolved_spawn_point_indices()
        ):
            vehicle_id = "vehicle_{0:03d}".format(vehicle_index + 1)
            seed_offset = vehicle_index * 1_000_003
            self.vehicle_states.append(
                VehicleState(
                    vehicle_id=vehicle_id,
                    requested_spawn_point_index=spawn_point_index,
                    rng=random.Random(config.seed + seed_offset),
                    actor_rng=random.Random(config.seed + 1 + seed_offset),
                    vehicle_history=VehicleHistory(vehicle_id),
                )
            )
        self.destinations: List[Destination] = []
        self.destinations_by_id: Dict[str, Destination] = {}
        self.logger = None

    @property
    def primary_vehicle_state(self) -> VehicleState:
        """Expose vehicle_001 for compatibility with the original unit-level API."""

        return self.vehicle_states[0]

    @property
    def vehicle_id(self) -> str:
        return self.primary_vehicle_state.vehicle_id

    @property
    def vehicle_history(self) -> VehicleHistory:
        return self.primary_vehicle_state.vehicle_history

    @vehicle_history.setter
    def vehicle_history(self, value: VehicleHistory) -> None:
        self.primary_vehicle_state.vehicle_history = value

    @property
    def active_trip(self) -> Optional[ActiveTrip]:
        return self.primary_vehicle_state.active_trip

    @active_trip.setter
    def active_trip(self, value: Optional[ActiveTrip]) -> None:
        self.primary_vehicle_state.active_trip = value

    @property
    def current_destination_id(self) -> Optional[str]:
        return self.primary_vehicle_state.current_destination_id

    @current_destination_id.setter
    def current_destination_id(self, value: Optional[str]) -> None:
        self.primary_vehicle_state.current_destination_id = value

    @property
    def current_location_id(self) -> str:
        return self.primary_vehicle_state.current_location_id

    @current_location_id.setter
    def current_location_id(self, value: str) -> None:
        self.primary_vehicle_state.current_location_id = value

    @property
    def current_location_name(self) -> str:
        return self.primary_vehicle_state.current_location_name

    @current_location_name.setter
    def current_location_name(self, value: str) -> None:
        self.primary_vehicle_state.current_location_name = value

    def _state_or_primary(self, state: Optional[VehicleState]) -> VehicleState:
        return state if state is not None else self.primary_vehicle_state

    def _output_directory(self) -> Path:
        return self.project_root / self.config.output_root / self.run_id

    def _write_run_config(
        self, output_directory: Path, server_version: str, destinations: List[Destination]
    ) -> None:
        primary = self.primary_vehicle_state
        vehicles = [
            {
                "vehicle_id": state.vehicle_id,
                "initial_spawn_point_index_requested": state.requested_spawn_point_index,
                "initial_spawn_point_index_used": state.actual_initial_spawn_point_index,
                "initial_spawn_location_used": state.actual_initial_spawn_location,
                "initial_spawn_position_error_m": state.initial_spawn_position_error_m,
                "initial_visit_counts": state.initial_history_counts,
            }
            for state in self.vehicle_states
        ]
        payload = {
            "run_id": self.run_id,
            "carla_version": server_version,
            "map": self.config.town,
            "seed": self.config.seed,
            "vehicle_count": len(self.vehicle_states),
            "initial_spawn_point_indices_requested": [
                state.requested_spawn_point_index for state in self.vehicle_states
            ],
            "vehicles": vehicles,
            # Legacy keys continue to describe vehicle_001.
            "initial_spawn_point_index_requested": primary.requested_spawn_point_index,
            "initial_spawn_point_index_used": primary.actual_initial_spawn_point_index,
            "initial_spawn_location_used": primary.actual_initial_spawn_location,
            "initial_spawn_position_error_m": primary.initial_spawn_position_error_m,
            "synchronous_mode": True,
            "fixed_delta_seconds": self.config.fixed_delta_seconds,
            "no_rendering_mode": self.config.no_rendering_mode,
            "simulation_speed": {
                "requested_multiplier": self.simulation_speed,
                "meaning": "Wall-clock pacing target only; simulated time remains fixed_delta_seconds per tick.",
            },
            "arrival_threshold_m": self.config.arrival_threshold_m,
            "destination_dwell_time_seconds": self.config.destination_dwell_time_seconds,
            "destination_selection": {
                "routine_probability": self.config.routine_probability,
                "exploration_probability": self.config.exploration_probability,
                "method": {
                    "cyclic": "configured fixed cycle per vehicle",
                    "stochastic": "legacy seeded static-class selection per vehicle",
                    "history_80_20": (
                        "seeded 80/20 draw from each vehicle's visit counts; "
                        "no user-authored destination weights"
                    ),
                }[self.config.destination_selection_mode],
                "mode": self.config.destination_selection_mode,
                "cycle_order": self.config.destination_cycle_order,
                "routine_destination_count": self.config.routine_destination_count,
                "history_input": self.config.vehicle_history_config,
                "initial_visit_counts": primary.initial_history_counts,
                "initial_visit_counts_by_vehicle": {
                    state.vehicle_id: state.initial_history_counts
                    for state in self.vehicle_states
                },
            },
            "route_planning": {
                "planner": "GlobalRoutePlanner",
                "controller": "one BasicAgent.set_global_plan per vehicle",
                "sampling_resolution_m": self.config.route_sampling_resolution_m,
                "origin_validation_tolerance_m": self.config.route_origin_validation_tolerance_m,
                "optimality": "shortest route according to CARLA road-network graph cost; not traffic/time optimal",
            },
            "traffic_manager": {
                "used_for_route_following": False,
                "reason": "Each BasicAgent follows its own complete precomputed route.",
            },
            "simulation_config": asdict(self.config),
            "destinations": [asdict(destination) for destination in destinations],
        }
        with (output_directory / "run_config.json").open("w", encoding="utf-8") as config_file:
            json.dump(payload, config_file, ensure_ascii=False, indent=2)

    @staticmethod
    def _apply_world_settings(world: Any, config: TripSimulationConfig) -> None:
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = config.fixed_delta_seconds
        settings.no_rendering_mode = config.no_rendering_mode
        world.apply_settings(settings)

    def _validate_destination_cycle(self) -> None:
        if self.config.destination_selection_mode != "cyclic":
            return
        unknown_ids = [
            destination_id
            for destination_id in self.config.destination_cycle_order
            if destination_id not in self.destinations_by_id
        ]
        if unknown_ids:
            raise ValueError(
                "destination_cycle_order contiene destinos inexistentes o deshabilitados: {0}.".format(
                    ", ".join(unknown_ids)
                )
            )

    def _validate_destination_categories(self) -> None:
        configured = set(self.config.required_destination_categories)
        observed = {destination.category for destination in self.destinations}
        if observed != configured:
            raise ValueError(
                "Las categorías de destinos deben ser exactamente {0}; se encontraron {1}.".format(
                    sorted(configured), sorted(observed)
                )
            )

    def _select_next_destination(
        self, state: Optional[VehicleState] = None
    ) -> DestinationDecision:
        state = self._state_or_primary(state)
        if self.config.destination_selection_mode == "cyclic":
            destination_id = self.config.destination_cycle_order[
                state.destination_cycle_index % len(self.config.destination_cycle_order)
            ]
            state.destination_cycle_index += 1
            destination = self.destinations_by_id[destination_id]
            return DestinationDecision(
                destination, "cyclic", state.vehicle_history.counts[destination_id], 1
            )
        if self.config.destination_selection_mode == "history_80_20":
            return select_from_history(
                self.destinations,
                state.vehicle_history,
                state.current_destination_id,
                self.config.routine_probability,
                self.config.routine_destination_count,
                state.rng,
            )
        destination = select_destination(
            self.destinations,
            state.current_destination_id,
            self.config.routine_probability,
            state.rng,
        )
        return DestinationDecision(
            destination,
            destination.frequency_class or "legacy_stochastic",
            state.vehicle_history.counts[destination.destination_id],
            1,
        )

    def _start_trip(
        self,
        carla_module: Any,
        carla_map: Any,
        planner: Any,
        vehicle: Any,
        now_s: float,
        state: Optional[VehicleState] = None,
    ) -> None:
        state = self._state_or_primary(state)
        origin_location = vehicle.get_location()
        decision = self._select_next_destination(state)
        destination = decision.destination
        state.trips_started += 1
        try:
            origin_waypoint = carla_map.get_waypoint(
                origin_location,
                project_to_road=True,
                lane_type=carla_module.LaneType.Driving,
            )
            if origin_waypoint is None:
                raise RuntimeError("No hay un waypoint de conducción para el origen actual.")
            route_origin_location = origin_waypoint.transform.location
            road_offset_m = origin_location.distance(route_origin_location)
            if road_offset_m > self.config.route_origin_validation_tolerance_m:
                raise RuntimeError(
                    "El vehículo está a {0:.2f} m del carril de conducción; máximo permitido: {1:.2f} m.".format(
                        road_offset_m, self.config.route_origin_validation_tolerance_m
                    )
                )
            destination_location = resolve_destination_location(
                carla_module, carla_map, destination
            )
            route = plan_route(planner, route_origin_location, destination_location)
            route_start_offset_m = validate_route_start(
                route,
                origin_location,
                self.config.route_origin_validation_tolerance_m,
            )
            agent = build_basic_agent(vehicle, route, self.config.target_speed_kmh)
        except (RuntimeError, ValueError) as error:
            failed = ActiveTrip(
                trip_number=state.next_trip_number,
                origin_id=state.current_location_id,
                origin_name=state.current_location_name,
                origin_location=origin_location,
                destination=destination,
                destination_location=origin_location,
                departure_time_s=now_s,
                last_location=origin_location,
                last_moving_time_s=now_s,
                agent=None,
                planned_route_distance_m=0.0,
                selection_class=decision.selection_class,
                history_visit_count_before=decision.visit_count_before,
                selection_candidate_count=decision.candidate_count,
            )
            state.next_trip_number += 1
            self._write_trip(self.logger, failed, now_s, "route_failed", state)
            print(
                "{0}: ruta fallida para {1}: {2}".format(
                    state.vehicle_id, destination.destination_id, error
                )
            )
            state.dwell_started_time_s = now_s
            return
        state.active_trip = ActiveTrip(
            trip_number=state.next_trip_number,
            origin_id=state.current_location_id,
            origin_name=state.current_location_name,
            origin_location=origin_location,
            destination=destination,
            destination_location=destination_location,
            departure_time_s=now_s,
            last_location=origin_location,
            last_moving_time_s=now_s,
            agent=agent,
            planned_route_distance_m=route_distance_m(route),
            selection_class=decision.selection_class,
            history_visit_count_before=decision.visit_count_before,
            selection_candidate_count=decision.candidate_count,
        )
        state.next_trip_number += 1
        print(
            "{0}/{1}: {2} -> {3} [{4}]; ruta planificada {5:.1f} m; "
            "inicio alineado {6:.2f} m".format(
                state.vehicle_id,
                state.active_trip.trip_id,
                state.active_trip.origin_id,
                destination.destination_id,
                decision.selection_class,
                state.active_trip.planned_route_distance_m,
                route_start_offset_m,
            )
        )

    def _write_trip(
        self,
        logger: RunLogger,
        trip: ActiveTrip,
        now_s: float,
        status: str,
        state: Optional[VehicleState] = None,
    ) -> None:
        state = self._state_or_primary(state)
        duration = max(0.0, now_s - trip.departure_time_s)
        average_speed = trip.distance_traveled_m / duration if duration else 0.0
        logger.write_trip(
            {
                "run_id": self.run_id,
                "vehicle_id": state.vehicle_id,
                "trip_id": trip.trip_id,
                "seed": self.config.seed,
                "origin_id": trip.origin_id,
                "origin_name": trip.origin_name,
                "origin_x": trip.origin_location.x,
                "origin_y": trip.origin_location.y,
                "origin_z": trip.origin_location.z,
                "destination_id": trip.destination.destination_id,
                "destination_name": trip.destination.destination_name,
                "destination_category": trip.destination.category,
                "frequency_class": trip.selection_class,
                "selection_class": trip.selection_class,
                "history_visit_count_before": trip.history_visit_count_before,
                "selection_candidate_count": trip.selection_candidate_count,
                "departure_sim_time_s": trip.departure_time_s,
                "arrival_sim_time_s": now_s if status == "completed" else "",
                "travel_time_s": duration,
                "distance_traveled_m": trip.distance_traveled_m,
                "average_speed_mps": average_speed,
                "average_speed_kmh": average_speed * 3.6,
                "collision_count": trip.collision_count,
                "lane_invasion_count": trip.lane_invasion_count,
                "status": status,
            }
        )

    def _finish_trip(
        self, now_s: float, status: str, state: Optional[VehicleState] = None
    ) -> None:
        state = self._state_or_primary(state)
        if state.active_trip is None:
            return
        trip = state.active_trip
        self._write_trip(self.logger, trip, now_s, status, state)
        state.total_distance_traveled_m += trip.distance_traveled_m
        state.total_trip_duration_s += max(0.0, now_s - trip.departure_time_s)
        if status == "completed":
            state.completed_trips += 1
            state.destination_counts[trip.destination.destination_id] += 1
            history_event = state.vehicle_history.record(trip.destination.destination_id)
            self.logger.write_history(
                {
                    "run_id": self.run_id,
                    "vehicle_id": history_event.vehicle_id,
                    "sequence": history_event.sequence,
                    "destination_id": history_event.destination_id,
                    "source": history_event.source,
                    "trip_id": trip.trip_id,
                    "completed_sim_time_s": now_s,
                }
            )
            state.current_destination_id = trip.destination.destination_id
            state.current_location_id = trip.destination.destination_id
            state.current_location_name = trip.destination.destination_name
        else:
            state.current_destination_id = None
            state.current_location_id = "POSITION_AFTER_{0}".format(trip.trip_id.upper())
            state.current_location_name = "Position after {0} ({1})".format(
                trip.trip_id, status
            )
        state.active_trip = None
        state.dwell_started_time_s = now_s
        print(
            "{0}/{1}: {2} ({3:.1f} m)".format(
                state.vehicle_id, trip.trip_id, status, trip.distance_traveled_m
            )
        )

    def _drain_events(
        self, now_s: float, state: Optional[VehicleState] = None
    ) -> None:
        del now_s
        state = self._state_or_primary(state)
        for event in state.event_collector.drain():
            trip_id = state.active_trip.trip_id if state.active_trip else ""
            self.logger.write_event(
                dict(
                    event,
                    run_id=self.run_id,
                    vehicle_id=state.vehicle_id,
                    trip_id=trip_id,
                )
            )
            if state.active_trip is not None:
                if event["event_type"] == "collision":
                    state.active_trip.collision_count += 1
                    state.total_collisions += 1
                elif event["event_type"] == "lane_invasion":
                    state.active_trip.lane_invasion_count += 1
                    state.total_lane_invasions += 1

    def _sample_trajectory(
        self,
        carla_map: Any,
        vehicle: Any,
        frame: int,
        now_s: float,
        state: Optional[VehicleState] = None,
    ) -> None:
        state = self._state_or_primary(state)
        trip = state.active_trip
        if trip is None:
            return
        if trip.last_trajectory_sample_time_s is not None and (
            now_s - trip.last_trajectory_sample_time_s
            < self.config.trajectory_sampling_interval_seconds
        ):
            return
        location = vehicle.get_location()
        velocity = vehicle.get_velocity()
        acceleration = vehicle.get_acceleration()
        waypoint = carla_map.get_waypoint(location, project_to_road=True)
        speed = speed_mps(velocity)
        self.logger.write_trajectory(
            {
                "run_id": self.run_id,
                "vehicle_id": state.vehicle_id,
                "trip_id": trip.trip_id,
                "frame": frame,
                "simulation_time_s": now_s,
                "x": location.x,
                "y": location.y,
                "z": location.z,
                "speed_mps": speed,
                "speed_kmh": speed * 3.6,
                "acceleration_mps2": speed_mps(acceleration),
                "road_id": waypoint.road_id if waypoint else "",
                "lane_id": waypoint.lane_id if waypoint else "",
                "distance_traveled_m": trip.distance_traveled_m,
            }
        )
        trip.last_trajectory_sample_time_s = now_s

    def _update_active_trip(
        self,
        carla_map: Any,
        vehicle: Any,
        frame: int,
        now_s: float,
        state: Optional[VehicleState] = None,
    ) -> None:
        state = self._state_or_primary(state)
        trip = state.active_trip
        if trip is None:
            return
        location = vehicle.get_location()
        trip.distance_traveled_m += trip.last_location.distance(location)
        trip.last_location = location
        current_speed = speed_mps(vehicle.get_velocity())
        if current_speed > self.config.blocked_speed_threshold_mps:
            trip.last_moving_time_s = now_s
        self._sample_trajectory(carla_map, vehicle, frame, now_s, state)
        if location.distance(trip.destination_location) <= self.config.arrival_threshold_m:
            self._finish_trip(now_s, "completed", state)
        elif now_s - trip.departure_time_s >= self.config.max_trip_time_seconds:
            self._finish_trip(now_s, "timeout", state)
        elif now_s - trip.last_moving_time_s >= self.config.blocked_time_threshold_seconds:
            self._finish_trip(now_s, "blocked", state)

    @staticmethod
    def _brake(carla_module: Any, vehicle: Any) -> None:
        vehicle.apply_control(
            carla_module.VehicleControl(throttle=0.0, steer=0.0, brake=1.0)
        )

    def _write_metrics(self, logger: RunLogger, simulation_duration_s: float) -> None:
        trips_started = sum(state.trips_started for state in self.vehicle_states)
        trips_completed = sum(state.completed_trips for state in self.vehicle_states)
        total_distance = sum(
            state.total_distance_traveled_m for state in self.vehicle_states
        )
        total_duration = sum(
            state.total_trip_duration_s for state in self.vehicle_states
        )
        destination_counts = Counter()
        for state in self.vehicle_states:
            destination_counts.update(state.destination_counts)
        distribution = (
            {
                destination.destination_id: (
                    destination_counts[destination.destination_id] / trips_completed
                )
                for destination in self.destinations
            }
            if trips_completed
            else {}
        )
        aggregate_average_speed_mps = (
            total_distance / total_duration if total_duration else 0.0
        )
        logger.write_metrics(
            {
                "run_id": self.run_id,
                "vehicle_count": len(self.vehicle_states),
                "trips_started": trips_started,
                "trips_completed": trips_completed,
                "trips_incomplete": trips_started - trips_completed,
                "simulation_duration_s": simulation_duration_s,
                "total_distance_traveled_m": total_distance,
                "aggregate_average_speed_mps": aggregate_average_speed_mps,
                "aggregate_average_speed_kmh": aggregate_average_speed_mps * 3.6,
                "total_collisions": sum(
                    state.total_collisions for state in self.vehicle_states
                ),
                "total_lane_invasions": sum(
                    state.total_lane_invasions for state in self.vehicle_states
                ),
                "observed_destination_distribution": json.dumps(
                    distribution, ensure_ascii=False, sort_keys=True
                ),
            }
        )

    def _load_vehicle_histories(self) -> None:
        history_path = self.project_root / self.config.vehicle_history_config
        allowed_destination_ids = set(self.destinations_by_id)
        for state in self.vehicle_states:
            state.vehicle_history = VehicleHistory.from_csv(
                history_path, state.vehicle_id, allowed_destination_ids
            )
            state.initial_history_counts = dict(
                sorted(state.vehicle_history.counts.items())
            )

    def _configure_blueprint(
        self, blueprint: Any, state: VehicleState
    ) -> None:
        if blueprint.has_attribute("role_name"):
            blueprint.set_attribute("role_name", state.vehicle_id)
        if blueprint.has_attribute("color"):
            colors = blueprint.get_attribute("color").recommended_values
            if colors:
                blueprint.set_attribute("color", state.actor_rng.choice(colors))

    def _set_initial_location_metadata(self, state: VehicleState) -> None:
        state.current_location_name = "Initial spawn point {0}".format(
            state.actual_initial_spawn_point_index
        )
        state.current_location_id = "ORIGIN_SPAWN_{0:03d}".format(
            state.actual_initial_spawn_point_index
        )
        matching_origins = [
            destination
            for destination in self.destinations
            if destination.reference_type == "spawn_point"
            and destination.spawn_point_index == state.actual_initial_spawn_point_index
        ]
        if matching_origins:
            state.current_destination_id = matching_origins[0].destination_id
            state.current_location_id = matching_origins[0].destination_id
            state.current_location_name = matching_origins[0].destination_name

    def _write_initial_histories(self) -> None:
        for state in self.vehicle_states:
            for history_event in state.vehicle_history.events:
                self.logger.write_history(
                    {
                        "run_id": self.run_id,
                        "vehicle_id": history_event.vehicle_id,
                        "sequence": history_event.sequence,
                        "destination_id": history_event.destination_id,
                        "source": history_event.source,
                        "trip_id": "",
                        "completed_sim_time_s": "",
                    }
                )

    def run(self) -> Path:
        import carla

        configure_carla_agents(carla, self.carla_pythonapi)
        random.seed(self.config.seed)
        client = carla.Client(self.config.host, self.config.port)
        client.set_timeout(self.config.client_timeout_seconds)
        world = None
        original_settings = None
        start_sim_time_s = 0.0
        try:
            world = client.get_world()
            active_map = world.get_map()
            if (
                active_map.name.replace("\\", "/").rsplit("/", 1)[-1].lower()
                != self.config.town.lower()
            ):
                raise RuntimeError(
                    "El mapa activo es {0}; se esperaba {1}.".format(
                        active_map.name, self.config.town
                    )
                )
            self.destinations = load_destinations(
                self.project_root / self.config.destinations_config, active_map.name
            )
            self.destinations_by_id = {
                destination.destination_id: destination
                for destination in self.destinations
            }
            self._validate_destination_categories()
            self._validate_destination_cycle()
            validate_destinations_on_map(carla, active_map, self.destinations)
            self._load_vehicle_histories()

            original_settings = world.get_settings()
            self._apply_world_settings(world, self.config)
            world.tick()
            spawn_points = active_map.get_spawn_points()
            blueprints = safe_vehicle_blueprints(
                world, self.config.vehicle_blueprint_filter
            )

            for state in self.vehicle_states:
                blueprint = state.actor_rng.choice(blueprints)
                self._configure_blueprint(blueprint, state)
                state.actor, state.actual_initial_spawn_point_index = (
                    spawn_vehicle_at_first_available_point(
                        world,
                        blueprint,
                        carla,
                        active_map,
                        spawn_points,
                        state.requested_spawn_point_index,
                        self.config.initial_spawn_fallback_enabled,
                        state.vehicle_id,
                    )
                )
                self._set_initial_location_metadata(state)
                if (
                    state.actual_initial_spawn_point_index
                    != state.requested_spawn_point_index
                ):
                    print(
                        "{0}: spawn point {1} ocupado/no disponible; se usará {2}.".format(
                            state.vehicle_id,
                            state.requested_spawn_point_index,
                            state.actual_initial_spawn_point_index,
                        )
                    )
                self._brake(carla, state.actor)

            # Every newly spawned actor receives the same synchronization frame.
            world.tick()
            for state in self.vehicle_states:
                expected_spawn_transform = driving_transform_from_spawn_point(
                    carla,
                    active_map,
                    spawn_points[state.actual_initial_spawn_point_index],
                )
                if expected_spawn_transform is None:
                    raise RuntimeError(
                        "No se pudo reconstruir el waypoint del spawn inicial de {0}.".format(
                            state.vehicle_id
                        )
                    )
                synchronized_location = state.actor.get_location()
                state.initial_spawn_position_error_m = validate_initial_spawn_location(
                    synchronized_location,
                    expected_spawn_transform.location,
                    self.config.initial_spawn_validation_tolerance_m,
                )
                state.actual_initial_spawn_location = {
                    "x": synchronized_location.x,
                    "y": synchronized_location.y,
                    "z": synchronized_location.z,
                }
                print(
                    "{0}: spawn {1} sincronizado: x={2:.3f}, y={3:.3f}, z={4:.3f}; "
                    "error={5:.2f} m".format(
                        state.vehicle_id,
                        state.actual_initial_spawn_point_index,
                        synchronized_location.x,
                        synchronized_location.y,
                        synchronized_location.z,
                        state.initial_spawn_position_error_m,
                    )
                )

            collision_bp = world.get_blueprint_library().find(
                "sensor.other.collision"
            )
            lane_bp = world.get_blueprint_library().find(
                "sensor.other.lane_invasion"
            )
            for state in self.vehicle_states:
                for sensor_bp, callback in (
                    (collision_bp, state.event_collector.collision),
                    (lane_bp, state.event_collector.lane_invasion),
                ):
                    sensor = world.spawn_actor(
                        sensor_bp, carla.Transform(), attach_to=state.actor
                    )
                    sensor.listen(callback)
                    state.sensors.append(sensor)

            world.tick()
            snapshot = world.get_snapshot()
            start_sim_time_s = snapshot.timestamp.elapsed_seconds
            now_s = start_sim_time_s
            output_directory = self._output_directory()
            self.logger = RunLogger(output_directory)
            self._write_initial_histories()
            self._write_run_config(
                output_directory, client.get_server_version(), self.destinations
            )
            planner = build_global_route_planner(
                active_map, self.config.route_sampling_resolution_m
            )
            for state in self.vehicle_states:
                self._start_trip(
                    carla,
                    active_map,
                    planner,
                    state.actor,
                    start_sim_time_s,
                    state,
                )

            wall_start = time.monotonic()
            while True:
                frame = world.tick()
                snapshot = world.get_snapshot()
                now_s = snapshot.timestamp.elapsed_seconds
                elapsed_s = now_s - start_sim_time_s
                for state in self.vehicle_states:
                    self._drain_events(now_s, state)
                    self._update_active_trip(
                        active_map, state.actor, frame, now_s, state
                    )
                if elapsed_s >= self.config.duration_seconds:
                    break
                for state in self.vehicle_states:
                    if state.active_trip is None:
                        self._brake(carla, state.actor)
                        if state.dwell_started_time_s is not None and (
                            now_s - state.dwell_started_time_s
                            >= self.config.destination_dwell_time_seconds
                        ):
                            self._start_trip(
                                carla,
                                active_map,
                                planner,
                                state.actor,
                                now_s,
                                state,
                            )
                    else:
                        state.actor.apply_control(state.active_trip.agent.run_step())
                # This only caps wall-clock pace; academic time remains simulated time.
                target_wall_elapsed = elapsed_s / float(self.simulation_speed)
                remaining = target_wall_elapsed - (time.monotonic() - wall_start)
                if remaining > 0.0:
                    time.sleep(remaining)

            for state in self.vehicle_states:
                if state.active_trip is not None:
                    self._finish_trip(now_s, "aborted", state)
                self._drain_events(now_s, state)
            self._write_metrics(self.logger, now_s - start_sim_time_s)
            print("Corrida completada. Resultados: {0}".format(output_directory))
            return output_directory
        finally:
            if self.logger is not None:
                self.logger.close()
            for state in self.vehicle_states:
                for sensor in state.sensors:
                    try:
                        if sensor.is_alive:
                            sensor.stop()
                            sensor.destroy()
                    except RuntimeError:
                        pass
                state.sensors = []
            for state in reversed(self.vehicle_states):
                try:
                    if state.actor is not None and state.actor.is_alive:
                        state.actor.destroy()
                except RuntimeError:
                    pass
                state.actor = None
            if world is not None and original_settings is not None:
                try:
                    world.tick()
                    world.apply_settings(original_settings)
                except RuntimeError:
                    pass
