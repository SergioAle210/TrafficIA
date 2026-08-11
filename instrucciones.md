# instrucciones.md

## Contexto general del proyecto

Este repositorio corresponde al proyecto:

**Desarrollo de un generador de tráfico urbano en CARLA mediante un modelo estocástico de elección de destinos y planificación de rutas para análisis de movilidad en escenarios simulados.**

El objetivo no es crear un sistema completo de conducción autónoma, sino construir una base técnica escalable para ejecutar corridas en CARLA 0.9.15, generar tráfico urbano controlado, registrar datos sintéticos y comparar un generador estocástico de destinos contra un escenario base aleatorio.

El proyecto debe permitir trabajar progresivamente desde una simulación estable con vehículos en Traffic Manager hasta una arquitectura con zonas origen-destino, datos dummy, selección probabilística de destinos, planificación de rutas, registro de métricas y análisis posterior.

---

## Versión de CARLA

Trabajar con:

```text
CARLA 0.9.15
Python API de CARLA 0.9.15
```

El servidor de CARLA se ejecutará manualmente con dentro del directorio de instalación de CARLA:

```powershell
C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low
```

El código de Python debe conectarse al servidor local mediante:

```python
client = carla.Client("localhost", 2000)
client.set_timeout(30.0)
```

---

## Criterios principales del repositorio

1. Mantener una estructura modular y escalable.
2. Evitar nombres de archivos con prefijos numéricos.
3. Usar nombres claros, descriptivos y consistentes.
4. Separar configuración, datos de entrada, datos de salida, scripts ejecutables y módulos fuente.
5. Mantener el modo síncrono como base para reproducibilidad.
6. Usar Traffic Manager para el comportamiento básico de circulación.
7. Usar datos dummy controlados para representar categorías de destino, destinos frecuentes y no frecuentes.
8. No mezclar archivos de configuración con archivos de resultados.
9. Registrar por corrida los datos necesarios para calcular métricas de movilidad.
10. Diseñar el código pensando en crecimiento futuro, aunque al inicio solo se implemente la simulación estable.

---

## Estructura recomendada del repositorio

Crear o mantener la siguiente estructura:

```text
carla-traffic-generator/
│
├── config/
│   ├── scenario_basic.json
│   ├── scenario_low_demand.json
│   ├── scenario_high_demand.json
│   └── traffic_manager.json
│
├── data/
│   ├── input/
│   │   ├── zones_config.csv
│   │   ├── destinations_config.csv
│   │   └── demand_profiles.csv
│   │
│   └── output/
│       └── .gitkeep
│
├── scripts/
│   ├── change_map.py
│   ├── stable_traffic.py
│   ├── generate_dummy_data.py
│   ├── log_basic_metrics.py
│   └── run_experiment.py
│
├── src/
│   ├── __init__.py
│   ├── connection.py
│   ├── world_settings.py
│   ├── vehicle_manager.py
│   ├── traffic_manager_config.py
│   ├── zones.py
│   ├── stochastic_model.py
│   ├── route_planner.py
│   ├── sensors.py
│   ├── logger.py
│   └── analysis.py
│
├── README.md
├── requirements.txt
└── instrucciones.md
```

### Nota sobre nombres de archivos

No usar nombres como:

```text
01_stable_traffic.py
02_log_basic_metrics.py
03_spawn_with_destinations.py
```

Usar nombres sin prefijos numéricos:

```text
stable_traffic.py
log_basic_metrics.py
spawn_with_destinations.py
generate_dummy_data.py
```

La lógica del archivo `01_stable_traffic.py` puede tomarse como base, pero el archivo final debe llamarse:

```text
stable_traffic.py
```

---

## Enfoque inicial de desarrollo

Antes de implementar el generador estocástico completo, se debe construir una base estable:

```text
1. Conexión a CARLA.
2. Carga de mapa.
3. Activación de modo síncrono.
4. Configuración de Traffic Manager.
5. Creación controlada de vehículos.
6. Reducción de choques mediante parámetros conservadores.
7. Registro básico de velocidad y vehículos detenidos.
8. Limpieza correcta de actores al finalizar.
```

No iniciar todavía con rutas complejas ni matrices origen-destino hasta que el tráfico base sea estable.

---

## Reglas de ejecución recomendadas

Para desarrollo inicial:

```powershell
.\CarlaUE4.exe -quality-level=Low
python .\scripts\stable_traffic.py --town Town03 --vehicles 10 --seconds 60
```

