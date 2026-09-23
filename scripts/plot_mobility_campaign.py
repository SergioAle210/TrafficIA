"""Export graduation-metric figures and exploratory traffic diagrams from offline data."""
import argparse
import hashlib
import html
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/output/.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

COLORS=['#2463A6','#D98420','#2463A6','#D98420']
SHORT=['Aleatorio\n210','Historial\n210','Aleatorio\n109','Historial\n109']
LONG=['Aleatorio · 210','Historial 80/20 · 210','Aleatorio · 109','Historial 80/20 · 109']
CATS=['residential','services_leisure','work_education']
CAT_NAMES=['Residencia','Servicios / ocio','Trabajo / educación']
CAT_COLORS=['#508D86','#8A71B3','#DDA94C']


def read_json(p):return json.loads(p.read_text(encoding='utf8'))


def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                         'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.titlepad':12,'figure.facecolor':'white','axes.facecolor':'white',
                         'text.color':'#182B3A','axes.labelcolor':'#334155','axes.edgecolor':'#94A3B8',
                         'grid.color':'#CBD5E1','grid.alpha':.45,'svg.fonttype':'none'})


def bars(ax,values,title,ylabel,fmt='.1f',colors=COLORS):
    ax.bar(range(4),values,color=colors,width=.65)
    ax.scatter(range(4),values,color=colors,s=15,zorder=3)
    ax.set(xticks=range(4),xticklabels=SHORT,title=title,ylabel=ylabel)
    ax.grid(axis='y');ax.set_axisbelow(True)
    maximum=max(values) if max(values)>0 else 1
    ax.set_ylim(0,maximum*1.24)
    for x,v in enumerate(values):ax.text(x,v+maximum*.035,format(v,fmt),ha='center',fontsize=10,fontweight='bold')


