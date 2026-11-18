"""Run totals must include dwell and must not reassign stale events to a new trip."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from src.simulation.trip_runner import EventCollector, TripSimulation, TripSimulationConfig


class EventAccountingTests(unittest.TestCase):
    def setUp(self):
        """Create a multivehicle simulation with a mock logger for event-accounting tests."""
        config = TripSimulationConfig.from_json(Path("config/multi_vehicle_trip.json"))
        self.simulation = TripSimulation(config, Path("."), 1)
        self.simulation.logger = Mock()

    def queue(self, state, event_type, timestamp):
        """Add a test sensor notification to the selected vehicle's event buffer."""
        event = SimpleNamespace(
            frame=100, timestamp=timestamp,
            transform=SimpleNamespace(location=SimpleNamespace(x=0, y=0, z=0)),
        )
        state.event_collector._append(event_type, event, "", "test")

    def test_dwell_events_count_in_run_totals_but_not_another_vehicle(self):
        """Check that waiting events enter run totals without being assigned to another vehicle."""
        state = self.simulation.vehicle_states[1]
        for _ in range(4):
            self.queue(state, "lane_invasion", 12.0)
        self.queue(state, "collision", 12.0)
        self.simulation._drain_events(12.0, state)
        self.assertEqual(state.total_lane_invasions, 4)
        self.assertEqual(state.total_collisions, 1)
        for call in self.simulation.logger.write_event.call_args_list:
            self.assertEqual(call[0][0]["vehicle_id"], "vehicle_002")
            self.assertEqual(call[0][0]["trip_id"], "")
        self.assertEqual(self.simulation.vehicle_states[0].total_lane_invasions, 0)
        self.simulation._write_metrics(self.simulation.logger, 600)
        metrics = self.simulation.logger.write_metrics.call_args[0][0]
        self.assertEqual(metrics["total_lane_invasions"], 4)
        self.assertEqual(metrics["total_collisions"], 1)
        self.simulation._drain_events(12.0, state)
        self.assertEqual(state.total_lane_invasions, 4)  # No double counting on drain.

    def test_active_events_update_both_scopes_and_stale_events_only_run_totals(self):
        """Check that delayed events do not enter a newer trip's event counters."""
        state = self.simulation.vehicle_states[0]
        state.active_trip = SimpleNamespace(
            trip_id="trip_002", departure_time_s=20.0, collision_count=0, lane_invasion_count=0,
        )
        self.queue(state, "collision", 19.9)
        self.queue(state, "collision", 20.0)
        self.queue(state, "lane_invasion", 21.0)
        self.simulation._drain_events(21.0, state)
        rows = [call[0][0] for call in self.simulation.logger.write_event.call_args_list]
        self.assertEqual([row["trip_id"] for row in rows], ["", "trip_002", "trip_002"])
        self.assertEqual(state.total_collisions, 2)
        self.assertEqual(state.active_trip.collision_count, 1)
        self.assertEqual(state.total_lane_invasions, 1)
        self.assertEqual(state.active_trip.lane_invasion_count, 1)

    def test_collision_preserves_raw_callbacks_and_records_other_actor_type(self):
        """Check that collision notifications retain individual callbacks and the other actor's type."""
        collector = EventCollector()
        vector = SimpleNamespace(x=1, y=2, z=3)
        event = SimpleNamespace(
            frame=10, timestamp=2.0, transform=SimpleNamespace(location=vector),
            normal_impulse=vector, other_actor=SimpleNamespace(id=123, type_id="vehicle.test"),
        )
        collector.collision(event)
        collector.collision(event)
        rows = collector.drain()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["other_actor_id"], 123)
        self.assertIn("other_actor_type=vehicle.test", rows[0]["details"])


if __name__ == "__main__":
    unittest.main()
