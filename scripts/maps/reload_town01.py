"""Reload Town01 on the local CARLA server, including when the map is already active."""

import argparse


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    import carla
    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)
    world = client.load_world("Town01")
    print("Mapa cargado:", world.get_map().name)


if __name__ == "__main__":
    main()
