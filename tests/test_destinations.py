"""Simulator-independent checks for destination configuration and selection."""

import random
import unittest
from pathlib import Path

from src.destinations import load_destinations, select_destination
from src.trip_runner import (
    TripSimulation,
    TripSimulationConfig,
    spawn_vehicle_at_first_available_point,
    validate_initial_spawn_location,
)
from src.route_planner import plan_route, validate_route_start


class DestinationSelectionTests(unittest.TestCase):
    def setUp(self):
        self.destinations = load_destinations(
            Path("data/input/Town01/destinations_config.csv"), "Town01"
        )

    def test_same_seed_produces_same_sequence(self):
        first_rng = random.Random(42)
        second_rng = random.Random(42)
        first = [select_destination(self.destinations, None, 0.8, first_rng).destination_id for _ in range(20)]
        second = [select_destination(self.destinations, None, 0.8, second_rng).destination_id for _ in range(20)]
        self.assertEqual(first, second)

    def test_current_destination_is_never_selected(self):
        for seed in range(100):
            destination = select_destination(
                self.destinations, "T01_A", 0.8, random.Random(seed)
            )
            self.assertNotEqual(destination.destination_id, "T01_A")

    def test_configured_cycle_visits_remaining_destinations_in_order(self):
        config = TripSimulationConfig.from_json(Path("config/single_vehicle_trip_cyclic.json"))
        simulation = TripSimulation(config, Path("."), 1)
        simulation.destinations = self.destinations
        simulation.destinations_by_id = {
            destination.destination_id: destination for destination in self.destinations
        }
        simulation._validate_destination_cycle()
        selected = [simulation._select_next_destination() for _ in range(6)]
        self.assertEqual(
            [decision.destination.destination_id for decision in selected],
            ["T01_006", "T01_101", "T01_133", "T01_006", "T01_101", "T01_133"],
        )


class SpawnFallbackTests(unittest.TestCase):
    def test_uses_next_available_spawn_deterministically(self):
        class FakeLocation:
            def __init__(self, x=0.0, y=0.0, z=0.0):
                self.x = x
                self.y = y
                self.z = z

        class FakeTransform:
            def __init__(self, location, rotation="rotation"):
                self.location = location
                self.rotation = rotation

        class FakeCarla:
            class LaneType:
                Driving = "driving"

            Location = FakeLocation
            Transform = FakeTransform

        class FakeMap:
            def get_waypoint(self, location, project_to_road, lane_type):
                return type("Waypoint", (), {"transform": FakeTransform(location)})()

        class FakeWorld:
            def __init__(self):
                self.attempts = []

            def try_spawn_actor(self, _blueprint, transform):
                self.attempts.append(transform)
                return None if len(self.attempts) == 1 else "vehicle"

        world = FakeWorld()
        spawn_points = [
            type("SpawnPoint", (), {"location": FakeLocation()})(),
            type("SpawnPoint", (), {"location": FakeLocation()})(),
            type("SpawnPoint", (), {"location": FakeLocation()})(),
        ]
        vehicle, index = spawn_vehicle_at_first_available_point(
            world, "blueprint", FakeCarla, FakeMap(), spawn_points, 0, True
        )
        self.assertEqual(vehicle, "vehicle")
        self.assertEqual(index, 1)
        self.assertEqual(len(world.attempts), 2)

    def test_fixed_spawn_does_not_try_another_position(self):
        class FakeLocation:
            def __init__(self, x=0.0, y=0.0, z=0.0):
                self.x, self.y, self.z = x, y, z

        class FakeTransform:
            def __init__(self, location, rotation="rotation"):
                self.location, self.rotation = location, rotation

        class FakeCarla:
            class LaneType:
                Driving = "driving"
            Location = FakeLocation
            Transform = FakeTransform

        class FakeMap:
            def get_waypoint(self, location, **_kwargs):
                return type("Waypoint", (), {"transform": FakeTransform(location)})()

        class FakeWorld:
            def __init__(self):
                self.attempts = 0
            def try_spawn_actor(self, _blueprint, _transform):
                self.attempts += 1
                return None

        world = FakeWorld()
        spawn_points = [type("SpawnPoint", (), {"location": FakeLocation()})() for _ in range(2)]
        with self.assertRaisesRegex(RuntimeError, "spawn point fijo 0"):
            spawn_vehicle_at_first_available_point(
                world, "blueprint", FakeCarla, FakeMap(), spawn_points, 0, False
            )
        self.assertEqual(world.attempts, 1)


class RouteOriginValidationTests(unittest.TestCase):
    class FakeLocation:
        def __init__(self, x=0.0, y=0.0, z=0.0):
            self.x, self.y, self.z = x, y, z

        def distance(self, other):
            return (
                (self.x - other.x) ** 2
                + (self.y - other.y) ** 2
                + (self.z - other.z) ** 2
            ) ** 0.5

    def test_synchronized_spawn_accepts_nearby_location(self):
        error_m = validate_initial_spawn_location(
            self.FakeLocation(100.0, 50.0, 0.5),
            self.FakeLocation(100.0, 50.0, 0.6),
            3.0,
        )
        self.assertAlmostEqual(error_m, 0.1)

    def test_synchronized_spawn_rejects_stale_origin(self):
        with self.assertRaisesRegex(RuntimeError, "origen inválido"):
            validate_initial_spawn_location(
                self.FakeLocation(0.0, 0.0, 0.0),
                self.FakeLocation(259.6, 129.5, 0.5),
                3.0,
            )

    def test_route_start_rejects_distant_first_waypoint(self):
        waypoint = type(
            "Waypoint",
            (),
            {"transform": type("Transform", (), {"location": self.FakeLocation(0.0, 0.0)})()},
        )()
        with self.assertRaisesRegex(RuntimeError, "ruta comienza"):
            validate_route_start(
                [(waypoint, "LANEFOLLOW")],
                self.FakeLocation(259.6, 129.5),
                5.0,
            )

    def test_route_rejects_an_endpoint_far_from_requested_destination(self):
        waypoint = type(
            "Waypoint",
            (),
            {"transform": type("Transform", (), {"location": self.FakeLocation(0.0, 0.0)})()},
        )()
        planner = type(
            "Planner",
            (),
            {"trace_route": lambda _self, _origin, _destination: [(waypoint, "LANEFOLLOW")]},
        )()
        with self.assertRaisesRegex(RuntimeError, "terminó a"):
            plan_route(planner, self.FakeLocation(), self.FakeLocation(62.5, 0.0))


if __name__ == "__main__":
    unittest.main()
