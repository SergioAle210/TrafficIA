"""Pure unit tests for individual dummy histories and 80/20 selection."""

import random
import tempfile
import unittest
from pathlib import Path

from src.destinations import load_destinations
from src.trip_runner import ActiveTrip, TripSimulation, TripSimulationConfig
from src.vehicle_history import (
    EXPLORATION,
    ROUTINE,
    VehicleHistory,
    generate_dummy_events,
    select_from_history,
    write_history_csv,
)


class VehicleHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.destinations = load_destinations(
            Path("data/input/Town01/destinations_config.csv"), "Town01"
        )
        cls.destination_ids = {item.destination_id for item in cls.destinations}

    def test_catalog_has_exactly_three_categories_and_no_manual_weights(self):
        self.assertEqual(
            {item.category for item in self.destinations},
            {"residential", "work_education", "services_leisure"},
        )
        self.assertTrue(all(item.frequency_class == "" for item in self.destinations))
        self.assertTrue(all(item.weight == 1.0 for item in self.destinations))

    def test_dummy_generation_is_reproducible_but_individual(self):
        kwargs = dict(
            destinations=self.destinations,
            vehicle_ids=["vehicle_001", "vehicle_002"],
            history_length=30,
            routine_destination_count=3,
            routine_probability=0.8,
            seed=42,
        )
        first = generate_dummy_events(**kwargs)
        second = generate_dummy_events(**kwargs)
        self.assertEqual(first, second)
        first_vehicle = [e.destination_id for e in first if e.vehicle_id == "vehicle_001"]
        second_vehicle = [e.destination_id for e in first if e.vehicle_id == "vehicle_002"]
        self.assertNotEqual(first_vehicle, second_vehicle)
        self.assertEqual(len(first_vehicle), 30)
        self.assertEqual(len(second_vehicle), 30)

    def test_routine_draw_uses_personal_most_visited_destinations(self):
        events = generate_dummy_events(
            self.destinations, ["vehicle_001"], 30, 3, 0.8, 42
        )
        history = VehicleHistory("vehicle_001", events)
        routine_ids = set(history.routine_ids(3))
        for seed in range(20):
            decision = select_from_history(
                self.destinations, history, None, 1.0, 3, random.Random(seed)
            )
            self.assertEqual(decision.selection_class, ROUTINE)
            self.assertIn(decision.destination.destination_id, routine_ids)
            self.assertGreater(decision.visit_count_before, 0)

    def test_exploration_prioritizes_an_unvisited_destination(self):
        events = generate_dummy_events(
            self.destinations, ["vehicle_001"], 6, 3, 1.0, 42
        )
        history = VehicleHistory("vehicle_001", events)
        decision = select_from_history(
            self.destinations, history, None, 0.0, 3, random.Random(7)
        )
        self.assertEqual(decision.selection_class, EXPLORATION)
        self.assertEqual(decision.visit_count_before, 0)

    def test_csv_round_trip_and_record_updates_counts(self):
        events = generate_dummy_events(
            self.destinations, ["vehicle_001"], 10, 3, 0.8, 42
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "history.csv"
            write_history_csv(path, events)
            history = VehicleHistory.from_csv(path, "vehicle_001", self.destination_ids)
        destination_id = self.destinations[0].destination_id
        previous = history.counts[destination_id]
        event = history.record(destination_id)
        self.assertEqual(history.counts[destination_id], previous + 1)
        self.assertEqual(event.source, "simulation")
        self.assertEqual(event.sequence, 11)

    def test_only_completed_trip_updates_history_and_incomplete_origin_is_relabelled(self):
        class FakeLocation:
            x = 1.0
            y = 2.0
            z = 0.0

        class FakeLogger:
            def __init__(self):
                self.trips = []
                self.history = []

            def write_trip(self, row):
                self.trips.append(row)

            def write_history(self, row):
                self.history.append(row)

        config = TripSimulationConfig.from_json(Path("config/single_vehicle_trip.json"))
        simulation = TripSimulation(config, Path("."), 1)
        simulation.logger = FakeLogger()
        destination = self.destinations[0]
        before = simulation.vehicle_history.counts[destination.destination_id]
        simulation.current_location_id = "T01_133"
        simulation.current_destination_id = "T01_133"
        simulation.active_trip = ActiveTrip(
            trip_number=1,
            origin_id="T01_133",
            origin_name="Casa 133",
            origin_location=FakeLocation(),
            destination=destination,
            destination_location=FakeLocation(),
            departure_time_s=0.0,
            last_location=FakeLocation(),
            last_moving_time_s=0.0,
            agent=None,
            planned_route_distance_m=10.0,
            selection_class=ROUTINE,
            history_visit_count_before=before,
            selection_candidate_count=3,
        )
        simulation._finish_trip(10.0, "blocked")
        self.assertEqual(simulation.vehicle_history.counts[destination.destination_id], before)
        self.assertEqual(simulation.current_location_id, "POSITION_AFTER_TRIP_001")
        self.assertIsNone(simulation.current_destination_id)
        self.assertEqual(simulation.logger.history, [])

        simulation.active_trip = ActiveTrip(
            trip_number=2,
            origin_id=simulation.current_location_id,
            origin_name=simulation.current_location_name,
            origin_location=FakeLocation(),
            destination=destination,
            destination_location=FakeLocation(),
            departure_time_s=10.0,
            last_location=FakeLocation(),
            last_moving_time_s=10.0,
            agent=None,
            planned_route_distance_m=10.0,
            selection_class=ROUTINE,
            history_visit_count_before=before,
            selection_candidate_count=3,
        )
        simulation._finish_trip(20.0, "completed")
        self.assertEqual(simulation.vehicle_history.counts[destination.destination_id], before + 1)
        self.assertEqual(simulation.current_location_id, destination.destination_id)
        self.assertEqual(len(simulation.logger.history), 1)


if __name__ == "__main__":
    unittest.main()
