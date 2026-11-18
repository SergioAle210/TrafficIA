"""Scenario selection and CLI regression tests, with no CARLA server."""

import argparse
import io
import json
import random
import unittest
from collections import Counter
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, mock_open, patch

from src.project_paths import PROJECT_ROOT as ROOT
from scripts.simulation.run_trips import configuration_from_args, main
from src.demand.destinations import load_destinations, select_uniform_destination
from src.simulation.trip_runner import ActiveTrip, TripSimulation, TripSimulationConfig
from src.demand.vehicle_history import VehicleHistory


CONFIG = ROOT / "config/trips/multi_vehicle_trip.json"
CATALOG = ROOT / "data/input/Town01/destinations_config.csv"


def simulation_for(mode="random_baseline", **overrides):
    """Build a simulation and catalog for the requested selector without connecting to CARLA."""
    overrides["destination_selection_mode"] = mode
    simulation = TripSimulation(
        TripSimulationConfig.from_json(CONFIG, overrides), ROOT, 1
    )
    simulation.destinations = load_destinations(CATALOG, "Town01")
    simulation.destinations_by_id = {
        item.destination_id: item for item in simulation.destinations
    }
    return simulation


def cli_args(**changes):
    """Create command-line arguments with defaults and the requested test overrides."""
    values = dict(
        config=CONFIG, town=None, seed=None, seconds=None, scenario=None,
        history_in=None, no_rendering=False,
    )
    values.update(changes)
    return argparse.Namespace(**values)


class UniformSelectionTests(unittest.TestCase):
    def setUp(self):
        """Load the destination catalog used in uniform-selection tests."""
        self.catalog = load_destinations(CATALOG, "Town01")

    def test_uniform_choice_receives_every_eligible_id_once_in_sorted_order(self):
        """Check that the random draw receives each eligible destination once in a stable order."""
        rng = Mock()
        rng.choice.side_effect = lambda candidates: candidates[0]
        select_uniform_destination(reversed(self.catalog), "T01_133", rng)
        candidates = rng.choice.call_args[0][0]
        expected = sorted(
            item.destination_id for item in self.catalog
            if item.destination_id != "T01_133"
        )
        self.assertEqual([item.destination_id for item in candidates], expected)
        self.assertEqual(len(candidates), 41)
        rng.random.assert_not_called()  # No category or routine branch before choice.

    def test_disabled_and_current_destinations_are_excluded(self):
        """Check that disabled destinations and the current destination are excluded from uniform selection."""
        current, other = self.catalog[:2]
        disabled = replace(self.catalog[2], enabled=False)
        for seed in range(20):
            self.assertEqual(
                select_uniform_destination(
                    [disabled, current, other], current.destination_id, random.Random(seed)
                ), other,
            )

    def test_no_candidates_raise_a_clear_error(self):
        """Check that an empty candidate set produces a clear error."""
        with self.assertRaisesRegex(ValueError, "ubicación actual"):
            select_uniform_destination([self.catalog[0]], self.catalog[0].destination_id, random.Random(42))

    def test_same_seed_and_different_csv_order_give_same_successive_sequence(self):
        """Check that CSV row order does not change the destination sequence for the same seed."""
        sequences = []
        for catalog in (self.catalog, list(reversed(self.catalog))):
            rng = random.Random(42)
            current = "T01_133"
            sequence = []
            for _ in range(200):
                destination = select_uniform_destination(catalog, current, rng)
                self.assertNotEqual(destination.destination_id, current)
                current = destination.destination_id
                sequence.append(current)
            sequences.append(sequence)
        self.assertEqual(*sequences)

    def test_weights_frequency_labels_and_categories_do_not_affect_draws(self):
        """Check that legacy weights, labels, and categories do not influence uniform draws."""
        changed = [
            replace(item, weight=float((index + 1) ** 5), frequency_class="routine",
                    category="arbitrary")
            for index, item in enumerate(self.catalog)
        ]
        sequences = []
        for catalog in (self.catalog, changed):
            rng = random.Random(42)
            sequences.append([
                select_uniform_destination(catalog, "T01_133", rng).destination_id
                for _ in range(200)
            ])
        self.assertEqual(*sequences)

    def test_fixed_seed_frequency_smoke_test(self):
        """Check that a repeatable sample of uniform draws has roughly balanced destination frequencies."""
        # Fixed seed, generous tolerance; structural choice test above is the contract.
        rng = random.Random(42)
        counts = Counter(
            select_uniform_destination(self.catalog[:3], None, rng).destination_id
            for _ in range(12000)
        )
        self.assertEqual(len(counts), 3)
        self.assertTrue(all(3700 < count < 4300 for count in counts.values()))


