"""Validate preserved campaign files and derive descriptive incident groups offline."""
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.analysis.incident_analysis import collision_episodes
from src.analysis.mobility_analysis import analyze_run, paired_checks


def read(path):
    """Read a JSON file into Python data."""
    return json.loads(path.read_text(encoding='utf8'))
def rows(path):
    """Read a CSV file as rows keyed by column name."""
    with path.open(encoding='utf8',newline='') as stream:return list(csv.DictReader(stream))
def digest(path):
    """Calculate a file's SHA-256 fingerprint by reading it in blocks."""
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    """Recheck campaign logs and write an integrity report for the data used in charts."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();plan=read(args.campaign);folder=args.campaign.parent
    if plan['status']!='completed' or any(c['status']!='completed' for c in plan['cases']):
        raise ValueError('Incomplete campaign')
    errors=[];verified=0;metrics=[];reviews=[];episodes=[]
    for relative,expected in read(folder/'source_sha256.json').items():
        if digest(folder/'source_snapshot'/relative)!=expected:errors.append('snapshot: '+relative)
    for case in plan['cases']:
        run=ROOT/'data/output'/case['run'];label='n%03d_%s'%(case['vehicle_count'],case['scenario'])
        for relative,expected in read(folder/(label+'_output_sha256.json')).items():
            if digest(run/relative)!=expected:errors.append(run.name+'/'+relative)
            verified+=1
        audit=read(folder/(label+'_audit.json'))
        errors.extend(audit['integrity_errors'])
        metric=analyze_run(run);metrics.append(metric);errors.extend(metric['integrity_errors'])
        trips=rows(run/'trips_log.csv');events=rows(run/'events_log.csv');conf=read(run/'run_config.json')
        origin=min(float(t['departure_sim_time_s']) for t in trips)
        actors={v['vehicle_id']:v['carla_actor_id'] for v in conf['vehicles']}
        grouped=collision_episodes(events,actors,origin)
        for item in grouped:item['run']=run.name
        episodes.extend(grouped)
        raw=metric['events']['collision']['observed_callbacks']
        if sum(e['raw_callbacks'] for e in grouped)!=raw:errors.append('episode callback mismatch')
        history=rows(run/'vehicle_history.csv')
        initial=sum(not h['trip_id'] for h in history)
        reached=sum(bool(h['trip_id']) for h in history)
        if reached!=metric['completed']:errors.append('history arrival mismatch')
        reviews.append(dict(run=run.name,vehicle_count=conf['vehicle_count'],scenario=conf['scenario'],
            origin_s=origin,episodes=len(grouped),raw_callbacks=raw,initial_history=initial,
            final_history=len(history),selection_counts=dict(Counter(t['selection_class'] for t in trips)),
            termination_reasons=dict(Counter(t['termination_reason'] for t in trips)),
            event_types=dict(Counter(e['details'].split('other_actor_type=')[-1] for e in events if e['event_type']=='collision')),
            observations=audit['observations'],wall_seconds=case['wall_seconds_process'],
            real_time_factor=case['achieved_process_ratio']))
        print('VERIFIED',conf['vehicle_count'],conf['scenario'],metric['statuses'],'episodes',len(grouped),flush=True)
    pairs=paired_checks(metrics)
    if any(not p['comparable'] for p in pairs):errors.append('noncomparable pair')
    result=dict(campaign=str(args.campaign.resolve()),verified_output_files=verified,errors=errors,pairs=pairs,
                runs=reviews,metrics=metrics,episodes=episodes,episode_method='Unordered actor pair, max consecutive gap 1 simulated s; all callbacks retained. Descriptive groups, not verified accidents.')
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'chart_input_review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf8')
    if errors:raise ValueError(str(errors))


if __name__=='__main__':main()
