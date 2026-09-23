# Generador de tráfico urbano en CARLA

Los objetivos académicos, criterios de evaluación y prioridades vigentes están
en [project-graduation-context.md](project-graduation-context.md). Consultarlo
antes de proponer cambios a la simulación o requisitos de aceptación.

Base técnica para crear tráfico urbano controlado y reproducible en **CARLA
0.9.15**. Conserva la primera iteración de tráfico estable y añade una prueba
de vehículos simultáneos reutilizados que ejecutan viajes sucesivos con selección
de destino, ruta explícita, sensores y registros por corrida.

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

En `history_80_20`, sin `--history-in` cada corrida vuelve al mismo dummy inicial.
`random_baseline` comienza sin historial de entrada, aunque el JSON tenga una
ruta de dummy configurada.

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

La llegada exige terminar la aproximación, estar dentro de `arrival_threshold_m`
**en el mismo `road_id`/`lane_id` que el destino, detenido (≤0.05 m/s), alineado
(≤10° respecto al carril) y centrado (error lateral ≤0.5 m)**. Pasar cerca por
el carril contrario o atravesar el radio en movimiento no completa el viaje.
El frenado forma parte del viaje; después de detenerse comienza
`destination_dwell_time_seconds` de **tiempo simulado**, y recibe un nuevo plan.
`travel_time`, espera y duración se obtienen de
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
`data/output/<run_id>/`. Viajes, trayectorias, eventos e historial incluyen
`vehicle_id`; la clave `run_id` + `vehicle_id` + `trip_id` identifica un viaje
entre corridas. Las métricas son agregadas por corrida. En `history_80_20`, el
historial de salida copia los eventos iniciales y agrega las llegadas; en
`random_baseline`, solo contiene llegadas de esa corrida. La configuración de
entrada nunca se modifica con resultados.

### Diagnosticar el seguimiento de curvas

El controlador conserva `CollinearSafeBasicAgent` y los PID oficiales. Tras
reproducir los contactos estáticos de Town01, se redujo únicamente
`controller_distance_ratio` de 0.5 a **0.1**. Este valor se entrega como
`distance_ratio` al `LocalPlanner`: el radio de descarte pasa de
`3 + 0.5 * velocidad_mps` a `3 + 0.1 * velocidad_mps`, aproximadamente de
5.78 a 3.56 m a 20 km/h. Así se conservan objetivos intermedios de curvas
estrechas. Durante la marcha normal se mantienen los 3 m de base y 20 km/h.
En la aproximación final se reduce la velocidad y el radio base de descarte
para detenerse centrado, como se describe abajo. Se conservan las ganancias
PID, el timestep y la selección de destinos.

Para registrar una prueba de tres vehículos con semilla 42:

```powershell
.\carla-env\Scripts\python.exe scripts/run_trip_simulation.py --config config/multi_vehicle_trip.json --scenario random_baseline --town Town01 --seed 42 --seconds 600 --simulation-speed 5 --no-rendering --navigation-diagnostics --controller-distance-ratio 0.1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Después de finalizar, repite el comando con `--scenario history_80_20`.
`--controller-distance-ratio 0.5` permite comparar el horizonte de marcha
anterior; ambos valores usan la política de llegada actual, por lo que ese
argumento por sí solo no reproduce todas las versiones históricas del runner.

`--navigation-diagnostics` añade `route_log.csv` (todos los waypoints del plan)
y `control_log.csv` (pose, velocidad, objetivo, dirección, acelerador, freno,
radio de descarte, distancia restante y velocidad objetivo por frame activo).
`arrival_log.csv` registra la pose, velocidad, carril y errores de cada llegada
completada, antes de iniciar la espera. El control
registrado en un frame se aplica para el siguiente tick; las colisiones se
asocian a la pose por `vehicle_id` y `frame`. El error lateral es positivo a la
derecha y se mide contra el segmento más cercano del plan completo, incluso
dentro de intersecciones; **no es una distancia física a la acera**. No se
muestrean controles durante las esperas ni después de cerrar el viaje.

Los diagnósticos están desactivados por defecto. No cambian los CSV anteriores
ni filtran callbacks. `run_config.json` registra las opciones del controlador,
la política de llegada y la versión/semántica de los diagnósticos. La evidencia
y las limitaciones de las pruebas están en la [bitácora](docs/bitacora_simulacion.md).

### Diagnosticar la llegada y la espera en T01_067

`scripts/diagnose_destination_dwell.py` ejecuta el runner actual y añade un
observador dentro de 25 m de T01_067. Conserva sus controles y transiciones;
permite examinar la llegada, el frenado, los cinco segundos de espera y el
arranque. El observador no modifica la conducción: usa la versión actual del
runner, incluida la corrección de llegada.

```powershell
.\carla-env\Scripts\python.exe scripts/diagnose_destination_dwell.py --config config/multi_vehicle_trip.json --scenario random_baseline --town Town01 --seed 42 --seconds 600 --simulation-speed 5 --no-rendering --controller-distance-ratio 0.1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Después de finalizar, repite con `--scenario history_80_20`. Acepta los mismos
argumentos del runner y activa los diagnósticos de navegación para esa corrida.
Además de los archivos habituales, guarda:

- `dwell_log.csv`: pose, velocidad, control ya aplicado, carril, orientación y
  huellas por frame, incluidas esperas. `phase_before`/`phase_after` identifican
  el cierre del viaje; `context_trip_id` conserva la referencia durante la espera.
- `dwell_geometry.json`: carriles y marcas muestreados cada 0.25 m, destino
  proyectado y dimensiones de los vehículos.
- `dwell_diagnostic_config.json`: significado de los campos y hashes del código
  usado. Las cuatro esquinas aproximadas del sensor se registran separadas
  de los ocho vértices de la caja física.

El control de `dwell_log.csv` es el observado al recibir el frame, antes de
emitir la siguiente orden; el de `control_log.csv` es la orden para el tick
siguiente. La captura se limita a esa zona: un vehículo sin filas puede
simplemente no haber pasado por ella. Estos logs no reemplazan los callbacks
ni cambian su atribución por viaje.

