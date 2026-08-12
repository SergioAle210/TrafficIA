"""CARLA navigation wrappers used by the one-vehicle trip runner."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence


def configure_carla_agents(carla_module: Any, carla_pythonapi: Optional[str] = None) -> None:
    """Make CARLA's bundled ``agents`` package importable before actors spawn.

    CARLA distributes ``carla`` (the API) and ``agents`` (BasicAgent and the
    GlobalRoutePlanner) separately. Installing only the CARLA wheel/egg often
    exposes the former but not the latter. The explicit CLI path must be the
    directory that directly contains the ``agents`` folder, usually
    ``...\\PythonAPI\\carla``.
    """

    try:
        importlib.import_module("agents.navigation.global_route_planner")
        importlib.import_module("agents.navigation.basic_agent")
        return
    except ModuleNotFoundError as error:
        if error.name != "agents":
            raise

    candidates = []
    if carla_pythonapi:
        candidates.append(Path(carla_pythonapi))
    environment_path = os.environ.get("CARLA_PYTHONAPI")
    if environment_path:
        candidates.append(Path(environment_path))
    carla_file = getattr(carla_module, "__file__", None)
    if carla_file:
        file_path = Path(carla_file)
        candidates.extend(parent for parent in file_path.parents)
    candidates.extend(Path(path) for path in sys.path if path)

    checked_paths = set()
    for candidate in candidates:
        for pythonapi_path in (candidate, candidate / "carla"):
            try:
                resolved = pythonapi_path.resolve()
            except OSError:
                continue
            if resolved in checked_paths or not (resolved / "agents").is_dir():
                continue
            checked_paths.add(resolved)
            if str(resolved) not in sys.path:
                sys.path.insert(0, str(resolved))
            importlib.invalidate_caches()
            importlib.import_module("agents.navigation.global_route_planner")
            importlib.import_module("agents.navigation.basic_agent")
            return

    raise RuntimeError(
        "No se encontró el paquete 'agents' de CARLA. Indica --carla-pythonapi "
        "con la carpeta que contiene 'agents' (por ejemplo, "
        "C:\\CARLA\\WindowsNoEditor\\PythonAPI\\carla) o define CARLA_PYTHONAPI."
    )


def build_global_route_planner(carla_map: Any, sampling_resolution: float) -> Any:
    """Build CARLA's OpenDRIVE-topology planner for the active map."""

    from agents.navigation.global_route_planner import GlobalRoutePlanner

    return GlobalRoutePlanner(carla_map, sampling_resolution)


def plan_route(planner: Any, origin_location: Any, destination_location: Any) -> List[Any]:
    """Return the ordered ``[Waypoint, RoadOption]`` route from CARLA."""

    route = list(planner.trace_route(origin_location, destination_location))
    if not route:
        raise RuntimeError("GlobalRoutePlanner no encontró una ruta entre origen y destino.")
    return route


def validate_route_start(
    route: Sequence[Any], origin_location: Any, tolerance_m: float
) -> float:
    """Ensure the route begins near the synchronized physical origin."""

    if not route:
        raise RuntimeError("No se puede validar una ruta vacía.")
    first_waypoint_location = route[0][0].transform.location
    distance_m = origin_location.distance(first_waypoint_location)
    if distance_m > tolerance_m:
        raise RuntimeError(
            "La ruta comienza a {0:.2f} m del origen real; máximo permitido: {1:.2f} m. "
            "Se cancela el viaje para evitar un giro hacia una ruta desalineada.".format(
                distance_m, tolerance_m
            )
        )
    return distance_m


def route_distance_m(route: Sequence[Any]) -> float:
    """Approximate planned route length from consecutive CARLA waypoints."""

    total_distance = 0.0
    previous = None
    for waypoint, _road_option in route:
        location = waypoint.transform.location
        if previous is not None:
            total_distance += previous.distance(location)
        previous = location
    return total_distance


def build_basic_agent(vehicle: Any, route: Sequence[Any], target_speed_kmh: float) -> Any:
    """Create an official CARLA BasicAgent configured with a precomputed plan."""

    from agents.navigation.basic_agent import BasicAgent

    agent = BasicAgent(vehicle, target_speed=target_speed_kmh)
    agent.set_global_plan(list(route), stop_waypoint_creation=True, clean_queue=True)
    return agent
