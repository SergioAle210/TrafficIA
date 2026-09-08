"""Exercise the real runner and CSV writers against an in-memory CARLA double."""

import copy
import csv
import fnmatch
import json
import math
import unittest
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.trip_runner import TripSimulation, TripSimulationConfig


ROOT = Path(__file__).resolve().parents[1]


class Location:
    def __init__(self, x=1.0, y=2.0, z=0.0):
        self.x, self.y, self.z = x, y, z

    def distance(self, other):
        return math.sqrt(sum((getattr(self, key) - getattr(other, key)) ** 2 for key in "xyz"))


class Actors(list):
    def filter(self, pattern):
        return [actor for actor in self if fnmatch.fnmatch(actor.type_id, pattern)]


class RunnerScenarioTests(unittest.TestCase):
    def run_with_fake_server(self, mode, directory, failure=None, diagnostics=False):
        config = TripSimulationConfig.from_json(ROOT / "config/multi_vehicle_trip.json", {
            "destination_selection_mode": mode, "duration_seconds": 0.11,
            "output_root": directory,
            "navigation_diagnostics_enabled": diagnostics,
        })
        if mode == "random_baseline":
            config.vehicle_history_config = "deliberately-missing.csv"
        simulation = TripSimulation(config, ROOT, 1)
        world, client, carla_map = Mock(), Mock(), Mock()
        carla_map.name = "Carla/Maps/Town01"
        carla_map.get_spawn_points.return_value = list(range(140))
        carla_map.get_waypoint.return_value = SimpleNamespace(
            transform=SimpleNamespace(location=Location()), road_id=4, lane_id=-1,
        )
        settings = SimpleNamespace(synchronous_mode=False, fixed_delta_seconds=None, no_rendering_mode=False)
        world.get_settings.side_effect = lambda: copy.copy(settings)
        world.get_map.return_value = carla_map
        client.get_world.return_value = world
        client.get_server_version.return_value = "0.9.15"
        actors, sensors, spawn_indices = Actors(), [], []
        signal = Mock(type_id="traffic.traffic_light")
        signal.get_opendrive_id.return_value = "signal_1"
        signal.get_state.return_value = "Red"
        signal.get_elapsed_time.return_value = 0.05
        signal.get_green_time.return_value = 10.0
        signal.get_yellow_time.return_value = 3.0
        signal.get_red_time.return_value = 10.0
        signal.is_frozen.return_value = False
        actors.append(signal)
        world.get_actors.return_value = actors
        world.get_weather.return_value = SimpleNamespace(
            cloudiness=10.0, precipitation=0.0, sun_altitude_angle=70.0,
            sun_azimuth_angle=20.0,
        )
        tick_times = []

        def tick():
            tick_times.append(len(tick_times) * 0.05 + 0.05)
            if failure == "interrupt" and len(tick_times) == 5:
                raise KeyboardInterrupt()
            return len(tick_times)

        world.tick.side_effect = tick
        world.get_snapshot.side_effect = lambda: SimpleNamespace(
            timestamp=SimpleNamespace(elapsed_seconds=tick_times[-1])
        )

        def spawn(_world, _blueprint, _carla, _map, _points, index, _fallback, vehicle_id):
            spawn_indices.append(index)
            if failure == "spawn" and len(spawn_indices) == 2:
                raise RuntimeError("occupied spawn")
            actor = Mock(id=100 + len(spawn_indices), type_id="vehicle.test",
                         attributes={"role_name": vehicle_id}, is_alive=True)
            actor.get_location.side_effect = Location
            actor.get_velocity.return_value = Location(1.0, 0.0, 0.0)
            actor.get_acceleration.return_value = Location(0.0, 0.0, 0.0)
            actors.append(actor)
            return actor, index

        def spawn_sensor(*args, **kwargs):
            sensor = Mock(is_alive=True)
            sensors.append(sensor)
            if failure == "sensor":
                sensor.listen.side_effect = RuntimeError("sensor listen failed")
            return sensor

        world.spawn_actor.side_effect = spawn_sensor
        blueprint = Mock()
        blueprint.has_attribute.return_value = False
        fake_carla = SimpleNamespace(
            Client=Mock(return_value=client), Transform=Mock(),
            VehicleControl=lambda **kwargs: SimpleNamespace(**kwargs),
            LaneType=SimpleNamespace(Driving=1),
        )
        agents = []

        def build_agent(*args):
            agent = Mock()
            agents.append(agent)
            return agent

        replacements = {
            "configure_carla_agents": Mock(),
            "validate_destinations_on_map": Mock(),
            "safe_vehicle_blueprints": Mock(return_value=[blueprint]),
            "spawn_vehicle_at_first_available_point": Mock(side_effect=spawn),
            "driving_transform_from_spawn_point": Mock(return_value=SimpleNamespace(location=Location())),
            "resolve_destination_location": Mock(return_value=Location(51.0, 2.0, 0.0)),
            "build_global_route_planner": Mock(),
            "plan_route": Mock(return_value=["fake road route"]),
            "validate_route_start": Mock(return_value=0.0),
            "route_distance_m": Mock(return_value=50.0),
            "build_basic_agent": Mock(side_effect=build_agent),
            "RouteTrace": Mock(side_effect=lambda route: SimpleNamespace(
                points=[dict(index=0, x=1, y=2)],
                sample=lambda vehicle, agent, control: dict(steer=0.25),
            )),
        }
        with ExitStack() as stack:
            stack.enter_context(patch.dict("sys.modules", {"carla": fake_carla}))
            stack.enter_context(patch("src.trip_runner.time.sleep"))
            for name, replacement in replacements.items():
                stack.enter_context(patch("src.trip_runner." + name, replacement))
            if failure:
                with self.assertRaises(KeyboardInterrupt if failure == "interrupt" else RuntimeError):
                    simulation.run()
            else:
                simulation.run()

        # Normal termination, Ctrl+C and setup failures all release owned resources.
        for actor in actors.filter("vehicle.*"):
            actor.destroy.assert_called_once_with()
        for sensor in sensors:
            sensor.stop.assert_called_once_with()
            sensor.destroy.assert_called_once_with()
        self.assertEqual(world.apply_settings.call_args[0][0], settings)
        self.assertTrue(all(state.actor is None and not state.sensors for state in simulation.vehicle_states))
        world.set_weather.assert_not_called()
        if not failure:
            for agent, actor in zip(agents, actors.filter("vehicle.*")):
                self.assertEqual(agent.run_step.call_count, 2)
                # One initial brake and the two unmodified agent commands.
                self.assertEqual(actor.apply_control.call_count, 3)
                for call in actor.apply_control.call_args_list[1:]:
                    self.assertIs(call[0][0], agent.run_step.return_value)
        return simulation, world, spawn_indices, replacements

    def test_diagnostics_capture_each_command_without_extra_ticks_or_agent_steps(self):
        with TemporaryDirectory() as directory:
            simulation, world, _, helpers = self.run_with_fake_server(
                "random_baseline", directory, diagnostics=True)
            self.assertEqual(world.tick.call_count, 7)
            self.assertEqual(helpers["RouteTrace"].call_count, 3)
            output = simulation._output_directory()
            with (output / "control_log.csv").open(newline="") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 6)
            self.assertEqual({row["frame"] for row in rows}, {"4", "5"})
            self.assertEqual({row["trip_id"] for row in rows}, {"trip_001"})
            for state in simulation.vehicle_states:
                # The runner clears actor/trip references in cleanup, but the
                # builder has exactly one call per car, with the same setting.
                self.assertEqual(sum(row["vehicle_id"] == state.vehicle_id for row in rows), 2)
            self.assertEqual([call[0][3] for call in helpers["build_basic_agent"].call_args_list],
                             [0.1, 0.1, 0.1])

    def test_both_scenarios_write_all_vehicle_ids_and_share_one_tick_per_frame(self):
        for mode in ("random_baseline", "history_80_20"):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                simulation, world, spawns, helpers = self.run_with_fake_server(mode, directory)
                self.assertEqual(spawns, [133, 6, 101])
                # Three setup frames, three simulation frames, one cleanup frame.
                self.assertEqual(world.tick.call_count, 7)
                world.reset_all_traffic_lights.assert_called_once_with()
                helpers["build_global_route_planner"].assert_called_once()
                self.assertEqual(helpers["build_basic_agent"].call_count, 3)
                output = simulation._output_directory()
                self.assertFalse((output / "control_log.csv").exists())
                helpers["RouteTrace"].assert_not_called()
                expected_ids = {"vehicle_001", "vehicle_002", "vehicle_003"}
                for name in ("trips_log.csv", "trajectory_log.csv"):
                    with (output / name).open(encoding="utf-8", newline="") as file:
                        rows = list(csv.DictReader(file))
                    self.assertEqual({row["vehicle_id"] for row in rows}, expected_ids)
                    if name == "trips_log.csv":
                        self.assertEqual({row["status"] for row in rows}, {"aborted"})
                        if mode == "random_baseline":
                            self.assertEqual({row["selection_class"] for row in rows}, {mode})
                with (output / "metrics_summary.csv").open(encoding="utf-8", newline="") as file:
                    metrics = next(csv.DictReader(file))
                self.assertEqual(metrics["vehicle_count"], "3")
                self.assertEqual(metrics["trips_incomplete"], "3")
                with (output / "vehicle_history.csv").open(encoding="utf-8", newline="") as file:
                    history = list(csv.DictReader(file))
                self.assertEqual(len(history), 0 if mode == "random_baseline" else 90)
                with (output / "run_config.json").open(encoding="utf-8") as file:
                    metadata = json.load(file)
                self.assertEqual(metadata["scenario"], mode)
                self.assertEqual(metadata["metrics_semantics_version"], 2)
                self.assertEqual([v["carla_actor_id"] for v in metadata["vehicles"]], [101, 102, 103])
                self.assertIn("CollinearSafeBasicAgent", metadata["route_planning"]["controller_compatibility_fix"])
                self.assertEqual(metadata["environment"]["weather"]["sun_altitude_angle"], 70.0)
                self.assertTrue(metadata["environment"]["traffic_lights_reset"])
                self.assertEqual(metadata["environment"]["external_vehicle_count"], 0)
                self.assertEqual(metadata["environment"]["traffic_lights"][0]["state"], "Red")

    def test_ctrl_c_cleans_up_all_actors_and_sensors(self):
        with TemporaryDirectory() as directory:
            self.run_with_fake_server("random_baseline", directory, "interrupt")

    def test_spawn_failure_cleans_up_previously_created_vehicle(self):
        with TemporaryDirectory() as directory:
            self.run_with_fake_server("random_baseline", directory, "spawn")

    def test_listen_failure_cleans_up_the_new_sensor_too(self):
        with TemporaryDirectory() as directory:
            self.run_with_fake_server("random_baseline", directory, "sensor")


if __name__ == "__main__":
    unittest.main()
