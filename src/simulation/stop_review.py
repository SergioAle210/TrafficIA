"""Passive stop evidence, continuous physical episodes and a live spectator."""
import json
import math
from collections import Counter, deque

from src.recording.visual_review import VisualReviewSimulation


class StopEpisodes:
    """Right-endpoint integration at speed <= threshold across trip boundaries."""
    def __init__(self, threshold):
        self.threshold = threshold
        self.open = {}
        self.sequence = Counter()

    def update(self, vehicle, now, dt, speed, phase, trip_id):
        if speed > self.threshold:
            return self.close(vehicle, now, 'recovered')
        if vehicle not in self.open:
            self.sequence[vehicle] += 1
            self.open[vehicle] = dict(vehicle_id=vehicle, episode=self.sequence[vehicle],
                start_s=now-dt, duration_s=0., phase_seconds={}, trips=[], last_sample_s=now)
        item = self.open[vehicle]
        item['duration_s'] += dt
        item['last_sample_s'] = now
        item['phase_seconds'][phase] = item['phase_seconds'].get(phase, 0.) + dt
        if trip_id and trip_id not in item['trips']:
            item['trips'].append(trip_id)
        return None

    def close(self, vehicle, now, reason):
        item = self.open.pop(vehicle, None)
        if item is not None:
            item.update(end_s=now, end_reason=reason, censored=reason != 'recovered')
        return item


class FollowSelector:
    def __init__(self):
        self.vehicle = None
        self.locked = False

    def choose(self, counters, warnings):
        if not self.locked and warnings:
            self.vehicle = sorted(warnings)[0]
            self.locked = True
        elif not self.locked:
            eligible = [(age, vehicle) for vehicle, age in counters.items() if age >= 30]
            if eligible:
                self.vehicle = max(eligible)[1]
            elif self.vehicle not in counters or counters.get(self.vehicle, 0) < 30:
                self.vehicle = sorted(counters)[0] if counters else None
        return self.vehicle


