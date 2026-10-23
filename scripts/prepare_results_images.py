"""Assemble a named, traceable figure collection for the graduation results.

Offline only. Copies preserved figures and makes a few summaries from audited
analysis JSON; never connects to CARLA or modifies the original figures.
"""
import argparse
import hashlib
import html
import json
import os
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'images'
DATA = ROOT/'data/output'
os.environ.setdefault('MPLCONFIGDIR', str(DATA/'.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

BLUE, ORANGE = '#2463A6', '#D98420'
SELECTORS = ('random_baseline', 'history_80_20')
LABELS = ('Aleatorio', 'Historial 80/20')
CATEGORIES = ('residential', 'work_education', 'services_leisure')
CATEGORY_NAMES = ('Residencia', 'Trabajo / educación', 'Servicios / ocio')
CATEGORY_COLORS = ('#508D86', '#DDA94C', '#8A71B3')
ENTRIES, OMITTED = [], []


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.resolve().relative_to(ROOT).as_posix()


def add_entry(folder, name, title, note, role, stage, sources, method, outputs):
    entry = dict(id=name, stage=stage, role=role, title=title, caption=note,
        method=method, sources=[dict(path=rel(p), sha256=sha(p)) for p in sources],
        files=[dict(path=rel(p), sha256=sha(p)) for p in outputs])
    ENTRIES.append(entry)
    return entry


def copy_figure(source, folder, name, title, note, role, stage):
    directory = OUT/folder
    directory.mkdir(parents=True, exist_ok=True)
    sources, outputs = [], []
    for ext in ('.png', '.svg'):
        origin = source.with_suffix(ext)
        if not origin.exists():
            if ext == '.png': raise FileNotFoundError(origin)
            continue
        target = directory/(name+ext)
        if target.exists() and sha(target) != sha(origin):
            raise FileExistsError('No se sobrescribe una figura distinta: '+str(target))
        shutil.copyfile(origin, target)
        assert sha(origin) == sha(target)
        sources.append(origin)
        outputs.append(target)
    return add_entry(folder, name, title, note, role, stage, sources, 'copia_identica', outputs)


def generated(fig, folder, name, title, note, stage, sources):
    directory = OUT/folder
    directory.mkdir(parents=True, exist_ok=True)
    fig.suptitle(title, x=.055, ha='left', y=.98, fontsize=17, fontweight='bold')
    fig.text(.055, .02, note, fontsize=9, va='bottom', color='#475569')
    fig.tight_layout(rect=(.02,.105,.995,.915))
    outputs=[]
    for ext in ('.png','.svg'):
        target=directory/(name+ext)
        fig.savefig(target, dpi=220)
        outputs.append(target)
    plt.close(fig)
    return add_entry(folder,name,title,note,'resultados',stage,sources,'resumen_nuevo_de_analisis_auditado',outputs)


def bars(axis, values, title, unit, labels=LABELS):
    values = np.asarray(values, dtype=float)
    axis.bar(range(len(values)), values, color=[BLUE,ORANGE], width=.58)
    axis.set(title=title, ylabel=unit, xticks=range(len(values)), xticklabels=labels)
    high=max(values) if max(values)>0 else 1.
    axis.set_ylim(0,high*1.3)
    axis.grid(axis='y',alpha=.25)
    axis.set_axisbelow(True)
    for i,value in enumerate(values):
        axis.text(i,value+high*.04,'%.2f'%value,ha='center',fontweight='bold')


def pilot_figures():
    for n,base,directory in (
            (3,'visual_review_20260915','01_tres_vehiculos_600s'),
            (5,'pilot5_20260915','02_cinco_vehiculos_600s'),
            (10,'pilot10_20260917','03_diez_vehiculos_600s'),
            (20,'pilot20_20260917','04_veinte_vehiculos_600s')):
        stage='%d vehículos · 600 s · semilla 42'%n
        prefix='n%03d_600s_semilla42'%n
        folder='resultados/'+directory
        source=DATA/base/'metrics/analysis.json'
        analysis=read(source)
        runs=sorted(analysis['runs'],key=lambda r:SELECTORS.index(r['scenario']))
        assert len(runs)==2 and all(r['vehicle_count']==n and r['seed']==42 and
            abs(r['simulation_duration_s']-600)<.01 and not r['integrity_errors'] for r in runs)
        assert all(r['exposure']['scope']=='vehicle_presence_including_dwell' for r in runs)
        for scenario,label in zip(SELECTORS,('aleatorio','historial_80_20')):
            sub=('baseline' if scenario==SELECTORS[0] else 'history')+('_no_cameras_review' if n==3 else '_review')
            copy_figure(DATA/base/sub/'trajectories',folder,prefix+'_trayectorias_y_velocidades_'+label,
                'Trayectorias y velocidades · '+LABELS[SELECTORS.index(scenario)],
                stage+'. Reconstrucción de registros; no es una captura de CARLA. Incluye los vehículos de esta flota.',
                'resultados',stage)
        fig,axes=plt.subplots(2,2,figsize=(11.5,8))
        panels=[([r['travel_time']['mean_s'] for r in runs],'Tiempo medio de viajes completados','Segundos simulados'),
                ([r['speed']['mean_kmh'] for r in runs],'Velocidad media de presencia','km/h'),
                ([r['events']['collision']['per_vehicle_km'] for r in runs],'Tasa de colisiones registradas','Callbacks / vehículo-km'),
                ([r['events']['lane_invasion']['per_vehicle_km'] for r in runs],'Tasa de invasiones de carril','Callbacks / vehículo-km')]
        for axis,args in zip(axes.flat,panels): bars(axis,*args)
        counts='; '.join('%s: %d completados, %d incompletos'%(label,r['completed'],r['incomplete_count']) for label,r in zip(LABELS,runs))
        note=stage+'. '+counts+'.\nTiempo: solo llegadas; velocidad: toda la presencia, incluidas esperas. Callbacks no equivalen a accidentes independientes.'
        generated(fig,folder,prefix+'_tiempo_velocidad_y_tasas_de_incidentes',
                  'Piloto de %d vehículos: movilidad e incidentes'%n,note,stage,[source])
        fig,axes=plt.subplots(1,2,figsize=(11.5,6))
        for axis,pop,title in zip(axes,('assigned','reached'),('Destinos asignados','Destinos alcanzados')):
            bottom=np.zeros(2)
            for cat,label,color in zip(CATEGORIES,CATEGORY_NAMES,CATEGORY_COLORS):
                values=np.array([next(d['proportion'] for d in r['destinations'][pop]['by_category'] if d['value']==cat)*100 for r in runs])
                axis.bar([0,1],values,bottom=bottom,color=color,label=label,width=.6)
                for x,v in enumerate(values):
                    if v: axis.text(x,bottom[x]+v/2,'%.1f%%'%v,ha='center',va='center',fontsize=10,color='white',fontweight='bold')
                bottom+=values
            axis.set(title=title,ylim=(0,103),ylabel='% dentro de cada población',xticks=[0,1],xticklabels=LABELS)
        axes[0].legend(loc='upper center',bbox_to_anchor=(1.08,-.10),ncol=3,fontsize=9)
        generated(fig,folder,prefix+'_distribucion_destinos_asignados_y_alcanzados',
            'Piloto de %d vehículos: categorías de destinos'%n,
            stage+'. Asignaciones y llegadas tienen denominadores distintos.\n80/20 describe ramas de selección; no exige 80/20 entre categorías ni entre llegadas.',stage,[source])


RENAME={
    'resumen_objetivos':'resumen_metricas_objetivo_3',
    'tiempos_viaje':'tiempos_de_viajes_completados_y_cobertura_de_llegadas',
    'estados_viaje':'diagnostico_estados_de_viaje_incluye_blocked',
    'destinos_categorias':'distribucion_destinos_por_categoria',
    'destinos_detalle':'distribucion_de_los_42_destinos',
    'velocidad_paradas':'evolucion_velocidad_y_tiempo_a_baja_velocidad',
    'incidentes':'colisiones_e_invasiones_conteos_y_tasas',
    'historial_ramas':'crecimiento_historial_y_seleccion_80_20',
    'flujo_densidad_velocidad':'relaciones_flujo_densidad_velocidad',
    'cobertura_flujo':'mapa_de_tramos_y_cobertura_de_densidades',
    'evolucion_resultados':'diagnostico_evolucion_llegadas_y_fallos',
    'comparacion_mitades':'diagnostico_primera_y_segunda_mitad_incluye_blocked',
    'comparacion_repeticiones':'diagnostico_comparacion_repeticiones_incluye_blocked',
    'evolucion_repeticiones':'comparacion_repeticiones_velocidad_y_llegadas'}
DIAGNOSTIC={'estados_viaje','evolucion_resultados','comparacion_mitades','comparacion_repeticiones'}


def campaign_figures():
    campaigns=[
        ('visual_analysis20_20260917','05_veinte_vehiculos_1800s_dos_semillas','n020_1800s_semillas210_109',
         '20 vehículos · 1800 s · semillas 210 y 109 · 17 septiembre'),
        ('visual_analysis20_100_guides_20260920','06_demanda_20_100_1800s','n020_100_1800s_semilla210',
         '20/100 vehículos · 1800 s · semilla 210 · corrida del 18 septiembre'),
        ('visual_analysis20_100_3600_20260922','07_demanda_20_100_3600s_repeticion_1','n020_100_3600s_semilla210_repeticion1',
         '20/100 vehículos · 3600 s · semilla 210 · repetición 1 · noche 21-22 septiembre'),
        ('visual_analysis20_100_3600_repeat_20260923','08_demanda_20_100_3600s_repeticion_2','n020_100_3600s_semilla210_repeticion2',
         '20/100 vehículos · 3600 s · semilla 210 · repetición 2 · noche 22-23 septiembre')]
    for base,directory,prefix,stage in campaigns:
        manifest=read(DATA/base/'figures_manifest.json')
        for item in manifest['figures']:
            suffix=item['name'].split('_',1)[1]
            role='respaldo_tecnico' if suffix in DIAGNOSTIC else 'resultados'
            folder=role+'/'+directory
            if suffix=='evolucion_repeticiones':
                folder='resultados/09_comparacion_dos_repeticiones'
                stage_for_item='Comparación de las dos campañas de 3600 s · semilla 210'
                item_prefix='n020_100_3600s_semilla210_ambas_repeticiones'
            else:
                stage_for_item=stage
                item_prefix=prefix
            name=item_prefix+'_'+RENAME[suffix]
            if suffix=='flujo_densidad_velocidad' and ('guides' in base or '3600' in base):
                name+='_con_lineas_guia'
            copy_figure(DATA/base/item['name'],folder,name,item['title'],
                stage_for_item+'. '+item['note'],role,stage_for_item)
    # Preserve the only materially different old plate; other pages duplicate the revised collection.
    copy_figure(DATA/'visual_analysis20_100_20260919/09_flujo_densidad_velocidad',
        'respaldo_tecnico/version_anterior_1800s_sin_guias',
        'n020_100_1800s_semilla210_relaciones_trafico_version_anterior_sin_guias',
        'Relaciones de tráfico: versión anterior sin líneas guía',
        'Mismos datos de la campaña del 18 septiembre. Usar preferentemente la versión con guías, no contar ambas como nuevas corridas.',
        'respaldo_tecnico','Versión anterior de visualización')


def supporting_figures():
    specs=[
        ('scaling_pilots_20260917/comparison','resultados/10_comparacion_pilotos',
         'n005_010_020_600s_semilla42_comparacion_escalamiento', 'Comparación descriptiva de pilotos de 5, 10 y 20 vehículos',
         'Pilotos · 600 s · semilla 42. No son réplicas de una misma cantidad ni una selección definitiva de demandas.'),
        ('pilot20_20260917/baseline_invasions','respaldo_tecnico/incidentes',
         'n020_600s_semilla42_reconstruccion_invasiones_cybertruck', 'Reconstrucción de invasiones del piloto de veinte',
         'Geometría derivada de registros, no captura ni medida de separación a la acera.'),
        ('manual_review_20260915/trajectories_and_speed','respaldo_tecnico/antecedentes_tres_vehiculos',
         'n003_600s_semilla42_trayectorias_revision_manual_14_septiembre', 'Trayectorias de la corrida manual',
         'Antecedente manual del 14 septiembre; no sustituye la pareja auditada de tres vehículos.'),
        ('visual_review_20260915/live_arrivals','respaldo_tecnico/antecedentes_tres_vehiculos',
         'n003_evidencia_visual_parcial_llegadas_intento_interrumpido', 'Evidencia visual parcial de llegadas',
         'Intento interrumpido con cámaras. Evidencia parcial de implementación, no corrida completa de resultados.'),
        ('arrival_correction_20260908/arrival_comparison','respaldo_tecnico/correcciones_implementacion',
         'n003_comparacion_antes_despues_correccion_llegadas', 'Comparación de corrección de llegadas',
         'Antecedente de depuración del controlador de llegada; no comparar sus versiones como tratamientos académicos.'),
        ('dwell_investigation_20260908/dwell_diagnosis','respaldo_tecnico/correcciones_implementacion',
         'n003_diagnostico_frenado_espera_y_siguiente_viaje', 'Diagnóstico de llegada y espera',
         'Antecedente de instrumentación; no métrica adicional del objetivo 3.'),
        ('reliability_campaign_20260908/long/review/invasion_geometry','respaldo_tecnico/incidentes',
         'n003_1800s_geometria_de_invasiones_en_curvas', 'Geometría de invasiones en la campaña larga de tres',
         'Contexto de incidentes y huella vehicular; no implica automáticamente infracción ni defecto.')]
    for source,folder,name,title,note in specs:
        copy_figure(DATA/source,folder,name,title,note,folder.split('/')[0],title)
    base='reliability20_20260917_seeds210_109_x5'
    for seed in (210,109):
        for scenario,label in (('baseline','aleatorio'),('history','historial_80_20')):
            copy_figure(DATA/base/('seed_%d_%s_review'%(seed,scenario))/'trajectories',
                'resultados/05_veinte_vehiculos_1800s_dos_semillas',
                'n020_1800s_semilla%d_trayectorias_y_velocidades_%s'%(seed,label),
                'Trayectorias y velocidades · %s · semilla %d'%(label,seed),
                '20 vehículos, 1800 s. Registros de cada vehículo; no es una captura de CARLA.',
                'resultados','20 vehículos · 1800 s · semillas 210 y 109 · 17 septiembre')
        copy_figure(DATA/base/('seed_%d_baseline_incident_01'%seed),
            'respaldo_tecnico/incidentes','n020_1800s_semilla%d_reconstruccion_contacto_aleatorio'%seed,
            'Reconstrucción de contacto · semilla %d'%seed,
            'Evidencia descriptiva del incidente; los callbacks persistentes no son accidentes independientes.',
            'respaldo_tecnico','20 vehículos · incidentes')


def clean_repeat_comparison():
    base=DATA/'visual_analysis20_100_3600_repeat_20260923'
    source=base/'repeat_comparison.csv'
    data=pd.read_csv(source)
    previous_source=base/'previous_review/chart_input_review.json'
    repeat_source=base/'chart_input_review.json'
    previous={(r['vehicle_count'],r['scenario']):r for r in read(previous_source)['metrics']}
    repeated={(r['vehicle_count'],r['scenario']):r for r in read(repeat_source)['metrics']}
    coverage=[]
    for key in sorted(previous):
        a,b=previous[key],repeated[key]
        assert a['started'] and b['started']
        coverage.append(dict(vehicle_count=key[0],scenario=key[1],metric='incomplete_fraction',
            first=a['incomplete_count']/a['started'],repeat=b['incomplete_count']/b['started']))
    data=pd.concat([data,pd.DataFrame(coverage)],ignore_index=True)
    labels=['20\nAleatorio','20\nHistorial','100\nAleatorio','100\nHistorial']
    metrics=[('completed_mean_time_s','Tiempo medio de completados','Segundos'),
             ('mean_speed_kmh','Velocidad media de presencia','km/h'),
             ('collision_rate_per_vehicle_km','Tasa de colisiones','Callbacks / vehículo-km'),
             ('invasion_rate_per_vehicle_km','Tasa de invasiones','Callbacks / vehículo-km'),
             ('completed','Llegadas completadas','Viajes'),
             ('incomplete_fraction','Proporción de viajes incompletos','% de viajes iniciados')]
    fig,axes=plt.subplots(2,3,figsize=(15,9))
    for axis,(metric,title,unit) in zip(axes.flat,metrics):
        rows=data[data.metric==metric].set_index(['vehicle_count','scenario'])
        order=[(n,s) for n in (20,100) for s in SELECTORS]
        assert set(rows.index)==set(order), metric
        values=rows.loc[order]
        multiplier=100 if metric=='incomplete_fraction' else 1
        maximum=values[['first','repeat']].to_numpy().max()*multiplier
        high=maximum if maximum>0 else 1.
        for column,offset,color,label in [('first',-.19,'#A9B8C5','Repetición 1'),('repeat',.19,BLUE,'Repetición 2')]:
            ys=values[column].to_numpy()*multiplier
            axis.bar(np.arange(4)+offset,ys,width=.36,color=color,label=label)
            for x,y in zip(np.arange(4)+offset,ys):
                lift=.03 if column=='first' else .095
                axis.text(x,y+high*lift,'%.0f'%y if metric=='completed' else '%.2f'%y,ha='center',fontsize=8)
        axis.set(title=title,ylabel=unit,xticks=range(4),xticklabels=labels,ylim=(0,high*1.3))
        if metric=='incomplete_fraction': axis.set_ylim(0,108)
        axis.grid(axis='y',alpha=.25);axis.set_axisbelow(True)
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.935),ncol=2,fontsize=10)
    generated(fig,'resultados/09_comparacion_dos_repeticiones',
        'n020_100_3600s_semilla210_comparacion_movilidad_incidentes_y_cobertura',
        'Dos repeticiones: movilidad, incidentes y cobertura de viajes',
        'Town01 · semilla 210 · 3600 s. Repetición 1: noche 21-22 septiembre; repetición 2: noche 22-23 septiembre.\nTiempo: solo llegadas; velocidad: toda la presencia. Las categorías de destinos se presentan en las figuras de cada campaña.\nLlegadas e incompletos describen cobertura, no objetivos adicionales. Sin intervalos entre semillas; callbacks no son accidentes.',
        'Comparación de las dos campañas de 3600 s · semilla 210',[source,previous_source,repeat_source])


