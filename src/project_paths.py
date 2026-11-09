"""Resolve relocated inputs without rewriting frozen JSON or CSV files."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Paths stored in historical configurations/manifests retain their original text.
# Only their physical location changes; existing snapshots always take priority.
RELOCATIONS = {
    "config/single_vehicle_trip.json": "config/trips/single_vehicle_trip.json",
    "config/single_vehicle_trip_cyclic.json": "config/trips/single_vehicle_trip_cyclic.json",
    "config/multi_vehicle_trip.json": "config/trips/multi_vehicle_trip.json",
    "config/scenario_basic.json": "config/examples/scenario_basic.json",
    "config/scenario_low_demand.json": "config/examples/scenario_low_demand.json",
    "config/scenario_high_demand.json": "config/examples/scenario_high_demand.json",
    "config/traffic_manager.json": "config/examples/traffic_manager.json",
    "config/pilots": "config/experiments/scaling_pilots",
    "config/demand_20_100": "config/experiments/demand_20_100",
    "data/input/Town01/destinations_config.csv": "data/input/catalogs/Town01/destinations_config.csv",
    "data/input/Town03/destinations_config.csv": "data/input/catalogs/Town03/destinations_config.csv",
    "data/input/Town01/vehicle_history_dummy.csv": "data/input/histories/Town01/bootstrap/vehicle_history_dummy.csv",
    "data/input/Town01/pilots": "data/input/histories/Town01/scaling_pilots",
    "data/input/Town01/demand_20_100": "data/input/histories/Town01/demand_20_100",
    "data/input/zones_config.csv": "data/input/examples/zones_config.csv",
    "data/input/destinations_config.csv": "data/input/examples/destinations_config.csv",
    "data/input/demand_profiles.csv": "data/input/examples/demand_profiles.csv",
}


def project_path(value, root=PROJECT_ROOT):
    """Resolve an input path under root, preserving existing files and snapshots.

    The returned path can also be used by preparation scripts when writing a
    new input. Unknown paths are not guessed or searched in unrelated folders.
    """
    root = Path(root).resolve()
    supplied = Path(value)
    candidate = supplied if supplied.is_absolute() else root / supplied
    candidate = candidate.resolve()
    if candidate.exists():
        return candidate
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return candidate
    for old, new in RELOCATIONS.items():
        try:
            suffix = relative.relative_to(old)
        except ValueError:
            continue
        return root / new / suffix
    return candidate
