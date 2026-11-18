"""Offline figures for two fleet sizes and two destination selectors."""
import argparse
import hashlib
import html
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.figures import plot_mobility as base
from src.analysis.traffic_flow_analysis import density_band_guides

plt=base.plt
COLORS=base.COLORS
STATUS=['completed','blocked','route_failed','aborted','timeout']
STATUS_NAMES=['Completados','Blocked','Ruta rechazada','Corte final','Timeout']
STATUS_COLORS=['#32867B','#B75E39','#8C679C','#A4B2BF','#DBA332']


def read(p):
    """Read a JSON file into Python data."""
    return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    """Calculate a file's SHA-256 fingerprint by reading it in blocks."""
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def proportions(run,population,level,values):
    """Return destination percentages in the requested category order for the selected population."""
    bins={d['value']:d['proportion'] for d in run['destinations'][population][level]}
    return [100 * bins[v] if bins[v] is not None else np.nan for v in values]


def minute_edges(seconds):
    """Keep 60-second bins at every duration, including a partial final bin."""
    if not np.isfinite(seconds) or seconds <= 0:
        raise ValueError('Duration must be positive and finite')
    return np.r_[np.arange(0., seconds, 60.), seconds]


def main():
    """Build demand-comparison charts from audited inputs, with optional repetition or individual-chart exports."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--compare-data',type=Path,help='Previous figure folder; requires re-audit in data/previous_review.')
    parser.add_argument('--independent-output',type=Path,help='Export one academic plot per file into a separate directory, without changing the input directory.')
    parser.add_argument('--prefix',default='campana_demanda',help='Readable filename prefix for independent figures.')
    args=parser.parse_args();out=args.data
    if args.independent_output:
        from scripts.figures.export_charts import Exporter, load_campaign, export_campaign, export_repetitions
        exporter=Exporter(args.independent_output)
        campaign=load_campaign(args.data)
        export_campaign(campaign,exporter,args.prefix)
        if args.compare_data:
            export_repetitions(load_campaign(args.compare_data),campaign,exporter)
        exporter.finish()
        return
    derived=read(out/'derivation_manifest.json');review=read(out/'chart_input_review.json')
    if review['errors'] or any(not p['comparable'] for p in review['pairs']):raise ValueError('Unvalidated inputs')
    runs=review['metrics'];extra=review['runs'];counts=sorted({r['vehicle_count'] for r in runs})
    seeds={r['seed'] for r in runs};duration={round(r['simulation_duration_s'],1) for r in runs}
    if len(counts)!=2 or len(seeds)!=1 or len(duration)!=1 or len(runs)!=4:
        raise ValueError('Use two fleet sizes, one seed, one duration, two selectors')
    expected=[(n,s) for n in counts for s in ('random_baseline','history_80_20')]
    if [(r['vehicle_count'],r['scenario']) for r in runs]!=expected:raise ValueError('Unexpected paired order')
    short=[('%d veh.\n'%r['vehicle_count'])+('Aleatorio' if r['scenario']=='random_baseline' else 'Historial') for r in runs]
    labels=[s.replace('\n',' · ') for s in short]
    base.SHORT=short;base.style();bars=base.bars
    seed=next(iter(seeds));seconds=next(iter(duration));minutes=seconds/60
    paths=[ROOT/'data/output'/r['run'] for r in runs]
    trips=[pd.read_csv(p/'trips_log.csv') for p in paths]
    completed=[t[t.status=='completed'] for t in trips]
    events=[pd.read_csv(p/'events_log.csv') for p in paths]
    flow=pd.read_csv(out/'flow_cells.csv');series=pd.read_csv(out/'time_series.csv')
    occupied=flow[flow.vehicle_seconds>0]
    guide_rows=[]
    for r in runs:
        cells=flow[flow.run==r['run']].to_dict('records')
        guide_rows.extend(dict(row,run=r['run'],vehicle_count=r['vehicle_count'],scenario=r['scenario'])
                          for row in density_band_guides(cells,width=10,min_cells=10,length_m=derived['section_length_m']))
    guides=pd.DataFrame(guide_rows)
    guides.to_csv(out/'flow_guides.csv',index=False)
    guide_method=dict(density_band_width=10,min_cells=10,
        pooling='Sum S,D and actual space-time area A=L*T: k=1000*sum(S)/sum(A); q=3600*sum(D)/sum(A); v=3.6*sum(D)/sum(S).',
        interpretation='Descriptive pooled points, not fitted equilibrium or confidence intervals. Display threshold only, not statistical sufficiency.',
        connection='Connect adjacent supported density bands only. Same triples, ordered by density, in all three panels. No extrapolation; gaps break the line.',
        excluded_from_guides='Empty cells have undefined speed. Sparse bands remain in CSV and their original points remain plotted.',
        fixed_parameters='10 veh/km/lane width and 10 cells are transparent display choices, not estimated critical density or capacity.')
    (out/'guide_method.json').write_text(json.dumps(guide_method,indent=2),encoding='utf8')
    figs=base.Figures(out)
    context='Town01 · %s vehículos · semilla %d · %g min por corrida. Una ejecución por combinación.'%(' / '.join(map(str,counts)),seed,minutes)

    fig,ax=plt.subplots(2,2,figsize=(13,9))
    bars(ax[0,0],[r['travel_time']['mean_s'] for r in runs],'Tiempo medio de viajes completados','Segundos simulados')
    bars(ax[0,1],[r['speed']['mean_kmh'] for r in runs],'Velocidad media de presencia','km/h',fmt='.2f')
    bottom=np.zeros(4)
    for cat,name,color in zip(base.CATS,base.CAT_NAMES,base.CAT_COLORS):
        values=np.array([proportions(r,'assigned','by_category',[cat])[0] for r in runs])
        ax[1,0].bar(range(4),values,bottom=bottom,color=color,label=name,width=.65)
        for i,v in enumerate(values):ax[1,0].text(i,bottom[i]+v/2,'%.1f%%'%v,ha='center',va='center',color='white',fontsize=9)
        bottom+=values
    ax[1,0].set(title='Destinos asignados por categoría',ylabel='% de asignaciones',ylim=(0,105),xticks=range(4),xticklabels=short)
    ax[1,0].legend(ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.15))
    bars(ax[1,1],[r['events']['collision']['per_vehicle_km'] for r in runs],'Colisiones: tasa de callbacks','Callbacks / vehículo-km',fmt='.2f')
    figs.save(fig,'01_resumen_objetivos','Dos demandas: las cuatro métricas del objetivo 3',
              context+'\nLa media temporal excluye viajes sin llegada; véase su peso en la lámina 03. Invasiones y episodios: lámina 07.')

    fig,ax=plt.subplots(1,3,figsize=(16,6))
    values=[t.travel_time_s.to_numpy() for t in completed]
    bp=ax[0].boxplot(values,patch_artist=True,showmeans=True,labels=short,
                    meanprops=dict(marker='D',markerfacecolor='#182B3A',markeredgecolor='white',markersize=5))
    for patch,color in zip(bp['boxes'],COLORS):patch.set_facecolor(color);patch.set_alpha(.55)
    ax[0].set(title='Solo viajes completados',ylabel='Segundos simulados');ax[0].grid(axis='y')
    for i,v in enumerate(values):
        v=np.sort(v);ax[1].step(v,np.arange(1,len(v)+1)/len(v),where='post',color=COLORS[i],ls='-' if i<2 else '--',label=labels[i])
    ax[1].set(title='Distribución acumulada de llegadas',xlabel='Tiempo (s)',ylabel='Fracción',ylim=(0,1.02));ax[1].legend(fontsize=8);ax[1].grid()
    bars(ax[2],[r['completed']/r['vehicle_count'] for r in runs],'Llegadas por vehículo de la flota','Llegadas / vehículo en %g min'%minutes,fmt='.2f')
    figs.save(fig,'02_tiempos_viaje','La media de llegadas no describe los viajes que no terminaron',
              'Cajas: mediana, cuartiles y extremos; rombo: media. Con mayor carga cambia qué viajes logran llegar.\nLos viajes de una corrida son dependientes. La tasa por vehículo usa toda la flota, incluso vehículos sin llegadas.')

    fig,ax=plt.subplots(1,2,figsize=(15,6.5))
    bottom=np.zeros(4)
    table=[]
    for state,name,color in zip(STATUS,STATUS_NAMES,STATUS_COLORS):
        values=np.array([100*r['statuses'].get(state,0)/r['started'] for r in runs])
        ax[0].bar(range(4),values,bottom=bottom,color=color,label=name,width=.65)
        for i,v in enumerate(values):
            if v>4:ax[0].text(i,bottom[i]+v/2,'%.1f%%'%v,ha='center',va='center',fontsize=9,color='white',fontweight='bold')
        bottom+=values
        table.append([r['statuses'].get(state,0) for r in runs])
    ax[0].set(title='Estado final de todos los intentos de viaje',ylabel='% de intentos iniciados',ylim=(0,100),xticks=range(4),xticklabels=short)
    ax[0].legend(ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.15))
    ax[1].axis('off');ax[1].set_title('Recuentos completos, sin ocultar los fallos')
    tab=ax[1].table(cellText=table+[list(r['started'] for r in runs)],rowLabels=STATUS_NAMES+['TOTAL'],colLabels=short,
                    cellLoc='center',bbox=[.16,.12,.83,.8])
    tab.auto_set_font_size(False);tab.set_fontsize(10)
    for (row,col),cell in tab.get_celld().items():
        cell.set_edgecolor('#CFD8DF')
        if row==0:cell.set_facecolor('#E7EFF4')
    figs.save(fig,'03_estados_viaje','Corte final, bloqueo y ruta rechazada son resultados distintos',
              'Blocked: baja velocidad continua según el detector vigente; puede repetirse en el mismo vehículo. Ruta rechazada: route_failed.\nAborted tiene motivo simulation_end. Las reasignaciones tras fallos aumentan los intentos; no son vehículos nuevos.')

    fig,ax=plt.subplots(2,2,figsize=(13,8.5))
    max_category = np.nanmax([proportions(r, p, 'by_category', base.CATS) for r in runs for p in ('assigned', 'reached')])
    for group,count in enumerate(counts):
        for col,(population,title) in enumerate((('assigned','Asignados'),('reached','Alcanzados'))):
            for offset,i in zip((-.19,.19),(group*2,group*2+1)):
                values=proportions(runs[i],population,'by_category',base.CATS)
                ax[group,col].bar(np.arange(3)+offset,values,width=.36,color=COLORS[i],label=labels[i])
                for x,v in zip(np.arange(3)+offset,values):
                    ax[group,col].text(x, (v if np.isfinite(v) else 0) + 1, base.metric_label(v, '.1f'), ha='center', fontsize=9)
            ax[group,col].set(title='%s · %d vehículos'%(title,count),xticks=range(3),xticklabels=base.CAT_NAMES,ylabel='Porcentaje (%)',ylim=(0,max_category*1.2))
            ax[group,col].legend(fontsize=8);ax[group,col].grid(axis='y');ax[group,col].set_axisbelow(True)
    figs.save(fig,'04_destinos_categorias','Destinos asignados y alcanzados bajo las dos demandas',
              'Asignados incluye decisiones cuyos viajes fallan o quedan al corte. Alcanzados incluye solo llegadas.\nUniformidad entre 42 destinos elegibles no significa 1/3 por categoría; 80/20 son ramas del selector, no categorías.')

    fig,ax=plt.subplots(2,1,figsize=(18,7.5));ids=[d['value'] for d in runs[0]['destinations']['assigned']['by_id']]
    arrays=[np.array([proportions(r,p,'by_id',ids) for r in runs]) for p in ('assigned','reached')]
    for axis,values,title in zip(ax,arrays,('Asignados','Alcanzados')):
        im=axis.imshow(values,aspect='auto',cmap='YlGnBu',vmin=0,vmax=np.nanmax(arrays))
        axis.set(title=title,yticks=range(4),yticklabels=labels,xticks=range(len(ids)),xticklabels=ids)
        axis.tick_params(axis='x',rotation=90,labelsize=8);fig.colorbar(im,ax=axis,pad=.015,label='% de cada población y corrida',fraction=.025)
    figs.save(fig,'05_destinos_detalle','Frecuencias de los 42 destinos',
              'Cada fila con asignaciones o llegadas suma 100 %. Una fila vacía indica que esa población carece de observaciones.')

    fig,ax=plt.subplots(2,2,figsize=(13,8.5))
    for group,count in enumerate(counts):
        for i in (group*2,group*2+1):
            d=series[series.run==runs[i]['run']];x=(d.start_elapsed_s+d.duration_s/2)/60
            ax[0,group].plot(x,d.speed_kmh,color=COLORS[i],label=labels[i],marker='o',ms=3)
            ax[1,group].plot(x,d.low_speed_percent,color=COLORS[i],label='Baja velocidad · '+labels[i].split(' · ')[-1],marker='o',ms=3)
            ax[1,group].plot(x,d.dwell_percent,color=COLORS[i],ls=':',label='Sin viaje activo · '+labels[i].split(' · ')[-1])
        ax[0,group].set(title='%d vehículos · velocidad de presencia'%count,ylabel='km/h',ylim=(0,20));ax[0,group].legend(fontsize=8)
        ax[1,group].set(title='%d vehículos · baja velocidad y fase dwell'%count,ylabel='% de tiempo de presencia',ylim=(0,103));ax[1,group].legend(fontsize=7)
    for axis in ax.flat:axis.grid();axis.set(xlabel='Minutos simulados',xlim=(0,minutes))
    figs.save(fig,'06_velocidad_paradas','Evolución de la velocidad y las detenciones',
              'Baja velocidad < 0,2 m/s. Dwell significa sin viaje activo: incluye espera tras llegar y tras fallos; puede solaparse con baja velocidad.\nVentanas de 60 s. Se conserva el arranque. Una parada aislada no demuestra congestión; no se seleccionan estados estacionarios.')

    fig,ax=plt.subplots(2,3,figsize=(16,9))
    bars(ax[0,0],[r['events']['collision']['observed_callbacks'] for r in runs],'Callbacks brutos de colisión','Callbacks',fmt='.0f')
    bars(ax[0,1],[r['events']['collision']['per_vehicle_km'] for r in runs],'Colisiones por exposición','Callbacks / vehículo-km',fmt='.2f')
    bars(ax[0,2],[e['episodes'] for e in extra],'Episodios descriptivos de contacto','Grupos, no accidentes verificados',fmt='.0f')
    bars(ax[1,0],[r['events']['lane_invasion']['observed_callbacks'] for r in runs],'Invasiones registradas','Callbacks',fmt='.0f')
    bars(ax[1,1],[r['events']['lane_invasion']['per_vehicle_km'] for r in runs],'Invasiones por exposición','Callbacks / vehículo-km',fmt='.3f')
    for i,e in enumerate(events):
        times=e[e.event_type=='collision'].simulation_time_s.to_numpy()-extra[i]['origin_s']
        numbers,edges=np.histogram(times,bins=minute_edges(seconds))
        ax[1,2].plot((edges[:-1]+edges[1:])/120,numbers,color=COLORS[i],ls='-' if i<2 else '--',label=labels[i])
    ax[1,2].set(title='Persistencia de callbacks por minuto',xlabel='Minutos simulados',ylabel='Callbacks en la ventana',xlim=(0,minutes));ax[1,2].legend(fontsize=8);ax[1,2].grid()
    figs.save(fig,'07_incidentes','Incidentes: magnitud, exposición y persistencia',
              'Episodio: mismo par de actores, uniendo callbacks separados hasta 1 s; conserva ambos sensores. Agrupación descriptiva.\nHay contactos con vehículos y objetos estáticos. Un callback no equivale a un accidente ni una invasión implica por sí sola infracción.')

    fig,ax=plt.subplots(1,3,figsize=(16,6))
    for i in (1,3):
        times=np.sort(completed[i].arrival_sim_time_s.to_numpy()-extra[i]['origin_s'])
        n=runs[i]['vehicle_count'];initial=extra[i]['initial_history'];total=extra[i]['final_history']
        x=np.r_[0,times,seconds]/60;y=np.r_[initial,initial+np.arange(1,len(times)+1),total]
        ax[0].step(x,y,where='post',label='%d vehículos: %d → %d'%(n,initial,total),color='#7D58A3' if i==1 else '#278377',lw=2)
        ax[1].step(x,y/n,where='post',label='%d vehículos'%n,color='#7D58A3' if i==1 else '#278377',lw=2)
    ax[0].set(title='Historial total del selector histórico',xlabel='Minutos simulados',ylabel='Visitas iniciales + llegadas');ax[0].legend(fontsize=8);ax[0].grid()
    ax[1].set(title='Historial medio por vehículo',xlabel='Minutos simulados',ylabel='Visitas / vehículo');ax[1].legend();ax[1].grid()
    for x,i in enumerate((1,3)):
        c=extra[i]['selection_counts'];n=sum(c.values());pct=100*c.get('routine',0)/n
        ax[2].bar(x,pct,color='#7D58A3',width=.55);ax[2].bar(x,100-pct,bottom=pct,color='#7EC8BA',width=.55)
        ax[2].text(x,pct/2,'%d rutina\n%.2f %%'%(c.get('routine',0),pct),ha='center',va='center',color='white',fontweight='bold')
        ax[2].text(x,(100+pct)/2,'%d exploración\n%.2f %%'%(c.get('exploration',0),100-pct),ha='center',va='center',fontsize=9)
    ax[2].axhline(80,color='#182B3A',ls='--',lw=1)
    ax[2].set(title='Rama elegida: todas las decisiones',xticks=[0,1],xticklabels=['%d vehículos'%n for n in counts],ylabel='% de decisiones',ylim=(0,105))
    figs.save(fig,'08_historial_ramas','El historial crece con llegadas; la frecuencia de decisiones también cambia',
              'Cada vehículo histórico empieza con 30 visitas. Blocked/ruta rechazada no añaden visitas, pero una reasignación sí cuenta como decisión.\nLa línea discontinua marca la probabilidad 80 %; no exige una cuota exacta. Baseline no usa este bootstrap.','historial')

    fig,ax=plt.subplots(2,3,figsize=(16,9))
    relations=[('density_veh_per_km_lane','speed_kmh','Velocidad-densidad','Densidad (veh/km/carril)','Velocidad espacial (km/h)'),
               ('density_veh_per_km_lane','flow_veh_per_h_lane','Flujo-densidad','Densidad (veh/km/carril)','Flujo (veh/h/carril)'),
               ('flow_veh_per_h_lane','speed_kmh','Velocidad-flujo','Flujo (veh/h/carril)','Velocidad espacial (km/h)')]
    for group,count in enumerate(counts):
        for col,(x,y,title,xlabel,ylabel) in enumerate(relations):
            for i in (group*2,group*2+1):
                d=occupied[occupied.run==runs[i]['run']]
                label = '%s · %d celdas' % (labels[i].split(' · ')[-1], len(d))
                ax[group,col].scatter(d[x],d[y],s=15,alpha=.17,color=COLORS[i],edgecolors='none',rasterized=True,label=label)
                line=guides[(guides.run==runs[i]['run'])&guides.supported]
                for _,part in line.groupby('segment',sort=True):
                    ax[group,col].plot(part[x],part[y],color=COLORS[i],lw=2.3,marker='o',ms=4.5,
                                       markeredgecolor='white',markeredgewidth=.6,zorder=5)
            ax[group,col].set(title='%s · %d vehículos'%(title,count),xlabel=xlabel,ylabel=ylabel,
                              xlim=(0,occupied[x].max()*1.06),ylim=(0,occupied[y].max()*1.1))
            ax[group,col].legend(fontsize=8,loc='upper right');ax[group,col].grid()
    figs.save(fig,'09_flujo_densidad_velocidad','Relaciones de tráfico: puntos observados y líneas guía',
              'Celdas de 50 m y hasta 60 s. Las guías agrupan bandas de 10 veh/km/carril con al menos 10 celdas.\nCada marcador cumple q=k·v. Las bandas sin soporte interrumpen la línea.\nQuedaron fuera de las celdas %s muestras sin proyección sobre un carril de conducción.'%format(sum(r['outside_driving_projection_rows'] for r in derived['runs']),','),'flujo')

    fig,ax=plt.subplots(1,2,figsize=(14,6.5));bg=np.asarray(derived['background_xy'])
    ax[0].scatter(bg[:,0],bg[:,1],s=2,color='#C5CBD1')
    for g in derived['selected_geometry']:
        xy=np.asarray(g['xy']);ax[0].plot(xy[:,0],xy[:,1],color='#2463A6',lw=2)
    ax[0].set(title='Los mismos tramos en ambas demandas',xlabel='x (m)',ylabel='y (m)');ax[0].invert_yaxis();ax[0].set_aspect('equal');ax[0].grid(alpha=.2)
    edges=np.array([0,5,10,20,40,60,100,150,250,500],dtype=float)
    edges=edges[:max(2,np.searchsorted(edges,occupied.density_veh_per_km_lane.max(),side='right')+1)]
    if edges[-1]<occupied.density_veh_per_km_lane.max():edges=np.r_[edges,occupied.density_veh_per_km_lane.max()+1]
    names=['%g-%g'%(a,b) for a,b in zip(edges[:-1],edges[1:])];coverage=[]
    for j,n in enumerate(counts):
        d=occupied[occupied.vehicle_count==n]
        values,_=np.histogram(d.density_veh_per_km_lane,bins=edges)
        ax[1].bar(np.arange(len(values))+(j-.5)*.38,values,width=.36,label='%d vehículos'%n,color=['#7D58A3','#278377'][j])
        for label,num in zip(names,values):coverage.append(dict(vehicle_count=n,density_bin=label,occupied_cells=int(num)))
    ax[1].set(title='Cobertura local por cantidad de vehículos',xlabel='Densidad media (veh/km/carril)',ylabel='Celdas con presencia',xticks=range(len(names)),xticklabels=names);ax[1].legend();ax[1].grid(axis='y');ax[1].set_axisbelow(True)
    pd.DataFrame(coverage).to_csv(out/'density_coverage.csv',index=False)
    figs.save(fig,'10_cobertura_flujo','Ámbito de medición y cobertura de densidades',
              '%d tramos de 50 m; %.1f km-carril. Se excluyen cruces y restos de tramo. Las celdas vacías conservan velocidad indefinida.\nMás vehículos totales no garantiza mayor densidad en cada tramo observado; las celdas no son réplicas independientes.'%(len(derived['selected_geometry']),len(derived['selected_geometry'])*.05),'flujo')

    fig,ax=plt.subplots(2,2,figsize=(13,8.5));outcome_rows=[]
    for group,count in enumerate(counts):
        for i in (group*2,group*2+1):
            arrival=np.sort(completed[i].arrival_sim_time_s.to_numpy()-extra[i]['origin_s'])
            ax[0,group].step(np.r_[0,arrival,seconds]/60,np.r_[0,np.arange(1,len(arrival)+1),len(arrival)],where='post',color=COLORS[i],label=labels[i])
            for status,linestyle in (('blocked','-'),('route_failed',':')):
                ends=trips[i][trips[i].status==status].end_sim_time_s.to_numpy()-extra[i]['origin_s']
                nums,edges=np.histogram(ends,bins=minute_edges(seconds));x=(edges[:-1]+edges[1:])/120
                ax[1,group].plot(x,nums,color=COLORS[i],ls=linestyle,label=labels[i].split(' · ')[-1]+' · '+status)
                outcome_rows.extend(dict(run=runs[i]['run'],vehicle_count=count,scenario=runs[i]['scenario'],status=status,start_elapsed_s=float(t),duration_s=float(end-t),count=int(num)) for t,end,num in zip(edges[:-1],edges[1:],nums))
        ax[0,group].set(title='%d vehículos · llegadas acumuladas'%count,ylabel='Llegadas',ylim=(0,max(1,max(r['completed'] for r in runs))*1.1));ax[0,group].legend(fontsize=8)
        ax[1,group].set(title='%d vehículos · fallos por minuto'%count,ylabel='Terminaciones en la ventana');ax[1,group].legend(fontsize=7)
    for axis in ax.flat:axis.set(xlabel='Minutos simulados',xlim=(0,minutes));axis.grid()
    upper=max(1,max(row['count'] for row in outcome_rows))*1.12
    for axis in ax[1,:]:axis.set_ylim(0,upper)
    pd.DataFrame(outcome_rows).to_csv(out/'outcomes_by_minute.csv',index=False)
    figs.save(fig,'11_evolucion_resultados','Llegadas y fallos a lo largo de la simulación',
              'Una curva de llegadas que se aplana indica pérdida de producción de viajes. Los blocked repetidos no son vehículos distintos.\nEsta figura identifica cuándo investigar; no atribuye el origen del bloqueo a congestión, al controlador o a la planificación por sí sola.')
    half_rows=[]
    for i,r in enumerate(runs):
        d=series[series.run==r['run']]
        midpoint=d.start_elapsed_s+d.duration_s/2
        for half,(lo,hi) in enumerate(((0,seconds/2),(seconds/2,seconds))):
            part=d[(midpoint>=lo)&(midpoint<hi)]
            exposure=part.vehicle_seconds.sum()
            ends=trips[i].end_sim_time_s-extra[i]['origin_s']
            in_half=(ends>=lo)&(ends<(hi if half==0 else hi+1e-3))
            half_rows.append(dict(run=r['run'],vehicle_count=r['vehicle_count'],scenario=r['scenario'],half=half+1,
                start_s=lo,end_s=hi,observed_start_s=part.start_elapsed_s.min(),
                observed_end_s=(part.start_elapsed_s+part.duration_s).max(),vehicle_seconds=exposure,
                speed_kmh=3.6*part.distance_m.sum()/exposure if exposure else np.nan,
                low_speed_percent=(part.low_speed_percent*part.vehicle_seconds).sum()/exposure if exposure else np.nan,
                completed=int((in_half&(trips[i].status=='completed')).sum()),
                blocked=int((in_half&(trips[i].status=='blocked')).sum())))
    halves=pd.DataFrame(half_rows);halves.to_csv(out/'half_comparison.csv',index=False)
    fig,ax=plt.subplots(2,2,figsize=(13,9))
    for axis,key,title,ylabel,fmt in zip(ax.flat,
            ('speed_kmh','low_speed_percent','completed','blocked'),
            ('Velocidad de presencia','Tiempo a baja velocidad','Llegadas durante cada mitad','Terminaciones blocked'),
            ('km/h','% de exposición','Llegadas','Intentos'),('.2f','.1f','.0f','.0f')):
        for h,offset in ((1,-.19),(2,.19)):
            vals=halves[halves.half==h][key].to_numpy()
            axis.bar(np.arange(4)+offset,vals,width=.36,color=COLORS,alpha=.5 if h==1 else 1,
                     hatch='//' if h==1 else None,label='%g-%g min'%((h-1)*minutes/2,h*minutes/2))
            top=max(1,halves[key].max())
            for x,v in zip(np.arange(4)+offset,vals):
                axis.text(x, (v if np.isfinite(v) else 0) + .025*top, base.metric_label(v,fmt), ha='center', fontsize=9)
        axis.set(title=title,ylabel=ylabel,xticks=range(4),xticklabels=short,ylim=(0,top*1.28))
        axis.legend(fontsize=8,ncol=2,loc='upper right');axis.grid(axis='y');axis.set_axisbelow(True)
    figs.save(fig,'12_comparacion_mitades','Primera y segunda mitad de las mismas corridas',
              'Las ventanas de hasta 60 s se asignan por su centro y se ponderan por exposición. N/D indica una mitad sin exposición medida.\nLas llegadas y los cierres por bloqueo se asignan por su instante de terminación.')
    if args.compare_data:
        from scripts.analysis.compare_repetitions import append_comparison
        append_comparison(out,args.compare_data,figs,base,review)
    figs.pdf.close()
    export(out,figs.items,runs,extra,derived,review,occupied,context)


def export(out,items,runs,extra,derived,review,occupied,context):
    """Save the figure gallery, supporting tables, and source manifest for the demand comparison."""
    campaign=Path(derived['campaign']).parent
    for name in ('summary.csv','destinations.csv'):shutil.copyfile(campaign/'metrics'/name,out/name)
    counts=sorted({r['vehicle_count'] for r in runs});seed=runs[0]['seed']
    cards=[]
    for item in items:
        cards.append('<section class="card" data-group="{group}"><h2>{title}</h2><p>{note}</p><a href="{name}.png" target="_blank"><img src="{name}.png" alt="{title}" loading="lazy"></a><p><a href="{name}.png" download>PNG</a> · <a href="{name}.svg" download>SVG vectorial</a></p></section>'.format(**{k:html.escape(v) for k,v in item.items()}))
    larger_fleet = [run for run in runs if run['vehicle_count'] == counts[-1]]
    warning = ('En los dos casos de %d vehículos se registraron %d cierres por bloqueo, '
               '%d rutas rechazadas y %d avisos del sensor de colisión.') % (
        counts[-1], sum(run['statuses'].get('blocked', 0) for run in larger_fleet),
        sum(run['statuses'].get('route_failed', 0) for run in larger_fleet),
        sum(run['events']['collision']['observed_callbacks'] for run in larger_fleet))
    page='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TrafficIA · demandas 20 y 100</title><style>
    *{box-sizing:border-box}body{margin:0;background:#eef2f5;color:#182b3a;font:16px/1.55 system-ui,sans-serif}header{background:#142c3e;color:white;padding:35px 5vw}h1{font-size:36px;margin:0 0 12px}header p{color:#d3e1eb;max-width:1050px}main{max-width:1450px;margin:auto;padding:24px}.card{background:white;border-radius:12px;padding:24px;margin:24px 0}.card img{width:100%;height:auto}.card p{white-space:pre-line;color:#475569}nav{position:sticky;top:0;background:#eef2f5ef;padding:12px 0;display:flex;gap:10px;flex-wrap:wrap}button,nav a{border:1px solid #b9c9d6;border-radius:7px;background:white;padding:10px;color:#234968;text-decoration:none;font:inherit;cursor:pointer}button.active{background:#2463a6;color:white}a{color:#2463a6}.note{padding:18px;border-left:4px solid #d98420;background:#fff6df}section[hidden]{display:none}</style>
    <header><h1>20 y 100 vehículos: qué cambió</h1><p>Resultados de la campaña · versión con líneas guía · '''+datetime.now().strftime('%Y-%m-%d')+'''.</p><p>'''+html.escape(context)+'''</p></header><main><nav><button class="active" data-filter="all">Todas</button><button data-filter="objetivos">Objetivos e incidencias</button><button data-filter="flujo">Flujo y densidad</button><button data-filter="historial">Historial</button><a href="graficas_campana.pdf">PDF completo</a><a href="informe_graficas.md">Método y resultados</a></nav><div class="note">'''+html.escape(warning)+'''</div>'''+''.join(cards)+'''<p>Datos originales conservados. Consulta CSV derivados y manifiestos junto a esta galería.</p></main><script>document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.card').forEach(c=>c.hidden=b.dataset.filter!=='all'&&c.dataset.group!==b.dataset.filter)});</script></html>'''
    (out/'index.html').write_text(page,encoding='utf8')
    report=['# Gráficas de dos demandas - '+campaign.name,'',context,'',warning,'',
        '## Resultados auditados','',
        '| Vehículos | Selector | Llegadas | Media completa (s) | Velocidad (km/h) | Blocked | Ruta rechazada | Corte final | Colisiones (callbacks) | Episodios descriptivos | Invasiones |',
        '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r,e in zip(runs,extra):
        report.append('| %d | %s | %d | %s | %s | %d | %d | %d | %d | %d | %d |'%(r['vehicle_count'],r['scenario'],r['completed'],base.metric_label(r['travel_time']['mean_s'],'.2f'),base.metric_label(r['speed']['mean_kmh'],'.2f'),r['statuses'].get('blocked',0),r['statuses'].get('route_failed',0),r['statuses'].get('aborted',0),e['raw_callbacks'],e['episodes'],r['events']['lane_invasion']['observed_callbacks']))
    report += ['', '## Primera y segunda mitad', '',
        'Cada corrida se divide por su duración simulada. La velocidad y el tiempo a baja velocidad se ponderan por exposición en ventanas asignadas por su centro. N/D indica una mitad sin exposición medida. half_comparison.csv conserva los límites observados. Las llegadas y los bloqueos se asignan por el instante de terminación.', '',
        '| Vehículos | Selector | Mitad | Velocidad (km/h) | Baja velocidad (%) | Llegadas | Blocked |',
        '|---:|---|---:|---:|---:|---:|---:|']
    for row in pd.read_csv(out/'half_comparison.csv').to_dict('records'):
        report.append('| %d | %s | %d | %s | %s | %d | %d |'%(row['vehicle_count'],row['scenario'],row['half'],base.metric_label(row['speed_kmh'],'.3f'),base.metric_label(row['low_speed_percent'],'.2f'),row['completed'],row['blocked']))
    report += ['', 'Las comparaciones entre selectores se hacen dentro de cada cantidad. Se conservan semilla, clima, controlador, flota y spawns comunes. Una semilla no estima variación entre réplicas ni demuestra mejora causal del selector.',
        '', '## Interpretación y objetivos','',
        '- Objetivo 1: primer contraste observado de dos cantidades simultáneas candidatas. No son caudales de entrada; los valores definitivos requieren evaluar la calidad del régimen observado.',
        '- Objetivo 2: agentes simultáneos con historiales crecientes. Histórico conserva 30 visitas iniciales por vehículo; baseline registra nuevas llegadas sin usar ese bootstrap para elegir.',
        '- Objetivo 3: destinos asignados/alcanzados, tiempo de completados, velocidad de presencia y eventos por vehículo-km. Los incompletos se muestran aparte: no se ocultan al interpretar medias.',
        '- Para comparar las flotas, lee la velocidad de presencia junto a las llegadas por vehículo, los intentos pendientes al corte y los motivos de cierre.',
        '- Blocked usa el detector vigente de baja velocidad continua. Sus reasignaciones multiplican decisiones e intentos; cada grupo no equivale a un nuevo vehículo. Los route_failed llevan motivo route_planning_rejected, cuya causa concreta requiere diagnóstico posterior.',
        '- Los eventos incluyen contactos con vehículos y objetos estáticos. Episodios: par de actor IDs sin distinguir emisor, separación consecutiva máxima de 1 s. Agrupación descriptiva, no clasificación de accidentes. Se conserva el conteo bruto y se señalan IDs ambiguos en chart_input_review.json.',
        '- La media de completados está condicionada a lograr una llegada: no representa los viajes bloqueados ni el tiempo que habrían tardado los cortados. No comparar sus cajas como si fueran réplicas independientes.',
        '', '## Cómo leer las líneas guía','',
        'Los puntos pequeños siguen siendo todas las celdas ocupadas originales. La línea y sus círculos resumen bandas fijas de densidad de 10 veh/km/carril. Se suman tiempo vehicular S, distancia D y área espacio-temporal A=L*T: k=1000*sum(S)/sum(A), q=3600*sum(D)/sum(A), v=3.6*sum(D)/sum(S). Se conserva q=k*v en cada círculo; v no es una media aritmética de velocidades de celda.',
        'Se dibuja una banda si contiene al menos diez celdas. Se unen solo bandas consecutivas con soporte; los huecos rompen la guía. Ancho y umbral son decisiones transparentes de visualización, no criterios de suficiencia estadística. Los puntos de bandas escasas no se borran. flow_guides.csv guarda recuentos y todos los resúmenes, también los no dibujados; guide_method.json conserva el método. No hay extrapolación, ajuste a Greenshields ni estimación de capacidad.',
        'En velocidad-flujo la conexión sigue densidad creciente, no flujo creciente: q bajo puede corresponder a pocos vehículos rápidos o a muchos casi parados. Los mismos círculos se proyectan en los tres paneles. La igualdad q=k*v se garantiza en esos círculos, no en cada punto de los segmentos rectos que solo los unen visualmente.',
        'La hipótesis lineal de Greenshields relaciona velocidad y densidad mediante v=vf*(1-k/kj). Al sustituirla en q=k*v se obtiene una parábola. Las guías de esta campaña se calculan directamente sobre las celdas observadas.',
        'FHWA distingue la identidad entre variables, la forma funcional elegida y la calibración de estados estacionarios. En Town01 se mezclan calles, fases semafóricas, esperas, contactos y transiciones. Una curva idealizada no debería esperarse de toda esa nube. [FHWA: variables, modelos y calibración](https://ops.fhwa.dot.gov/publications/weatherempirical/sect3.htm).',
        'Para estudiar la capacidad de un tramo haría falta identificar estados comparables y distinguir semáforos, esperas en destino y contactos en la vía.',
        'Rutina histórica observada: '+ '; '.join('%d vehículos: %.2f %%'%(e['vehicle_count'],100*e['selection_counts'].get('routine',0)/sum(e['selection_counts'].values())) for e in extra if e['scenario']=='history_80_20')+'. Son ramas de decisiones, no proporciones obligatorias de llegadas, categorías o densidades. Su funcionamiento no prueba por sí solo la validez del diagrama fundamental.',
        '', '## Método de flujo, densidad y velocidad','',
        'Se reutiliza la selección geométrica previa: carriles driving rectos fuera de cruces, ancho/offset constante y una laneSection. Solo bloques completos de 50 m y ventanas de 60 s; última ventana parcial. API de mapa OpenDRIVE offline, sin cliente ni simulación nueva.',
        'S es tiempo vehicular (s), D distancia longitudinal absoluta (m), L longitud (m) y T ventana (s): k=1000*S/(L*T), q=3600*D/(L*T), v=3.6*D/S. Unidades: veh/km/carril, veh/h/carril, km/h. Se verifica q=k*v; la identidad no calibra una curva.',
        'Se interpola entre frames consecutivos y se divide cada intervalo en fronteras espacio-temporales. No se inventa el primer intervalo de 0.05 s por vehículo. Las transiciones entre road/lane no se interpolan en s y se cuantifican como incertidumbre. Filas fuera de la proyección driving quedan fuera de las celdas, pero permanecen en los registros y las series globales.',
        'Se incluyen paradas y dwell. La fase dwell significa ausencia de viaje activo: incluye pausas tras llegada y tras intentos fallidos, no solo estancia en destino. Puede solaparse con baja velocidad y sus porcentajes no se suman. Celdas vacías: k=q=0 y velocidad indefinida. Se mezclan lugares/fases semafóricas y no se seleccionan estados estacionarios. Máximos muestrales no son capacidad, ni se impone una parábola para imitar el esquema teórico.',
        'El diagrama es local y cubre parte de Town01, no un diagrama macroscópico de toda la ciudad. Cien vehículos globales pueden acumularse en otros tramos y producir menos celdas con presencia en el ámbito seleccionado.',
        '', '## Cobertura numérica','',
        '| Vehículos | Selector | Filas | Celdas con presencia | Fuera de proyección | Exposición inicial no observada (veh-s) |',
        '|---:|---|---:|---:|---:|---:|']
    for r in derived['runs']:
        report.append('| %d | %s | %d | %d | %d | %.3f |'%(r['vehicle_count'],r['scenario'],r['rows'],r['nonempty_cells'],r['outside_driving_projection_rows'],r['initial_unobserved_vehicle_seconds']))
    report += ['', 'Se validaron %d archivos de salida contra los hashes guardados por la campaña, además de la instantánea de fuentes. Sin errores en auditorías conservadas ni en métricas recalculadas; parejas comparables.'%review['verified_output_files'],
        'Las gráficas se derivan leyendo el CSV por bloques, sin retener millones de filas a la vez. No se cambian controlador, simulación ni logs originales.',
        '', '## Reproducción','', '```powershell',
        '.\\carla-env\\Scripts\\python.exe scripts/figures/build_plot_data.py --campaign '+str(Path(derived['campaign']).relative_to(ROOT)).replace('\\','/')+' --output data/output/NUEVA_CARPETA',
        '.\\carla-env\\Scripts\\python.exe scripts/figures/verify_plot_inputs.py --campaign '+str(Path(derived['campaign']).relative_to(ROOT)).replace('\\','/')+' --output data/output/NUEVA_CARPETA',
        '.\\carla-env\\Scripts\\python.exe scripts/figures/plot_demand.py --data data/output/NUEVA_CARPETA',
        '```','', 'Usar carla-env y Town01.xodr local; CARLA no necesita estar abierto. Primera orden exige carpeta nueva. Figuras PNG/SVG, PDF y galería HTML se escriben únicamente en derivados.', '', '## Láminas','']
    for item in items:report+=['### '+item['title'],'',item['note'],'','!['+item['title']+']('+item['name']+'.png)','']
    (out/'informe_graficas.md').write_text('\n'.join(report),encoding='utf8')
    sources=['scripts/figures/plot_demand.py','scripts/figures/plot_mobility.py','scripts/figures/verify_plot_inputs.py','src/analysis/incident_analysis.py','src/analysis/traffic_flow_analysis.py']
    if (out/'repeat_comparison.json').exists():
        sources.append('scripts/analysis/compare_repetitions.py')
        with (out/'informe_graficas.md').open('a',encoding='utf8') as stream:
            stream.write('\n\n[Comparación detallada con la primera campaña](comparacion_repeticiones.md).\n')
    manifest=dict(figures=items,campaign=derived['campaign'],source_sha256={name:sha(ROOT/name) for name in sources},
                  input_sha256={name:sha(out/name) for name in ('derivation_manifest.json','chart_input_review.json','flow_cells.csv','time_series.csv')},
                  guide_sha256={name:sha(out/name) for name in ('flow_guides.csv','guide_method.json')})
    if (out/'repeat_comparison.json').exists():
        manifest['comparison_sha256']={name:sha(out/name) for name in ('repeat_comparison.json','repeat_comparison.csv','comparacion_repeticiones.md')}
    (out/'figures_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
    print('EXPORTED',len(items),'figures PNG/SVG, PDF and HTML:',out.resolve())


if __name__=='__main__':main()
