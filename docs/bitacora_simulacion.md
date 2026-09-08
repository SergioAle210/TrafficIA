# Bitácora de simulación y validación

Este archivo conserva el contexto técnico entre sesiones. En cada ajuste del
runner o del controlador, añadir fecha, síntoma, evidencia, causa confirmada o
hipótesis, archivos afectados, pruebas realizadas, rutas de resultados y
limitaciones pendientes. No reemplazar resultados antiguos ni presentar pruebas
unitarias como validación de física real.

## 2026-09-08: primeras pruebas de 600 segundos

Condiciones: CARLA 0.9.15, Town01, tres vehículos en `[133, 6, 101]`, semilla 42,
600 segundos simulados, `--simulation-speed 5 --no-rendering`, 20 km/h objetivo.
Se mantuvo el clima del servidor (precipitación 40, humedad 80, altitud solar 20).
Clima, 36 semáforos, modelos vehiculares, colores, spawns y semillas coincidieron.
Se desactivó el renderizado antes de las corridas para mantenerlo desactivado
también entre ellas, evitando reactivar innecesariamente la ruta D3D11 que había
fallado con `DXGI_ERROR_INVALID_CALL`.

| Medida | Baseline original | Histórico original |
|---|---:|---:|
| Tiempo real de ejecución, incluida inicialización | 122.7 s | 122.7 s |
| Viajes iniciados / completados / aborted | 14 / 11 / 3 | 14 / 11 / 3 |
| Distancia total | 5761.33 m | 5706.85 m |
| Velocidad media agregada | 11.89 km/h | 11.77 km/h |
| Registros de colisión | 857 | 1 |
| Invasiones en events_log / metrics_summary | 13 / 13 | 27 / 23 |
| Visitas finales por vehículo | 5, 4, 2 | 34, 34, 33 |

Resultados originales, preservados sin correcciones retroactivas:

- `data/output/town01_random_baseline_seed_42_20260908T165057503284Z/`
- `data/output/town01_history_80_20_seed_42_20260908T165328025159Z/`

Las decisiones pudieron reproducirse a partir de la semilla y el historial
individual. No hubo `blocked`, `timeout` ni `route_failed`. Los tres `aborted`
por corrida correspondían a viajes activos al terminar los 600 segundos.
Al finalizar quedaron cero vehículos y sensores, modo asíncrono restaurado y
renderizado desactivado. No hubo crash en estas pruebas.

### Problema 1: alcance a un vehículo detenido

En el baseline, 852 de los 857 registros pertenecen al contacto repetido entre
los carros 002 y 003: 426 callbacks por sensor, desde 250.55 hasta 271.85 segundos
desde el inicio de los viajes. No representan 852 accidentes independientes.
Antes del contacto, el carro 002 circulaba a unos 19.29 km/h y el 003 estaba
detenido, ambos en `road_id=6`, `lane_id=1`, con `y` aproximadamente 326.59.

Se confirmó un defecto de borde en el detector oficial de CARLA 0.9.15:
`BasicAgent._vehicle_obstacle_detected()` usa por defecto el intervalo angular
desde cero y `is_within_distance()` aplica límites estrictos. Un ángulo de cero
queda excluido aunque el objetivo esté exactamente delante. Una prueba offline
con geometría real de la SDK reproduce el falso negativo del agente original.
Esto encaja con la alineación observada; los logs antiguos no registraban cada
decisión interna del detector, así que no permiten atribuir todos los contactos
a esta única causa sin volver a probar.

Fuentes oficiales:

- [BasicAgent 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/PythonAPI/carla/agents/navigation/basic_agent.py)
- [is_within_distance 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/PythonAPI/carla/agents/tools/misc.py)

**Ajuste:** `src/carla_agent.py` define `CollinearSafeBasicAgent`, una subclase
local que cambia únicamente el límite inferior predeterminado de 0 a -0.001
grados. Como el ángulo calculado no es negativo, esto permite incluir cero.
Conserva los límites positivos explícitos, filtros de carril, tratamiento de
intersecciones, frenado y planificador oficiales. `src/route_planner.py` crea
esta subclase con un diccionario de opciones nuevo por agente. No se modificó
la instalación en `WindowsNoEditor`, la velocidad objetivo, el timestep, las
rutas ni la elección de destinos. El mismo ajuste se usa en ambos escenarios.

La extensión depende de un método interno de CARLA 0.9.15; revisar su contrato
y repetir las pruebas si se actualiza la SDK.

### Problema 2: totales que omitían las esperas

Los cuatro eventos faltantes del histórico eran de `vehicle_002` entre
`trip_003` y `trip_004`, con `trip_id` vacío. El código incrementaba los totales
solo cuando había un viaje activo. La causa está confirmada tanto en las marcas
de tiempo como en `TripSimulation._drain_events()`.

