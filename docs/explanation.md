# TrafficIA: guía breve de configuraciones y datos

Guía para entender los archivos antes de grabar los videos. Describe la organización actual y utiliza una corrida real de **20 vehículos con historial, R1**, como ejemplo. La explicación de `scripts`, `src` y `tests` queda para después.

**Cómo seguir la guía:** los campos se presentan en el orden en que aparecen en cada JSON o encabezado CSV. Los números indican la posición del campo o columna, no el número de línea. Los archivos que comparten estructura se explican una sola vez; las diferencias se indican junto a la tabla.

## 1. Qué contiene cada carpeta

| Carpeta | Para qué sirve |
|---|---|
| `config/` | Define cómo preparar y ejecutar el escenario: vehículos, tiempos, selección y ambiente. |
| `data/input/` | Aporta los destinos y las visitas iniciales que lee el generador. |
| `data/output/` | Conserva lo que ocurrió en cada ejecución y los análisis posteriores. |
| `docs/` | Explica el proyecto, sus decisiones, resultados y forma de uso. |

**JSON:** conjunto de campos con valores; por ejemplo, `"vehicle_count": 20`. **CSV:** tabla; cada fila representa un destino, una visita, un intento u otra observación, según el archivo. `true` significa activado, `false` desactivado y `null` ausencia de un valor o límite.

Los JSON de `config/` indican las rutas actuales de los catálogos, historiales y configuraciones. Las rutas relativas parten de la raíz de TrafficIA. Los registros históricos de `data/output/` conservan sus rutas originales; el programa mantiene la compatibilidad para resolverlas. Los manifiestos de preparación y las huellas actuales de `relocation-manifest.json` corresponden a los archivos actualizados; este último conserva también las huellas anteriores en `original_sha256` y `original_size_bytes`.

## 2. `config`: qué define cada JSON

### Archivos y diferencias principales

| Carpeta y archivo dentro de `config/` | Contenido y uso |
|---|---|
| `trips/single_vehicle_trip.json` | Prueba de **1 vehículo**, historial 80/20, semilla 42 y 600 s. Límite individual de viaje: 300 s. |
| `trips/single_vehicle_trip_cyclic.json` | La misma prueba, pero repite una lista fija de destinos. Sirve para revisar recorridos. |
| `trips/multi_vehicle_trip.json` | Prueba de **3 vehículos**, historial 80/20, semilla 42 y 600 s; sin límite individual de viaje. |
| `experiments/scaling_pilots/town01_05.json` | Piloto de **5 vehículos**, semilla 42 y 600 s. |
| `experiments/scaling_pilots/town01_10.json` | Piloto de **10 vehículos**, con las mismas condiciones generales. |
| `experiments/scaling_pilots/town01_20.json` | Piloto de **20 vehículos**, con las mismas condiciones generales. |
| `experiments/scaling_pilots/preparation_manifest.json` | Constancia de cómo se prepararon esos tres grupos. |
| `experiments/demand_20_100/town01_020.json` | Configuración base de **20 vehículos**, semilla 210 y 1800 s. |
| `experiments/demand_20_100/town01_100.json` | Configuración base de **100 vehículos**; amplía posiciones e historial. |
| `experiments/demand_20_100/weather.json` | Ambiente conservado para la comparación de 20 y 100. |
| `experiments/demand_20_100/preparation_manifest.json` | Constancia de la preparación de 20/100 y huellas de sus entradas. |
| `examples/scenario_basic.json` y `examples/scenario_low_demand.json` | Referencias iniciales para Town03: 20 vehículos, semilla 42 y 90 s. |
| `examples/scenario_high_demand.json` | Referencia inicial para Town03: 70 vehículos, semilla 42 y 120 s. |
| `examples/traffic_manager.json` | Parámetros de referencia de Traffic Manager para la etapa inicial. |

Los archivos de `examples` son antecedentes; no son las configuraciones de la evaluación principal de Town01. [Abrir configuraciones](C:/CARLA/TrafficIA/config/).

### Campos compartidos: leer primero `town01_020.json`

[Abrir el JSON de 20 vehículos](C:/CARLA/TrafficIA/config/experiments/demand_20_100/town01_020.json). Este es su orden exacto, también utilizado por el JSON de 100, los pilotos y `multi_vehicle_trip.json`. En los dos JSON `single_vehicle_trip*` se omiten `vehicle_count` e `initial_spawn_point_indices`; los demás conservan su orden relativo. Los valores pueden cambiar entre archivos.