class Figures:
    def __init__(self,out):
        self.out=out;self.items=[];self.pdf=PdfPages(out/'graficas_campana.pdf')
    def save(self,fig,name,title,note,group='objetivos'):
        fig.suptitle(title,fontsize=17,fontweight='bold',x=.04,ha='left',y=.985)
        fig.text(.04,.018,note,fontsize=9,color='#475569',va='bottom')
        fig.tight_layout(rect=(.015,.075,.995,.925))
        fig.savefig(self.out/(name+'.png'),dpi=170)
        fig.savefig(self.out/(name+'.svg'))
        self.pdf.savefig(fig)
        plt.close(fig);self.items.append(dict(name=name,title=title,note=note,group=group))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,required=True)
    args=parser.parse_args();out=args.data;style()
    derived=read_json(out/'derivation_manifest.json');campaign=Path(derived['campaign']).parent
    analysis=read_json(campaign/'metrics/analysis.json');runs=analysis['runs']
    if [(r['seed'],r['scenario'],r['vehicle_count']) for r in runs]!=[(s,m,20) for s in (210,109) for m in ('random_baseline','history_80_20')]:
        raise ValueError('This report layout is defined for the four 20-vehicle runs with seeds 210/109, in paired order.')
    extended=read_json(campaign/'extended_review.json')['runs']
    incident=read_json(campaign/'incident_review.json')['episodes']
    paths=[ROOT/'data/output'/r['run'] for r in runs]
    trips=[pd.read_csv(p/'trips_log.csv') for p in paths]
    completed=[t[t.status=='completed'] for t in trips]
    flow=pd.read_csv(out/'flow_cells.csv');series=pd.read_csv(out/'time_series.csv')
    figs=Figures(out)

    fig,axes=plt.subplots(2,2,figsize=(13,9))
    bars(axes[0,0],[r['travel_time']['mean_s'] for r in runs],'Tiempo medio de viaje completado','Segundos simulados')
    bars(axes[0,1],[r['speed']['mean_kmh'] for r in runs],'Velocidad media durante presencia','km/h',fmt='.2f')
    bottom=np.zeros(4)
    for cat,name,color in zip(CATS,CAT_NAMES,CAT_COLORS):
        values=np.array([next(d['proportion'] for d in r['destinations']['assigned']['by_category'] if d['value']==cat)*100 for r in runs])
        axes[1,0].bar(range(4),values,bottom=bottom,color=color,label=name,width=.65)
        for i,v in enumerate(values):axes[1,0].text(i,bottom[i]+v/2,'%.1f%%'%v,ha='center',va='center',fontsize=9,color='white',fontweight='bold')
        bottom+=values
    axes[1,0].set(title='Destinos asignados por categoría',ylabel='% de asignaciones',ylim=(0,105),xticks=range(4),xticklabels=SHORT)
    axes[1,0].legend(ncol=3,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.15))
    bars(axes[1,1],[r['events']['collision']['per_vehicle_km'] for r in runs],'Colisiones: tasa de callbacks brutos','Callbacks / vehículo-km',fmt='.3f')
    axes[1,1].text(.97,.90,'Invasiones: 0 en las cuatro corridas',ha='right',transform=axes[1,1].transAxes,fontsize=9)
    figs.save(fig,'01_resumen_objetivos','Las cuatro métricas del objetivo específico 3',
              'Town01 · 20 vehículos · 1.800 s por corrida · semillas 210 y 109. Cada barra es una corrida; no son intervalos de confianza.\nEl tiempo usa solo llegadas; la velocidad incluye detenciones y esperas. Los callbacks no equivalen a accidentes independientes.')

    fig,axes=plt.subplots(1,3,figsize=(16,5.8))
    values=[t.travel_time_s.to_numpy() for t in completed]
    bp=axes[0].boxplot(values,patch_artist=True,showmeans=True,labels=SHORT,
                      meanprops=dict(marker='D',markerfacecolor='#182B3A',markeredgecolor='white',markersize=5))
    for patch,color in zip(bp['boxes'],COLORS):patch.set_facecolor(color);patch.set_alpha(.55)
    axes[0].set(title='Distribución de viajes completados',ylabel='Segundos simulados');axes[0].grid(axis='y')
    for i,a in enumerate(values):
        a=np.sort(a);axes[1].step(a,np.arange(1,len(a)+1)/len(a),where='post',color=COLORS[i],ls='-' if i<2 else '--',label=LONG[i])
    axes[1].set(title='Distribución acumulada',xlabel='Tiempo de viaje completado (s)',ylabel='Fracción de llegadas',ylim=(0,1.02));axes[1].legend(fontsize=8);axes[1].grid()
    bars(axes[2],[100*r['completed']/r['started'] for r in runs],'Viajes completados / iniciados','%',fmt='.1f')
    axes[2].set_ylim(0,108)
    for i,r in enumerate(runs):axes[2].text(i,5,'%d / %d\n%d al corte'%(r['completed'],r['started'],r['incomplete_count']),ha='center',color='white',fontsize=9)
    figs.save(fig,'02_tiempos_viaje','Tiempos de viaje y viajes que quedaron al corte',
              'Cajas: mediana, cuartiles y valores extremos; rombo: media. No son incertidumbre entre réplicas.\n783 llegadas; 78 viajes activos cortados a los 1.800 s. Sus tiempos parciales no se mezclan con tiempos de llegada completos.')

    fig,axes=plt.subplots(2,2,figsize=(13,8.5))
    for si,seed in enumerate((210,109)):
        for pi,(population,title) in enumerate((('assigned','Asignados'),('reached','Alcanzados'))):
            ax=axes[si,pi]
            for offset,i in zip((-.19,.19),(si*2,si*2+1)):
                values=[next(d['proportion'] for d in runs[i]['destinations'][population]['by_category'] if d['value']==cat)*100 for cat in CATS]
                ax.bar(np.arange(3)+offset,values,width=.36,color=COLORS[i],label=LONG[i])
                for x,v in zip(np.arange(3)+offset,values):ax.text(x,v+1,'%.1f'%v,ha='center',fontsize=9)
            ax.set(title='%s · semilla %d'%(title,seed),xticks=range(3),xticklabels=CAT_NAMES,ylabel='Porcentaje (%)',ylim=(0,65));ax.grid(axis='y');ax.set_axisbelow(True);ax.legend(fontsize=9)
    figs.save(fig,'03_destinos_categorias','Distribución de destinos: tres categorías, dos poblaciones',
              'Asignados: todas las decisiones, incluidos viajes sin completar. Alcanzados: solo llegadas.\nAleatorio significa uniforme entre destinos elegibles, no 1/3 por categoría. El catálogo contiene 18 / 18 / 6 destinos.')

    fig,axes=plt.subplots(2,1,figsize=(18,7.5))
    ids=[d['value'] for d in runs[0]['destinations']['assigned']['by_id']]
    arrays=[np.array([[next(d['proportion'] for d in r['destinations'][p]['by_id'] if d['value']==identifier)*100 for identifier in ids] for r in runs]) for p in ('assigned','reached')]
    limit=max(a.max() for a in arrays)
    for ax,a,title in zip(axes,arrays,('Destinos asignados','Destinos alcanzados')):
        im=ax.imshow(a,aspect='auto',cmap='YlGnBu',vmin=0,vmax=limit)
        ax.set(title=title,yticks=range(4),yticklabels=LONG,xticks=range(len(ids)),xticklabels=ids)
        ax.tick_params(axis='x',rotation=90,labelsize=8)
        fig.colorbar(im,ax=ax,pad=.015,label='% dentro de cada corrida y población',fraction=.025)
    figs.save(fig,'04_destinos_detalle','Frecuencias de los 42 destinos',
              'La escala de color es común. Cada fila suma 100 %; los ceros se conservan. Las frecuencias por identificador y categoría están en destinations.csv.')

    # Remaining figures and artifact export follow below.
    finish_figures(figs,out,derived,campaign,runs,extended,incident,trips,completed,flow,series)


