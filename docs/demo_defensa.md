# Demostración de TrafficIA: diapositiva 45

Cuatro ejecuciones de **180 segundos simulados** cada una, confirmadas para
la demostración. Son **12 minutos simulados en total**. Se reservan otros
tres minutos de exposición para explicar la arquitectura y abrir los registros.

| Orden | Nombre para identificar la salida | Vehículos | Selector | Duración simulada |
|---|---|---:|---|---:|
| 1 | `20_uniforme` | 20 | `random_baseline` | 180 s |
| 2 | `20_historico_80_20` | 20 | `history_80_20` | 180 s |
| 3 | `100_uniforme` | 100 | `random_baseline` | 180 s |
| 4 | `100_historico_80_20` | 100 | `history_80_20` | 180 s |

## Tiempo de la demostración

`--seconds 180` mide tiempo **simulado**. `--simulation-speed 1` solicita
un ritmo de un segundo simulado por segundo real, pero el equipo puede
procesarlo más despacio. Crear vehículos, comprobar entradas, cerrar los
registros y calcular métricas también consume tiempo real. Por eso, el
comando completo no garantiza terminar en doce minutos de reloj.

Ensaya las cuatro ejecuciones antes de la defensa. Si exceden el tiempo
disponible, utiliza las grabaciones con los registros de esas mismas
ejecuciones. Indica cualquier aceleración del video. Conserva los registros
de cualquier falla o interrupción; una ejecución incompleta no se presenta
como una corrida completada.

## 1. Iniciar CARLA: primera ventana de PowerShell

Utiliza el mismo arranque descrito en los anexos: calidad gráfica baja,
DirectX 11 y ventana de 800 por 600 píxeles. Ejecuta este bloque una sola vez:

```powershell
Set-Location C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```

Espera a que aparezca el simulador. Mantén CARLA abierto durante las cuatro
ejecuciones; las instrucciones siguientes van en una segunda ventana.

## 2. Preparar TrafficIA y cargar Town01: segunda ventana

Todos los comandos siguientes utilizan directamente el Python del entorno
virtual, por lo que no necesitas activar `carla-env` con otro comando.

```powershell
Set-Location C:\CARLA\TrafficIA
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
.\carla-env\Scripts\python.exe .\scripts\change_map.py --town Town01
```

Espera a que Town01 termine de cargar, aproximadamente de 10 a 15 segundos.
Si ya está activo, el comando conserva el mapa. La variable de entorno
indica dónde están los agentes de CARLA y solo afecta esta terminal y los
procesos que inicies desde ella.

## 3. Comprobaciones previas

Durante el ensayo, comprueba primero las pruebas del proyecto. No crean
vehículos en el servidor:

```powershell
.\carla-env\Scripts\python.exe -B -m unittest discover -s tests
```

Después comprueba el servidor y las entradas. También puedes repetir este
bloque antes de cada ejecución independiente:

```powershell
.\carla-env\Scripts\python.exe -u .\scripts\run_demand_campaign.py --counts 20 100 --seed 210 --seconds 180 --simulation-speed 1 --check-only
if ($LASTEXITCODE -ne 0) { throw 'La comprobación previa falló. Revisa el mensaje antes de ejecutar vehículos.' }
```

El resultado debe indicar `"status": "ready"`, CARLA 0.9.15 y cero actores
creados. Esta revisión verifica las entradas preparadas, el mapa y un mundo
sin otros vehículos, peatones o sensores, fuera del modo síncrono de otra
ejecución. No inicia CARLA, no crea vehículos ni cambia el clima.

Si encuentra actores o un estado síncrono pendiente, termina la ejecución
anterior. Si esa ejecución falló y no limpió el mundo, reinicia CARLA y repite
los pasos 2 y 3; no elimines registros para ocultar la interrupción.

## 4. Aplicar el ambiente existente y preparar los nombres de salida

Las ejecuciones individuales conservan el clima que tenga el servidor.
Este bloque aplica la plantilla ambiental que ya utilizó la campaña. Solo
ajusta el mundo abierto; no modifica el JSON ni sus valores. Ejecútalo después
de cargar Town01 y repítelo si reinicias CARLA:

```powershell
@'
import json
from pathlib import Path
import carla

client = carla.Client('localhost', 2000)
client.set_timeout(15.0)
world = client.get_world()
weather = carla.WeatherParameters()
for name, value in json.loads(Path('config/demand_20_100/weather.json').read_text(encoding='utf-8')).items():
    setattr(weather, name, value)
world.set_weather(weather)
print('Clima de la campaña aplicado.')
'@ | .\carla-env\Scripts\python.exe -
if ($LASTEXITCODE -ne 0) { throw 'No se pudo aplicar el ambiente preparado.' }
```

Crea una carpeta nueva para los cuatro registros de consola. Conserva esta
terminal abierta para mantener el valor de `$demo`:

```powershell
$demo = Join-Path (Get-Location).Path ("data\output\demo_individual_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff"))
New-Item -ItemType Directory -Path $demo -ErrorAction Stop | Out-Null
```

## 5. Ejecutar cada caso por separado

Ejecuta **un bloque a la vez**. Espera a que termine y vuelve a la terminal
cuando quieras iniciar el siguiente. No ejecutes dos clientes simultáneamente.
Cada bloque contiene una sola corrida de 180 segundos simulados.

### 20 vehículos: aleatorio uniforme

```powershell
.\carla-env\Scripts\python.exe -u .\scripts\review_trip_simulation.py `
  --config .\config\demand_20_100\town01_020.json --scenario random_baseline `
  --seed 210 --seconds 180 --simulation-speed 1 --navigation-diagnostics --no-cameras `
  2>&1 | Tee-Object -FilePath (Join-Path $demo '20_uniforme_console.txt')
if ($LASTEXITCODE -ne 0) { throw 'La ejecución 20_uniforme no terminó correctamente.' }
```

### 20 vehículos: histórico 80/20

```powershell
.\carla-env\Scripts\python.exe -u .\scripts\review_trip_simulation.py `
  --config .\config\demand_20_100\town01_020.json --scenario history_80_20 `
  --seed 210 --seconds 180 --simulation-speed 1 --navigation-diagnostics --no-cameras `
  2>&1 | Tee-Object -FilePath (Join-Path $demo '20_historico_80_20_console.txt')
if ($LASTEXITCODE -ne 0) { throw 'La ejecución 20_historico_80_20 no terminó correctamente.' }
```

### 100 vehículos: aleatorio uniforme

```powershell
.\carla-env\Scripts\python.exe -u .\scripts\review_trip_simulation.py `
  --config .\config\demand_20_100\town01_100.json --scenario random_baseline `
  --seed 210 --seconds 180 --simulation-speed 1 --navigation-diagnostics --no-cameras `
  2>&1 | Tee-Object -FilePath (Join-Path $demo '100_uniforme_console.txt')
if ($LASTEXITCODE -ne 0) { throw 'La ejecución 100_uniforme no terminó correctamente.' }
```

### 100 vehículos: histórico 80/20

```powershell
.\carla-env\Scripts\python.exe -u .\scripts\review_trip_simulation.py `
  --config .\config\demand_20_100\town01_100.json --scenario history_80_20 `
  --seed 210 --seconds 180 --simulation-speed 1 --navigation-diagnostics --no-cameras `
  2>&1 | Tee-Object -FilePath (Join-Path $demo '100_historico_80_20_console.txt')
if ($LASTEXITCODE -ne 0) { throw 'La ejecución 100_historico_80_20 no terminó correctamente.' }
```

El parámetro `--no-cameras` evita crear cámaras RGB por vehículo; la ventana
de CARLA permanece visible. Puedes observar desde la cámara del espectador
y grabar la pantalla con tu herramienta habitual. La posición de esa cámara
no determina los destinos ni las rutas.

Se conservan semilla 210, paso de 0.05 s, puntos de salida, historiales,
controlador y política de bloqueo predeterminada. Los argumentos seleccionan
el modelo y los 180 s de la demo sin reescribir ningún archivo de configuración.
Cada histórico comienza con las visitas preparadas de su grupo; no carga el
historial producido por la demostración anterior.

## 6. Localizar los cuatro resultados

Cada consola termina con `Revisión guardada en:` y la carpeta correspondiente.
Los cuatro archivos `*_console.txt` de `$demo` permiten reconocer el caso.
Los CSV originales permanecen en `data/output/town01_...`; no se renombran
ni se mueven. Si quieres repetir un caso, crea otra carpeta `$demo` para
conservar también su registro de consola anterior.