Luego probar:

```powershell
python .\scripts\stable_traffic.py --town Town03 --vehicles 20 --seconds 90
python .\scripts\stable_traffic.py --town Town03 --vehicles 30 --seconds 120
```

Cuando la simulación sea estable:

```powershell
python .\scripts\stable_traffic.py --town Town03 --vehicles 30 --seconds 120 --no-rendering
```

---

## Recomendación de modos de simulación

Usar siempre:

```text
synchronous_mode = True
fixed_delta_seconds = 0.05
```

Durante depuración visual:

```text
no_rendering_mode = False
```

Durante corridas largas o múltiples experimentos:

```text
no_rendering_mode = True
```

No confundir modo síncrono con no-rendering:

```text
Modo síncrono: controla el avance del tiempo.
No-rendering: desactiva el renderizado visual.
```

Ambos pueden usarse juntos.

---

## Configuración recomendada de Traffic Manager

Usar una configuración conservadora al inicio:

```text
global_distance_to_leading_vehicle = 5.0
vehicle_percentage_speed_difference = 30.0
auto_lane_change = False
ignore_lights_percentage = 0.0
ignore_signs_percentage = 0.0
ignore_vehicles_percentage = 0.0
ignore_walkers_percentage = 0.0
```

Interpretación:

- Los vehículos deben circular más lento que el límite.
- Deben mantener mayor distancia.
- No deben ignorar semáforos ni señales.
- No deben ignorar otros vehículos.
- El cambio automático de carril debe desactivarse al inicio para reducir comportamientos inestables.

---

## Script base: `stable_traffic.py`

Crear este archivo en:

```text
scripts/stable_traffic.py
```

Código recomendado:

```python
import argparse
import math
import random
import time

import carla


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 2000
TM_PORT = 8000

SEED = 42
FIXED_DELTA_SECONDS = 0.05


def speed_kmh(vehicle: carla.Vehicle) -> float:
    velocity = vehicle.get_velocity()
    speed_ms = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    return speed_ms * 3.6


def get_safe_vehicle_blueprints(world: carla.World):
    blueprint_library = world.get_blueprint_library()
    vehicle_bps = blueprint_library.filter("vehicle.*")

    excluded_keywords = [
        "carlacola",
        "firetruck",
        "ambulance",
        "sprinter",
        "fusorosa",
        "crossbike",
        "diamondback",
        "bh",
        "yamaha",
        "kawasaki",
        "harley",
        "vespa",
    ]

    safe_bps = []

    for bp in vehicle_bps:
        if any(keyword in bp.id.lower() for keyword in excluded_keywords):
            continue

        if bp.has_attribute("number_of_wheels"):
            wheels = int(bp.get_attribute("number_of_wheels"))
            if wheels != 4:
                continue

        safe_bps.append(bp)

    return safe_bps


def destroy_existing_vehicles(world: carla.World):
    actors = world.get_actors()
    vehicles = actors.filter("vehicle.*")

    if len(vehicles) > 0:
        print(f"Eliminando vehículos anteriores: {len(vehicles)}")

    for vehicle in vehicles:
        vehicle.destroy()


def apply_world_settings(world: carla.World, no_rendering: bool):
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
    settings.no_rendering_mode = no_rendering
    world.apply_settings(settings)


def restore_world_settings(world: carla.World, original_settings):
    world.apply_settings(original_settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--town", default="Town03")
    parser.add_argument("--vehicles", type=int, default=20)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--no-rendering", action="store_true")
    args = parser.parse_args()

    random.seed(SEED)

    client = carla.Client(DEFAULT_HOST, DEFAULT_PORT)
    client.set_timeout(30.0)

    print(f"Cargando mapa: {args.town}")
    world = client.load_world(args.town)

    original_settings = world.get_settings()

    traffic_manager = client.get_trafficmanager(TM_PORT)
    traffic_manager.set_synchronous_mode(True)
    traffic_manager.set_random_device_seed(SEED)

    apply_world_settings(world, args.no_rendering)

    vehicles = []

    try:
        destroy_existing_vehicles(world)
        world.tick()

        carla_map = world.get_map()
        spawn_points = carla_map.get_spawn_points()
        vehicle_bps = get_safe_vehicle_blueprints(world)

        print("Mapa actual:", carla_map.name)
        print("Spawn points disponibles:", len(spawn_points))
        print("Blueprints seguros disponibles:", len(vehicle_bps))

        if len(spawn_points) == 0:
            print("No hay spawn points disponibles.")
            return

        if len(vehicle_bps) == 0:
            print("No hay blueprints de vehículos seguros.")
            return

        random.shuffle(spawn_points)

        amount = min(args.vehicles, len(spawn_points))

        for spawn_point in spawn_points[:amount]:
            bp = random.choice(vehicle_bps)

            if bp.has_attribute("color"):
                color = random.choice(bp.get_attribute("color").recommended_values)
                bp.set_attribute("color", color)

            bp.set_attribute("role_name", "autopilot")

            vehicle = world.try_spawn_actor(bp, spawn_point)

            if vehicle is None:
                continue

            vehicle.set_autopilot(True, traffic_manager.get_port())

            traffic_manager.auto_lane_change(vehicle, False)
            traffic_manager.distance_to_leading_vehicle(vehicle, 5.0)
            traffic_manager.vehicle_percentage_speed_difference(vehicle, 30.0)
            traffic_manager.ignore_lights_percentage(vehicle, 0.0)
            traffic_manager.ignore_signs_percentage(vehicle, 0.0)
            traffic_manager.ignore_vehicles_percentage(vehicle, 0.0)
            traffic_manager.ignore_walkers_percentage(vehicle, 0.0)
            traffic_manager.update_vehicle_lights(vehicle, True)

            vehicles.append(vehicle)

        print(f"Vehículos creados: {len(vehicles)}")
        print("Modo síncrono: activo")
        print(f"No-rendering: {args.no_rendering}")
        print(f"Duración: {args.seconds} segundos")

        total_frames = int(args.seconds / FIXED_DELTA_SECONDS)

        for frame in range(total_frames):
            world.tick()

            if frame % int(1.0 / FIXED_DELTA_SECONDS) == 0:
                speeds = [speed_kmh(v) for v in vehicles if v.is_alive]
                avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
                stopped = sum(1 for s in speeds if s < 1.0)

                print(
                    f"t={frame * FIXED_DELTA_SECONDS:6.1f}s | "
                    f"vehículos={len(speeds):3d} | "
                    f"velocidad_promedio={avg_speed:6.2f} km/h | "
                    f"detenidos={stopped:3d}"
                )

            time.sleep(0.001)

    finally:
        print("Eliminando vehículos creados...")

        for vehicle in vehicles:
            if vehicle is not None and vehicle.is_alive:
                vehicle.destroy()

        world.tick()

        traffic_manager.set_synchronous_mode(False)
        restore_world_settings(world, original_settings)

        print("Simulación finalizada correctamente.")


if __name__ == "__main__":
    main()
```

