"""Prepared demand inputs and bounded-memory audit failure detection."""
import csv
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from scripts.campaigns import run_demand as campaign
from src.project_paths import PROJECT_ROOT as ROOT
from scripts.diagnostics.observation_stream import audit_stream
from scripts.campaigns.run_demand import check_hashes, preflight, read
from src.demand.destinations import load_destinations
from src.simulation.trip_runner import TripSimulation, TripSimulationConfig



class ManualCampaignTests(unittest.TestCase):
    @contextlib.contextmanager
    def campaign_fixture(self, manual=True, interactive=True, check_only=False):
        """Exercise the real campaign loop with a fake server and clock.

        Each case reports 180 simulated seconds and uses two seconds of mock
        wall time. Tests can advance the clock separately at the keyboard prompt.
        """
        with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
            root = Path(folder)
            output = root/'data/output/campaign'
            flags = ['--output', str(output), '--seconds', '180']
            if manual:
                flags.append('--manual-start')
            if check_only:
                flags.append('--check-only')
            args = campaign.parse_args(flags)
            world = Mock()
            world.get_map.return_value.name = 'Town01'
            world.get_settings.return_value = NS(synchronous_mode=False, fixed_delta_seconds=None, no_rendering_mode=False)
            world.get_actors.return_value.filter.return_value = []
            world.get_weather.return_value = NS(cloudiness=10.)
            world.set_weather.side_effect = lambda weather: setattr(world.get_weather, 'return_value', weather)
            client = Mock()
            client.get_world.return_value = world
            client.get_server_version.return_value = client.get_client_version.return_value = '0.9.15'
            carla = NS(Client=Mock(return_value=client), WeatherParameters=lambda: NS(cloudiness=0.))
            clock = [0.]
            created = []

            def make_simulation(config, *unused, **kwargs):
                run_id = 'run_%d' % (len(created)+1)
                created.append(run_id)
                run_path = root/'data/output'/run_id

                def run():
                    run_path.mkdir()
                    clock[0] += 2.
                    return run_path

                return NS(run_id=run_id, run=run)

            stack.enter_context(patch.dict('sys.modules', {'carla': carla}))
            stack.enter_context(patch.object(campaign, 'ROOT', root))
            stack.enter_context(patch.object(campaign.sys, 'stdin', NS(isatty=lambda: interactive)))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(patch.object(campaign, 'read', side_effect=lambda path:
                {'input_sha256': {}} if path.name == 'preparation_manifest.json' else {'cloudiness': 60.}))
            stack.enter_context(patch.object(campaign, 'check_hashes'))
            stack.enter_context(patch.object(campaign, 'validate_map'))
            stack.enter_context(patch.object(campaign, 'digest', return_value='test_hash'))
            stack.enter_context(patch.object(campaign.shutil, 'copyfile'))
            stack.enter_context(patch.object(campaign.TripSimulationConfig, 'from_json',
                                            side_effect=lambda *a, **k: NS(output_root='data/output')))
            stack.enter_context(patch.object(campaign, 'VisualReviewSimulation', side_effect=make_simulation))
            stack.enter_context(patch.object(campaign.time, 'monotonic', side_effect=lambda: clock[0]))
            stack.enter_context(patch.object(campaign, 'analyze_run', return_value={
                'statuses': {'completed': 1}, 'completed': 1, 'simulation_duration_s': 180.,
                'events': {k: {'observed_callbacks': 0} for k in ('collision', 'lane_invasion')}}))
            stack.enter_context(patch.object(campaign, 'audit_stream', return_value={
                'integrity_errors': [], 'observations': 3600}))
            stack.enter_context(patch.object(campaign.subprocess, 'run', return_value=NS(returncode=0)))
            keyboard = stack.enter_context(patch('builtins.input', return_value=''))
            yield NS(args=args, output=output, world=world, carla=carla,
                     clock=clock, created=created, keyboard=keyboard)

    def test_manual_start_waits_before_all_cases_and_excludes_wait_from_run_time(self):
        with self.campaign_fixture() as session:
            prompts = []

            def confirm(prompt):
                plan = json.loads((session.output/'campaign.json').read_text())
                index = len(prompts)
                self.assertEqual(len(session.created), index)
                self.assertEqual([c['status'] for c in plan['cases']],
                                 ['completed']*index + ['pending']*(4-index))
                self.assertNotIn('started_at_utc', plan['cases'][index])
                prompts.append(prompt)
                session.clock[0] += 600.
                return ''

            session.keyboard.side_effect = confirm
            self.assertEqual(campaign.run_campaign(session.args), 0)
            plan = json.loads((session.output/'campaign.json').read_text())
            self.assertTrue(plan['manual_start'])
            self.assertEqual(plan['status'], 'completed')
            self.assertEqual(len(prompts), 4)
            for i, case in enumerate(plan['cases'], 1):
                self.assertIn('[%d/4]' % i, prompts[i-1])
                self.assertIn('manual_start_confirmed_at_utc', case)
                self.assertEqual(case['wall_seconds_process'], 2.)
                self.assertEqual(case['achieved_process_ratio'], 90.)
                label = 'n%03d_%s' % (case['vehicle_count'], case['scenario'])
                self.assertTrue((session.output/(label+'_audit.json')).is_file())
                self.assertTrue((session.output/(label+'_output_sha256.json')).is_file())
            self.assertEqual(session.world.get_weather().cloudiness, 10.)

    def test_default_automatic_mode_does_not_read_keyboard(self):
        with self.campaign_fixture(manual=False, interactive=False) as session:
            self.assertEqual(campaign.run_campaign(session.args), 0)
            session.keyboard.assert_not_called()
            self.assertEqual(len(session.created), 4)
            plan = json.loads((session.output/'campaign.json').read_text())
            self.assertFalse(plan['manual_start'])

    def test_manual_start_requires_terminal_before_connecting_or_creating_output(self):
        with self.campaign_fixture(interactive=False) as session:
            with self.assertRaisesRegex(ValueError, 'terminal interactiva'):
                campaign.run_campaign(session.args)
            session.carla.Client.assert_not_called()
            self.assertFalse(session.output.exists())

    def test_check_only_with_manual_flag_never_waits_or_changes_weather(self):
        with self.campaign_fixture(interactive=False, check_only=True) as session:
            self.assertEqual(campaign.run_campaign(session.args), 0)
            session.keyboard.assert_not_called()
            session.world.set_weather.assert_not_called()
            self.assertFalse(session.output.exists())

    def test_cancel_between_cases_preserves_completed_case_and_restores_weather(self):
        with self.campaign_fixture() as session:
            session.keyboard.side_effect = ['', KeyboardInterrupt]
            self.assertEqual(campaign.run_campaign(session.args), 130)
            plan = json.loads((session.output/'campaign.json').read_text())
            self.assertEqual(plan['status'], 'incomplete')
            self.assertEqual([c['status'] for c in plan['cases']], ['completed'] + ['pending']*3)
            self.assertEqual(len(session.created), 1)
            self.assertNotIn('manual_start_confirmed_at_utc', plan['cases'][1])
            self.assertEqual(session.world.get_weather().cloudiness, 10.)

    def test_closed_input_does_not_launch_a_case(self):
        with self.campaign_fixture() as session:
            session.keyboard.side_effect = EOFError
            self.assertEqual(campaign.run_campaign(session.args), 1)
            plan = json.loads((session.output/'campaign.json').read_text())
            self.assertEqual(plan['status'], 'incomplete')
            self.assertIn('entrada de la terminal', plan['error'])
            self.assertEqual(session.created, [])
            self.assertEqual(session.world.get_weather().cloudiness, 10.)

    def test_weather_is_checked_again_after_manual_confirmation(self):
        with self.campaign_fixture() as session:
            def change_weather(prompt):
                session.world.get_weather.return_value = NS(cloudiness=99.)
                return ''
            session.keyboard.side_effect = change_weather
            self.assertEqual(campaign.run_campaign(session.args), 1)
            plan = json.loads((session.output/'campaign.json').read_text())
            self.assertIn('clima cambio', plan['error'])
            self.assertEqual(session.created, [])
            self.assertEqual(session.world.get_weather().cloudiness, 10.)

    def test_only_an_empty_answer_confirms_the_case(self):
        with patch('builtins.input', side_effect=['todavia no', '']) as keyboard, \
                contextlib.redirect_stdout(io.StringIO()):
            campaign.wait_for_case_start(1, 4, {'vehicle_count': 20, 'scenario': 'random_baseline'})
            self.assertEqual(keyboard.call_count, 2)


class DemandCampaignTests(unittest.TestCase):
    def test_nested_hundred_preserves_twenty_histories_and_destination_streams(self):
        """Check that extending to 100 vehicles preserves the first 20 histories and destination sequences."""
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
        """Check that preflight rejects an unsuitable world without changing its actors or settings."""
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
        """Create small observation logs with optional missing records and run the streaming audit."""
        def write(name, rows):
            """Write sample rows and their column names to a test CSV file."""
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
        """Check that the audit accepts complete observations and reports missing frames."""
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
        """Check that an arrival log is required whenever a completed trip is reported."""
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            self.assertEqual(self.audit_fixture(folder, no_arrivals=True)['integrity_errors'], [])
            result = audit_stream(folder, dict(simulation_duration_s=.15, completed=1, integrity_errors=[]))
            self.assertIn('arrival_completed_count_mismatch', result['integrity_errors'])


if __name__ == '__main__':
    unittest.main()
