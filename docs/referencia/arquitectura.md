# Cómo funciona un viaje

TrafficIA asigna destinos, controla el ciclo de viaje de cada vehículo y registra sus resultados. CARLA proporciona el mapa vial, la física, los sensores y los agentes de navegación. Una corrida usa el mismo controlador de conducción para todos los vehículos, con independencia de cómo elijan su destino.

## Del JSON al primer destino

1. El ejecutor de viajes aplica los argumentos de la línea de comandos al JSON. `TripSimulationConfig` valida la configuración resultante. El ejecutor de campañas usa la misma clase de configuración para fijar la flota, la semilla, la duración y el selector de cada caso. [Ejecutor de viajes](../../scripts/simulation/run_trips.py) y [ejecutor de campañas](../../scripts/campaigns/run_demand.py)
2. `TripSimulation` comprueba el mapa activo, resuelve las referencias viales del catálogo y carga los historiales que requiere el selector. Activa el modo síncrono y coloca los vehículos en los puntos configurados. Tras un paso común de sincronización, verifica la posición efectiva de cada vehículo y le asocia sensores de colisión e invasión de carril. [Coordinador de la simulación](../../src/simulation/trip_runner.py)
3. Cada vehículo dispone de un generador seudoaleatorio para los destinos y otro para los atributos del actor. La posición real del vehículo sirve de origen al primer plan de ruta y a las asignaciones posteriores.

Las configuraciones distribuidas fijan `initial_spawn_fallback_enabled` en `false`. Si un punto está ocupado, la corrida se detiene. Cuando este parámetro vale `true`, el ejecutor prueba primero el índice solicitado y luego los demás en orden ascendente. En `run_config.json`, `vehicles[].initial_spawn_point_index_requested` y `vehicles[].initial_spawn_point_index_used` identifican el origen previsto y el utilizado.

## Elección del destino

| Selector | Regla de elección |
|---|---|
| `random_baseline` | Ordena por identificador los destinos habilitados y sortea uno con probabilidad uniforme. Excluye el destino actual cuando está identificado. [Selección uniforme](../../src/demand/destinations.py) |
| `history_80_20` | Ordena los destinos visitados por frecuencia y, en caso de empate, por identificador. Las configuraciones de Town01 fijan el máximo de destinos habituales (`routine_destination_count`) en tres y la probabilidad de rutina (`routine_probability`) en 0,8. La rama de rutina pondera cada candidato por sus visitas. La exploración sortea primero entre los lugares sin visitas previas y, una vez agotados, entre los restantes fuera de la rutina. Si la rama elegida carece de candidatos, utiliza la otra. También excluye el destino actual cuando está identificado. [Historial individual](../../src/demand/vehicle_history.py) |

## Ruta, llegada y nuevo intento

`GlobalRoutePlanner` calcula la ruta desde la posición vial efectiva. TrafficIA verifica su origen y, cuando el destino queda detrás en el mismo tramo, busca un retorno que respete el sentido del carril. `BasicAgent` gobierna el vehículo a partir de ese plan. La adaptación de TrafficIA conserva el control de dirección durante el frenado y permite detectar un vehículo situado directamente enfrente. [Planificación de rutas](../../src/navigation/route_planner.py) y [agente de conducción](../../src/navigation/carla_agent.py)

El parámetro `fixed_delta_seconds` fija el paso de simulación para toda la flota. Para completar un viaje deben quedar como máximo 0,5 m del recorrido planificado. El vehículo debe estar dentro del radio configurado para el destino, en su carril o en la continuación validada, con velocidad de hasta 0,05 m/s, una desviación lateral máxima de 0,5 m y un error de orientación de hasta 10°. [Control de llegada](../../src/navigation/arrival.py)

Al confirmar la llegada, el simulador registra una visita para ese vehículo. Durante la espera lo mantiene en el mundo con el freno aplicado. Cada intento cerrado conserva el motivo de su terminación, tanto si llega como si agota el tiempo, se bloquea o el planificador rechaza la ruta. La siguiente asignación parte de la posición en la que se encuentra el vehículo. [Estados de cierre](datos-y-metricas.md#estados-y-métricas)

Durante un viaje activo, el simulador mide el tiempo transcurrido desde la salida o desde el último paso en que el vehículo superó `blocked_speed_threshold_mps`. Al alcanzar `blocked_time_threshold_seconds` emite un aviso. Con `terminate` cierra el intento y espera antes de reasignar destino. Con `keep_trip` conserva el viaje y registra un único aviso hasta que el vehículo supere de nuevo el umbral de velocidad.

## Registro y análisis

| Componente | Responsabilidad |
|---|---|
| [Registro por corrida](../../src/recording/run_logger.py) | Escribe viajes, trayectorias, visitas, eventos de los sensores y métricas agregadas. |
| [Observación por paso](../../src/recording/visual_review.py) | Registra la fase de cada vehículo antes y después de actualizar el viaje. Puede asociar imágenes RGB al mismo vehículo y fotograma de simulación. El ejecutor de campañas usa esta instrumentación con las cámaras desactivadas. |
| [Análisis de movilidad](../../src/analysis/mobility_analysis.py) | Calcula las distribuciones de destinos, los tiempos, la velocidad y las tasas de eventos a partir de los registros. Compara las condiciones de las corridas que usan distintos selectores. |
| [Análisis de incidentes](../../src/analysis/incident_analysis.py) y [análisis de flujo](../../src/analysis/traffic_flow_analysis.py) | El primero agrupa avisos de colisión por par de actores e intervalo temporal. El segundo calcula densidad, flujo y velocidad para cada tramo de carril y ventana temporal. |

Al terminar, el ejecutor cierra los registros, retira sus vehículos y sensores y restablece los ajustes del mundo. La campaña de demanda también restaura el clima y guarda el estado final del servidor.
