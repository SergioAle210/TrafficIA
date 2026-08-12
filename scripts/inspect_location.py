"""Print a spectator-selected location as a destination CSV template."""

from __future__ import annotations

import argparse
import math
import sys
from typing import List, Optional

import carla


def short_map_name(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1].lower()


def nearest_spawn_point_index(carla_map: carla.Map, location: carla.Location) -> int:
    spawn_points = carla_map.get_spawn_points()
    if not spawn_points:
        return -1
    return min(
        range(len(spawn_points)),
        key=lambda index: spawn_points[index].location.distance(location),
    )


def draw_spawn_points(
    world: carla.World,
    spawn_points: List[carla.Transform],
    lifetime_seconds: float,
    highlight_index: Optional[int],
) -> None:
    """Draw each CARLA-recommended spawn point with its index and direction."""

    normal_color = carla.Color(255, 255, 255)
    highlighted_color = carla.Color(255, 80, 80)
    for index, spawn_point in enumerate(spawn_points):
        is_highlighted = index == highlight_index
        color = highlighted_color if is_highlighted else normal_color
        location = spawn_point.location
        label_location = location + carla.Location(z=1.5)
        forward = spawn_point.get_forward_vector()
        arrow_end = carla.Location(
            x=location.x + forward.x * 3.0,
            y=location.y + forward.y * 3.0,
            z=location.z + forward.z * 3.0,
        )
        world.debug.draw_string(
            label_location,
            str(index),
            draw_shadow=False,
            color=color,
            life_time=lifetime_seconds,
            persistent_lines=True,
        )
        world.debug.draw_arrow(
            location,
            arrow_end,
            thickness=0.12 if is_highlighted else 0.06,
            arrow_size=0.25 if is_highlighted else 0.15,
            color=color,
            life_time=lifetime_seconds,
            persistent_lines=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspecciona el spectator y devuelve un waypoint vial para destinations_config.csv."
    )
    parser.add_argument("--town", default="Town01", help="Mapa que se espera ya esté activo.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument(
        "--show-spawn-points",
        action="store_true",
        help="Dibuja índices y orientación de todos los spawn points en la ventana de CARLA.",
    )
    parser.add_argument(
        "--highlight-spawn-point",
        type=int,
        default=None,
        help="Índice a resaltar en rojo; por defecto se resalta el más cercano al spectator.",
    )
    parser.add_argument(
        "--debug-lifetime-seconds",
        type=float,
        default=120.0,
        help="Tiempo simulado que permanecen los índices dibujados (por defecto: 120).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = carla.Client(args.host, args.port)
    client.set_timeout(30.0)
    try:
        world = client.get_world()
        carla_map = world.get_map()
        if short_map_name(carla_map.name) != short_map_name(args.town):
            raise RuntimeError("El mapa activo es {0}; se esperaba {1}.".format(carla_map.name, args.town))
        spectator_location = world.get_spectator().get_transform().location
        waypoint = carla_map.get_waypoint(
            spectator_location, project_to_road=True, lane_type=carla.LaneType.Driving
        )
        if waypoint is None:
            raise RuntimeError("No se encontró un waypoint de conducción cerca del spectator.")
        road_location = waypoint.transform.location
        spawn_index = nearest_spawn_point_index(carla_map, road_location)
        spawn_points = carla_map.get_spawn_points()
        if args.debug_lifetime_seconds <= 0.0:
            raise RuntimeError("debug_lifetime_seconds debe ser mayor que cero.")
        if args.highlight_spawn_point is not None and (
            args.highlight_spawn_point < 0 or args.highlight_spawn_point >= len(spawn_points)
        ):
            raise RuntimeError(
                "highlight_spawn_point inválido: {0}; el mapa tiene {1} puntos.".format(
                    args.highlight_spawn_point, len(spawn_points)
                )
            )
        if args.show_spawn_points:
            highlighted_index = (
                args.highlight_spawn_point
                if args.highlight_spawn_point is not None
                else spawn_index
            )
            draw_spawn_points(world, spawn_points, args.debug_lifetime_seconds, highlighted_index)
            print(
                "Spawn points dibujados durante {0:.0f} s; el índice {1} aparece en rojo.".format(
                    args.debug_lifetime_seconds, highlighted_index
                )
            )
        print("Spectator: x={0:.3f}, y={1:.3f}, z={2:.3f}".format(
            spectator_location.x, spectator_location.y, spectator_location.z
        ))
        print("Waypoint vial accesible: x={0:.3f}, y={1:.3f}, z={2:.3f}".format(
            road_location.x, road_location.y, road_location.z
        ))
        print("road_id={0}, lane_id={1}, s={2:.3f}, is_junction={3}".format(
            waypoint.road_id, waypoint.lane_id, waypoint.s, waypoint.is_junction
        ))
        print("spawn_point_index más cercano: {0}".format(spawn_index))
        print("\nPlantilla CSV (usa el waypoint vial, no la ubicación física del edificio):")
        print(
            "DEST_MANUAL,Nombre editable,{0},categoria_provisional,routine,1.0,true,coordinates,,{1:.3f},{2:.3f},{3:.3f},{4},{5},Descripción editable".format(
                args.town, road_location.x, road_location.y, road_location.z,
                waypoint.road_id, waypoint.lane_id
            )
        )
        return 0
    except RuntimeError as error:
        print("Error: {0}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
