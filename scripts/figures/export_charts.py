"""Export individual mobility charts from user-selected TrafficIA records."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.figures import plot_mobility as base
from src.analysis.mobility_analysis import analyze_run
from src.analysis.incident_analysis import collision_episodes
from scripts.analysis.compare_repetitions import comparison_rows
from src.analysis.traffic_flow_analysis import density_band_guides

plt = base.plt
SELECTORS = ('random_baseline', 'history_80_20')
NAMES = ('Aleatorio', 'Historial')
COLORS = ('#2463A6', '#D98420')
CATEGORIES = ('residential', 'work_education', 'services_leisure')
CATEGORY_NAMES = ('Residencia', 'Trabajo /\neducación', 'Servicios /\nocio')
SCENARIO_LABELS = dict(zip(SELECTORS, NAMES))


def read(path):
    """Read a JSON file into Python data."""
    return json.loads(path.read_text(encoding='utf8'))


def sha(path):
    """Calculate a file's SHA-256 fingerprint without loading the whole file at once."""
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def source_path(path):
    """Keep project paths portable and retain the location of external inputs."""
    path = path.resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


class Exporter:
    def __init__(self, output, pdf=None):
        """Prepare the chart output folder, source tracking, and common figure style."""
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.pdf = pdf
        self.figures = []
        self.sources = {}
        self.source(Path(__file__))
        self.source(ROOT / 'scripts/figures/plot_mobility.py')
        self.source(ROOT / 'src/analysis/traffic_flow_analysis.py')
        base.style()
        plt.rcParams.update({'font.size': 16, 'axes.labelsize': 16,
                             'axes.titlesize': 16, 'xtick.labelsize': 16,
                             'ytick.labelsize': 16, 'legend.fontsize': 16,
                             'svg.hashsalt': 'TrafficIA-resultados'})

    def source(self, path):
        """Register a source file's fingerprint and return its relative path."""
        path = Path(path).resolve()
        key = source_path(path)
        if key not in self.sources:
            self.sources[key] = sha(path)
        return key

    def save(self, fig, name, title, sources, method):
        """Save an individual chart as PNG and SVG and record its sources and method."""
        if Path(name).name != name or any(c in name for c in '/\\:'):
            raise ValueError('El prefijo debe ser un nombre de archivo.')
        fig.tight_layout(pad=1.05)
        files = []
        for extension in ('.png', '.svg'):
            target = self.output / (name + extension)
            metadata = {'Date': None} if extension == '.svg' else None
            fig.savefig(target, dpi=220, metadata=metadata)
            files.append({'path': target.name, 'sha256': sha(target)})
        if self.pdf is not None:
            fig.suptitle(title)
            self.pdf.savefig(fig)
        plt.close(fig)
        self.figures.append(dict(name=name, title=title, files=files,
            sources=[self.source(path) for path in dict.fromkeys(sources)], method=method))

    def finish(self, filename='manifest.json', **metadata):
        """Check that source files stayed unchanged and write the chart manifest."""
        # Check that exporting did not change any of the data that were read.
        for key, digest in self.sources.items():
            if sha(ROOT / key) != digest:
                raise ValueError('La fuente cambió durante la exportación: ' + key)
        manifest = dict(format_version=2, source_base='project_root', generated_by=source_path(Path(__file__)),
            source_sha256=self.sources, figures=self.figures,
            figure_count=len(self.figures), formats=['png', 'svg'],
            scope='Una gráfica por archivo. Sin simulaciones ni modificación de datos.',
            flow_guides='Bandas de 10 veh/km/carril, mínimo 10 celdas; agregación por área espacio-temporal; solo se conectan bandas adyacentes.')
        manifest.update(metadata)
        target = self.output / filename
        target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
        print('EXPORTED %d independent charts: %s' % (len(self.figures), self.output.resolve()))
        return target


