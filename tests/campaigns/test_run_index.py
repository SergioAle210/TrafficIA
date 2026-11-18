import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.campaigns.index_runs import build_rows, write_index


class DemoIndexTests(unittest.TestCase):
    def setUp(self):
        """Create a temporary demonstration campaign with explicit case identities."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.campaign_dir = self.root / "demo"
        self.campaign_dir.mkdir()
        self.path = self.campaign_dir / "campaign.json"
        self.cases = [
            dict(vehicle_count=n, scenario=s, status="pending", run_directories=[])
            for n in (20, 100) for s in ("random_baseline", "history_80_20")
        ]

    def save(self):
        """Write the current test cases to the temporary campaign manifest."""
        self.path.write_text(json.dumps(dict(duration_s=180, cases=self.cases)), encoding="utf-8")

    def test_labels_follow_cases_not_directory_order(self):
        """Check that index labels use case identities rather than directory order."""
        self.cases.reverse()
        self.save()
        rows = build_rows(self.path, self.root)
        self.assertEqual([r["caso"] for r in rows], [
            "100_historico_80_20", "100_uniforme", "20_historico_80_20", "20_uniforme",
        ])

    def test_partial_campaign_preserves_status_and_missing_results(self):
        """Check that unfinished campaigns retain their statuses and distinguish missing results from zeros."""
        self.cases[0].update(status="completed", completed_trips=0, run_directories=["run20"])
        self.cases[1].update(status="interrupted", run_directories=["partial"])
        self.save()
        rows = build_rows(self.path, self.root)
        self.assertEqual(rows[0]["viajes_completados"], 0)
        self.assertEqual(rows[1]["estado"], "interrupted")
        self.assertEqual(rows[1]["viajes_completados"], "")
        self.assertEqual(rows[2]["carpeta"], "")

    def test_index_links_real_logs_without_modifying_sources(self):
        """Check that the index links existing logs without modifying their contents."""
        run = self.root / "run20"
        run.mkdir()
        log = run / "trips_log.csv"
        log.write_text("trip_id,status\ntrip_001,completed\n", encoding="utf-8")
        self.cases[0].update(status="completed", completed_trips=1, run_directories=["run20"])
        self.save()
        before = (self.path.read_bytes(), log.read_bytes())
        csv_path, html_path = write_index(self.path, self.root)
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["caso"], "20_uniforme")
        self.assertEqual(Path(rows[0]["carpeta"]), run.resolve())
        markup = html_path.read_text(encoding="utf-8")
        self.assertIn(log.resolve().as_uri(), markup)
        self.assertNotIn('href="' + (run.resolve() / "events_log.csv").as_uri(), markup)
        self.assertEqual(before, (self.path.read_bytes(), log.read_bytes()))

    def test_duplicate_combination_is_rejected(self):
        """Check that duplicate demonstration case combinations are rejected."""
        self.cases.append(dict(self.cases[0]))
        self.save()
        with self.assertRaises(ValueError):
            build_rows(self.path, self.root)

    def test_run_directory_must_remain_under_output_root(self):
        """Check that indexed run directories cannot escape the allowed output folder."""
        self.cases[0]["run_directories"] = ["../outside"]
        self.save()
        with self.assertRaises(ValueError):
            build_rows(self.path, self.root)


if __name__ == "__main__":
    unittest.main()
