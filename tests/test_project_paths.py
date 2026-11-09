"""Relocated inputs preserve bytes, old manifests and snapshot isolation."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_pilots import write_new_or_identical
from scripts.run_demand_campaign import check_hashes
from src.project_paths import PROJECT_ROOT, project_path
from src.simulation.trip_runner import TripSimulation, TripSimulationConfig


class ProjectPathTests(unittest.TestCase):
    def test_all_relocated_inputs_keep_their_original_bytes(self):
        manifest = json.loads((PROJECT_ROOT / "docs/relocation-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 25)
        for entry in manifest["files"]:
            with self.subTest(path=entry["new"]):
                current = PROJECT_ROOT / entry["new"]
                self.assertEqual(project_path(entry["old"]), current)
                self.assertEqual(project_path(PROJECT_ROOT / entry["old"]), current)
                self.assertEqual(hashlib.sha256(current.read_bytes()).hexdigest(), entry["sha256"])

    def test_frozen_campaign_manifest_still_verifies(self):
        path = project_path("config/demand_20_100/preparation_manifest.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        check_hashes(manifest["input_sha256"])

    def test_existing_snapshot_takes_priority_over_relocated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / "config/multi_vehicle_trip.json"
            new = root / "config/trips/multi_vehicle_trip.json"
            old.parent.mkdir(parents=True)
            new.parent.mkdir(parents=True)
            old.write_bytes(b"original snapshot")
            new.write_bytes(b"different preparation")
            self.assertEqual(project_path(old, root), old)
            self.assertEqual(project_path("config/multi_vehicle_trip.json", root).read_bytes(), b"original snapshot")

    def test_unknown_or_external_paths_are_not_redirected_to_project_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "checkout"
            external = Path(folder) / "snapshot/config/multi_vehicle_trip.json"
            self.assertEqual(project_path(external, root), external)
            self.assertEqual(project_path("data/input/missing.csv", root), root / "data/input/missing.csv")

    def test_old_and_current_config_paths_load_the_same_simulation(self):
        for old, new in (
            ("config/multi_vehicle_trip.json", "config/trips/multi_vehicle_trip.json"),
            ("config/demand_20_100/town01_100.json", "config/experiments/demand_20_100/town01_100.json"),
        ):
            previous = TripSimulationConfig.from_json(PROJECT_ROOT / old)
            current = TripSimulationConfig.from_json(PROJECT_ROOT / new)
            self.assertEqual(previous, current)
            simulation = TripSimulation(current, PROJECT_ROOT, 1)
            # The usual loading path still uses the original strings in the JSON.
            from src.demand.destinations import load_destinations
            simulation.destinations = load_destinations(PROJECT_ROOT / current.destinations_config, current.town)
            simulation.destinations_by_id = {item.destination_id: item for item in simulation.destinations}
            simulation._load_vehicle_histories()
            self.assertTrue(all(len(state.vehicle_history.events) == 30 for state in simulation.vehicle_states))

    def test_preparation_uses_relocated_path_and_refuses_different_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / "config/pilots/town01_05.json"
            new = root / "config/experiments/scaling_pilots/town01_05.json"
            write_new_or_identical(old, "frozen input\n", root)
            self.assertEqual(new.read_text(), "frozen input\n")
            before = new.read_bytes()
            write_new_or_identical(old, "frozen input\n", root)
            self.assertEqual(new.read_bytes(), before)
            with self.assertRaises(ValueError):
                write_new_or_identical(old, "different input\n", root)
            self.assertEqual(new.read_bytes(), before)
            self.assertFalse(old.exists())

    def test_relocated_snapshot_can_load_its_own_catalog_and_histories(self):
        manifest = json.loads((PROJECT_ROOT / "docs/relocation-manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for entry in manifest["files"]:
                target = root / entry["new"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PROJECT_ROOT / entry["new"], target)
            config = TripSimulationConfig.from_json(root / "config/experiments/demand_20_100/town01_100.json")
            simulation = TripSimulation(config, root, 1)
            from src.demand.destinations import load_destinations
            simulation.destinations = load_destinations(project_path(config.destinations_config, root), config.town)
            simulation.destinations_by_id = {item.destination_id: item for item in simulation.destinations}
            simulation._load_vehicle_histories()
            self.assertEqual(len(simulation.destinations), 42)
            self.assertEqual(len(simulation.vehicle_states), 100)
            self.assertTrue(all(len(state.vehicle_history.events) == 30 for state in simulation.vehicle_states))
            self.assertTrue(str(project_path(config.vehicle_history_config, root)).startswith(str(root)))


if __name__ == "__main__":
    unittest.main()