def load_campaign(data, runs_root=None):
    """Read a raw run, a mobility report, or a directory of verified plotting inputs."""
    data = Path(data).resolve()
    derived_path = data / 'derivation_manifest.json'
    derived = read(derived_path) if derived_path.is_file() else {}
    sources = [derived_path] if derived else []
    raw = (data / 'run_config.json').is_file()
    if raw:
        runs = [analyze_run(data)]
    else:
        review_path = data / 'chart_input_review.json'
        if review_path.is_file():
            review = read(review_path)
            if review['errors'] or any(not pair['comparable'] for pair in review['pairs']):
                raise ValueError('La auditoría encontró errores o parejas no comparables.')
            runs = review['metrics']
            sources.append(review_path)
        else:
            analysis_path = data / 'analysis.json'
            if not analysis_path.is_file() and 'campaign' in derived:
                analysis_path = Path(derived['campaign']).parent / 'metrics/analysis.json'
            if not analysis_path.is_file():
                raise ValueError('Indica una corrida, un informe de movilidad o los derivados de una campaña: ' + str(data))
            runs = read(analysis_path)['runs']
            sources.append(analysis_path)
    if not runs or any(r['integrity_errors'] for r in runs):
        raise ValueError('Se requieren corridas con registros íntegros.')
    if len({r['run'] for r in runs}) != len(runs):
        raise ValueError('Hay identificadores de corrida repetidos.')
    runs = sorted(runs, key=lambda r: (r['vehicle_count'], r['seed'], r['scenario'] != SELECTORS[0], r['scenario'], r['run']))
    trips, trip_sources, extras = [], [], {}
    for run in runs:
        if raw:
            folder = data
        elif runs_root is not None:
            folder = Path(runs_root) / run['run']
        else:
            folder = Path(run.get('source_directory') or ROOT / 'data/output' / run['run'])
            if not (folder / 'run_config.json').is_file():
                folder = ROOT / 'data/output' / run['run']
        config_path = folder / 'run_config.json'
        config = read(config_path)
        if config['run_id'] != run['run']:
            raise ValueError('Identificador de corrida distinto en ' + str(folder))
        path = folder / 'trips_log.csv'
        table = pd.read_csv(path)
        done = table[table.status == 'completed']
        if len(table) != run['started'] or len(done) != run['completed']:
            raise ValueError('Los recuentos no coinciden: ' + run['run'])
        mean = run['travel_time']['mean_s']
        if (done.empty and mean is not None) or (not done.empty and (mean is None or not np.isclose(done.travel_time_s.mean(), mean))):
            raise ValueError('El tiempo medio no coincide: ' + run['run'])
        for population, subset in (('assigned', table), ('reached', done)):
            for dimension, column in (('by_id', 'destination_id'), ('by_category', 'destination_category')):
                counts = subset[column].value_counts()
                for item in run['destinations'][population][dimension]:
                    value = item['proportion']
                    if subset.empty:
                        matches = value is None
                    else:
                        matches = value is not None and np.isclose(counts.get(item['value'], 0) / len(subset), value)
                    if not matches:
                        raise ValueError('La distribución no coincide: ' + run['run'])
        history = pd.read_csv(folder / 'vehicle_history.csv')
        initial = int(history.trip_id.isna().sum())
        if len(history) - initial != len(done):
            raise ValueError('El historial no coincide con las llegadas: ' + run['run'])
        origin = table.departure_sim_time_s.min()
        events = pd.read_csv(folder / 'events_log.csv', keep_default_na=False).to_dict('records')
        actors = {v['vehicle_id']: v['carla_actor_id'] for v in config.get('vehicles', [])}
        extras[run['run']] = dict(origin_s=origin, final_history=len(history), initial_history=initial,
            episodes=collision_episodes(events, actors, origin), selection_counts=table.selection_class.value_counts().to_dict(),
            routine_probability=config.get('simulation_config', {}).get('routine_probability'))
        trips.append(table)
        trip_sources.append(path)
        sources.extend([config_path, path, folder / 'events_log.csv', folder / 'vehicle_history.csv', folder / 'metrics_summary.csv'])
    result = dict(data=data, derived=derived, runs=runs, extras=extras, trips=trips, trip_sources=trip_sources,
                  sources=sources, groups=sorted({(r['vehicle_count'], r['seed']) for r in runs}), flow=None, series=None)
    if derived:
        for key, filename in [('flow', 'flow_cells.csv'), ('series', 'time_series.csv')]:
            path = data / filename
            frame = pd.read_csv(path)
            if set(frame.run) != {r['run'] for r in runs}:
                raise ValueError('Las corridas de ' + str(path) + ' no coinciden con el informe.')
            result[key] = frame
            sources.append(path)
    return result


