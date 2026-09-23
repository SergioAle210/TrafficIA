"""Descriptive repeat comparison; one matched case is not a statistical sample."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd


def comparison_rows(first, second):
    """Match by scenario/fleet/seed, refuse incompatible measurement conditions."""
    def indexed(runs):
        result = {}
        for r in runs:
            key = (r['vehicle_count'], r['scenario'], r['seed'])
            if key in result:
                raise ValueError('Duplicate case')
            result[key] = r
        return result
    old, new = indexed(first), indexed(second)
    if old.keys() != new.keys():
        raise ValueError('Different cases')
    rows, checks = [], []
    for key in old:
        a, b = old[key], new[key]
        fields = ('map', 'simulation_duration_s', 'metrics_semantics_version', 'comparability')
        differences = [field for field in fields if a[field] != b[field]]
        if a['exposure']['scope'] != b['exposure']['scope']:
            differences.append('exposure_scope')
        if a['integrity_errors'] or b['integrity_errors']:
            differences.append('integrity_errors')
        checks.append(dict(vehicle_count=key[0], scenario=key[1], seed=key[2], differences=differences))
        if differences:
            raise ValueError('Noncomparable repeat: %s %s' % (key, differences))
        def metrics(r):
            return dict(completed=r['completed'], mean_speed_kmh=r['speed']['mean_kmh'],
                completed_mean_time_s=r['travel_time']['mean_s'],
                blocked=r['statuses'].get('blocked', 0), route_failed=r['statuses'].get('route_failed', 0),
                aborted=r['statuses'].get('aborted', 0), distance_km=r['exposure']['distance_m']/1000,
                collisions=r['events']['collision']['observed_callbacks'],
                collision_rate_per_vehicle_km=r['events']['collision']['per_vehicle_km'],
                invasions=r['events']['lane_invasion']['observed_callbacks'],
                invasion_rate_per_vehicle_km=r['events']['lane_invasion']['per_vehicle_km'])
        for name, av in metrics(a).items():
            bv = metrics(b)[name]
            delta = bv-av if av is not None and bv is not None else None
            rows.append(dict(vehicle_count=key[0], scenario=key[1], seed=key[2], metric=name,
                first=av, repeat=bv, delta=delta,
                relative_change_percent=100*delta/av if av not in (0, None) and delta is not None else None))
    return rows, checks


def append_comparison(out, previous, figs, base, review):
    read = lambda p: json.loads(p.read_text(encoding='utf8'))
    previous_manifest = read(previous/'figures_manifest.json')
    # Re-audited old raw files, stored with this analysis, not overwriting the old report.
    first = read(out/'previous_review/chart_input_review.json')
    if first['errors'] or review['errors']:
        raise ValueError('Invalid review')
    rows, checks = comparison_rows(first['metrics'], review['metrics'])
    old_campaign = Path(first['campaign']).parent
    new_campaign = Path(review['campaign']).parent
    plans=[read(folder/'campaign.json') for folder in (old_campaign,new_campaign)]
    dates=[]
    for plan in plans:
        dates.append(' / '.join(datetime.fromisoformat(plan[k]).astimezone(timezone(timedelta(hours=-6))).strftime('%Y-%m-%d %H:%M')
                               for k in ('started_at_utc','ended_at_utc')))
    seconds=review['metrics'][0]['simulation_duration_s'];minutes=seconds/60
    seed=review['metrics'][0]['seed']
    if any(abs(r['simulation_duration_s']-seconds)>1e-5 for r in review['metrics']):
        raise ValueError('Mixed durations in campaign')
    source_a, source_b = read(old_campaign/'source_sha256.json'), read(new_campaign/'source_sha256.json')
    changed = sorted(k for k in set(source_a)|set(source_b) if source_a.get(k) != source_b.get(k))
    if changed:
        raise ValueError('Campaign sources differ: '+str(changed))
    files = [previous/'time_series.csv', previous/'derivation_manifest.json',
             out/'previous_review/chart_input_review.json', out/'chart_input_review.json']
    hashes = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    for name in ('time_series.csv','derivation_manifest.json'):
        if hashes[str((previous/name).resolve())] != previous_manifest['input_sha256'][name]:
            raise ValueError('Previous chart input changed: '+name)
    table = pd.DataFrame(rows);table.to_csv(out/'repeat_comparison.csv', index=False)
    result = dict(first_campaign=str(old_campaign), repeat_campaign=str(new_campaign),
        checks=checks, identical_campaign_snapshot_files=len(source_a), snapshot_differences=changed,
        input_sha256=hashes, local_intervals=dates,
        interpretation='Two repetitions of the same seed, not independent seed replications. No confidence interval or causal claim.', rows=rows)
    (out/'repeat_comparison.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    plt=base.plt
    labels=['%d veh.\n%s'%(r['vehicle_count'],'Aleatorio' if r['scenario']=='random_baseline' else 'Historial') for r in review['metrics']]
    fig,axes=plt.subplots(2,3,figsize=(16,9))
    for axis,metric,title,unit,fmt in zip(axes.flat,
            ('completed','mean_speed_kmh','completed_mean_time_s','blocked','collision_rate_per_vehicle_km','invasions'),
            ('Llegadas','Velocidad de presencia','Tiempo medio de completados','Terminaciones blocked','Colisiones por exposición','Invasiones'),
            ('Viajes','km/h','Segundos','Intentos','Callbacks / vehículo-km','Callbacks'),('.0f','.2f','.1f','.0f','.1f','.0f')):
        d=table[table.metric==metric];maximum=max(1,d[['first','repeat']].to_numpy().max())
        for column,offset,color,label in (('first',-.19,'#A9B8C5','Primera'),('repeat',.19,'#2463A6','Repetición')):
            axis.bar(np.arange(4)+offset,d[column],width=.36,color=color,label=label)
            for x,value in zip(np.arange(4)+offset,d[column]):
                axis.text(x,value+.025*maximum,format(value,fmt),ha='center',fontsize=8)
        axis.set(title=title,ylabel=unit,xticks=range(4),xticklabels=labels,ylim=(0,maximum*1.3))
        axis.legend(ncol=2,fontsize=8);axis.grid(axis='y');axis.set_axisbelow(True)
    figs.save(fig,'13_comparacion_repeticiones','Misma semilla y configuración: los resultados no son idénticos',
        'Primera: %s. Repetición: %s (Guatemala).\nAmbas: semilla %d, %.0f s. Tiempo: solo completados. Callbacks no son accidentes independientes; no hay réplicas entre semillas.'%(dates[0],dates[1],seed,seconds))
    old_series=pd.read_csv(previous/'time_series.csv');new_series=pd.read_csv(out/'time_series.csv')
    fig,axes=plt.subplots(4,2,figsize=(14,13))
    for i,(a,b) in enumerate(zip(first['metrics'],review['metrics'])):
        for r,series,e,label,color,ls in ((a,old_series,first['runs'][i],'Primera','#8294A6','--'),(b,new_series,review['runs'][i],'Repetición','#2463A6','-')):
            d=series[series.run==r['run']]
            axes[i,0].plot((d.start_elapsed_s+d.duration_s/2)/60,d.speed_kmh,color=color,ls=ls,label=label)
            trips=pd.read_csv(Path(r['source_directory'])/'trips_log.csv')
            t=np.sort(trips[trips.status=='completed'].arrival_sim_time_s.to_numpy()-e['origin_s'])
            axes[i,1].step(np.r_[0,t,seconds]/60,np.r_[0,np.arange(1,len(t)+1),len(t)],where='post',color=color,ls=ls,label=label)
        for j,axis in enumerate(axes[i]):
            axis.set(title=labels[i].replace('\n',' · '),xlabel='Minutos simulados',xlim=(0,minutes),
                     ylabel='km/h' if j==0 else 'Llegadas acumuladas',ylim=(0,20 if j==0 else 1.08*max(r['completed'] for r in first['metrics']+review['metrics'])))
            axis.grid();axis.legend(fontsize=8)
    figs.save(fig,'14_evolucion_repeticiones','La evolución se parece; la coincidencia exacta no se reproduce',
        'Izquierda: velocidad de presencia en ventanas de 60 s. Derecha: todas las llegadas acumuladas.\nLas mismas condiciones registradas no garantizan trayectorias idénticas; no se atribuye la divergencia a una causa sin investigarla.')
    report=['# Comparación de dos campañas de %.0f s'%seconds,'',
        'Primera: %s. Repetición: %s (hora de Guatemala). Semilla %d en ambas.'%(dates[0],dates[1],seed),
        'Condiciones registradas comparables y %d archivos de código/entradas de campaña idénticos. Ambas campañas auditadas de nuevo: 52 archivos de salida cada una.'%len(source_a),
        'Dos repeticiones de la misma semilla no representan réplicas con semillas independientes. Las diferencias son descriptivas; no se calculan intervalos de confianza.', '',
        '| Vehículos | Selector | Métrica | Primera | Repetición | Diferencia | Cambio (%) |',
        '|---:|---|---|---:|---:|---:|---:|']
    for row in rows:
        pct='no definido (base cero)' if row['relative_change_percent'] is None else '%.2f'%row['relative_change_percent']
        report.append('| %d | %s | %s | %.3f | %.3f | %+.3f | %s |'%(row['vehicle_count'],row['scenario'],row['metric'],row['first'],row['repeat'],row['delta'],pct))
    report+=['','Los callbacks pueden multiplicarse por contactos persistentes; se conservan sus tasas por vehículo-km. Las terminaciones blocked repiten intentos de los mismos vehículos. El detector sigue terminando viajes tras 60 s sin superar 0.2 m/s; no se aplicó la propuesta de conservar el destino durante la detención.',
        'El método de guías, los tramos y las ventanas de análisis se conservan. No se declara capacidad vial ni validación completa de la dinámica por observar tendencias similares.','',
        '![Comparación](13_comparacion_repeticiones.png)','![Evolución](14_evolucion_repeticiones.png)']
    (out/'comparacion_repeticiones.md').write_text('\n'.join(report),encoding='utf8')