| N.º | Campo | Qué significa en este archivo |
|---:|---|---|
| 1 | `town` | Mapa: `Town01`. |
| 2 | `seed` | Inicialización del azar: `210`. |
| 3 | `duration_seconds` | Duración base: `1800` segundos **simulados**. |
| 4 | `fixed_delta_seconds` | Avance del mundo por paso: `0.05` s. |
| 5 | `no_rendering_mode` | `false`: se permite dibujar el entorno. No significa que se estén grabando imágenes. |
| 6 | `initial_spawn_point_index` | Punto de aparición del primer vehículo: índice `133`. |
| 7 | `initial_spawn_fallback_enabled` | `false`: no sustituir automáticamente la posición inicial por otra alternativa. |
| 8 | `vehicle_count` | Cantidad simultánea: `20`. |
| 9 | `initial_spawn_point_indices` | Lista ordenada de posiciones iniciales de los 20 vehículos. |
| 10 | `destinations_config` | Ruta del catálogo: `data/input/catalogs/Town01/destinations_config.csv`. |
| 11 | `output_root` | Carpeta donde crear la salida: `data/output`. |
| 12 | `destination_selection_mode` | Selector base: `history_80_20`. La ejecución puede elegir `random_baseline`. |
| 13 | `destination_cycle_order` | Lista utilizada solo con el selector `cyclic`; no fija el orden del histórico. |
| 14 | `vehicle_history_config` | Historial inicial de 20: `data/input/histories/Town01/scaling_pilots/vehicle_history_20.csv`. |
| 15 | `routine_destination_count` | Hasta `3` destinos más visitados forman la rutina. |
| 16 | `required_destination_categories` | Categorías que debe contener el catálogo: residencial, trabajo/educación y servicios/ocio. |
| 17 | `routine_probability` | Probabilidad de rutina: `0.8`; no es una cuota exacta de decisiones. |
| 18 | `exploration_probability` | Probabilidad de exploración: `0.2`; no es un porcentaje de categorías. |
| 19 | `arrival_threshold_m` | Radio de cercanía al destino: `4 m`; se combina con otras condiciones de llegada. |
| 20 | `destination_dwell_time_seconds` | Espera después de llegar: `5 s`. |
| 21 | `max_trip_time_seconds` | `null`: no hay un límite individual de duración del viaje. |
| 22 | `blocked_speed_threshold_mps` | Umbral de baja velocidad para detectar bloqueo: `0.2 m/s`. |
| 23 | `blocked_time_threshold_seconds` | Tiempo continuado bajo ese umbral para declarar bloqueo: `60 s`. |
| 24 | `trajectory_sampling_interval_seconds` | Intervalo solicitado entre muestras de trayectoria: `0.5 s`. |
| 25 | `route_sampling_resolution_m` | Separación de referencia del muestreo de planificación: `2 m`. |
| 26 | `route_origin_validation_tolerance_m` | Tolerancia al validar el comienzo de la ruta: `5 m`. |
| 27 | `initial_spawn_validation_tolerance_m` | Tolerancia al comprobar la posición inicial: `3 m`. |
| 28 | `target_speed_kmh` | Velocidad objetivo: `20 km/h`; no es la velocidad que siempre alcanza el vehículo. |
| 29 | `vehicle_blueprint_filter` | Filtro de modelos candidatos: `vehicle.*`. |

**Configuración base y ejecución:** los JSON de 20/100 indican 1800 s, pero las campañas principales utilizaron 3600 mediante un ajuste al ejecutar. También se cambia el selector para comparar ambos modelos. Lo que realmente se utilizó queda en `data/output/.../run_config.json`.

### `weather.json`: ambiente de la comparación

[Abrir el ambiente](C:/CARLA/TrafficIA/config/experiments/demand_20_100/weather.json).

| N.º | Campo | Valor | Significado breve |
|---:|---|---:|---|
| 1 | `cloudiness` | 60 | Nubosidad. |
| 2 | `dust_storm` | 0 | Tormenta de polvo desactivada. |
| 3 | `fog_density` | 5 | Concentración de niebla. |
| 4 | `fog_distance` | 0.75 m | Distancia desde la que comienza la niebla. |
| 5 | `fog_falloff` | ≈0.1 | Distribución vertical de la niebla. |
| 6 | `mie_scattering_scale` | ≈0.03 | Dispersión de luz por partículas grandes. |
| 7 | `precipitation` | 40 | Intensidad visual de lluvia. |
| 8 | `precipitation_deposits` | 40 | Presencia de charcos. |
| 9 | `rayleigh_scattering_scale` | ≈0.0331 | Dispersión de luz por partículas pequeñas. |
| 10 | `scattering_intensity` | 1 | Contribución de luz a la niebla. |
| 11 | `sun_altitude_angle` | 20° | Elevación del sol. |
| 12 | `sun_azimuth_angle` | 275° | Dirección del sol. |
| 13 | `wetness` | 80 | Apariencia mojada de las superficies. |
| 14 | `wind_intensity` | 30 | Intensidad del viento. |