---

## Script para cambiar mapa: `change_map.py`

Crear este archivo en:

```text
scripts/change_map.py
```

Código recomendado:

```python
import argparse

import carla


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--town", default="Town03")
    args = parser.parse_args()

    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)

    world = client.load_world(args.town)
    print("Mapa cargado:", world.get_map().name)


if __name__ == "__main__":
    main()
```

Uso:

```powershell
python .\scripts\change_map.py --town Town03
```

---

## Script para generar datos dummy: `generate_dummy_data.py`

Crear este archivo en:

```text
scripts/generate_dummy_data.py
```

Este script debe generar archivos CSV iniciales para alimentar el generador estocástico. Estos archivos no deben registrar viajes todavía. Solo deben representar la configuración sintética de zonas, destinos y perfiles de demanda.

Archivos que debe crear:

```text
data/input/zones_config.csv
data/input/destinations_config.csv
data/input/demand_profiles.csv
```

Código recomendado:

```python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("data/input")


ZONES = [
    {
        "zone_id": "Z_RES_01",
        "zone_name": "Zona residencial norte",
        "category": "residencial",
        "spawn_indices": "0;1;2;3;4",
        "description": "Zona de origen residencial con baja concentración de actividad comercial.",
    },
    {
        "zone_id": "Z_RES_02",
        "zone_name": "Zona residencial sur",
        "category": "residencial",
        "spawn_indices": "5;6;7;8;9",
        "description": "Zona residencial alternativa para distribuir orígenes.",
    },
    {
        "zone_id": "Z_COM_01",
        "zone_name": "Zona comercial principal",
        "category": "comercial",
        "spawn_indices": "10;11;12;13;14",
        "description": "Destino comercial frecuente con alta atracción de viajes.",
    },
    {
        "zone_id": "Z_COM_02",
        "zone_name": "Zona comercial secundaria",
        "category": "comercial",
        "spawn_indices": "15;16;17;18",
        "description": "Destino comercial no frecuente o de menor atracción.",
    },
    {
        "zone_id": "Z_SER_01",
        "zone_name": "Zona de servicios",
        "category": "servicios",
        "spawn_indices": "19;20;21;22",
        "description": "Zona asociada a servicios urbanos como hospital, banco o trámites.",
    },
    {
        "zone_id": "Z_EDU_01",
        "zone_name": "Zona educativa",
        "category": "educativo",
        "spawn_indices": "23;24;25;26",
        "description": "Zona de destino frecuente asociada a estudios o trabajo académico.",
    },
]


DESTINATIONS = [
    {
        "destination_id": "D_COM_01",
        "zone_id": "Z_COM_01",
        "destination_name": "Centro comercial principal",
        "category": "comercial",
        "frequency_class": "frecuente",
        "weight": 0.25,
        "description": "Destino frecuente asociado a compras y actividad comercial.",
    },
    {
        "destination_id": "D_EDU_01",
        "zone_id": "Z_EDU_01",
        "destination_name": "Universidad o centro educativo",
        "category": "educativo",
        "frequency_class": "frecuente",
        "weight": 0.20,
        "description": "Destino frecuente asociado a movilidad recurrente.",
    },
    {
        "destination_id": "D_SER_01",
        "zone_id": "Z_SER_01",
        "destination_name": "Hospital o servicios principales",
        "category": "servicios",
        "frequency_class": "frecuente",
        "weight": 0.15,
        "description": "Destino frecuente asociado a servicios esenciales.",
    },
    {
        "destination_id": "D_RES_01",
        "zone_id": "Z_RES_01",
        "destination_name": "Retorno residencial norte",
        "category": "residencial",
        "frequency_class": "frecuente",
        "weight": 0.10,
        "description": "Destino frecuente de retorno a zona residencial.",
    },
    {
        "destination_id": "D_RES_02",
        "zone_id": "Z_RES_02",
        "destination_name": "Retorno residencial sur",
        "category": "residencial",
        "frequency_class": "frecuente",
        "weight": 0.10,
        "description": "Destino frecuente de retorno a zona residencial alternativa.",
    },
    {
        "destination_id": "D_COM_02",
        "zone_id": "Z_COM_02",
        "destination_name": "Comercio secundario",
        "category": "comercial",
        "frequency_class": "no_frecuente",
        "weight": 0.07,
        "description": "Destino comercial menos visitado.",
    },
    {
        "destination_id": "D_SER_02",
        "zone_id": "Z_SER_01",
        "destination_name": "Banco o trámite ocasional",
        "category": "servicios",
        "frequency_class": "no_frecuente",
        "weight": 0.05,
        "description": "Destino de servicios con menor frecuencia.",
    },
    {
        "destination_id": "D_REC_01",
        "zone_id": "Z_COM_02",
        "destination_name": "Destino recreativo ocasional",
        "category": "recreativo",
        "frequency_class": "no_frecuente",
        "weight": 0.04,
        "description": "Destino de exploración o recreación.",
    },
    {
        "destination_id": "D_SER_03",
        "zone_id": "Z_SER_01",
        "destination_name": "Gasolinera o servicio rápido",
        "category": "servicios",
        "frequency_class": "no_frecuente",
        "weight": 0.03,
        "description": "Destino ocasional de corta duración.",
    },
    {
        "destination_id": "D_MISC_01",
        "zone_id": "Z_COM_02",
        "destination_name": "Destino misceláneo",
        "category": "miscelaneo",
        "frequency_class": "no_frecuente",
        "weight": 0.01,
        "description": "Destino poco frecuente para conservar variabilidad.",
    },
]


DEMAND_PROFILES = [
    {
        "profile_id": "low_demand",
        "description": "Nivel bajo de demanda para pruebas iniciales.",
        "vehicles": 20,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 2.0,
    },
    {
        "profile_id": "medium_demand",
        "description": "Nivel medio de demanda para pruebas de estabilidad.",
        "vehicles": 40,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 1.5,
    },
    {
        "profile_id": "high_demand",
        "description": "Nivel alto de demanda para evaluación comparativa.",
        "vehicles": 70,
        "routine_probability": 0.80,
        "exploration_probability": 0.20,
        "spawn_interval_seconds": 1.0,
    },
]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No hay filas para escribir en {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_destination_weights(destinations: list[dict]) -> None:
    total_weight = sum(float(row["weight"]) for row in destinations)

    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            f"La suma de pesos de destinos debe ser 1.0, pero actualmente es {total_weight:.6f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directorio donde se crearán los CSV de entrada.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    validate_destination_weights(DESTINATIONS)

    zones_path = output_dir / "zones_config.csv"
    destinations_path = output_dir / "destinations_config.csv"
    demand_profiles_path = output_dir / "demand_profiles.csv"

    write_csv(zones_path, ZONES)
    write_csv(destinations_path, DESTINATIONS)
    write_csv(demand_profiles_path, DEMAND_PROFILES)

    print("Datos dummy generados correctamente:")
    print(f"- {zones_path}")
    print(f"- {destinations_path}")
    print(f"- {demand_profiles_path}")


if __name__ == "__main__":
    main()
```

