"""Observe Town01/T01_067 arrivals without changing TripSimulation controls.

Accepts the same CLI as run_trip_simulation.py; pass the multi-vehicle config.
Adds a per-frame dwell log within 25 m of T01_067, including completed trips.
"""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_trip_simulation import configuration_from_args, parse_args
from src.navigation.navigation_diagnostics import RouteTrace, wrap_degrees
from src.simulation.trip_runner import TripSimulation, resolve_destination_location, speed_mps


FIELDS = [
    "run_id", "vehicle_id", "frame", "simulation_time_s", "phase_before",
    "phase_after", "trip_before", "trip_after", "context_trip_id", "destination_id",
    "dwell_elapsed_s", "x", "y", "z", "yaw_deg", "pitch_deg", "roll_deg",
    "vx", "vy", "vz", "speed_mps", "velocity_yaw_deg", "angular_velocity_z_deg_s",
    "observed_steer", "observed_throttle", "observed_brake", "distance_to_destination_m",
    "map_road_id", "map_lane_id", "map_s", "map_yaw_deg", "map_heading_error_deg",
    "map_left_marking", "map_right_marking", "reference_lateral_m",
    "reference_heading_error_deg", "sensor_corners_json", "physical_vertices_json",
]


def sensor_corners_xy(transform, bounding_box):
    """Match LaneInvasionSensor.cpp 0.9.15 MakeBounds, including its offset.

    Stock code adds box.location in world axes, rotates extents only by yaw,
    and ignores pitch/roll. This is deliberately separate from physical vertices.
    Order: front right, rear right, front left, rear left.
    """
    yaw = math.radians(transform.rotation.yaw)
    c, s = math.cos(yaw), math.sin(yaw)
    x = transform.location.x + bounding_box.location.x
    y = transform.location.y + bounding_box.location.y
    ex, ey = bounding_box.extent.x, bounding_box.extent.y
    return [(x+dx*c-dy*s, y+dx*s+dy*c)
            for dx, dy in [(ex,ey),(-ex,ey),(ex,-ey),(-ex,-ey)]]


def waypoint_record(wp):
    t = wp.transform
    return dict(x=t.location.x, y=t.location.y, z=t.location.z, yaw_deg=t.rotation.yaw,
                road_id=wp.road_id, section_id=wp.section_id, lane_id=wp.lane_id,
                s=wp.s, lane_width_m=wp.lane_width, left_marking=str(wp.left_lane_marking.type),
                right_marking=str(wp.right_lane_marking.type))


