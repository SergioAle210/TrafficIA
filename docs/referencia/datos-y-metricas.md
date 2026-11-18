# Configuraciones, registros y métricas

## Antes de ejecutar

| Entrada | Qué define |
|---|---|
| [Configuraciones de viajes](../../config/trips/) | Mapa esperado, semilla, duración, paso de simulación, puntos de aparición, catálogo, historial y tolerancias de navegación. La configuración cíclica fija el orden de los destinos para comprobar las rutas. |
| [Configuraciones de demanda](../../config/experiments/demand_20_100/) | Tamaños de flota admitidos por la campaña y clima común. El manifiesto identifica la geometría de los puntos de aparición y las huellas del mapa OpenDRIVE y de las entradas. |
| [Catálogo de Town01](destinos-town01.md) | Relaciona el identificador y la categoría de cada lugar con una referencia vial que el simulador puede resolver sobre el mapa. |
| [Historiales iniciales](../../data/input/histories/Town01/) | Cada fila representa una visita con `vehicle_id`, `sequence`, `destination_id` y `source`. El selector histórico carga las visitas correspondientes a cada vehículo configurado. |

Las rutas relativas de las entradas se resuelven desde la raíz del proyecto o de la copia de la campaña que se está verificando. Si el archivo existe en esa ubicación, se usa tal cual. Para las entradas conocidas, el lector también reconoce rutas registradas por versiones anteriores. El manifiesto recoge la ubicación y la huella SHA-256 de las 25 entradas de referencia. [Resolución de rutas](../../src/project_paths.py) y [manifiesto de entradas](huellas-entradas.json)

## Después de ejecutar

| Archivo | Contenido y condiciones de escritura |
|---|---|
| `run_config.json` | Registra la configuración efectiva, la versión de CARLA, las condiciones del mundo, las semillas y los identificadores de los vehículos. |
| `trips_log.csv` | Contiene una fila por intento cerrado. Identifica origen, destino, rama de elección, visitas previas, duración, estado final y motivo de cierre. |
| `vehicle_history.csv` | Registra las visitas iniciales del vehículo, cuando se cargan, y las que se añaden al completar viajes. Estas últimas incluyen `trip_id` y `completed_sim_time_s`. |
| `trajectory_log.csv` | Muestra la posición, la velocidad y el carril durante el viaje activo, con el intervalo de muestreo definido en la configuración. |
| `events_log.csv` | Contiene una fila por aviso de colisión o invasión de carril. Un aviso recibido durante la espera puede tener `trip_id` vacío. |
| `blocked_warnings.csv` | Recoge el instante en que se alcanzó el umbral de detención, el viaje afectado y la política aplicada. |
| Resumen de la corrida (CSV) | Resume distancia, tiempo, viajes y eventos. Distingue las magnitudes de los viajes activos de las acumuladas durante toda la presencia de la flota. |
| `route_log.csv` y `control_log.csv` | Con los diagnósticos de navegación activos, registran el plan vial y las órdenes de control al emitirse. |
| `arrival_log.csv` | Con los diagnósticos de navegación activos, se crea al producirse la primera llegada y registra la posición, velocidad y alineación aceptadas. |
| `observation_log.csv` | El ejecutor instrumentado registra una fila por vehículo y fotograma, con `phase_before`, `phase_after` y el identificador del viaje asociado a la transición. |
| `visual_review_config.json`, `capture_summary.json` e `image_index.csv` | La ejecución instrumentada guarda la configuración y cobertura de la observación. Con cámaras activas, el índice relaciona cada imagen con su vehículo y fotograma. `image_capture_enabled` indica si se solicitó la captura. |

## Seguir un viaje

Abre la carpeta que imprimió el ejecutor. Si usaste una campaña, su manifiesto identifica los directorios de cada caso bajo `data/output/`. Cruza `trips_log.csv` y `vehicle_history.csv` por `run_id`, `vehicle_id` y `trip_id` para localizar la visita de un viaje completado. Si la corrida incluye `observation_log.csv`, filtra ese archivo por `vehicle_id` y busca el `trip_id` del intento en la columna `context_trip_id`.

