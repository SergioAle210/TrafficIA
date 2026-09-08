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

## 2026-09-08 — Guardado de la fase y revisión previa a escalar

Commits de la implementación existente, creados antes de continuar:

- `7e78670`: escenario aleatorio, compatibilidad del agente, contabilidad de
  eventos y pruebas.
- `463e159`: README y evidencia de las corridas anteriores.

Se repitieron las 48 pruebas con `carla-env` y `CARLA_PYTHONAPI`: todas pasaron.
Los CSV genéricos y el documento LaTeX con cambios previos quedaron fuera.

La conexión de diagnóstico a `localhost:2000` agotó su timeout de 5 segundos.
No se ejecutó una nueva corrida real en esta revisión. Para continuar la
validación física hace falta un servidor accesible, preferiblemente ya en
Town01; las pruebas unitarias no lo requieren.

### Revisión del seguimiento lateral (todavía sin ajuste)

El `LocalPlanner` instalado de CARLA usa `base_min_distance=3.0` y
`distance_ratio=0.5`. En `run_step` elimina consecutivamente los waypoints
iniciales que están a menos de `3 + 0.5 * velocidad_mps` del vehículo, salvo
el último punto. A 20 km/h eso equivale a aproximadamente 5.78 m. El primer
punto restante es el objetivo del PID. Esto permite plantear una hipótesis
de recorte de curvas, pero no demuestra la causa de los contactos registrados.
El paso del PID por defecto (0.05 s) coincide con el de estas corridas:
no hay evidencia de un desajuste temporal en esta configuración.

El baseline registrado usó Audi e-tron (`vehicle_001`), Volkswagen T2 2021
(`vehicle_002`) y Audi TT (`vehicle_003`). No se deben atribuir todos los
contactos a un mismo modelo ni sustituirlos sin registrar esa variación.

Próxima validación, antes de aumentar la flota:

1. Reconstruir las rutas de los viajes con contactos cerca de `(96, 202)` y
   `(98, 325)` y contrastarlas con carriles y geometría de Town01.
2. Registrar el waypoint objetivo, orientación, dirección aplicada y separación
   lateral del vehículo en esos tramos; los CSV actuales no contienen esos
   datos y no permiten demostrar un error del PID por sí solos.
3. Si se confirma un problema de seguimiento, variar un solo parámetro por
   prueba, conservando modelos, semilla, clima y escenario. No eliminar eventos
   ni mover destinos para ocultar el síntoma.
4. Repetir ambos escenarios con tres carros y documentar resultados antes de
   pasar a cinco. La corrección de contactos estáticos sigue pendiente.

## 2026-09-08 — Diagnóstico de contactos estáticos y seguimiento de curvas

Implementación y pruebas guardadas en `483ee51`
(`fix(navigation): prevent corner cutting and opposite-lane arrivals`).
Se prepararon únicamente los archivos de esta corrección; los CSV genéricos
y `i-marco_teorico.tex` quedaron fuera de los commits.

### Condiciones y reproducción anterior al ajuste

Se comprobó primero la conexión mediante `carla-env`: `localhost:2000`
respondió con CARLA 0.9.15 y `Carla/Maps/Town01`. Tras esperar un snapshot se
puede inspeccionar la lista actual de actores; un cliente recién conectado
puede devolver una lista todavía vacía antes de recibir el primer frame.
No se recargó el mapa. Se conservó el clima anterior: precipitación 40,
humedad 80, altitud solar 20 y los demás campos guardados en `run_config.json`.
Se activó no-rendering antes de la serie y se mantuvo entre corridas.

Todas las corridas de esta investigación usan tres vehículos, spawns
`[133, 6, 101]`, semilla 42, 600 s simulados, delta 0.05 s y objetivo de
20 km/h. Modelos: Audi e-tron, Volkswagen T2 2021 y Audi TT, respectivamente.
Se ejecutaron secuencialmente con `--simulation-speed 5 --no-rendering` y
`--navigation-diagnostics`, sin Traffic Manager ni otros clientes de tráfico.
No se regeneró el dummy ni se modificaron destinos, geometría o sensores.

Se revisaron las cuatro carpetas de resultados de la primera investigación,
`src/trip_runner.py`, `src/route_planner.py`, `src/carla_agent.py` y los agentes
instalados de CARLA. Se reconstruyeron los viajes con contactos:

