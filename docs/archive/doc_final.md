# Iteración: viajes sucesivos con un vehículo en Town01

> Antecedente de una etapa anterior. Para la organización y ejecución actuales, consultar [README](../../README.md) y [la guía de carpetas](../repository-layout.md).

## Resultado

La primera iteración continúa disponible sin cambios en
`scripts/stable_traffic.py`: genera tráfico estable con Traffic Manager. La
nueva iteración usa exactamente un actor lógico `vehicle_001`, lo reutiliza en
varios viajes y se limita a Town01. El catálogo actual contiene 42 destinos y el
modo predeterminado elige mediante historial individual 80/20. No implementa
todavía múltiples vehículos, comparación final random-vs-stochastic, peatones,
ML ni optimización por congestión.

## Archivos creados

- `config/trips/single_vehicle_trip.json`: parámetros reproducibles de la prueba.
- `data/input/catalogs/Town01/destinations_config.csv`: 42 destinos normalizados sobre
  spawn points viales de Town01.
- `scripts/run_trip_simulation.py`: punto de entrada de la nueva corrida.
- `scripts/inspect_location.py`: obtiene la posición del spectator y el
  waypoint vial apto para registrar destinos manuales.
- `src/destinations.py`: lectura/validación de configuración y selección
  pseudoaleatoria reproducible 80/20.
- `src/route_planner.py`: integración de `GlobalRoutePlanner` y `BasicAgent`.
- `src/run_logger.py`: escritores CSV por corrida.
- `src/trip_runner.py`: ciclo del vehículo, llegada, espera, sensores,
  limpieza, métricas y restauración del mundo.
- `src/vehicle_history.py`: historial individual, generación dummy y selección
  80/20 sin pesos manuales.
- `config/trips/single_vehicle_trip_cyclic.json`: regresión de las tres rutas 6, 101
  y 133 que ya funcionaban.

## Archivos modificados

- `scripts/generate_dummy_data.py`: además de los CSV dummy heredados, genera
  `data/input/histories/Town01/bootstrap/vehicle_history_dummy.csv` sin sobrescribir el catálogo.
- `README.md`: documenta ejecución, rutas, no-rendering, velocidad y captura
  manual de lugares.

## Funcionamiento

La configuración contiene `routine_probability=0.8` y
`exploration_probability=0.2`. El historial dummy inicial es distinto por
`vehicle_id` y reproducible con la semilla. El 80 % elige entre los tres destinos
personales con mayor conteo y el 20 % entre los demás, priorizando los nunca
visitados. Solo una llegada `completed` agrega una visita y cambia decisiones
posteriores dentro de la corrida. El destino conceptual actual queda excluido.

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
`destination_name`, `map`, `category`, `enabled`, `reference_type`,
`spawn_point_index`, `x`, `y`, `z`, `road_id`, `lane_id` y `description`. No
contiene pesos ni frecuencia manual. Las tres categorías son `residential`,
`work_education` y `services_leisure`.

`vehicle_history_dummy.csv` contiene `vehicle_id`, `sequence`,
`destination_id` y `source`. Cada salida `vehicle_history.csv` añade `run_id`,
`trip_id` y `completed_sim_time_s` para distinguir la base dummy de las visitas
producidas por la simulación.

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
- `vehicle_history.csv`: copia del historial dummy más cada destino alcanzado
  durante la corrida.

Los estados posibles registrados son `completed`, `timeout`, `route_failed`,
`blocked` y `aborted`.

## Cambiar o agregar destinos reales

Ejecuta `inspect_location.py` con Town01 activo, posicionando primero el
spectator junto al lugar conceptual. El script muestra tanto la posición del
spectator como el waypoint de conducción más cercano, `road_id`, `lane_id`,
coordenadas, `s` y el spawn index próximo. Copia la fila propuesta, usando las
coordenadas del waypoint vial; no navegues hacia el interior de un edificio.

Puedes conservar `reference_type=spawn_point` y cambiar
`spawn_point_index`, o usar `reference_type=coordinates` con x/y/z y los IDs
viales inspeccionados. Cada fila requiere una de las tres categorías, pero no
requiere clase de frecuencia ni peso. Si cambia el catálogo, vuelve a generar el
historial dummy para evitar referencias a IDs eliminados.

## Selección actual y regresión cíclica

El vehículo aparece en el spawn 133, reconocido también como `T01_133`, por lo
que nunca se selecciona como primer destino. La configuración normal usa
`history_80_20`. Para repetir la secuencia verificada
`T01_006 → T01_101 → T01_133`, utiliza
`config/trips/single_vehicle_trip_cyclic.json`.

Para inspeccionar visualmente los spawn points, ejecuta:

```powershell
python .\scripts\inspect_location.py --town Town01 --show-spawn-points --highlight-spawn-point 133 --debug-lifetime-seconds 300
```

CARLA dibuja los índices y su orientación; el punto resaltado aparece en rojo.

## Limitaciones conocidas

- Los 42 destinos se proyectan al carril de Town01 antes de crear actores. La
  herramienta `validate_destinations.py` confirmó 41 rutas desde `T01_133` hacia
  los demás IDs. El ID 75 fue excluido porque CARLA devolvía una ruta degenerada
  de 0 m; los IDs 24 y 49 se excluyeron por ser puentes.
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
  `config/trips/single_vehicle_trip.json`; `initial_spawn_fallback_enabled=false`
  asegura que la corrida no cambie automáticamente a otra posición.
- Las dependencias de `GlobalRoutePlanner` y `BasicAgent` (`networkx` y
  `shapely`) se verifican antes de crear actores; se instalan con
  `python -m pip install -r .\requirements.txt`.
- Después de crear el vehículo se avanza un frame síncrono antes de calcular la
  primera ruta. La posición real se valida contra el spawn y el primer waypoint
  se valida contra el origen; una desalineación cancela el viaje antes de
  aplicar control. Esto corrige el giro hacia paredes causado por planificar
  temporalmente desde `(0,0,0)`.
- Los crash contexts locales registraron `DXGI_ERROR_INVALID_CALL` en D3D11 y
  `EXCEPTION_ACCESS_VIOLATION`; CARLA estaba usando `Intel UHD Graphics 770`.
  Para cambiar Town01/Town04 se recomienda reiniciar el servidor, y para corridas
  largas usar una GPU dedicada o `--no-rendering`.

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
