"""Prepare 20/100 nested inputs; inspect Town01 without spawning or ticking."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_pilots import nested_spawns, write_new_or_identical
from src.demand.destinations import load_destinations
from src.simulation.trip_runner import TripSimulationConfig
from src.demand.vehicle_history import VehicleHistory, generate_dummy_events, write_history_csv
from src.project_paths import project_path

CONFIG_DIR = Path('config/experiments/demand_20_100')
# Keep original serialized paths so the prepared inputs/manifests stay identical.
MANIFEST_CONFIG_DIR = Path('config/demand_20_100')
HISTORY_PATH = Path('data/input/Town01/demand_20_100/vehicle_history_100.csv')


def prepare(carla_map, weather, root=ROOT):
    if carla_map.name.replace('\\', '/').split('/')[-1] != 'Town01':
        raise ValueError('Se requiere Town01; no se cambia el mapa.')
    base_path = project_path('config/pilots/town01_20.json', root)
    base = json.loads(base_path.read_text(encoding='utf8'))
    points, details, signatures = {}, {}, set()
    for index, transform in enumerate(carla_map.get_spawn_points()):
        waypoint = carla_map.get_waypoint(transform.location)
        if waypoint is None or waypoint.is_junction or str(waypoint.lane_type) != 'Driving':
            continue
        signature = (waypoint.road_id, waypoint.lane_id, round(waypoint.s, 2))
        if signature in signatures:
            continue
        signatures.add(signature)
        location = waypoint.transform.location
        points[index] = (location.x, location.y)
        details[index] = dict(index=index, x=location.x, y=location.y, z=location.z,
                              yaw=waypoint.transform.rotation.yaw, road_id=waypoint.road_id,
                              lane_id=waypoint.lane_id)
    chosen = nested_spawns(points, base['initial_spawn_point_indices'], 100)
    minimum = min(math.hypot(points[i][0]-points[j][0], points[i][1]-points[j][1])
                  for k, i in enumerate(chosen) for j in chosen[k+1:])
    if minimum < 15:
        raise ValueError('Separacion entre centros menor que 15 m; revisar geometria.')
    destinations = load_destinations(project_path(base['destinations_config'], root), 'Town01')
    allowed = {d.destination_id for d in destinations}
    ids = ['vehicle_%03d' % n for n in range(1, 101)]
    events = generate_dummy_events(destinations, ids, 30, base['routine_destination_count'],
                                   base['routine_probability'], 42)
    for vehicle in ids[:20]:
        previous = VehicleHistory.from_csv(project_path(base['vehicle_history_config'], root), vehicle, allowed)
        if previous.events != [event for event in events if event.vehicle_id == vehicle]:
            raise ValueError('El historial de los primeros veinte no coincide: '+vehicle)
    history_path = project_path(HISTORY_PATH, root)
    if history_path.exists():
        previous = [e for vehicle in ids for e in VehicleHistory.from_csv(history_path, vehicle, allowed).events]
        if previous != events:
            raise ValueError('Se rechaza sobrescribir un historial distinto.')
    else:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        write_history_csv(history_path, events)
    configs = []
    for count in (20, 100):
        name = MANIFEST_CONFIG_DIR/('town01_%03d.json' % count)
        history = base['vehicle_history_config'] if count == 20 else HISTORY_PATH.as_posix()
        config = dict(base, seed=210, duration_seconds=1800., vehicle_count=count,
                      initial_spawn_point_indices=chosen[:count], vehicle_history_config=history)
        config_path = project_path(name, root)
        write_new_or_identical(config_path, json.dumps(config, indent=2)+'\n', root)
        TripSimulationConfig.from_json(config_path)
        configs.append(name.as_posix())
    write_new_or_identical(root/CONFIG_DIR/'weather.json', json.dumps(weather, indent=2, sort_keys=True)+'\n', root)
    manifest = dict(map=carla_map.name, configurations=configs, counts=[20,100],
                    xodr_sha256=hashlib.sha256(carla_map.to_opendrive().encode('utf8')).hexdigest(),
                    min_center_distance_m=minimum, ordered_spawns=[details[i] for i in chosen],
                    bootstrap_seed=42, run_seed_default=210, initial_visits_per_vehicle=30,
                    history_rows_100=len(events), prefix_20_preserved=True,
                    selection='Preserve first 20; extend over all unique driving/nonjunction map spawns by deterministic max-min XY distance. Geometric screening, not capacity or spawn-success proof.')
    names = configs+[HISTORY_PATH.as_posix(), base['vehicle_history_config'], base['destinations_config'], (MANIFEST_CONFIG_DIR/'weather.json').as_posix()]
    manifest['input_sha256'] = {n:hashlib.sha256(project_path(n, root).read_bytes()).hexdigest() for n in names}
    write_new_or_identical(root/CONFIG_DIR/'preparation_manifest.json', json.dumps(manifest, indent=2)+'\n', root)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weather-from', type=Path, required=True, help='Previous run_config.json whose weather is preserved.')
    args = parser.parse_args()
    import carla
    client = carla.Client('localhost', 2000)
    client.set_timeout(10)
    world = client.get_world()
    weather = json.loads(args.weather_from.read_text(encoding='utf8'))['environment']['weather']
    result = prepare(world.get_map(), weather)
    print('Prepared:', result['configurations'], 'history rows:', result['history_rows_100'],
          'minimum center separation:', result['min_center_distance_m'])


if __name__ == '__main__':
    main()
