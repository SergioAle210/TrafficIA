"""Camera callback/frame association, state transitions and resource ownership."""
import tempfile
import csv
import json
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from src.simulation.trip_runner import TripSimulation, TripSimulationConfig
from src.recording.visual_review import ImageRecorder, VisualReviewSimulation, image_index, capture_spacing, agent_light_context

ROOT = Path(__file__).resolve().parents[1]


class Image:
    def __init__(self, frame, failure=False, started=None, release=None):
        """Create a test camera image with configurable timing and saving behavior."""
        self.frame, self.timestamp = frame, frame * .05
        self.failure, self.started, self.release = failure, started, release

    def save_to_disk(self, path):
        """Simulate image saving, with optional blocking or a disk error for writer tests."""
        if self.started:
            self.started.set()
            if not self.release.wait(5):
                raise TimeoutError('test writer release')
        if self.failure:
            raise OSError('disk failure')
        Path(path).write_bytes(b'test-image')


class VisualReviewTests(unittest.TestCase):
    def test_cached_agent_light_is_observed_without_rerunning_hazard_detector(self):
        """Check that review reads the cached traffic light without calling hazard detection again."""
        light = Mock(id=72, get_state=Mock(return_value='Red'))
        agent = NS(_last_traffic_light=light, _affected_by_traffic_light=Mock())
        self.assertEqual(agent_light_context(NS(agent=agent)), (72, 'Red'))
        agent._affected_by_traffic_light.assert_not_called()
        self.assertIs(agent._last_traffic_light, light)
        light.get_state.return_value = 'Green'
        self.assertEqual(agent_light_context(NS(agent=agent)), (72, 'Green'))

    def test_no_active_trip_does_not_report_stale_agent_light(self):
        """Check that waiting observations do not report a previous trip's cached traffic light."""
        self.assertEqual(agent_light_context(None), ('',''))
        self.assertEqual(agent_light_context(NS(agent=NS(_last_traffic_light=None))), ('',''))

    def config(self, **overrides):
        """Load the review test configuration with the requested overrides."""
        return TripSimulationConfig.from_json(ROOT/'config/multi_vehicle_trip.json', overrides)

    def test_delayed_callback_is_joined_by_vehicle_and_frame_not_latest_trip(self):
        """Check that delayed images match by vehicle and frame rather than the newest trip."""
        observation = dict(simulation_time_s=10.0, phase_before='travel', phase_after='dwell',
                           trip_before='trip_001', trip_after='', context_trip_id='trip_001', destination_id='A')
        images = [dict(vehicle_id='v1', frame=200, sensor_timestamp_s=10.05),
                  dict(vehicle_id='v2', frame=200, sensor_timestamp_s=10.0),
                  dict(vehicle_id='v1', frame=210, sensor_timestamp_s=10.5)]
        index = image_index(images, {('v1',200):observation})
        self.assertEqual(index[0]['context_trip_id'], 'trip_001')
        self.assertEqual(index[0]['phase_after'], 'dwell')
        self.assertEqual(index[0]['simulation_time_s'], 10)
        self.assertEqual(index[0]['sensor_timestamp_s'], 10.05)
        self.assertAlmostEqual(index[0]['timestamp_error_s'], .05)
        self.assertFalse(index[1]['matched_observation'])
        self.assertFalse(index[2]['matched_observation'])

    def test_first_irregular_interval_is_not_misreported_as_continuous_loss(self):
        """Check that irregular camera startup does not falsely imply repeated missing images."""
        result = capture_spacing([101,110,120,130],139,10)
        self.assertEqual(result['potential_missing_samples'],0)
        self.assertEqual(result['missing_tail_samples'],0)
        self.assertEqual(len(result['irregular_intervals']),1)
        result = capture_spacing([100,110,130],150,10)
        self.assertEqual(result['potential_missing_samples'],1)
        self.assertEqual(result['missing_tail_samples'],2)

    def test_writer_reports_disk_failure_and_continues_to_next_image(self):
        """Check that an image-saving error is recorded and later images are still processed."""
        with tempfile.TemporaryDirectory() as directory:
            recorder = ImageRecorder(directory)
            recorder.receive('v1', Image(10, failure=True))
            recorder.receive('v1', Image(20))
            recorder.close(); recorder.close()
            self.assertFalse(recorder.rows[0]['saved'])
            self.assertIn('disk failure', recorder.rows[0]['error'])
            self.assertTrue(recorder.rows[1]['saved'])
            self.assertFalse(recorder.worker.is_alive())

    def test_bounded_queue_counts_drops_without_blocking_callback(self):
        """Check that a full image queue records drops without blocking the camera callback."""
        with tempfile.TemporaryDirectory() as directory:
            started, release = threading.Event(), threading.Event()
            recorder = ImageRecorder(directory, capacity=1)
            try:
                recorder.receive('v1', Image(10, started=started, release=release))
                self.assertTrue(started.wait(2))
                recorder.receive('v1', Image(20))
                recorder.receive('v1', Image(30))
                self.assertEqual(recorder.dropped['v1'], 1)
            finally:
                release.set(); recorder.close()
            self.assertEqual(len(recorder.rows), 3)
            self.assertEqual(sum(r['saved'] for r in recorder.rows), 2)

    def test_observation_brackets_arrival_and_delegates_update_once(self):
        """Check that arrival phases are observed around exactly one normal trip update."""
        simulation = VisualReviewSimulation(self.config(), ROOT, 1)
        state = simulation.vehicle_states[0]
        simulation.vehicle_states = [state]
        location = NS(x=1., y=2., z=0.)
        state.actor = Mock(id=11)
        state.actor.get_transform.return_value = NS(location=location, rotation=NS(yaw=0))
        state.actor.get_velocity.return_value = NS(x=0.,y=0.,z=0.)
        state.actor.is_at_traffic_light.return_value = True
        state.actor.get_traffic_light.return_value = Mock(id=99, get_state=Mock(return_value='Red'))
        state.active_trip = NS(trip_id='trip_001', destination=NS(destination_id='D1'))
        simulation._observation_writer = Mock()
        def arrive(*args):
            """Simulate an arrival by clearing the vehicle's active trip."""
            state.active_trip = None
        with patch.object(TripSimulation, '_update_active_trip', side_effect=arrive) as update:
            simulation._update_active_trip(Mock(), state.actor, 10, .5, state)
        update.assert_called_once()
        row = simulation._observations[(state.vehicle_id,10)]
        self.assertEqual((row['phase_before'],row['phase_after']), ('travel','dwell'))
        self.assertEqual(row['context_trip_id'], 'trip_001')
        self.assertEqual(row['traffic_light_state'], 'Red')
        state.actor.apply_control.assert_not_called()

    def test_capture_finalize_runs_after_interruption(self):
        """Check that review finalization runs after a simulation interruption."""
        simulation = VisualReviewSimulation(self.config(), ROOT, 1)
        with patch.object(TripSimulation,'run',side_effect=KeyboardInterrupt), \
             patch.object(simulation,'_finalize_review') as finalizer:
            with self.assertRaises(KeyboardInterrupt):
                simulation.run()
        finalizer.assert_called_once()

    def test_camera_is_owned_before_listen_can_fail(self):
        """Check that a camera is registered for cleanup before listener setup can fail."""
        simulation = VisualReviewSimulation(self.config(), ROOT, 1)
        simulation.vehicle_states = simulation.vehicle_states[:1]
        state = simulation.vehicle_states[0]
        camera = Mock(id=123, listen=Mock(side_effect=RuntimeError('listen failed')))
        world = Mock(spawn_actor=Mock(return_value=camera))
        state.actor = Mock(get_world=Mock(return_value=world))
        fake_carla = NS(Transform=Mock(),Location=Mock(),Rotation=Mock(),AttachmentType=NS(Rigid=1))
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict('sys.modules', {'carla':fake_carla}), patch.object(TripSimulation,'_write_run_config'):
                with self.assertRaisesRegex(RuntimeError,'listen failed'):
                    simulation._write_run_config(Path(directory),'0.9.15',[])
            self.assertIn(camera, state.sensors)
            simulation._finalize_review()
            self.assertTrue(simulation._observation_file.closed)
            self.assertFalse(simulation._recorder.worker.is_alive())

    def test_render_disabled_and_nonintegral_camera_period_are_rejected(self):
        """Check that camera capture rejects disabled rendering and incompatible sampling intervals."""
        with self.assertRaisesRegex(ValueError,'renderizado'):
            VisualReviewSimulation(self.config(no_rendering_mode=True), ROOT, 1)
        with self.assertRaisesRegex(ValueError,'múltiplo'):
            VisualReviewSimulation(self.config(fixed_delta_seconds=.03), ROOT, 1)

    def test_without_cameras_keeps_observation_log_and_never_spawns_rgb(self):
        """Check that camera-free review still records observations and creates no RGB sensors."""
        simulation = VisualReviewSimulation(self.config(no_rendering_mode=True), ROOT, 1, capture_images=False)
        simulation.vehicle_states = simulation.vehicle_states[:1]
        world = Mock()
        simulation.vehicle_states[0].actor = Mock(get_world=Mock(return_value=world))
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict('sys.modules', {'carla':Mock()}), patch.object(TripSimulation,'_write_run_config'):
                simulation._write_run_config(Path(directory),'0.9.15',[])
            world.spawn_actor.assert_not_called()
            self.assertIsNone(simulation._recorder)
            self.assertEqual(simulation._camera_ids, [])
            self.assertFalse(simulation._observation_file.closed)
            simulation._finalize_review()
            self.assertTrue(simulation._observation_file.closed)
            summary = json.loads((Path(directory)/'capture_summary.json').read_text())
            self.assertFalse(summary['image_capture_enabled'])
            self.assertEqual(summary['cameras'], {})

    def test_no_camera_stream_preserves_rows_and_counts_without_retaining_them(self):
        """Check that camera-free observations are written and counted without accumulating rows in memory."""
        simulation = VisualReviewSimulation(self.config(), ROOT, 1, capture_images=False)
        state = simulation.vehicle_states[0]
        simulation.vehicle_states = [state]
        state.actor = Mock(id=11)
        state.actor.get_transform.return_value = NS(location=NS(x=1., y=2., z=0.), rotation=NS(yaw=0.))
        state.actor.get_velocity.return_value = NS(x=1., y=0., z=0.)
        state.active_trip = NS(trip_id='trip_001', destination=NS(destination_id='D1'))
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict('sys.modules', {'carla':Mock()}), patch.object(TripSimulation,'_write_run_config'):
                simulation._write_run_config(Path(directory), '0.9.15', [])
            with patch.object(TripSimulation, '_update_active_trip') as update:
                for frame in range(1, 501):
                    simulation._update_active_trip(Mock(), state.actor, frame, frame*.05, state)
            self.assertEqual(update.call_count, 500)
            self.assertEqual(simulation._observations, {})
            simulation._finalize_review()
            with (Path(directory)/'observation_log.csv').open(newline='', encoding='utf8') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 500)
            self.assertEqual(rows[-1]['frame'], '500')
            self.assertEqual(rows[-1]['context_trip_id'], 'trip_001')
            self.assertEqual(rows[-1]['phase_after'], 'travel')
            summary = json.loads((Path(directory)/'capture_summary.json').read_text())
            self.assertEqual(summary['observation_rows_by_vehicle'], {state.vehicle_id:500})
            state.actor.apply_control.assert_not_called()


if __name__ == '__main__':
    unittest.main()
