import random
import time
import carla


NUM_VEHICLES = 50
SIMULATION_SECONDS = 120
SEED = 42


def main():
    random.seed(SEED)

    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)

    world = client.get_world()
    blueprints = world.get_blueprint_library()

    vehicle_bps = blueprints.filter("vehicle.*")
    spawn_points = world.get_map().get_spawn_points()

    print("Mapa actual:", world.get_map().name)
    print("Spawn points disponibles:", len(spawn_points))

    if len(spawn_points) == 0:
        print("No hay spawn points disponibles en este mapa.")
        return

    traffic_manager = client.get_trafficmanager(8000)
    traffic_manager.set_global_distance_to_leading_vehicle(2.5)
    traffic_manager.set_random_device_seed(SEED)

    vehicles = []

    try:
        random.shuffle(spawn_points)

        amount = min(NUM_VEHICLES, len(spawn_points))

        for spawn_point in spawn_points[:amount]:
            bp = random.choice(vehicle_bps)

            if bp.has_attribute("color"):
                color = random.choice(bp.get_attribute("color").recommended_values)
                bp.set_attribute("color", color)

            vehicle = world.try_spawn_actor(bp, spawn_point)

            if vehicle is not None:
                vehicle.set_autopilot(True, traffic_manager.get_port())
                vehicles.append(vehicle)

        print(f"Vehículos creados: {len(vehicles)}")
        print(f"Simulación activa durante {SIMULATION_SECONDS} segundos.")
        print("Podés moverte manualmente con la cámara del simulador.")

        time.sleep(SIMULATION_SECONDS)

    finally:
        print("Eliminando vehículos...")
        for vehicle in vehicles:
            if vehicle is not None:
                vehicle.destroy()


if __name__ == "__main__":
    main()