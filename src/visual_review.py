"""Read-only visual instrumentation around the existing trip state machine."""
import csv
import hashlib
import json
import math
import queue
import threading
import time
from collections import Counter
from pathlib import Path

from src.trip_runner import TripSimulation, speed_mps


CAMERA = dict(width=640, height=360, height_m=18.0, interval_s=0.5, fov=90.0)
OBSERVATION_FIELDS = [
    'vehicle_id', 'frame', 'simulation_time_s', 'phase_before', 'phase_after',
    'trip_before', 'trip_after', 'context_trip_id', 'destination_id',
    'x', 'y', 'z', 'yaw_deg', 'speed_mps', 'low_speed',
    'traffic_light_id', 'traffic_light_state', 'at_traffic_light',
    'agent_traffic_light_id', 'agent_traffic_light_state', 'nearby_vehicles_json',
]
INDEX_FIELDS = [
    'vehicle_id', 'frame', 'simulation_time_s', 'sensor_timestamp_s', 'camera_transform_json', 'path', 'saved', 'error',
    'matched_observation', 'timestamp_error_s', 'phase_before', 'phase_after',
    'trip_before', 'trip_after', 'context_trip_id', 'destination_id',
]


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class ImageRecorder:
    """Bounded callback queue; disk I/O never issues simulator commands."""

    def __init__(self, output, capacity=128):
        self.output = Path(output)
        self.queue = queue.Queue(capacity)
        self.lock = threading.Lock()
        self.rows = []
        self.received = Counter()
        self.dropped = Counter()
        self.accepting = True
        self.closed = False
        self.last_callback = time.monotonic()
        self.worker = threading.Thread(target=self._write_images, name='visual-review-images', daemon=True)
        self.worker.start()

    def receive(self, vehicle_id, image):
        with self.lock:
            if not self.accepting:
                return
            self.last_callback = time.monotonic()
            self.received[vehicle_id] += 1
            try:
                self.queue.put_nowait((vehicle_id, image))
            except queue.Full:
                self.dropped[vehicle_id] += 1
                self.rows.append(dict(vehicle_id=vehicle_id, frame=image.frame,
                                      sensor_timestamp_s=image.timestamp, camera_transform_json='', path='', saved=False, error='queue_full'))

    def _write_images(self):
        while True:
            item = self.queue.get()
            try:
                if item is None:
                    return
                vehicle_id, image = item
                relative = Path('images') / vehicle_id / ('frame_%09d.png' % image.frame)
                transform = getattr(image, 'transform', None)
                pose = (dict(x=transform.location.x, y=transform.location.y, z=transform.location.z,
                             yaw_deg=transform.rotation.yaw, pitch_deg=transform.rotation.pitch)
                        if transform is not None else None)
                row = dict(vehicle_id=vehicle_id, frame=image.frame, sensor_timestamp_s=image.timestamp,
                           camera_transform_json=json.dumps(pose),
                           path=relative.as_posix(), saved=False, error='')
                try:
                    destination = self.output / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    image.save_to_disk(str(destination))
                    row['saved'] = destination.is_file() and destination.stat().st_size > 0
                    if not row['saved']:
                        row['error'] = 'missing_or_empty_image'
                except Exception as error:
                    row['error'] = '%s: %s' % (type(error).__name__, error)
                with self.lock:
                    self.rows.append(row)
            finally:
                self.queue.task_done()

    def close(self):
        if self.closed:
            return
        with self.lock:
            self.accepting = False
        self.queue.put(None)
        self.worker.join(timeout=30)
        if self.worker.is_alive():
            raise RuntimeError('El escritor de imágenes no terminó dentro de 30 s.')
        self.closed = True