def finish_figures(figs,out,derived,campaign,runs,extended,incident,trips,completed,flow,series):
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    for si,seed in enumerate((210,109)):
        for i in (si*2,si*2+1):
            d=series[series.run==runs[i]['run']]
            x=(d.start_elapsed_s+d.duration_s/2)/60
            axes[0,si].plot(x,d.speed_kmh,color=COLORS[i],label=LONG[i],marker='o',ms=3)
            axes[1,si].plot(x,d.low_speed_percent,color=COLORS[i],label=LONG[i],marker='o',ms=3)
        axes[0,si].set(title='Semilla %d · velocidad'%seed,ylabel='km/h',ylim=(0,20));axes[0,si].legend(fontsize=9)
        axes[1,si].set(title='Semilla %d · tiempo a baja velocidad'%seed,ylabel='% de tiempo de presencia',ylim=(0,75))
    for ax in axes.flat:ax.grid();ax.set(xlabel='Minutos simulados',xlim=(0,30))
    figs.save(fig,'05_velocidad_paradas','Evolución temporal de la velocidad y las detenciones',
              'Ventanas de 60 s; velocidad = distancia / tiempo de presencia. Se incluye la espera en destino.\nMenos de 0,2 m/s no significa automáticamente congestión: incluye semáforos, interacciones y esperas normales.')

    fig,axes=plt.subplots(2,2,figsize=(13,8.5))
    counts=[r['events']['collision']['observed_callbacks'] for r in runs]
    bars(axes[0,0],counts,'Callbacks brutos de colisión','Callbacks',fmt='.0f')
    bars(axes[0,1],[r['events']['collision']['per_vehicle_km'] for r in runs],'Tasa por distancia de presencia','Callbacks / vehículo-km',fmt='.3f')
    episodes=[sum(e['run']==r['run'] for e in incident) for r in runs]
    bars(axes[1,0],episodes,'Episodios descriptivos de contacto','Episodios',fmt='.0f');axes[1,0].set_ylim(0,1.5)
    for i,r in enumerate(runs):
        es=[e for e in incident if e['run']==r['run']]
        if not es:axes[1,1].text(1,i,'Sin eventos',va='center',fontsize=9,color='#64748B')
        for e in es:
            x=e['first_elapsed_s']/60
            axes[1,1].scatter([x],[i],s=100,marker='X',color=COLORS[i],zorder=3)
            axes[1,1].annotate('%d callbacks · %.2f s'%(e['raw_callbacks'],e['span_s']),(x,i),xytext=(-6,14) if x>20 else (8,14),textcoords='offset points',ha='right' if x>20 else 'left',fontsize=9)
    axes[1,1].set(title='Momento de los dos contactos',xlabel='Minutos simulados',yticks=range(4),yticklabels=LONG,xlim=(0,30),ylim=(-.6,3.6));axes[1,1].grid(axis='x')
    figs.save(fig,'06_incidentes','Incidentes: distinguir persistencia de frecuencia',
              'Invasiones: cero en las cuatro corridas (conteo y tasas = 0). Colisiones: 524 callbacks, concentrados en dos contactos.\nEpisodio descriptivo: mismo par, uniendo callbacks con separaciones de hasta 1 s; conserva ambos sensores. No sustituye la métrica original.')

    fig,axes=plt.subplots(1,2,figsize=(13,5.8))
    for i,color in ((1,'#7D58A3'),(3,'#278377')):
        origin=trips[i].departure_sim_time_s.min()
        arrivals=np.sort(completed[i].arrival_sim_time_s.to_numpy()-origin)
        axes[0].step(np.r_[0,arrivals,1800]/60,np.r_[600,600+np.arange(1,len(arrivals)+1),600+len(arrivals)],where='post',label='Semilla %d: %d visitas'%(runs[i]['seed'],600+len(arrivals)),color=color,lw=2)
    axes[0].set(title='Historial acumulado de los veinte vehículos',xlabel='Minutos simulados',ylabel='Visitas iniciales + llegadas',xlim=(0,30));axes[0].legend();axes[0].grid()
    for x,i in enumerate((1,3)):
        c=Counter(trips[i].selection_class);n=sum(c.values());routine=100*c['routine']/n
        axes[1].bar(x,routine,color='#7D58A3',width=.55)
        axes[1].bar(x,100-routine,bottom=routine,color='#7EC8BA',width=.55)
        axes[1].text(x,routine/2,'%d rutina\n%.2f %%'%(c['routine'],routine),ha='center',va='center',color='white',fontweight='bold')
        axes[1].text(x,(100+routine)/2,'%d exploración\n%.2f %%'%(c['exploration'],100-routine),ha='center',va='center',fontsize=9)
    axes[1].axhline(80,color='#182B3A',ls='--',lw=1,label='Probabilidad de rutina: 80 %')
    axes[1].set(title='Rama elegida en todas las decisiones',xticks=[0,1],xticklabels=['Semilla 210','Semilla 109'],ylabel='% de decisiones',ylim=(0,115));axes[1].legend(loc='upper center',fontsize=9)
    figs.save(fig,'07_historial_ramas','El historial sí crece; 80/20 es una probabilidad',
              'Cada corrida histórica empieza con 30 visitas por vehículo (600 en total). Solo una llegada añade una visita.\nRutina/exploración son ramas del selector; no son categorías de destino ni una cuota exacta que deba cumplirse en cada corrida.','historial')

    fig,axes=plt.subplots(2,3,figsize=(16,9))
    occupied=flow[flow.vehicle_seconds>0]
    relations=[('density_veh_per_km_lane','speed_kmh','Velocidad–densidad','Densidad (veh/km/carril)','Velocidad espacial (km/h)'),
               ('density_veh_per_km_lane','flow_veh_per_h_lane','Flujo–densidad','Densidad (veh/km/carril)','Flujo espacio-temporal (veh/h/carril)'),
               ('flow_veh_per_h_lane','speed_kmh','Velocidad–flujo','Flujo espacio-temporal (veh/h/carril)','Velocidad espacial (km/h)')]
    for si,seed in enumerate((210,109)):
        for col,(x,y,title,xlab,ylab) in enumerate(relations):
            ax=axes[si,col]
            for i in (si*2,si*2+1):
                d=occupied[occupied.run==runs[i]['run']]
                ax.scatter(d[x],d[y],s=12,alpha=.35,color=COLORS[i],label=('Aleatorio' if i%2==0 else 'Historial 80/20')+' · n=%d'%len(d),edgecolors='none',rasterized=True)
            ax.set(title=title+' · %d'%seed,xlabel=xlab,ylabel=ylab,xlim=(0,occupied[x].max()*1.06),ylim=(0,occupied[y].max()*1.10));ax.grid();ax.legend(fontsize=8,loc='upper right')
    figs.save(fig,'08_flujo_densidad_velocidad','Las relaciones de tu imagen, con observaciones de las corridas',
              'Cada punto: un tramo recto de un carril (50 m) y una ventana de 60 s; última ventana de 59,95 s. 38 tramos, 2.458 celdas con presencia.\nNubes exploratorias sin ajuste: semáforos, destinos y diferencias entre tramos impiden interpretar automáticamente una rama como saturación.','flujo')

    fig,axes=plt.subplots(1,2,figsize=(13,6.5))
    bg=np.asarray(derived['background_xy']);axes[0].scatter(bg[:,0],bg[:,1],s=2,color='#C5CBD1')
    for g in derived['selected_geometry']:
        xy=np.asarray(g['xy']);axes[0].plot(xy[:,0],xy[:,1],color='#2463A6',lw=2)
    axes[0].set(title='Ámbito de medición local en Town01',xlabel='x (m)',ylabel='y (m)');axes[0].invert_yaxis();axes[0].set_aspect('equal');axes[0].grid(alpha=.2)
    d=occupied.copy();k=d.density_veh_per_km_lane
    edges=[0,5,10,15,20,30,40,50,70];labels=['0–5','5–10','10–15','15–20','20–30','30–40','40–50','50–70']
    bin_=pd.cut(k,edges,labels=labels,include_lowest=True);counts=bin_.value_counts(sort=False)
    axes[1].bar(range(len(counts)),counts.values,color='#508D86')
    for x,n in enumerate(counts.values):axes[1].text(x,n+10,str(n),ha='center',fontsize=9)
    axes[1].set(title='Cobertura de densidades locales',xlabel='Densidad media de la celda (veh/km/carril)',ylabel='Celdas con presencia',xticks=range(len(labels)),xticklabels=labels);axes[1].grid(axis='y');axes[1].set_axisbelow(True)
    figs.save(fig,'09_cobertura_flujo','Dónde y con qué cobertura se construyeron los puntos',
              'Azul: 38 tramos rectos de 50 m (1,9 km-carril); gris: resto del mapa. Cruces y restos de tramo quedan fuera de esta medición.\nLas celdas vacías se conservan en flow_cells.csv con velocidad indefinida. La nube mezcla lugares/períodos y no equivale a réplicas independientes.','flujo')
    figs.pdf.close()
    export_gallery(out,figs.items,runs,derived,campaign)