def axis(size=(6.5, 4.1)):
    """Create a Matplotlib figure and axes with the requested size."""
    return plt.subplots(figsize=size)


def grid(ax):
    """Place a light grid behind the chart's data."""
    ax.grid(alpha=.35)
    ax.set_axisbelow(True)


def run_labels(campaign, multiline=True):
    separator = '\n' if multiline else ' · '
    labels = ['%d veh. · semilla %d%s%s' % (r['vehicle_count'], r['seed'], separator,
              SCENARIO_LABELS.get(r['scenario'], r['scenario'])) for r in campaign['runs']]
    return [label if labels.count(label) == 1 else label + separator + run['run']
            for label, run in zip(labels, campaign['runs'])]


def bar_values(ax, values, labels, ylabel, decimals=2):
    """Draw colored bars, label their values, and configure the chart axes."""
    values = np.asarray(values, dtype=float)
    ax.bar(np.arange(len(values)), values, color=list(COLORS), width=.64)
    high = max(1., max(values[np.isfinite(values)], default=0.))
    for x, value in enumerate(values):
        ax.text(x, (value if np.isfinite(value) else 0) + high * .025, base.metric_label(value, '.%df' % decimals),
                ha='center', fontsize=15)
    ax.set(xticks=np.arange(len(values)), xticklabels=labels, ylabel=ylabel, ylim=(0, high * 1.19))
    ax.tick_params(axis='x', labelsize=14)
    grid(ax)


