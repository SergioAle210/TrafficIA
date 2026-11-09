"""Simulator-independent checks for the three-vehicle orchestration state."""

import unittest
from pathlib import Path

from src.demand.destinations import load_destinations
from src.simulation.trip_runner import ActiveTrip, TripSimulation, TripSimulationConfig
from src.demand.vehicle_history import ROUTINE


class FakeLocation:
    x = 1.0
    y = 2.0
    z = 0.0


class FakeLogger:
    def __init__(self):
        self.trips = []
        self.history = []
        self.metrics = []

    def write_trip(self, row):
        self.trips.append(row)

    def write_history(self, row):
        self.history.append(row)

    def write_metrics(self, row):
        self.metrics.append(row)


class MultiVehicleStateTests(unittest.TestCase):
    def setUp(self):
        self.config = TripSimulationConfig.from_json(
            Path("config/multi_vehicle_trip.json")
        )
        self.simulation = TripSimulation(self.config, Path("."), 1)
        self.simulation.destinations = load_destinations(
            Path("data/input/Town01/destinations_config.csv"), "Town01"
        )
        self.simulation.destinations_by_id = {
            destination.destination_id: destination
            for destination in self.simulation.destinations
        }

    def test_configuration_creates_three_explicit_independent_states(self):
        self.assertEqual(self.config.vehicle_count, 3)
        self.assertEqual(self.config.resolved_spawn_point_indices(), [133, 6, 101])
        self.assertEqual(
            [state.vehicle_id for state in self.simulation.vehicle_states],
            ["vehicle_001", "vehicle_002", "vehicle_003"],
        )
        self.assertEqual(
            [state.requested_spawn_point_index for state in self.simulation.vehicle_states],
            [133, 6, 101],
        )

    def test_all_three_histories_load_thirty_individual_events(self):
        self.simulation._load_vehicle_histories()
        self.assertEqual(
            [len(state.vehicle_history.events) for state in self.simulation.vehicle_states],
            [30, 30, 30],
        )
        self.assertEqual(
            [state.vehicle_history.vehicle_id for state in self.simulation.vehicle_states],
            ["vehicle_001", "vehicle_002", "vehicle_003"],
        )

    def test_destination_sequences_are_reproducible_and_individual(self):
        first = self.simulation
        second = TripSimulation(self.config, Path("."), 1)
        second.destinations = self.simulation.destinations
        second.destinations_by_id = self.simulation.destinations_by_id
        first._load_vehicle_histories()
        second._load_vehicle_histories()

        first_sequences = [
            [
                first._select_next_destination(state).destination.destination_id
                for _ in range(10)
            ]
            for state in first.vehicle_states
        ]
        second_sequences = [
            [
                second._select_next_destination(state).destination.destination_id
                for _ in range(10)
            ]
            for state in second.vehicle_states
        ]

        self.assertEqual(first_sequences, second_sequences)
        self.assertEqual(len({tuple(sequence) for sequence in first_sequences}), 3)

    def test_completed_trip_updates_only_its_vehicle_history(self):
        self.simulation._load_vehicle_histories()
        self.simulation.logger = FakeLogger()
        destination = self.simulation.destinations[0]
        first, second, third = self.simulation.vehicle_states
        counts_before = [
            state.vehicle_history.counts[destination.destination_id]
            for state in self.simulation.vehicle_states
        ]
        second.active_trip = ActiveTrip(
            trip_number=1,
            origin_id="T01_006",
            origin_name="Origin",
            origin_location=FakeLocation(),
            destination=destination,
            destination_location=FakeLocation(),
            departure_time_s=0.0,
            last_location=FakeLocation(),
            last_moving_time_s=0.0,
            agent=None,
            planned_route_distance_m=10.0,
            selection_class=ROUTINE,
            history_visit_count_before=counts_before[1],
            selection_candidate_count=3,
        )

        self.simulation._finish_trip(10.0, "completed", second)

        self.assertEqual(
            first.vehicle_history.counts[destination.destination_id], counts_before[0]
        )
        self.assertEqual(
            second.vehicle_history.counts[destination.destination_id], counts_before[1] + 1
        )
        self.assertEqual(
            third.vehicle_history.counts[destination.destination_id], counts_before[2]
        )
        self.assertEqual(self.simulation.logger.history[0]["vehicle_id"], "vehicle_002")
        self.assertEqual(self.simulation.logger.trips[0]["vehicle_id"], "vehicle_002")

    def test_summary_aggregates_all_vehicle_states(self):
        self.simulation.logger = FakeLogger()
        first, second, third = self.simulation.vehicle_states
        first.trips_started = 2
        first.completed_trips = 1
        first.total_distance_traveled_m = 100.0
        first.total_trip_duration_s = 10.0
        first.destination_counts[self.simulation.destinations[0].destination_id] = 1
        second.trips_started = 1
        second.completed_trips = 1
        second.total_distance_traveled_m = 50.0
        second.total_trip_duration_s = 10.0
        second.destination_counts[self.simulation.destinations[1].destination_id] = 1
        second.total_collisions = 1
        third.trips_started = 1
        third.total_lane_invasions = 2

        self.simulation._write_metrics(self.simulation.logger, 30.0)

        row = self.simulation.logger.metrics[0]
        self.assertEqual(row["vehicle_count"], 3)
        self.assertEqual(row["trips_started"], 4)
        self.assertEqual(row["trips_completed"], 2)
        self.assertEqual(row["trips_incomplete"], 2)
        self.assertEqual(row["aggregate_average_speed_mps"], 7.5)
        self.assertEqual(row["total_collisions"], 1)
        self.assertEqual(row["total_lane_invasions"], 2)


class MultiVehicleConfigValidationTests(unittest.TestCase):
    def test_duplicate_spawn_points_are_rejected(self):
        config = TripSimulationConfig.from_json(Path("config/single_vehicle_trip.json"))
        config.vehicle_count = 2
        config.initial_spawn_point_indices = [133, 133]
        with self.assertRaisesRegex(ValueError, "índices repetidos"):
            config.validate()


if __name__ == "__main__":
    unittest.main()
