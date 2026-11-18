"""Stop policy, passive detector provenance, episodes and spectator selection."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from src.simulation.trip_runner import TripSimulation, TripSimulationConfig
from src.simulation.stop_review import StopEpisodes, FollowSelector, StopReviewSimulation
from src.navigation.route_planner import configure_carla_agents


class StopPolicyTests(unittest.TestCase):
    def simulation(self, policy='keep_trip'):
        """Build a stationary test vehicle and trip using the requested blocked-attempt policy."""
        config = TripSimulationConfig.from_json(Path('config/multi_vehicle_trip.json'), dict(blocked_policy=policy))
        sim = TripSimulation(config, Path('.'), 1)
        state = sim.vehicle_states[0]
        loc = NS(x=0., y=0., z=0., distance=lambda other:0.)
        actor = Mock()
        actor.get_location.return_value = loc
        actor.get_velocity.return_value = NS(x=0., y=0., z=0.)
        actor.get_transform.return_value = NS(location=loc, rotation=NS(yaw=0.))
        trip = NS(trip_id='trip_001', distance_traveled_m=0., last_location=loc,
            last_update_time_s=None, departure_time_s=0., stopped_time_s=0., last_moving_time_s=0.,
            approach=NS(update=Mock(), remaining_m=100), destination_location=loc, arrival_corridor=None,
            destination=NS(destination_id='D1'), blocked_warning_issued=False)
        state.active_trip = trip
        sim.logger = Mock()
        sim._sample_trajectory = Mock()
        sim._finish_trip = Mock()
        return sim, state, actor

    def step(self, sim, state, actor, now):
        """Update a test trip at the requested time while preventing an arrival."""
        with patch('src.simulation.trip_runner.is_at_destination', return_value=False), patch('src.simulation.trip_runner.is_aligned', return_value=True):
            sim._update_active_trip(Mock(), actor, int(now*20), now, state)

    def test_warning_boundary_once_recovery_rearms_and_keeps_destination(self):
        """Check that the warning fires once per stop and can fire again after movement resumes."""
        sim, state, actor = self.simulation()
        trip = state.active_trip
        for now in (59.95,60,60.05,70): self.step(sim,state,actor,now)
        self.assertIs(state.active_trip,trip)
        sim.logger.write_blocked_warning.assert_called_once()
        sim._finish_trip.assert_not_called()
        sim.logger.write_history.assert_not_called()
        actor.get_velocity.return_value.x=.2
        self.step(sim,state,actor,71)
        self.assertEqual(trip.last_moving_time_s,0)
        actor.get_velocity.return_value.x=.201
        self.step(sim,state,actor,72)
        actor.get_velocity.return_value.x=0
        self.step(sim,state,actor,131.95)
        self.assertEqual(sim.logger.write_blocked_warning.call_count,1)
        self.step(sim,state,actor,132)
        self.assertEqual(sim.logger.write_blocked_warning.call_count,2)

    def test_default_terminates_and_arrival_has_priority(self):
        """Check that the default stop policy closes blocked trips while valid arrival takes priority."""
        sim,state,actor = self.simulation('terminate')
        self.step(sim,state,actor,60)
        sim._finish_trip.assert_called_once_with(60,'blocked',state)
        sim,state,actor = self.simulation()
        state.active_trip.approach.remaining_m=0
        sim.config.navigation_diagnostics_enabled=False
        with patch('src.simulation.trip_runner.is_at_destination',return_value=True), patch('src.simulation.trip_runner.is_aligned',return_value=True), patch('src.simulation.trip_runner.stopped_and_aligned',return_value=True):
            sim._update_active_trip(Mock(),actor,1200,60,state)
        sim._finish_trip.assert_called_once_with(60,'completed',state)
        sim.logger.write_blocked_warning.assert_not_called()

    def test_cli_and_invalid_policy(self):
        """Check command-line stop-policy selection and rejection of invalid policy values."""
        from scripts.simulation.run_trips import parse_args, configuration_from_args
        with patch('sys.argv',['run','--config','config/multi_vehicle_trip.json','--blocked-policy','keep_trip']):
            self.assertEqual(configuration_from_args(parse_args()).blocked_policy,'keep_trip')
        self.assertEqual(TripSimulationConfig.from_json(Path('config/multi_vehicle_trip.json')).blocked_policy,'terminate')
        with self.assertRaises(ValueError):
            TripSimulationConfig.from_json(Path('config/multi_vehicle_trip.json'),dict(blocked_policy='off'))

    def test_kept_trip_aborted_at_run_end_does_not_add_a_visit(self):
        """Check that an unfinished retained trip adds no visit when the run ends."""
        sim,state,actor=self.simulation()
        trip=state.active_trip
        self.step(sim,state,actor,60)
        state.vehicle_history=Mock()
        sim._write_trip=Mock()
        TripSimulation._finish_trip(sim,300,'aborted',state)
        sim._write_trip.assert_called_once_with(sim.logger,trip,300,'aborted',state)
        state.vehicle_history.record.assert_not_called()
        self.assertIsNone(state.active_trip)

    def test_policy_comparison_rejects_other_configuration_changes(self):
        """Check that stop-policy comparisons reject unrelated configuration changes."""
        from scripts.diagnostics.compare_stop_policies import comparison_conditions
        a=dict(simulation_config=dict(blocked_policy='terminate',output_root='a',seed=210),
               vehicles=[dict(carla_actor_id=1,blueprint_id='car',vehicle_id='v')], environment={'weather':'same'})
        b=dict(simulation_config=dict(blocked_policy='keep_trip',output_root='b',seed=210),
               vehicles=[dict(carla_actor_id=2,blueprint_id='car',vehicle_id='v')], environment={'weather':'same'})
        self.assertEqual(comparison_conditions(a),comparison_conditions(b))
        b['simulation_config']['seed']=109
        self.assertNotEqual(comparison_conditions(a),comparison_conditions(b))


class EpisodeTests(unittest.TestCase):
    def test_episode_continues_across_trip_and_dwell_and_censors_at_end(self):
        """Check that a physical stop spans trip changes and is marked unfinished at observation end."""
        tracker=StopEpisodes(.2)
        for now,phase,trip in [(1,'travel','A'),(2,'retry_wait',''),(3,'travel','B')]:
            self.assertIsNone(tracker.update('v',now,1,.2,phase,trip))
        end=tracker.close('v',3,'simulation_end')
        self.assertEqual(end['duration_s'],3)
        self.assertEqual(end['trips'],['A','B'])
        self.assertEqual(end['phase_seconds'],dict(travel=2,retry_wait=1))
        self.assertTrue(end['censored'])
        tracker.update('v',4,1,0,'destination_dwell','')
        end=tracker.update('v',5,1,.201,'travel','C')
        self.assertFalse(end['censored'])
        self.assertEqual(end['episode'],2)
        self.assertEqual(end['duration_s'],1)

    def test_follow_longest_then_lock_first_warning_even_after_trip_ends(self):
        """Check that spectator selection locks on the first warning even after that trip ends."""
        selector=FollowSelector()
        self.assertEqual(selector.choose({'v1':31,'v2':40},set()),'v2')
        self.assertEqual(selector.choose({'v1':60,'v2':41},{'v1'}),'v1')
        self.assertEqual(selector.choose({'v2':200},{'v2'}),'v1')

    def test_failure_finalization_restores_spectator_and_closes_streams(self):
        """Check that failed execution restores the spectator and closes diagnostic files."""
        config=TripSimulationConfig.from_json(Path('config/multi_vehicle_trip.json'))
        sim=StopReviewSimulation(config,Path('.'),1)
        sim.spectator=Mock()
        sim.original_spectator=object()
        with tempfile.TemporaryDirectory() as directory:
            sim._review_output=Path(directory)
            sim.streams['stop_episodes']=(Path(directory)/'episodes.jsonl').open('w')
            sim.episodes.update('v',1,1,0,'travel','A')
            sim.last_frame_s=1
            with patch('src.recording.visual_review.VisualReviewSimulation._finalize_review') as parent:
                sim._finalize_review()
            sim.spectator.set_transform.assert_called_once_with(sim.original_spectator)
            self.assertTrue(sim.streams['stop_episodes'].closed)
            self.assertEqual(json.loads((Path(directory)/'episodes.jsonl').read_text())['end_reason'],'interrupted')
            parent.assert_called_once()


class PassiveDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load CARLA's agent support or skip these tests when it is unavailable."""
        try:
            import carla
            configure_carla_agents(carla,os.environ.get('CARLA_PYTHONAPI'))
        except (ImportError,RuntimeError) as error: raise unittest.SkipTest(str(error))

    def test_each_detector_once_returns_identical_control_and_resets_cache(self):
        """Check that passive observations use each detector once and leave the resulting control unchanged."""
        from src.navigation.carla_agent import CollinearSafeBasicAgent
        from agents.navigation.basic_agent import BasicAgent
        import carla
        agent=CollinearSafeBasicAgent.__new__(CollinearSafeBasicAgent)
        actor=NS(id=7)
        light=NS(id=8,get_state=lambda:'Red')
        control=carla.VehicleControl(brake=.5,steer=.1)
        def stock_step(self):
            """Simulate a normal agent step that checks vehicles and lights before returning its control."""
            self._vehicle_obstacle_detected([])
            self._affected_by_traffic_light([])
            return control
        with patch.object(BasicAgent,'run_step',stock_step), patch.object(BasicAgent,'_vehicle_obstacle_detected',return_value=(True,actor,4.)) as obstacle, patch.object(BasicAgent,'_affected_by_traffic_light',return_value=(True,light)) as signal:
            self.assertIs(agent.run_step(),control)
            obstacle.assert_called_once()
            signal.assert_called_once()
            self.assertEqual(agent.hazard_observation['obstacle_id'],7)
            self.assertEqual(agent.hazard_observation['light_id'],8)
            obstacle.return_value=(False,None,-1)
            signal.return_value=(False,None)
            agent.run_step()
            self.assertIsNone(agent.hazard_observation['obstacle_id'])
            self.assertFalse(agent.hazard_observation['light_detected'])


if __name__=='__main__': unittest.main()
