"""Prevent the measured premature arrival from Town01's opposing lane."""

import math
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock

from src.simulation.trip_runner import is_at_destination


class Location:
    def __init__(self, x, y):
        """Store planar coordinates for a lightweight test location."""
        self.x, self.y = x, y

    def distance(self, other):
        """Return the straight-line distance to another test location."""
        return math.hypot(self.x-other.x, self.y-other.y)


class ArrivalTests(unittest.TestCase):
    def test_nearby_opposing_lane_does_not_complete_trip(self):
        """Check that a nearby vehicle in the opposing lane is not considered at the destination."""
        # vehicle_001 originally completed its 479 m plan after only 215 m.
        location, goal = Location(92.377, 77.98), Location(88.382, 77.936)
        self.assertLess(location.distance(goal), 4)
        carla_map = Mock()
        carla_map.get_waypoint.side_effect = [NS(road_id=22, lane_id=1), NS(road_id=22, lane_id=-1)]
        self.assertFalse(is_at_destination(carla_map, location, goal, 4))

    def test_same_lane_within_threshold_is_an_arrival(self):
        """Check that the correct lane and an acceptable distance satisfy the location check."""
        carla_map = Mock()
        carla_map.get_waypoint.return_value = NS(road_id=22, lane_id=-1)
        self.assertTrue(is_at_destination(carla_map, Location(88.382, 75), Location(88.382, 77.936), 4))

    def test_different_road_or_missing_projection_is_not_an_arrival(self):
        """Check that a different road or missing lane projection fails the location check."""
        for current in (NS(road_id=24, lane_id=-1), None):
            carla_map = Mock()
            carla_map.get_waypoint.side_effect = [current, NS(road_id=22, lane_id=-1)]
            self.assertFalse(is_at_destination(carla_map, Location(1, 1), Location(1, 2), 4))

    def test_distance_check_still_applies_and_avoids_map_queries(self):
        """Check that a distant position is rejected before querying the map."""
        carla_map = Mock()
        self.assertFalse(is_at_destination(carla_map, Location(0, 0), Location(10, 0), 4))
        carla_map.get_waypoint.assert_not_called()


if __name__ == "__main__":
    unittest.main()
