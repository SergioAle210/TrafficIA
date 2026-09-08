# Generador de tráfico urbano en CARLA

Base técnica para crear tráfico urbano controlado y reproducible en **CARLA
0.9.15**. Conserva la primera iteración de tráfico estable y añade una prueba
acotada de un vehículo reutilizado que ejecuta viajes sucesivos con selección de
destino, ruta explícita, sensores y registros por corrida.

## Requisitos

- Windows de 64 bits y CARLA 0.9.15 (`WindowsNoEditor`).
- Python 3.7.9 de 64 bits. Esta versión coincide con el wheel
  `carla-0.9.15-cp37-cp37m-win_amd64.whl` incluido en la distribución utilizada.
- `pip==24.0` dentro de un entorno virtual llamado `carla-env`.
- La Python API de CARLA instalada desde el wheel local incluido en
  `WindowsNoEditor/PythonAPI/carla/dist`.

Python 3.7 ya no recibe actualizaciones de seguridad. Se utiliza aquí únicamente
para reproducir el entorno de CARLA 0.9.15 y debe mantenerse aislado dentro del
entorno virtual.

Desde la raíz del repositorio, crea y activa el entorno:

```powershell
cd C:\CARLA\TrafficIA
python -m venv carla-env
.\carla-env\Scripts\Activate.ps1
```

Si PowerShell bloquea temporalmente la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\carla-env\Scripts\Activate.ps1
```

Instala las versiones reproducibles:

```powershell
python -m pip install --upgrade pip==24.0
python -m pip install -r .\requirements.txt
```

Instala `carla` desde el wheel que acompaña al servidor:

```powershell
cd C:\CARLA\WindowsNoEditor\PythonAPI\carla\dist
python -m pip install .\carla-0.9.15-cp37-cp37m-win_amd64.whl
cd C:\CARLA\TrafficIA
```

La carpeta `agents` no forma parte del wheel. Define su ubicación en cada nueva
sesión de PowerShell o utiliza el argumento `--carla-pythonapi` al ejecutar la
simulación de viajes:

```powershell
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
```

Verifica el entorno antes de iniciar CARLA:

```powershell
python --version
python -m pip --version
python -c "import carla; print(carla.__file__)"
python -m unittest discover -s tests -v
```

`carla-env` está excluido de Git. Debe recrearse en cada computadora y activarse
al abrir una terminal nueva. Usa `deactivate` para cerrarlo.

## Estructura principal

```text
config/       Configuraciones base de escenarios y Traffic Manager
data/input/   Configuración dummy reproducible
data/output/  Resultados de futuras corridas
scripts/      Puntos de entrada ejecutables
src/          Módulos compartidos para las siguientes fases
```

Los directorios heredados `configs/`, `data/raw/`, `data/processed/` y
`data/results/` no son usados por esta fase. La estructura activa sigue
`instrucciones.md`: `config/`, `data/input/` y `data/output/`.

## Iniciar CARLA

Abre PowerShell en el directorio de instalación de CARLA y ejecuta:

```powershell
cd C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low
```

Para una inspección visual corta puede reducirse la ventana:

```powershell
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```

Esta configuración no vuelve adecuada una GPU integrada para corridas largas.
Los registros locales muestran que CARLA está usando `Intel UHD Graphics 770` y
ha fallado dentro de D3D11. Si existe una GPU NVIDIA/AMD, configura
`CarlaUE4.exe` como aplicación de alto rendimiento en Windows.

Espera a que el simulador termine de cargar. Los scripts se conectan a
`localhost:2000` con un timeout de 30 segundos.

## Flujo recomendado en equipos con recursos limitados

El cambio de mapa y la creación del tráfico se ejecutan en pasos separados para
evitar encadenar ambas cargas. Después de iniciar CARLA, cambia el mapa desde la
raíz de este repositorio:

```powershell
python .\scripts\change_map.py --town Town01
```

Espera entre 10 y 15 segundos después de ver `Mapa cargado` para que el servidor se
estabilice. `change_map.py` no recarga el mapa si ya está activo.

Para cambiar de Town01 a Town04, detén primero cualquier cliente con `Ctrl+C`,
espera su limpieza, cierra CARLA y vuelve a iniciarlo. Evita cargar varios mapas
sucesivamente en el mismo proceso de Unreal cuando se usa calidad `Low`.

## Ejecutar tráfico estable

Prueba inicial recomendada:

```powershell
python .\scripts\stable_traffic.py --town Town01 --vehicles 10 --seconds 60 --no-rendering
```

El script usa el mundo que ya está activo: nunca carga ni recarga mapas. El
argumento opcional `--town` solo comprueba que el mapa actual sea el esperado y
termina con un mensaje claro si no coincide. Después activa el modo síncrono con
un delta fijo de `0.05` segundos, habilita no-rendering cuando se solicita,
sincroniza Traffic Manager y crea solo vehículos de cuatro ruedas con parámetros
conservadores. Los vehículos se crean progresivamente, avanzando un tick entre
cada actor para evitar una ráfaga de carga.

Las métricas mostradas son:

- cantidad de vehículos activos;
- velocidad promedio en km/h;
- cantidad de vehículos detenidos (velocidad menor que 1 km/h).

Al finalizar, incluso después de `Ctrl+C`, elimina los vehículos creados,
desactiva el modo síncrono de Traffic Manager y restaura la configuración original
del mundo. Para corridas sin renderizado:

```powershell
python .\scripts\stable_traffic.py --town Town01 --vehicles 30 --seconds 120 --no-rendering
```

El script elimina al inicio cualquier vehículo que ya exista en el mapa para que
la corrida comience desde un estado controlado. No elimina peatones ni otros tipos
de actores.

## Generar datos dummy

Ejecuta:

```powershell
python .\scripts\generate_dummy_data.py
```

El comando conserva los CSV genéricos anteriores y genera además un historial
inicial individual y reproducible para Town01:

```text
data/input/zones_config.csv
data/input/destinations_config.csv
data/input/demand_profiles.csv
data/input/Town01/vehicle_history_dummy.csv
```

El catálogo Town01 no contiene pesos ni etiquetas permanentes de frecuencia. El
historial dummy contiene visitas previas independientes; sus conteos son los
pesos derivados por el modelo. Para preparar cinco carros con 30 visitas cada
uno:

```powershell
python .\scripts\generate_dummy_data.py --seed 42 --vehicles 5 --history-length 30
```

La misma semilla genera los mismos historiales, pero cada `vehicle_id` recibe un
perfil distinto. Durante una corrida solo los viajes `completed` se agregan al
historial de salida; no se modifica el CSV de entrada.

Para continuar explícitamente desde el estado de una corrida anterior:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --history-in .\data\output\<run_id>\vehicle_history.csv --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Para continuar una corrida de tres carros, añade también
`--config .\config\multi_vehicle_trip.json`; el historial debe contener filas
para los tres `vehicle_id` configurados.

Sin `--history-in`, cada corrida vuelve al mismo dummy inicial, requisito útil
para comparar experimentos bajo condiciones equivalentes.

## Ejecutar viajes sucesivos en Town01

El catálogo contiene 42 destinos Town01 tomados de `rutas.md`. Cada destino
referencia un spawn point válido sobre la red vial. La configuración
predeterminada conserva la prueba compatible de un vehículo.

Con Town01 ya cargado, ejecuta:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --simulation-speed 1
```