def export_campaign(campaign, exporter, prefix):
    """Export separate charts for a campaign's destination choices, mobility, and recorded events."""
    c = campaign
    runs, trips, extra = c['runs'], c['trips'], c['extras']
    completed = [t[t.status == 'completed'] for t in trips]
    labels = run_labels(c)
    def save(fig, suffix, title, sources=None, method='Valores de las corridas conservadas.'):
        """Save a campaign chart using its filename prefix and default source list."""
        exporter.save(fig, prefix + '_' + suffix, title, sources or c['sources'], method)

    for population, spanish in (('assigned', 'asignados'), ('reached', 'alcanzados')):
        fig, ax = axis((8, 4.2))
        categories = sorted({d['value'] for r in runs for d in r['destinations'][population]['by_category']})
        width = .8 / len(runs)
        for i, run in enumerate(runs):
            bins = {d['value']: d['proportion'] for d in run['destinations'][population]['by_category']}
            values = [100 * bins[cat] if bins.get(cat) is not None else np.nan for cat in categories]
            x = np.arange(len(categories)) + (i - (len(runs) - 1) / 2) * width
            ax.bar(x, values, width=width, label=labels[i])
        ax.set(xticks=range(len(categories)), xticklabels=[dict(zip(CATEGORIES, CATEGORY_NAMES)).get(cat, cat) for cat in categories],
               ylabel='Porcentaje (%)', ylim=(0, 100))
        ax.legend(fontsize=10)
        grid(ax)
        save(fig, 'destinos_' + spanish, 'Distribución de destinos ' + spanish)

    identifiers = sorted({d['value'] for r in runs for d in r['destinations']['assigned']['by_id']})
    arrays = []
    for population in ('assigned', 'reached'):
        rows = []
        for run in runs:
            bins = {d['value']: d['proportion'] for d in run['destinations'][population]['by_id']}
            rows.append([100 * bins[k] if bins.get(k) is not None else np.nan for k in identifiers])
        arrays.append(np.asarray(rows))
    max_percent = max((np.nanmax(a) for a in arrays if np.isfinite(a).any()), default=100)
    for spanish, values in zip(('asignados', 'alcanzados'), arrays):
        fig, ax = axis((12, 3.7))
        im = ax.imshow(values, aspect='auto', cmap='YlGnBu', vmin=0, vmax=max_percent or 1)
        ax.set(yticks=range(len(runs)), yticklabels=run_labels(c, False), xticks=range(len(identifiers)), xticklabels=identifiers)
        ax.tick_params(axis='x', rotation=90, labelsize=13)
        ax.tick_params(axis='y', labelsize=14)
        colorbar = fig.colorbar(im, ax=ax, label='Porcentaje (%)', fraction=.027, pad=.02)
        colorbar.ax.tick_params(labelsize=14)
        colorbar.ax.yaxis.label.set_size(14)
        save(fig, 'destinos_identificador_' + spanish, 'Frecuencias por identificador: ' + spanish,
             method='Porcentaje por corrida con escala común. Las filas sin viajes en esa población quedan sin definir.')

    fig, ax = axis()
    values = [t.travel_time_s.to_numpy() for t in completed]
    boxes = ax.boxplot(values, patch_artist=True, showmeans=True, labels=labels,
        meanprops=dict(marker='D', markerfacecolor='#182B3A', markeredgecolor='white', markersize=5))
    for patch, color in zip(boxes['boxes'], (COLORS * len(runs))):
        patch.set_facecolor(color)
        patch.set_alpha(.55)
    ax.set(ylabel='Tiempo de viaje\ncompletado (s)')
    ax.tick_params(axis='x', labelsize=14)
    grid(ax)
    save(fig, 'tiempo_viaje_cajas', 'Distribución de tiempos de viaje', c['trip_sources'],
         'Solo completados. Caja: cuartiles; línea: mediana; rombo: media; bigotes: 1,5 veces el rango intercuartílico; puntos: valores fuera de bigotes.')
    fig, ax = axis()
    for i, data in enumerate(values):
        if not len(data):
            continue
        data = np.sort(data)
        ax.step(data, np.arange(1, len(data) + 1) / len(data), where='post', label=labels[i])
    ax.set(xlabel='Tiempo de viaje completado (s)', ylabel='Fracción acumulada\nde llegadas', ylim=(0, 1.02))
    if any(len(data) for data in values):
        ax.legend(fontsize=14, handlelength=1.5, labelspacing=.25)
    else:
        ax.text(.5, .5, 'Sin llegadas', ha='center', transform=ax.transAxes)
    grid(ax)
    save(fig, 'tiempo_viaje_acumulada', 'Distribución acumulada de tiempos', c['trip_sources'], 'Distribución empírica de los viajes completados; sin excluir viajes de duración mínima.')
    fig, ax = axis()
    bar_values(ax, [r['completed'] / r['vehicle_count'] for r in runs], labels, 'Llegadas por vehículo')
    save(fig, 'llegadas_por_vehiculo', 'Llegadas por vehículo', method='Número de llegadas dividido entre toda la flota, incluidos actores sin llegada.')

    for suffix, title, unit, values in [
            ('tiempo_medio', 'Tiempo medio de viajes completados', 's', [r['travel_time']['mean_s'] for r in runs]),
            ('velocidad_media', 'Velocidad media', 'km/h', [r['speed']['mean_kmh'] for r in runs]),
            ('episodios_colision', 'Episodios de contacto', 'Episodios', [len(extra[r['run']]['episodes']) for r in runs])]:
        fig, ax = axis()
        bar_values(ax, values, labels, unit)
        save(fig, suffix, title)
    for kind, name in [('collision', 'colisiones'), ('lane_invasion', 'invasiones')]:
        for field, unit in [('observed_callbacks', 'Avisos'), ('per_vehicle_km', 'Avisos / vehículo-km')]:
            fig, ax = axis()
            bar_values(ax, [r['events'][kind][field] for r in runs], labels, unit)
            save(fig, name + '_' + field, name.capitalize() + ' · ' + unit)

    fig, ax = axis()
    bottom = np.zeros(len(runs))
    for status in sorted({status for run in runs for status in run['statuses']}):
        counts = np.array([r['statuses'].get(status, 0) for r in runs])
        ax.bar(range(len(runs)), counts, bottom=bottom, label=status)
        bottom += counts
    ax.set(xticks=range(len(runs)), xticklabels=labels, ylabel='Intentos de viaje')
    ax.legend()
    grid(ax)
    save(fig, 'estados_viaje', 'Intentos por estado de cierre')

    fig, ax = axis()
    for i, run in enumerate(runs):
        episodes = extra[run['run']]['episodes']
        ax.scatter([e['first_elapsed_s'] / 60 for e in episodes], [i] * len(episodes), color=COLORS[i % len(COLORS)])
    ax.set(yticks=range(len(runs)), yticklabels=labels, ylabel='Corrida', xlabel='Tiempo simulado (min)',
           xlim=(0, max(r['simulation_duration_s'] for r in runs) / 60))
    grid(ax)
    save(fig, 'episodios_tiempo', 'Inicio de los episodios de contacto')

    if c['series'] is not None:
        for field, unit in [('speed_kmh', 'km/h'), ('low_speed_percent', '%')]:
            fig, ax = axis()
            for i, run in enumerate(runs):
                window = c['series'][c['series'].run == run['run']]
                ax.plot((window.start_elapsed_s + window.duration_s / 2) / 60, window[field], label=labels[i])
            ax.set(xlabel='Tiempo simulado (min)', ylabel=unit)
            ax.legend(fontsize=10)
            grid(ax)
            save(fig, 'evolucion_' + field, 'Evolución de ' + ('velocidad' if field == 'speed_kmh' else 'tiempo a baja velocidad'))
    historical = [i for i, run in enumerate(runs) if run['scenario'] == 'history_80_20']
    if historical:
        export_history(c, exporter, prefix, historical)
    if c['flow'] is not None:
        export_flow(c, exporter, prefix)