El diagnóstico del 2026-09-08 reprodujo las dos invasiones del histórico:
la esquina delantera izquierda sale hacia el carril contrario durante el
frenado posterior a la llegada y regresa al arrancar el siguiente viaje.
El runner cierra el viaje a 19.21 km/h en plena curva y frena con dirección
cero; el vehículo avanza 3.12 m antes de detenerse, con unos 33° de
desalineación. Esa fase añadió observación; la corrección posterior introduce
la aproximación descrita a continuación. No se crearon commits. Evidencia,
gráfico y resultados en la [bitácora](docs/bitacora_simulacion.md).

### Parar siguiendo el carril antes de iniciar la espera

`src/arrival.py` sigue el progreso ordenado sobre la ruta y limita la velocidad
con `min(velocidad_crucero, sqrt(2 * 1.5 * max(distancia_restante - 0.5, 0)))`
en m/s. A 20 km/h, la reducción empieza aproximadamente 10.8 m antes del
destino. Al alcanzar el margen final de 0.5 m, frena completamente conservando
la dirección calculada por el agente si está centrado y alineado. Si todavía
necesita orientarse, avanza con objetivo de 1 km/h mientras permanezca dentro
del radio y del carril del destino, y frena al cumplir ambos límites. Desde
`arrival_policy_version=3`, también reconoce cambios de IDs sobre la
continuación dirigida y única de ese carril, limitada a 3 m del destino.
Se conservan la parada, el centrado y la orientación requeridos. Los
obstáculos y semáforos pueden frenar
antes; la aproximación no anula esas decisiones.

El plan se completa hasta el waypoint real del destino, muestreando el tramo
final cada 0.5 m. Se añaden 6 m de continuación vial únicamente como guía
lateral para evitar que una cola vacía ponga la dirección a cero durante el
frenado. Esa continuación figura en `route_log.csv`, pero no se incluye en la
distancia planificada del viaje. Una continuación ambigua se rechaza como
`route_failed`, sin elegir un giro arbitrario.

Al bajar la velocidad, `CollinearSafeBasicAgent` reduce el radio base de descarte
desde 3 m hasta el mínimo de 1 m usado por el último waypoint del planner
oficial: `max(1, 3 * velocidad_objetivo / velocidad_crucero)`. El término
`distance_ratio=0.1`, las ganancias PID y el límite de cambio de dirección se
conservan. El radio base vuelve a 3 m al circular a velocidad de crucero.

`arrival_policy_version=3` identifica la semántica actual en `run_config.json`;
`arrival_control` registra sus límites. Los tiempos de viaje ahora incluyen el
frenado y la espera contiene cinco segundos completos después de la parada.
Por ello los tiempos y la cantidad de viajes en 600 s no son directamente
equivalentes a las corridas que cerraban el viaje a velocidad de marcha.

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

## Dos escenarios: aleatorio e historial 80/20

Ambos modos usan el mismo catálogo de Town01, los mismos tres vehículos, un
`GlobalRoutePlanner` compartido y un `BasicAgent` independiente por carro.
Solo cambia la elección del siguiente destino; el planificador y el controlador
vial permanecen iguales.

### `random_baseline`: elección uniforme por ID

En cada salida se toman los destinos habilitados del mapa, se excluye el destino
actual, se ordenan por ID y se elige uno con `random.Random.choice()` usando la
semilla individual del carro. Con los 42 destinos actuales, al salir de uno del
catálogo hay 41 candidatos: cada uno tiene probabilidad `1/41`, aproximadamente
2.44 %. Si el carro queda en una posición intermedia tras un viaje incompleto,
no tiene un destino actual identificado y pueden ser elegibles los 42.

No se sortea primero una categoría: una categoría con más IDs puede recibir más
viajes. El selector no consulta pesos, etiquetas de frecuencia ni historial.
Empieza con cero visitas y registra cada llegada completada para análisis. Ese
historial es pasivo: no influye en las elecciones siguientes.
Las decisiones son independientes, pero dos carros sí pueden elegir el mismo
destino; no se reservan destinos exclusivos por vehículo.

### `history_80_20`: preferencias derivadas de visitas individuales

Cada carro carga solo sus filas del dummy y recalcula sus tres destinos más
visitados antes de cada elección. Los empates de conteos se resuelven por ID.
Después excluye el destino actual de los candidatos, sin reemplazarlo por un
cuarto destino dentro del grupo rutinario.

- Con probabilidad 80 %, elige entre los recurrentes elegibles proporcionalmente
  a sus visitas. Conteos de 10, 6 y 4 implican 50 %, 30 % y 20 % dentro de esa
  rama si los tres son elegibles.
- Con probabilidad 20 %, explora uniformemente destinos nunca visitados. Cuando
  se agotan, elige entre los restantes fuera de su grupo recurrente.
- Si una rama queda sin candidatos, se utiliza la otra. Solo una llegada
  `completed` incrementa las visitas del carro correspondiente y puede cambiar
  su ranking futuro.

80/20 es una probabilidad por decisión, no una proporción exacta exigible a una
corrida corta. Los campos `selection_class` y `selection_candidate_count` del
log permiten revisar la rama realmente utilizada y su cantidad de candidatos.

### Ejecutar las dos pruebas de 600 segundos

Estas corridas reales pueden ejecutarse manualmente o por el agente cuando el
usuario lo autorice expresamente. No se programa monitoreo automático. Primero
ejecuta el baseline y espera a que termine; después ejecuta el histórico.
No deben correr simultáneamente contra el mismo servidor.

Requisitos: servidor CARLA 0.9.15 abierto, Town01 cargado, sin otros clientes que
generen tráfico, cambien el clima o avancen el mundo. Los spawn points 133, 6 y
101 deben estar libres. No vuelvas a generar el dummy actual: ya tiene cinco
vehículos con 30 visitas cada uno y el generador reemplaza ese CSV.

Desde PowerShell, sin necesidad de activar el entorno:

