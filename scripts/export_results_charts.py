"""Export one plot per file from the preserved campaign data, without CARLA.

Titles and panel letters belong to LaTeX. PNG/SVG files contain axes, legends
and observations only; the JSON manifest records their source files and hashes.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import plot_mobility_campaign as base
from src.analysis.traffic_flow_analysis import density_band_guides

plt = base.plt
SELECTORS = ('random_baseline', 'history_80_20')
NAMES = ('Aleatorio', 'Historial')
COLORS = ('#2463A6', '#D98420')
CATEGORIES = ('residential', 'work_education', 'services_leisure')
CATEGORY_NAMES = ('Residencia', 'Trabajo /\neducación', 'Servicios /\nocio')
CAMPAIGNS = (
    ('visual_analysis20_100_guides_20260920', 'demanda_1800s'),
    ('visual_analysis20_100_3600_20260922', 'demanda_3600s_r1'),
    ('visual_analysis20_100_3600_repeat_20260923', 'demanda_3600s_r2'),
)


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def relative(path):
    return path.resolve().relative_to(ROOT.parent).as_posix()


class Exporter:
    def __init__(self, output):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.figures = []
        self.sources = {}
        self.source(Path(__file__))
        self.source(ROOT / 'scripts/plot_mobility_campaign.py')
        self.source(ROOT / 'src/analysis/traffic_flow_analysis.py')
        base.style()
        # Most plots are placed at 0.48\textwidth in the thesis. A 16 pt source
        # font remains approximately 7 pt when a 6.5 inch plot is reduced there.
        plt.rcParams.update({'font.size': 16, 'axes.labelsize': 16,
                             'axes.titlesize': 16, 'xtick.labelsize': 16,
                             'ytick.labelsize': 16, 'legend.fontsize': 16,
                             'svg.hashsalt': 'TrafficIA-resultados'})

    def source(self, path):
        path = Path(path).resolve()
        key = relative(path)
        if key not in self.sources:
            self.sources[key] = sha(path)
        return key

    def save(self, fig, name, title, sources, method):
        # Each scientific plot is created on its own Figure, never cropped from
        # a dashboard. Colorbars are the only possible supplementary axes.
        fig.tight_layout(pad=1.05)
        files = []
        for extension in ('.png', '.svg'):
            target = self.output / (name + extension)
            metadata = {'Date': None} if extension == '.svg' else None
            fig.savefig(target, dpi=220, metadata=metadata)
            files.append({'path': target.name, 'sha256': sha(target)})
        plt.close(fig)
        self.figures.append(dict(name=name, title=title, files=files,
            sources=[self.source(path) for path in sources], method=method))

    def finish(self, filename='manifest.json'):
        # Check that exporting did not change any of the data that were read.
        for key, digest in self.sources.items():
            if sha(ROOT.parent / key) != digest:
                raise ValueError('La fuente cambió durante la exportación: ' + key)
        manifest = dict(format_version=1, generated_by=relative(Path(__file__)),
            source_sha256=self.sources, figures=self.figures,
            figure_count=len(self.figures), formats=['png', 'svg'],
            scope='Una gráfica por archivo. Sin simulaciones ni modificación de datos.',
            flow_guides='Bandas de 10 veh/km/carril, mínimo 10 celdas; agregación por área espacio-temporal; solo se conectan bandas adyacentes.')
        target = self.output / filename
        target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
        print('EXPORTED %d independent charts: %s' % (len(self.figures), self.output.resolve()))
        return target


def load_campaign(data):
    data = Path(data).resolve()
    derived = read(data / 'derivation_manifest.json')
    review_path = data / 'chart_input_review.json'
    if review_path.exists():
        review = read(review_path)
        if review['errors'] or any(not pair['comparable'] for pair in review['pairs']):
            raise ValueError('La campaña contiene errores o parejas no comparables')
        runs, extra = review['metrics'], review['runs']
        sources = [review_path, data / 'derivation_manifest.json']
    else:
        campaign = Path(derived['campaign']).parent
        analysis = campaign / 'metrics/analysis.json'
        extended = campaign / 'extended_review.json'
        runs, extra = read(analysis)['runs'], read(extended)['runs']
        sources = [analysis, extended, data / 'derivation_manifest.json']
    if any(run['integrity_errors'] for run in runs):
        raise ValueError('La campaña contiene errores de integridad')
    counts = sorted({run['vehicle_count'] for run in runs})
    seeds = sorted({run['seed'] for run in runs}, reverse=True)
    groups = counts if len(counts) > 1 else seeds
    group_key = 'vehicle_count' if len(counts) > 1 else 'seed'
    if len(runs) != 4 or len(groups) != 2:
        raise ValueError('Se requieren dos parejas de selectores')
    order = [(group, selector) for group in groups for selector in SELECTORS]
    runs = sorted(runs, key=lambda r: order.index((r[group_key], r['scenario'])))
    extras = {r.get('run', r.get('summary', {}).get('run')): r for r in extra}
    trips, trip_sources = [], []
    for run in runs:
        path = ROOT / 'data/output' / run['run'] / 'trips_log.csv'
        table = pd.read_csv(path)
        done = table[table.status == 'completed']
        if len(table) != run['started'] or len(done) != run['completed']:
            raise ValueError('Los recuentos no coinciden: ' + run['run'])
        if not np.isclose(done.travel_time_s.mean(), run['travel_time']['mean_s']):
            raise ValueError('El tiempo medio no coincide: ' + run['run'])
        # Check both populations directly against the original trip log.
        for population, subset in (('assigned', table), ('reached', done)):
            for dimension, column in (('by_id', 'destination_id'), ('by_category', 'destination_category')):
                observed = subset[column].value_counts()
                for item in run['destinations'][population][dimension]:
                    if not np.isclose(observed.get(item['value'], 0) / len(subset), item['proportion'] or 0):
                        raise ValueError('La distribución no coincide: ' + run['run'])
        trips.append(table)
        trip_sources.append(path)
        if 'summary' in extras[run['run']]:
            summary = extras[run['run']]['summary']
            extras[run['run']] = dict(origin_s=float(table.departure_sim_time_s.min()),
                final_history=summary['final_history_rows'],
                initial_history=summary['final_history_rows'] - len(done),
                selection_counts=summary['selection_classes'])
    duration = {round(r['simulation_duration_s'], 1) for r in runs}
    if len(duration) != 1:
        raise ValueError('Las duraciones no coinciden')
    return dict(data=data, derived=derived, runs=runs, extras=extras, trips=trips,
        sources=sources, trip_sources=trip_sources, groups=groups, group_key=group_key,
        seconds=next(iter(duration)), flow=pd.read_csv(data / 'flow_cells.csv'),
        series=pd.read_csv(data / 'time_series.csv'))


def axis(size=(6.5, 4.1)):
    return plt.subplots(figsize=size)


def grid(ax):
    ax.grid(alpha=.35)
    ax.set_axisbelow(True)


def run_labels(campaign, multiline=True):
    separator = '\n' if multiline else ' · '
    return [('%d veh.' % r['vehicle_count'] if campaign['group_key'] == 'vehicle_count'
             else 'Semilla %d' % r['seed']) + separator + NAMES[SELECTORS.index(r['scenario'])]
            for r in campaign['runs']]


def bar_values(ax, values, labels, ylabel, decimals=2):
    values = np.asarray(values)
    ax.bar(np.arange(len(values)), values, color=list(COLORS) * 2, width=.64)
    high = max(1., max(values))
    for x, value in enumerate(values):
        ax.text(x, value + high * .025, ('%.' + str(decimals) + 'f') % value,
                ha='center', fontsize=15)
    ax.set(xticks=np.arange(len(values)), xticklabels=labels, ylabel=ylabel, ylim=(0, high * 1.19))
    ax.tick_params(axis='x', labelsize=14)
    grid(ax)


def export_campaign(campaign, exporter, prefix):
    c = campaign
    runs, trips, extra = c['runs'], c['trips'], c['extras']
    completed = [t[t.status == 'completed'] for t in trips]
    labels = run_labels(c)
    def save(fig, suffix, title, sources=None, method='Valores de las corridas conservadas.'):
        exporter.save(fig, prefix + '_' + suffix, title, sources or c['sources'], method)

    # Destination categories, with the two fleet sizes on the same single axis.
    for population, spanish in (('assigned', 'asignados'), ('reached', 'alcanzados')):
        fig, ax = axis((8, 4.2))
        tick_labels = []
        for group_index, group in enumerate(c['groups']):
            group_label = '%d veh.' % group if c['group_key'] == 'vehicle_count' else 'Semilla %d' % group
            tick_labels.extend([name + '\n' + group_label for name in CATEGORY_NAMES])
            for selector, offset in enumerate((-.23, .23)):
                run = runs[group_index * 2 + selector]
                bins = {d['value']: 100 * d['proportion'] for d in run['destinations'][population]['by_category']}
                x = np.arange(3) + group_index * 3.6 + offset
                values = [bins[category] for category in CATEGORIES]
                ax.bar(x, values, width=.42, color=COLORS[selector], label=NAMES[selector] if group_index == 0 else None)
                for pos, value in zip(x, values):
                    ax.text(pos, value + 1., '%.1f' % value, ha='center', fontsize=13)
        ax.set(xticks=np.r_[np.arange(3), np.arange(3) + 3.6], xticklabels=tick_labels,
               ylabel='Porcentaje de ' + ('asignaciones' if population == 'assigned' else 'llegadas') + ' (%)', ylim=(0, 68))
        ax.tick_params(labelsize=13)
        ax.yaxis.label.set_size(14)
        ax.legend(loc='upper right', ncol=2, fontsize=14)
        grid(ax)
        save(fig, 'destinos_' + spanish, 'Distribución de destinos ' + spanish,
             method='Frecuencias por categoría divididas entre el total de la población de cada corrida; asignaciones y llegadas separadas.')

    identifiers = [d['value'] for d in runs[0]['destinations']['assigned']['by_id']]
    arrays = []
    for population in ('assigned', 'reached'):
        arrays.append(np.asarray([[100 * (d['proportion'] or 0) for d in run['destinations'][population]['by_id']] for run in runs]))
        if any([d['value'] for d in run['destinations'][population]['by_id']] != identifiers for run in runs):
            raise ValueError('Orden de identificadores distinto')
    for spanish, values in zip(('asignados', 'alcanzados'), arrays):
        fig, ax = axis((12, 3.7))
        im = ax.imshow(values, aspect='auto', cmap='YlGnBu', vmin=0, vmax=max(a.max() for a in arrays))
        ax.set(yticks=range(4), yticklabels=run_labels(c, False), xticks=range(len(identifiers)), xticklabels=identifiers)
        ax.tick_params(axis='x', rotation=90, labelsize=13)
        ax.tick_params(axis='y', labelsize=14)
        colorbar = fig.colorbar(im, ax=ax, label='Porcentaje (%)', fraction=.027, pad=.02)
        colorbar.ax.tick_params(labelsize=14)
        colorbar.ax.yaxis.label.set_size(14)
        save(fig, 'destinos_identificador_' + spanish, 'Frecuencias por identificador: ' + spanish,
             method='Cada fila suma 100 %. Escala común a asignaciones y llegadas. Se conservan destinos con frecuencia cero.')

    fig, ax = axis()
    values = [t.travel_time_s.to_numpy() for t in completed]
    boxes = ax.boxplot(values, patch_artist=True, showmeans=True, labels=labels,
        meanprops=dict(marker='D', markerfacecolor='#182B3A', markeredgecolor='white', markersize=5))
    for patch, color in zip(boxes['boxes'], list(COLORS) * 2):
        patch.set_facecolor(color)
        patch.set_alpha(.55)
    ax.set(ylabel='Tiempo de viaje\ncompletado (s)')
    ax.tick_params(axis='x', labelsize=14)
    grid(ax)
    save(fig, 'tiempo_viaje_cajas', 'Distribución de tiempos de viaje', c['trip_sources'],
         'Solo completados. Caja: cuartiles; línea: mediana; rombo: media; bigotes: 1,5 veces el rango intercuartílico; puntos: valores fuera de bigotes.')
    fig, ax = axis()
    for i, data in enumerate(values):
        data = np.sort(data)
        ax.step(data, np.arange(1, len(data) + 1) / len(data), where='post', color=COLORS[i % 2],
                ls='-' if i < 2 else '--', label=run_labels(c, False)[i])
    ax.set(xlabel='Tiempo de viaje completado (s)', ylabel='Fracción acumulada\nde llegadas', ylim=(0, 1.02))
    ax.legend(fontsize=14, handlelength=1.5, labelspacing=.25)
    grid(ax)
    save(fig, 'tiempo_viaje_acumulada', 'Distribución acumulada de tiempos', c['trip_sources'], 'Distribución empírica de los viajes completados; sin excluir viajes de duración mínima.')
    fig, ax = axis()
    bar_values(ax, [r['completed'] / r['vehicle_count'] for r in runs], labels, 'Llegadas por vehículo')
    save(fig, 'llegadas_por_vehiculo', 'Llegadas por vehículo', method='Número de llegadas dividido entre toda la flota, incluidos actores sin llegada.')

    for per_vehicle, suffix in ((False, 'historial_total'), (True, 'historial_por_vehiculo')):
        fig, ax = axis()
        for i in (1, 3):
            run = runs[i]
            info = extra[run['run']]
            times = np.sort(completed[i].arrival_sim_time_s.to_numpy() - info['origin_s'])
            initial, total = info['initial_history'], info['final_history']
            if total - initial != len(times):
                raise ValueError('El historial no coincide con las llegadas')
            x = np.r_[0, times, c['seconds']] / 60
            y = np.r_[initial, initial + np.arange(1, len(times) + 1), total]
            if per_vehicle:
                y = y / run['vehicle_count']
            group_label = '%d vehículos' % run['vehicle_count'] if c['group_key'] == 'vehicle_count' else 'Semilla %d' % run['seed']
            ax.step(x, y, where='post', color=('#7D58A3', '#278377')[i // 2], label=group_label)
        ax.set(xlabel='Tiempo simulado (min)', ylabel='Visitas por vehículo' if per_vehicle else 'Visitas acumuladas', xlim=(0, c['seconds'] / 60))
        ax.legend()
        grid(ax)
        save(fig, suffix, 'Crecimiento del historial', c['sources'] + c['trip_sources'], 'Visitas iniciales más una visita por viaje completado; reinicio independiente en cada corrida.')
    fig, ax = axis()
    for x, i in enumerate((1, 3)):
        counts = extra[runs[i]['run']]['selection_counts']
        routine = 100 * counts.get('routine', 0) / sum(counts.values())
        for bottom, value, color, label in ((0, routine, '#7D58A3', 'Rutina'), (routine, 100 - routine, '#7EC8BA', 'Exploración')):
            ax.bar(x, value, bottom=bottom, color=color, width=.5, label=label if x == 0 else None)
            ax.text(x, bottom + value / 2, '%.2f %%' % value, ha='center', va='center', color='white' if bottom == 0 else '#182B3A')
    ax.axhline(80, color='#182B3A', ls='--', lw=1, label='Rutina configurada: 80 %')
    ax.set(xticks=(0, 1), xticklabels=['%d vehículos' % g if c['group_key'] == 'vehicle_count' else 'Semilla %d' % g for g in c['groups']], ylabel='Porcentaje de decisiones (%)', ylim=(0, 103))
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), fontsize=14, ncol=2,
              columnspacing=1, handlelength=1.7)
    save(fig, 'seleccion_rutina_exploracion', 'Ramas de selección histórica', method='Todas las decisiones del selector histórico; la línea señala la probabilidad configurada, no una cuota observada.')
    export_flow(c, exporter, prefix)


def export_flow(c, exporter, prefix):
    flow = c['flow']
    occupied = flow[flow.vehicle_seconds > 0]
    rows = []
    for run in c['runs']:
        cells = flow[flow.run == run['run']].to_dict('records')
        rows.extend(dict(row, run=run['run']) for row in density_band_guides(cells, width=10, min_cells=10, length_m=c['derived']['section_length_m']))
    guides = pd.DataFrame(rows)
    if not np.allclose(guides.flow_veh_per_h_lane, guides.density_veh_per_km_lane * guides.speed_kmh, equal_nan=True):
        raise ValueError('Las guías no conservan q=k v')
    sources = c['sources'] + [c['data'] / 'flow_cells.csv']
    relations = (
        ('density_veh_per_km_lane', 'speed_kmh', 'velocidad_densidad', 'Densidad (veh/km/carril)', 'Velocidad espacial (km/h)'),
        ('density_veh_per_km_lane', 'flow_veh_per_h_lane', 'flujo_densidad', 'Densidad (veh/km/carril)', 'Flujo (veh/h/carril)'),
        ('flow_veh_per_h_lane', 'speed_kmh', 'velocidad_flujo', 'Flujo (veh/h/carril)', 'Velocidad espacial (km/h)'),
    )
    for group_index, group in enumerate(c['groups']):
        for x, y, suffix, xlabel, ylabel in relations:
            fig, ax = axis()
            for i in (group_index * 2, group_index * 2 + 1):
                run = c['runs'][i]
                data = occupied[occupied.run == run['run']]
                ax.scatter(data[x], data[y], s=12, alpha=.18, color=COLORS[i % 2], edgecolors='none', rasterized=True)
                supported = guides[(guides.run == run['run']) & guides.supported]
                labelled = False
                for _, part in supported.groupby('segment', sort=True):
                    ax.plot(part[x], part[y], color=COLORS[i % 2], lw=2, marker='o', ms=4,
                        label=NAMES[i % 2] if not labelled else None)
                    labelled = True
            ax.set(xlabel=xlabel, ylabel=ylabel, xlim=(0, occupied[x].max() * 1.06), ylim=(0, occupied[y].max() * 1.1))
            ax.legend(fontsize=16, handlelength=1.5)
            grid(ax)
            group_name = '%dveh' % group if c['group_key'] == 'vehicle_count' else 'semilla%d' % group
            exporter.save(fig, prefix + '_flujo_' + suffix + '_' + group_name, suffix.replace('_', ' '), sources,
                'Celdas ocupadas de 50 m y ventanas de 60 s (última parcial); guías por bandas de densidad con al menos diez celdas; no ajuste teórico.')
    fig, ax = axis((6.5, 5.1))
    background = np.asarray(c['derived']['background_xy'])
    ax.scatter(background[:, 0], background[:, 1], s=2, color='#C5CBD1')
    for geometry in c['derived']['selected_geometry']:
        xy = np.asarray(geometry['xy'])
        ax.plot(xy[:, 0], xy[:, 1], color=COLORS[0], lw=2)
    ax.set(xlabel='Coordenada x (m)', ylabel='Coordenada y (m)', aspect='equal')
    ax.invert_yaxis()
    grid(ax)
    exporter.save(fig, prefix + '_mapa_tramos', 'Tramos de medición de tráfico', c['sources'], 'Geometría conservada en el manifiesto; los tramos azules delimitan el ámbito local.')
    edges = np.array([0, 5, 10, 20, 40, 60, 100, 150, 250, 500], dtype=float)
    edges = edges[:max(2, np.searchsorted(edges, occupied.density_veh_per_km_lane.max(), side='right') + 1)]
    if edges[-1] < occupied.density_veh_per_km_lane.max():
        edges = np.r_[edges, occupied.density_veh_per_km_lane.max() + 1]
    fig, ax = axis((6.5, 4.6))
    for group_index, group in enumerate(c['groups']):
        values, _ = np.histogram(occupied[occupied[c['group_key']] == group].density_veh_per_km_lane, bins=edges)
        ax.bar(np.arange(len(values)) + (group_index - .5) * .38, values, width=.36,
            color=('#7D58A3', '#278377')[group_index], label='%d vehículos' % group if c['group_key'] == 'vehicle_count' else 'Semilla %d' % group)
    ax.set(xticks=range(len(edges) - 1), xticklabels=['%g–%g' % (a, b) for a, b in zip(edges[:-1], edges[1:])], xlabel='Banda de densidad (veh/km/carril)', ylabel='Número de celdas ocupadas')
    ax.tick_params(axis='x', labelsize=14, rotation=40)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment('right')
    ax.legend()
    grid(ax)
    exporter.save(fig, prefix + '_cobertura_densidad', 'Cobertura por bandas de densidad', sources, 'Celdas ocupadas agrupadas por demanda y ambos selectores; intervalos cerrados a la izquierda, último cerrado también a la derecha.')


def export_repetitions(first, second, exporter):
    for count in (20, 100):
        for metric in ('velocidad', 'llegadas'):
            fig, ax = axis((6.5, 4.2))
            sources = []
            for repetition, c in enumerate((first, second), 1):
                for i, run in enumerate(c['runs']):
                    if run['vehicle_count'] != count:
                        continue
                    label = NAMES[SELECTORS.index(run['scenario'])] + ' · R%d' % repetition
                    color = COLORS[SELECTORS.index(run['scenario'])]
                    if metric == 'velocidad':
                        data = c['series'][c['series'].run == run['run']]
                        x = (data.start_elapsed_s + data.duration_s / 2) / 60
                        y = data.speed_kmh
                        sources.append(c['data'] / 'time_series.csv')
                    else:
                        trips = c['trips'][i]
                        times = np.sort(trips[trips.status == 'completed'].arrival_sim_time_s.to_numpy() - c['extras'][run['run']]['origin_s'])
                        x = np.r_[0, times, c['seconds']] / 60
                        y = np.r_[0, np.arange(1, len(times) + 1), len(times)]
                        sources.extend(c['sources'] + [c['trip_sources'][i]])
                    if metric == 'velocidad':
                        ax.plot(x, y, color=color, ls='-' if repetition == 1 else '--', label=label)
                    else:
                        ax.step(x, y, where='post', color=color, ls='-' if repetition == 1 else '--', label=label)
            ax.set(xlabel='Tiempo simulado (min)', ylabel='Velocidad de presencia\n(km/h)' if metric == 'velocidad' else 'Llegadas acumuladas', xlim=(0, first['seconds'] / 60), ylim=(0, None))
            if metric == 'velocidad':
                ax.set_ylim(0, 20)
            ax.legend(ncol=2, fontsize=14, columnspacing=1, handlelength=1.6)
            grid(ax)
            exporter.save(fig, 'evolucion_repeticiones_%s_%dveh' % (metric, count), 'Evolución de ' + metric,
                list(dict.fromkeys(sources)), 'R1 y R2 separadas; velocidad por ventanas de 60 s y llegadas por sus tiempos exactos de registro.')


def export_collection(output, thesis_output=None, include_1800=True):
    exporter = Exporter(output)
    exporter.source(Path(__file__))
    exporter.source(ROOT / 'src/analysis/traffic_flow_analysis.py')
    loaded = {}
    for directory, prefix in CAMPAIGNS:
        if not include_1800 and prefix == 'demanda_1800s':
            continue
        campaign = load_campaign(ROOT / 'data/output' / directory)
        export_campaign(campaign, exporter, prefix)
        loaded[prefix] = campaign
    export_repetitions(loaded['demanda_3600s_r1'], loaded['demanda_3600s_r2'], exporter)
    manifest = exporter.finish()
    if thesis_output:
        target = Path(thesis_output)
        target.mkdir(parents=True, exist_ok=True)
        paths = [manifest] + [exporter.output / item['path'] for figure in exporter.figures for item in figure['files']]
        for path in paths:
            shutil.copyfile(path, target / path.name)
            if sha(path) != sha(target / path.name):
                raise ValueError('La copia no coincide: ' + path.name)
        print('COPIED identical files: ' + str(target.resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'images/graficas_independientes')
    parser.add_argument('--thesis-output', type=Path)
    parser.add_argument('--only-3600', action='store_true')
    args = parser.parse_args()
    export_collection(args.output, args.thesis_output, not args.only_3600)


if __name__ == '__main__':
    main()
