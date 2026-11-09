"""Check geometry/sign conventions and that telemetry never drives the actor."""

import csv
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest.mock import Mock

from src.navigation.navigation_diagnostics import RouteTrace
from src.recording.run_logger import RunLogger


def waypoint(x, y, yaw=0, road=12):
    """Create a lightweight waypoint with known position, orientation, and lane geometry."""
    location = NS(x=x, y=y, z=0)
    return NS(transform=NS(location=location, rotation=NS(yaw=yaw)),
              road_id=road, lane_id=-1, lane_width=4)


class RouteTraceTests(unittest.TestCase):
    def test_projection_is_on_segment_and_sign_is_right(self):
        """Check that route projection stays on the segment and reports the correct sideways-error sign."""
        trace = RouteTrace([(waypoint(0, 0), "straight"), (waypoint(10, 0), "straight")])
        row = trace.project(5, 1, 10)
        self.assertEqual(row["route_x"], 5)
        self.assertEqual(row["route_y"], 0)
        self.assertEqual(row["lateral_error_m"], 1)
        self.assertEqual(row["heading_error_deg"], 10)
        self.assertEqual(trace.project(5, -1, 0)["lateral_error_m"], -1)
        self.assertAlmostEqual(trace.project(12, 1, 0)["route_distance_m"], math.sqrt(5))

    def test_duplicate_junction_points_and_yaw_wrap(self):
        """Check that duplicate waypoints and the angle boundary are handled during route projection."""
        a, b = waypoint(10, 0, 179), waypoint(0, 0, -179)
        route = [(a, "lane"), (a, "right"), (b, "right")]
        trace = RouteTrace(route)
        route.clear()
        row = trace.project(5, -1, -179)
        self.assertEqual(len(trace.points), 3)
        self.assertEqual(row["route_segment_index"], 1)
        self.assertEqual(row["lateral_error_m"], 1)
        self.assertEqual(row["heading_error_deg"], 1)

    def test_degenerate_route_has_no_fabricated_projection(self):
        """Check that a route with no usable segment returns no invented projection."""
        trace = RouteTrace([(waypoint(0, 0), "end")])
        self.assertEqual(trace.project(0, 1, 0), {})

    def test_sample_preserves_control_and_distinguishes_vehicle_from_target(self):
        """Check that diagnostics preserve controls and distinguish vehicle state from the target waypoint."""
        a, b = waypoint(0, 0), waypoint(10, 0)
        trace = RouteTrace([(a, "lane"), (b, "lane")])
        a.transform.location.distance = lambda other: 10
        vehicle = Mock()
        vehicle.get_transform.return_value = a.transform
        vehicle.get_velocity.return_value = NS(x=3, y=4, z=0)
        planner = NS(target_waypoint=b, _min_distance=5.5, get_plan=lambda: [(b, "lane")])
        agent = Mock()
        agent.get_local_planner.return_value = planner
        control = NS(steer=0.25, throttle=0.4, brake=0)
        row = trace.sample(vehicle, agent, control)
        self.assertEqual((row["x"], row["target_x"], row["speed_mps"]), (0, 10, 5))
        self.assertEqual((row["steer"], row["purge_distance_m"]), (0.25, 5.5))
        vehicle.apply_control.assert_not_called()
        agent.run_step.assert_not_called()

    def test_optional_writers_keep_frame_and_trip_keys(self):
        """Check that optional diagnostic logs retain their frame and trip identifiers."""
        with TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            logger = RunLogger(output)
            self.assertFalse((output / "control_log.csv").exists())
            keys = dict(run_id="run", vehicle_id="vehicle_002", trip_id="trip_003")
            logger.write_control(dict(keys, frame=42, simulation_time_s=2.1, steer=0.5))
            logger.write_route(dict(keys, index=0, x=1, y=2))
            logger.close()
            with (output / "control_log.csv").open(newline="") as file:
                row = next(csv.DictReader(file))
            self.assertEqual(row["frame"], "42")
            self.assertEqual(row["trip_id"], "trip_003")
            self.assertEqual(row["vehicle_id"], "vehicle_002")


if __name__ == "__main__":
    unittest.main()
