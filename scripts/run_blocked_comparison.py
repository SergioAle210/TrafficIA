"""Compare blocked termination with retained destinations, using a live spectator."""
import argparse
import contextlib
import json
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_demand_campaign import preflight, validate_map, check_hashes, digest, save, read, Tee
from scripts.audit_observation_stream import audit_stream
from src.analysis.mobility_analysis import analyze_run, read_csv
from src.simulation.stop_review import StopReviewSimulation
from src.simulation.trip_runner import TripSimulationConfig


def json_rows(path):
    with path.open(encoding='utf8') as stream:
        for line in stream:
            yield json.loads(line)


def audit_stops(run, metrics):
    warnings = read_csv(run/'blocked_warnings.csv')
    thresholds = list(json_rows(run/'stop_thresholds.jsonl'))
    config = read(run/'run_config.json')['simulation_config']
    errors = []
    keys = lambda rows: [(r['vehicle_id'], int(r['frame'])) for r in rows]
    if keys(warnings) != keys(thresholds): errors.append('warning_evidence_mismatch')
    if len(set(keys(warnings))) != len(warnings): errors.append('duplicate_warning')
    policy = config['blocked_policy']
    if policy == 'terminate' and len(warnings) != metrics['statuses'].get('blocked', 0):
        errors.append('warning_termination_mismatch')
    if policy == 'keep_trip' and metrics['statuses'].get('blocked', 0):
        errors.append('keep_trip_terminated_as_blocked')
    evidence = Counter(reason for r in thresholds for reason in r['evidence'])
    phase_seconds, ends = Counter(), Counter()
    physical_60 = 0
    for episode in json_rows(run/'stop_episodes.jsonl'):
        phase_seconds.update(episode['phase_seconds'])
        ends[episode['end_reason']] += 1
        physical_60 += episode['duration_s'] >= config['blocked_time_threshold_seconds']-1e-6
    return dict(integrity_errors=errors, threshold_warnings=len(warnings),
        physical_episodes_at_least_60s=physical_60, episode_end_reasons=dict(ends),
        stopped_seconds_by_phase=dict(phase_seconds), threshold_evidence=dict(evidence),
        first_thresholds=[{k:r[k] for k in ('vehicle_id','context_trip_id','destination_id',
            'elapsed_s','counter_s','route_remaining_m','evidence','command','recent_contacts')} for r in thresholds[:10]])


def comparison_conditions(config):
    """Only policy is intentionally varied; compare all other effective inputs."""
    simulation = dict(config['simulation_config'])
    simulation.pop('blocked_policy')
    simulation.pop('output_root')
    vehicles = [{k:v for k,v in vehicle.items() if k != 'carla_actor_id'} for vehicle in config['vehicles']]
    return dict(simulation=simulation, vehicles=vehicles, environment=config.get('environment'),
                arrival_control=config.get('arrival_control'), route_planning=config.get('route_planning'))


