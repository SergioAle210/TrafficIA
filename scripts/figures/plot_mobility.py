"""Plot mobility metrics from a TrafficIA run, analysis directory, or campaign plotting inputs."""
import argparse
import html
import os
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/output/.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

COLORS=['#2463A6','#D98420','#2463A6','#D98420']
SHORT=[]
CATS=['residential','services_leisure','work_education']
CAT_NAMES=['Residencia','Servicios / ocio','Trabajo / educación']
CAT_COLORS=['#508D86','#8A71B3','#DDA94C']


def style():
    """Set shared fonts, colors, and axis styles for the campaign figures."""
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
                         'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.titlepad':12,'figure.facecolor':'white','axes.facecolor':'white',
                         'text.color':'#182B3A','axes.labelcolor':'#334155','axes.edgecolor':'#94A3B8',
                         'grid.color':'#CBD5E1','grid.alpha':.45,'svg.fonttype':'none'})


def metric_label(value, fmt):
    """Keep an undefined travel time or rate distinct from a measured zero."""
    return 'N/D' if pd.isna(value) else format(value, fmt)


def bars(ax,values,title,ylabel,fmt='.1f',colors=COLORS):
    """Draw and label campaign cases using consistent colors and units."""
    values = np.asarray(values, dtype=float)
    positions = range(len(values))
    palette = [colors[i % len(colors)] for i in positions]
    ax.bar(positions, values, color=palette, width=.65)
    ax.scatter(positions, values, color=palette, s=15, zorder=3)
    labels = SHORT if len(SHORT) == len(values) else [str(i + 1) for i in positions]
    ax.set(xticks=positions, xticklabels=labels,title=title,ylabel=ylabel)
    ax.grid(axis='y');ax.set_axisbelow(True)
    maximum = max(values[np.isfinite(values)], default=0) or 1
    ax.set_ylim(0,maximum*1.24)
    for x, value in enumerate(values):
        y = value if np.isfinite(value) else 0
        ax.text(x, y + maximum * .035, metric_label(value, fmt), ha='center', fontsize=10, fontweight='bold')


class Figures:
    def __init__(self,out):
        """Prepare figure tracking and open the campaign's multipage PDF."""
        self.out=out;self.items=[];self.pdf=PdfPages(out/'graficas_campana.pdf')
    def save(self,fig,name,title,note,group='objetivos'):
        """Save a titled figure to image files and the campaign PDF, then record its details."""
        fig.suptitle(title,fontsize=17,fontweight='bold',x=.04,ha='left',y=.985)
        fig.text(.04,.018,note,fontsize=9,color='#475569',va='bottom')
        fig.tight_layout(rect=(.015,.075,.995,.925))
        fig.savefig(self.out/(name+'.png'),dpi=170)
        fig.savefig(self.out/(name+'.svg'))
        self.pdf.savefig(fig)
        plt.close(fig);self.items.append(dict(name=name,title=title,note=note,group=group))


def write_gallery(output, exporter, campaign, prefix, runs_root):
    items = []
    report = ['# Gráficas de movilidad', '', '| Corrida | Vehículos | Semilla | Selector | Duración simulada (s) | Llegadas |',
              '|---|---:|---:|---|---:|---:|']
    for run in campaign['runs']:
        report.append('| {run} | {vehicle_count} | {seed} | {scenario} | {simulation_duration_s:g} | {completed} |'.format(**run))
    cards = []
    for figure in exporter.figures:
        name, title, note = figure['name'], figure['title'], figure['method']
        items.append(dict(figure, note=note))
        cards.append('<section><h2>{}</h2><p>{}</p><a href="{}.svg"><img src="{}.png" alt="{}" loading="lazy"></a></section>'.format(
            html.escape(title), html.escape(note), html.escape(name, quote=True), html.escape(name, quote=True), html.escape(title, quote=True)))
        report.extend(['', '## ' + title, '', note, '', '[Figura](' + name + '.png)'])
    page = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Movilidad · TrafficIA</title><style>body{font:1rem system-ui;margin:2rem auto;max-width:70rem;padding:1rem}'
            'img{max-width:100%}</style><main><h1>Movilidad</h1><nav><a href="graficas_campana.pdf">PDF</a> · '
            '<a href="informe_graficas.md">Informe</a></nav>' + ''.join(cards) + '</main></html>')
    (output / 'index.html').write_text(page, encoding='utf8')
    def quote_ps(value):
        return "'" + str(value).replace("'", "''") + "'"
    command = (r'& .\carla-env\Scripts\python.exe .\scripts\figures\plot_mobility.py --data ' + quote_ps(campaign['data'])
               + ' --output ' + quote_ps(output) + ' --prefix ' + quote_ps(prefix))
    if runs_root:
        command += ' --runs-root ' + quote_ps(runs_root.resolve())
    report.extend(['', '## Reproducir desde la raíz de TrafficIA', '', '```powershell', command, '```'])
    (output / 'informe_graficas.md').write_text('\n'.join(report) + '\n', encoding='utf8')
    exporter.finish('figures_manifest.json', figures=items, source=str(campaign['data']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True, help='Corrida, informe de movilidad o derivados de campaña.')
    outputs = parser.add_mutually_exclusive_group()
    outputs.add_argument('--output', type=Path, help='Directorio de la galería, el PDF y el informe.')
    outputs.add_argument('--independent-output', type=Path, help='Exportar cada gráfica por separado.')
    parser.add_argument('--prefix', default='movilidad', help='Prefijo de los archivos de figuras.')
    parser.add_argument('--runs-root', type=Path, help='Raíz de los registros originales si se trasladaron.')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    from scripts.figures.export_charts import Exporter, export_campaign, load_campaign
    campaign = load_campaign(args.data, args.runs_root)
    if args.independent_output:
        exporter = Exporter(args.independent_output)
        export_campaign(campaign, exporter, args.prefix)
        exporter.finish()
        return
    data = campaign['data']
    output = (args.output or (data if campaign['derived'] else data.with_name(data.name + '_graficas'))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with PdfPages(output / 'graficas_campana.pdf') as pdf:
        exporter = Exporter(output, pdf=pdf)
        export_campaign(campaign, exporter, args.prefix)
    metrics_dir = data
    if campaign['derived'].get('campaign'):
        metrics_dir = Path(campaign['derived']['campaign']).parent / 'metrics'
    for name in ('summary.csv', 'destinations.csv'):
        source = metrics_dir / name
        if source.is_file() and source.resolve() != output / name:
            shutil.copyfile(source, output / name)
    write_gallery(output, exporter, campaign, args.prefix, args.runs_root)
    print('Galería guardada en', output)


if __name__ == '__main__':
    main()
