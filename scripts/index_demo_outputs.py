"""Label existing demonstration runs without changing their configuration or logs."""

import argparse
import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    (20, "random_baseline"): "20_uniforme",
    (20, "history_80_20"): "20_historico_80_20",
    (100, "random_baseline"): "100_uniforme",
    (100, "history_80_20"): "100_historico_80_20",
}
FIELDS = (
    "caso", "vehiculos", "selector", "estado", "carpeta",
    "viajes_completados", "duracion_objetivo_s", "tiempo_proceso_s",
)
LOGS = (
    "run_config.json", "trips_log.csv", "observation_log.csv",
    "events_log.csv", "vehicle_history.csv",
)


def build_rows(campaign_path, data_root=None):
    """Read the campaign's explicit case/run mapping, including unfinished cases."""
    data_root = Path(data_root or ROOT / "data/output").resolve()
    campaign = json.loads(Path(campaign_path).read_text(encoding="utf-8"))
    rows, seen = [], set()
    for case in campaign["cases"]:
        key = (int(case["vehicle_count"]), case["scenario"])
        if key not in ALIASES or key in seen:
            raise ValueError("Combinación desconocida o repetida: {0}".format(key))
        seen.add(key)
        directories = case.get("run_directories", [])
        if len(directories) > 1:
            raise ValueError("Se esperaba una carpeta por caso: " + ALIASES[key])
        run_path = None
        if directories:
            run_path = (data_root / directories[0]).resolve()
            run_path.relative_to(data_root)
            if run_path == data_root:
                raise ValueError("La salida debe ser una subcarpeta de data/output.")
        rows.append({
            "caso": ALIASES[key], "vehiculos": key[0], "selector": key[1],
            "estado": case.get("status", "pending"),
            "carpeta": str(run_path) if run_path is not None else "",
            "viajes_completados": case.get("completed_trips", ""),
            "duracion_objetivo_s": campaign["duration_s"],
            "tiempo_proceso_s": case.get("wall_seconds_process", ""),
        })
    if not rows:
        raise ValueError("La campaña no contiene casos.")
    return rows


def render_html(rows):
    entries = []
    for row in rows:
        run_path = Path(row["carpeta"]) if row["carpeta"] else None
        links = []
        if run_path is not None and run_path.is_dir():
            links.append('<a href="{0}">Abrir carpeta</a>'.format(
                html.escape(run_path.as_uri(), quote=True)))
            for name in LOGS:
                path = run_path / name
                if path.is_file():
                    links.append('<a href="{0}">{1}</a>'.format(
                        html.escape(path.as_uri(), quote=True), html.escape(name)))
        entries.append(
            '<tr><td><strong>{0}</strong></td><td>{1}</td><td>{2}</td><td>{3}</td></tr>'.format(
                html.escape(row["caso"]), html.escape(row["estado"]),
                html.escape(str(row["viajes_completados"])),
                '<br>'.join(links) if links else 'Sin archivos disponibles',
            )
        )
    return '''<!doctype html>
<html lang="es"><meta charset="utf-8">
<title>Demostración de TrafficIA</title>
<style>
body {font: 18px Arial, sans-serif; color: #1f4a76; max-width: 1100px; margin: 40px auto; padding: 0 20px;}
h1, a {color: #0277ab;} table {border-collapse: collapse; width: 100%;}
th, td {padding: 16px; border-bottom: 1px solid #d7e2e9; text-align: left; vertical-align: top;}
th {background: #eaf7ff;} td a {line-height: 1.7;} p {line-height: 1.5;}
</style>
<h1>Demostración de TrafficIA</h1>
<p>El índice identifica las salidas según <code>campaign.json</code>.
Los archivos originales conservan sus nombres y contenido.</p>
<table><thead><tr><th>Caso</th><th>Estado</th><th>Llegadas registradas</th><th>Registros</th></tr></thead>
<tbody>''' + ''.join(entries) + '''</tbody></table>
<p><code>completed</code>: finalizado; <code>pending</code>: pendiente;
<code>running</code>: en ejecución; <code>failed</code>: fallo;
<code>interrupted</code>: interrumpido. Una celda vacía no representa un cero.</p>
<p>Este índice refleja el estado al generarlo. Ejecuta de nuevo el comando de índice para actualizarlo.</p>
</html>'''


def write_index(campaign_path, data_root=None):
    campaign_path = Path(campaign_path).resolve()
    rows = build_rows(campaign_path, data_root)
    csv_path = campaign_path.parent / "indice_demo.csv"
    html_path = campaign_path.parent / "indice_demo.html"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    html_path.write_text(render_html(rows), encoding="utf-8")
    return csv_path, html_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True, help="campaign.json de la demostración.")
    args = parser.parse_args(argv)
    try:
        for path in write_index(args.campaign):
            print(path)
        return 0
    except (OSError, ValueError, KeyError) as error:
        print("No se pudo crear el índice: {0}".format(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