Uso:

```powershell
python .\scripts\generate_dummy_data.py
```

Resultado esperado:

```text
data/input/zones_config.csv
data/input/destinations_config.csv
data/input/demand_profiles.csv
```

---

## Significado de los CSV dummy

### `zones_config.csv`

Representa zonas del mapa de CARLA.

Campos sugeridos:

```text
zone_id
zone_name
category
spawn_indices
description
```

Este archivo pertenece al:

```text
Módulo de zonas
```

Sirve para agrupar spawn points en zonas lógicas.

---

### `destinations_config.csv`

Representa los destinos posibles del generador.

Campos sugeridos:

```text
destination_id
zone_id
destination_name
category
frequency_class
weight
description
```

Este archivo pertenece al:

```text
Módulo estocástico
Módulo de zonas
```

Sirve para seleccionar destinos frecuentes y no frecuentes.

---

### `demand_profiles.csv`

Representa niveles de demanda.

Campos sugeridos:

```text
profile_id
description
vehicles
routine_probability
exploration_probability
spawn_interval_seconds
```

Este archivo pertenece al:

```text
Archivo de configuración
Módulo ODD
Módulo estocástico
```

Sirve para diferenciar baja, media y alta demanda.

---

## Importante sobre datos dummy

Los datos dummy son datos de configuración, no resultados de simulación.