def export_history(c, exporter, prefix, historical):
    runs, trips, extra = c['runs'], c['trips'], c['extras']
    labels = run_labels(c)
    for per_vehicle, suffix in ((False, 'historial_total'), (True, 'historial_por_vehiculo')):
        fig, ax = axis()
        for i in historical:
            run = runs[i]
            info = extra[run['run']]
            arrivals = trips[i].loc[trips[i].status == 'completed', 'arrival_sim_time_s']
            times = np.sort(arrivals.to_numpy() - info['origin_s'])
            initial, total = info['initial_history'], info['final_history']
            if total - initial != len(times):
                raise ValueError('El historial no coincide con las llegadas')
            x = np.r_[0, times, run['simulation_duration_s']] / 60
            y = np.r_[initial, initial + np.arange(1, len(times) + 1), total]
            if per_vehicle:
                y = y / run['vehicle_count']
            ax.step(x, y, where='post', label=labels[i])
        ax.set(xlabel='Tiempo simulado (min)', ylabel='Visitas por vehículo' if per_vehicle else 'Visitas acumuladas')
        ax.legend()
        grid(ax)
        exporter.save(fig, prefix + '_' + suffix, 'Crecimiento del historial', c['sources'], 'Visitas iniciales más una visita por viaje completado; reinicio independiente en cada corrida.')
    fig, ax = axis()
    for x, i in enumerate(historical):
        info = extra[runs[i]['run']]
        counts = info['selection_counts']
        total = sum(counts.values())
        if total:
            routine = 100 * counts.get('routine', 0) / total
            ax.bar(x, routine, color=COLORS[0], label='Rutina' if x == 0 else None)
            ax.bar(x, 100 - routine, bottom=routine, color=COLORS[1], label='Exploración' if x == 0 else None)
        if info['routine_probability'] is not None:
            ax.plot(x, info['routine_probability'] * 100, 'k_', label='Configuración' if x == 0 else None)
    ax.set(xticks=range(len(historical)), xticklabels=[labels[i] for i in historical], ylabel='Porcentaje de decisiones (%)', ylim=(0, 103))
    ax.legend()
    exporter.save(fig, prefix + '_seleccion_rutina_exploracion', 'Ramas de selección histórica', c['sources'],
                  'Porcentajes de las decisiones registradas. La marca indica la probabilidad configurada.')


