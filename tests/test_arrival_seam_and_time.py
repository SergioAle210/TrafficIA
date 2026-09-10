"""Arrival seams, optional deadlines and matched full-run exposure."""
import math
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from src.arrival import ArrivalLaneCorridor
from src.trip_runner import TripSimulation, TripSimulationConfig, is_at_destination


class Location:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def distance(self, other):
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)


def waypoint(x, lane=1, road=15):
    return NS(road_id=road, section_id=0, lane_id=lane, s=100-x,
              transform=NS(location=Location(x), rotation=NS(yaw=0)))


class ArrivalSeamTests(unittest.TestCase):
    def setUp(self):
        self.goal = waypoint(0, -1, 20)
        self.corridor = ArrivalLaneCorridor([(self.goal, None)] + [(waypoint(i*.5), None) for i in range(1, 13)])
        self.map = NS(get_waypoint=lambda loc, **kw: self.goal if loc.x == 0 else waypoint(loc.x))

    def test_seam_is_valid_only_on_verified_bounded_continuation(self):
        self.assertTrue(is_at_destination(self.map, Location(.91), Location(), 4, self.corridor))
        self.assertFalse(is_at_destination(self.map, Location(.91), Location(), 4))
        self.assertFalse(is_at_destination(self.map, Location(3.1), Location(), 4, self.corridor))
        for wrong in [waypoint(.9, -1), waypoint(.9, 2), waypoint(.9, 1, 99)]:
            self.assertFalse(self.corridor.contains(wrong, Location(.9)))
        distant_s = waypoint(.9)
        distant_s.s = 300
        self.assertFalse(self.corridor.contains(distant_s, Location(.9)))

    def simulation(self, remaining=0, limit=None):
        sim = TripSimulation.__new__(TripSimulation)
        sim.config = NS(arrival_threshold_m=4, blocked_speed_threshold_mps=.2,
                        blocked_time_threshold_seconds=60, max_trip_time_seconds=limit,
                        navigation_diagnostics_enabled=False)
        sim._sample_trajectory = Mock()
        sim._finish_trip = Mock()
        trip = NS(distance_traveled_m=0, last_location=Location(.9), last_update_time_s=None,
                  departure_time_s=0, stopped_time_s=0, last_moving_time_s=0,
                  approach=NS(update=Mock(), remaining_m=remaining), destination_location=Location(),
                  arrival_corridor=self.corridor)
        state = NS(active_trip=trip)
        vehicle = Mock()
        vehicle.get_location.return_value = Location(.9)
        vehicle.get_transform.return_value = NS(location=Location(.9), rotation=NS(yaw=-12.48))
        vehicle.get_velocity.return_value = Location(.01)
        return sim, state, vehicle

    def test_runner_keeps_alignment_after_seam_and_completes_only_when_aligned(self):
        sim, state, vehicle = self.simulation()
        sim._update_active_trip(self.map, vehicle, 1, 1, state)
        self.assertTrue(state.active_trip.approach.settling)
        sim._finish_trip.assert_not_called()
        vehicle.get_transform.return_value.rotation.yaw = 0
        sim._update_active_trip(self.map, vehicle, 2, 1.05, state)
        sim._finish_trip.assert_called_once_with(1.05, "completed", state)

    def test_disabled_deadline_keeps_moving_trip_beyond_300_seconds(self):
        for limit in [None, 300]:
            sim, state, vehicle = self.simulation(remaining=100, limit=limit)
            vehicle.get_velocity.return_value = Location(5)
            sim._update_active_trip(self.map, vehicle, 1, 301, state)
            if limit is None:
                sim._finish_trip.assert_not_called()
            else:
                sim._finish_trip.assert_called_once_with(301, "timeout", state)

    def test_disabled_deadline_preserves_blockage_and_records_stopped_time(self):
        sim, state, vehicle = self.simulation(remaining=100)
        sim._update_active_trip(self.map, vehicle, 1, 60, state)
        sim._finish_trip.assert_called_once_with(60, "blocked", state)
        self.assertEqual(state.active_trip.stopped_time_s, 60)

    def test_deadline_configuration_rejects_nonfinite_or_nonpositive_values(self):
        config = Path(__file__).resolve().parents[1] / "config/multi_vehicle_trip.json"
        for limit in [-1, 0, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                TripSimulationConfig.from_json(config, dict(max_trip_time_seconds=limit))
        self.assertIsNone(TripSimulationConfig.from_json(config).max_trip_time_seconds)

    def test_cli_can_restore_legacy_deadline_or_disable_it(self):
        from scripts.run_trip_simulation import parse_args, configuration_from_args
        config = Path(__file__).resolve().parents[1] / "config/multi_vehicle_trip.json"
        for argument, expected in [("0", None), ("300", 300)]:
            with patch("sys.argv", ["run", "--config", str(config), "--max-trip-seconds", argument]):
                self.assertEqual(configuration_from_args(parse_args()).max_trip_time_seconds, expected)

    def test_exposure_includes_motion_during_dwell_and_all_elapsed_time(self):
        state = NS(actor=Mock(), exposure_last_time_s=None, exposure_last_location=None,
                   observed_time_s=0, observed_distance_m=0, active_trip=None)
        for time, x in [(10, 0), (12, 5), (15, 5.2)]:
            state.actor.get_location.return_value = Location(x)
            TripSimulation._sample_vehicle_exposure(state, time)
        self.assertEqual(state.observed_time_s, 5)
        self.assertAlmostEqual(state.observed_distance_m, 5.2)


if __name__ == "__main__":
    unittest.main()