| Escenario | Vehículo / viaje | Origen → destino | Curva con contacto |
|---|---|---|---|
| Baseline | 003 / 002 | T01_030 → T01_050 | road 256, lane 1, cerca de (96, 202) |
| Baseline | 002 / 003 | T01_055 → T01_052 | road 256, lane 1, cerca de (96, 202) |
| Baseline | 001 / 006 | T01_030 → T01_027 | road 108, lane 1, cerca de (98, 325) |
| Histórico | 003 / 004 | T01_030 → T01_020 | road 256, lane 1, cerca de (96, 202) |

Ambas son curvas a la derecha de 4 m de ancho. El trazado de
`GlobalRoutePlanner` sigue sus centros; no se encontró un salto del plan hacia
el objeto ni un origen desalineado. Los puntos duplicados en uniones se
conservaron en el plan y en el log. La corrección colineal anterior se revisó
y se mantuvo: afecta al detector de vehículos, no resuelve el seguimiento
lateral frente a objetos estáticos.

**Antes de cambiar el controlador** se añadieron diagnósticos de solo lectura
y se ejecutaron estas reproducciones con el `distance_ratio=0.5` anterior:

- `data/output/town01_random_baseline_seed_42_20260908T181229522720Z/`:
  14 iniciados, 11 completados, 3 aborted; 6 callbacks de colisión (5 estáticos
  genéricos y 1 acera) y 10 invasiones.
- `data/output/town01_history_80_20_seed_42_20260908T181453301340Z/`:
  14 iniciados, 11 completados, 3 aborted; 1 callback estático y 27 invasiones.

### Causa confirmada y límite de identificación del objeto

El `LocalPlanner` elimina puntos a menos de `3 + 0.5 * velocidad_mps` y
entrega el primero restante al PID. A 20 km/h son unos 5.78 m. En estas curvas
ese descarte adelanta el objetivo y el vehículo recorta por el interior.
La secuencia se midió por frame, no se dedujo únicamente del CSV de colisiones:

- Baseline, 003/002, frame 37256: centro `(95.893, 201.978)`, error lateral
  interior **1.761 m**, objetivo `(101.420, 199.141)` ya en la recta de salida,
  distancia al objetivo 5.938 m, radio de descarte 5.683 m, dirección 0.208.
  Un segundo antes el error era 0.568 m y el objetivo estaba a 6.757 m; el
  rumbo del vehículo ya adelantaba al de la curva en 10.114 grados.
- Baseline, 002/003: error interior máximo **1.903 m** cerca de (96, 202).
- Baseline, 001/006, frame 42687: reaparece exactamente la posición del
  contacto antiguo con la acera, `(98.139, 324.789)`, con error interior
  **1.067 m**, objetivo `(92.879, 320.360)`, distancia 6.604 m y dirección 0.435.
- Histórico, 003/004: contacto cerca de `(95.949, 201.977)` con error
  interior **1.781 m** y objetivo también en la recta de salida.

El inventario `get_environment_objects()` identifica
`sphericalPlantPot_44_SM_0`, tipo `Static`, centrada en
`(97.370, 203.530, 0.525)`, semiextensiones `(0.797, 0.797, 0.425)` m.
Las huellas XY de los vehículos se solapan con su caja durante los contactos
genéricos reproducidos. Centradas y orientadas sobre la ruta, esas huellas
dejan unos 1.76–1.87 m respecto a esa caja. Esto apoya fuertemente que la
maceta sea el objeto tocado. **El sensor solo devuelve `static.static` e ID 0**:
la asociación geométrica no identifica de forma inequívoca la malla de colisión.
Una caja proyectada en XY tampoco es la superficie física del objeto.

Fuentes contrastadas con la SDK local:
[LocalPlanner 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/PythonAPI/carla/agents/navigation/local_planner.py)
y [PID 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/PythonAPI/carla/agents/navigation/controller.py).
El paso PID sigue siendo 0.05 s, igual al timestep; no se confirmó un fallo
de sincronización temporal ni fue necesario cambiar sus ganancias.

### Cambios y ensayo descartado como validación final

En `src/route_planner.py` se entrega un único parámetro distinto:
`distance_ratio=0.1`. Se conserva `base_min_distance=3.0`, lo que da unos
3.56 m de descarte a 20 km/h. No se modificó `src/carla_agent.py` ni la SDK.
La configuración `controller_distance_ratio` y el argumento CLI
`--controller-distance-ratio` permiten comparar explícitamente 0.5 y 0.1;
se rechazan valores negativos o no finitos antes de conectar.