def export_flow(c, exporter, prefix):
    """Export lane-flow, density, speed, and observation-coverage charts."""
    flow = c['flow']
    occupied = flow[flow.vehicle_seconds > 0]
    rows = []
    for run in c['runs']:
        cells = flow[flow.run == run['run']].to_dict('records')
        rows.extend(dict(row, run=run['run']) for row in density_band_guides(cells, width=10, min_cells=10, length_m=c['derived']['section_length_m']))
    guides = pd.DataFrame(rows)
    if not guides.empty and not np.allclose(guides.flow_veh_per_h_lane, guides.density_veh_per_km_lane * guides.speed_kmh, equal_nan=True):
        raise ValueError('Las guías no conservan q=k v')
    sources = c['sources'] + [c['data'] / 'flow_cells.csv']
    relations = (
        ('density_veh_per_km_lane', 'speed_kmh', 'velocidad_densidad', 'Densidad (veh/km/carril)', 'Velocidad espacial (km/h)'),
        ('density_veh_per_km_lane', 'flow_veh_per_h_lane', 'flujo_densidad', 'Densidad (veh/km/carril)', 'Flujo (veh/h/carril)'),
        ('flow_veh_per_h_lane', 'speed_kmh', 'velocidad_flujo', 'Flujo (veh/h/carril)', 'Velocidad espacial (km/h)'),
    )
    for group in c['groups']:
        for x, y, suffix, xlabel, ylabel in relations:
            fig, ax = axis()
            for i, run in enumerate(c['runs']):
                if (run['vehicle_count'], run['seed']) != group:
                    continue
                data = occupied[occupied.run == run['run']]
                ax.scatter(data[x], data[y], s=12, alpha=.18, color=COLORS[i % 2], edgecolors='none', rasterized=True, label=run_labels(c, False)[i])
                if guides.empty:
                    continue
                supported = guides[(guides.run == run['run']) & guides.supported]
                for _, part in supported.groupby('segment', sort=True):
                    ax.plot(part[x], part[y], color=COLORS[i % 2], lw=2, marker='o', ms=4)
            ax.set(xlabel=xlabel, ylabel=ylabel, xlim=(0, None), ylim=(0, None))
            ax.legend(fontsize=16, handlelength=1.5)
            grid(ax)
            group_name = '%dveh_semilla%d' % group
            exporter.save(fig, prefix + '_flujo_' + suffix + '_' + group_name, suffix.replace('_', ' '), sources,
                'Celdas ocupadas de 50 m y ventanas de 60 s (última parcial); guías por bandas de densidad con al menos diez celdas; no ajuste teórico.')
    fig, ax = axis((6.5, 5.1))
    background = np.asarray(c['derived']['background_xy'])
    if background.size:
        ax.scatter(background[:, 0], background[:, 1], s=2, color='#C5CBD1')
    for geometry in c['derived']['selected_geometry']:
        xy = np.asarray(geometry['xy'])
        ax.plot(xy[:, 0], xy[:, 1], color=COLORS[0], lw=2)
    ax.set(xlabel='Coordenada x (m)', ylabel='Coordenada y (m)', aspect='equal')
    ax.invert_yaxis()
    grid(ax)
    exporter.save(fig, prefix + '_mapa_tramos', 'Tramos de medición de tráfico', c['sources'], 'Geometría conservada en el manifiesto; los tramos azules delimitan el ámbito local.')
    edges = np.array([0, 5, 10, 20, 40, 60, 100, 150, 250, 500], dtype=float)
    max_density = occupied.density_veh_per_km_lane.max() if not occupied.empty else 0.
    edges = edges[:max(2, np.searchsorted(edges, max_density, side='right') + 1)]
    if edges[-1] < max_density:
        edges = np.r_[edges, max_density + 1]
    fig, ax = axis((6.5, 4.6))
    for group_index, group in enumerate(c['groups']):
        run_ids = [r['run'] for r in c['runs'] if (r['vehicle_count'], r['seed']) == group]
        cells = occupied[occupied.run.isin(run_ids)]
        values, _ = np.histogram(cells.density_veh_per_km_lane, bins=edges)
        width = .8 / len(c['groups'])
        ax.bar(np.arange(len(values)) + (group_index - (len(c['groups']) - 1) / 2) * width,
               values, width=width, label='%d veh. · semilla %d' % group)
    ax.set(xticks=range(len(edges) - 1), xticklabels=['%g–%g' % (a, b) for a, b in zip(edges[:-1], edges[1:])], xlabel='Banda de densidad (veh/km/carril)', ylabel='Número de celdas ocupadas')
    ax.tick_params(axis='x', labelsize=14, rotation=40)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment('right')
    ax.legend()
    grid(ax)
    exporter.save(fig, prefix + '_cobertura_densidad', 'Cobertura por bandas de densidad', sources, 'Celdas ocupadas agrupadas por demanda y ambos selectores; intervalos cerrados a la izquierda, último cerrado también a la derecha.')


