"""Prepared demand inputs and bounded-memory audit failure detection."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from scripts.audit_observation_stream import audit_stream
from scripts.run_demand_campaign import check_hashes, preflight, read
from src.demand.destinations import load_destinations
from src.simulation.trip_runner import TripSimulation, TripSimulationConfig

ROOT = Path(__file__).resolve().parents[1]


class DemandCampaignTests(unittest.TestCase):
    def test_nested_hundred_preserves_twenty_histories_and_destination_streams(self):
        manifest = read(ROOT/'config/demand_20_100/preparation_manifest.json')
        check_hashes(manifest['input_sha256'])
        destinations = load_destinations(ROOT/'data/input/Town01/destinations_config.csv', 'Town01')
        old = None
        for count in (20, 100):
            config = TripSimulationConfig.from_json(ROOT/('config/demand_20_100/town01_%03d.json' % count))
            self.assertEqual(config.vehicle_count, count)
            self.assertEqual(config.seed, 210)
            self.assertFalse(config.initial_spawn_fallback_enabled)
            simulation = TripSimulation(config, ROOT, 5)
            simulation.destinations = destinations
            simulation.destinations_by_id = {d.destination_id:d for d in destinations}
            simulation._load_vehicle_histories()
            current = {}
            for state in simulation.vehicle_states:
                self.assertEqual(len(state.vehicle_history.events), 30)
                self.assertEqual([e.sequence for e in state.vehicle_history.events], list(range(1, 31)))
                self.assertEqual({simulation.destinations_by_id[e.destination_id].category for e in state.vehicle_history.events},
                                 {'residential', 'work_education', 'services_leisure'})
                current[state.vehicle_id] = (state.vehicle_history.events,
                    [simulation._select_next_destination(state).destination.destination_id for _ in range(12)])
            if old:
                self.assertEqual(config.resolved_spawn_point_indices()[:20], old_spawns)
                self.assertEqual({key:current[key] for key in old}, old)
            old, old_spawns = current, config.resolved_spawn_point_indices()

    def test_preflight_rejects_wrong_map_or_existing_actors_without_modifying_world(self):
        world = Mock()
        world.get_map.return_value.name = 'Carla/Maps/Town01'
        world.get_settings.return_value = NS(synchronous_mode=False, fixed_delta_seconds=None, no_rendering_mode=False)
        world.get_weather.return_value = NS(cloudiness=60.)
        world.get_actors.return_value.filter.return_value = []
        self.assertEqual(preflight(world)['vehicles'], 0)
        world.get_map.return_value.name = 'Town02'
        with self.assertRaisesRegex(RuntimeError, 'Town01'):
            preflight(world)
        world.get_map.return_value.name = 'Town01'
        world.get_actors.return_value.filter.side_effect = lambda pattern: [Mock()] if pattern=='vehicle.*' else []
        with self.assertRaisesRegex(RuntimeError, 'limpio'):
            preflight(world)
        world.tick.assert_not_called()
        world.apply_settings.assert_not_called()
        world.set_weather.assert_not_called()

    def audit_fixture(self, folder, gap=False, missing_arrival=False, no_arrivals=False):
        def write(name, rows):
            with (folder/name).open('w', newline='', encoding='utf8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        (folder/'run_config.json').write_text(json.dumps(dict(vehicle_count=1, simulation_config=dict(fixed_delta_seconds=.05))))
        (folder/'capture_summary.json').write_text(json.dumps(dict(simulation_completed=True, observation_rows_by_vehicle=dict(vehicle_001=3))))
        write('trips_log.csv', [dict(vehicle_id='vehicle_001', trip_id='trip_001')])
        write('arrival_log.csv', [dict(vehicle_id='vehicle_001', trip_id='trip_001', frame=99 if missing_arrival else 3)])
        rows = [dict(vehicle_id='vehicle_001', frame=frame, simulation_time_s=frame*.05,
                     x=1, y=2, z=0, speed_mps=0, yaw_deg=0, phase_before='travel',
                     phase_after='dwell' if frame==3 else 'travel', trip_before='trip_001',
                     trip_after='' if frame==3 else 'trip_001', context_trip_id='trip_001', low_speed=True)
                for frame in (1, 2, 3)]
        if gap:
            rows[1].update(frame=8, simulation_time_s=.4)
        write('observation_log.csv', rows)
        if no_arrivals:
            (folder/'arrival_log.csv').unlink()
        return audit_stream(folder, dict(simulation_duration_s=.15, completed=0 if no_arrivals else 1, integrity_errors=[]))

    def test_streaming_audit_accepts_complete_arrival_and_rejects_missing_frames(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            result = self.audit_fixture(folder)
            self.assertEqual(result['integrity_errors'], [])
            self.assertEqual(result['observations'], 3)
            self.assertEqual(result['matched_arrivals'], 1)
            self.assertAlmostEqual(result['vehicle_summary']['vehicle_001']['longest_low_speed_seconds'], .15)
            broken = self.audit_fixture(folder, gap=True)
            self.assertIn('vehicle_001: nonconsecutive_frames', broken['integrity_errors'])
            self.assertIn('vehicle_001: discontinuous_time', broken['integrity_errors'])
            missing = self.audit_fixture(folder, missing_arrival=True)
            self.assertIn('arrival_frame_missing', missing['integrity_errors'])

    def test_no_arrival_file_is_allowed_only_when_no_trip_completed(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            self.assertEqual(self.audit_fixture(folder, no_arrivals=True)['integrity_errors'], [])
            result = audit_stream(folder, dict(simulation_duration_s=.15, completed=1, integrity_errors=[]))
            self.assertIn('arrival_completed_count_mismatch', result['integrity_errors'])


if __name__ == '__main__':
    unittest.main()
