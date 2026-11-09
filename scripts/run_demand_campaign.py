"""Run sequential paired 20/100 experiments; preserve partial outputs on failure."""
import argparse
import contextlib
import gc
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_observation_stream import audit_stream
from scripts.prepare_demand_campaign import CONFIG_DIR
from src.analysis.mobility_analysis import analyze_run
from src.simulation.trip_runner import TripSimulationConfig
from src.recording.visual_review import VisualReviewSimulation
from src.project_paths import project_path


def stamp():
    """Return the current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).isoformat()


def read(path):
    """Read project JSON data while resolving supported relocated input paths."""
    return json.loads(project_path(path, ROOT).read_text(encoding='utf8'))


def save(path, value):
    """Write JSON to a temporary file and replace the target after the write succeeds."""
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf8')
    temp.replace(path)


def digest(path):
    """Calculate a project's input-file fingerprint after resolving its current location."""
    result = hashlib.sha256()
    with project_path(path, ROOT).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def check_hashes(expected):
    """Reject missing or changed experiment inputs by comparing their recorded fingerprints."""
    changed = [name for name, value in expected.items() if not project_path(name, ROOT).is_file() or digest(ROOT/name)!=value]
    if changed:
        raise RuntimeError('Archivos congelados cambiaron: '+str(changed))


def preflight(world):
    """Check that CARLA has a clean asynchronous world and record its initial state."""
    settings, actors = world.get_settings(), world.get_actors()
    weather = world.get_weather()
    state = dict(at_utc=stamp(), map=world.get_map().name,
                 vehicles=len(actors.filter('vehicle.*')), sensors=len(actors.filter('sensor.*')),
                 walkers=len(actors.filter('walker.*')), synchronous=settings.synchronous_mode,
                 fixed_delta_seconds=settings.fixed_delta_seconds, no_rendering=settings.no_rendering_mode,
                 weather={n:getattr(weather,n) for n in dir(weather)
                          if not n.startswith('_') and isinstance(getattr(weather,n),(float,int))})
    if state['map'].replace('\\','/').split('/')[-1]!='Town01':
        raise RuntimeError('Se requiere Town01; el script no cambia mapas.')
    if state['vehicles'] or state['sensors'] or state['walkers'] or state['synchronous']:
        raise RuntimeError('Se requiere mundo limpio y asincrono. No se eliminan actores ajenos: '+str(state))
    return state


def validate_map(carla_map, manifest):
    """Check that the map and spawn geometry match the prepared campaign inputs."""
    if hashlib.sha256(carla_map.to_opendrive().encode('utf8')).hexdigest()!=manifest['xodr_sha256']:
        raise RuntimeError('OpenDRIVE distinto de la preparacion de entradas.')
    spawns = carla_map.get_spawn_points()
    for item in manifest['ordered_spawns']:
        if item['index']>=len(spawns):
            raise RuntimeError('Indice de spawn ausente.')
        wp = carla_map.get_waypoint(spawns[item['index']].location)
        if wp is None or wp.is_junction or str(wp.lane_type)!='Driving':
            raise RuntimeError('Spawn fuera del ambito preparado.')
        loc = wp.transform.location
        if wp.road_id!=item['road_id'] or wp.lane_id!=item['lane_id'] or math.hypot(loc.x-item['x'],loc.y-item['y'])>.1:
            raise RuntimeError('La geometria de un spawn difiere de la preparada.')


class Tee:
    def __init__(self, *streams):
        """Store the output streams that should receive the same console text."""
        self.streams = streams
    def write(self, text):
        """Write and flush the same text to every configured output stream."""
        for stream in self.streams:
            stream.write(text)
            stream.flush()
        return len(text)
    def flush(self):
        """Flush all configured output streams."""
        for stream in self.streams:
            stream.flush()