La duración predeterminada es 600 s simulados y el timeout individual es 300 s.
Esto permite completar rutas largas de Town01 a 20 km/h; para una comprobación
corta puede usarse `--seconds 120`.

Si Python encuentra `carla` pero muestra `No module named 'agents'`, usa el
directorio de la distribución de CARLA que contiene la carpeta `agents`:

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Para ejecutar simultáneamente `vehicle_001`, `vehicle_002` y `vehicle_003` en
los spawn points 133, 6 y 101 respectivamente, usa:

```powershell
python .\scripts\run_trip_simulation.py --config .\config\multi_vehicle_trip.json --town Town01 --seed 42 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Los tres actores se crean antes del mismo frame de sincronización y cada uno
mantiene su propio historial, selección 80/20, `BasicAgent`, ruta, espera,
sensores y contador de viajes. El archivo dummy actual puede contener cinco
vehículos: esta configuración usa los tres primeros y deja `vehicle_004` y
`vehicle_005` disponibles para una ampliación posterior.

También puede definirse una vez por sesión de PowerShell:

```powershell
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
```

La configuración predeterminada usa `history_80_20`. Para cada viaje hace una
decisión reproducible: 80 % entre los tres IDs más visitados por el vehículo,
ponderados por sus conteos históricos, y 20 % entre los demás IDs, priorizando
los nunca visitados. No se selecciona la ubicación actual. Una llegada completada
se guarda en `vehicle_history.csv` y afecta la siguiente decisión de esa corrida.

Para comprobar únicamente las tres rutas ya validadas (6 → 101 → 133), conserva
el modo anterior con:

```powershell
python .\scripts\run_trip_simulation.py --config .\config\single_vehicle_trip_cyclic.json --town Town01 --seed 42 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Las rutas se crean antes de circular con `GlobalRoutePlanner.trace_route()` y
se entregan como pares `[Waypoint, RoadOption]` a
`BasicAgent.set_global_plan()`. Es una ruta corta según el costo de la red vial
de CARLA, no una ruta óptima respecto a tráfico, congestión o tiempo real.
Cada `BasicAgent` controla un vehículo y sigue su plan completo; por ello no se
activa Traffic Manager para estos actores. `stable_traffic.py` sigue utilizando
Traffic Manager sin cambios.

