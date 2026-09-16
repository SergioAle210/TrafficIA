"""Descriptive mobility metrics with explicit populations and exposure.

No CARLA dependency; never changes or filters the original simulation logs.
Version 3 runs measure full vehicle presence, including dwell. Legacy runs
use active-trip intervals and only events assigned to those intervals for
rates, reporting all observed events separately.
"""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path):
    with Path(path).open(encoding="utf8", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Expected a finite nonnegative measurement: %r" % value)
    return result


def ratio(numerator, denominator):
    return numerator / denominator if denominator > 0 else None


def distribution(rows, field, domain):
    counts = Counter(row[field] for row in rows)
    return [dict(value=value, count=counts[value], proportion=ratio(counts[value], len(rows)))
            for value in sorted(set(domain) | set(counts))]


def analyze_run(path):
    path = Path(path)
    config = json.loads((path / "run_config.json").read_text(encoding="utf8"))
    trips = read_csv(path / "trips_log.csv")
    events = read_csv(path / "events_log.csv")
    summaries = read_csv(path / "metrics_summary.csv")
    if len(summaries) != 1:
        raise ValueError("Expected one metrics row: " + str(path))
    summary = summaries[0]
    errors, warnings = [], []

    def check(condition, message):
        if not condition:
            errors.append(message)

    key = lambda r: (r["vehicle_id"], r["trip_id"])
    keys = {key(t) for t in trips}
    check(len(keys) == len(trips), "duplicate trip key")
    check(all(t["run_id"] == config["run_id"] for t in trips + events), "run_id mismatch")
    check(summary["run_id"] == config["run_id"], "summary run_id mismatch")
    statuses = Counter(t["status"] for t in trips)
    check(set(statuses) <= {"completed", "aborted", "timeout", "blocked", "route_failed"}, "unknown trip status")
    completed = [t for t in trips if t["status"] == "completed"]
    incomplete = [t for t in trips if t["status"] != "completed"]
    times = [number(t["travel_time_s"]) for t in completed]
    for t in trips:
        duration = number(t["travel_time_s"])
        departure = number(t["departure_sim_time_s"])
        if t["status"] == "completed":
            check(abs(number(t["arrival_sim_time_s"]) - departure - duration) < 1e-4,
                  "arrival time mismatch: " + str(key(t)))
        else:
            check(t["arrival_sim_time_s"] == "", "incomplete trip has arrival: " + str(key(t)))
        if t.get("end_sim_time_s", "") != "":
            check(abs(number(t["end_sim_time_s"]) - departure - duration) < 1e-4,
                  "end time mismatch: " + str(key(t)))
            check(number(t["stopped_time_s"]) <= duration + 1e-4, "stopped time exceeds trip duration")
    check(int(summary["trips_started"]) == len(trips), "started count mismatch")
    check(int(summary["trips_completed"]) == len(completed), "completed count mismatch")
    check(int(summary["trips_incomplete"]) == len(incomplete), "incomplete count mismatch")
    check(int(summary["vehicle_count"]) == config["vehicle_count"], "vehicle count mismatch")
    trip_distance = sum(number(t["distance_traveled_m"]) for t in trips)
    trip_time = sum(number(t["travel_time_s"]) for t in trips)
    check(math.isclose(trip_distance, number(summary["total_distance_traveled_m"]), rel_tol=1e-7, abs_tol=1e-5),
          "trip distance summary mismatch")
    observed = Counter(e["event_type"] for e in events)
    assigned_events = [e for e in events if e["trip_id"]]
    check(all(key(e) in keys for e in assigned_events), "event assigned to unknown trip")
    assigned = Counter(e["event_type"] for e in assigned_events)
    per_trip_events = Counter((key(e), e["event_type"]) for e in assigned_events)
    for kind in ["collision", "lane_invasion"]:
        check(int(summary["total_" + kind + "s"]) == observed[kind], kind + " summary mismatch")
        for t in trips:
            check(int(t[kind + "_count"]) == per_trip_events[(key(t), kind)], "trip " + kind + " mismatch: " + str(key(t)))

    if (path / "vehicle_history.csv").exists():
        history = read_csv(path / "vehicle_history.csv")
        check(Counter(key(h) for h in history if h["trip_id"]) == Counter(key(t) for t in completed),
              "history/completed mismatch")
    if (path / "arrival_log.csv").exists():
        arrivals = read_csv(path / "arrival_log.csv")
        check(Counter(key(a) for a in arrivals) == Counter(key(t) for t in completed), "arrival/completed mismatch")
        for a in arrivals:
            check(number(a["speed_mps"]) <= .05 + 1e-8 and abs(float(a["heading_error_deg"])) <= 10 + 1e-8
                  and abs(float(a["lateral_error_m"])) <= .5 + 1e-8
                  and number(a["distance_to_destination_m"]) <= config.get("arrival_threshold_m", 4) + 1e-8
                  and number(a["route_remaining_m"]) <= .5 + 1e-8, "arrival thresholds: " + str(key(a)))
        # Lane topology is verified by the runner; this offline audit cannot
        # infer directed continuity solely from road/lane IDs in CSV files.

    schema = config.get("metrics_semantics_version", 1)
    if schema < 2:
        errors.append("event totals before semantics version 2 omit dwell; use a separately documented legacy audit")
    full_presence = schema >= 3
    if full_presence:
        distance = number(summary["total_observed_distance_m"])
        exposure_s = number(summary["total_vehicle_time_s"])
        rate_events = observed
        scope = "vehicle_presence_including_dwell"
        check(math.isclose(exposure_s, number(summary["simulation_duration_s"]) * config["vehicle_count"], abs_tol=.001),
              "vehicle time does not cover full run")
        check(distance + 1e-5 >= trip_distance, "full distance below active-trip distance")
    else:
        distance, exposure_s, rate_events = trip_distance, trip_time, assigned
        scope = "legacy_active_trip_intervals"
        warnings.append("Legacy exposure excludes dwell; rates include only assigned events. Full observed counts are retained.")
    if not distance:
        warnings.append("Zero distance exposure: rates per vehicle-km are undefined.")
    destinations = config.get("destinations", [])
    destination_ids = [d["destination_id"] for d in destinations]
    categories = [d["category"] for d in destinations]
    diagnostic_config = path / "visual_review_config.json"
    if not diagnostic_config.exists():
        diagnostic_config = path / "dwell_diagnostic_config.json"
    source_hashes = (json.loads(diagnostic_config.read_text(encoding="utf8")).get("source_sha256")
                     if diagnostic_config.exists() else None)
    if source_hashes is None:
        warnings.append("No driving source hashes available in this run; code identity cannot be checked.")
    incomplete_details = [dict(vehicle_id=t["vehicle_id"], trip_id=t["trip_id"], status=t["status"],
                               elapsed_time_s=number(t["travel_time_s"]), destination_id=t["destination_id"],
                               reason=t.get("termination_reason", "legacy_not_recorded")) for t in incomplete]
    vehicle_events = Counter((e["vehicle_id"], e["event_type"]) for e in events)
    return dict(
        analysis_version=1, run=config["run_id"], source_directory=str(path.resolve()),
        scenario=config["scenario"], seed=config["seed"], vehicle_count=config["vehicle_count"],
        map=config["map"], simulation_duration_s=number(summary["simulation_duration_s"]),
        metrics_semantics_version=schema, statuses=dict(statuses), started=len(trips), completed=len(completed),
        incomplete_count=len(incomplete), incomplete_fraction=ratio(len(incomplete), len(trips)),
        incomplete_trips=incomplete_details,
        destinations=dict(
            assigned=dict(by_id=distribution(trips, "destination_id", destination_ids),
                          by_category=distribution(trips, "destination_category", categories)),
            reached=dict(by_id=distribution(completed, "destination_id", destination_ids),
                         by_category=distribution(completed, "destination_category", categories))),
        travel_time=dict(population="completed_trips_only_including_stops", count=len(times),
                         mean_s=statistics.mean(times) if times else None,
                         median_s=statistics.median(times) if times else None,
                         sample_stddev_s=statistics.stdev(times) if len(times) > 1 else None,
                         min_s=min(times) if times else None, max_s=max(times) if times else None),
        exposure=dict(scope=scope, distance_m=distance, vehicle_time_s=exposure_s),
        speed=dict(scope=scope, mean_kmh=ratio(3.6 * distance, exposure_s)),
        events={kind: dict(observed_callbacks=observed[kind], callbacks_in_rate=rate_events[kind],
                           unassigned_callbacks=observed[kind] - assigned[kind],
                           per_vehicle_km=ratio(rate_events[kind], distance/1000),
                           per_vehicle_hour=ratio(rate_events[kind], exposure_s/3600))
                for kind in ["collision", "lane_invasion"]},
        event_breakdown=[dict(vehicle_id=v, event_type=k, callbacks=n) for (v, k), n in sorted(vehicle_events.items())],
        comparability=dict(carla_version=config.get("carla_version"), source_sha256=source_hashes,
                           environment=config.get("environment"),
                           vehicles=[{k: v.get(k) for k in ["vehicle_id", "blueprint_id", "actor_attributes",
                                                          "initial_spawn_location_used", "actor_seed", "destination_seed"]}
                                     for v in config.get("vehicles", [])],
                           arrival_policy_version=config.get("arrival_policy_version"),
                           arrival_control=config.get("arrival_control"),
                           route_planning=config.get("route_planning"),
                           trip_time_policy=config.get("trip_time_policy", dict(max_trip_time_seconds=config.get("simulation_config", {}).get("max_trip_time_seconds"))),
                           simulation_config={k: v for k, v in config.get("simulation_config", {}).items()
                                              if k not in ["destination_selection_mode", "vehicle_history_config", "output_root"]}),
        integrity_errors=errors, warnings=warnings,
    )


def paired_checks(runs):
    """Pair treatments only inside matching seed/flota/duration groups."""
    groups = defaultdict(list)
    for run in runs:
        groups[(run["map"], run["seed"], run["vehicle_count"], round(run["simulation_duration_s"], 1))].append(run)
    result = []
    for group, members in sorted(groups.items()):
        baseline = [r for r in members if r["scenario"] == "random_baseline"]
        history = [r for r in members if r["scenario"] == "history_80_20"]
        if len(baseline) != 1 or len(history) != 1:
            result.append(dict(group=group, comparable=False, differences=["missing or ambiguous treatment pair"], runs=[r["run"] for r in members]))
            continue
        a, b = baseline[0], history[0]
        differences = [k for k in a["comparability"] if a["comparability"][k] != b["comparability"][k]]
        if a["exposure"]["scope"] != b["exposure"]["scope"]:
            differences.append("exposure_scope")
        if a["integrity_errors"] or b["integrity_errors"]:
            differences.append("integrity_errors")
        result.append(dict(group=group, comparable=not differences, differences=differences, runs=[a["run"], b["run"]]))
    return result
