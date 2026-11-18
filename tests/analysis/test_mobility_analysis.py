"""Metric populations, incomplete trips, callback units and legacy coverage."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path
from src.analysis.mobility_analysis import analyze_run, paired_checks


def write_rows(path, rows):
    """Write sample records with a header to a temporary CSV file."""
    with path.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class MobilityAnalysisTests(unittest.TestCase):
    def setUp(self):
        """Prepare known trip, sensor, and summary records in a temporary run folder."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.config = dict(run_id="run", scenario="random_baseline", seed=42, vehicle_count=2, map="Town01",
                           metrics_semantics_version=3, destinations=[dict(destination_id="A", category="home"),
                           dict(destination_id="B", category="work"), dict(destination_id="C", category="services")])
        self.trips = []
        for vehicle, trip, dest, category, departure, duration, distance, status, lanes in [
                ("v1", "t1", "A", "home", 0, 10, 100, "completed", 1),
                ("v2", "t1", "B", "work", 0, 20, 100, "completed", 0),
                ("v1", "t2", "A", "home", 15, 5, 50, "aborted", 0)]:
            self.trips.append(dict(run_id="run", vehicle_id=vehicle, trip_id=trip, destination_id=dest,
                                   destination_category=category, departure_sim_time_s=departure,
                                   arrival_sim_time_s=departure+duration if status == "completed" else "",
                                   travel_time_s=duration, distance_traveled_m=distance, status=status,
                                   lane_invasion_count=lanes, collision_count=0))
        self.events = [dict(run_id="run", vehicle_id="v1", trip_id="t1", event_type="lane_invasion"),
                       dict(run_id="run", vehicle_id="v1", trip_id="", event_type="lane_invasion"),
                       dict(run_id="run", vehicle_id="v1", trip_id="", event_type="collision")]
        self.summary = dict(run_id="run", vehicle_count=2, trips_started=3, trips_completed=2, trips_incomplete=1,
                            simulation_duration_s=20, total_distance_traveled_m=250,
                            total_observed_distance_m=260, total_vehicle_time_s=40, total_collisions=1, total_lane_invasions=2)

    def analyze(self):
        """Write the current test records and analyze them as a simulation run."""
        (self.path / "run_config.json").write_text(json.dumps(self.config), encoding="utf8")
        write_rows(self.path / "trips_log.csv", self.trips)
        write_rows(self.path / "events_log.csv", self.events)
        write_rows(self.path / "metrics_summary.csv", [self.summary])
        return analyze_run(self.path)

    def test_complete_times_and_assigned_reached_populations_stay_separate(self):
        """Check that completed travel times, destination assignments, and arrivals use their correct populations."""
        result = self.analyze()
        self.assertEqual(result["integrity_errors"], [])
        self.assertEqual(result["travel_time"]["mean_s"], 15)
        self.assertEqual(result["travel_time"]["count"], 2)
        self.assertEqual(result["incomplete_trips"][0]["elapsed_time_s"], 5)
        a = result["destinations"]["assigned"]["by_id"][0]
        b = result["destinations"]["reached"]["by_id"][0]
        self.assertAlmostEqual(a["proportion"], 2/3)
        self.assertEqual(b["proportion"], .5)
        self.assertEqual(result["destinations"]["assigned"]["by_id"][2]["count"], 0)

    def test_full_exposure_includes_dwell_events_and_uses_ratio_of_totals(self):
        """Check that full-presence rates include waiting events and divide aggregate totals."""
        result = self.analyze()
        self.assertEqual(result["speed"]["mean_kmh"], 23.4)
        self.assertAlmostEqual(result["events"]["lane_invasion"]["per_vehicle_km"], 2/.260)
        self.assertAlmostEqual(result["events"]["collision"]["per_vehicle_km"], 1/.260)
        self.assertEqual(result["events"]["lane_invasion"]["unassigned_callbacks"], 1)

    def test_legacy_uses_active_trip_exposure_and_preserves_all_event_counts(self):
        """Check that legacy runs use active-trip exposure while retaining all observed event counts."""
        self.config["metrics_semantics_version"] = 2
        result = self.analyze()
        self.assertAlmostEqual(result["speed"]["mean_kmh"], 3.6*250/35)
        self.assertEqual(result["events"]["lane_invasion"]["per_vehicle_km"], 4)
        self.assertEqual(result["events"]["lane_invasion"]["observed_callbacks"], 2)
        self.assertEqual(result["events"]["collision"]["per_vehicle_km"], 0)
        self.assertTrue(result["warnings"])

    def test_zero_exposure_and_no_arrivals_are_undefined_not_zero_success(self):
        """Check that unavailable rates and travel-time averages are reported as undefined."""
        for t in self.trips:
            t.update(status="aborted", arrival_sim_time_s="", distance_traveled_m=0)
        self.summary.update(trips_completed=0, trips_incomplete=3, total_observed_distance_m=0, total_distance_traveled_m=0)
        result = self.analyze()
        self.assertIsNone(result["travel_time"]["mean_s"])
        self.assertIsNone(result["events"]["lane_invasion"]["per_vehicle_km"])
        self.assertTrue(all(b["proportion"] is None for b in result["destinations"]["reached"]["by_id"]))

    def test_integrity_failures_are_reported_instead_of_silently_excluding_rows(self):
        """Check that inconsistent records produce integrity errors instead of being silently discarded."""
        self.trips[-1]["arrival_sim_time_s"] = 20
        self.events[0]["trip_id"] = "unknown"
        self.summary["total_vehicle_time_s"] = 30
        result = self.analyze()
        self.assertIn("event assigned to unknown trip", result["integrity_errors"])
        self.assertIn("vehicle time does not cover full run", result["integrity_errors"])
        self.assertTrue(any("incomplete trip has arrival" in e for e in result["integrity_errors"]))

    def test_comparison_checks_time_policy_and_exposure_without_rejecting_events(self):
        """Check that comparison validates timing and exposure settings without treating incidents as invalid runs."""
        baseline = self.analyze()
        history = copy.deepcopy(baseline)
        history.update(run="history", scenario="history_80_20")
        self.assertTrue(paired_checks([baseline, history])[0]["comparable"])
        history["comparability"]["trip_time_policy"] = dict(max_trip_time_seconds=300)
        history["exposure"]["scope"] = "legacy_active_trip_intervals"
        check = paired_checks([baseline, history])[0]
        self.assertFalse(check["comparable"])
        self.assertIn("trip_time_policy", check["differences"])
        self.assertIn("exposure_scope", check["differences"])

    def test_visual_review_source_hashes_are_used_for_pair_comparison(self):
        """Check that source fingerprints recorded by visual review are considered when comparing runs."""
        (self.path / 'visual_review_config.json').write_text(json.dumps(dict(source_sha256={'runner':'abc'})), encoding='utf8')
        baseline = self.analyze()
        history = copy.deepcopy(baseline)
        history.update(run='history', scenario='history_80_20')
        self.assertEqual(baseline['comparability']['source_sha256'], {'runner':'abc'})
        self.assertTrue(paired_checks([baseline, history])[0]['comparable'])
        history['comparability']['source_sha256']['runner'] = 'different'
        self.assertIn('source_sha256', paired_checks([baseline, history])[0]['differences'])


if __name__ == "__main__":
    unittest.main()