**Ajuste:** los totales ahora cuentan todos los callbacks drenados, incluidas
esperas. Los contadores por viaje siguen limitados a eventos asociados al viaje.
Un evento atrasado cuyo timestamp preceda la salida del viaje activo no se le
atribuye al nuevo viaje: queda con `trip_id` vacío, pero sí entra en el total.
No se reconstruyen retrospectivamente los contadores de viajes ya escritos.

El esquema CSV se conserva. `run_config.json` incorpora
`metrics_semantics_version=2`, la definición de los conteos y el ajuste del
controlador. Cada vehículo registra `carla_actor_id` para relacionarlo con
`other_actor_id`; los detalles de colisión añaden `other_actor_type`.
Se mantienen todos los callbacks originales, sin deduplicarlos silenciosamente.

### Pruebas del ajuste

48 pruebas automatizadas correctas, sin skips en `carla-env` con la ruta agents
configurada. Incluyen el falso negativo del agente original, detección corregida,
frenado efectivo en `run_step`, exclusión de vehículos detrás/lejanos/en otro
carril, límites angulares explícitos, conteos durante espera y callbacks tardíos.
Las pruebas de agentes usan la SDK pero no se conectan a un servidor.

```powershell
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
.\carla-env\Scripts\python.exe -m unittest discover -s tests -v
```

Sin la SDK o el paquete agents, las cuatro pruebas de compatibilidad se marcan
como omitidas; no deben confundirse con pruebas ejecutadas correctamente.

### Revalidación real después del ajuste

Ambas repeticiones terminaron sin crash, con las mismas condiciones ambientales
entre sí y los mismos parámetros, salvo el selector de destino. Cada comando
tardó 122.7 segundos reales para 600 segundos simulados.

| Medida | Baseline corregido | Histórico corregido |
|---|---:|---:|
| Viajes iniciados / completados / aborted | 14 / 11 / 3 | 14 / 11 / 3 |
| Distancia total | 5761.05 m | 5707.89 m |
| Velocidad media agregada | 11.89 km/h | 11.78 km/h |
| Registros de colisión totales | 7 | 2 |
| Registros de contacto entre los vehículos de la corrida | 0 | 0 |
| Invasiones en events_log / metrics_summary | 13 / 13 | 27 / 27 |
| Invasiones sin viaje asignado (incluidas en total) | 0 | 4 |
| Visitas finales por vehículo | 5, 4, 2 | 34, 34, 33 |

Resultados nuevos:

- `data/output/town01_random_baseline_seed_42_20260908T170849735844Z/`
- `data/output/town01_history_80_20_seed_42_20260908T171106564331Z/`

Se verificaron claves de viaje únicas, número de viajes, historias iniciales
más llegadas por vehículo y coincidencia entre el número de filas de eventos y
los totales de `metrics_summary.csv`. Hubo muestras de trayectoria de los tres
carros. El histórico conservó los cuatro eventos de espera con `trip_id` vacío
y ahora los incluyó en el total. La limpieza dejó cero vehículos y sensores,
modo asíncrono restaurado y renderizado desactivado.

**Resultado del ajuste:** el contacto repetido entre carros observado en el
baseline original no reapareció en esta repetición. Los registros totales de
colisión bajaron de 857 a 7, pero no desaparecieron todos los contactos.

**Pendiente concreto:** el baseline tiene seis callbacks `static.static` cerca
de `(96, 202)` y uno `static.sidewalk` cerca de `(98, 325)`; el histórico tiene
dos callbacks `static.static`. No son colisiones con los otros carros de la
corrida. Hace falta investigar geometría/trazado/control lateral en esas zonas
antes de ampliar el número de vehículos. El tipo genérico `static.static` no
identifica por sí solo qué objeto fue tocado. No se ha modificado esa geometría
ni ocultado esos eventos. Las variaciones de contactos estáticos no permiten
afirmar que el ajuste resuelva toda la conducción o toda la seguridad.

### Límites y siguiente paso

- Una sola semilla y tres vehículos no establecen superioridad estadística de
  un modelo. Conservar condiciones iguales para cada comparación.
- Las colisiones son callbacks de sensores; un contacto sostenido puede generar
  muchos y ser reportado por los dos vehículos. No interpretarlos como accidentes.
- Una invasión de carril puede involucrar marcas `Broken` o `NONE`; no equivale
  automáticamente a una maniobra ilegal o un accidente.
- El total incluye los eventos recibidos y drenados por el proceso. No garantiza
  recuperar callbacks que se pierdan ante un crash del servidor o cierre abrupto.
- Ctrl+C sigue limpiando los actores, pero puede dejar CSV parciales sin resumen
  final. No mezclar esas carpetas con corridas completas.