class ScenarioConfigurationTests(unittest.TestCase):
    def test_cli_overrides_are_applied_before_validation(self):
        """Check that command-line overrides take effect before configuration validation."""
        with CONFIG.open(encoding="utf-8") as file:
            payload = json.load(file)
        payload.update(destination_selection_mode="cyclic", destination_cycle_order=[],
                       duration_seconds=-1)
        payload.pop("vehicle_history_config")
        with patch("pathlib.Path.open", mock_open(read_data=json.dumps(payload))):
            config = configuration_from_args(cli_args(scenario="random_baseline", seconds=600))
        self.assertEqual(config.destination_selection_mode, "random_baseline")
        self.assertEqual(config.duration_seconds, 600)
        self.assertEqual(config.vehicle_history_config, "")

    def test_no_cli_scenario_keeps_configured_mode_and_single_vehicle_compatibility(self):
        """Check that omitting the scenario override preserves configuration and single-vehicle compatibility."""
        config = configuration_from_args(cli_args())
        self.assertEqual(config.destination_selection_mode, "history_80_20")
        single = TripSimulationConfig.from_json(ROOT / "config/single_vehicle_trip.json")
        self.assertEqual(single.vehicle_count, 1)
        self.assertEqual(single.resolved_spawn_point_indices(), [133])

    def test_history_input_rejected_for_explicit_or_json_baseline(self):
        """Check that uniform-baseline mode rejects an explicit history input."""
        with self.assertRaisesRegex(ValueError, "--history-in"):
            configuration_from_args(cli_args(scenario="random_baseline", history_in=Path("missing.csv")))
        config = simulation_for().config
        with patch("scripts.simulation.run_trips.TripSimulationConfig.from_json", return_value=config):
            with self.assertRaisesRegex(ValueError, "--history-in"):
                configuration_from_args(cli_args(history_in=Path("missing.csv")))

    def test_configuration_errors_do_not_connect_to_carla(self):
        """Check that invalid configurations fail before any CARLA connection is attempted."""
        args = cli_args(scenario="random_baseline", history_in=Path("missing.csv"))
        with patch("scripts.simulation.run_trips.parse_args", return_value=args), \
                patch("scripts.simulation.run_trips.TripSimulation") as runner, \
                redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(), 1)
        runner.assert_not_called()
        self.assertIn("--history-in", error.getvalue())

    def test_legacy_modes_are_still_accepted(self):
        """Check that supported legacy selection modes remain valid."""
        for mode in ("cyclic", "stochastic"):
            simulation = simulation_for(mode)
            simulation._load_vehicle_histories()
            simulation._validate_destination_cycle()
            self.assertIsNotNone(simulation._select_next_destination().destination)

    def test_baseline_does_not_open_history_even_when_missing(self):
        """Check that uniform-baseline execution does not need to open an initial history file."""
        simulation = simulation_for(vehicle_history_config="does-not-exist.csv")
        with patch.object(VehicleHistory, "from_csv", side_effect=AssertionError("Must not load history")):
            simulation._load_vehicle_histories()
        self.assertEqual([len(s.vehicle_history.events) for s in simulation.vehicle_states], [0, 0, 0])
        self.assertTrue(all(s.initial_history_counts == {} for s in simulation.vehicle_states))

    def test_history_mode_still_requires_a_valid_history_for_all_vehicles(self):
        """Check that historical mode requires a valid initial history for every vehicle."""
        with self.assertRaisesRegex(ValueError, "obligatorio"):
            simulation_for("history_80_20", vehicle_history_config="")
        with self.assertRaises(FileNotFoundError):
            simulation_for("history_80_20", vehicle_history_config="does-not-exist.csv")._load_vehicle_histories()
        simulation = simulation_for("history_80_20")
        simulation._load_vehicle_histories()
        self.assertEqual([len(s.vehicle_history.events) for s in simulation.vehicle_states], [30, 30, 30])


