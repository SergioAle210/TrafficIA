import carla

client = carla.Client("localhost", 2000)
client.set_timeout(30.0)

world = client.load_world("Town01")
print("Mapa cargado:", world.get_map().name)