class DwellDiagnosticSimulation(TripSimulation):
    """Delegate every state transition/control to the unchanged base runner."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dwell_file = None
        self._dwell_writer = None
        self._last_trips = {}
        self._focus = None
        self._reference = None

    def _write_run_config(self, output_directory, server_version, destinations):
        super()._write_run_config(output_directory, server_version, destinations)
        import carla
        vehicle = self.primary_vehicle_state.actor
        carla_map = vehicle.get_world().get_map()
        self._focus = resolve_destination_location(carla, carla_map, self.destinations_by_id["T01_067"])
        goal_wp = carla_map.get_waypoint(self._focus)
        # Preserve both lanes and their markings, with enough extent for the
        # full vehicle footprint at the edge of the sampling circle.
        waypoints = [wp for wp in carla_map.generate_waypoints(0.25)
                     if wp.transform.location.distance(self._focus) <= 35]
        reference = [wp for wp in waypoints if
                     (wp.road_id, wp.lane_id) == (goal_wp.road_id, goal_wp.lane_id)]
        reference.sort(key=lambda wp: wp.s, reverse=goal_wp.lane_id > 0)
        self._reference = RouteTrace([(wp, "reference_lane") for wp in reference])
        geometry = dict(destination_id="T01_067", goal=waypoint_record(goal_wp),
                        sampling_radius_m=25, map_sampling_m=0.25,
                        lanes=[waypoint_record(wp) for wp in waypoints], vehicles=[])
        for state in self.vehicle_states:
            bb = state.actor.bounding_box
            geometry["vehicles"].append(dict(
                vehicle_id=state.vehicle_id, blueprint=state.actor.type_id,
                bbox_location=[bb.location.x, bb.location.y, bb.location.z],
                bbox_extent=[bb.extent.x, bb.extent.y, bb.extent.z],
                bbox_rotation=[bb.rotation.pitch, bb.rotation.yaw, bb.rotation.roll],
            ))
        (output_directory / "dwell_geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf8")
        metadata = dict(
            schema_version=1, subclass="DwellDiagnosticSimulation",
            sampling="after each tick; before state update and before any command for the next tick",
            observed_control="Vehicle.get_control at sample time; the already-applied command, not a new command",
            phases="phase_before/after bracket the unchanged _update_active_trip; start appears on next sample",
            reference="fixed destination road/lane polyline; right positive; physical clearance is not inferred",
            sensor_corners="stock 0.9.15 MakeBounds XY, in FR/RR/FL/RL order; compare separately with physical vertices",
            source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                           ["src/simulation/trip_runner.py", "src/navigation/route_planner.py", "src/navigation/carla_agent.py", "src/navigation/arrival.py",
                            "src/navigation/navigation_diagnostics.py", "scripts/diagnose_destination_dwell.py"]},
        )
        (output_directory / "dwell_diagnostic_config.json").write_text(json.dumps(metadata, indent=2), encoding="utf8")
        self._dwell_file = (output_directory / "dwell_log.csv").open("w", newline="", encoding="utf8")
        self._dwell_writer = csv.DictWriter(self._dwell_file, fieldnames=FIELDS)
        self._dwell_writer.writeheader()

    def _finish_trip(self, now_s, status, state=None):
        state = self._state_or_primary(state)
        trip = state.active_trip
        result = super()._finish_trip(now_s, status, state)
        if trip is not None:
            self._last_trips[state.vehicle_id] = trip
        return result

    def _observe(self, carla_map, vehicle, frame, now_s, state):
        import carla
        t = vehicle.get_transform()
        if self._focus is None or t.location.distance(self._focus) > 25:
            return None
        trip = state.active_trip or self._last_trips.get(state.vehicle_id)
        v = vehicle.get_velocity()
        u = vehicle.get_control()
        wp = carla_map.get_waypoint(t.location, project_to_road=True)
        reference = self._reference.project(t.location.x, t.location.y, t.rotation.yaw)
        corners = []
        for x,y in sensor_corners_xy(t, vehicle.bounding_box):
            corner_wp = carla_map.get_waypoint(carla.Location(x,y,t.location.z), project_to_road=False)
            projected = self._reference.project(x, y, t.rotation.yaw)
            corners.append(dict(x=x, y=y, reference_lateral_m=projected.get("lateral_error_m"),
                                road_id=corner_wp.road_id if corner_wp else None,
                                lane_id=corner_wp.lane_id if corner_wp else None))
        vertices = vehicle.bounding_box.get_world_vertices(t)
        return dict(
            run_id=self.run_id, vehicle_id=state.vehicle_id, frame=frame, simulation_time_s=now_s,
            phase_before="travel" if state.active_trip else "dwell",
            trip_before=state.active_trip.trip_id if state.active_trip else "",
            context_trip_id=trip.trip_id if trip else "",
            destination_id=trip.destination.destination_id if trip else "",
            x=t.location.x, y=t.location.y, z=t.location.z, yaw_deg=t.rotation.yaw,
            pitch_deg=t.rotation.pitch, roll_deg=t.rotation.roll,
            vx=v.x, vy=v.y, vz=v.z, speed_mps=speed_mps(v),
            velocity_yaw_deg=math.degrees(math.atan2(v.y,v.x)) if math.hypot(v.x,v.y)>0.01 else "",
            angular_velocity_z_deg_s=vehicle.get_angular_velocity().z,
            observed_steer=u.steer, observed_throttle=u.throttle, observed_brake=u.brake,
            distance_to_destination_m=t.location.distance(trip.destination_location) if trip else "",
            map_road_id=wp.road_id if wp else "", map_lane_id=wp.lane_id if wp else "",
            map_s=wp.s if wp else "", map_yaw_deg=wp.transform.rotation.yaw if wp else "",
            map_heading_error_deg=wrap_degrees(t.rotation.yaw-wp.transform.rotation.yaw) if wp else "",
            map_left_marking=str(wp.left_lane_marking.type) if wp else "",
            map_right_marking=str(wp.right_lane_marking.type) if wp else "",
            reference_lateral_m=reference.get("lateral_error_m", ""),
            reference_heading_error_deg=reference.get("heading_error_deg", ""),
            sensor_corners_json=json.dumps(corners),
            physical_vertices_json=json.dumps([[v.x,v.y,v.z] for v in vertices]),
        )

    def _update_active_trip(self, carla_map, vehicle, frame, now_s, state=None):
        state = self._state_or_primary(state)
        row = self._observe(carla_map, vehicle, frame, now_s, state)
        result = super()._update_active_trip(carla_map, vehicle, frame, now_s, state)
        if row is not None:
            row.update(phase_after="travel" if state.active_trip else "dwell",
                       trip_after=state.active_trip.trip_id if state.active_trip else "",
                       dwell_elapsed_s=now_s-state.dwell_started_time_s
                       if state.active_trip is None and state.dwell_started_time_s is not None else "")
            self._dwell_writer.writerow(row)
        return result

    def run(self):
        try:
            return super().run()
        finally:
            if self._dwell_file is not None:
                self._dwell_file.close()


def main():
    args = parse_args()
    config = configuration_from_args(args)
    if config.town != "Town01":
        raise ValueError("Este diagnóstico corresponde a T01_067 en Town01.")
    config.navigation_diagnostics_enabled = True
    output = DwellDiagnosticSimulation(config, ROOT, args.simulation_speed,
                                      str(args.carla_pythonapi) if args.carla_pythonapi else None).run()
    print("Diagnóstico de llegada guardado en: {0}".format(output))


if __name__ == "__main__":
    main()
