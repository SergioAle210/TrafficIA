# Manual de PowerShell

Ejecuta los ejemplos desde la raíz de TrafficIA. Los comandos que inspeccionan el mapa o crean vehículos necesitan un servidor de CARLA en marcha. Las pruebas y el análisis de registros se pueden ejecutar con el servidor apagado.

## Preparar el entorno

TrafficIA usa CARLA 0.9.15 y Python 3.7.9 de 64 bits en Windows. En cada sesión de PowerShell, indica la carpeta de la instalación de CARLA que contiene `CarlaUE4.exe`. El paquete `carla` se instala en el entorno virtual, mientras que `CARLA_PYTHONAPI` señala la carpeta del simulador que contiene `agents`.

```powershell
$carlaDir = Read-Host 'Ruta de la carpeta que contiene CarlaUE4.exe'
$env:CARLA_PYTHONAPI = Join-Path $carlaDir 'PythonAPI\carla'
$py = Join-Path $PWD 'carla-env\Scripts\python.exe'
```

En una instalación nueva, verifica que el primer comando muestre `3.7.9 64`. Crea el entorno e instala las dependencias y el paquete de CARLA con ese intérprete.

```powershell
python -c "import struct, sys; print(sys.version.split()[0], struct.calcsize('P') * 8)"
python -m venv carla-env
& $py -m pip install --upgrade pip==24.0
& $py -m pip install -r .\requirements.txt
& $py -m pip install "$env:CARLA_PYTHONAPI\dist\carla-0.9.15-cp37-cp37m-win_amd64.whl"
```

Comprueba qué copia del SDK carga el entorno y ejecuta la suite de pruebas.

```powershell
& $py -c "import carla; print(carla.__file__)"
& $py -m unittest discover -s tests -v
```

