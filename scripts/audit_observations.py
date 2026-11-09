"""Audit complete runs with phase/stop context; no visual-coverage claim."""
import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analysis.mobility_analysis import analyze_run
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data/output/.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    with path.open(encoding='utf8', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--minimum-cycles', type=int, default=0,
                        help='Optional coverage requirement; absent arrivals alone are not corrupt logs.')
    parser.add_argument('--xodr', type=Path,
                        default=Path(r'C:\CARLA\WindowsNoEditor\CarlaUE4\Content\Carla\Maps\OpenDrive\Town01.xodr'))
    args=parser.parse_args(); run,out=args.run,args.output
    out.mkdir(parents=True, exist_ok=False)
    analysis=analyze_run(run)
    config=json.loads((run/'run_config.json').read_text(encoding='utf8'))
    meta=json.loads((run/'visual_review_config.json').read_text(encoding='utf8'))
    capture=json.loads((run/'capture_summary.json').read_text(encoding='utf8'))
    observations=read(run/'observation_log.csv'); trips=read(run/'trips_log.csv')
    arrivals=read(run/'arrival_log.csv') if (run/'arrival_log.csv').exists() else []
    events=read(run/'events_log.csv')
    dt=float(config['simulation_config']['fixed_delta_seconds'])
    start=min(float(t['departure_sim_time_s']) for t in trips)
    by_vehicle=defaultdict(list)
    for row in observations: by_vehicle[row['vehicle_id']].append(row)
    errors=list(analysis['integrity_errors'])
    def check(condition, message):
        if not condition: errors.append(message)
    check(len(arrivals)==analysis['completed'],'arrival log missing or count differs')
    hashes={group:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value
                   for name,value in meta[group].items()} for group in ('source_sha256','input_sha256')}
    warnings=[]
    if not all(all(group.values()) for group in hashes.values()):
        warnings.append('Current source/input differs from recorded hashes; use the run snapshot for reproduction.')
    check(capture['simulation_completed'], 'capture not finalized as complete')
    expected=round(analysis['simulation_duration_s']/dt)
    stops=[]; vehicles=[]; cycles=[]
    frame_sets=[]
    for vehicle, rows in sorted(by_vehicle.items()):
        frames=[int(r['frame']) for r in rows]; frame_sets.append(set(frames))
        check(len(rows)==expected, vehicle+': incorrect observation count')
        check(all(b-a==1 for a,b in zip(frames,frames[1:])),vehicle+': nonconsecutive observation frames')
        check(all(abs(float(b['simulation_time_s'])-float(a['simulation_time_s'])-dt)<1e-6
                  for a,b in zip(rows,rows[1:])),vehicle+': time discontinuity')
        keys={t['trip_id'] for t in trips if t['vehicle_id']==vehicle}
        check(all(r['phase_before'] in ('travel','dwell') and r['phase_after'] in ('travel','dwell') for r in rows),vehicle+': unknown phase')
        check(all(not r['context_trip_id'] or r['context_trip_id'] in keys for r in rows),vehicle+': unknown observation trip')
        index={r['frame']:r for r in rows}
        for arrival in [a for a in arrivals if a['vehicle_id']==vehicle]:
            t=float(arrival['simulation_time_s']); row=index.get(arrival['frame'])
            check(row is not None and row['phase_before']=='travel' and row['phase_after']=='dwell'
                  and row['context_trip_id']==arrival['trip_id'],vehicle+': arrival transition mismatch')
            following=sorted([trip for trip in trips if trip['vehicle_id']==vehicle and float(trip['departure_sim_time_s'])>t],key=lambda trip:float(trip['departure_sim_time_s']))
            nxt=following[0] if following else None
            depart=float(nxt['departure_sim_time_s']) if nxt else None
            dwell=[r for r in rows if float(r['simulation_time_s'])>t and (depart is None or float(r['simulation_time_s'])<=depart)]
            restart=[r for r in rows if nxt and r['trip_before']==nxt['trip_id']]
            covered=bool(dwell and restart)
            if depart:
                check(abs(depart-t-config['simulation_config']['destination_dwell_time_seconds'])<=dt+1e-5,vehicle+': dwell duration mismatch')
                check(all(r['phase_before']=='dwell' for r in dwell),vehicle+': dwell phase mismatch')
            cycles.append(dict(vehicle_id=vehicle,trip_id=arrival['trip_id'],arrival_s=t-start,
                next_trip=nxt['trip_id'] if nxt else None,dwell_s=depart-t if depart else None,
                dwell_max_speed_mps=max((float(r['speed_mps']) for r in dwell),default=None),
                dwell_displacement_m=(((float(dwell[-1]['x'])-float(dwell[0]['x']))**2+(float(dwell[-1]['y'])-float(dwell[0]['y']))**2)**.5) if dwell else None,
                recorded_complete_cycle=covered,visual_coverage=False))
        current=[]
        def finish_stop():
            if not current: return
            duration=float(current[-1]['simulation_time_s'])-float(current[0]['simulation_time_s'])+dt
            if duration<10: return
            near=[json.loads(r['nearby_vehicles_json']) for r in current]
            stops.append(dict(vehicle_id=vehicle,start_s=float(current[0]['simulation_time_s'])-start,
                end_s=float(current[-1]['simulation_time_s'])-start,duration_s=duration,
                position_start={k:float(current[0][k]) for k in ('x','y','yaw_deg')},
                phases=dict(Counter(r['phase_before'] for r in current)),
                traffic_light_states=dict(Counter(r['traffic_light_state'] or 'not_at_light' for r in current)),
                cached_agent_light_states=dict(Counter(r.get('agent_traffic_light_state','') or 'none' for r in current)),
                frames_with_nearby_vehicle=sum(bool(n) for n in near),
                min_nearby_center_distance_m=min((n['distance_m'] for group in near for n in group),default=None),
                nearby_vehicle_ids=sorted({n['vehicle_id'] for group in near for n in group}),frames=len(current)))
        for row in rows:
            if row['low_speed']=='True': current.append(row)
            else: finish_stop();current=[]
        finish_stop()
        vt=[t for t in trips if t['vehicle_id']==vehicle]
        vehicles.append(dict(vehicle_id=vehicle,observations=len(rows),statuses=dict(Counter(t['status'] for t in vt)),
            completed_cycles=sum(c['recorded_complete_cycle'] for c in cycles if c['vehicle_id']==vehicle),
            event_callbacks=dict(Counter(e['event_type'] for e in events if e['vehicle_id']==vehicle)),
            max_stop_s=max((s['duration_s'] for s in stops if s['vehicle_id']==vehicle),default=0),
            low_speed_fraction=sum(r['low_speed']=='True' for r in rows)/len(rows),
            low_speed_with_cached_red_s=dt*sum(r['low_speed']=='True' and r.get('agent_traffic_light_state')=='Red' for r in rows),
            low_speed_with_nearby_vehicle_s=dt*sum(r['low_speed']=='True' and bool(json.loads(r['nearby_vehicles_json'])) for r in rows)))
    check(len(frame_sets)==config['vehicle_count'] and all(s==frame_sets[0] for s in frame_sets),'vehicle frame sets differ')
    check(all(v['completed_cycles']>=args.minimum_cycles for v in vehicles),'missing full recorded arrival/dwell/restart cycle')
    check(all(t['termination_reason']=='simulation_end' for t in trips if t['status']=='aborted'),'unexpected abort reason')
    import carla
    xodr=args.xodr
    road_map=carla.Map('Town01-offline',xodr.read_text(encoding='utf8'))
    lanes=[]
    for a in arrivals:
        wp=road_map.get_waypoint(carla.Location(*(float(a[axis]) for axis in 'xyz')))
        valid=wp is not None and (wp.road_id,wp.lane_id)==(int(a['road_id']),int(a['lane_id']))
        check(valid,'arrival lane projection mismatch: '+a['vehicle_id']+'/'+a['trip_id'])
        lanes.append(dict(vehicle_id=a['vehicle_id'],trip_id=a['trip_id'],projected_lane_matches_log=valid))
    audit=dict(run=run.name,integrity_errors=errors,warnings=warnings,hashes_unchanged=hashes,vehicles=vehicles,
        minimum_cycles_required=args.minimum_cycles,
        arrival_lane_checks=lanes,xodr_sha256=hashlib.sha256(xodr.read_bytes()).hexdigest(),
        cycles=cycles,stops_10s_or_longer=stops,capture=capture,
        limitations=['This auditor reviews observations, not camera content; no visual validation claim.',
                     'Traffic-light and nearby-vehicle context does not prove the exclusive cause of a stop.',
                     'Speeds below 0.2 m/s define low-speed intervals; brief motion separates intervals.'])
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    (out/'metrics.json').write_text(json.dumps(analysis,indent=2),encoding='utf8')
    fig,axes=plt.subplots(len(by_vehicle),2,figsize=(14,3.5*len(by_vehicle)),squeeze=False)
    for i,(v,rows) in enumerate(sorted(by_vehicle.items())):
        sample=rows[::10]
        axes[i,0].plot([float(r['simulation_time_s'])-start for r in sample],[3.6*float(r['speed_mps']) for r in sample],lw=.8)
        for a in [a for a in arrivals if a['vehicle_id']==v]: axes[i,0].axvline(float(a['simulation_time_s'])-start,color='#2a9d8f',alpha=.7,lw=.8)
        axes[i,0].set(title=v+' · velocidad y llegadas (verde)',xlabel='Tiempo simulado (s)',ylabel='km/h',xlim=(0,analysis['simulation_duration_s']),ylim=(0,25))
        axes[i,1].plot([float(r['x']) for r in sample],[float(r['y']) for r in sample],lw=1)
        axes[i,1].scatter([float(a['x']) for a in arrivals if a['vehicle_id']==v],[float(a['y']) for a in arrivals if a['vehicle_id']==v],c='#2a9d8f',s=25,zorder=3)
        axes[i,1].set(title=v+' · trayectoria registrada',xlabel='x (m)',ylabel='y (m)');axes[i,1].set_aspect('equal');axes[i,1].invert_yaxis()
        for ax in axes[i]: ax.grid(alpha=.2)
    fig.suptitle('%s · %s vehículos · semilla %s · registros de observación' % (analysis['scenario'],len(by_vehicle),analysis['seed']))
    fig.tight_layout(rect=(0,0,1,.97));fig.savefig(out/'trajectories.png',dpi=140);plt.close(fig)
    print(json.dumps(dict(run=run.name,statuses=analysis['statuses'],errors=errors,vehicles=vehicles,stops=len(stops)),indent=2))
    if errors: raise SystemExit(1)


if __name__=='__main__': main()
