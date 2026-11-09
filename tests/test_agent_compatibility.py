"""Offline regression against the installed CARLA SDK; never connects to a server."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.navigation.route_planner import configure_carla_agents


class CollinearObstacleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import carla
            configure_carla_agents(carla, os.environ.get("CARLA_PYTHONAPI"))
        except (ImportError, RuntimeError) as error:
            raise unittest.SkipTest("CARLA SDK/agents unavailable: {0}".format(error))
        from agents.navigation.basic_agent import BasicAgent
        from src.navigation.carla_agent import CollinearSafeBasicAgent
        cls.carla = carla
        cls.stock_type = BasicAgent
        cls.fixed_type = CollinearSafeBasicAgent

    def agent_and_target(self, agent_type, x=8.0, y=0.0):
        carla = self.carla

        def vehicle(actor_id, vx, vy):
            return SimpleNamespace(
                id=actor_id, bounding_box=carla.BoundingBox(
                    carla.Location(), carla.Vector3D(2.0, 0.8, 1.0)),
                get_transform=lambda: carla.Transform(carla.Location(vx, vy, 0)),
                get_location=lambda: carla.Location(vx, vy, 0),
                get_velocity=lambda: carla.Vector3D(5, 0, 0),
            )

        def waypoint(location, **kwargs):
            return SimpleNamespace(
                road_id=6, lane_id=1 if abs(location.y) < 1.0 else 2,
                lane_width=3.5, is_junction=False,
            )

        agent = agent_type.__new__(agent_type)
        agent._vehicle = vehicle(1, 0.0, 0.0)
        agent._map = SimpleNamespace(get_waypoint=waypoint)
        agent._ignore_vehicles = False
        agent._base_vehicle_threshold = 10.0
        agent._offset = 0
        agent._use_bbs_detection = False
        agent._local_planner = SimpleNamespace(
            get_plan=lambda: [],
            get_incoming_waypoint_and_direction=lambda steps: (waypoint(carla.Location()), None),
            run_step=lambda: carla.VehicleControl(throttle=0.4, steer=0.1),
        )
        return agent, vehicle(2, x, y)

    def test_stock_misses_exactly_collinear_vehicle_and_fix_detects_it(self):
        stock, target = self.agent_and_target(self.stock_type)
        self.assertFalse(stock._vehicle_obstacle_detected([target], 10)[0])
        fixed, target = self.agent_and_target(self.fixed_type)
        detected, actor, _ = fixed._vehicle_obstacle_detected([target], 10)
        self.assertTrue(detected)
        self.assertEqual(actor.id, 2)

    def test_fix_keeps_behind_adjacent_and_distant_vehicles_excluded(self):
        for x, y in [(-8.0, 0.0), (8.0, 3.5), (30.0, 0.0)]:
            with self.subTest(x=x, y=y):
                fixed, target = self.agent_and_target(self.fixed_type, x, y)
                self.assertFalse(fixed._vehicle_obstacle_detected([target], 10)[0])

    def test_nonzero_angle_and_explicit_positive_lower_bound_keep_stock_behavior(self):
        fixed, target = self.agent_and_target(self.fixed_type, 8, 0.2)
        self.assertTrue(fixed._vehicle_obstacle_detected([target], 10)[0])
        fixed, target = self.agent_and_target(self.fixed_type)
        self.assertFalse(fixed._vehicle_obstacle_detected([target], 10, low_angle_th=10)[0])

    def test_official_run_step_brakes_for_a_collinear_obstacle(self):
        fixed, target = self.agent_and_target(self.fixed_type)
        actors = Mock()
        actors.filter.return_value = [target]
        fixed._world = SimpleNamespace(get_actors=lambda: actors)
        fixed._speed_ratio = 1
        fixed._base_tlight_threshold = 5
        fixed._lights_list = []
        fixed._affected_by_traffic_light = Mock(return_value=(False, None))
        fixed._max_brake = 0.5
        control = fixed.run_step()
        self.assertEqual(control.throttle, 0.0)
        self.assertEqual(control.brake, 0.5)
        self.assertAlmostEqual(control.steer, 0.1)

    def test_arrival_horizon_tracks_speed_and_restores_cruise_without_changing_pid(self):
        fixed, _ = self.agent_and_target(self.fixed_type)
        local = fixed._local_planner
        local._base_min_distance = 3.0
        local._distance_ratio = 0.1
        local.set_speed = Mock()
        for speed, distance in [(20,3.0),(10,1.5),(0,1.0),(20,3.0)]:
            fixed.set_arrival_speed(speed,20)
            self.assertEqual(local._base_min_distance,distance)
            self.assertEqual(local._distance_ratio,0.1)
            local.set_speed.assert_called_with(speed)


if __name__ == "__main__":
    unittest.main()