def write_report(output, plan):
    lines = ['# Comparación diagnóstica de detenciones', '',
        'Estado: **'+plan['status']+'**. Sin cámaras; el espectador en vivo no constituye evidencia visual guardada.', '',
        '| Caso | Completados | blocked | Pendientes al cierre | Avisos | Velocidad (km/h) | Colisiones (callbacks) | Invasiones (callbacks) |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for case in plan['cases']:
        if case['status'] != 'completed': continue
        m, a = case['metrics'], case['stop_audit']
        speed = m['speed']['mean_kmh']
        lines.append('| {} | {} | {} | {} | {} | {} | {} | {} |'.format(case['label'], m['completed'],
            m['statuses'].get('blocked',0), m['statuses'].get('aborted',0), a['threshold_warnings'], speed,
            m['events']['collision']['observed_callbacks'],m['events']['lane_invasion']['observed_callbacks']))
    for key in ('error','cleanup_error'):
        if plan.get(key): lines += ['', '**'+key+'**: '+plan[key]]
    lines += ['', '## Cronología y límites', '',
        'Los motivos registrados son decisiones del agente; no demuestran por sí solos el origen físico de una cola.',
        'Los avisos y las terminaciones son cantidades distintas. Cero blocked bajo keep_trip no demuestra mejor circulación.',
        'Los contactos son callbacks recientes (hasta 20 en 5 s), no accidentes únicos. Las esperas pendientes están censuradas.']
    for case in plan['cases']:
        if case['status'] != 'completed': continue
        lines += ['', '### '+case['label'], '']
        a = case['stop_audit']
        lines.append('Tiempo detenido por fase (vehículo-segundos): '+json.dumps(a['stopped_seconds_by_phase'])+'.')
        lines.append('Episodios físicos de al menos 60 s: '+str(a['physical_episodes_at_least_60s'])+'.')
        for row in case['stop_audit']['first_thresholds']:
            lines.append('- t={:.2f}s: {}/{} hacia {}, restante={:.2f}m; evidencia: {}.'.format(
                row['elapsed_s'], row['vehicle_id'], row['context_trip_id'], row['destination_id'],
                row['route_remaining_m'], ', '.join(row['evidence'])))
        if not case['stop_audit']['first_thresholds']:
            lines.append('No apareció un aviso de 60 s. Comprobación visual de ese evento pendiente; no se amplió la duración.')
    (output/'informe.md').write_text('\n'.join(lines)+'\n', encoding='utf8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--technical-only', action='store_true', help='Solo comprobación de 15 s con 100 vehículos.')
    group.add_argument('--skip-technical', action='store_true', help='Solo las dos corridas de 300 s tras verificar la prueba técnica.')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--carla-pythonapi', default=r'C:\CARLA\WindowsNoEditor\PythonAPI\carla')
    args = parser.parse_args(argv)
    import carla
    client = carla.Client('localhost', 2000)
    client.set_timeout(15)
    world = client.get_world()
    initial = preflight(world)
    if client.get_server_version() != '0.9.15' or client.get_client_version() != '0.9.15':
        raise RuntimeError('Se requiere CARLA 0.9.15.')
    if initial['no_rendering']: raise RuntimeError('Activa renderizado para el espectador.')
    config_dir = ROOT/'config/demand_20_100'
    manifest = read(config_dir/'preparation_manifest.json')
    check_hashes(manifest['input_sha256'])
    validate_map(world.get_map(), manifest)
    if args.check_only:
        print(json.dumps(initial, indent=2))
        return 0
    output = ROOT/'data/output'/('blocked_comparison_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    sources = list(ROOT.glob('src/**/*.py')) + list(ROOT.glob('scripts/*.py'))
    sources += [ROOT/p for p in manifest['input_sha256']]+[config_dir/'preparation_manifest.json']
    frozen = {p.relative_to(ROOT).as_posix():digest(p) for p in sources}
    for relative in frozen:
        target = output/'source_snapshot'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relative, target)
    save(output/'source_sha256.json', frozen)
    cases = []
    if not args.skip_technical: cases.append(dict(label='technical_15s', policy='terminate', seconds=15., status='pending'))
    if not args.technical_only:
        cases += [dict(label=p, policy=p, seconds=300., status='pending') for p in ('terminate','keep_trip')]
    plan = dict(status='running', cases=cases, seed=210, vehicles=100, scenario='random_baseline',
                requested_speed=1, cameras=False, initial_world=initial, comparison_equal_except_policy=None)
    save(output/'campaign.json', plan)
    print('CAMPAIGN', output, flush=True)
    original_weather = world.get_weather()
    conditions = []
    try:
        weather = carla.WeatherParameters()
        for key,value in read(config_dir/'weather.json').items(): setattr(weather,key,value)
        world.set_weather(weather)
        expected_weather = preflight(world)['weather']
        for case in cases:
            check_hashes(frozen)
            before = preflight(world)
            if before['weather'] != expected_weather: raise RuntimeError('El clima cambió.')
            save(output/(case['label']+'_preflight.json'), before)
            config = TripSimulationConfig.from_json(config_dir/'town01_100.json', dict(
                seed=210, duration_seconds=case['seconds'], destination_selection_mode='random_baseline',
                blocked_policy=case['policy'], max_trip_time_seconds=None, navigation_diagnostics_enabled=True))
            simulation = StopReviewSimulation(config, ROOT, 1, args.carla_pythonapi)
            case.update(status='running', run=str(ROOT/config.output_root/simulation.run_id))
            save(output/'campaign.json', plan)
            print('START', case['label'], case['seconds'], 's; mirar ventana CARLA', flush=True)
            started = time.monotonic()
            with (output/(case['label']+'_console.txt')).open('w', encoding='utf8') as log:
                with contextlib.redirect_stdout(Tee(sys.stdout,log)), contextlib.redirect_stderr(Tee(sys.stderr,log)):
                    run = simulation.run()
            case['wall_seconds'] = time.monotonic()-started
            after = preflight(world)
            save(output/(case['label']+'_cleanup.json'), after)
            check_hashes(frozen)
            metrics = analyze_run(run)
            audit = audit_stream(run, metrics)
            stop_audit = audit_stops(run, metrics)
            save(output/(case['label']+'_audit.json'), dict(observations=audit, stops=stop_audit))
            if audit['integrity_errors'] or stop_audit['integrity_errors']:
                raise RuntimeError('Auditoría falló: '+str(audit['integrity_errors']+stop_audit['integrity_errors']))
            if case['seconds']==300: conditions.append(comparison_conditions(read(run/'run_config.json')))
            save(output/(case['label']+'_output_sha256.json'), {p.name:digest(p) for p in run.iterdir() if p.is_file()})
            case.update(status='completed', metrics=metrics, stop_audit=stop_audit)
            save(output/'campaign.json', plan)
            print('END', case['label'], metrics['statuses'], flush=True)
        if len(conditions)==2:
            plan['comparison_equal_except_policy'] = conditions[0]==conditions[1]
            if not plan['comparison_equal_except_policy']: raise RuntimeError('Condiciones distintas además de política.')
        plan['status'] = 'completed'
    except BaseException as error:
        plan.update(status='incomplete', error=type(error).__name__+': '+str(error))
        for case in cases:
            if case['status']=='running': case.update(status='failed', error=str(error))
        raise
    finally:
        try:
            world.set_weather(original_weather)
            final = preflight(world)
            save(output/'final_server_state.json', final)
            if any(initial[k]!=final[k] for k in ('synchronous','fixed_delta_seconds','no_rendering','weather')):
                raise RuntimeError('No se restauró el estado del mundo.')
        except Exception as error:
            plan.update(status='incomplete', cleanup_error=str(error))
            print('CIERRE INCOMPLETO:', error, flush=True)
        save(output/'campaign.json', plan)
        write_report(output, plan)
    return 0 if plan['status']=='completed' else 1


if __name__=='__main__':
    raise SystemExit(main())
