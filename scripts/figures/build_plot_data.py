"""Derive offline chart data from an audited campaign; never connect to CARLA server."""
import argparse
import hashlib
import json
import math
import sys
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import carla

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.analysis.traffic_flow_analysis import split_space_time_interval,edie_metrics


def json_read(p):
    """Read a JSON file into Python data."""
    return json.loads(p.read_text(encoding='utf8'))


def file_sha256(path):
    """Calculate a file's SHA-256 fingerprint by reading it in blocks."""
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def observation_rows(path,chunk_size=100000):
    """Yield selected observation columns in chunks to limit memory use."""
    fields=['vehicle_id','frame','simulation_time_s','x','y','z','low_speed','phase_before']
    for chunk in pd.read_csv(path,usecols=fields,chunksize=chunk_size):
        yield from chunk[fields].itertuples(index=False,name=None)


def eligible_lanes(xodr):
    """Find straight driving lanes outside junctions that meet the flow-analysis geometry requirements."""
    result={}
    for road in ET.fromstring(xodr).findall('road'):
        length=float(road.get('length'))
        if road.get('junction')!='-1' or length<50:continue
        if not all(g.find('line') is not None for g in road.findall('planView/geometry')):continue
        sections=road.findall('lanes/laneSection')
        if len(sections)!=1:continue
        offsets=road.findall('lanes/laneOffset')
        if any(any(abs(float(o.get(k,'0')))>1e-8 for k in ('b','c','d')) for o in offsets):continue
        for side in ('left','right'):
            for lane in sections[0].findall(side+'/lane'):
                if lane.get('type')!='driving':continue
                widths=lane.findall('width')
                if not widths or any(any(abs(float(w.get(k,'0')))>1e-8 for k in ('b','c','d')) for w in widths):continue
                result[int(road.get('id')),int(lane.get('id'))]=length
    return result


