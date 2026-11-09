"""Offline LocalPlanner regression using the measured Town01 turn geometry."""

import os
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from src.navigation.route_planner import build_basic_agent, configure_carla_agents
from src.simulation.trip_runner import TripSimulationConfig
from scripts.run_trip_simulation import configuration_from_args


ROOT = Path(__file__).resolve().parents[1]


class TrackingConfigurationTests(unittest.TestCase):
    def test_ratio_defaults_and_explicit_stock_replay(self):
        """Check the default look-ahead ratio and the option to restore CARLA's original value."""
        for file in ("single_vehicle_trip.json", "multi_vehicle_trip.json"):
            config = TripSimulationConfig.from_json(ROOT / "config" / file)
            self.assertEqual(config.controller_distance_ratio, 0.1)
        config = TripSimulationConfig.from_json(ROOT / "config/multi_vehicle_trip.json",
                                                {"controller_distance_ratio": 0.5})
        self.assertEqual(config.controller_distance_ratio, 0.5)

    def test_invalid_ratios_rejected_before_connection(self):
        """Check that invalid look-ahead ratios fail before connecting to CARLA."""
        for value in (-0.1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                TripSimulationConfig.from_json(ROOT / "config/multi_vehicle_trip.json",
                                               {"controller_distance_ratio": value})

    def test_cli_replays_stock_ratio_and_enables_diagnostics(self):
        """Check command-line options for the original look-ahead ratio and navigation diagnostics."""
        args = NS(config=ROOT / "config/multi_vehicle_trip.json", town=None, seed=None,
                  seconds=None, scenario="random_baseline", history_in=None,
                  no_rendering=True, navigation_diagnostics=True, controller_distance_ratio=0.5)
        config = configuration_from_args(args)
        self.assertEqual(config.controller_distance_ratio, 0.5)
        self.assertTrue(config.navigation_diagnostics_enabled)


class LocalPlannerTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load the CARLA local planner or skip these tests if the SDK is unavailable."""
        try:
            import carla
            configure_carla_agents(carla, os.environ.get("CARLA_PYTHONAPI"))
        except (ImportError, RuntimeError) as error:
            raise unittest.SkipTest("CARLA SDK/agents unavailable: {0}".format(error))
        from agents.navigation.local_planner import LocalPlanner, RoadOption
        cls.carla, cls.planner_type, cls.option = carla, LocalPlanner, RoadOption

    def planner(self, ratio):
        """Build a local planner with a mock vehicle and a known curved route."""
        carla = self.carla
        vehicle = Mock()
        vehicle.get_location.return_value = carla.Location(92.989, 205.934, 0)
        vehicle.get_transform.return_value = carla.Transform(vehicle.get_location(), carla.Rotation(yaw=-77.628))
        vehicle.get_velocity.return_value = carla.Vector3D(0, -5.55, 0)
        vehicle.get_control.return_value = carla.VehicleControl()
        local = self.planner_type(vehicle, opt_dict={"distance_ratio": ratio})
        # Extracted from GlobalRoutePlanner in Town01, road 256, lane 1.
        xy = [(92.401, 206.330), (92.483, 204.649), (92.896, 203.172),
              (93.637, 201.829), (94.663, 200.697), (95.917, 199.845),
              (97.338, 199.316), (98.852, 199.141), (101.420, 199.141)]
        route = [(NS(transform=carla.Transform(carla.Location(x, y, 0))), self.option.RIGHT)
                 for x, y in xy]
        local.set_global_plan(route, stop_waypoint_creation=True, clean_queue=True)
        local._vehicle_controller = Mock()
        return local, route

    def test_shorter_horizon_keeps_curve_target_instead_of_skipping_it(self):
        """Check that shorter look-ahead retains the needed waypoint on a curve."""
        stock, stock_route = self.planner(0.5)
        fixed, fixed_route = self.planner(0.1)
        stock.run_step()
        fixed.run_step()
        self.assertIs(stock.target_waypoint, stock_route[5][0])
        self.assertIs(fixed.target_waypoint, fixed_route[3][0])
        self.assertAlmostEqual(stock._min_distance, 5.775, places=6)
        self.assertAlmostEqual(fixed._min_distance, 3.555, places=6)
        fixed._vehicle_controller.run_step.assert_called_once_with(20, fixed_route[3][0])

    def test_last_waypoint_still_brakes_when_reached(self):
        """Check that the local planner brakes after reaching the last waypoint."""
        local, route = self.planner(0.1)
        local._vehicle.get_location.return_value = route[-1][0].transform.location
        local.set_global_plan([route[-1]], stop_waypoint_creation=True, clean_queue=True)
        control = local.run_step()
        self.assertTrue(local.done())
        self.assertEqual(control.brake, 1)
        self.assertEqual(control.throttle, 0)

    def test_builder_keeps_full_plan_and_options_are_independent(self):
        """Check that agent construction preserves the whole route and does not share mutable options."""
        with patch("src.navigation.carla_agent.CollinearSafeBasicAgent") as agent_type:
            route = [object(), object()]
            build_basic_agent(object(), route, 20)
            first = agent_type.call_args[1]["opt_dict"]
            agent_type.return_value.set_global_plan.assert_called_with(
                route, stop_waypoint_creation=True, clean_queue=True)
            build_basic_agent(object(), route, 20, 0.5)
            second = agent_type.call_args[1]["opt_dict"]
            self.assertEqual(first, {"distance_ratio": 0.1})
            self.assertEqual(second, {"distance_ratio": 0.5})
            self.assertIsNot(first, second)


if __name__ == "__main__":
    unittest.main()