class StopReviewSimulation(VisualReviewSimulation):
    def __init__(self, *args, follow_spectator=True, **kwargs):
        super().__init__(*args, capture_images=False, **kwargs)
        if follow_spectator and self.config.no_rendering_mode:
            raise ValueError('El espectador requiere renderizado activo.')
        self.follow_spectator = follow_spectator
        self.episodes = StopEpisodes(self.config.blocked_speed_threshold_mps)
        self.selector = FollowSelector()
        self.commands = {}
        self.current = {}
        self.contacts = {}
        self.ends = {}
        self.pending_warnings = set()
        self.streams = {}
        self.spectator = None
        self.original_spectator = None
        self.last_console_s = -float('inf')
        self.last_frame_s = None
        self.sample_times = {}
        self.follow_events = []
        self.spectator_restored = False

    def _write_run_config(self, output_directory, server_version, destinations):
        super()._write_run_config(output_directory, server_version, destinations)
        for name in ('stop_observations', 'stop_episodes', 'stop_thresholds'):
            self.streams[name] = (output_directory/(name+'.jsonl')).open('w', encoding='utf8')
        if self.follow_spectator:
            world = self.primary_vehicle_state.actor.get_world()
            self.spectator = world.get_spectator()
            self.original_spectator = self.spectator.get_transform()
        import hashlib
        sources = ['src/simulation/stop_review.py', 'scripts/run_blocked_comparison.py', 'src/navigation/carla_agent.py',
                   'src/simulation/trip_runner.py', 'src/recording/visual_review.py', 'src/recording/run_logger.py']
        metadata = dict(policy=self.config.blocked_policy, follow_spectator=self.follow_spectator,
            cameras=False, observation_period_s=.5, follow_from_s=30, lock_at_first_warning=True,
            episode_definition='Right-endpoint time at speed <= threshold, continuous across trips; phase_seconds separates destination dwell from retry waits.',
            legacy_stopped_time='Trip stopped_time_s remains speed strictly below threshold; blocked clock resets only strictly above.',
            control_semantics='Command issued after control_frame; post-physics observation_frame is later. Missing/stale detector evidence is not a causal classification.',
            nearby_semantics='Fleet only, within 30m, center distance not clearance.',
            contacts_window_s=5, contacts_max_callbacks=20,
            source_sha256={p:hashlib.sha256((self.project_root/p).read_bytes()).hexdigest() for p in sources})
        (output_directory/'stop_review_config.json').write_text(json.dumps(metadata, indent=2), encoding='utf8')

    def _emit(self, name, row):
        if row is not None:
            self.streams[name].write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')

    def _on_sensor_event(self, state, event):
        if event['event_type'] == 'collision':
            self.contacts.setdefault(state.vehicle_id, deque(maxlen=20)).append(dict(event))

    def _finish_trip(self, now_s, status, state=None):
        state = self._state_or_primary(state)
        self.ends[state.vehicle_id] = status
        return super()._finish_trip(now_s, status, state)

    def _on_blocked_threshold(self, state, frame, now_s):
        super()._on_blocked_threshold(state, frame, now_s)
        self.pending_warnings.add(state.vehicle_id)

    def _record_applied_control(self, state, frame, now_s, control):
        trip = state.active_trip
        hazard = dict(getattr(trip.agent, 'hazard_observation', {})) if trip else {}
        self.commands[state.vehicle_id] = dict(control_frame=frame, control_time_s=now_s,
            control_trip=trip.trip_id if trip else '', throttle=float(control.throttle),
            brake=float(control.brake), steer=float(control.steer),
            arrival_brake=bool(trip and trip.approach.target_speed_kmh(self.config.target_speed_kmh)==0),
            dwell_brake=trip is None, hazards=hazard)

    def _observe_row(self, carla_map, state, trip, row):
        vehicle, now = state.vehicle_id, row['simulation_time_s']
        active_before = row['phase_before'] == 'travel'
        phase = ('travel' if active_before else
                 'destination_dwell' if self.ends.get(vehicle)=='completed' else 'retry_wait')
        ended = self.episodes.update(vehicle, now, self.config.fixed_delta_seconds,
            row['speed_mps'], phase, row['trip_before'])
        self._emit('stop_episodes', ended)
        command = self.commands.get(vehicle, {})
        counter = (max(0., now-trip.last_moving_time_s) if active_before and trip else 0.)
        evidence = []
        if command and row['frame']-command['control_frame'] == 1:
            if command['arrival_brake']: evidence.append('arrival_brake')
            if command['dwell_brake']: evidence.append('dwell_brake')
            if command['hazards'].get('light_detected'): evidence.append('agent_traffic_light')
            if command['hazards'].get('vehicle_detected'): evidence.append('agent_vehicle_obstacle')
        if not evidence: evidence.append('insufficient_evidence')
        wp = carla_map.get_waypoint(state.actor.get_location())
        item = dict(row, elapsed_s=now-self.start_sim_time_s, phase=phase, counter_s=counter,
            road_id=wp.road_id if wp else None, lane_id=wp.lane_id if wp else None,
            is_junction=wp.is_junction if wp else None,
            route_remaining_m=trip.approach.remaining_m if active_before and trip else None,
            command=command, evidence=evidence,
            recent_contacts=[e for e in self.contacts.get(vehicle, ()) if 0<=now-float(e['simulation_time_s'])<=5])
        self.current[vehicle] = item
        warning = vehicle in self.pending_warnings
        if warning:
            self._emit('stop_thresholds', dict(item, policy=self.config.blocked_policy))
        if now-self.sample_times.get(vehicle, -float('inf')) >= .5-1e-6 or warning or ended:
            self._emit('stop_observations', item)
            self.sample_times[vehicle] = now

    def _after_observation_frame(self, frame, now_s):
        self.last_frame_s = now_s
        counters = {v:r['counter_s'] for v,r in self.current.items() if r['phase_before']=='travel'}
        old = self.selector.vehicle
        was_locked = self.selector.locked
        selected = self.selector.choose(counters, self.pending_warnings)
        self.pending_warnings.clear()
        if selected != old or was_locked != self.selector.locked:
            event = dict(frame=frame, elapsed_s=now_s-self.start_sim_time_s,
                         vehicle_id=selected, locked=self.selector.locked)
            self.follow_events.append(event)
            print('ESPECTADOR', json.dumps(event), flush=True)
        if selected is None:
            return
        row = self.current[selected]
        if self.spectator is not None:
            import carla
            yaw = math.radians(row['yaw_deg'])
            self.spectator.set_transform(carla.Transform(
                carla.Location(x=row['x']-12*math.cos(yaw), y=row['y']-12*math.sin(yaw), z=row['z']+22),
                carla.Rotation(pitch=-60, yaw=row['yaw_deg'])))
        if now_s-self.last_console_s >= 1-1e-6:
            self.last_console_s = now_s
            print('OBS t={:.1f}s {} / {} destino={} v={:.3f}m/s contador={:.1f}s fase={} evidencia={}'.format(
                row['elapsed_s'], selected, row['context_trip_id'], row['destination_id'],
                row['speed_mps'], row['counter_s'], row['phase'], ','.join(row['evidence'])), flush=True)

    def _finalize_review(self):
        try:
            if self.spectator is not None and self.original_spectator is not None:
                self.spectator.set_transform(self.original_spectator)
                self.spectator_restored = True
        finally:
            for vehicle in list(self.episodes.open):
                self._emit('stop_episodes', self.episodes.close(vehicle, self.last_frame_s,
                    'simulation_end' if self._review_finished else 'interrupted'))
            for stream in self.streams.values():
                stream.close()
            if self._review_output is not None:
                (self._review_output/'spectator_log.json').write_text(json.dumps(dict(
                    followed=self.follow_events, locked_vehicle=self.selector.vehicle if self.selector.locked else None,
                    spectator_restored=self.spectator_restored,
                    visual_review='Live spectator only; no stored image proof or automatic visual confirmation.'), indent=2), encoding='utf8')
            super()._finalize_review()