```powershell
cd C:\CARLA\TrafficIA
.\carla-env\Scripts\python.exe .\scripts\run_trip_simulation.py --config .\config\multi_vehicle_trip.json --scenario random_baseline --town Town01 --seed 42 --seconds 600 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Después de que aparezca `Corrida completada`, ejecuta:

```powershell
.\carla-env\Scripts\python.exe .\scripts\run_trip_simulation.py --config .\config\multi_vehicle_trip.json --scenario history_80_20 --town Town01 --seed 42 --seconds 600 --simulation-speed 1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Si Town01 aún no está cargado, antes de las corridas usa:

```powershell
.\carla-env\Scripts\python.exe .\scripts\change_map.py --town Town01
```

Conserva la misma sesión, clima e iluminación entre ambas pruebas y no cambies
de mapa. El runner no modifica el clima ni la posición del sol. Reinicia los
ciclos de semáforos antes del frame inicial y registra su estado, tiempos y si
están congelados, además del clima, posición solar y presencia de otros carros
o peatones. El reinicio utiliza la
[API oficial `World.reset_all_traffic_lights()` de CARLA 0.9.15](https://carla.readthedocs.io/en/0.9.15/python_api/#carla.World).
Si reinicias el servidor, verifica que las condiciones registradas coincidan;
el runner no restaura automáticamente el clima de una corrida anterior.

### Configuración y reproducibilidad

Para la campaña larga preparada en este espacio de trabajo, con CARLA y
Town01 ya disponibles:

```powershell
.\carla-env\Scripts\python.exe -u .\data\output\reliability_campaign_20260908\run_campaign.py --long
```

Ejecuta secuencialmente **seis corridas de 1.800 s**: semillas 42, 7 y 123,
cada una con `random_baseline` e `history_80_20`, y tres vehículos. A 5× son
aproximadamente 36 minutos reales más inicialización. Conserva el clima y el
historial dummy; cambiar la semilla también cambia los modelos elegidos por
el runner. Guarda las consolas, el manifiesto y la auditoría en
`data/output/reliability_campaign_20260908/long/`, además de los logs habituales
por corrida. Al finalizar comprueba llegadas, esperas, eventos e historiales
y muestra si hay incidencias. No sobrescribe una campaña ya existente.
**El usuario ejecutó esta campaña el 2026-09-09.** Las seis corridas terminaron;
su revisión encontró cero colisiones, pero fallos de planificación, un bloqueo
de llegada e invasiones con el Cybertruck. Véanse los resultados abajo y la
[bitácora](docs/bitacora_simulacion.md#2026-09-09--revisión-de-la-campaña-larga-ejecutada-por-el-usuario).

Los dos comandos usan `config/multi_vehicle_trip.json`. `--scenario` sobrescribe
`destination_selection_mode` antes de validar la configuración efectiva; sin
ese argumento se conserva el modo del JSON (`history_80_20` actualmente).
Los modos anteriores `cyclic` y `stochastic` siguen disponibles mediante JSON.

| Parámetro | Valor de estas pruebas |
|---|---|
| `vehicle_count`, `initial_spawn_point_indices` | `3`, `[133, 6, 101]` |
| `initial_spawn_point_index`, `initial_spawn_fallback_enabled` | `133`, `false`; el escalar coincide con el primer índice |
| `seed`, `target_speed_kmh` | `42`, `20` |
| `duration_seconds`, `fixed_delta_seconds` | `600`, `0.05` s simulados |
| `arrival_threshold_m`, `destination_dwell_time_seconds` | `4` m, `5` s |
| `max_trip_time_seconds` | `null`: sin límite independiente; corte al terminar la corrida |
| `blocked_speed_threshold_mps`, `blocked_time_threshold_seconds` | `0.2` m/s durante `60` s |
| `trajectory_sampling_interval_seconds` | `0.5` s |
| `routine_destination_count`, `routine_probability`, `exploration_probability` | `3`, `0.8`, `0.2`; no intervienen en baseline |

`--seed`, `--seconds`, `--town` y `--no-rendering` permiten sobrescribir sus
valores correspondientes. `--simulation-speed` controla el objetivo de ritmo
real, no la física: 600 segundos son tiempo simulado y pueden tardar más en un
equipo lento. Si usas `--no-rendering`, úsalo en ambas corridas.

`--max-trip-seconds 300` reproduce el límite anterior por viaje y
`--max-trip-seconds 0` lo desactiva. La configuración multivehículo usa ahora
`null`; el detector de velocidad baja durante 60 s se mantiene. Esto permite
viajes de más de 300 s sin convertirlos en llegadas: si siguen activos al corte
global se registran como `aborted`. Las esperas permanecen en el tiempo de viaje.

Para el carro de índice `i` (empezando en cero), la semilla de destinos es
`seed + i * 1000003`; la de modelo/color vehicular suma uno más. Los sorteos
vehiculares no consumen los sorteos de destinos. Mismo catálogo, semilla e
historial y misma secuencia de llegadas producen las mismas decisiones; esto
no garantiza trayectorias físicas idénticas si cambian el servidor o los eventos.
Los modelos y atributos realmente creados también quedan en `run_config.json`.

`history_80_20` carga 30 visitas de cada uno de los primeros tres carros; los
historiales de `vehicle_004` y `vehicle_005` quedan disponibles para después.
Cada corrida vuelve al dummy; no reutiliza resultados anteriores automáticamente.
`--history-in <ruta>` permite continuar explícitamente un historial en modo
histórico, pero no debe usarse en esta primera comparación. El baseline funciona
sin archivo dummy y rechaza cualquier `--history-in` explícito.

### Resultados y estados de viaje

Las carpetas nuevas incluyen mapa, escenario, semilla y fecha UTC, por ejemplo:

```text
data/output/town01_random_baseline_seed_42_<fechaUTC>/
data/output/town01_history_80_20_seed_42_<fechaUTC>/
```

- `run_config.json`: escenario efectivo, parámetros, destinos, condiciones del
  mundo y datos iniciales por carro. En baseline, `history_input` es `null` y
  los conteos iniciales están vacíos, aunque el JSON original configure un dummy.
- `trips_log.csv`: origen, destino, rama de elección, tiempo, distancia,
  velocidad, incidentes y estado. Baseline registra
  `selection_class=random_baseline`; el histórico, `routine` o `exploration`.
  `history_visit_count_before` es telemetría de visitas previas, no un peso de
  selección en baseline.
- `trajectory_log.csv`: muestras de posición, velocidad y carril por vehículo y
  viaje, con tiempo simulado. El frame inicial no se reinicia a cero entre corridas.
- `events_log.csv`: colisiones e invasiones de carril separadas; una invasión no
  equivale automáticamente a un accidente.
- `vehicle_history.csv`: en baseline comienza vacío y añade solo llegadas; en
  histórico comienza con 90 visitas (30 por carro) y añade las nuevas con
  `source=simulation`. La secuencia pertenece a cada `vehicle_id`.
- `metrics_summary.csv`: una fila agregada con `vehicle_count=3`, viajes,
  distancia, velocidad, incidentes y distribución de destinos completados.
  Desde `metrics_semantics_version=2`, los totales de eventos incluyen las
  esperas, por lo que pueden superar la suma de los eventos por viaje.
  `total_collisions` cuenta callbacks, no accidentes independientes.
  La versión 3 añade `total_observed_distance_m` y `total_vehicle_time_s`,
  medidos cada tick para toda la presencia de los vehículos, incluidas esperas.
  Los campos previos de distancia y velocidad conservan su ámbito de viajes
  activos para no cambiar retroactivamente su significado.

Los viajes nuevos incluyen `end_sim_time_s`, `termination_reason`,
`max_trip_time_seconds` y `stopped_time_s`. Este último integra los intervalos
de tick cuya velocidad final es menor de 0.2 m/s; no identifica por sí solo
el motivo de parada. `blocked` sigue significando velocidad baja sostenida,
no una clasificación automática de la causa física.

| Estado | Significado |
|---|---|
| `completed` | Llegó dentro del umbral y al carril del destino; se añade una visita al historial. |
| `aborted` | Seguía viajando cuando terminó la duración de la corrida. No es por sí solo un error de ruta. |
| `blocked` | Permaneció por debajo del umbral de velocidad demasiado tiempo; puede incluir una espera prolongada en semáforo. |
| `timeout` | Superó el tiempo máximo por viaje sin llegar. |
| `route_failed` | No pudo obtener o validar el plan antes de circular. |

Con `Ctrl+C` se ejecuta la limpieza de sensores, vehículos y ajustes del mundo.
Una interrupción deja resultados parciales: actualmente no garantiza cerrar
los viajes activos ni escribir `metrics_summary.csv`. Si CARLA se cierra o pierde
la conexión, tampoco se puede garantizar la destrucción remota de actores; hay
que reiniciar el servidor. Para comparar 600 segundos, deja finalizar cada comando.

### Verificación realizada y pendiente

La corrección de retorno dentro del mismo tramo mantiene el trazado y las
decisiones de giro de CARLA, pero añade un circuito dirigido cuando el destino
queda detrás del origen. Conserva la validación de extremos. Para comprobar
todos los pares del catálogo sin crear vehículos:

```powershell
.\carla-env\Scripts\python.exe scripts/validate_route_catalog.py --report data/output/catalog_check_nuevo.json
```

### Análisis de las cuatro métricas académicas

`scripts/analyze_mobility.py` procesa corridas preservadas sin conectar con
CARLA ni modificar los logs. Por ejemplo, para la campaña diagnóstica anterior:

```powershell
.\carla-env\Scripts\python.exe scripts/analyze_mobility.py --campaign data/output/reliability_campaign_20260908/long/campaign.json --output data/output/analisis_largo_nuevo
```

También acepta directorios de corrida como argumentos. El directorio de salida
debe ser nuevo. Genera `analysis.json`, `summary.csv`, `destinations.csv` y
`report.md`, con comprobaciones de integridad y comparabilidad por escenario.

- Destinos: distribuciones de asignados y alcanzados, por ID y categoría.
- Tiempo: media, mediana y dispersión de completados, incluidas sus detenciones;
  todos los incompletos conservan estado y duración parcial por separado.
- Velocidad: suma de distancias / suma de tiempos de presencia vehicular en
  registros versión 3; incluye las esperas y no es media de velocidades individuales.
- Eventos: callbacks de invasión y colisión separados, con conteos y tasas por
  vehículo-km y vehículo-hora. Las invasiones no hacen fallar la auditoría.

Para registros versión 2, la exposición disponible abarca viajes activos:
la velocidad usa ese ámbito y las tasas incluyen solo eventos asignados a un
viaje. Se conservan aparte todos los eventos observados, incluidos los de
espera, y se advierte esa limitación. No mezclar las velocidades de ambos
ámbitos sin recalcular una definición común. Las tasas con exposición cero
son no definidas; no se sustituyen por cero.

Las comparaciones son descriptivas. El programa comprueba condiciones
registradas y denuncia pares ausentes, ambiguos o incompatibles; no establece
causalidad, significancia estadística ni cumplimiento integral del ODD.

### Antecedentes de validación

Las 97 pruebas automatizadas pasan con `carla-env` y agents disponible: incluyen selector uniforme,
exclusión, reproducibilidad, independencia de pesos/historial, validación CLI,
aislamiento por carro y actualización solo por llegadas. Las pruebas con un
doble de CARLA también cubren ambos modos, CSV reales en directorios temporales,
un tick por frame y limpieza ante `Ctrl+C`, spawn fallido o fallo de sensor.
No son una validación de circulación ni física real.

```powershell
.\carla-env\Scripts\python.exe -c "import carla; print('CARLA SDK disponible')"
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
.\carla-env\Scripts\python.exe -m unittest discover -s tests -v
```

Como antecedente, la fase multivehículo pasó 21 pruebas y una corrida CARLA real
de 180 segundos: los tres carros completaron un viaje y empezaron otro; hubo
cero colisiones y tres eventos de invasión de carril. Esa evidencia corresponde
al modo histórico previo, no valida el nuevo baseline durante 600 segundos.

El 2026-09-08 el usuario autorizó al agente a ejecutar ambas corridas de 600
segundos. Terminaron sin crash, con 11 viajes completados por escenario, pero
mostraron contactos repetidos entre carros en baseline y cuatro eventos durante
esperas omitidos del resumen histórico. La evidencia, correcciones y revalidación
están en la [bitácora de simulación](docs/bitacora_simulacion.md).
Después del ajuste, ambas repeticiones completaron 11 viajes sin contactos entre
los carros. El baseline pasó de 857 a 7 callbacks de colisión; el histórico tuvo
2. Esos contactos estáticos motivaron la investigación de curvas descrita abajo.
El resumen histórico ya coincide con sus 27 invasiones registradas,
incluidas las cuatro durante las esperas.

La investigación posterior confirmó un recorte de curvas por el descarte
anticipado de waypoints y corrigió además una llegada prematura desde el
carril contrario. Con `distance_ratio=0.1`, las corridas finales de 600 s,
tres vehículos y semilla 42 produjeron:

| Validación previa de curvas | random_baseline | history_80_20 |
|---|---:|---:|
| Viajes iniciados / completados / aborted | 14 / 11 / 3 | 14 / 11 / 3 |
| Callbacks de colisión | 0 | 0 |
| Invasiones de carril | 0 | 2 |

Las referencias con 0.5 y la misma regla de llegada habían registrado seis
colisiones en baseline y una en histórico. Los pasos por ambas curvas se
conservaron. La desviación interior máxima del baseline bajó de 1.90 a 0.86 m
cerca de `(96, 202)` y de 1.61 a 0.72 m cerca de `(98, 325)`. Las dos invasiones
restantes del histórico son de marca `Broken`, cerca de `(2, 321)` y `(1, 318)`;
una ocurrió durante la espera y ambas entran en el resumen. Las 70 pruebas
incluyen regresiones del seguimiento y la llegada, además de los diagnósticos.

Resultados de esa validación previa:

- `data/output/town01_random_baseline_seed_42_20260908T182618700799Z/`
- `data/output/town01_history_80_20_seed_42_20260908T182846213527Z/`

La limpieza final dejó cero vehículos y sensores, modo asíncrono y no-rendering.
Esto valida la corrección en esas condiciones; no demuestra ausencia de
contactos con otros modelos, semillas o cargas.
No se inicia monitoreo automático. En aquella validación quedaron pendientes
la comparación estadística formal, las gráficas de densidad/flujo y más
vehículos. Los avances posteriores se registran abajo; las primeras
[gráficas exploratorias](docs/graficas_campana_veinte.md) ya están disponibles.

La corrección posterior de llegada y espera (2026-09-08), con tres vehículos,
semilla 42 y 600 s por escenario, obtuvo:

| Validación actual | random_baseline | history_80_20 |
|---|---:|---:|
| Iniciados / completados / aborted al terminar 600 s | 14 / 11 / 3 | 14 / 11 / 3 |
| Colisiones / invasiones | 0 / 0 | 0 / 0 |
| blocked / timeout / route_failed | 0 / 0 / 0 | 0 / 0 / 0 |
| Distancia total (m) | 5784.41 | 5665.75 |
| Máxima velocidad registrada al completar (m/s) | 0.000925 | 0.008274 |

Todas las llegadas cumplen parada, radio, carril, orientación y centrado. En
T01_067, el vehículo 002 termina a 0.003 km/h, con error lateral de 0.087 m
y error de rumbo de 9.97°. Cumple los cinco segundos de espera con movimiento
residual menor de 0.2 mm y arranca sin invasiones. La caja física permanece
entre -1.43 y +1.60 m respecto al centro en los 15 s anteriores y 10 posteriores
a la llegada; ambos bordes están a ±2 m en esa zona.

Resultados actuales:

- `data/output/town01_random_baseline_seed_42_20260908T214348287830Z/`
- `data/output/town01_history_80_20_seed_42_20260908T214121761147Z/`
- [Comparación visual antes/después](data/output/arrival_correction_20260908/arrival_comparison.png).

Se comprobaron los mismos modelos, clima, semáforos y secuencias de destinos
que en el diagnóstico anterior; no se filtraron eventos. Las 80 pruebas
incluyen llegada en curva/recta, cola final, frenado con dirección, alineación
lenta limitada al destino y registro único de la visita. Los dos intentos
intermedios con bloqueo se conservaron y están descritos en la bitácora.
La limpieza dejó CARLA disponible, sin vehículos ni sensores, en modo
asíncrono y con renderizado restaurado. No se hicieron commits.

La repetición posterior de **600 s con semilla 42** conservó, en ambos
escenarios, 11 viajes completados, cero colisiones e invasiones y ausencia de
`blocked`, `timeout` y `route_failed`. Las 22 llegadas y sus visitas al historial
pasaron la auditoría; también coincidieron clima, modelos y secuencia de
destinos. Las 80 pruebas unitarias volvieron a pasar.

Las trayectorias presentan variación entre ejecuciones: la mayor diferencia
de tiempo por viaje fue 0.50 s en baseline y 0.15 s en histórico. Comparando
posiciones al mismo frame relativo, las diferencias máximas fueron 3.12 m y
1.41 m respectivamente. Estas cifras describen diferencias entre corridas,
no desplazamientos respecto al carril. La coincidencia de resultados de
seguridad y selección no constituye determinismo exacto de la física.

Repeticiones:

- `data/output/town01_random_baseline_seed_42_20260908T220730234302Z/`
- `data/output/town01_history_80_20_seed_42_20260908T220937759845Z/`
- Auditoría: `data/output/reliability_campaign_20260908/audit.json`.

El **2026-09-09** se revisaron las seis corridas de **1.800 s** ejecutadas por
el usuario, siempre con tres vehículos. El código y los datos coinciden con
los hashes del manifiesto; clima y semáforos coinciden en las seis corridas,
y cada par con la misma semilla conserva modelos, atributos y spawns.

| Escenario | Semilla | completed | timeout | route_failed | blocked | aborted | Colisiones | Invasiones |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random_baseline | 42 | 34 | 1 | 1 | 0 | 2 | 0 | 0 |
| history_80_20 | 42 | 31 | 1 | 1 | 0 | 3 | 0 | 0 |
| random_baseline | 7 | 25 | 2 | 1 | 0 | 3 | 0 | 0 |
| history_80_20 | 7 | 31 | 1 | 2 | 0 | 3 | 0 | 0 |
| random_baseline | 123 | 26 | 3 | 2 | 1 | 3 | 0 | 8 |
| history_80_20 | 123 | 27 | 2 | 2 | 0 | 3 | 0 | 2 |

Las **174 llegadas** cumplen los criterios actuales; viajes, eventos e
historiales cuadran y los 17 `aborted` coinciden con el fin de los 1.800 s.
Las 80 pruebas automatizadas pasan. `exit=0` indica que el proceso terminó;
la campaña **todavía no valida estabilidad de comportamiento**:

- Los nueve `route_failed` se reprodujeron sin circular: origen y destino
  pertenecen al mismo tramo dirigido, con destino detrás del origen. El
  `GlobalRoutePlanner` devuelve un solo waypoint cerca del origen y la
  validación rechaza el plan. Existe un circuito dirigido en el grafo. El
  barrido de los 1.722 pares del catálogo encontró 60 fallos de este patrón.
- Los diez `timeout` agotan el límite fijo de 300 s por viaje tras acumular
  82.70–167.25 s casi detenidos, mayormente cerca de semáforos; ninguna parada
  continua supera 32.35 s. Hace falta revisar el presupuesto de viaje y
  registrar la causa de espera, sin equiparar estos casos a un atasco permanente.
- El único `blocked`, Cybertruck en T01_067, revela una limitación de la llegada:
  al pasar de `road/lane=20/-1` a su continuación `15/+1`, la igualdad de IDs
  desactiva la alineación lenta. Frena a 0.91 m del destino, todavía con 12.48°
  de error de rumbo, y termina bloqueado. Debe reconocer la continuidad
  dirigida y acotada del carril conservando los criterios de parada/alineación.
- Las diez invasiones son del Cybertruck con semilla 123: ocho `NONE` en cuatro
  pasos cerca de `(8, 2)`, con la huella reconstruida ligeramente fuera del
  borde exterior; dos `Broken` durante la llegada a T01_067, con caja física
  hasta 0.175 m dentro del carril contrario. No son colisiones ni cambios de
  carril planificados. Queda validar el seguimiento en curva para este modelo.

Ambas zonas originales, `(96, 202)` y `(98, 325)`, fueron recorridas en las seis
corridas sin nuevos contactos. La revisión conservó los logs originales y no
cambió la conducción ni hizo commits. CARLA quedó disponible en Town01, sin
vehículos/sensores, asíncrono y con renderizado.

Evidencia: `data/output/reliability_campaign_20260908/long/audit.json` y
`long/review/` dentro de esa campaña (auditoría recalculada, diagnóstico de
rutas/controles/geometría y pruebas). [Huella del Cybertruck en ambas curvas](data/output/reliability_campaign_20260908/long/review/invasion_geometry.png).

Para conservar contexto entre sesiones, registrar cada ajuste de simulación en
esa bitácora: fecha, causa o hipótesis, archivos, pruebas, carpetas de resultados
y limitaciones. Mantener los logs originales y documentar cambios de significado
de las métricas antes de comparar corridas antiguas y nuevas.

## Configuración base

Los archivos de `config/` documentan los parámetros previstos para escenarios
básico, de baja demanda y de alta demanda, además de los ajustes conservadores de
Traffic Manager. En esta fase `stable_traffic.py` expone sus valores operativos
por argumentos y constantes; la carga automática de escenarios se incorporará al
separar la lógica común hacia `src/`.

## Revisión instrumentada de tres vehículos

`scripts/review_trip_simulation.py` conserva la conducción del runner y
registra fases, posición y velocidad por tick. Durante las paradas añade
semáforo y proximidad de otros vehículos; ese contexto no clasifica por sí
solo una parada como congestión. Para ejecutarlo **sin cámaras RGB**:

```powershell
.\carla-env\Scripts\python.exe -u scripts/review_trip_simulation.py `
  --no-cameras --config config/multi_vehicle_trip.json `
  --scenario random_baseline --seed 42 --seconds 600 --simulation-speed 1 `
  --navigation-diagnostics `
  --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Cambiar a `--scenario history_80_20` ejecuta el otro tratamiento. CARLA debe
estar en Town01; el script valida el mapa y es el único cliente que avanza
los ticks. Cada ejecución crea una carpeta nueva y conserva hashes de
código/entradas, `observation_log.csv` y `capture_summary.json`.

Sin `--no-cameras`, añade tres cámaras cenitales de 640 × 360, altura 18 m
y captura cada 0.5 s, con imágenes e índice por vehículo/frame. Este modo
falló dos veces por pérdida del dispositivo D3D en la Intel UHD 770,
incluso usando RenderOffScreen. El estudiante autorizó continuar sin cámaras;
los intentos incompletos se conservaron y no cuentan como corridas válidas.
La evidencia visual completa queda pendiente. Véase el
[informe de revisión](docs/revision_visual_tres_vehiculos.md).

La revisión del **2026-09-15** completó ambos escenarios sin cámaras:
600 s cada uno, tres vehículos, semilla 42 y ritmo 1×. Cada escenario registró
11 llegadas y tres `aborted` por fin de simulación; cero `blocked`, fallos de
ruta, colisiones, invasiones o errores de integridad. Se auditaron 22 ciclos
de llegada/espera/reinicio y 72,000 observaciones. Pasaron **107 pruebas**.
Se puede preparar el piloto de cinco vehículos sobre esta evidencia de logs;
la validación visual y los niveles definitivos de demanda siguen pendientes.

## Próximos pasos

La [revisión del controlador y los incidentes](docs/control_e_incidentes.md)
explica qué cambios redujeron contactos e invasiones, su evidencia y sus
límites para comparar selectores. Las tasas corresponden al controlador
común corregido; no se exige cero eventos ni se atribuye su reducción al 80/20.

Los [pilotos de cinco, diez y veinte](docs/pilotos_escalamiento.md) completaron
ambos escenarios sin cámaras, semilla 42 y 600 s a 1×. El 17 de septiembre se
ejecutaron diez (28/33 llegadas baseline/histórico) y veinte (55/63 llegadas).
Las cuatro corridas nuevas tienen cero errores de integridad, bloqueos,
fallos de ruta, timeout y colisiones. Con veinte hubo dos invasiones por
escenario, todas del Cybertruck y conservadas como métrica. Se auditaron
179 llegadas, 175 ciclos completos y 720,000 observaciones; los cuatro ciclos
restantes quedaron en espera al corte. Las 235 elecciones se reprodujeron
sin diferencias. Pasaron 111 pruebas y las fuentes permanecieron intactas.

Configuraciones e historiales: `config/pilots/` y `data/input/Town01/pilots/`.
[Comparación de las seis corridas](data/output/scaling_pilots_20260917/metrics/report.md).
CARLA quedó en Town01 sin vehículos/sensores, asíncrono y con renderizado.
Sigue registrar repeticiones/semillas y validar mayor duración antes de fijar
las dos demandas; veinte no demuestra por sí solo saturación. No se modificó
el controlador ni se hicieron commits en esta etapa.

Actualización del 17 de septiembre: se completó y auditó una
[campaña larga con veinte vehículos](docs/campana_larga_veinte_vehiculos.md),
semillas 210/109, ambos selectores, 1,800 s y ritmo solicitado 5×, sin cámaras
ni cambios de conducción. Ritmo alcanzado: 1.730–1.832×. Hubo 783 llegadas,
78 viajes cortados, 781 ciclos completos y 861 decisiones reproducidas sin
diferencias, con 2,880,000 observaciones y cero errores de integridad.
Baseline 210/109 registró 14/510 callbacks de colisión, concentrados en dos
episodios entre vehículos; histórico registró cero. No hubo invasiones,
bloqueos, fallos de ruta ni timeout. Los historiales crecieron a 796/791
visitas. El intento inicial a 1× se conserva como parcial excluido, tras
la petición de acelerar las cuatro corridas. CARLA quedó limpio en Town01.
Sigue definir la unidad de incidente y una matriz comparable de repeticiones
y flotas antes de fijar las demandas; estas dos semillas son una ampliación
exploratoria y no prueban por sí solas repetibilidad física exacta.

**Gráficas del 17 de septiembre:** [guía e interpretación](docs/graficas_campana_veinte.md),
[PDF de nueve láminas](data/output/visual_analysis20_20260917/graficas_campana.pdf)
y [galería local](data/output/visual_analysis20_20260917/index.html).
Cubren destinos, tiempos completos/cortados, velocidad de presencia,
colisiones/invasiones, crecimiento del historial y relaciones locales
velocidad–densidad, flujo–densidad y velocidad–flujo. Estas últimas usan
38 tramos de 50 m y ventanas de 60 s: 2,458 celdas con presencia, sin ajuste
de curva ni estimación de capacidad. Las cuatro corridas tienen veinte
vehículos y todavía no comparan dos demandas. Los scripts
`scripts/build_campaign_plot_data.py` y `scripts/plot_mobility_campaign.py`
trabajan offline con `carla-env`; no requieren servidor ni cambian conducción.
Pasaron 118 pruebas, incluidas siete de agregación espacio-temporal.

**Gráficas de 3600 segundos (22 de septiembre):** la nueva
[galería y análisis](docs/graficas_demandas_3600.md) conserva los resultados
anteriores y presenta doce láminas, incluidas las guías de tráfico y una
comparación de ambas medias horas. Con veinte hubo 422/397 llegadas, sin
blocked ni rutas rechazadas; con cien, 252/252 llegadas y 3932/4147 blocked.
Se verificaron 52 archivos y se procesaron 17.28 millones de observaciones.
132 pruebas pasaron. Análisis offline, sin cambios de conducción ni commits.

**Líneas guía para leer los diagramas (20 de septiembre):** la
[explicación y galería revisada](docs/lectura_diagramas_y_guias.md) añade
resúmenes por bandas de densidad a los mismos puntos observados. Cada
marcador conserva q=k·v; se interrumpe la guía donde hay pocas celdas. No se
ajusta una parábola ni se estima capacidad. Se aclara la diferencia entre
probabilidad 80/20, nubes observadas y modelos teóricos. Pasaron 130 pruebas;
sin nuevas simulaciones. Las figuras del día 19 se conservan.

**Gráficas de 20 y 100 vehículos (19 de septiembre):** se analizó la campaña
completa del día 18, semilla 210, ambos selectores y 1,800 s por caso. La
[guía de resultados](docs/graficas_demandas_20_100.md) enlaza once láminas
PNG/SVG, PDF, galería y datos derivados. Se verificaron 52 archivos y se
procesaron 8.64 millones de observaciones offline. Con veinte hubo 215/196
llegadas y 10.38/10.71 km/h; con cien, 173/183 y 2.47/2.55 km/h. Cien acumuló
3,460 `blocked` y 417 `route_failed` entre ambos selectores, separados de los
cortes por fin de simulación. Las nubes de tráfico cubren mayores densidades,
pero los contactos y bloqueos impiden presentarlas como una capacidad vial
calibrada. Primero corresponde investigar esas secuencias; no se exige cero
invasiones. Pasaron 126 pruebas; no se ejecutó CARLA para generar las figuras.

**Fundamento de las demandas:** la [investigación del 17 de septiembre](docs/fundamento_demandas_town01.md)
verifica el antecedente NoCrash (20/100 en Town01; 15/70 en Town02) y distingue
capacidad vial, carga computacional y población simultánea. El 18 de septiembre
el estudiante eligió probar directamente **20 y 100**, semilla **210**, ambos
selectores y **1,800 s por corrida a 5× solicitado**. Las dos cantidades siguen
siendo candidatas; cien no implica saturación por definición. La
[campaña preparada y sus comprobaciones](docs/campana_demanda_20_100.md)
conserva historiales completos y registra cada frame sin cámaras RGB.

Con una sola instancia de CARLA 0.9.15 en Town01, desde la raíz del repositorio:

```powershell
.\carla-env\Scripts\python.exe -u scripts/run_demand_campaign.py --seed 210 --seconds 1800 --simulation-speed 5
```

Ejecuta secuencialmente 20/baseline, 20/histórico, 100/baseline y 100/histórico;
crea una carpeta nueva de campaña, comprueba limpieza entre casos y genera
auditorías y métricas. `--check-only` comprueba las entradas y el servidor sin
crear actores. La velocidad real depende de la carga; 5× no es una garantía.

La campaña larga previa con tres vehículos ya está ejecutada y revisada. Según la aclaración posterior
del estudiante y el objetivo específico 3, **no se exige cero invasiones de
carril**: se conservan como métrica de comparación. La recomendación previa
de eliminar las invasiones del Cybertruck como requisito para avanzar queda
actualizada por [el contexto académico](project-graduation-context.md).

Los puntos 1–3 ya tienen implementación y validación focalizada: rutas de
retorno, continuidad de llegada, límite temporal opcional y análisis de las
cuatro métricas. Pasaron 97 pruebas, 1.722 pares del catálogo y los nueve casos
de ruta fallidos anteriores. Cuatro corridas reales con tres vehículos
(600 s por escenario con semilla 42; 900 s con semilla 123) completaron 48
viajes, sin `route_failed`, `blocked`, `timeout` ni colisiones. Se conservaron
nueve invasiones del Cybertruck en baseline/123. Los doce `aborted` son viajes
activos al terminar. Esto valida los casos investigados, no toda la matriz final.

Resultados y comparación descriptiva:
[informe](data/output/mobility_fixes_20260909/metrics/report.md),
[distribuciones](data/output/mobility_fixes_20260909/metrics/destinations.csv)
y [bitácora](docs/bitacora_simulacion.md#2026-09-09--correcciones-de-movilidad-y-análisis-de-métricas).
La comprobación sobre el mapa también validó el carril de las 48 llegadas.
CARLA quedó sin actores vehiculares ni sensores, asíncrono y con renderizado.

El estudiante completó una **ejecución manual de baseline/42 el 2026-09-14**:
tres vehículos, 600 s, renderizado y ritmo 1×. La auditoría offline del día 15
confirmó 11 llegadas, tres viajes activos al corte y cero errores de integridad,
colisiones, invasiones, fallos de ruta o bloqueos. Tiempo medio de completados:
137.209 s; velocidad de presencia completa: 11.565 km/h. Solo comprobó que
terminara: siguen pendientes la observación detallada y el histórico manual.
Revisar salidas, curvas, paradas, llegadas y reinicios; conservar los logs y
anotar vehículo/momento ante dudas. Las invasiones siguen siendo una métrica,
no un requisito de cero eventos.

La [revisión y propuesta de demanda](docs/seleccion_niveles_demanda.md) documenta
los resultados, su comparación con el día 9 y el respaldo metodológico.
Se proponen pilotos de **5 → 10 → 20 vehículos** y candidatos iniciales de
cinco y veinte para los dos niveles; aún no están validados. Los 20/70 de
los JSON antiguos corresponden a Town03, con distintas duraciones, y no se
pueden trasladar directamente a este experimento. Antes de escalar hay que
preparar spawns, ampliar historiales y revisar la interpretación de `blocked`
en presencia de colas. No se aumentó la flota ni se modificó la conducción.

Después queda definir la comparación de ambos selectores bajo **dos niveles de
demanda**, como exige el objetivo 1, y ejecutar su matriz experimental.
El estudiante confirmó que los niveles de demanda serán distintas cantidades
de vehículos simultáneos. Elegir esas cantidades y la matriz de repeticiones
queda para después de corregir rutas/llegadas, definir límites temporales y
preparar las métricas. Cinco vehículos no es un requisito del protocolo.
La ampliación técnica hasta veinte quedó validada en los pilotos del día 17;
la elección de las dos demandas definitivas sigue pendiente.
Sigue pendiente caracterizar la variación física entre repeticiones si se
requiere determinismo por frame para el experimento.
Todavía no se calculan densidad o flujo para diagramas
fundamentales, ni se implementan comparación estadística final, visualizaciones
avanzadas o Google Maps API.

## Extra: errores de dependencias de rutas

- **Un carro alcanza a otro perfectamente alineado delante**: CARLA 0.9.15
  excluye el ángulo exacto de 0° en su detector básico. El proyecto usa ahora
  `CollinearSafeBasicAgent` para incluirlo sin alterar el plan de ruta ni los
  parámetros de frenado. Las pruebas de regresión contra la SDK requieren
  `$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'`.
- **El resumen muestra menos eventos que `events_log.csv`**: antes se omitían
  las esperas. La versión 2 cuenta todos los callbacks drenados; los eventos
  sin viaje tienen `trip_id` vacío. Los logs antiguos se conservan sin reescribir.
- **Cientos de colisiones en un contacto**: cada sensor puede emitir múltiples
  callbacks. Se preservan para diagnóstico; no son un conteo de accidentes
  únicos. `carla_actor_id` y `other_actor_type` ayudan a identificar participantes.
- **`--history-in no se puede combinar con random_baseline`**: elimina
  `--history-in`; el baseline solo registra llegadas nuevas. Para consumir un
  historial, usa `--scenario history_80_20`.
- **`No existe el historial dummy` / `No hay historial dummy para vehicle_XXX`**:
  en modo histórico, comprueba `vehicle_history_config` o `--history-in` y que
  existan filas de cada carro configurado. El baseline no necesita ese archivo.
- **`El mapa activo es ...; se esperaba Town01`**: detén los clientes y carga
  Town01 antes de ejecutar. `--town` valida el mapa esperado, no lo cambia.
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
