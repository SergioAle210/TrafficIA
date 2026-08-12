# Iteración: viajes sucesivos con un vehículo en Town01

## Resultado

La primera iteración continúa disponible sin cambios en
`scripts/stable_traffic.py`: genera tráfico estable con Traffic Manager. La
nueva iteración usa exactamente un actor lógico `vehicle_001`, lo reutiliza en
varios viajes y se limita a Town01. No implementa todavía múltiples vehículos,
comparación random-vs-stochastic, peatones, ML ni optimización por congestión.

## Archivos creados

- `config/single_vehicle_trip.json`: parámetros reproducibles de la prueba.
- `data/input/Town01/destinations_config.csv`: tres destinos manuales Lugar A-C
  sobre waypoints viales de Town01.
- `scripts/run_trip_simulation.py`: punto de entrada de la nueva corrida.
- `scripts/inspect_location.py`: obtiene la posición del spectator y el
  waypoint vial apto para registrar destinos manuales.
- `src/destinations.py`: lectura/validación de configuración y selección
  pseudoaleatoria reproducible 80/20.
- `src/route_planner.py`: integración de `GlobalRoutePlanner` y `BasicAgent`.
- `src/run_logger.py`: escritores CSV por corrida.
- `src/trip_runner.py`: ciclo del vehículo, llegada, espera, sensores,
  limpieza, métricas y restauración del mundo.

## Archivos modificados

- `scripts/generate_dummy_data.py`: además de los CSV dummy heredados,
  reconstruye `data/input/Town01/destinations_config.csv`.
- `README.md`: documenta ejecución, rutas, no-rendering, velocidad y captura
  manual de lugares.

## Funcionamiento

La configuración contiene `routine_probability=0.8` y
`exploration_probability=0.2`. Para cada viaje se hace primero esa elección de
clase y luego una selección ponderada dentro de la clase. Se usa una instancia
local `random.Random(seed)`; no se cambia ningún peso como consecuencia de los
resultados. El destino conceptual actual queda excluido.

`GlobalRoutePlanner` construye su grafo desde la topología OpenDRIVE que expone
el mapa de CARLA. `trace_route(origen, destino)` devuelve una secuencia ordenada
de pares `[Waypoint, RoadOption]`, que se entrega a
`BasicAgent.set_global_plan()`. Por tanto “óptima” significa la ruta corta del
grafo vial bajo el costo de ese planificador, no un óptimo ante tráfico,
congestión ni tiempo de recorrido real.

Traffic Manager no se activa para el nuevo actor: para validar seguimiento de
ruta completo, `BasicAgent` recibe y ejecuta el plan explícito. La configuración
de Traffic Manager sigue empleándose exclusivamente por la simulación estable
anterior.

Tras llegar dentro de `arrival_threshold_m`, el vehículo frena y se mantiene en
espera durante `destination_dwell_time_seconds` de tiempo de CARLA. Entonces se
incrementa `trip_id`, se selecciona otro destino, se crea otra ruta y el mismo
actor sigue el nuevo viaje. Los tiempos académicos usan
`WorldSnapshot.timestamp.elapsed_seconds`; cualquier pausa de pared solo sirve
para limitar la velocidad visible de la ejecución.

## Formato de CSV

`destinations_config.csv` es configuración: `destination_id`,
`destination_name`, `map`, `category`, `frequency_class`, `weight`, `enabled`,
`reference_type`, `spawn_point_index`, `x`, `y`, `z`, `road_id`, `lane_id` y
`description`. `frequency_class` usa `routine` o `exploration`, equivalentes en
esta prueba a frecuente/rutina y no-frecuente/exploración. Las categorías
provisionales son `residential`, `commercial` y `services`, manteniendo tres
categorías preparadas para el reemplazo definitivo.

Cada `data/output/<run_id>/` contiene:

- `run_config.json`: mapa, versión de servidor CARLA, seed, destinos, modo
  síncrono, delta fijo, no-rendering, configuración de velocidad, selección,
  ruta y controlador.
- `trips_log.csv`: una fila por viaje con origen, destino, tiempos simulados,
  distancia, velocidad media, conteos de eventos y estado.
- `trajectory_log.csv`: muestras configurables con frame, tiempo simulado,
  posición, velocidad, aceleración, road/lane y distancia acumulada.
- `events_log.csv`: colisiones e invasiones de carril separadas, con frame,
  tiempo simulado, actor relacionado y ubicación.
- `metrics_summary.csv`: viajes iniciados/completados/incompletos, tiempo y
  distancia total, velocidad agregada, conteos de eventos y distribución
  observada de destinos.