Si una prueba señala una diferencia de SHA-256 en una copia recién clonada, comprueba los finales de línea de la entrada indicada. [Formato e integridad de las entradas](../../config/README.md#integridad-de-las-entradas)

## Iniciar CARLA y cargar Town01

Inicia el servidor en su propia ventana. Cuando se muestre el mundo, carga Town01 desde la terminal de TrafficIA. El cliente se conecta a `localhost:2000` y conserva el mundo si Town01 ya está activo. Cuando hay otro mapa, CARLA reemplaza el mundo al cargar Town01. Termina antes cualquier simulación que esté usando ese servidor.

```powershell
Start-Process -FilePath (Join-Path $carlaDir 'CarlaUE4.exe') -WorkingDirectory $carlaDir `
    -ArgumentList '-quality-level=Low', '-dx11', '-windowed', '-ResX=800', '-ResY=600'
```

```powershell
& $py .\scripts\maps\load_map.py --town Town01
```

## Inspeccionar el mapa

Coloca la cámara del espectador sobre la zona de interés. El inspector imprime la posición del espectador, el punto proyectado en un carril de conducción, su carretera y carril, el índice de aparición más cercano y una fila de ejemplo para el catálogo. Este comando dibuja los índices y la orientación de todos los puntos de aparición y resalta el 133 en rojo durante 120 segundos simulados.

```powershell
& $py .\scripts\maps\inspect_location.py --town Town01 --show-spawn-points --highlight-spawn-point 133 --debug-lifetime-seconds 120
```

`--town` comprueba el nombre del mapa activo. `--show-spawn-points` habilita el dibujo. Si omites `--highlight-spawn-point`, se resalta el índice más cercano al punto vial proyectado. `--debug-lifetime-seconds` acepta una duración positiva. `--host` y `--port` permiten seleccionar el servidor que se quiere inspeccionar.

Para verificar las rutas del catálogo, empieza por un origen y después comprueba todos los pares dirigidos. Los dos comandos consultan el mapa activo sin crear vehículos.

```powershell
& $py .\scripts\maps\validate_destinations.py --town Town01 --origin-id T01_133
$informeRutas = Join-Path '.\data\output' ('rutas_' + (Get-Date -Format yyyyMMdd_HHmmssfff) + '.json')
& $py .\scripts\maps\validate_catalog_routes.py --report $informeRutas --carla-pythonapi $env:CARLA_PYTHONAPI
```

El primer comando imprime las distancias desde `T01_133` y los destinos cuya ruta falló. Permite cambiar el catálogo con `--destinations`, la separación entre puntos de ruta con `--sampling-resolution` (metros), la conexión con `--host` y `--port`, y la ubicación de `agents` con `--carla-pythonapi`. El segundo comprueba cada par dirigido de destinos distintos del catálogo de Town01 y escribe un JSON en la ruta nueva indicada por `--report`. Si el manifiesto de una campaña identifica los casos con `id` y `run_directories`, `--campaign-manifest` permite comprobar además el origen real de sus intentos `route_failed`. Para los casos que genera `run_demand.py`, que carecen del campo `id`, usa la validación del catálogo sin esa opción. [Referencias viales del catálogo](../referencia/destinos-town01.md)

## Ejecutar viajes

La configuración de varios vehículos define un origen fijo para cada uno. El historial contiene las visitas iniciales de cada uno. La consola imprime la carpeta de la corrida al terminar.

```powershell
$flota = '.\config\trips\multi_vehicle_trip.json'
$historial = '.\data\input\histories\Town01\bootstrap\vehicle_history_dummy.csv'
& $py .\scripts\simulation\run_trips.py --config $flota --scenario history_80_20 --history-in $historial --seconds 120
```

| Opción | Efecto |
|---|---|
| `--config`, `--town` | Seleccionan el JSON y el mapa que debe estar activo. El JSON predeterminado es `config/trips/single_vehicle_trip.json`. |
| `--scenario`, `--history-in` | `history_80_20` permite cargar un historial inicial o reutilizar el `vehicle_history.csv` de otra corrida. Se necesitan visitas para todos los vehículos configurados. Con `random_baseline`, omite `--history-in`. |
| `--seed`, `--seconds` | Sobrescriben la semilla y la duración total simulada del JSON. Al terminar se cierran los viajes activos. |
| `--max-trip-seconds` | Fija el límite de tiempo simulado por intento. El valor `0` desactiva ese límite. |
| `--blocked-policy` | `terminate` cierra el intento al alcanzar el umbral de detención. `keep_trip` conserva el destino y registra el aviso. |
| `--simulation-speed` | Solicita un ritmo de 1 a 5 segundos simulados por segundo real. El valor predeterminado es 1 y el paso físico sigue siendo el del JSON. |
| `--no-rendering` | Desactiva el renderizado del mundo durante la corrida. |
| `--navigation-diagnostics` | Registra el plan de ruta, las órdenes de control y las llegadas confirmadas. |
| `--controller-distance-ratio` | Ajusta el factor que relaciona la velocidad con la distancia a la que el controlador descarta puntos de ruta. Cambia el comportamiento de conducción. |
| `--carla-pythonapi` | Indica la carpeta que contiene los agentes de navegación de CARLA. |

El ejecutor instrumentado registra la fase de cada vehículo en cada paso y activa los diagnósticos de navegación. Acepta las opciones de viajes y añade `--no-cameras`. Con esa opción se omiten las cámaras RGB y se mantienen los registros, aunque el espectador puede seguir viendo el mundo. Para prescindir también del renderizado, combina `--no-cameras` con `--no-rendering`. La captura RGB requiere renderizado activo. [Contenido de los archivos de salida](../referencia/datos-y-metricas.md#después-de-ejecutar)

```powershell
& $py .\scripts\simulation\observe_trips.py --config $flota --scenario random_baseline --seconds 60 --no-cameras
```

## Ejecutar una campaña

El ejecutor combina cada flota seleccionada con los dos selectores de destinos. Las configuraciones, los historiales iniciales y el clima se distribuyen con el proyecto. Se necesitan el cliente y el servidor de CARLA 0.9.15, Town01 en modo asíncrono y un mundo libre de vehículos, peatones y sensores.

Este ejemplo fija la duración de cada caso en segundos simulados. Primero comprueba el mapa y las huellas de las entradas. Después inicia una campaña en una carpeta nueva bajo `data/output/`. Con `--manual-start` se requiere una terminal interactiva.

```powershell
$duracion = 120
& $py .\scripts\campaigns\run_demand.py --seconds $duracion --check-only --carla-pythonapi $env:CARLA_PYTHONAPI
if ($LASTEXITCODE -ne 0) { throw 'Revisa el estado del servidor y las entradas.' }
& $py -u .\scripts\campaigns\run_demand.py --seconds $duracion --simulation-speed 1 --manual-start --carla-pythonapi $env:CARLA_PYTHONAPI
```

| Opción | Uso |
|---|---|
| `--check-only` | Verifica el servidor, el mapa y las entradas. Si supera las comprobaciones devuelve el estado `ready` sin crear actores. |
| `--manual-start` | Espera una pulsación de Enter antes de cada caso, incluido el primero. Si lo omites, los casos se ejecutan de forma continua. |
| `--counts` | Selecciona uno o ambos tamaños de flota admitidos. Consulta los valores con `--help` y pásalos en orden ascendente, sin repetirlos. Por defecto se usan ambas flotas. |
| `--seed`, `--seconds`, `--simulation-speed` | Fijan la semilla, la duración por caso y el ritmo solicitado respecto al reloj real. La semilla interviene en la selección de destinos y atributos de los vehículos. |
| `--output` | Permite elegir una carpeta nueva dentro de `data/output/`. Al omitirla, el ejecutor asigna el nombre. |
| `--purpose` | Etiqueta la ejecución como `exploratory_demand` o `technical_check`. |
| `--carla-pythonapi` | Indica la carpeta que contiene `agents` para el ejecutor de cada caso. |

Cuando la campaña termina correctamente, la consola muestra `COMPLETE` seguido de la ruta del manifiesto JSON. Si falla o se interrumpe durante la ejecución de los casos, muestra `INCOMPLETE` y la ruta del manifiesto parcial. Copia la ruta del manifiesto para generar un índice de tus casos. El índice se guarda junto al manifiesto en CSV y HTML. Desde el HTML puedes abrir las carpetas y los registros de cada corrida.

```powershell
$manifiesto = Read-Host 'Ruta del manifiesto que imprimió la campaña'
& $py .\scripts\campaigns\index_runs.py --campaign $manifiesto
```

## Analizar y graficar

Puedes analizar una corrida individual pasando su carpeta como argumento posicional a `analyze_mobility.py` y eligiendo una carpeta nueva con `--output`. El programa escribe las métricas disponibles y devuelve el código 1 si detecta errores de integridad o si falta una pareja comparable de selectores. El informe distingue ambas situaciones. [Cómo interpretar las métricas](../referencia/datos-y-metricas.md#estados-y-métricas)

```powershell
$corrida = Read-Host 'Ruta de la carpeta de tu corrida'
$informe = Join-Path '.\data\output' ('metricas_' + (Get-Date -Format yyyyMMdd_HHmmssfff))
& $py .\scripts\analysis\analyze_mobility.py $corrida --output $informe
```

Para generar la galería de tu campaña, ejecuta primero todos los casos con ambas flotas, los dos selectores, la misma semilla y la misma duración. Utiliza el manifiesto indicado por `COMPLETE` y conserva las carpetas de sus corridas. Los comandos se ejecutan con el servidor apagado. El cálculo espacial usa el SDK de CARLA y el archivo OpenDRIVE de Town01 de tu instalación.

```powershell
$analisis = Join-Path '.\data\output' ('analisis_' + (Get-Date -Format yyyyMMdd_HHmmssfff))
$graficas = Join-Path $analisis 'graficas'
$xodr = Join-Path $carlaDir 'CarlaUE4\Content\Carla\Maps\OpenDrive\Town01.xodr'
& $py .\scripts\analysis\analyze_mobility.py --campaign $manifiesto --output "$analisis\metricas"
if ($LASTEXITCODE -ne 0) { throw 'Consulta el informe de métricas y comparabilidad.' }
& $py .\scripts\figures\build_plot_data.py --campaign $manifiesto --output $graficas --xodr $xodr
if ($LASTEXITCODE -ne 0) { throw 'Revisa el error de cálculo de densidad y flujo.' }
& $py .\scripts\figures\verify_plot_inputs.py --campaign $manifiesto --output $graficas
if ($LASTEXITCODE -ne 0) { throw 'Revisa la verificación de los registros antes de graficar.' }
& $py .\scripts\figures\plot_demand.py --data $graficas
```

En `$analisis\metricas` encontrarás el informe de movilidad, las tablas CSV y el análisis en JSON. En `$graficas` se guardan las mediciones por tramo y ventana, la verificación de las fuentes y las figuras. Abre `index.html` en esa carpeta para consultar la galería. También se exportan un PDF y archivos PNG y SVG. [Definición de flujo y densidad](../referencia/datos-y-metricas.md#flujo-y-densidad-por-carril)

`plot_demand.py` admite `--independent-output` y `--prefix` para guardar figuras individuales con un prefijo propio. Cuando un caso termina sin llegadas, la exportación individual indica que el tiempo medio de viaje está sin definir. Para comparar dos campañas tuyas, genera primero la galería de cada una con los pasos anteriores. Vuelve a verificar el manifiesto de la primera con `verify_plot_inputs.py` indicando como `--output` la subcarpeta `previous_review/` dentro de los derivados de la segunda. Ejecuta `plot_demand.py` con `--data` apuntando a los derivados de la segunda y `--compare-data` a la galería de la primera. La comparación empareja los casos por flota, selector y semilla y exige que coincidan las condiciones de medición y las huellas de los archivos de código y de entrada que guardó cada campaña.

### Graficar una corrida y reunir galerías

Para una corrida individual, pasa su carpeta de registros a `plot_mobility.py`. También admite la carpeta de un informe de movilidad o los derivados de una campaña. En estos dos casos necesita acceso a las corridas originales. Si las moviste, `--runs-root` indica la carpeta que las contiene por identificador. Las gráficas de flujo y las series por ventana requieren los derivados de `build_plot_data.py`.

```powershell
$corrida = Read-Host 'Carpeta de la corrida'
$destino = Join-Path '.\data\output' ('figuras_' + (Get-Date -Format yyyyMMdd_HHmmssfff))
& $py .\scripts\figures\plot_mobility.py --data $corrida --output "$destino\galeria"
& $py .\scripts\figures\export_charts.py --data $corrida --output "$destino\individuales" --prefix movilidad
& $py .\scripts\figures\build_collection.py --data "$destino\galeria" --output "$destino\coleccion"
```

Abre `index.html` en la galería para consultar las figuras y el PDF. El exportador escribe PNG, SVG y un manifiesto con huellas SHA-256. El constructor reúne las galerías que indiques en `--data` en una carpeta nueva, verifica las copias y genera un catálogo, una página HTML y fragmentos LaTeX. Acepta gráficas de diagnóstico adicionales con `--figure`. Con `--independent` genera las figuras directamente desde los registros.

## Otras herramientas

Las rutas de la tabla parten de `scripts/`. Usa `--help` para consultar la sintaxis de cada comando.

| Herramienta | Requisitos, argumentos y resultado |
|---|---|
| `maps/reload_town01.py` | Recarga Town01 en el servidor local, incluso si ya está activo. Úsalo cuando puedas reemplazar el mundo actual. |
| `preparation/generate_sample_inputs.py` | `--output-dir` indica la carpeta que contiene `catalogs/Town01/destinations_config.csv`. Escribe o reemplaza los CSV de `examples/` y el historial de `histories/Town01/bootstrap/`. La raíz predeterminada es `data/input/`. `--seed`, `--vehicles`, `--history-length`, `--routine-destinations` y `--routine-probability` controlan la generación de visitas iniciales. |
| `preparation/prepare_pilots.py` | Lee el mapa Town01 activo y prepara configuraciones e historiales para flotas de tamaño creciente. Comprueba los archivos existentes y rechaza sustituir una entrada distinta. |
| `preparation/prepare_demand.py` | Usa el mapa Town01 y las entradas de flota distribuidas. `--weather-from` recibe el `run_config.json` de una corrida propia con `environment.weather`. Crea entradas de demanda o comprueba que sean idénticas a las existentes. |
| `simulation/run_traffic_manager.py` | Retira los vehículos que ya están en el mapa antes de crear su flota con autopiloto. Acepta `--town`, `--vehicles`, `--seconds` de tiempo simulado y `--no-rendering`. Informa del progreso por consola. |
| `simulation/spawn_autopilot.py` | Crea vehículos con autopiloto en los puntos de aparición disponibles del mapa y los deja circular durante un intervalo de reloj real. Retira los actores creados al terminar. |
| `diagnostics/inspect_dwell.py` | Acepta las opciones de `run_trips.py` y requiere Town01. Registra la aproximación y la espera en `T01_067` en `dwell_log.csv`. Guarda la geometría y la configuración de diagnóstico junto a la corrida. |
| `diagnostics/compare_stop_policies.py` | Requiere Town01 libre, en modo asíncrono y con renderizado. Ejecuta un diagnóstico de las políticas `terminate` y `keep_trip`. `--check-only` verifica el entorno, `--technical-only` ejecuta la comprobación breve y `--skip-technical` selecciona las ejecuciones por política. Admite `--carla-pythonapi`. |
| `diagnostics/audit_observations.py` | Recibe dos argumentos posicionales, la carpeta de una corrida instrumentada y una carpeta de salida nueva. Escribe `audit.json` y gráficas de trayectorias. `--minimum-cycles` exige un mínimo de ciclos completos y `--xodr` indica la geometría vial. Usa `--source-root` con la carpeta `source_snapshot/` de la campaña para comprobar las huellas contra el código empleado en tu ejecución. |

`diagnostics/observation_stream.py` y `analysis/compare_repetitions.py` son módulos auxiliares que se utilizan desde los ejecutores y las herramientas de gráficas.

## Resolver incidencias

| Síntoma | Qué comprobar |
|---|---|
| Expira la conexión a `localhost:2000` | Espera a que termine de cargar el servidor y comprueba el mapa activo con `& $py .\scripts\maps\inspect_location.py --town Town01`. |
| No se encuentra `carla` o `agents` | Verifica el intérprete en `$py`, la compatibilidad del paquete con Python 3.7 de 64 bits y la existencia de la subcarpeta `agents` en `$env:CARLA_PYTHONAPI`. |
| La campaña informa de una huella de entrada distinta | Identifica el archivo en el mensaje de error y compara sus bytes con la huella de referencia antes de repetir `--check-only`. [Integridad de las entradas](../../config/README.md#integridad-de-las-entradas) |
| Falla la importación de `networkx` o `shapely` | Instala `requirements.txt` con el mismo intérprete que ejecuta los viajes. |
| El punto de aparición está ocupado o el mundo está en modo síncrono | Termina la simulación que utiliza ese mundo y espera a que retire sus actores. Para una campaña, vuelve a ejecutar `--check-only`. |
| CARLA muestra un error de Unreal o D3D11 | Conserva las salidas y reinicia el servidor. Usa una ventana de baja resolución y `--no-cameras` si necesitas únicamente los registros de observación. |
| El análisis rechaza una campaña incompleta | Consulta el manifiesto que indica la consola y pasa al analizador las carpetas de las corridas que hayan terminado. |

Al interrumpir un ejecutor de viajes con `Ctrl+C`, este inicia la retirada de sus vehículos y sensores. En una campaña interrumpida puedes consultar en el manifiesto qué casos alcanzaron el estado `completed`.
