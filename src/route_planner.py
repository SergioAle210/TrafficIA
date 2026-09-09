"""CARLA navigation wrappers used by the multi-vehicle trip runner."""

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


def plan_route(
    planner: Any,
    origin_location: Any,
    destination_location: Any,
    endpoint_tolerance_m: float = 5.0,
) -> List[Any]:
    """Return a route whose first and last waypoints cover both requested ends."""

    route = list(planner.trace_route(origin_location, destination_location))
    if not route:
        raise RuntimeError("GlobalRoutePlanner no encontró una ruta entre origen y destino.")
    route_end = route[-1][0].transform.location
    endpoint_error_m = route_end.distance(destination_location)
    if endpoint_error_m > endpoint_tolerance_m:
        raise RuntimeError(
            "GlobalRoutePlanner terminó a {0:.2f} m del destino; máximo permitido: {1:.2f} m.".format(
                endpoint_error_m, endpoint_tolerance_m
            )
        )
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


def arrival_route(route: Sequence[Any], goal: Any) -> List[Any]:
    """Replace an early/overshooting terminal tail with the exact lane goal.

    OpenDRIVE negative lanes travel toward increasing s, positive lanes toward
    decreasing s. Keep the last preceding waypoint on the goal's lane, then
    sample that lane every 0.5 m through the requested stopping point.
    """
    direction = 1 if goal.lane_id < 0 else -1
    anchors = [i for i, (wp, _) in enumerate(route)
               if (wp.road_id, wp.section_id, wp.lane_id) ==
               (goal.road_id, goal.section_id, goal.lane_id)
               and (goal.s-wp.s)*direction >= -0.01]
    if not anchors:
        raise RuntimeError("La ruta no alcanza un tramo anterior al destino en su carril.")
    index = anchors[-1]
    result = list(route[:index+1])
    current, option = result[-1]
    remaining = (goal.s-current.s)*direction
    if remaining > 10.0:
        raise RuntimeError("El tramo final sin cubrir supera 10 m; se rechaza la ruta.")
    while remaining > 0.5:
        candidates = [wp for wp in current.next(0.5)
                      if (wp.road_id, wp.section_id, wp.lane_id) ==
                      (goal.road_id, goal.section_id, goal.lane_id)]
        if len(candidates) != 1:
            raise RuntimeError("No hay una continuación única al punto de parada.")
        current = candidates[0]
        next_remaining = (goal.s-current.s)*direction
        if next_remaining >= remaining:
            raise RuntimeError("La continuación no progresa hacia el destino.")
        result.append((current, option))
        remaining = next_remaining
    if result[-1][0].transform.location.distance(goal.transform.location) < 0.01:
        result[-1] = (goal, option)
    else:
        result.append((goal, option))
    return result


def steering_continuation(route: Sequence[Any], distance_m: float) -> List[Any]:
    """Keep lateral targets ahead while stopping; not part of trip distance.

    Do not invent a turn at a branching junction. Reject ambiguous support
    before spawning a trip instead of driving beyond its planned lane.
    """
    from agents.navigation.local_planner import RoadOption

    result = list(route)
    current = result[-1][0]
    covered = 0.0
    while covered < distance_m:
        step = min(0.5, distance_m-covered)
        candidates = current.next(step)
        if len(candidates) != 1:
            raise RuntimeError("No hay guía lateral única después del punto de parada.")
        current = candidates[0]
        result.append((current, RoadOption.LANEFOLLOW))
        covered += step
    return result


def build_basic_agent(
    vehicle: Any, route: Sequence[Any], target_speed_kmh: float,
    distance_ratio: float = 0.1,
) -> Any:
    """Create an official CARLA BasicAgent configured with a precomputed plan."""

    from src.carla_agent import CollinearSafeBasicAgent

    # A fresh options dict avoids CARLA's mutable default being shared by agents.
    # Town01 tight turns: the stock 0.5 s horizon skips the curve's interior
    # waypoints at 20 km/h and cuts toward the curb. Keep the stock 3 m base,
    # PID gains and speed; shorten only the speed-dependent purge distance.
    agent = CollinearSafeBasicAgent(
        vehicle, target_speed=target_speed_kmh, opt_dict={"distance_ratio": distance_ratio}
    )
    agent.set_global_plan(list(route), stop_waypoint_creation=True, clean_queue=True)
    return agent