Los estados posibles registrados son `completed`, `timeout`, `route_failed`,
`blocked` y `aborted`.

## Cambiar Lugar A-C y agregar destinos reales

Ejecuta `inspect_location.py` con Town01 activo, posicionando primero el
spectator junto al lugar conceptual. El script muestra tanto la posición del
spectator como el waypoint de conducción más cercano, `road_id`, `lane_id`,
coordenadas, `s` y el spawn index próximo. Copia la fila propuesta, usando las
coordenadas del waypoint vial; no navegues hacia el interior de un edificio.

Puedes conservar `reference_type=spawn_point` y cambiar
`spawn_point_index`, o usar `reference_type=coordinates` con x/y/z y los IDs
viales inspeccionados. Para esta prueba, mantén las tres filas habilitadas y
sus IDs en `destination_cycle_order`. Para futuros destinos reales, sustituye
las filas manteniendo sus IDs o adapta el ciclo. Cada fila ya tiene categoría,
clase de frecuencia y peso: las categorías definitivas se podrán introducir sin
alterar los resultados históricos.

## Secuencia manual actual

El vehículo aparece en el spawn point 133, cercano a Lugar A, proyectado al
carril de conducción. La selección está en modo `cyclic` y el ciclo configurado
es `T01_B → T01_C → T01_A`: por eso el primer viaje no es hacia A. Tras llegar,
espera el tiempo configurado y continúa con el siguiente ID; después de A vuelve
a B. Para cambiar el orden, edita solo `destination_cycle_order` en
`config/single_vehicle_trip.json` y usa IDs existentes, sin repetirlos dentro
de la misma vuelta.

Para inspeccionar visualmente los spawn points, ejecuta:

```powershell
python .\scripts\inspect_location.py --town Town01 --show-spawn-points --highlight-spawn-point 133 --debug-lifetime-seconds 300
```

CARLA dibuja los índices y su orientación; el punto resaltado aparece en rojo.

## Limitaciones conocidas

- Los tres waypoints manuales se validan al inicio contra el `road_id` y
  `lane_id` de Town01. Si se modifica el mapa o una coordenada, vuelve a
  ejecutar `inspect_location.py` y actualiza la fila correspondiente.
- La reproducibilidad de selección está cubierta por la semilla. La trayectoria
  física puede seguir dependiendo de la versión exacta de CARLA, condiciones del
  servidor y controlador; `run_config.json` conserva esos parámetros.
- La detección de bloqueo usa un umbral de velocidad y duración configurable;
  puede requerir calibración al incorporar tráfico adicional.
- `--simulation-speed 2..5` es un objetivo de ritmo de pared, no una garantía
  de multiplicador ni una modificación de `fixed_delta_seconds`.
- Si el spawn inicial está ocupado, la configuración actual falla de forma
  explícita para no cambiar el origen. Se puede habilitar el fallback de manera
  consciente con `initial_spawn_fallback_enabled=true`.
- Antes de crear el vehículo, el transform de cada spawn se proyecta al waypoint
  de conducción más cercano; esto evita que un spawn defectuoso lo ubique dentro
  de una casa o fuera de la carretera.
- El origen inicial se fija mediante `initial_spawn_point_index` en
  `config/single_vehicle_trip.json`; `initial_spawn_fallback_enabled=false`
  asegura que la corrida no cambie automáticamente a otra posición.
- Las dependencias de `GlobalRoutePlanner` y `BasicAgent` (`networkx` y
  `shapely`) se verifican antes de crear actores; se instalan con
  `python -m pip install -r .\requirements.txt`.
- Después de crear el vehículo se avanza un frame síncrono antes de calcular la
  primera ruta. La posición real se valida contra el spawn y el primer waypoint
  se valida contra el origen; una desalineación cancela el viaje antes de
  aplicar control. Esto corrige el giro hacia paredes causado por planificar
  temporalmente desde `(0,0,0)`.

## Comandos PowerShell

En una consola de CARLA:

```powershell
cd C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low
```

En otra consola, desde este repositorio, carga Town01:

```powershell
python .\scripts\change_map.py --town Town01
```

Ejecuta la prueba visible, normal, con seed 42:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --simulation-speed 1
```

Si la instalación de Python solo encuentra el módulo `carla`, pasa la carpeta
que contiene los agentes de navegación oficiales:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Opcionalmente, sin renderizado y con ritmo acelerado solicitado:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --no-rendering --simulation-speed 5
```