def export_gallery(out,items,runs,derived,campaign):
    cells=pd.read_csv(out/'flow_cells.csv');occupied=cells[cells.vehicle_seconds>0]
    for name in ('summary.csv','destinations.csv'):
        shutil.copyfile(campaign/'metrics'/name,out/name)
    cards=[]
    for item in items:
        cards.append('<section class="card" data-group="{group}" id="{name}"><h2>{title}</h2><p>{note}</p>'
                     '<a href="{name}.png" target="_blank"><img src="{name}.png" alt="{title}" loading="lazy"></a>'
                     '<div class="links"><a href="{name}.png" download>PNG</a><a href="{name}.svg" download>SVG vectorial</a></div></section>'.format(**{k:html.escape(v) for k,v in item.items()}))
    page='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TrafficIA · gráficas de la campaña de veinte</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef2f5;color:#182b3a;font:16px/1.55 system-ui,sans-serif}
header{background:#142c3e;color:white;padding:40px max(5vw,20px)}header p{max-width:960px;color:#d3e1eb}h1{font-size:clamp(27px,4vw,44px);line-height:1.12;margin:0 0 18px}
main{max-width:1450px;margin:auto;padding:24px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:22px;position:sticky;top:0;background:#eef2f5ee;padding:12px 0;z-index:2}
button,.download{border:1px solid #b9c9d6;background:white;border-radius:7px;padding:10px 15px;color:#234968;cursor:pointer;text-decoration:none;font:inherit}button.active{background:#2463a6;color:white}
.card{background:white;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 3px 14px #142c3e0d}.card h2{font-size:23px;margin:0 0 8px}.card p{color:#536474;white-space:pre-line;max-width:1100px}.card img{display:block;width:100%;height:auto;margin-top:16px}.links{display:flex;gap:20px}a{color:#2463a6}.facts{display:flex;gap:14px;flex-wrap:wrap}.fact{border-left:3px solid #79b9be;padding:3px 16px;font-size:17px}.note{background:#fff6df;border-left:4px solid #d98420;padding:18px;margin:0 0 24px}
footer{padding:30px;color:#526575;font-size:14px}section[hidden]{display:none}
</style><header><h1>Lo que muestran las cuatro corridas</h1><p>Town01 · aleatorio frente a historial 80/20. Resultados observados, con las unidades y límites de interpretación visibles.</p><div class="facts"><div class="fact">20 vehículos</div><div class="fact">30 min simulados por corrida</div><div class="fact">Semillas 210 y 109</div><div class="fact">783 llegadas</div></div></header><main>
<nav><button class="active" data-filter="all">Todas</button><button data-filter="objetivos">Cuatro métricas</button><button data-filter="flujo">Flujo y densidad</button><button data-filter="historial">Historial 80/20</button><a class="download" href="graficas_campana.pdf" target="_blank">Abrir PDF completo</a><a class="download" href="informe_graficas.md">Método y lectura</a></nav>
<div class="note"><strong>Cómo leerlas.</strong> Los 524 callbacks se concentran en dos episodios de contacto. Las nubes flujo–densidad–velocidad son exploratorias: no se ajustó una curva ni se estimó una capacidad vial. Las celdas de tiempo/tramo no son réplicas independientes.</div>
'''+''.join(cards)+'''<footer>Gráficas elaboradas a partir de registros conservados; no requirieron nuevas simulaciones. Los CSV derivados, el manifiesto y los archivos vectoriales están junto a esta galería.</footer></main><script>
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.card').forEach(c=>c.hidden=b.dataset.filter!=='all'&&c.dataset.group!==b.dataset.filter)});
</script></html>'''
    (out/'index.html').write_text(page,encoding='utf8')
    report=['# Gráficas de las corridas de veinte vehículos','',
            'Cuatro corridas: semillas 210/109, random_baseline/history_80_20, 1,800 s simulados. El cambio de ritmo de reloj no cambia las unidades simuladas.',
            '', '## Correspondencia con los objetivos', '',
            '- Objetivo general: datos auditados, figuras reproducibles y manifiestos; estas corridas no prueban determinismo físico exacto.',
            '- Objetivo 1: categorías y ODD; mapa del ámbito de medición. Todas las corridas tienen veinte vehículos: todavía no comparan dos niveles de demanda.',
            '- Objetivo 2: veinte agentes simultáneos e historial creciente, visibles en registros y gráfica 07.',
            '- Objetivo 3: gráficas 01–06 cubren destinos, tiempo de viaje, velocidad media y tasas de incidentes/invasiones.',
            '', '## Lectura de los resultados', '',
            '- El histórico no reduce consistentemente el tiempo medio: con 210 pasa de 155.49 a 168.56 s; con 109, de 182.19 a 174.06 s. Cambian también los recorridos, por lo que estas medias describen las poblaciones resultantes.',
            '- La categoría trabajo/educación representa 28.4–28.8 % de las asignaciones históricas frente a 11.5–12.8 % del baseline. El catálogo tiene 18 destinos residenciales, 18 de servicios/ocio y 6 de trabajo/educación: elegir destinos uniformemente no significa repartir las categorías por tercios.',
            '- La velocidad media de presencia se mantiene entre 10.28 y 10.71 km/h. Incluye paradas; no es la velocidad objetivo del controlador.',
            '- Hubo cero invasiones en estas cuatro corridas. Los 14/510 callbacks de baseline incluyen registros repetidos de ambos sensores durante contactos persistentes: la auditoría identifica un episodio por semilla (dos en total). Histórico registró cero eventos. La agrupación por pareja y separación máxima de 1 s es descriptiva, pendiente de definición formal como métrica.',
            '- En las nubes locales aparece menor velocidad en densidades mayores, pero no una rama congestionada suficientemente caracterizada para estimar capacidad. Hay pocos puntos densos y se mezclan semáforos, ubicaciones y períodos; no son réplicas independientes.',
            '- El siguiente contraste debe conservar duración y medición, variar cantidades simultáneas candidatas y repetir condiciones/semillas. Las gráficas ayudan a justificar esas cantidades; aún no fijan las dos demandas definitivas.',
            '', '## Figuras', '']
    for item in items:report += ['### '+item['title'],'',item['note'],'','![Gráfica]('+item['name']+'.png)','','[SVG]('+item['name']+'.svg)','']
    report+=['## Método de las relaciones flujo–densidad–velocidad','',
             'Se usa el mapa OpenDRIVE offline, sin conectarse al servidor ni avanzar frames. Se seleccionan por geometría, antes de examinar tráfico, carriles driving rectos fuera de intersecciones, de ancho/offset constantes y una sola laneSection. Se retienen solo bloques completos de 50 m.',
             'Para cada celda de longitud L y tiempo T, S es la suma de tiempo vehicular y D la distancia longitudinal recorrida: k=1000*S/(L*T), q=3600*D/(L*T), v=3.6*D/S. Unidades: veh/km/carril, veh/h/carril y km/h. La identidad q=k*v se verifica numéricamente; no es evidencia de que una curva empírica esté calibrada.',
             'Las trayectorias se interpolan linealmente entre observaciones consecutivas de 0.05 s y se cortan en fronteras espaciales/temporales. Se incluye cualquier fase y velocidad. Las ventanas comienzan en la primera observación (t=0.05 s); son de 60 s excepto la última, de aproximadamente 59.95 s. No se inventa el primer intervalo sin observación previa.',
             'Se descartan intervalos que cambian de road/lane porque no permiten interpolar s de forma continua. La cota temporal de esas transiciones se registra por corrida. Se usan distancias longitudinales absolutas; los pequeños desplazamientos en reversa se cuantifican, sin filtrarlos.',
             'La selección mide 38 tramos / 1.9 km-carril; no representa toda la red. Los puntos combinan tramos y fases semafóricas heterogéneas. No se seleccionaron estados estacionarios. Una baja velocidad puede provenir de rojo, interacción o espera en destino; no se clasifica automáticamente como saturación.',
             'q es flujo espacio-temporal derivado de trayectorias, no conteo directo de cruces en un detector ni cantidad de viajes completados por hora. Con k=0 se conserva q=0 y v indefinida, no una velocidad artificial de cero.',
             '', '## Cobertura y límites numéricos', '',
             '- Celdas con presencia: %d de %d. Las celdas vacías se conservan en CSV.'%(len(occupied),len(cells)),
             '- Densidad local: %.3f–%.3f veh/km/carril; flujo observado máximo: %.3f veh/h/carril. Es un máximo muestral, no capacidad.'%(occupied.density_veh_per_km_lane.min(),occupied.density_veh_per_km_lane.max(),occupied.flow_veh_per_h_lane.max()),
             '- La serie temporal de velocidad usa diferencias de posición de las observaciones; falta el primer 0.05 s por vehículo. El resumen de las cuatro métricas usa las cifras oficiales auditadas, con exposición completa.',
             '- Los viajes parciales se muestran como cortados, sin convertirlos en tiempos completos. Los boxplots describen viajes dependientes entre sí, no incertidumbre entre réplicas.',
             '- No se ajusta Greenshields ni una curva triangular; no se estiman densidad crítica, atasco ni capacidad. El diagrama de referencia es conceptual, no la forma que se obliga a seguir a los datos.',
             '- La flota cambia entre semillas (18 modelos); cada pareja conserva modelos, spawns, clima y controlador. No se atribuyen diferencias exclusivamente al selector.',
             '', '## Fuentes conceptuales', '',
             '- [FHWA, Traffic Stream Characteristics](https://www.fhwa.dot.gov/publications/research/operations/tft/chap2.pdf): características del flujo y medición compatible.',
             '- [FHWA, variables y estados estacionarios](https://ops.fhwa.dot.gov/publications/weatherempirical/sect3.htm): q, k, velocidad espacial e hipótesis para calibración.',
             '- Marco teórico local, secciones 6.2.3.1–6.2.3.2: definiciones espacio-temporales y diferencia entre identidad y diagrama fundamental.',
             '', '## Reproducción', '',
             '```powershell',
             '.\\carla-env\\Scripts\\python.exe scripts/build_campaign_plot_data.py --campaign data/output/reliability20_20260917_seeds210_109_x5/campaign.json --output data/output/NUEVA_CARPETA',
             '.\\carla-env\\Scripts\\python.exe scripts/plot_mobility_campaign.py --data data/output/NUEVA_CARPETA',
             '```',
             '', 'La primera orden rechaza carpetas existentes. La segunda regenera únicamente las figuras derivadas. Los logs originales no se modifican. Se requiere carla-env y el archivo Town01.xodr local; no hace falta CARLA en ejecución.', '']
    (out/'informe_graficas.md').write_text('\n'.join(report),encoding='utf8')
    inputs=[out/name for name in ('derivation_manifest.json','flow_cells.csv','time_series.csv')]
    inputs += [campaign/name for name in ('metrics/analysis.json','metrics/summary.csv','metrics/destinations.csv','extended_review.json','incident_review.json')]
    inputs += [ROOT/'data/output'/r['run']/'trips_log.csv' for r in runs]
    source_hashes={str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    (out/'figures_manifest.json').write_text(json.dumps(dict(figures=items,source=derived['campaign'],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=source_hashes),indent=2,ensure_ascii=False),encoding='utf8')
    print('EXPORTED',len(items),'figures, PNG/SVG, PDF and HTML gallery:',out.resolve())


if __name__=='__main__':main()
