"""Analyze the four graduation metrics in preserved CARLA run directories."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.mobility_analysis import analyze_run, paired_checks


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="*", type=Path)
    parser.add_argument("--campaign", type=Path, help="Manifest with cases/run_directories; paths relative to data/output")
    parser.add_argument("--output", type=Path, required=True, help="New report directory; never overwrites inputs")
    args = parser.parse_args()
    paths = list(args.runs)
    if args.campaign:
        campaign = json.loads(args.campaign.read_text(encoding="utf8"))
        if campaign.get("status") != "completed" or any(c.get("status") != "completed" for c in campaign["cases"]):
            raise ValueError("Campaign is incomplete; analyze finished run directories explicitly instead.")
        paths += [ROOT / "data/output" / name for c in campaign["cases"] for name in c["run_directories"]]
    if not paths or len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("Specify distinct run directories or a completed campaign.")
    runs = [analyze_run(path) for path in paths]
    if len({r["run"] for r in runs}) != len(runs):
        raise ValueError("Duplicate run IDs")
    pairs = paired_checks(runs)
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(analysis_version=1, runs=runs, pairs=pairs,
                  interpretation="Descriptive comparison; incomplete durations are not complete travel times. Events are callbacks, not accidents.")
    (args.output / "analysis.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf8")
    summary, destinations = [], []
    for run in runs:
        row = {k: run[k] for k in ["run", "scenario", "seed", "vehicle_count", "simulation_duration_s", "completed", "incomplete_count"]}
        row.update(mean_completed_trip_s=run["travel_time"]["mean_s"], median_completed_trip_s=run["travel_time"]["median_s"],
                   mean_speed_kmh=run["speed"]["mean_kmh"], exposure_scope=run["exposure"]["scope"],
                   distance_m=run["exposure"]["distance_m"], vehicle_time_s=run["exposure"]["vehicle_time_s"],
                   collisions=run["events"]["collision"]["observed_callbacks"],
                   invasions=run["events"]["lane_invasion"]["observed_callbacks"],
                   invasions_per_vehicle_km=run["events"]["lane_invasion"]["per_vehicle_km"],
                   collisions_per_vehicle_km=run["events"]["collision"]["per_vehicle_km"],
                   integrity_errors=len(run["integrity_errors"]))
        summary.append(row)
        for population, levels in run["destinations"].items():
            for level, bins in levels.items():
                destinations.extend(dict(run=run["run"], population=population, level=level, **item) for item in bins)
    write_csv(args.output / "summary.csv", summary, summary[0].keys())
    write_csv(args.output / "destinations.csv", destinations, ["run", "population", "level", "value", "count", "proportion"])
    text = ["# Comparación descriptiva de movilidad", "", report["interpretation"], "",
            "Tiempo: solo viajes completados, incluidas sus esperas. Se conservan todos los incompletos en analysis.json.",
            "Las tasas distinguen colisiones e invasiones y usan la exposición indicada por corrida.", "",
            "| Escenario | Semilla | Vehículos | Completados | Incompletos | Tiempo medio (s) | Velocidad media (km/h) | Invasiones / vehículo-km |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    display = lambda value: "N/D" if value is None else "%.3f" % value
    for row in summary:
        text.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            row["scenario"], row["seed"], row["vehicle_count"], row["completed"], row["incomplete_count"],
            display(row["mean_completed_trip_s"]), display(row["mean_speed_kmh"]), display(row["invasions_per_vehicle_km"])))
    text += ["", "## Comparabilidad y cobertura", ""]
    for pair in pairs:
        text.append("- %s: %s." % (pair["group"], "condiciones registradas coinciden" if pair["comparable"] else ", ".join(pair["differences"])))
    for run in runs:
        text.append("- `%s`: %s; estados %s; errores de integridad %s." % (run["run"], run["exposure"]["scope"], run["statuses"], run["integrity_errors"]))
        text.extend("  - " + warning for warning in run["warnings"])
    text += ["", "Las distribuciones de destinos asignados y alcanzados, por ID y categoría, están en destinations.csv.",
             "No se interpreta un evento de marca como infracción ni se establece significancia estadística a partir de estas tablas.", ""]
    (args.output / "report.md").write_text("\n".join(text), encoding="utf8")
    print("Report:", args.output.resolve())
    for run in runs:
        print(run["scenario"], run["seed"], run["statuses"], "invasions", run["events"]["lane_invasion"]["observed_callbacks"],
              "integrity_errors", run["integrity_errors"])
    return int(any(r["integrity_errors"] for r in runs) or any(not p["comparable"] for p in pairs))


if __name__ == "__main__":
    raise SystemExit(main())