Después de las cuatro ejecuciones, este bloque reúne sus rutas en un CSV
pequeño. Solo incluye los casos que imprimieron el mensaje final de guardado:

```powershell
$indiceIndividual = @(Get-ChildItem -LiteralPath $demo -Filter '*_console.txt' |
  Select-String -Pattern 'guardada en: (.+)$' |
  ForEach-Object {
    [pscustomobject]@{
      caso = $_.Filename -replace '_console\.txt$', ''
      carpeta = $_.Matches[0].Groups[1].Value.Trim()
    }
  })
$indiceIndividual | Export-Csv -LiteralPath (Join-Path $demo 'indice_individual.csv') -NoTypeInformation -Encoding UTF8
$indiceIndividual | Format-Table -AutoSize
```

Tras una demo completa deben aparecer cuatro filas. Si falta un caso,
revisa su archivo de consola; una corrida interrumpida no equivale a una
corrida completada. Este índice identifica carpetas y no certifica la
integridad de sus registros.

Para abrir, por ejemplo, la carpeta del histórico de 20 vehículos:

```powershell
$salida20Historico = $indiceIndividual | Where-Object { $_.caso -eq '20_historico_80_20' }
if ($null -ne $salida20Historico) { Invoke-Item -LiteralPath $salida20Historico.carpeta }
```

Allí puedes mostrar `run_config.json`, `trips_log.csv`, `observation_log.csv`,
`events_log.csv` y `vehicle_history.csv`. Para una revisión de integridad tras
el ensayo, utiliza el comando existente sobre una corrida completa y una
carpeta de auditoría nueva:

```powershell
$auditoria20Historico = Join-Path $demo ('auditoria_20_historico_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
if ($null -ne $salida20Historico) {
  .\carla-env\Scripts\python.exe .\scripts\audit_observations.py $salida20Historico.carpeta $auditoria20Historico
}
```

Esta revisión se hace fuera de los doce minutos de simulación. No se exige
una llegada por vehículo para declarar íntegros los registros.

## Alternativa: ejecutar los cuatro casos automáticamente

Si prefieres que las cuatro corridas avancen sin una pausa manual entre ellas,
utiliza este bloque **en lugar de los cuatro comandos del paso 5**. Requiere
CARLA abierto, Town01 y la comprobación previa. La campaña aplica su plantilla
ambiental y restaura el clima anterior al terminar, además de calcular métricas
y realizar auditorías. Ese trabajo adicional consume tiempo real.

```powershell
$campanaDemo = Join-Path (Get-Location).Path ("data\output\demo_campana_" + (Get-Date -Format "yyyyMMdd_HHmmss_fff"))
.\carla-env\Scripts\python.exe -u .\scripts\run_demand_campaign.py --counts 20 100 --seed 210 --seconds 180 --simulation-speed 1 --purpose technical_check --output $campanaDemo
.\carla-env\Scripts\python.exe .\scripts\index_demo_outputs.py --campaign (Join-Path $campanaDemo 'campaign.json')
Invoke-Item (Join-Path $campanaDemo 'indice_demo.html')
```

No crees previamente `$campanaDemo`: el ejecutor crea esa carpeta y rechaza
sobrescribir una existente. La etiqueta `technical_check` identifica estas
pruebas breves y no cambia las reglas de simulación.

`index_demo_outputs.py` es un auxiliar para las salidas de **campañas**:
lee `campaign.json` y genera `indice_demo.html` e `indice_demo.csv`, con nombres
legibles, estados y enlaces a los archivos existentes. Si la campaña se
interrumpe y ya existe su manifiesto, puedes generar el índice para consultar
los casos terminados, interrumpidos o pendientes.

Las ejecuciones individuales del paso 5 no generan `campaign.json`; utilizan
el índice del paso 6. Ninguno de los índices modifica los CSV de las corridas.

## Orden de los archivos para explicar la arquitectura

Los archivos conservan sus nombres; la implementación se agrupa por función:

```text
scripts/
  run_demand_campaign.py       Campaña automática y comprobación previa
  run_trip_simulation.py       Entrada para una ejecución sencilla
  review_trip_simulation.py    Ejecuta cada caso de esta demo y registra pasos
  index_demo_outputs.py        Índice de salidas de campañas existentes
src/
  demand/
    destinations.py           Catálogo y elección uniforme
    vehicle_history.py        Historial individual y elección 80/20
  navigation/
    route_planner.py          Planificación de rutas y creación del agente
    carla_agent.py            Agente de conducción usado por el proyecto
    arrival.py                Criterios de aproximación y llegada
    navigation_diagnostics.py Datos para revisar rutas y controles
  simulation/
    trip_runner.py            Ciclo de viajes y coordinación de vehículos
    stop_review.py            Experimento de detenciones, fuera de esta demo
  recording/
    run_logger.py             Registros de viajes, trayectorias y eventos
    visual_review.py          Observación de todos los pasos de simulación
  analysis/
    mobility_analysis.py      Métricas de los viajes y de la presencia
    incident_analysis.py      Análisis de notificaciones
    traffic_flow_analysis.py  Medidas de flujo, densidad y velocidad
```

Los archivos `__init__.py` permiten importar las carpetas como paquetes.
`scripts/` contiene los comandos de entrada: algunos ejecutan simulaciones
y otros preparan datos, validan, analizan o generan gráficas. El funcionamiento
compartido está agrupado en `src/`. Los comandos existentes conservan sus
nombres; en la explicación no es necesario abrirlos todos.

La secuencia para explicar es: **leer entradas → coordinar los vehículos →
elegir destino → planificar y conducir → comprobar llegada → registrar y
analizar**. La elección uniforme está en `destinations.py`; la histórica,
en `vehicle_history.py`. Un planificador global se comparte entre vehículos
y cada vehículo tiene su agente de conducción.

### Guion para los tres minutos restantes

| Tiempo | Qué mostrar | Qué puedes decir |
|---|---|---|
| 0:00–0:35 | `scripts/review_trip_simulation.py` y la carpeta `config/demand_20_100/` | «Desde este comando inicio cada prueba. Lee las condiciones preparadas y recibe el grupo de vehículos, la regla de elección y la duración que vamos a mostrar». |
| 0:35–1:10 | `src/simulation/trip_runner.py`, clase `TripSimulation` | «Aquí se coordina el ciclo de todos los vehículos: elegir, conducir, comprobar la llegada y volver a empezar». |
| 1:10–1:45 | Carpetas `demand/` y `navigation/`; función `select_from_history` | «La elección del destino está separada de la conducción. El historial utiliza la regla 80/20; el planificador calcula el recorrido y cada agente controla su vehículo». |
| 1:45–2:15 | `recording/` e `indice_individual.csv` | «Mientras el simulador avanza, guardamos el estado de los vehículos y lo que ocurre en los viajes. Este índice identifica los cuatro casos y la carpeta de cada uno». |
| 2:15–3:00 | `trips_log.csv` de un caso completado | «Cada fila corresponde a un intento. Aquí vemos el destino, el tipo de selección y si terminó en llegada. Estos registros permiten calcular los resultados». |

Para el último paso, filtra `vehicle_id` y muestra `selection_class`,
`destination_id`, `destination_category` y `status`. En el histórico aparecen
`routine` y `exploration`; en el uniforme, `random_baseline`. Una llegada
completada añade una visita al historial. Si la demostración no contiene
ambas ramas o una llegada del vehículo seleccionado, muestra lo registrado;
no atribuyas al video una comprobación estadística del 80/20.

Estas demostraciones de 180 s producen 3600 observaciones por vehículo si
terminan completas. Las 72 000 observaciones por vehículo de la tesis
corresponden a corridas de 3600 s. Los resultados académicos siguen siendo
los de aquellas ocho corridas; no se sustituyen por los de la demo.

## Alcance de la reorganización

Se trasladaron módulos a carpetas, se actualizaron sus importaciones y las
rutas de código que guardan los informes de procedencia. Las copias de código
de las campañas incluyen ahora las subcarpetas de `src/`. La selección,
el controlador, el orden del ciclo, los cálculos y los formatos de los CSV
se mantienen. Los nombres y hashes de los archivos fuente reflejarán su nueva
ubicación; las salidas históricas conservan su procedencia original.

La misma lógica no garantiza trayectorias idénticas en nuevas corridas de
CARLA. Se comprueba la conservación del código y las entradas mediante
revisión de cambios y pruebas; el rendimiento real se comprueba al ensayar
en el equipo que utilizarás durante la defensa.