def parse_args(argv=None):
    """Read campaign options and validate the requested ascending vehicle counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=210)
    parser.add_argument('--seconds', type=float, default=1800)
    parser.add_argument('--simulation-speed', type=int, choices=(1,2,3,4,5), default=5)
    parser.add_argument('--counts', nargs='+', type=int, choices=(20,100), default=[20,100])
    parser.add_argument('--output', type=Path, help='New directory within data/output; never overwrite.')
    parser.add_argument('--purpose', choices=('exploratory_demand','technical_check'), default='exploratory_demand')
    parser.add_argument('--check-only', action='store_true', help='Validate inputs and server; create no actors and do not change weather.')
    parser.add_argument('--carla-pythonapi', type=Path, default=Path(r'C:\CARLA\WindowsNoEditor\PythonAPI\carla'))
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds<=0:
        parser.error('--seconds debe ser positivo y finito')
    if args.counts!=sorted(set(args.counts)):
        parser.error('--counts debe contener cantidades distintas en orden ascendente')
    return args


def run_campaign(args):
    """Validate inputs, run the requested cases, and save campaign progress, audits, and metrics."""
    import carla
    manifest = read(ROOT/CONFIG_DIR/'preparation_manifest.json')
    check_hashes(manifest['input_sha256'])
    configs = {n:ROOT/CONFIG_DIR/('town01_%03d.json'%n) for n in args.counts}
    for path in configs.values():
        TripSimulationConfig.from_json(path, dict(seed=args.seed, duration_seconds=args.seconds))
    client = carla.Client('localhost',2000)
    client.set_timeout(15)
    world = client.get_world()
    initial = preflight(world)
    if client.get_server_version()!='0.9.15' or client.get_client_version()!='0.9.15':
        raise RuntimeError('Esta campana requiere cliente y servidor CARLA 0.9.15.')
    validate_map(world.get_map(), manifest)
    if args.check_only:
        print(json.dumps(dict(status='ready', server='0.9.15', preflight=initial,
                             counts=args.counts, seed=args.seed, seconds=args.seconds,
                             simulation_speed=args.simulation_speed, actors_created=0),indent=2))
        return 0
    name = 'demand20_100_seed_%d_%s'%(args.seed,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output = (args.output or ROOT/'data/output'/name).resolve()
    try:
        output.relative_to((ROOT/'data/output').resolve())
    except ValueError:
        raise ValueError('--output debe estar dentro de data/output.')
    if output == (ROOT/'data/output').resolve():
        raise ValueError('Se requiere un subdirectorio nuevo.')
    output.mkdir(parents=True,exist_ok=False)
    sources = list(ROOT.glob('src/**/*.py'))+[ROOT/'scripts'/n for n in (
        'run_demand_campaign.py','prepare_demand_campaign.py','prepare_pilots.py','review_trip_simulation.py',
        'run_trip_simulation.py','audit_observation_stream.py','analyze_mobility.py')]
    sources += [project_path(n, ROOT) for n in manifest['input_sha256']]+[ROOT/CONFIG_DIR/'preparation_manifest.json']
    frozen = {p.relative_to(ROOT).as_posix():digest(p) for p in sources}
    for relative in frozen:
        dest = output/'source_snapshot'/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(project_path(relative, ROOT),dest)
    save(output/'source_sha256.json',frozen)
    cases = [dict(vehicle_count=n,scenario=s,seed=args.seed,status='pending',run_directories=[])
             for n in args.counts for s in ('random_baseline','history_80_20')]
    plan = dict(status='prepared',created_at_utc=stamp(),purpose=args.purpose,counts=args.counts,
                seed=args.seed,duration_s=args.seconds,simulation_speed=args.simulation_speed,
                cameras=False,bootstrap_seed=42,history_initial_visits=30,cases=cases,
                weather=read(ROOT/CONFIG_DIR/'weather.json'),initial_world=initial,
                invocation=sys.argv,server_version=client.get_server_version())
    save(output/'campaign.json',plan)
    original_weather = world.get_weather()
    print('CAMPAIGN',output,flush=True)
    outcome = 0
    try:
        weather = carla.WeatherParameters()
        for key,value in plan['weather'].items():
            setattr(weather,key,value)
        world.set_weather(weather)
        expected_weather = preflight(world)['weather']
        plan.update(status='running',started_at_utc=stamp())
        for number,case in enumerate(cases,1):
            check_hashes(frozen)
            state = preflight(world)
            if state['weather']!=expected_weather:
                raise RuntimeError('El clima cambio durante la campana.')
            label='n%03d_%s'%(case['vehicle_count'],case['scenario'])
            save(output/(label+'_preflight.json'),state)
            config=TripSimulationConfig.from_json(configs[case['vehicle_count']],dict(
                seed=args.seed,duration_seconds=args.seconds,destination_selection_mode=case['scenario'],
                navigation_diagnostics_enabled=True))
            simulation=VisualReviewSimulation(config,ROOT,args.simulation_speed,str(args.carla_pythonapi),capture_images=False)
            expected_run=ROOT/config.output_root/simulation.run_id
            case.update(status='running',started_at_utc=stamp(),run=expected_run.name,
                        run_directories=[expected_run.relative_to(ROOT/'data/output').as_posix()])
            save(output/'campaign.json',plan)
            print('[%d/%d] START %s, %s simulated seconds'%(number,len(cases),label,args.seconds),flush=True)
            start=time.monotonic()
            with (output/(label+'_console.txt')).open('w',encoding='utf8') as log:
                with contextlib.redirect_stdout(Tee(sys.stdout,log)), contextlib.redirect_stderr(Tee(sys.stderr,log)):
                    run=simulation.run()
            case['wall_seconds_process']=time.monotonic()-start
            save(output/(label+'_cleanup.json'),preflight(world))
            check_hashes(frozen)
            del simulation
            gc.collect()
            metrics=analyze_run(run)
            audit=audit_stream(run,metrics)
            save(output/(label+'_metrics.json'),metrics)
            save(output/(label+'_audit.json'),audit)
            save(output/(label+'_output_sha256.json'),{p.relative_to(run).as_posix():digest(p) for p in run.rglob('*') if p.is_file()})
            if audit['integrity_errors']:
                raise RuntimeError('Errores de integridad en '+label+': '+str(audit['integrity_errors']))
            case.update(status='completed',ended_at_utc=stamp(),statuses=metrics['statuses'],
                        completed_trips=metrics['completed'],collisions=metrics['events']['collision']['observed_callbacks'],
                        invasions=metrics['events']['lane_invasion']['observed_callbacks'],
                        observations=audit['observations'],integrity_errors=[],
                        achieved_process_ratio=metrics['simulation_duration_s']/case['wall_seconds_process'])
            save(output/'campaign.json',plan)
            print('[%d/%d] END %s %s; collisions=%s invasions=%s'%(number,len(cases),label,case['statuses'],case['collisions'],case['invasions']),flush=True)
        plan.update(status='completed',ended_at_utc=stamp())
        save(output/'campaign.json',plan)
        command=[sys.executable,'scripts/analyze_mobility.py','--campaign',str(output/'campaign.json'),'--output',str(output/'metrics')]
        with (output/'analysis_console.txt').open('w',encoding='utf8') as log:
            result=subprocess.run(command,cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError('La comparacion final fallo; revisar analysis_console.txt.')
        check_hashes(frozen)
        save(output/'source_verification.json',dict(verified_at_utc=stamp(),unchanged=frozen))
    except BaseException as error:
        outcome=130 if isinstance(error,KeyboardInterrupt) else 1
        for case in cases:
            if case['status']=='running':
                case.update(status='interrupted' if outcome==130 else 'failed',error=str(error))
        plan.update(status='incomplete',stopped_at_utc=stamp(),error=type(error).__name__+': '+str(error))
        (output/'failure.txt').write_text(traceback.format_exc(),encoding='utf8')
        print('STOP: se conservan resultados parciales en',output,flush=True)
    finally:
        try:
            world.set_weather(original_weather)
            final=preflight(world)
            save(output/'final_server_state.json',final)
            if any(final[key]!=initial[key] for key in ('synchronous','fixed_delta_seconds','no_rendering','weather')):
                raise RuntimeError('El estado final del mundo difiere del inicial.')
        except Exception as error:
            outcome=outcome or 1
            plan.update(status='incomplete',cleanup_error=str(error))
        save(output/'campaign.json',plan)
    print('COMPLETE' if outcome==0 else 'INCOMPLETE',output/'campaign.json',flush=True)
    return outcome


if __name__=='__main__':
    try:
        raise SystemExit(run_campaign(parse_args()))
    except (RuntimeError,ValueError,FileNotFoundError) as error:
        print('Error:',error,file=sys.stderr)
        raise SystemExit(1)