No mezclar:

```text
data/input/
```

con:

```text
data/output/
```

Correcto:

```text
data/input/destinations_config.csv      # destinos posibles
data/output/run_001/trips_log.csv       # viajes generados
```

Incorrecto:

```text
data/input/destinations_config.csv      # destinos posibles y viajes registrados en el mismo archivo
```

La configuración debe permanecer fija para que los experimentos sean reproducibles.

---

## Escenario base aleatorio

Implementar posteriormente un modo llamado:

```text
random_baseline
```

En este modo, todos los destinos tienen la misma probabilidad.

Ejemplo:

```text
D01 = 10 %
D02 = 10 %
D03 = 10 %
D04 = 10 %
D05 = 10 %
D06 = 10 %
D07 = 10 %
D08 = 10 %
D09 = 10 %
D10 = 10 %
```

Este escenario sirve como comparación base.

---

## Escenario estocástico propuesto

Implementar posteriormente un modo llamado:

```text
stochastic_model
```

En este modo, los destinos usan pesos definidos en `destinations_config.csv`.

Ejemplo:

```text
D_COM_01 = 25 %
D_EDU_01 = 20 %
D_SER_01 = 15 %
D_RES_01 = 10 %
D_RES_02 = 10 %
D_COM_02 = 7 %
D_SER_02 = 5 %
D_REC_01 = 4 %
D_SER_03 = 3 %
D_MISC_01 = 1 %
```

La comparación entre `random_baseline` y `stochastic_model` debe mantener constantes:

```text
mapa
clima
duración
número de vehículos
Traffic Manager
semillas
ODD
criterio de llegada
métricas calculadas
```

La única diferencia debe ser la lógica de elección de destino.

---

## Métricas objetivo

El proyecto debe permitir calcular posteriormente:

```text
distribución de destinos
tiempo promedio de viaje
velocidad media
tasa de colisiones
tasa de invasiones de carril
distancia recorrida
cantidad de viajes completados
viajes incompletos
densidad aproximada
flujo vehicular aproximado
concentración de viajes
```

Inicialmente, solo implementar velocidad promedio y vehículos detenidos en consola.

