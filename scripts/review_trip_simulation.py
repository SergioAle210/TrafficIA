"""Observe unchanged trip driving, optionally without GPU camera sensors."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_trip_simulation import configuration_from_args, parse_args
from src.recording.visual_review import VisualReviewSimulation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-cameras', action='store_true',
                        help='Registra fases y paradas sin crear cámaras RGB; no produce evidencia visual.')
    args = parse_args(parser)
    config = configuration_from_args(args)
    path = VisualReviewSimulation(config, ROOT, args.simulation_speed,
        str(args.carla_pythonapi) if args.carla_pythonapi else None,
        capture_images=not args.no_cameras).run()
    print('Revisión guardada en:', path)


if __name__ == '__main__':
    main()