def image_index(image_rows, observations):
    """Join exact actor/frame keys, never nearest timestamps or current trip."""
    result = []
    for image in sorted(image_rows, key=lambda r: (r['vehicle_id'], r['frame'])):
        row = dict(image)
        observation = observations.get((image['vehicle_id'], image['frame']))
        row['matched_observation'] = observation is not None
        row['simulation_time_s'] = observation['simulation_time_s'] if observation else ''
        row['timestamp_error_s'] = abs(image['sensor_timestamp_s'] - observation['simulation_time_s']) if observation else ''
        for key in ['phase_before', 'phase_after', 'trip_before', 'trip_after', 'context_trip_id', 'destination_id']:
            row[key] = observation[key] if observation else ''
        result.append(row)
    return result


def capture_spacing(frames, last_observed, step):
    """Report gaps, not a fictitious fixed phase inferred from the first callback.

    CARLA's first RGB callback may be off the steady sample cadence. Keep all
    intervals; only gaps longer than a period imply potential missing samples.
    """
    deltas = [b-a for a,b in zip(frames, frames[1:])]
    return dict(interval_frames_histogram=dict(Counter(deltas)),
                irregular_intervals=[dict(before=a, after=b, delta=b-a) for a,b in zip(frames,frames[1:]) if b-a!=step],
                potential_missing_samples=sum(max(0,(d-1)//step) for d in deltas),
                missing_tail_samples=max(0,(last_observed-frames[-1])//step) if frames else None)


def phase_record(trip):
    return ('travel', trip.trip_id) if trip is not None else ('dwell', '')


def agent_light_context(active_trip):
    """Read the prior control step's cached light without invoking its detector."""
    agent = getattr(active_trip, 'agent', None)
    light = getattr(agent, '_last_traffic_light', None)
    return (light.id, str(light.get_state())) if light is not None else ('', '')


class VisualReviewSimulation(TripSimulation):
    """Observe before/after updates; inherit every route/control/tick decision."""

    def __init__(self, *args, capture_images=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.capture_images = capture_images
        if self.capture_images and self.config.no_rendering_mode:
            raise ValueError('La revisión RGB requiere renderizado activo.')
        ratio = CAMERA['interval_s'] / self.config.fixed_delta_seconds
        if self.capture_images and not math.isclose(ratio, round(ratio), abs_tol=1e-8):
            raise ValueError('El intervalo de cámara debe ser múltiplo del delta fijo.')
        self.config.navigation_diagnostics_enabled = True
        self._recorder = None
        self._observations = {}
        self._observation_counts = Counter()
        self._observation_file = None
        self._last_trips = {}
        self._review_output = None
        self._camera_ids = []
        self._start_wall = None
        self._review_finished = False
        self._position_cache = {}
        self._cache_frame = None

    def _write_run_config(self, output_directory, server_version, destinations):
        super()._write_run_config(output_directory, server_version, destinations)
        import carla
        self._review_output = output_directory
        self._recorder = ImageRecorder(output_directory) if self.capture_images else None
        self._observation_file = (output_directory / 'observation_log.csv').open('w', encoding='utf8', newline='')
        self._observation_writer = csv.DictWriter(self._observation_file, fieldnames=OBSERVATION_FIELDS)
        self._observation_writer.writeheader()
        world = self.primary_vehicle_state.actor.get_world()
        source_files = ['src/trip_runner.py', 'src/route_planner.py', 'src/carla_agent.py', 'src/arrival.py',
                        'src/navigation_diagnostics.py', 'src/visual_review.py', 'src/vehicle_history.py',
                        'src/run_logger.py', 'scripts/run_trip_simulation.py', 'scripts/review_trip_simulation.py']
        inputs = [self.config.destinations_config, self.config.vehicle_history_config]
        metadata = dict(schema_version=3, image_capture_enabled=self.capture_images,
            camera=CAMERA if self.capture_images else None,
            source_sha256={f: hashlib.sha256((self.project_root/f).read_bytes()).hexdigest() for f in source_files},
            input_sha256={f: hashlib.sha256((self.project_root/f).read_bytes()).hexdigest()
                          for f in inputs if f and (self.project_root/f).is_file()},
            observation_semantics='After physics tick, before/after unchanged trip update. New-trip selection later in the same frame first appears next frame.',
            low_speed_threshold_mps=self.config.blocked_speed_threshold_mps,
            nearby_radius_m=30, nearby_scope='configured fleet only; offsets in ego forward/right axes; center distances, not clearance',
            agent_traffic_light_semantics='During low speed and active trips only: ID cached by BasicAgent in the prior control step, with current light state. Passive context, not exclusive stop attribution; blank during dwell.',
            camera_attachment='rigid relative x=0 y=0 z=18; pitch=-90 yaw=0 roll=0; default RGB postprocessing',
            capture_integrity='Exact vehicle/frame join to world time; retain raw sensor timestamp separately; report cadence gaps and camera startup.',
            timestamp_semantics='CARLA 0.9.15 RGB uses a render-thread frame and a later stream timestamp. Sensor timestamp can lead world time of its frame. No nearest-time remapping.',
            timestamp_source='https://github.com/carla-simulator/carla/blob/0.9.15/Unreal/CarlaUE4/Plugins/Carla/Source/Carla/Sensor/PixelReader.h',
            camera_actor_ids=self._camera_ids,
        )
        for state in (self.vehicle_states if self.capture_images else []):
            blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
            for name, value in [('image_size_x', CAMERA['width']), ('image_size_y', CAMERA['height']),
                                ('sensor_tick', CAMERA['interval_s']), ('fov', CAMERA['fov'])]:
                blueprint.set_attribute(name, str(value))
            camera = world.spawn_actor(blueprint,
                carla.Transform(carla.Location(z=CAMERA['height_m']), carla.Rotation(pitch=-90)),
                attach_to=state.actor, attachment_type=carla.AttachmentType.Rigid)
            # Ownership is registered before listen so the inherited finally also cleans failed setup.
            state.sensors.append(camera)
            self._camera_ids.append(camera.id)
            camera.listen(lambda img, vehicle_id=state.vehicle_id: self._recorder.receive(vehicle_id, img))
        (output_directory/'visual_review_config.json').write_text(json.dumps(metadata, indent=2), encoding='utf8')
        self._start_wall = time.monotonic()

    def _finish_trip(self, now_s, status, state=None):
        state = self._state_or_primary(state)
        trip = state.active_trip
        result = super()._finish_trip(now_s, status, state)
        if trip is not None:
            self._last_trips[state.vehicle_id] = trip
        return result

    def _update_active_trip(self, carla_map, vehicle, frame, now_s, state=None):
        state = self._state_or_primary(state)
        before_phase, before_trip = phase_record(state.active_trip)
        trip = state.active_trip or self._last_trips.get(state.vehicle_id)
        if frame != self._cache_frame:
            self._position_cache = {s.vehicle_id: (s.actor.get_transform(), speed_mps(s.actor.get_velocity()), s.actor.id)
                                    for s in self.vehicle_states}
            self._cache_frame = frame
        transform, speed, _ = self._position_cache[state.vehicle_id]
        location = transform.location
        low_speed = speed < self.config.blocked_speed_threshold_mps
        near = []
        light, light_state, at_light = '', '', ''
        agent_light, agent_light_state = '', ''
        if low_speed:
            agent_light, agent_light_state = agent_light_context(state.active_trip)
            at_light = vehicle.is_at_traffic_light()
            if at_light:
                traffic_light = vehicle.get_traffic_light()
                if traffic_light is not None:
                    light, light_state = traffic_light.id, str(traffic_light.get_state())
            yaw = math.radians(transform.rotation.yaw)
            for other_id, (other_t, other_speed, actor_id) in self._position_cache.items():
                if other_id == state.vehicle_id:
                    continue
                distance = location.distance(other_t.location)
                if distance > 30:
                    continue
                dx, dy = other_t.location.x-location.x, other_t.location.y-location.y
                near.append(dict(vehicle_id=other_id, actor_id=actor_id, distance_m=distance,
                                 forward_m=dx*math.cos(yaw)+dy*math.sin(yaw),
                                 right_m=-dx*math.sin(yaw)+dy*math.cos(yaw), speed_mps=other_speed))
        result = super()._update_active_trip(carla_map, vehicle, frame, now_s, state)
        after_phase, after_trip = phase_record(state.active_trip)
        row = dict(vehicle_id=state.vehicle_id, frame=frame, simulation_time_s=now_s,
                   phase_before=before_phase, phase_after=after_phase, trip_before=before_trip, trip_after=after_trip,
                   context_trip_id=trip.trip_id if trip else '', destination_id=trip.destination.destination_id if trip else '',
                   x=location.x, y=location.y, z=location.z, yaw_deg=transform.rotation.yaw, speed_mps=speed,
                   low_speed=low_speed, traffic_light_id=light, traffic_light_state=light_state, at_traffic_light=at_light,
                   agent_traffic_light_id=agent_light, agent_traffic_light_state=agent_light_state,
                   nearby_vehicles_json=json.dumps(sorted(near, key=lambda n:n['distance_m'])))
        # Only RGB needs a delayed frame join. Headless observation is streamed
        # to CSV so memory does not grow with vehicles times simulation ticks.
        if self.capture_images:
            self._observations[(state.vehicle_id, frame)] = row
        self._observation_counts[state.vehicle_id] += 1
        self._observation_writer.writerow(row)
        self._observe_row(carla_map, state, trip, row)
        return result

    def _observe_row(self, carla_map, state, trip, row):
        """Optional passive consumer of an already collected observation."""

    def _write_metrics(self, logger, duration):
        # Drain already rendered GPU callbacks without generating extra simulation ticks.
        if self._camera_ids:
            time.sleep(1)
        super()._write_metrics(logger, duration)
        self._review_finished = True

    def _finalize_review(self):
        if self._review_output is None:
            return
        if self._recorder is not None:
            self._recorder.close()
        if self._observation_file is not None:
            self._observation_file.close()
        index = image_index(self._recorder.rows if self._recorder else [], self._observations)
        write_csv(self._review_output/'image_index.csv', INDEX_FIELDS, index)
        by_vehicle = {}
        step = round(CAMERA['interval_s']/self.config.fixed_delta_seconds)
        for state in (self.vehicle_states if self.capture_images else []):
            images = [r for r in index if r['vehicle_id'] == state.vehicle_id]
            observed_frames = sorted(f for v,f in self._observations if v == state.vehicle_id)
            received_frames = sorted(set(r['frame'] for r in images))
            offsets = [r['timestamp_error_s'] for r in images if r['matched_observation']]
            by_vehicle[state.vehicle_id] = dict(received=self._recorder.received[state.vehicle_id],
                saved=sum(r['saved'] for r in images), queue_drops=self._recorder.dropped[state.vehicle_id],
                save_errors=sum(not r['saved'] and r['error']!='queue_full' for r in images),
                duplicate_frames=len(images)-len(received_frames),
                unmatched_frames=[r['frame'] for r in images if not r['matched_observation']],
                sensor_world_timestamp_offset_abs_max_s=max(offsets) if offsets else None,
                sensor_world_timestamp_offset_abs_min_s=min(offsets) if offsets else None,
                spacing=capture_spacing(received_frames, observed_frames[-1], step) if observed_frames else None,
                first_observed_frame=observed_frames[0] if observed_frames else None,
                first_image_frame=received_frames[0] if received_frames else None,
                last_observed_frame=observed_frames[-1] if observed_frames else None,
                last_image_frame=received_frames[-1] if received_frames else None)
        metadata = dict(run_id=self.run_id, simulation_completed=self._review_finished,
                        image_capture_enabled=self.capture_images,
                        observation_rows_by_vehicle=dict(self._observation_counts), cameras=by_vehicle,
                        camera_actor_ids=self._camera_ids, wall_seconds_since_camera_setup=time.monotonic()-self._start_wall if self._start_wall else None,
                        note=('Warm-up before the first image is not silently counted as complete visual coverage.'
                              if self.capture_images else 'No RGB cameras requested. Logs do not provide visual coverage.'))
        (self._review_output/'capture_summary.json').write_text(json.dumps(metadata, indent=2), encoding='utf8')

    def run(self):
        try:
            return super().run()
        finally:
            self._finalize_review()