class BaselineStateTests(unittest.TestCase):
    def test_histories_actor_randomness_and_other_vehicles_do_not_affect_choices(self):
        """Check that uniform choices are independent of histories, actor setup, and other vehicles."""
        first, second = simulation_for(), simulation_for()
        first._load_vehicle_histories()
        second._load_vehicle_histories()
        for index, state in enumerate(second.vehicle_states):
            for _ in range(100 + index):
                state.vehicle_history.record("T01_006")
                state.actor_rng.random()
        # Interleave the vehicles differently to detect accidental shared RNGs.
        sequences = {}
        for simulation, order in ((first, [0, 1, 2]), (second, [2, 1, 0])):
            sequences[simulation] = {}
            for index in order:
                state = simulation.vehicle_states[index]
                state.current_destination_id = "T01_133"
                sequence = []
                for _ in range(100):
                    decision = simulation._select_next_destination(state)
                    self.assertEqual(decision.selection_class, "random_baseline")
                    self.assertEqual(decision.candidate_count, 41)
                    state.current_destination_id = decision.destination.destination_id
                    sequence.append(state.current_destination_id)
                sequences[simulation][index] = sequence
        self.assertEqual(sequences[first], sequences[second])
        self.assertEqual(len({tuple(s) for s in sequences[first].values()}), 3)

    def test_only_completed_visits_enter_the_corresponding_passive_history(self):
        """Check that passive history records only completed visits for the correct vehicle."""
        for status in ("completed", "aborted", "blocked", "timeout", "route_failed"):
            with self.subTest(status=status):
                simulation = simulation_for()
                simulation._load_vehicle_histories()
                simulation.logger = Mock()
                simulation._write_initial_histories()
                simulation.logger.write_history.assert_not_called()
                state = simulation.vehicle_states[1]
                destination = simulation.destinations[0]
                location = argparse.Namespace(x=1.0, y=2.0, z=0.0)
                state.active_trip = ActiveTrip(
                    trip_number=1, origin_id="T01_006", origin_name="Origin",
                    origin_location=location, destination=destination,
                    destination_location=location, departure_time_s=0.0,
                    last_location=location, last_moving_time_s=0.0, agent=None,
                    planned_route_distance_m=10.0, selection_class="random_baseline",
                    history_visit_count_before=0, selection_candidate_count=41,
                )
                simulation._finish_trip(10.0, status, state)
                expected = 1 if status == "completed" else 0
                self.assertEqual([len(s.vehicle_history.events) for s in simulation.vehicle_states], [0, expected, 0])
                self.assertEqual(simulation.logger.write_history.call_count, expected)
                row = simulation.logger.write_trip.call_args[0][0]
                self.assertEqual(row["vehicle_id"], "vehicle_002")
                self.assertEqual(row["selection_class"], "random_baseline")
                if expected:
                    history = simulation.logger.write_history.call_args[0][0]
                    self.assertEqual(history["sequence"], 1)
                    self.assertEqual(history["source"], "simulation")
                    self.assertEqual(history["vehicle_id"], "vehicle_002")

    def test_run_metadata_distinguishes_scenarios_and_history_use(self):
        """Check that run metadata clearly identifies the selector and how history is used."""
        for mode in ("random_baseline", "history_80_20"):
            simulation = simulation_for(mode)
            simulation._load_vehicle_histories()
            self.assertIn(mode, simulation._output_directory().name)
            with TemporaryDirectory() as directory:
                simulation._write_run_config(Path(directory), "0.9.15", simulation.destinations)
                with (Path(directory) / "run_config.json").open(encoding="utf-8") as file:
                    metadata = json.load(file)
            self.assertEqual(metadata["scenario"], mode)
            self.assertEqual(metadata["vehicle_count"], 3)
            self.assertEqual(len(metadata["vehicles"]), 3)
            selection = metadata["destination_selection"]
            self.assertEqual(selection["history_affects_selection"], mode == "history_80_20")
            if mode == "random_baseline":
                self.assertIsNone(selection["history_input"])
                self.assertEqual(selection["initial_visit_counts_by_vehicle"], {
                    "vehicle_001": {}, "vehicle_002": {}, "vehicle_003": {},
                })


if __name__ == "__main__":
    unittest.main()
