"""Read-only route/control telemetry; no CARLA import or control modifications."""

import math


ROUTE_FIELDS = [
    "run_id", "vehicle_id", "trip_id", "index", "x", "y", "z", "yaw_deg",
    "road_id", "lane_id", "lane_width_m", "road_option",
]
CONTROL_FIELDS = [
    "run_id", "vehicle_id", "trip_id", "frame", "simulation_time_s",
    "x", "y", "z", "yaw_deg", "speed_mps", "steer", "throttle", "brake",
    "target_x", "target_y", "target_yaw_deg", "target_road_id", "target_lane_id",
    "target_distance_m", "purge_distance_m", "route_segment_index",
    "route_x", "route_y", "route_yaw_deg", "route_road_id", "route_lane_id",
    "route_distance_m", "lateral_error_m", "heading_error_deg", "lane_width_m",
]


def wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


class RouteTrace:
    """Snapshot the full plan before LocalPlanner destructively consumes it.

    Lateral error is positive to the right in CARLA's XY coordinates. The
    nearest nonzero polyline segment supplies the reference, including in
    junctions where Map.get_waypoint may select a different connecting lane.
    This measures tracking of the plan, not physical clearance from a curb.
    """

    def __init__(self, route):
        self.points = []
        for index, (waypoint, option) in enumerate(route):
            transform = waypoint.transform
            self.points.append(dict(
                index=index, x=transform.location.x, y=transform.location.y,
                z=transform.location.z, yaw_deg=transform.rotation.yaw,
                road_id=waypoint.road_id, lane_id=waypoint.lane_id,
                lane_width_m=waypoint.lane_width, road_option=str(option),
            ))
        self.segments = []
        for a, b in zip(self.points, self.points[1:]):
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]
            length2 = dx * dx + dy * dy
            if length2 > 1e-8:
                self.segments.append((a, b, dx, dy, length2))

    def project(self, x, y, yaw_deg):
        nearest = None
        for a, b, dx, dy, length2 in self.segments:
            fraction = max(0.0, min(1.0, ((x-a["x"])*dx + (y-a["y"])*dy) / length2))
            px, py = a["x"] + fraction*dx, a["y"] + fraction*dy
            distance2 = (x-px)**2 + (y-py)**2
            if nearest is None or distance2 < nearest[0]:
                nearest = (distance2, a, b, dx, dy, fraction, px, py, length2)
        if nearest is None:
            return {}
        distance2, a, b, dx, dy, fraction, px, py, length2 = nearest
        # Interpolate the actual waypoint tangents, including the -180/180 seam.
        yaw = a["yaw_deg"] + fraction * wrap_degrees(b["yaw_deg"] - a["yaw_deg"])
        return dict(
            route_segment_index=a["index"], route_x=px, route_y=py,
            route_yaw_deg=wrap_degrees(yaw), route_road_id=a["road_id"],
            route_lane_id=a["lane_id"], route_distance_m=math.sqrt(distance2),
            lateral_error_m=(dx*(y-py) - dy*(x-px)) / math.sqrt(length2),
            heading_error_deg=wrap_degrees(yaw_deg-yaw),
            lane_width_m=a["lane_width_m"],
        )

    def sample(self, vehicle, agent, control):
        transform = vehicle.get_transform()
        location = transform.location
        velocity = vehicle.get_velocity()
        local = agent.get_local_planner()
        target = local.target_waypoint
        row = dict(
            x=location.x, y=location.y, z=location.z, yaw_deg=transform.rotation.yaw,
            speed_mps=math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2),
            steer=control.steer, throttle=control.throttle, brake=control.brake,
            purge_distance_m=getattr(local, "_min_distance", ""),
        )
        if target is not None and local.get_plan():
            row.update(
                target_x=target.transform.location.x, target_y=target.transform.location.y,
                target_yaw_deg=target.transform.rotation.yaw,
                target_road_id=target.road_id, target_lane_id=target.lane_id,
                target_distance_m=location.distance(target.transform.location),
            )
        row.update(self.project(location.x, location.y, transform.rotation.yaw))
        return row
