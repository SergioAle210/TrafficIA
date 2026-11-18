"""Collect selected TrafficIA galleries and diagnostic figures with their provenance."""
import argparse
import hashlib
import html
import json
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def gallery_entries(folder):
    """Accept both a plotted gallery and the independent exporter's manifest."""
    folder = folder.resolve()
    manifest = folder / 'figures_manifest.json'
    if not manifest.is_file():
        manifest = folder / 'manifest.json'
    if not manifest.is_file():
        raise ValueError('Genera primero la galería o usa --independent con tus registros: ' + str(folder))
    for item in json.loads(manifest.read_text(encoding='utf8'))['figures']:
        name = item['name']
        records = item.get('files') or [{'path': name + ext} for ext in ('.png', '.svg')]
        files = []
        for record in records:
            source = (folder / record['path']).resolve()
            source.relative_to(folder)
            if source.suffix.lower() not in ('.png', '.svg'):
                continue
            files.append((source, record.get('sha256')))
        yield item['title'], item.get('note', item.get('method', '')), files, manifest


def tex_escape(text):
    special = {'\\': r'\textbackslash{}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(special.get(c, '\\' + c if c in '#$%&_{}' else c) for c in text)


def write_catalog(directory, figures):
    cards, lines, snippets = [], ['# Catálogo de figuras', ''], []
    for figure in figures:
        png = next(f['path'] for f in figure['files'] if f['path'].endswith('.png'))
        title, caption = figure['title'], figure['caption']
        image = html.escape(quote(png), quote=True)
        links = ' · '.join('<a href="{}">{}</a>'.format(html.escape(quote(f['path'])), Path(f['path']).suffix[1:].upper())
                          for f in figure['files'])
        cards.append('<article><h2>{}</h2><img loading="lazy" src="{}" alt="{}"><p>{}</p>{}</article>'.format(
            html.escape(title), image, html.escape(title, quote=True), html.escape(caption), links))
        lines.extend(['## ' + title.replace('\n', ' '), '', caption.replace('\n', ' '), '', '[PNG](' + quote(png) + ')', ''])
        snippets.extend([r'\begin{figure}[htbp]', r'  \centering', r'  \includegraphics[width=\linewidth]{' + png + '}',
                         r'  \caption{' + tex_escape(title) + '}', r'\end{figure}', ''])
    page = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Colección de TrafficIA</title><style>body{font:1rem system-ui;max-width:70rem;margin:2rem auto;padding:1rem}'
            'img{max-width:100%}article{margin-bottom:3rem}</style><main><h1>Colección de TrafficIA</h1>'
            '<label>Buscar figura <input id="search" type="search"></label>' + ''.join(cards) +
            '</main><script>document.querySelector("#search").oninput=e=>{for(const card of document.querySelectorAll("article"))'
            'card.hidden=!card.textContent.toLowerCase().includes(e.target.value.toLowerCase())}</script></html>')
    (directory / 'index.html').write_text(page, encoding='utf8')
    (directory / 'README.md').write_text('\n'.join(lines), encoding='utf8')
    (directory / 'figuras_resultados.tex').write_text('\n'.join(snippets), encoding='utf8')
    (directory / 'catalogo.json').write_text(json.dumps({'figures': figures, 'figure_count': len(figures)},
                                                        ensure_ascii=False, indent=2), encoding='utf8')


def build_collection(galleries, extra_files, output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError('Elige una carpeta nueva para la colección: ' + str(output))
    entries = [entry for folder in galleries for entry in gallery_entries(folder)]
    for source in extra_files:
        source = source.resolve()
        if source.suffix.lower() != '.png':
            raise ValueError('--figure requiere una imagen PNG.')
        files = [(source, None)]
        if source.with_suffix('.svg').is_file():
            files.append((source.with_suffix('.svg'), None))
        entries.append((source.stem, '', files, None))
    if not entries:
        raise ValueError('La colección requiere al menos una figura.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(output.parent)) as temp:
        directory = Path(temp) / 'collection'
        images = directory / 'figuras'
        images.mkdir(parents=True)
        figures = []
        for index, (title, caption, sources, manifest) in enumerate(entries, 1):
            files = []
            formats = set()
            for source, expected_hash in sources:
                ext = source.suffix.lower()
                if ext in formats:
                    raise ValueError('Formato duplicado en la figura: ' + title)
                formats.add(ext)
                destination = images / ('figura_%03d%s' % (index, ext))
                digest = sha(source)
                if expected_hash and expected_hash != digest:
                    raise ValueError('La figura cambió desde su exportación: ' + str(source))
                shutil.copyfile(source, destination)
                if sha(destination) != digest:
                    raise IOError('La copia no coincide: ' + str(source))
                if ext == '.png':
                    with Image.open(destination) as image:
                        image.verify()
                files.append(dict(path=destination.relative_to(directory).as_posix(), source=str(source), sha256=digest))
            if '.png' not in formats:
                raise ValueError('Falta el PNG de la figura: ' + title)
            figures.append(dict(title=title, caption=caption, manifest=str(manifest) if manifest else None, files=files))
        write_catalog(directory, figures)
        directory.rename(output)
    print('Colección guardada en', output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, nargs='+', default=[], help='Carpetas de galerías o entradas para --independent.')
    parser.add_argument('--figure', type=Path, nargs='+', default=[], help='Imágenes PNG de diagnóstico adicionales.')
    parser.add_argument('--output', type=Path, help='Carpeta de destino de la colección.')
    parser.add_argument('--independent', action='store_true', help='Generar gráficas desde los registros o derivados indicados en --data.')
    parser.add_argument('--compare-data', type=Path, help='Primera ejecución para comparar en modo independiente.')
    parser.add_argument('--runs-root', type=Path, help='Raíz de los registros para la exportación independiente.')
    parser.add_argument('--copy-to', '--thesis-output', type=Path, help='Copia adicional de la exportación independiente.')
    args = parser.parse_args()
    if args.independent:
        if not args.data or args.figure:
            parser.error('--independent requiere --data y admite únicamente registros o derivados.')
        sys.path.insert(0, str(ROOT))
        from scripts.figures.export_charts import export_collection
        output = args.output or ROOT / 'images/graficas_independientes'
        export_collection(args.data, output, compare_data=args.compare_data, copy_to=args.copy_to, runs_root=args.runs_root)
    else:
        if args.compare_data or args.copy_to or args.runs_root:
            parser.error('--compare-data, --copy-to y --runs-root requieren --independent.')
        build_collection(args.data, args.figure, args.output or ROOT / 'images/coleccion')


if __name__ == '__main__':
    main()
