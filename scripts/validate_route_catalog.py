"""Check every directed catalogue pair on CARLA's map without spawning actors."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demand.destinations import load_destinations
from src.navigation.route_planner import (configure_carla_agents, build_global_route_planner, plan_route,
                               arrival_route, steering_continuation, validate_route_start, route_distance_m)
from src.simulation.trip_runner import resolve_destination_location


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--campaign-manifest", type=Path)
    parser.add_argument("--carla-pythonapi", default=r"C:\CARLA\WindowsNoEditor\PythonAPI\carla")
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    import carla
    client = carla.Client("localhost", 2000)
    client.set_timeout(15)
    world = client.get_world()
    carla_map = world.get_map()
    if not carla_map.name.endswith("/Town01"):
        raise RuntimeError("La validación requiere Town01.")
    configure_carla_agents(carla, args.carla_pythonapi)
    planner = build_global_route_planner(carla_map, 2)
    destinations = load_destinations(ROOT / "data/input/catalogs/Town01/destinations_config.csv", "Town01")
    goals = {d.destination_id: resolve_destination_location(carla, carla_map, d) for d in destinations}
    checks = []

    def check(origin_id, origin, destination_id, context):
        result = dict(origin=origin_id, destination=destination_id, context=context)
        try:
            destination = goals[destination_id]
            origin = carla_map.get_waypoint(origin).transform.location
            route = arrival_route(plan_route(planner, origin, destination), carla_map.get_waypoint(destination))
            validate_route_start(route, origin, 5)
            steering_continuation(route, 6)
            result.update(valid=True, points=len(route), distance_m=route_distance_m(route),
                          end_error_m=route[-1][0].transform.location.distance(destination))
        except (RuntimeError, ValueError) as error:
            result.update(valid=False, error=str(error))
        checks.append(result)

    for origin_id, origin in goals.items():
        for destination_id in goals:
            if destination_id != origin_id:
                check(origin_id, origin, destination_id, "catalogue")
    if args.campaign_manifest:
        manifest = json.loads(args.campaign_manifest.read_text(encoding="utf8"))
        for case in manifest["cases"]:
            run = ROOT / "data/output" / case["run_directories"][0]
            with (run / "trips_log.csv").open(encoding="utf8", newline="") as f:
                for trip in csv.DictReader(f):
                    if trip["status"] == "route_failed":
                        origin = carla.Location(*(float(trip["origin_" + axis]) for axis in "xyz"))
                        check(trip["origin_id"], origin, trip["destination_id"],
                              case["id"] + "/" + trip["vehicle_id"] + "/" + trip["trip_id"])
    failures = [c for c in checks if not c["valid"]]
    report = dict(map=carla_map.name, checks=len(checks), failures=len(failures), results=checks)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf8")
    print("Checked", len(checks), "Failures", len(failures))
    for failure in failures:
        print(failure)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
