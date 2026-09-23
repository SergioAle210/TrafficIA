"""Check complete phase/frame logs with memory proportional to vehicles/trips."""
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.mobility_analysis import analyze_run, read_csv


def audit_stream(run, metrics=None):
    run = Path(run)
    metrics = metrics if metrics is not None else analyze_run(run)
    config = json.loads((run/'run_config.json').read_text(encoding='utf8'))
    capture = json.loads((run/'capture_summary.json').read_text(encoding='utf8'))
    dt = config['simulation_config']['fixed_delta_seconds']
    expected_count = round(metrics['simulation_duration_s']/dt)
    ids = {'vehicle_%03d' % n for n in range(1, config['vehicle_count']+1)}
    trips = {(r['vehicle_id'], r['trip_id']) for r in read_csv(run/'trips_log.csv')}
    arrival_path = run/'arrival_log.csv'
    # The runner creates this log on the first arrival, not at startup.
    arrival_rows = read_csv(arrival_path) if arrival_path.exists() else []
    arrivals = {(r['vehicle_id'], int(r['frame'])):r for r in arrival_rows}
    counts, errors, states = Counter(), Counter(), {}
    matched = set()
    def check(condition, message):
        if not condition:
            errors[message] += 1
    check(len(arrival_rows)==metrics['completed'], 'arrival_completed_count_mismatch')
    check(len(arrivals)==len(arrival_rows), 'duplicate_arrival_frame')
    with (run/'observation_log.csv').open(encoding='utf8', newline='') as stream:
        for row in csv.DictReader(stream):
            vehicle = row['vehicle_id']
            check(vehicle in ids, 'unknown_vehicle')
            if vehicle not in ids:
                continue
            frame, now = int(row['frame']), float(row['simulation_time_s'])
            numeric = [float(row[k]) for k in ('x','y','z','speed_mps','yaw_deg')]
            check(all(math.isfinite(v) for v in numeric+[now]), 'nonfinite_observation')
            previous = states.get(vehicle)
            if previous is None:
                states[vehicle] = previous = dict(first_frame=frame, first_time=now, frame=frame-1,
                                                  time=now-dt, low_ticks=0, stop_ticks=0, max_stop_ticks=0)
            check(frame == previous['frame']+1, vehicle+': nonconsecutive_frames')
            check(abs(now-previous['time']-dt) < 1e-6, vehicle+': discontinuous_time')
            for key in ('phase_before', 'phase_after'):
                check(row[key] in ('travel','dwell'), 'invalid_phase')
            for key in ('trip_before','trip_after','context_trip_id'):
                check(not row[key] or (vehicle,row[key]) in trips, 'unknown_trip')
            arrival = arrivals.get((vehicle,frame))
            if arrival:
                matched.add((vehicle,frame))
                check(row['phase_before']=='travel' and row['phase_after']=='dwell'
                      and row['context_trip_id']==arrival['trip_id'], 'arrival_transition_mismatch')
            low = row['low_speed']=='True'
            check(row['low_speed'] in ('True','False'), 'invalid_low_speed_flag')
            previous['low_ticks'] += int(low)
            previous['stop_ticks'] = previous['stop_ticks']+1 if low else 0
            previous['max_stop_ticks'] = max(previous['max_stop_ticks'], previous['stop_ticks'])
            previous.update(frame=frame, time=now)
            counts[vehicle] += 1
    check(set(counts)==ids, 'missing_vehicles')
    for vehicle in ids:
        check(counts[vehicle]==expected_count, vehicle+': observation_count')
    check(dict(counts)==capture['observation_rows_by_vehicle'], 'capture_counts_differ')
    check(capture['simulation_completed'], 'simulation_incomplete')
    check(matched==set(arrivals), 'arrival_frame_missing')
    check(len({(s['first_frame'],s['frame']) for s in states.values()})==1, 'different_vehicle_frame_ranges')
    check(len({(s['first_time'],s['time']) for s in states.values()})==1, 'different_vehicle_time_ranges')
    return dict(schema_version=1, audit_scope='Streaming frame/time/phase/trip/arrival consistency plus mobility metrics. No image, lane geometry or queue-cause verification.',
                run=run.name, observations=sum(counts.values()), observations_by_vehicle=dict(counts),
                matched_arrivals=len(matched), vehicle_summary={v:dict(low_speed_seconds=s['low_ticks']*dt,
                    longest_low_speed_seconds=s['max_stop_ticks']*dt) for v,s in states.items()},
                integrity_errors=list(metrics['integrity_errors'])+list(errors), error_counts=dict(errors))