El primer ensayo con 0.1 quedó en
`data/output/town01_random_baseline_seed_42_20260908T181720405162Z/`.
Aunque registró cero colisiones e invasiones, sus 13 viajes completados **no
se usan como resultado final**: reveló un defecto independiente de llegada.
El 001/001 completó tras 215.5 m una ruta de 479.3 m al pasar por el carril
contrario, a menos de 4 m del destino. Su pose cercana al cierre era
`(92.377, 78.288)`, road 22/lane 1, mientras el destino estaba en road 22/lane -1.
La pequeña diferencia lateral bastó para activar la comprobación euclidiana
antigua y empezar el siguiente viaje prematuramente.

`src/trip_runner.py` exige ahora distancia dentro del umbral **y coincidencia
de road_id/lane_id con el destino**. Esta regla se aplica a ambos escenarios
y a ambos valores del controlador. Se repitieron las referencias 0.5 con la
nueva regla antes de la comparación final; los contactos volvieron a aparecer.
`run_config.json` documenta `arrival_policy`, por lo que no debe confundirse
la semántica de llegada nueva con la de los registros anteriores.

También se añadieron `src/navigation_diagnostics.py`, escritores opcionales
en `src/run_logger.py` y argumentos en `scripts/run_trip_simulation.py`:

- `route_log.csv`: plan completo por vehículo/viaje antes de que se consuma.
- `control_log.csv`: pose, velocidad, objetivo, dirección, acelerador, freno,
  radio de descarte y proyección lateral sobre el plan, en cada frame con
  control activo. El comando se registra antes de aplicarlo para el tick siguiente.
- La proyección ignora segmentos de longitud cero para el cálculo, conserva
  los waypoints originales y usa tangentes interpoladas al cruzar ±180°.
  Es error respecto a la polilínea, no separación respecto a la acera. En
  rutas que se cruzan a sí mismas, la referencia espacial más cercana puede
  ser ambigua; no se usa para controlar ni decidir llegadas.
- Los CSV y conteos de eventos anteriores mantienen su esquema y semántica
  versión 2. No se suprimen callbacks. Los diagnósticos son optativos.

Las **64 pruebas unitarias pasan sin skips** con `carla-env` y
`CARLA_PYTHONAPI`, incluidas las regresiones anteriores. Las nuevas pruebas
usan la geometría medida de Town01 con el `LocalPlanner` real para comprobar
que 0.1 retiene un objetivo intermedio; cubren frenado al agotar el plan,
opciones independientes, CLI, valores inválidos, llegada en carril contrario,
proyección/signos, archivos opcionales y ausencia de ticks, llamadas al agente
o controles adicionales al habilitar el diagnóstico. No sustituyen las corridas físicas.

### Comparación real final con la misma regla de llegada

Las cuatro corridas siguientes terminaron sin crash. La comparación automática
de `run_config.json` confirmó igualdad de clima, iluminación, los 36 semáforos
reiniciados, modelos, atributos/colores, posiciones iniciales y semillas por
vehículo. No había vehículos externos. En cada escenario, la secuencia de
orígenes, destinos, clases de selección y estados fue idéntica entre 0.5 y 0.1.
Solo se varió `controller_distance_ratio`; ambas referencias ya incluían la
comprobación de carril al llegar y los mismos diagnósticos.

| Medida | Baseline 0.5 | Baseline 0.1 | Histórico 0.5 | Histórico 0.1 |
|---|---:|---:|---:|---:|
| Iniciados / completados / aborted | 14 / 11 / 3 | 14 / 11 / 3 | 14 / 11 / 3 | 14 / 11 / 3 |
| Distancia total (m) | 5761.75 | 5560.23 | 5707.66 | 5674.97 |
| Velocidad media agregada (km/h) | 11.89 | 11.47 | 11.78 | 11.71 |
| Callbacks de colisión | 6 | **0** | 1 | **0** |
| Invasiones, events_log = metrics_summary | 10 | 0 | 27 | 2 |
| Filas de control | 34886 | 34886 | 34886 | 34886 |
| Historial final por vehículo | 5, 4, 2 | 5, 4, 2 | 34, 34, 33 | 34, 34, 33 |