def export_repetitions(first, second, exporter):
    """Plot the speed and arrival evolution of both repetitions for each vehicle count."""
    rows, _ = comparison_rows(first['runs'], second['runs'])
    labels = run_labels(first)
    order = [(r['vehicle_count'], r['scenario'], r['seed']) for r in first['runs']]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, (metric, title) in zip(axes.flat, [
            ('completed_mean_time_s', 'Tiempo medio de completados (s)'), ('mean_speed_kmh', 'Velocidad media (km/h)'),
            ('collision_rate_per_vehicle_km', 'Colisiones / vehículo-km'), ('invasion_rate_per_vehicle_km', 'Invasiones / vehículo-km'),
            ('completed', 'Llegadas'), ('incomplete_fraction', 'Proporción de intentos incompletos')]):
        if metric == 'incomplete_fraction':
            first_values = [r['incomplete_fraction'] for r in first['runs']]
            repeat_values = [r['incomplete_fraction'] for r in second['runs']]
        else:
            indexed = {(r['vehicle_count'], r['scenario'], r['seed']): r for r in rows if r['metric'] == metric}
            first_values = [indexed[key]['first'] for key in order]
            repeat_values = [indexed[key]['repeat'] for key in order]
        for offset, values, label in [(-.2, first_values, 'Primera'), (.2, repeat_values, 'Repetición')]:
            ax.bar(np.arange(len(order)) + offset, np.asarray(values, dtype=float), .4, label=label)
        ax.set(xticks=range(len(order)), xticklabels=labels, title=title)
        ax.tick_params(axis='x', labelsize=8)
        grid(ax)
    axes.flat[0].legend()
    exporter.save(fig, 'comparacion_repeticiones', 'Comparación de corridas emparejadas',
                  first['sources'] + second['sources'], 'Casos emparejados por flota, selector y semilla.')
    for count, seed in first['groups']:
        for metric in ('velocidad', 'llegadas'):
            if metric == 'velocidad' and (first['series'] is None or second['series'] is None):
                continue
            fig, ax = axis((6.5, 4.2))
            sources = []
            for repetition, c in enumerate((first, second), 1):
                for i, run in enumerate(c['runs']):
                    if (run['vehicle_count'], run['seed']) != (count, seed):
                        continue
                    label = SCENARIO_LABELS.get(run['scenario'], run['scenario']) + ' · R%d' % repetition
                    color = COLORS[i % len(COLORS)]
                    if metric == 'velocidad':
                        data = c['series'][c['series'].run == run['run']]
                        x = (data.start_elapsed_s + data.duration_s / 2) / 60
                        y = data.speed_kmh
                        sources.append(c['data'] / 'time_series.csv')
                    else:
                        trips = c['trips'][i]
                        times = np.sort(trips[trips.status == 'completed'].arrival_sim_time_s.to_numpy() - c['extras'][run['run']]['origin_s'])
                        x = np.r_[0, times, run['simulation_duration_s']] / 60
                        y = np.r_[0, np.arange(1, len(times) + 1), len(times)]
                        sources.extend(c['sources'] + [c['trip_sources'][i]])
                    if metric == 'velocidad':
                        ax.plot(x, y, color=color, ls='-' if repetition == 1 else '--', label=label)
                    else:
                        ax.step(x, y, where='post', color=color, ls='-' if repetition == 1 else '--', label=label)
            ax.set(xlabel='Tiempo simulado (min)', ylabel='Velocidad de presencia\n(km/h)' if metric == 'velocidad' else 'Llegadas acumuladas', xlim=(0, None), ylim=(0, None))
            ax.legend(ncol=2, fontsize=14, columnspacing=1, handlelength=1.6)
            grid(ax)
            exporter.save(fig, 'evolucion_repeticiones_%s_%dveh_semilla%d' % (metric, count, seed), 'Evolución de ' + metric,
                list(dict.fromkeys(sources)), 'R1 y R2 separadas; velocidad por ventanas de 60 s y llegadas por sus tiempos exactos de registro.')