Este ejemplo lee tus registros y muestra el destino y el estado de los primeros intentos. Si hay una llegada, también busca la visita correspondiente en el historial.

```powershell
$corrida = Read-Host 'Ruta de la carpeta de tu corrida'
$viajes = Import-Csv -LiteralPath (Join-Path $corrida 'trips_log.csv')
$viajes | Select-Object -First 5 vehicle_id, trip_id, destination_id, travel_time_s, status

$llegada = $viajes | Where-Object status -eq 'completed' | Select-Object -First 1
if ($llegada) {
    Import-Csv -LiteralPath (Join-Path $corrida 'vehicle_history.csv') |
        Where-Object {
            $_.run_id -eq $llegada.run_id -and
            $_.vehicle_id -eq $llegada.vehicle_id -and
            $_.trip_id -eq $llegada.trip_id
        } |
        Select-Object vehicle_id, trip_id, destination_id, sequence, source
}
```

## Estados y métricas

`completed` indica llegada confirmada. Si termina la simulación mientras el viaje sigue activo, se registra `aborted` con `termination_reason=simulation_end`. Los cierres por rechazo de la ruta, límite de tiempo individual y detención prolongada con política `terminate` se registran como `route_failed`, `timeout` y `blocked`, respectivamente. En el registro de observación, la fase `dwell` abarca los pasos sin viaje activo, incluida la espera después de una llegada o un fallo.

| Métrica | Cálculo e interpretación |
|---|---|
| Distribución de destinos | Frecuencia por identificador o categoría. La distribución de asignaciones usa todos los intentos. La de llegadas usa los viajes con estado `completed`. |
| Tiempo medio de viaje | Media de `travel_time_s` para los viajes completados, incluidas sus detenciones. Se informa junto con el número de llegadas y la proporción de intentos incompletos. Sin llegadas, la media queda indefinida. |
| Velocidad media durante la presencia | En la versión 3 de las métricas se calcula como `3,6 × total_observed_distance_m / total_vehicle_time_s`, en km/h. Incluye la espera y pondera por el tiempo de presencia de cada vehículo. |
| Colisiones e invasiones de carril | Se cuentan por separado las notificaciones de cada tipo de sensor. Las tasas usan la distancia acumulada de la flota en vehículo-km o su tiempo de presencia en vehículo-horas. Una tasa queda indefinida si su denominador es cero. Un contacto prolongado puede generar varios avisos. |

En los registros con `metrics_semantics_version=2`, el análisis limita la distancia y el tiempo a los viajes activos y usa en las tasas únicamente los avisos asociados a ellos. Conserva por separado el número total de avisos observados. El informe identifica el alcance de estas medidas en `exposure.scope`. [Implementación de las métricas](../../src/analysis/mobility_analysis.py)

Para comparar selectores, el analizador agrupa corridas por mapa, semilla, flota y duración. Comprueba la configuración y la forma de medir la exposición antes de comparar sus métricas. En el análisis de incidentes, los avisos de colisión consecutivos de una misma pareja de actores se agrupan en episodios según su separación en tiempo simulado. [Agrupación de avisos de colisión](../../src/analysis/incident_analysis.py)

## Flujo y densidad por carril

El análisis espacial combina las observaciones por paso con la geometría OpenDRIVE del mapa. Divide los carriles de conducción seleccionados en tramos y el tiempo en ventanas. Para cada celda acumula el tiempo de presencia de los vehículos (`S`, en segundos) y la distancia longitudinal recorrida (`D`, en metros), con una longitud de tramo `L` en metros y una duración efectiva `T` en segundos.

| Magnitud | Cálculo | Unidad |
|---|---|---|
| Densidad | `1000 × S / (L × T)` | vehículos/km/carril |
| Flujo | `3600 × D / (L × T)` | vehículos/h/carril |
| Velocidad media espacial | `3,6 × D / S`, cuando hay presencia | km/h |

En una celda vacía, la densidad y el flujo valen cero y la velocidad queda sin definir. Para resumir las observaciones por bandas de densidad, el análisis suma el tiempo, la distancia y el área de las celdas con presencia. [Cálculo por tramo y ventana](../../src/analysis/traffic_flow_analysis.py)