Cada corrida avanzó 600.000009 s simulados (error numérico del timestep) y
tardó aproximadamente 122 s reales desde la creación del ID hasta el cierre.
Los tres `aborted` son los viajes activos al alcanzar la duración. No hubo
`blocked`, `timeout` ni `route_failed`. La distancia menor con 0.1 refleja
tiempos distintos de paso y espera; no demuestra una mejora de movilidad.
El primer viaje del Audi e-tron del baseline recorrió 475.4 m de su plan de
479.3 m y llegó desde el carril correcto: ya no se cerró tras los 215.5 m
del ensayo rechazado.

Referencias con 0.5 y llegada corregida:

- `data/output/town01_random_baseline_seed_42_20260908T182133276773Z/`
- `data/output/town01_history_80_20_seed_42_20260908T182355451125Z/`

Resultados finales con 0.1:

- `data/output/town01_random_baseline_seed_42_20260908T182618700799Z/`
- `data/output/town01_history_80_20_seed_42_20260908T182846213527Z/`

La cobertura de las curvas se comprobó contra `control_log.csv`, tomando
vehículos en movimiento (>1 m/s), a menos de 12 m de cada punto y proyectados
al segmento de la ruta en road 256 o 108, respectivamente. Los mismos pares
vehículo/viaje atravesaron esas curvas antes y después:

| Zona / escenario | Pasos (vehículo/viaje) | Máximo error interior 0.5 → 0.1 |
|---|---|---:|
| (96, 202), baseline | 002/003 y 003/002 | 1.903 → 0.857 m |
| (98, 325), baseline | 001/006, 002/002 y 003/002 | 1.605 → 0.719 m |
| (96, 202), histórico | 003/004 | 1.790 → 0.770 m |
| (98, 325), histórico | 003/004 | 1.501 → 0.651 m |

En los pasos por road 256, la separación mínima de la huella XY a la caja de
la maceta pasó de solapamiento a 0.993–1.018 m. Esto es una medida geométrica
aproximada, adicional a los sensores: **las corridas finales no registraron
contactos estáticos ni entre vehículos en ninguna parte del mapa**.

Las dos invasiones restantes del histórico son de `vehicle_002`, marca `Broken`:
frame 466113 cerca de `(2.176, 321.026)`, sin viaje asignado durante la espera,
y frame 466243 cerca de `(1.149, 318.196)`, en `trip_004`. No corresponden a
los puntos estáticos investigados. Ambas se conservaron y el resumen cuenta 2;
la suma por viaje es 1 porque la otra pertenece a una espera.

La auditoría verificó claves únicas de viaje, tres IDs en trayectorias y
controles, totales iguales al número de callbacks, historial inicial más
llegadas por vehículo, secuencias comparables y ausencia de fallos de ruta.
Después de la última corrida se esperó un snapshot nuevo y se confirmó:
CARLA disponible, Town01, cero vehículos y sensores, modo asíncrono y
no-rendering activo.

Los artefactos auxiliares locales están en
`data/output/static_contact_investigation/`: `environment_objects.json`,
`vehicle_boxes.json`, `comparison.json`, `cleanup.json`, `unit_tests.txt`,
los cuatro logs de consola finales y `analyze.py`. Este último comprueba
integridad y genera la comparación sin escribir en las carpetas de corrida:

```powershell
.\carla-env\Scripts\python.exe data/output/static_contact_investigation/analyze.py data/output/town01_random_baseline_seed_42_20260908T182133276773Z data/output/town01_history_80_20_seed_42_20260908T182355451125Z data/output/town01_random_baseline_seed_42_20260908T182618700799Z data/output/town01_history_80_20_seed_42_20260908T182846213527Z
```

`data/output/` sigue excluido de Git; las carpetas antiguas se preservaron.
Los comandos para reproducir ambas configuraciones están en README. No se
crearon automatizaciones ni se aumentó la flota.

### Pendientes tras esta corrección

- La causa del recorte quedó confirmada por las medidas y por variar un solo
  parámetro en la comparación final. El resultado está limitado a Town01,
  tres modelos y semilla 42; repetir con otras semillas/modelos antes de escalar.
- Revisar las dos invasiones de marca `Broken` en la zona de T01_067 y sus
  esperas. No interpretarlas automáticamente como accidentes o maniobras ilegales.
- El nombre de la maceta es una asociación geométrica muy consistente;
  `static.static`/ID 0 no permite demostrar qué malla produjo el callback.
- No se midieron contactos perdidos por un posible cierre abrupto ni se
  establecieron garantías generales de conducción. Se conservan los límites
  de contabilidad y física descritos en las entradas anteriores.
