# TrafficIA · Tráfico urbano en CARLA

TrafficIA simula viajes sucesivos en el mapa urbano Town01 de CARLA. Cada vehículo elige un destino, sigue una ruta por la red vial y, tras llegar y esperar, inicia otro viaje. Las campañas permiten comparar dos reglas de elección sobre el mismo catálogo y con el mismo controlador.

| Selector | Cómo elige el siguiente destino |
|---|---|
| `random_baseline` | Elige con igual probabilidad entre los destinos habilitados distintos del actual. |
| `history_80_20` | Con la configuración incluida, el vehículo tiene un 80 % de probabilidad de intentar volver a uno de sus tres destinos más visitados y un 20 % de explorar, con preferencia por los lugares que aún no ha visitado. Cada llegada actualiza su historial. |

Los registros permiten comparar los destinos asignados y alcanzados, la duración de los viajes completados, la velocidad media de la flota incluidas las esperas y la frecuencia de colisiones e invasiones de carril registradas por los sensores. [Definiciones de las métricas](docs/referencia/datos-y-metricas.md#estados-y-métricas)

## Primera simulación en Town01

El ejemplo usa CARLA 0.9.15 y Python 3.7.9 de 64 bits en Windows. Prepara el entorno `carla-env` del proyecto y, en la consola que utilizarás para ejecutar los scripts, define `CARLA_PYTHONAPI` con la ruta a `PythonAPI\carla`, la carpeta del simulador que contiene `agents`. [Preparar el entorno](docs/guias/manual.md#preparar-el-entorno)

Abre otra ventana de PowerShell en la carpeta que contiene `CarlaUE4.exe` e inicia el servidor local.

```powershell
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```

Cuando el servidor haya cargado el mundo, vuelve a la consola del proyecto. Desde la raíz de TrafficIA, carga Town01 y ejecuta un vehículo con el selector histórico durante el tiempo que indiques. El ejemplo fija una duración de dos minutos simulados.

```powershell
.\carla-env\Scripts\python.exe .\scripts\maps\load_map.py --town Town01
.\carla-env\Scripts\python.exe .\scripts\simulation\run_trips.py --scenario history_80_20 --seconds 120
```

Al terminar, busca **Salida guardada en** en la consola y abre la carpeta indicada dentro de `data/output/`. En `trips_log.csv`, cada fila corresponde a un intento. El estado `completed` indica una llegada y `aborted` identifica un viaje aún activo al final de la simulación. Consulta `vehicle_history.csv` para ver las visitas y `run_config.json` para comprobar el mapa, la semilla y los parámetros efectivos. [Cómo seguir un viaje en los registros](docs/referencia/datos-y-metricas.md#seguir-un-viaje)

## Guías y referencia

| Tarea | Recurso |
|---|---|
| Inspeccionar puntos del mapa, iniciar campañas, ejecutar pruebas o generar gráficas | [Manual de PowerShell](docs/guias/manual.md) |
| Entender cómo se selecciona un destino y cuándo se acepta una llegada | [Arquitectura del simulador](docs/referencia/arquitectura.md) |
| Elegir la flota, el catálogo y el historial de una simulación | [Configuraciones](config/README.md) y [datos de entrada y salida](data/README.md) |
| Localizar la implementación, los comandos y las pruebas | [Código fuente](src/), [scripts](scripts/) y [pruebas](tests/) |
| Explorar las guías y la evolución del simulador | [Índice de documentación](docs/README.md) |

[Licencia del proyecto](LICENSE)