def main():
    """Build time-series and lane-flow data from a completed campaign and record their source fingerprints."""
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--xodr',type=Path,default=Path(r'C:\CARLA\WindowsNoEditor\CarlaUE4\Content\Carla\Maps\OpenDrive\Town01.xodr'))
    a=p.parse_args();plan=json_read(a.campaign)
    if plan['status']!='completed' or any(c['status']!='completed' for c in plan['cases']):
        raise ValueError('Campaign is incomplete')
    a.output.mkdir(parents=True,exist_ok=False)
    xodr=a.xodr.read_text(encoding='utf8');road_map=carla.Map('Town01-chart-analysis',xodr)
    eligible=eligible_lanes(xodr);geometry=[]
    for (road,lane),length in sorted(eligible.items()):
        for section in range(int(length//50)):
            coords=[]
            for s in np.linspace(section*50+.001,(section+1)*50-.001,26):
                wp=road_map.get_waypoint_xodr(road,lane,float(s))
                if wp is None:raise ValueError('Selected lane has incomplete map coverage')
                coords.append([wp.transform.location.x,wp.transform.location.y])
            geometry.append(dict(road_id=road,lane_id=lane,section=section,s0_m=section*50,s1_m=(section+1)*50,xy=coords))
    background=[[w.transform.location.x,w.transform.location.y] for w in road_map.generate_waypoints(2)]
    manifest=dict(campaign=str(a.campaign.resolve()),section_length_m=50,time_window_s=60,
                  xodr_path=str(a.xodr),xodr_sha256=hashlib.sha256(a.xodr.read_bytes()).hexdigest(),
                  selected_geometry=geometry,background_xy=background,runs=[],sources={},
                  method='Offline OpenDRIVE projection with project_to_road=False; straight nonjunction lanes of constant width; 50m complete sections. Linear interpolation of station and time inside each 0.05s interval. Road/lane transitions excluded and quantified. Absolute longitudinal distance; reverse displacements reported. Last time window uses actual duration. Empty-cell speed undefined. No stationary-state filtering or curve fitting.')
    all_cells=[];all_series=[]
    for case in plan['cases']:
        wall=time.monotonic();run=ROOT/'data/output'/case['run'];print('READ',run.name,flush=True)
        conf=json_read(run/'run_config.json')
        first=None;last=None;row_count=0
        trips=pd.read_csv(run/'trips_log.csv');start=float(trips.departure_sim_time_s.min())
        previous={};cells=defaultdict(lambda:[0.,0.]);series=defaultdict(lambda:[0.,0.,0.,0.])
        transitions_s=0.;outside_map=0;reverse_m=0.;eligible_distance=0.;missing_intervals=0
        for vehicle,frame,t,x,y,z,low,phase in observation_rows(run/'observation_log.csv'):
            if first is None:first=t
            last=t;row_count+=1
            wp=road_map.get_waypoint(carla.Location(x=x,y=y,z=z),project_to_road=False,lane_type=carla.LaneType.Driving)
            key=(wp.road_id,wp.lane_id) if wp is not None else None
            s=wp.s if wp is not None else None
            if wp is None:outside_map+=1
            prev=previous.get(vehicle);previous[vehicle]=(frame,t,x,y,z,key,s)
            if prev is None:continue
            pf,pt,px,py,pz,pk,ps=prev;dt=t-pt
            if frame-pf!=1 or abs(dt-.05)>1e-5:missing_intervals+=1;continue
            t0=pt-first;t1=t-first;bin_=int(((t0+t1)/2)//60)
            distance=math.sqrt((x-px)**2+(y-py)**2+(z-pz)**2)
            bucket=series[bin_];bucket[0]+=dt;bucket[1]+=distance
            bucket[2]+=dt*bool(low);bucket[3]+=dt*(phase=='dwell')
            if key!=pk:
                if key in eligible or pk in eligible:transitions_s+=dt
                continue
            if key not in eligible:continue
            forward=(s-ps)*(-1 if key[1]>0 else 1)
            if forward<0:reverse_m+=abs(forward)
            eligible_distance+=abs(s-ps)
            for section,window,seconds,metres in split_space_time_interval(ps,s,t0,t1,eligible[key]):
                bucket=cells[key[0],key[1],section,window];bucket[0]+=seconds;bucket[1]+=metres
        if missing_intervals:raise ValueError('Observation gaps: '+str(missing_intervals))
        if first is None or last<=first:raise ValueError('Insufficient observations')
        horizon=last-first
        nonempty=0;max_identity_error=0
        for g in geometry:
            for window in range(math.ceil(horizon/60)):
                duration=min(60,horizon-window*60)
                seconds,metres=cells[g['road_id'],g['lane_id'],g['section'],window]
                k,q,v=edie_metrics(seconds,metres,50,duration)
                if v is not None:nonempty+=1;max_identity_error=max(max_identity_error,abs(q-k*v))
                all_cells.append(dict(run=run.name,seed=conf['seed'],scenario=conf['scenario'],vehicle_count=conf['vehicle_count'],road_id=g['road_id'],lane_id=g['lane_id'],section=g['section'],
                                      start_elapsed_s=first-start+window*60,duration_s=duration,vehicle_seconds=seconds,longitudinal_distance_m=metres,
                                      density_veh_per_km_lane=k,flow_veh_per_h_lane=q,speed_kmh=v))
        for window,(seconds,metres,low_s,dwell_s) in sorted(series.items()):
            all_series.append(dict(run=run.name,seed=conf['seed'],scenario=conf['scenario'],vehicle_count=conf['vehicle_count'],start_elapsed_s=first-start+60*window,
                                   duration_s=min(60,horizon-window*60),vehicle_seconds=seconds,distance_m=metres,
                                   speed_kmh=3.6*metres/seconds,low_speed_percent=100*low_s/seconds,dwell_percent=100*dwell_s/seconds))
        reference=pd.read_csv(run/'metrics_summary.csv').iloc[0]
        summary=dict(run=run.name,seed=conf['seed'],scenario=conf['scenario'],vehicle_count=conf['vehicle_count'],rows=row_count,observed_start_elapsed_s=first-start,
                     observed_duration_s=horizon,nonempty_cells=nonempty,total_cells=len(geometry)*math.ceil(horizon/60),
                     selected_vehicle_seconds=sum(v[0] for v in cells.values()),selected_distance_m=sum(v[1] for v in cells.values()),
                     uncertain_transition_vehicle_seconds_upper_bound=transitions_s,outside_driving_projection_rows=outside_map,
                     reverse_longitudinal_distance_m=reverse_m,eligible_longitudinal_distance_m=eligible_distance,
                     q_minus_kv_max=max_identity_error,series_vehicle_seconds=sum(v[0] for v in series.values()),
                     series_distance_m=sum(v[1] for v in series.values()),reference_distance_m=float(reference.total_observed_distance_m),
                     initial_unobserved_vehicle_seconds=float(reference.total_vehicle_time_s)-sum(v[0] for v in series.values()))
        if max_identity_error>1e-8:raise ValueError('q=k*v failed')
        manifest['runs'].append(summary)
        for name in ('run_config.json','observation_log.csv','trips_log.csv','events_log.csv','vehicle_history.csv','metrics_summary.csv'):
            path=run/name;manifest['sources'][str(path.relative_to(ROOT))]=file_sha256(path)
        print('DONE',conf['seed'],conf['scenario'],'cells',nonempty,'wall_s',round(time.monotonic()-wall,1),flush=True)
    pd.DataFrame(all_cells).to_csv(a.output/'flow_cells.csv',index=False)
    pd.DataFrame(all_series).to_csv(a.output/'time_series.csv',index=False)
    manifest['analysis_source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('src/analysis/traffic_flow_analysis.py','scripts/figures/build_plot_data.py')}
    (a.output/'derivation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('OUTPUT',a.output.resolve(),flush=True)


if __name__=='__main__':main()