def export_collection(data, output, prefix='movilidad', compare_data=None, copy_to=None, runs_root=None):
    """Export one or more inputs selected on the command line."""
    if compare_data and len(data) != 1:
        raise ValueError('--compare-data requiere una sola entrada en --data.')
    campaigns = [load_campaign(path, runs_root) for path in data]
    previous = load_campaign(compare_data, runs_root) if compare_data else None
    if previous:
        if {r['run'] for r in previous['runs']} & {r['run'] for r in campaigns[0]['runs']}:
            raise ValueError('Selecciona dos ejecuciones distintas para la comparación.')
        comparison_rows(previous['runs'], campaigns[0]['runs'])
    exporter = Exporter(output)
    for index, campaign in enumerate(campaigns, 1):
        name = prefix if len(campaigns) == 1 else '%s_%d' % (prefix, index)
        export_campaign(campaign, exporter, name)
    if previous:
        export_repetitions(previous, campaigns[0], exporter)
    manifest = exporter.finish()
    if copy_to:
        target = Path(copy_to)
        target.mkdir(parents=True, exist_ok=True)
        files = [manifest] + [exporter.output / f['path'] for item in exporter.figures for f in item['files']]
        for path in files:
            destination = target / path.name
            if destination.exists() and sha(destination) != sha(path):
                raise FileExistsError(destination)
        for path in files:
            destination = target / path.name
            if not destination.exists():
                shutil.copyfile(path, destination)
            if sha(destination) != sha(path):
                raise IOError('La copia no coincide: ' + str(destination))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, nargs='+', required=True, help='Corridas, informes o carpetas de datos para gráficas.')
    parser.add_argument('--output', type=Path, default=ROOT / 'images/graficas_independientes')
    parser.add_argument('--runs-root', type=Path, help='Carpeta que contiene los registros originales por identificador.')
    parser.add_argument('--compare-data', type=Path, help='Primera ejecución de los mismos casos.')
    parser.add_argument('--prefix', default='movilidad')
    parser.add_argument('--copy-to', '--thesis-output', type=Path)
    args = parser.parse_args()
    export_collection(args.data, args.output, args.prefix, args.compare_data, args.copy_to, args.runs_root)


if __name__ == '__main__':
    main()
