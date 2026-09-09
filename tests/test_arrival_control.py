"""Arrival regressions: curved braking, route progress and dwell accounting."""

import math
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from src.arrival import ArrivalApproach, approach_control, stopped_and_aligned
from src.route_planner import arrival_route
from src.trip_runner import ActiveTrip, TripSimulation, TripSimulationConfig


class Location:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def distance(self, other):
        return math.sqrt((self.x-other.x)**2+(self.y-other.y)**2+(self.z-other.z)**2)


class Waypoint:
    def __init__(self, s, lane_id=-1, curved=False):
        self.s, self.lane_id = s, lane_id
        self.road_id, self.section_id = 20, 0
        self.curved = curved
        angle = s/20.0 if curved else 0
        location = Location(20*math.sin(angle), 20*(1-math.cos(angle))) if curved else Location(s)
        self.transform = NS(location=location, rotation=NS(yaw=math.degrees(angle)))

    def next(self, distance):
        return [Waypoint(self.s+distance*(1 if self.lane_id < 0 else -1), self.lane_id, self.curved)]


def route(points):
    return [(NS(transform=NS(location=Location(x,y))), None) for x,y in points]


class ArrivalControlTests(unittest.TestCase):
    def test_route_finishes_at_exact_goal_in_curve_and_both_lane_directions(self):
        for lane, points, goal_s in [(-1,[0,2,4,6],9), (1,[10,8,6,4],1)]:
            goal = Waypoint(goal_s, lane, curved=True)
            fixed = arrival_route([(Waypoint(s,lane,True),"curve") for s in points], goal)
            self.assertIs(fixed[-1][0], goal)
            self.assertTrue(all(a[0].transform.location.distance(b[0].transform.location) <= .501
                                for a,b in zip(fixed[3:],fixed[4:])))

    def test_terminal_overshoot_is_trimmed_without_an_about_turn(self):
        goal = Waypoint(5)
        fixed = arrival_route([(Waypoint(s),None) for s in [0,2,4,6,8]], goal)
        self.assertEqual(fixed[-1][0].s,5)
        self.assertTrue(all(a[0].s < b[0].s for a,b in zip(fixed,fixed[1:])))

    def test_missing_lane_anchor_fails_instead_of_inventing_a_route(self):
        with self.assertRaises(RuntimeError):
            arrival_route([(Waypoint(0,1),None)],Waypoint(3,-1))

    def test_nearby_later_leg_does_not_jump_to_destination(self):
        path = route([(0,0),(10,0),(20,0),(20,20),(10,20),(0,20),(0,1)])
        approach = ArrivalApproach(path)
        approach.update(Location(0,1))
        self.assertGreater(approach.remaining_m,70)
        self.assertEqual(approach.target_speed_kmh(20),20)

    def test_curve_speed_uses_route_length_and_reduces_before_arrival_radius(self):
        approach = ArrivalApproach(route([(0,0),(10,0),(10,10)]))
        approach.update(Location(10,2))
        self.assertEqual(approach.remaining_m,8)
        speed = approach.target_speed_kmh(20)
        self.assertGreater(speed,0)
        self.assertLess(speed,20)
        approach.update(Location(10,9.6))
        self.assertEqual(approach.target_speed_kmh(20),0)

    def test_braking_keeps_live_steering_and_cannot_override_hazard_stop(self):
        approach = ArrivalApproach(route([(0,0),(10,0)]))
        agent = Mock()
        agent.run_step.return_value = NS(throttle=0.0, brake=0.5, steer=0.42)
        approach.update(Location(5))
        control = approach_control(agent, approach,20)
        self.assertEqual((control.steer,control.brake,control.throttle),(.42,.5,0))
        approach.update(Location(9.6))
        control = approach_control(agent, approach,20)
        self.assertEqual((control.steer,control.brake,control.throttle),(.42,1,0))
        agent.set_arrival_speed.assert_called_with(0,20)
        self.assertEqual(agent.run_step.call_count,2)

    def test_arrival_requires_stop_heading_and_centering(self):
        waypoint = Waypoint(5)
        vehicle = Mock()
        for speed, yaw, y, expected in [(5.34,0,0,False),(.01,-33,0,False),
                                        (.01,0,-1.02,False),(.01,3,.1,True)]:
            vehicle.get_transform.return_value = NS(location=Location(5,y),rotation=NS(yaw=yaw))
            self.assertEqual(stopped_and_aligned(vehicle,waypoint,speed),expected)

    def test_alignment_creep_retains_obstacle_braking_and_stops_once_aligned(self):
        approach = ArrivalApproach(route([(0,0),(10,0)]))
        approach.update(Location(9.6))
        approach.settling = True
        agent = Mock()
        agent.run_step.return_value = NS(steer=.3,throttle=0,brake=.5)
        control = approach_control(agent,approach,20)
        agent.set_arrival_speed.assert_called_with(1.0,20)
        self.assertEqual(control.brake,.5)
        self.assertEqual(control.throttle,0)
        approach.settling = False
        control = approach_control(agent,approach,20)
        self.assertEqual(control.brake,1)

    def test_runner_wait_starts_only_after_stopping_and_records_one_visit(self):
        root = Path(__file__).resolve().parents[1]
        sim = TripSimulation(TripSimulationConfig.from_json(root/'config/multi_vehicle_trip.json'),root,1)
        sim.logger = Mock()
        sim._sample_trajectory = Mock()
        state = sim.primary_vehicle_state
        destination = NS(destination_id='T01_067',destination_name='Curve',category='services_leisure')
        approach = ArrivalApproach(route([(0,0),(10,0)]))
        state.active_trip = ActiveTrip(
            trip_number=1,origin_id='origin',origin_name='Origin',origin_location=Location(),
            destination=destination,destination_location=Location(10),departure_time_s=0,
            last_location=Location(),last_moving_time_s=0,agent=Mock(),planned_route_distance_m=10,
            selection_class='routine',history_visit_count_before=0,selection_candidate_count=1,
            approach=approach,
        )
        vehicle, carla_map = Mock(), Mock()
        vehicle.get_location.return_value = Location(9.7)
        vehicle.get_transform.return_value = NS(location=Location(9.7),rotation=NS(yaw=0))
        carla_map.get_waypoint.side_effect = lambda location, **kwargs: Waypoint(location.x)
        vehicle.get_velocity.return_value = Location(5.34)
        sim._update_active_trip(carla_map,vehicle,100,5,state)
        self.assertIsNotNone(state.active_trip)
        self.assertIsNone(state.dwell_started_time_s)
        sim.logger.write_history.assert_not_called()
        # Measured second trial: centered but stopped with an 11 degree error.
        vehicle.get_transform.return_value.rotation.yaw=-11
        vehicle.get_velocity.return_value = Location(0.01)
        sim._update_active_trip(carla_map,vehicle,110,5.5,state)
        self.assertTrue(approach.settling)
        self.assertIsNone(state.dwell_started_time_s)
        for y, opposing in [(4.1,False),(0,True)]:
            vehicle.get_location.return_value = Location(9.7,y)
            vehicle.get_transform.return_value.location = Location(9.7,y)
            carla_map.get_waypoint.side_effect = lambda location, **kwargs: Waypoint(
                location.x, 1 if opposing and location.x < 10 else -1)
            sim._update_active_trip(carla_map,vehicle,115,5.75,state)
            self.assertFalse(approach.settling)
            self.assertIsNotNone(state.active_trip)
            self.assertIsNone(state.dwell_started_time_s)
        vehicle.get_location.return_value = Location(9.7)
        vehicle.get_transform.return_value.location = Location(9.7)
        carla_map.get_waypoint.side_effect = lambda location, **kwargs: Waypoint(location.x)
        vehicle.get_transform.return_value.rotation.yaw=0
        vehicle.get_velocity.return_value = Location(0.01)
        sim._update_active_trip(carla_map,vehicle,120,6,state)
        self.assertIsNone(state.active_trip)
        self.assertEqual(state.dwell_started_time_s,6)
        sim._update_active_trip(carla_map,vehicle,121,6.05,state)
        sim.logger.write_history.assert_called_once()
        self.assertEqual(sim.logger.write_trip.call_args[0][0]['arrival_sim_time_s'],6)
        self.assertEqual(state.completed_trips,1)


if __name__ == '__main__':
    unittest.main()