Nubosidad, lluvia, charcos, humedad visual, viento, densidad de niebla y polvo usan una escala de 0 a 100. `precipitation = 40` no significa 40 % de probabilidad de lluvia ni 40 mm/h. Estos ajustes ambientales no modifican por sí solos la física o la adherencia del vehículo. [Referencia oficial de CARLA 0.9.15](https://carla.readthedocs.io/en/0.9.15/python_api/#carla.WeatherParameters).

La campaña aplica este ambiente. Una ejecución individual conserva el clima del servidor salvo que se aplique expresamente; tener el archivo guardado no cambia el mundo automáticamente.

### Los dos `preparation_manifest.json`

Son comprobantes de preparación, no registros de viajes. Tienen estructuras distintas, por eso se muestran por separado.

**[Pilotos de 5, 10 y 20](C:/CARLA/TrafficIA/config/experiments/scaling_pilots/preparation_manifest.json):**

| N.º | Campo | Qué conserva |
|---:|---|---|
| 1 | `map` | Mapa utilizado. |
| 2 | `seed` | Semilla de preparación: 42. |
| 3 | `counts` | Cantidades: 5, 10 y 20. |
| 4 | `selection` | Cómo se eligieron las posiciones iniciales. |
| 5 | `history` | Cómo se prepararon las visitas. |
| 6 | `base_config_sha256` | Huella de la configuración base. |
| 7 | `destinations_sha256` | Huella del catálogo. |
| 8 | `original_history_sha256` | Huella del historial original. |
| 9 | `xodr_sha256` | Huella de la geometría vial del mapa. |
| 10 | `ordered_spawns` | Lista ordenada de las 20 posiciones. |
| 11 | `fleets` | Configuración, historial y comprobantes de cada grupo. |

Dentro de cada elemento de `ordered_spawns`, el orden es: `spawn_index` (índice), `destination_id` (destino), `x`, `y`, `z` (posición), `yaw_deg` (orientación), `road_id` (vía), `lane_id` (carril), `lane_width_m` (ancho).

Dentro de cada elemento de `fleets`: `vehicles` (cantidad), `config` (JSON), `history` (CSV), `history_rows` (filas), `min_spawn_center_distance_m` (separación mínima), `config_sha256` (huella del JSON), `history_sha256` (huella del CSV).

**[Comparación de 20 y 100](C:/CARLA/TrafficIA/config/experiments/demand_20_100/preparation_manifest.json):**

| N.º | Campo | Qué conserva |
|---:|---|---|
| 1 | `map` | Mapa utilizado. |
| 2 | `configurations` | Rutas de los JSON de 20 y 100. |
| 3 | `counts` | Cantidades: 20 y 100. |
| 4 | `xodr_sha256` | Huella de la geometría vial. |
| 5 | `min_center_distance_m` | Separación mínima entre centros de posiciones iniciales; no capacidad vial. |
| 6 | `ordered_spawns` | Lista ordenada de las 100 posiciones. |
| 7 | `bootstrap_seed` | Semilla de preparación: 42. |
| 8 | `run_seed_default` | Semilla prevista para ejecutar: 210. |
| 9 | `initial_visits_per_vehicle` | 30 visitas iniciales por vehículo. |
| 10 | `history_rows_100` | 3000 filas del historial de cien. |
| 11 | `prefix_20_preserved` | El grupo de 100 conserva el prefijo de 20. |
| 12 | `selection` | Cómo se ampliaron las posiciones iniciales. |
| 13 | `input_sha256` | Rutas de entradas y sus huellas de integridad. |

Dentro de cada elemento de `ordered_spawns`: `index` (índice), `x`, `y`, `z` (posición), `yaw` (orientación), `road_id` (vía), `lane_id` (carril).

### Campos propios de `examples`

Los tres `scenario_*.json` siguen este orden:

| N.º | Campo | Significado |
|---:|---|---|
| 1 | `scenario_name` | Nombre del caso. |
| 2 | `town` | Mapa. |
| 3 | `vehicles` | Cantidad de vehículos. |
| 4 | `duration_seconds` | Duración simulada. |
| 5 | `seed` | Inicialización del azar. |
| 6 | `synchronous_mode` | Activa el avance coordinado. |
| 7 | `fixed_delta_seconds` | Segundos simulados por paso. |
| 8 | `no_rendering_mode` | Indica si se desactiva el dibujo del entorno. |

En `traffic_manager.json`:

| N.º | Campo | Significado |
|---:|---|---|
| 1 | `port` | Puerto 8000. |
| 2 | `random_seed` | Semilla. |
| 3 | `synchronous_mode` | Sincronización. |
| 4 | `global_distance_to_leading_vehicle` | Distancia de seguimiento. |
| 5 | `vehicle_percentage_speed_difference` | Reducción respecto al límite de velocidad. |
| 6 | `auto_lane_change` | Cambios automáticos de carril. |
| 7 | `ignore_lights_percentage` | Porcentaje de ignorar semáforos. |
| 8 | `ignore_signs_percentage` | Porcentaje de ignorar señales. |
| 9 | `ignore_vehicles_percentage` | Porcentaje de ignorar vehículos. |
| 10 | `ignore_walkers_percentage` | Porcentaje de ignorar peatones. |
| 11 | `update_vehicle_lights` | Actualización de luces. |

**Traffic Manager no conduce la comparación principal.**

## 3. `data/input`: qué representa cada fila

### Catálogos: una fila = un destino

[catalogs/Town01/destinations_config.csv](C:/CARLA/TrafficIA/data/input/catalogs/Town01/destinations_config.csv) contiene **42 destinos**. [catalogs/Town03/destinations_config.csv](C:/CARLA/TrafficIA/data/input/catalogs/Town03/destinations_config.csv) conserva cinco destinos provisionales de una etapa anterior.

Orden de las columnas de **Town01**:

| N.º | Columna | Significado |
|---:|---|---|
| 1 | `destination_id` | Identificador del lugar, por ejemplo `T01_006`. |
| 2 | `destination_name` | Nombre legible: `Casa 006`. |
| 3 | `map` | Mapa al que pertenece. |
| 4 | `category` | `residential`, `work_education` o `services_leisure` en Town01. |
| 5 | `enabled` | Indica si el lugar está habilitado. |
| 6 | `reference_type` | Cómo se ubica: punto de aparición (`spawn_point`) o coordenadas. |
| 7 | `spawn_point_index` | Índice del punto de CARLA utilizado como referencia. No es el identificador de un vehículo. |
| 8 | `x` | Coordenada X en metros, cuando se especifica directamente. |
| 9 | `y` | Coordenada Y en metros. |
| 10 | `z` | Altura en metros. |
| 11 | `road_id` | Referencia de vía, cuando se indica. |
| 12 | `lane_id` | Referencia de carril, cuando se indica. |
| 13 | `description` | Nota descriptiva del lugar. |

En **Town03**, después de `category` aparecen dos columnas adicionales: **5. `frequency_class`** (clase fija) y **6. `weight`** (peso fijo). Después sigue `enabled`, ahora en la posición 7, y el resto mantiene el orden anterior hasta `description`, en la 15.

En Town01 las coordenadas y los campos de vía/carril están vacíos porque los lugares se resuelven mediante su `spawn_point_index`. El catálogo activo no asigna un peso fijo ni una etiqueta de rutina a cada lugar: la rutina depende del historial individual.

### Historiales: una fila = una visita sintética

| Archivo dentro de `data/input/histories/Town01/` | Contenido |
|---|---|
| `bootstrap/vehicle_history_dummy.csv` | 150 visitas: 5 vehículos × 30. Las pruebas de uno o tres toman los vehículos correspondientes. |
| `scaling_pilots/vehicle_history_05.csv` | 150 visitas: 5 × 30. |
| `scaling_pilots/vehicle_history_10.csv` | 300 visitas: 10 × 30. |
| `scaling_pilots/vehicle_history_20.csv` | 600 visitas: 20 × 30. También se utiliza en la comparación principal de 20. |
| `demand_20_100/vehicle_history_100.csv` | 3000 visitas: 100 × 30. |

Todos tienen las mismas cuatro columnas, en este orden:

| N.º | Columna | Significado |
|---:|---|---|
| 1 | `vehicle_id` | Vehículo al que pertenece la visita. |
| 2 | `sequence` | Orden de la visita dentro de ese historial. |
| 3 | `destination_id` | Lugar visitado; coincide con un identificador del catálogo. |
| 4 | `source` | `dummy`: visita creada para inicializar el experimento. |

Ejemplo: `vehicle_001,1,T01_006,dummy` significa que la primera visita sintética de ese vehículo fue a Casa 006. No es un viaje físicamente ejecutado en la corrida. **30 visitas pueden repetir lugares.** El selector uniforme no consulta estas visitas para decidir.

[Abrir el historial inicial de 20](C:/CARLA/TrafficIA/data/input/histories/Town01/scaling_pilots/vehicle_history_20.csv).

### `data/input/examples`: datos de las primeras etapas

Las columnas se enumeran de izquierda a derecha, como en sus encabezados.

| Archivo | Qué es una fila y qué indican sus columnas |
|---|---|
| `zones_config.csv` | Una zona: 1. `zone_id` identificador; 2. `zone_name` nombre; 3. `category` tipo; 4. `spawn_indices` índices separados por `;`; 5. `description` explicación. Hay 6 zonas. |
| `destinations_config.csv` | Un destino de ejemplo: 1. `destination_id` identificador; 2. `zone_id` zona; 3. `destination_name` nombre; 4. `category` tipo; 5. `frequency_class` clase fija; 6. `weight` peso; 7. `description` explicación. Hay 10. |
| `demand_profiles.csv` | Un perfil: 1. `profile_id` identificador; 2. `description` explicación; 3. `vehicles` cantidad; 4. `routine_probability` probabilidad de rutina; 5. `exploration_probability` probabilidad de exploración; 6. `spawn_interval_seconds` intervalo propuesto de aparición. Hay 3 perfiles. |

Estos archivos no son las entradas utilizadas por los JSON principales de Town01. [Abrir ejemplos](C:/CARLA/TrafficIA/data/input/examples/).

## 4. `data/output`: seguir una ejecución de 20 vehículos

### Carpeta elegida y archivos generados

[Abrir la corrida histórica R1 de 20 vehículos](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260922T043508477380Z/).

Su nombre identifica mapa, selector, semilla y fecha UTC. La cantidad se confirma en `run_config.json`; no aparece en el nombre de esta carpeta. Es una corrida de **3600 s**, no la futura demostración de 180 s. Los archivos de observación, imágenes y diagnóstico dependen del modo de ejecución.

| Archivo | Qué guarda / qué representa un registro |
|---|---|
| `run_config.json` | Condiciones efectivas. Entre sus campos, en orden: `scenario` (selector), `environment` (ambiente), `vehicle_count` (cantidad), `vehicles` (vehículos), `simulation_config` (configuración utilizada) y `destinations` (destinos). |
| `trips_log.csv` | **Una fila por intento cerrado**, completado o incompleto. Es el archivo principal para explicar el resultado de cada elección. |
| `vehicle_history.csv` | Una fila por visita: las iniciales y las añadidas por llegadas. |
| `arrival_log.csv` | Una fila por llegada aceptada, con posición, velocidad, carril y errores de alineación. |
| `events_log.csv` | Una fila por aviso recibido de colisión o invasión de carril. |
| `trajectory_log.csv` | Una muestra de movimiento durante un viaje activo; intervalo solicitado de 0.5 s. |
| `observation_log.csv` | Una observación por vehículo y paso, incluyendo viajes y esperas; intervalo de 0.05 s en esta campaña. |
| `metrics_summary.csv` | Una fila de resumen de toda la corrida: intentos, llegadas, distancias, velocidades y avisos. |
| `route_log.csv` | Un punto de la ruta planificada: orden, posición, orientación, vía y carril. |
| `control_log.csv` | Estado y controles de conducción: dirección, aceleración, frenado y referencias de seguimiento. Es diagnóstico detallado. |
| `visual_review_config.json` | Configuración de observación, captura y huellas de fuentes/entradas. |
| `capture_summary.json` | Estado final de captura y cantidad de observaciones por vehículo. |
| `image_index.csv` | Referencias de imágenes y su relación con pasos; aquí solo tiene encabezados porque las cámaras estaban desactivadas. |

En este ejemplo `events_log.csv` también tiene solo encabezados: hubo **cero avisos de ambos tipos**. La razón es distinta a la de `image_index.csv`. `capture_summary.json` registra **72 000 observaciones por vehículo**, 1 440 000 entre los veinte; no todos los CSV guardan una fila por paso.

### `trips_log.csv`: significado de todas sus columnas

[Abrir el registro de viajes](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260922T043508477380Z/trips_log.csv).

| N.º | Columna | Qué guarda |
|---:|---|---|
| 1 | `run_id` | Ejecución a la que pertenece. |
| 2 | `vehicle_id` | Vehículo lógico, por ejemplo `vehicle_013`. |
| 3 | `trip_id` | Número del intento de ese vehículo, por ejemplo `trip_001`. |
| 4 | `seed` | Semilla de la ejecución. |
| 5 | `origin_id` | Identificador del origen. Puede ser una posición intermedia. |
| 6 | `origin_name` | Nombre del origen. |
| 7 | `origin_x` | Coordenada X de la salida, en metros. |
| 8 | `origin_y` | Coordenada Y de la salida, en metros. |
| 9 | `origin_z` | Altura de la salida, en metros. |
| 10 | `destination_id` | Identificador del destino elegido. |
| 11 | `destination_name` | Nombre del destino elegido. |
| 12 | `destination_category` | Categoría del destino elegido. |
| 13 | `frequency_class` | Campo conservado por compatibilidad; en estas corridas repite `selection_class`. |
| 14 | `selection_class` | `random_baseline`, `routine` o `exploration`: cómo se eligió. |
| 15 | `history_visit_count_before` | Visitas previas al destino elegido en ese historial. |
| 16 | `selection_candidate_count` | Número de candidatos de la selección realizada; en el histórico, de la rama utilizada. |
| 17 | `departure_sim_time_s` | Reloj del simulador al iniciar. |
| 18 | `arrival_sim_time_s` | Reloj al llegar; vacío si no se completó. |
| 19 | `travel_time_s` | Tiempo simulado desde la salida hasta el cierre, incluyendo detenciones del intento. |
| 20 | `distance_traveled_m` | Distancia recorrida durante el intento, en metros. |
| 21 | `average_speed_mps` | Distancia dividida entre duración, en m/s. |
| 22 | `average_speed_kmh` | La misma velocidad media, en km/h. |
| 23 | `collision_count` | Avisos de colisión asociados al intento; no necesariamente accidentes independientes. |
| 24 | `lane_invasion_count` | Avisos de invasión de carril asociados al intento. |
| 25 | `status` | Resultado del intento. |
| 26 | `end_sim_time_s` | Reloj al cerrar el intento, cualquiera que sea su resultado. |
| 27 | `stopped_time_s` | Tiempo del intento por debajo del umbral de baja velocidad de 0.2 m/s; no exige inmovilidad exacta. |
| 28 | `max_trip_time_seconds` | Límite individual; vacío en esta corrida porque estaba deshabilitado. |
| 29 | `termination_reason` | Motivo concreto del cierre, por ejemplo `stopped_aligned_arrival`. |

`status`: **`completed`** = llegó; **`blocked`** = alcanzó el umbral de bloqueo; **`route_failed`** = ruta rechazada; **`aborted`** = seguía activo al terminar la ejecución; **`timeout`** = agotó un límite individual habilitado. En la corrida elegida hay **397 `completed` y 20 `aborted`**.

Los relojes no tienen que comenzar en cero. Para un viaje completado, la diferencia entre llegada y salida da su duración. La clave para seguir el mismo intento es **`run_id` + `vehicle_id` + `trip_id`**; `trip_001` se repite entre vehículos.

### Ejemplo real para enseñar en pantalla

Filtra `vehicle_id = vehicle_013` y `trip_id = trip_001`:

| Dato | Valor redondeado |
|---|---|
| Recorrido | Hospital (`T01_015`) → Oficina 044 (`T01_044`) |
| Selección | Rutina; 7 visitas previas al destino y 3 candidatos |
| Resultado | `completed` |
| Tiempo y distancia | 57.80 s y 221.41 m |
| Velocidad media | 13.79 km/h |

En [vehicle_history.csv](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260922T043508477380Z/vehicle_history.csv), ese mismo intento añadió la **visita 31** de `vehicle_013` a `T01_044`.

Este historial de salida conserva los campos de entrada, pero **antepone `run_id`**. Sus columnas aparecen así:

| N.º | Columna | Qué guarda |
|---:|---|---|
| 1 | `run_id` | Ejecución a la que pertenece el historial. |
| 2 | `vehicle_id` | Vehículo de la visita. |
| 3 | `sequence` | Orden de la visita en su historial. |
| 4 | `destination_id` | Lugar visitado. |
| 5 | `source` | `dummy` para visitas iniciales; `simulation` para las nuevas. |
| 6 | `trip_id` | Viaje que produjo la visita; vacío en las iniciales. |
| 7 | `completed_sim_time_s` | Momento simulado de llegada; vacío en las iniciales. |

Aquí hay **600 iniciales + 397 nuevas = 997 filas**.

### Cómo leer los otros registros sin abrirlos todos

En estas tablas compactas solo se agrupan **columnas consecutivas**, conservando su orden de izquierda a derecha.

**`arrival_log.csv`: una llegada aceptada.**

| Posición | Columnas, en orden | Qué guardan |
|---:|---|---|
| 1–3 | `run_id`, `vehicle_id`, `trip_id` | Ejecución, vehículo e intento. |
| 4 | `destination_id` | Lugar alcanzado. |
| 5–6 | `frame`, `simulation_time_s` | Paso y momento simulado de llegada. |
| 7–9 | `x`, `y`, `z` | Posición, en metros. |
| 10 | `speed_mps` | Velocidad al aceptar la llegada. |
| 11–12 | `heading_error_deg`, `lateral_error_m` | Error de orientación y desplazamiento lateral. |
| 13 | `distance_to_destination_m` | Distancia al destino. |
| 14–15 | `road_id`, `lane_id` | Vía y carril. |
| 16 | `route_remaining_m` | Distancia restante de la ruta. |

**`events_log.csv`: un aviso de sensor.**

| Posición | Columnas, en orden | Qué guardan |
|---:|---|---|
| 1–3 | `run_id`, `vehicle_id`, `trip_id` | Ejecución, vehículo e intento; durante una espera puede faltar el intento. |
| 4–5 | `frame`, `simulation_time_s` | Paso y momento del aviso. |
| 6 | `event_type` | Tipo de aviso. |
| 7 | `other_actor_id` | Otro actor involucrado, cuando corresponde. |
| 8–10 | `x`, `y`, `z` | Posición. |
| 11 | `details` | Datos adicionales del aviso. |

**`trajectory_log.csv`: una muestra durante un viaje activo.**

| Posición | Columnas, en orden | Qué guardan |
|---:|---|---|
| 1–3 | `run_id`, `vehicle_id`, `trip_id` | Ejecución, vehículo e intento. |
| 4–5 | `frame`, `simulation_time_s` | Paso y momento de la muestra. |
| 6–8 | `x`, `y`, `z` | Posición. |
| 9–10 | `speed_mps`, `speed_kmh` | Velocidad en m/s y km/h. |
| 11 | `acceleration_mps2` | Aceleración, en m/s². |
| 12–13 | `road_id`, `lane_id` | Vía y carril. |
| 14 | `distance_traveled_m` | Distancia acumulada del intento. |

**`observation_log.csv`: una observación por vehículo y paso, también durante las esperas.** La carpeta identifica la ejecución.

| Posición | Columnas, en orden | Qué guardan |
|---:|---|---|
| 1 | `vehicle_id` | Vehículo observado. |
| 2–3 | `frame`, `simulation_time_s` | Paso y momento simulado. |
| 4–5 | `phase_before`, `phase_after` | Fase antes y después: viaje (`travel`) o espera (`dwell`). |
| 6–7 | `trip_before`, `trip_after` | Intento antes y después. |
| 8 | `context_trip_id` | Intento utilizado como contexto de esa observación. |
| 9 | `destination_id` | Destino asociado. |
| 10–12 | `x`, `y`, `z` | Posición. |
| 13 | `yaw_deg` | Orientación, en grados. |
| 14 | `speed_mps` | Velocidad, en m/s. |
| 15 | `low_speed` | Indica si está bajo el umbral de baja velocidad. |
| 16–17 | `traffic_light_id`, `traffic_light_state` | Identificador y estado del semáforo asociado por CARLA. |
| 18 | `at_traffic_light` | Indica si CARLA sitúa al vehículo en un semáforo. |
| 19–20 | `agent_traffic_light_id`, `agent_traffic_light_state` | Identificador y estado del semáforo considerado por el agente. |
| 21 | `nearby_vehicles_json` | Información de vehículos cercanos, guardada como JSON dentro de la celda. |

### Resumen de corrida y resumen de campaña

**`metrics_summary.csv`: una fila de resumen de la corrida.**

| N.º | Columna | Qué guarda |
|---:|---|---|
| 1 | `run_id` | Ejecución resumida. |
| 2 | `vehicle_count` | Cantidad de vehículos. |
| 3 | `trips_started` | Intentos iniciados. |
| 4 | `trips_completed` | Intentos que llegaron. |
| 5 | `trips_incomplete` | Intentos que terminaron sin llegada. |
| 6 | `simulation_duration_s` | Duración simulada de la corrida. |
| 7 | `total_distance_traveled_m` | Distancia acumulada en intervalos con viaje activo. |
| 8 | `aggregate_average_speed_mps` | Velocidad agregada de esos intervalos, en m/s. |
| 9 | `aggregate_average_speed_kmh` | La misma velocidad, en km/h. |
| 10 | `total_collisions` | Avisos de colisión de toda la ejecución. |
| 11 | `total_lane_invasions` | Avisos de invasión de carril de toda la ejecución. |
| 12 | `observed_destination_distribution` | Distribución de **llegadas**, no elecciones. |
| 13 | `total_observed_distance_m` | Distancia observada durante la presencia completa del grupo. |
| 14 | `total_vehicle_time_s` | Tiempo acumulado de presencia: aquí, 20 × 3600 ≈ 72 000 vehículo-segundos; no es un conteo de observaciones. |

La [carpeta de campaña R1](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/) reúne las cuatro combinaciones de vehículos y selector:

| Archivo o grupo | Contenido |
|---|---|
| `campaign.json` | Casos ejecutados, condiciones, estados y rutas hacia las corridas. |
| `metrics/summary.csv` | Una fila por corrida, con las métricas derivadas utilizadas para comparar. |
| `metrics/destinations.csv` | Conteos y proporciones por destino/categoría; separa asignaciones y llegadas. |
| `metrics/analysis.json`, `metrics/report.md` | Análisis detallado e informe legible. |
| `*_preflight.json`, `*_cleanup.json`, `final_server_state.json` | Estado del servidor antes y después de ejecutar. |
| `*_metrics.json`, `*_audit.json` | Métricas y comprobaciones de coherencia de cada caso. |
| `source_snapshot/`, `source_sha256.json`, `source_verification.json`, `*_output_sha256.json` | Copias de fuentes y huellas de integridad. |
| `*_console.txt` | Mensajes de ejecución o análisis. |

En [metrics/summary.csv](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/metrics/summary.csv), estos son los campos principales que conviene localizar, en el orden del encabezado. Se indican sus posiciones reales; se omiten otras columnas para mantener breve la guía.

| Posición | Columna | Qué consultar para el histórico de 20 |
|---:|---|---|
| 2 | `scenario` | Selector utilizado. |
| 4 | `vehicle_count` | Tamaño del grupo: 20. |
| 8 | `mean_completed_trip_s` | Duración media: **171.86 s**, solo de completados. |
| 10 | `mean_speed_kmh` | Velocidad media: **10.64 km/h**, incluyendo esperas. |
| 16 | `invasions_per_vehicle_km` | Tasa de avisos de invasión por vehículo-kilómetro. |
| 17 | `collisions_per_vehicle_km` | Tasa de avisos de colisión por vehículo-kilómetro. |

Para mostrar el 80/20, cuenta `selection_class` en los **417 intentos**: 327 de rutina y 90 de exploración; **327 ÷ 417 × 100 = 78.42 %**. No agregues las visitas iniciales ni filtres solo las llegadas para calcular esa proporción de decisiones.

## 5. `docs`: dónde consultar cada tema

| Archivos | Contenido |
|---|---|
| `README.md`, `repository-layout.md`, `relocation-manifest.json` | Índice, organización y comprobación de los archivos trasladados. |
| `project-graduation-context.md`, `rutas.md` | Alcance académico y lugares del catálogo. |
| `bitacora_simulacion.md`, `pilotos_escalamiento.md`, `seleccion_niveles_demanda.md`, `fundamento_demandas_town01.md` | Preparación, decisiones y antecedentes de las cantidades de vehículos. |
| `campana_demanda_20_100.md`, `campana_larga_veinte_vehiculos.md`, `repetibilidad_demandas_3600.md` | Campañas, resultados y comparación entre repeticiones. |
| `graficas_*.md`, `lectura_diagramas_y_guias.md` | Ubicación e interpretación de las figuras. |
| `control_e_incidentes.md`, `diagnostico_blocked.md`, `revision_visual_tres_vehiculos.md` | Revisión de conducción, avisos y bloqueos. |
| `demo_defensa.md` | Comandos y preparación de la demostración. |
| `archive/` | Propuestas y redacción de etapas anteriores. |

## 6. Orden para tus tres videos

| Video | Qué mostrar |
|---|---|
| Ejecución: 12 minutos previstos | Cuatro segmentos de 3 minutos: uniforme e histórico, con 20 y con 100. Los segundos simulados configurados no garantizan la misma duración real del video. |
| Explicación de archivos y después código | JSON de 20 → clima → catálogo → historial inicial → `run_config.json` → intento de `vehicle_013` → nueva visita → resumen. La parte de código se prepara después. |
| Respaldo del mapa sin vehículos | Lugares identificados en el catálogo y sus tres categorías. |

Para el video de archivos, basta explicar un viaje con sus registros relacionados. Este ejemplo procede de una campaña de la tesis; cuando muestres resultados de los videos nuevos, abre las carpetas de esas mismas grabaciones. [Guía de ejecución disponible](C:/CARLA/TrafficIA/docs/demo_defensa.md).