La llegada se detecta con `arrival_threshold_m`; al llegar, el actor frena,
espera `destination_dwell_time_seconds` de **tiempo simulado**, y recibe un
nuevo plan. `travel_time`, espera y duración se obtienen de
`WorldSnapshot.timestamp.elapsed_seconds`, nunca de reloj de pared.

### Sincronización segura antes de calcular la ruta

En modo síncrono, el runner crea todos los vehículos y avanza un único frame
antes de consultar sus posiciones físicas. Antes de iniciar los primeros viajes
comprueba que cada posición esté a no más de
`initial_spawn_validation_tolerance_m` del spawn esperado. También proyecta el
origen actual al carril de conducción y verifica que el primer waypoint de
`GlobalRoutePlanner` esté dentro de `route_origin_validation_tolerance_m`.

Una inicialización correcta muestra algo similar a:

```text
vehicle_001: spawn 133 sincronizado: x=..., y=..., z=...; error=0.02 m
vehicle_001/trip_001: T01_133 -> T01_... [routine]; ruta planificada ... m; inicio alineado 0.10 m
```

Si CARLA devuelve temporalmente `(0,0,0)` u otra posición desactualizada, la
corrida se cancela antes de aplicar acelerador o dirección. Esto evita que
`BasicAgent` intente alcanzar un primer waypoint calculado desde un origen que
no corresponde con la posición visible del vehículo.

### Velocidad de ejecución y no-rendering

`--simulation-speed` acepta 1 a 5. Mantiene `synchronous_mode=True` y el mismo
`fixed_delta_seconds`; solo limita el ritmo del reloj real a ese múltiplo cuando
el equipo puede alcanzarlo. Por tanto no cambia la física ni el significado de
las métricas. `--no-rendering` desactiva el renderizado y puede mejorar el
rendimiento, pero tampoco reemplaza el modo síncrono.

```powershell
python .\scripts\run_trip_simulation.py --town Town01 --seed 42 --no-rendering --simulation-speed 5
```

### Definir un destino manual

1. Carga Town01 y mueve el spectator cerca del lugar conceptual.
2. Ejecuta `python .\scripts\inspect_location.py --town Town01`.
3. Copia la plantilla que imprime el script a
   `data/input/Town01/destinations_config.csv`.
4. Usa las coordenadas del **waypoint vial accesible** (no las del edificio),
   junto con `road_id`, `lane_id` y el índice de spawn cercano mostrados.

### Visualizar los spawn points de CARLA

Con la ventana de CARLA visible, ejecuta:

```powershell
python .\scripts\inspect_location.py --town Town01 --show-spawn-points --highlight-spawn-point 133 --debug-lifetime-seconds 300
```

Verás cada índice y una flecha con su orientación. El 133 se muestra en rojo;
los dibujos permanecen 300 segundos simulados. Mueve el spectator por el mapa
para comparar el origen con otros puntos antes de poner el índice elegido en
`initial_spawn_point_index`.

Para validar sin crear actores que todos los destinos tengan ruta desde 133:

```powershell
python .\scripts\validate_destinations.py --town Town01 --origin-id T01_133 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

La validación actual obtiene 41 rutas válidas y ninguna fallida desde `T01_133`.
El ID 75 fue retirado porque CARLA devolvía para él una ruta degenerada de 0 m;
los IDs 24 y 49 permanecen fuera por representar puentes.

Cada corrida guarda `run_config.json`, `trips_log.csv`, `trajectory_log.csv`,
`events_log.csv`, `metrics_summary.csv` y `vehicle_history.csv` en
`data/output/<run_id>/`. Todos los registros incluyen `vehicle_id`; la pareja
`vehicle_id` + `trip_id` identifica un viaje. El historial de salida copia los
eventos iniciales de cada carro y agrega sus llegadas completadas. La
configuración de entrada nunca se modifica con resultados.

### Ajustar el origen inicial fijo

Edita [config/single_vehicle_trip.json](config/single_vehicle_trip.json) para un
carro o [config/multi_vehicle_trip.json](config/multi_vehicle_trip.json) para
varios. En la configuración múltiple, `vehicle_count` debe coincidir con la
cantidad de elementos únicos de `initial_spawn_point_indices`.
`initial_spawn_fallback_enabled: false` impide que un actor cambie de origen por
su cuenta: si algún punto está ocupado, la corrida completa falla con un mensaje
claro. Para elegir otro punto de carretera, ubica el spectator sobre el carril,
ejecuta `inspect_location.py` y copia el índice mostrado. El programa proyecta
cada punto al waypoint de conducción antes de crear el vehículo.

## Configuración base

Los archivos de `config/` documentan los parámetros previstos para escenarios
básico, de baja demanda y de alta demanda, además de los ajustes conservadores de
Traffic Manager. En esta fase `stable_traffic.py` expone sus valores operativos
por argumentos y constantes; la carga automática de escenarios se incorporará al
separar la lógica común hacia `src/`.

## Próximos pasos

Validar visualmente la corrida simultánea en 133, 6 y 101, implementar
posteriormente el escenario aleatorio equivalente y escalar gradualmente a 5,
10, 20 y 30 vehículos. Todavía no se calculan densidad o flujo para diagramas
fundamentales, ni se implementan comparación estadística final, visualizaciones
avanzadas o Google Maps API.

## Extra: errores de dependencias de rutas

- **`No module named 'agents'`**: la API `carla` está disponible, pero faltan
  los agentes oficiales. Añade
  `--carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla` al comando, o
  define `$env:CARLA_PYTHONAPI` con esa ruta.
- **`No module named 'networkx'`**: `GlobalRoutePlanner` necesita esta librería.
  Instala las dependencias con:

  ```powershell
  python -m pip install -r .\requirements.txt
  ```

  Luego vuelve a ejecutar la simulación con los mismos argumentos.
- **`No module named 'shapely'`**: `BasicAgent` necesita esta librería. Ejecuta
  el mismo comando de instalación anterior. El runner comprueba ahora todos los
  módulos de navegación antes de crear el vehículo o los sensores.
- **`No se pudo crear vehicle_XXX en el spawn point fijo`**: el punto elegido
  para ese actor está ocupado o no está disponible. Con
  `initial_spawn_fallback_enabled: false` el runner se detiene para conservar
  todos los orígenes fijos; cambia el índice correspondiente en
  `initial_spawn_point_indices` o activa el fallback si prefieres otra cosa.
- **Vehículo fuera de la carretera o dentro de una casa**: detén la corrida con
  `Ctrl+C`. El runner proyecta ahora cada spawn point al waypoint de conducción
  más cercano antes de crear el vehículo, para colocarlo sobre el carril.
- **Detener una corrida multivehículo**: usa `Ctrl+C`. El bloque de limpieza
  detiene y destruye los sensores de cada carro, destruye todos los vehículos y
  restaura la configuración anterior del mundo antes de terminar.
- **El vehículo nace bien pero gira de inmediato hacia una pared**: el problema
  observado era una ruta calculada antes de sincronizar el actor recién creado;
  el origen quedaba temporalmente en `(0,0,0)`. El runner ejecuta ahora un tick
  posterior al spawn, valida la posición real y rechaza cualquier ruta cuyo
  primer waypoint no esté alineado con el vehículo. Los valores de tolerancia
  están en `config/single_vehicle_trip.json` y
  `config/multi_vehicle_trip.json`.
- **Cambiar el origen fijo**: modifica `initial_spawn_point_index` en
  `config/single_vehicle_trip.json`. Usa `inspect_location.py` con el spectator
  situado sobre la carretera para conocer un índice cercano y válido.
- **Tres destinos consecutivos de regresión**: `T01_006`, `T01_101` y
  `T01_133` usan los spawn points 6, 101 y 133. Se ejecutan con
  `config/single_vehicle_trip_cyclic.json`; el modo normal usa historial 80/20.
- **CARLA se cierra con `DXGI_ERROR_INVALID_CALL`**: es un fallo del servidor
  Unreal/D3D11, no del planificador Python. En este equipo el crash context
  identifica `Intel UHD Graphics 770`, aunque CARLA recomienda una GPU dedicada
  con al menos 6 GB. Usa GPU de alto rendimiento si existe, evita recargar mapas
  repetidamente, reinicia CARLA entre Town01 y Town04 y usa `--no-rendering` en
  corridas largas.
- **Ventana que solo dice `Fatal error!`**: los registros locales muestran una
  `EXCEPTION_ACCESS_VIOLATION` posterior. Aplica el mismo procedimiento: detener
  clientes, reiniciar el servidor y no reutilizar la sesión para otro mapa.

```powershell
cd C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```