Después, agregar logs CSV.

---

## Archivos de salida esperados por corrida

Cada corrida debe guardar sus resultados en una carpeta independiente:

```text
data/output/run_001/
│
├── run_config.json
├── trips_log.csv
├── trajectory_log.csv
├── events_log.csv
└── metrics_summary.csv
```

### `run_config.json`

Debe guardar la configuración exacta usada en la corrida:

```text
mapa
clima
duración
número de vehículos
semilla
modo síncrono
no-rendering
escenario
perfil de demanda
parámetros de Traffic Manager
```

### `trips_log.csv`

Debe guardar un resumen por vehículo o viaje:

```text
run_id
vehicle_id
origin_zone
destination_id
destination_category
frequency_class
departure_time
arrival_time
travel_time
distance_m
avg_speed_kmh
status
```

### `trajectory_log.csv`

Debe guardar datos por tick o por intervalo:

```text
run_id
time
frame
vehicle_id
x
y
z
speed_kmh
```

### `events_log.csv`

Debe guardar eventos:

```text
run_id
time
frame
vehicle_id
event_type
event_description
other_actor_id
```

### `metrics_summary.csv`

Debe guardar métricas agregadas:

```text
run_id
scenario
vehicles
completed_trips
incomplete_trips
avg_travel_time
avg_speed_kmh
collision_rate
lane_invasion_rate
```

---

## Buenas prácticas de código

1. Usar funciones pequeñas.
2. Evitar código duplicado.
3. Usar `argparse` en scripts ejecutables.
4. Usar `pathlib.Path` para rutas.
5. Usar encoding `utf-8`.
6. Usar nombres en inglés para archivos, funciones y variables.
7. Usar comentarios breves cuando el bloque no sea evidente.
8. No dejar actores vivos al finalizar.
9. Restaurar configuración original del mundo al terminar.
10. Capturar errores de conexión con mensajes claros.

---

## Requisitos iniciales

Crear `requirements.txt` con:

```text
numpy
pandas
matplotlib
```

No incluir `carla` en `requirements.txt` si se está usando la distribución local de CARLA, porque normalmente el paquete se instala desde el `.egg` incluido en CARLA o desde la configuración local del entorno.

---

## README mínimo sugerido

El `README.md` debe incluir:

```text
1. Nombre del proyecto.
2. Versión de CARLA.
3. Descripción breve.
4. Estructura del repositorio.
5. Cómo ejecutar CARLA.
6. Cómo cambiar de mapa.
7. Cómo ejecutar tráfico estable.
8. Cómo generar datos dummy.
9. Próximos pasos del proyecto.
```

---

## Orden de implementación sugerido

Implementar en este orden:

```text
1. Crear estructura del repositorio.
2. Crear scripts/change_map.py.
3. Crear scripts/stable_traffic.py.
4. Crear scripts/generate_dummy_data.py.
5. Crear data/input/ mediante generate_dummy_data.py.
6. Crear config/scenario_basic.json.
7. Crear README.md.
8. Probar stable_traffic.py con Town03 y 10 vehículos.
9. Probar con 20 y 30 vehículos.
10. Agregar logging básico en log_basic_metrics.py.
11. Separar lógica común hacia src/.
12. Implementar stochastic_model.py.
13. Implementar comparación random_baseline vs stochastic_model.
```

---

## Alcance inmediato

Por ahora, NO implementar todavía:

```text
sensores de colisión
sensores de invasión de carril
planificación completa de rutas
comparación estadística final
visualizaciones avanzadas
Google Maps API
```

Eso se implementará después de tener una base estable.

---

## Criterio de éxito de la primera fase

La primera fase se considera completa cuando:

```text
1. CARLA carga Town03 correctamente.
2. stable_traffic.py crea entre 10 y 30 vehículos.
3. Los vehículos se mueven con Traffic Manager.
4. La simulación corre en modo síncrono.
5. El script imprime velocidad promedio y vehículos detenidos.
6. El script elimina los vehículos al finalizar.
7. El script restaura la configuración original del mundo.
8. generate_dummy_data.py crea correctamente los CSV de entrada.
```

---

## Nota final para Codex

Priorizar que el proyecto funcione de forma simple antes de hacerlo más complejo.

El primer objetivo no es construir todo el generador completo, sino dejar una base sólida y escalable para trabajar con CARLA 0.9.15 de manera controlada, reproducible y compatible con un futuro modelo estocástico de elección de destinos.
