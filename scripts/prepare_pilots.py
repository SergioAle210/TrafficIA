"""Prepare nested Town01 pilot fleets and bootstrap histories without spawning actors."""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.destinations import load_destinations
from src.trip_runner import TripSimulationConfig
from src.vehicle_history import VehicleHistory, generate_dummy_events, write_history_csv

COUNTS = (5, 10, 20)


def nested_spawns(points, prefix, count):
    """Extend fixed spawns by max-min center distance; ties use the lower index."""
    if not prefix or len(set(prefix)) != len(prefix) or any(i not in points for i in prefix):
        raise ValueError('Invalid fixed spawn prefix')
    if not len(prefix) <= count <= len(points):
        raise ValueError('Insufficient valid spawn candidates')
    chosen = list(prefix)
    while len(chosen) < count:
        candidates = [i for i in sorted(points) if i not in chosen]
        selected = max(candidates, key=lambda i: (
            min(math.hypot(points[i][0]-points[j][0], points[i][1]-points[j][1]) for j in chosen), -i))
        chosen.append(selected)
    return chosen


def write_new_or_identical(path, text):
    if path.exists():
        if path.read_text(encoding='utf8') != text:
            raise ValueError('Refusing to replace different existing pilot input: '+str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf8')


def prepare(carla_map, root=ROOT):
    if carla_map.name.replace('\\','/').split('/')[-1] != 'Town01':
        raise ValueError('Prepare requires Town01; the script never changes maps')
    base_path = root/'config/multi_vehicle_trip.json'
    base = json.loads(base_path.read_text(encoding='utf8'))
    destinations = load_destinations(root/base['destinations_config'], 'Town01')
    spawn_points = carla_map.get_spawn_points()
    points, details = {}, {}
    for destination in destinations:
        index = destination.spawn_point_index
        if index is None or index >= len(spawn_points):
            continue
        wp = carla_map.get_waypoint(spawn_points[index].location)
        if wp is None or wp.is_junction or str(wp.lane_type) != 'Driving':
            continue
        loc = wp.transform.location
        points[index] = (loc.x, loc.y)
        details[index] = dict(spawn_index=index, destination_id=destination.destination_id,
                              x=loc.x, y=loc.y, z=loc.z, yaw_deg=wp.transform.rotation.yaw,
                              road_id=wp.road_id, lane_id=wp.lane_id, lane_width_m=wp.lane_width)
    chosen = nested_spawns(points, base['initial_spawn_point_indices'], max(COUNTS))
    ids = ['vehicle_%03d' % i for i in range(1, max(COUNTS)+1)]
    events = generate_dummy_events(destinations, ids, 30, base['routine_destination_count'],
                                   base['routine_probability'], base['seed'])
    allowed = {d.destination_id for d in destinations}
    # Preserve the five existing personal histories, not just the first three.
    for v in ids[:5]:
        old = VehicleHistory.from_csv(root/base['vehicle_history_config'], v, allowed).events
        if old != [e for e in events if e.vehicle_id == v]:
            raise ValueError('Generated prefix differs from existing history: '+v)
    manifest = dict(map=carla_map.name, seed=base['seed'], counts=list(COUNTS),
        selection='Preserve [133,6,101]; extend among catalog driving/nonjunction spawns by max-min XY center distance, lower-index ties. Spatial dispersion is not a network-capacity estimate.',
        history='30 synthetic visits per vehicle, shared existing generator; nested identical prefixes; first five unchanged.',
        base_config_sha256=hashlib.sha256(base_path.read_bytes()).hexdigest(),
        destinations_sha256=hashlib.sha256((root/base['destinations_config']).read_bytes()).hexdigest(),
        original_history_sha256=hashlib.sha256((root/base['vehicle_history_config']).read_bytes()).hexdigest(),
        xodr_sha256=hashlib.sha256(carla_map.to_opendrive().encode('utf8')).hexdigest(),
        ordered_spawns=[details[i] for i in chosen], fleets=[])
    for count in COUNTS:
        config_name = 'config/pilots/town01_%02d.json' % count
        history_name = 'data/input/Town01/pilots/vehicle_history_%02d.csv' % count
        selected_events = [e for e in events if e.vehicle_id in ids[:count]]
        history_path = root/history_name
        if history_path.exists():
            existing = [e for v in ids[:count] for e in VehicleHistory.from_csv(history_path,v,allowed).events]
            if existing != selected_events:
                raise ValueError('Existing pilot history differs: '+history_name)
        else:
            write_history_csv(history_path, selected_events)
        config = dict(base, vehicle_count=count, initial_spawn_point_indices=chosen[:count],
                      vehicle_history_config=history_name)
        write_new_or_identical(root/config_name, json.dumps(config,indent=2)+'\n')
        TripSimulationConfig.from_json(root/config_name)
        minimum = min(math.hypot(points[i][0]-points[j][0],points[i][1]-points[j][1])
                      for n,i in enumerate(chosen[:count]) for j in chosen[:count][n+1:])
        if minimum < 15:
            raise ValueError('Pilot spawn centers less than 15 m apart')
        manifest['fleets'].append(dict(vehicles=count, config=config_name, history=history_name,
             history_rows=len(selected_events), min_spawn_center_distance_m=minimum,
             config_sha256=hashlib.sha256((root/config_name).read_bytes()).hexdigest(),
             history_sha256=hashlib.sha256(history_path.read_bytes()).hexdigest()))
    write_new_or_identical(root/'config/pilots/preparation_manifest.json',json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    import carla
    client = carla.Client('localhost',2000)
    client.set_timeout(10)
    result = prepare(client.get_world().get_map())
    print(json.dumps(result,indent=2))