def documentation():
    figures=sorted(ENTRIES,key=lambda e:e['files'][0]['path'])
    counts=Counter(e['role'] for e in figures)
    lines=['# Imágenes para los resultados del trabajo de graduación','',
        'Colección preparada sin ejecutar CARLA y sin modificar las imágenes o datos originales. Fecha: 2026-09-23.','',
        '- `resultados/`: figuras para las métricas del objetivo 3, implementación de pilotos y relaciones de tráfico.',
        '- `respaldo_tecnico/`: antecedentes, correcciones y láminas que incluyen `blocked`, fallos o mitades. Son anexos opcionales, no métricas académicas adicionales.',
        '- [Galería visual](index.html): muestra primero resultados; permite buscar y mostrar también respaldo.',
        '- [Bloques LaTeX](figuras_resultados.tex): fragmentos independientes para copiar; requieren `\\usepackage{graphicx}` y compilación desde la raíz del proyecto.',
        '- [Catálogo y hashes](catalogo.json): procedencia, título, pie sugerido y nombres exactos.','',
        '**%d figuras de resultados y %d de respaldo.** PNG para `\\includegraphics`; SVG cuando existe para edición/vector. No usar ambas versiones como figuras distintas.'%(counts['resultados'],counts['respaldo_tecnico']), '',
        '## Orden sugerido para el capítulo','',
        '1. Pilotos 3 → 5 → 10 → 20: resúmenes y una trayectoria por etapa para evidenciar agentes simultáneos.',
        '2. Dos demandas 20/100: distribuciones de destinos, tiempo medio, velocidad e incidentes de 3600 s.',
        '3. Repetibilidad: comparación directa de las dos campañas de 3600 s y sus series de velocidad/llegadas.',
        '4. Relaciones flujo-densidad-velocidad y mapa de cobertura como análisis exploratorio.',
        '5. Historial acumulado y ramas 80/20 como evidencia del funcionamiento del generador.','',
        '## Límites que deben acompañar las figuras','',
        'Las cuatro métricas son distribución de destinos, tiempo medio de viaje, velocidad media y tasa de incidentes/invasiones. `blocked` no se añade como quinta métrica. Sin embargo, los viajes sin llegada deben declararse al interpretar el promedio de completados; no ocultarlos por retirar una lámina diagnóstica.',
        'Los pilotos de tres a veinte son etapas de validación; no acreditan un experimento controlado único entre todas las fechas. El 80/20 corresponde a decisiones, no cuotas por categoría o por llegadas. Las líneas guía no ajustan ni validan capacidad vial. Callbacks de colisión no equivalen a accidentes independientes.',
        'Repetición 1: noche local del 21 al 22 septiembre. Repetición 2: noche del 22 al 23. Cada una contiene cuatro casos (20/100 × aleatorio/historial), todos de 3600 s. La carpeta 1800 s pertenece a otra campaña; no es una tercera repetición de 3600 s.',
        'Las láminas copiadas mantienen sus títulos/notas originales y algunas referencias internas a números de lámina. El catálogo relaciona sus nombres nuevos; esas referencias no son números de figura del documento LaTeX.',
        'Se omiten duplicados de QA, capturas RGB por frame y pruebas técnicas cortas. De la versión del 19 septiembre se conserva solo la nube sin guías en respaldo; las demás láminas están representadas por la revisión del 20. Nada se borra de data/output.','',
        '## Catálogo de figuras','']
    tex=['% Fragmentos opcionales; copiar las figuras elegidas. Compilar desde la raíz.',
         '% En el preámbulo: \\usepackage{graphicx}',
         '% No se modificaron protocolo-final.tex ni i-marco_teorico.tex.','']
    cards=[]
    for entry in figures:
        png=next(f['path'] for f in entry['files'] if f['path'].endswith('.png'))
        local=Path(png).relative_to('images').as_posix()
        lines += ['### '+entry['title'],'',
            '**Etapa:** '+entry['stage']+' · **Uso:** '+entry['role']+'.','',
            '['+Path(local).name+']('+local+')','',entry['caption'].replace('\n',' '),'',
            'Fuente: '+', '.join('['+Path(s['path']).name+'](../'+s['path']+')' for s in entry['sources']),'']
        if entry['role']=='resultados':
            caption=entry['caption'].replace('\n',' ').replace('%',r'\%').replace('_',r'\_').replace('&',r'\&')
            tex += ['% '+entry['title'],r'\begin{figure}[htbp]',r'  \centering',
                r'  \includegraphics[width=\linewidth]{'+png+'}',
                r'  \caption{'+caption+'}',r'  \label{fig:'+entry['id'].replace('_','-')+'}',r'\end{figure}','']
        files=' · '.join('<a href="'+html.escape(Path(f['path']).relative_to('images').as_posix())+'">'+Path(f['path']).suffix[1:].upper()+'</a>' for f in entry['files'])
        text=entry['title']+' '+entry['stage']+' '+entry['id']
        cards.append('<article data-role="'+entry['role']+'" data-search="'+html.escape(text.lower())+'"><p class="tag">'+html.escape(entry['stage'])+'</p><h2>'+html.escape(entry['title'])+'</h2><a href="'+html.escape(local)+'"><img loading="lazy" src="'+html.escape(local)+'" alt="'+html.escape(entry['title'])+'"></a><p>'+html.escape(entry['caption']).replace('\n','<br>')+'</p><p>'+files+'</p><code>'+html.escape(Path(local).name)+'</code></article>')
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    (OUT/'figuras_resultados.tex').write_text('\n'.join(tex)+'\n',encoding='utf8')
    (OUT/'catalogo.json').write_text(json.dumps(dict(figures=figures,counts=dict(counts),
        generated_by=rel(Path(__file__)),builder_sha256=sha(Path(__file__)),
        omitted='QA duplicates, per-frame RGB captures, smoke tests; superseded charts except old no-guide traffic plate'),indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    page='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Figuras para resultados · TrafficIA</title>
<style>body{font:16px system-ui,sans-serif;margin:0;background:#eef2f6;color:#182b3a}header{padding:28px 4%;background:#123349;color:white}header a{color:#afe1ed}main{padding:24px 4%}.controls{position:sticky;top:0;background:#fff;padding:14px 4%;box-shadow:0 2px 6px #0002;z-index:2;display:flex;gap:18px;flex-wrap:wrap;align-items:center}input[type=search]{padding:10px;min-width:280px;font:inherit}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:24px}article{background:white;border-radius:10px;padding:20px;overflow-wrap:anywhere}h2{font-size:20px}img{width:100%;height:auto;background:#fff}p{line-height:1.5}.tag{font-size:13px;color:#526779}code{font-size:12px}article[hidden]{display:none}a{color:#2463a6}@media(max-width:600px){.grid{display:block}article{margin-bottom:20px}}</style>
<header><h1>Figuras para los resultados</h1><p>Pilotos de 3, 5, 10 y 20 vehículos · demandas de 20/100 · dos repeticiones de 3600 s</p><p><a href="README.md">Índice y criterios</a> · <a href="figuras_resultados.tex">Fragmentos LaTeX</a> · <a href="catalogo.json">Procedencia y hashes</a></p></header>
<div class="controls"><input id="search" type="search" placeholder="Buscar: tres, 3600, repetición 2, flujo…"><label><input id="technical" type="checkbox"> Mostrar también respaldo técnico</label><span id="count"></span></div><main><p>Las figuras principales corresponden a resultados y funcionamiento del modelo. Los estados blocked quedan en respaldo técnico. Los viajes incompletos siguen documentados para interpretar los tiempos de llegada.</p><div class="grid">'''+''.join(cards)+'''</div></main><script>function filter(){let n=0;const q=document.getElementById('search').value.toLowerCase(),t=document.getElementById('technical').checked;document.querySelectorAll('article').forEach(a=>{a.hidden=(!t&&a.dataset.role!=='resultados')||!a.dataset.search.includes(q);if(!a.hidden)n++;});document.getElementById('count').textContent=n+' figuras';}document.getElementById('search').addEventListener('input',filter);document.getElementById('technical').addEventListener('change',filter);filter();</script></html>'''
    (OUT/'index.html').write_text(page,encoding='utf8')


def verify():
    names=[entry['id'] for entry in ENTRIES]
    assert len(names)==len(set(names)), 'Duplicate names'
    for entry in ENTRIES:
        for item in entry['files']:
            path=ROOT/item['path']
            assert path.is_file() and sha(path)==item['sha256']
            if path.suffix=='.png':
                with Image.open(path) as im:
                    im.verify()
            if entry['method']=='copia_identica':
                source=next(s for s in entry['sources'] if Path(s['path']).suffix==path.suffix)
                assert source['sha256']==item['sha256']
    print(json.dumps(dict(figures=len(ENTRIES),files=sum(len(e['files']) for e in ENTRIES),
        roles=dict(Counter(e['role'] for e in ENTRIES)),status='verified'),indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--independent',action='store_true',help='Regenerate the chapter plots as separate files from preserved CSV/JSON; leave the previous collection intact.')
    parser.add_argument('--output',type=Path,default=OUT/'graficas_independientes')
    parser.add_argument('--thesis-output',type=Path,help='Copy the generated files and manifest to the chapter image directory.')
    parser.add_argument('--only-3600',action='store_true')
    args=parser.parse_args()
    if args.independent:
        import sys
        sys.path.insert(0,str(ROOT))
        from scripts.export_results_charts import export_collection
        export_collection(args.output,args.thesis_output,not args.only_3600)
        return
    if OUT.exists():
        raise FileExistsError('images ya existe; revisar antes de regenerar para no sobrescribir trabajo manual.')
    OUT.mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.titlepad':14,'axes.titlesize':12,'svg.fonttype':'none'})
    pilot_figures()
    campaign_figures()
    supporting_figures()
    clean_repeat_comparison()
    documentation()
    verify()


if __name__=='__main__':
    main()
