"""The diagnostic subclass observes transitions without overriding controls."""

import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from scripts.diagnose_destination_dwell import DwellDiagnosticSimulation, sensor_corners_xy
from src.simulation.trip_runner import TripSimulation


class DwellDiagnosticsTests(unittest.TestCase):
    def test_sensor_footprint_matches_stock_world_offset_and_corner_order(self):
        """Check that the diagnostic sensor footprint matches CARLA's offset and corner order."""
        t = NS(location=NS(x=5, y=10), rotation=NS(yaw=90))
        box = NS(location=NS(x=1, y=0), extent=NS(x=2,y=1))
        for actual, expected in zip(sensor_corners_xy(t,box), [(5,12),(5,8),(7,12),(7,8)]):
            self.assertAlmostEqual(actual[0],expected[0])
            self.assertAlmostEqual(actual[1],expected[1])

    def test_braking_starting_and_event_accounting_are_inherited(self):
        """Check that diagnostic recording preserves normal braking, trip starts, and event accounting."""
        for method in ("_brake", "_start_trip", "_drain_events", "_write_metrics"):
            self.assertIs(getattr(DwellDiagnosticSimulation,method),getattr(TripSimulation,method))

    def test_arrival_frame_keeps_before_and_after_phases(self):
        """Check that an arrival frame records both its travel and waiting phases."""
        simulation = DwellDiagnosticSimulation.__new__(DwellDiagnosticSimulation)
        simulation._observe = Mock(return_value=dict(phase_before="travel",trip_before="trip_003"))
        simulation._dwell_writer = Mock()
        state = NS(active_trip=NS(trip_id="trip_003"),dwell_started_time_s=None)
        vehicle, carla_map = Mock(), Mock()
        def complete(*args):
            """Simulate trip completion by clearing the active trip and starting the wait."""
            state.active_trip=None
            state.dwell_started_time_s=10
        with patch.object(TripSimulation,"_update_active_trip",side_effect=complete) as update:
            simulation._update_active_trip(carla_map,vehicle,200,10,state)
        update.assert_called_once_with(carla_map,vehicle,200,10,state)
        row = simulation._dwell_writer.writerow.call_args[0][0]
        self.assertEqual((row['phase_before'],row['phase_after']),('travel','dwell'))
        self.assertEqual((row['trip_before'],row['trip_after']),('trip_003',''))
        self.assertEqual(row['dwell_elapsed_s'],0)
        vehicle.apply_control.assert_not_called()

    def test_wait_is_observed_even_with_no_active_trip(self):
        """Check that waiting observations continue when no trip is active."""
        simulation = DwellDiagnosticSimulation.__new__(DwellDiagnosticSimulation)
        simulation._observe=Mock(return_value=dict(phase_before="dwell",trip_before=""))
        simulation._dwell_writer=Mock()
        state=NS(active_trip=None,dwell_started_time_s=10)
        with patch.object(TripSimulation,"_update_active_trip") as update:
            simulation._update_active_trip(Mock(),Mock(),210,10.5,state)
        self.assertEqual(update.call_count,1)
        self.assertEqual(simulation._dwell_writer.writerow.call_args[0][0]['dwell_elapsed_s'],0.5)

    def test_outside_focus_does_not_skip_normal_runner_update(self):
        """Check that the normal trip update still runs outside the diagnostic area."""
        simulation = DwellDiagnosticSimulation.__new__(DwellDiagnosticSimulation)
        simulation._observe=Mock(return_value=None)
        simulation._dwell_writer=Mock()
        with patch.object(TripSimulation,"_update_active_trip") as update:
            simulation._update_active_trip(Mock(),Mock(),1,0.05,NS())
        self.assertEqual(update.call_count,1)
        simulation._dwell_writer.writerow.assert_not_called()

    def test_diagnostic_file_closes_when_base_runner_is_interrupted(self):
        """Check that an interrupted simulation still closes the diagnostic log."""
        simulation=DwellDiagnosticSimulation.__new__(DwellDiagnosticSimulation)
        simulation._dwell_file=Mock()
        with patch.object(TripSimulation,"run",side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            simulation.run()
        simulation._dwell_file.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
