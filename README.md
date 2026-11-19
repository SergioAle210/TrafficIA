# TrafficIA · Tráfico urbano en CARLA

TrafficIA simula viajes sucesivos en el mapa urbano Town01 de CARLA. Cada vehículo elige un destino, sigue una ruta por la red vial y, tras llegar y esperar, inicia otro viaje. Las campañas permiten comparar dos reglas de elección sobre el mismo catálogo de destinos y con el mismo controlador.

| Selector | Cómo elige el siguiente destino |
|---|---|
| `random_baseline` | Elige con igual probabilidad entre los destinos habilitados distintos del actual. |
| `history_80_20` | Con la configuración incluida, el vehículo tiene un 80 % de probabilidad de intentar volver a uno de sus tres destinos más visitados y un 20 % de explorar, con preferencia por los lugares que aún no ha visitado. Cada llegada actualiza su historial. |

Los registros permiten comparar los destinos asignados y alcanzados, la duración de los viajes completados, la velocidad media de la flota durante los viajes y las esperas, y la frecuencia de los avisos de colisión e invasión de carril que emiten los sensores. [Definiciones de las métricas](docs/referencia/datos-y-metricas.md#estados-y-métricas)

## Variables de entorno

CARLA 0.9.15 distribuye los agentes de navegación por separado del paquete de Python `carla`. Define `CARLA_PYTHONAPI` con la ruta absoluta a `PythonAPI\carla`, la carpeta que contiene `agents`. También puedes indicar esa ruta con `--carla-pythonapi` en los comandos que lo admiten.

Para guardar la ruta entre sesiones, crea `.env` a partir de la plantilla desde la raíz de TrafficIA. [Plantilla de entorno](.env.example)

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

En `.env`, sustituye la ruta de ejemplo por la de tu instalación, sin comillas. Git excluye este archivo local.

TrafficIA lee la variable del entorno del proceso. En cada nueva sesión de PowerShell, carga manualmente el valor desde `.env` y comprueba que la ruta contenga la carpeta `agents`.

```powershell
$linea = Get-Content -LiteralPath '.env' | Where-Object { $_ -match '^CARLA_PYTHONAPI=\s*\S' } | Select-Object -First 1
if (-not $linea) { throw 'Define CARLA_PYTHONAPI en .env.' }
$env:CARLA_PYTHONAPI = ($linea -split '=', 2)[1].Trim()
Test-Path -LiteralPath (Join-Path $env:CARLA_PYTHONAPI 'agents') -PathType Container
```

La última orden debe devolver `True`. Si devuelve `False`, corrige la ruta en `.env` y vuelve a cargarla en la misma consola.

El host, el puerto, el mapa y la duración se configuran en el JSON de la simulación o mediante las opciones que admite cada comando.

## Primera simulación en Town01

El ejemplo usa CARLA 0.9.15 y Python 3.7.9 de 64 bits en Windows. Prepara el entorno `carla-env` del proyecto y configura `CARLA_PYTHONAPI` en la consola desde la que ejecutarás los viajes. [Preparar el entorno](docs/guias/manual.md#preparar-el-entorno)

Abre otra ventana de PowerShell en la carpeta que contiene `CarlaUE4.exe` e inicia el servidor local.

```powershell
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```

Cuando el servidor haya cargado el mundo, vuelve a la consola del proyecto. Desde la raíz de TrafficIA, carga Town01 y ejecuta un vehículo con el selector histórico durante el tiempo que indiques. El ejemplo fija una duración de dos minutos simulados.

```powershell
.\carla-env\Scripts\python.exe .\scripts\maps\load_map.py --town Town01
.\carla-env\Scripts\python.exe .\scripts\simulation\run_trips.py --scenario history_80_20 --seconds 120
```

Al terminar, busca **Salida guardada en** en la consola y abre la carpeta indicada dentro de `data/output/`. En `trips_log.csv`, cada fila corresponde a un intento de viaje. El estado `completed` indica una llegada y `aborted` identifica un viaje aún activo al final de la simulación. Consulta `vehicle_history.csv` para ver las visitas y `run_config.json` para comprobar el mapa, la semilla y los parámetros efectivos. [Cómo seguir un viaje en los registros](docs/referencia/datos-y-metricas.md#seguir-un-viaje)

## Guías y referencia

| Tarea | Recurso |
|---|---|
| Inspeccionar puntos del mapa, iniciar campañas, ejecutar pruebas o generar gráficas | [Manual de PowerShell](docs/guias/manual.md) |
| Entender cómo se selecciona un destino y cuándo se acepta una llegada | [Arquitectura del simulador](docs/referencia/arquitectura.md) |
| Elegir la flota, el catálogo y el historial de una simulación | [Configuraciones](config/README.md) y [datos de entrada y salida](data/README.md) |
| Localizar la implementación, los comandos y las pruebas | [Código fuente](src/), [scripts](scripts/) y [pruebas](tests/) |
| Explorar las guías y la evolución del simulador | [Índice de documentación](docs/README.md) |

[Licencia del proyecto](LICENSE)
