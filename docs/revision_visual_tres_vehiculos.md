# Revisión de tres vehículos — 2026-09-15

Estado: **dos corridas de 600 s completadas y auditadas sin cámaras**, por
solicitud del estudiante después de dos fallos gráficos. Revisión visual
completa pendiente. Esta revisión precede a los pilotos de 5, 10 y 20
vehículos; no establece todavía los dos niveles definitivos de demanda.

## Condiciones y método

Town01, CARLA 0.9.15, tres vehículos, semilla 42, 600 segundos simulados
por escenario (`random_baseline` y `history_80_20`), delta 0.05 s, ritmo 1×
y renderizado activo. Se conservan los modelos, spawns `[133, 6, 101]`,
clima lluvioso y parámetros de `config/multi_vehicle_trip.json`.

`scripts/review_trip_simulation.py` reutiliza los argumentos habituales y
`VisualReviewSimulation` hereda la conducción de `TripSimulation`. El modo
visual inicialmente previsto añade una
cámara RGB rígida cenital por vehículo: 640 × 360, altura 18 m, FOV 90° e
intervalo solicitado 0.5 s. Los callbacks guardan imágenes mediante una cola;
solo el runner avanza el mundo. No se modificaron rutas, controlador, reglas
de llegada ni el umbral `blocked` de 60 s.

Cada corrida conserva:

- `images/vehicle_XXX/frame_*.png`: imágenes originales.
- `image_index.csv`: asociación exacta vehículo/frame con tiempo del mundo,
  viaje y fases antes/después de actualizar el viaje; timestamp y pose de la
  cámara originales por separado.
- `observation_log.csv`: posición, orientación y velocidad por tick, incluyendo
  espera; semáforo y otros vehículos configurados a menos de 30 m cuando la
  velocidad es inferior a 0.2 m/s. Las distancias son entre centros y no prueban
  obstrucción ni congestión.
- `visual_review_config.json`: cámaras, semántica y hashes de código/entradas;
  `run_config.json`: configuración efectiva, flota y ambiente.
- `capture_summary.json`: guardado, descartes de cola, errores, asociación,
  cadencia y finalización. Cámaras incluidas en la limpieza heredada.

Los timestamps RGB observados pueden diferir 0.05–0.10 s del tiempo del
mundo del mismo frame. Se conserva esa diferencia; no se reasignan imágenes
al viaje más reciente ni al timestamp más cercano. El código de
[PixelReader de CARLA 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/Unreal/CarlaUE4/Plugins/Carla/Source/Carla/Sensor/PixelReader.h)
asigna el frame desde el hilo de renderizado; la documentación de
[sincronización](https://carla.readthedocs.io/en/0.9.15/adv_synchrony_timestep/)
también advierte el retraso de cámaras GPU. El índice identifica el frame
declarado por el sensor, sin afirmar sincronía perfecta de todos sus campos.

En algunos intervalos aparecen 11 y después 9 frames, alrededor del objetivo
de 10. `potential_missing_samples` es una alerta conservadora por huecos,
**no un conteo demostrado de imágenes perdidas**: un desplazamiento de un
frame puede dispararla aun conservando todas las capturas. Se informan por
separado las pérdidas comprobables de cola/guardado y las irregularidades.

## Verificación técnica

Suite con `carla-env` y agents de la SDK: **106 pruebas aprobadas** inicialmente
y **107** después de añadir el modo `--no-cameras`.
Incluye asociación con callbacks retrasados, fases de llegada, cola limitada,
errores de escritura, finalización ante interrupción y propiedad de sensores
antes de activar su listener. Registro:
`data/output/visual_review_20260915/unit_tests.txt` y
`unit_tests_no_cameras.txt`. La prueba nueva verifica que se conserve el
registro de observaciones sin crear cámaras ni un escritor de imágenes.

Se conservaron las comprobaciones técnicas de 15 s, que no se mezclan con las
corridas de evaluación. Cada una produjo 90 imágenes (30 por vehículo).
La primera permitió corregir la interpretación de timestamp/cadencia del
auditor; los archivos originales permanecen intactos. La segunda verificó la
versión corregida. Una tercera, después de reiniciar el servidor con
RenderOffScreen, verificó nuevamente las tres vistas y su limpieza.

## Intento interrumpido y recuperación

El primer intento de baseline se interrumpió cerca de 196 s:
`town01_random_baseline_seed_42_20260916T005550477777Z`.
Conserva 1,179 imágenes y dos llegadas, pero carece de resumen final válido.
No se transforma en una corrida completa ni se inventan finalizaciones para
los viajes activos al perder el servidor.

El crash context de Unreal identifica `GPUCrash`, pérdida del dispositivo
D3D (`0x887A0020 INTERNAL_ERROR`) y GPU Intel UHD Graphics 770. El timeout
del cliente es posterior a ese fallo. La evidencia se resume en
`data/output/visual_review_20260915/server_crash.json`; no demuestra por sí
sola qué operación provocó el fallo gráfico. Las dos secuencias de llegada
disponibles muestran espera y reinicio sobre la calzada; no sustituyen la
cobertura completa de los tres vehículos.

El estudiante preparó de nuevo CARLA y Town01 con `-RenderOffScreen`.
Este modo conserva las imágenes de sensores y evita presentar la ventana;
se distingue de desactivar el renderizado, según la
[documentación de renderizado](https://carla.readthedocs.io/en/0.9.15/adv_rendering_options/).
No se redujeron cámaras, resolución ni frecuencia para el reintento.

Ese reintento, `town01_random_baseline_seed_42_20260916T010728902573Z`,
también perdió el dispositivo D3D. El segundo crash context confirma los
argumentos `-quality-level=Low -dx11 -RenderOffScreen`, la misma GPU y el mismo
error. Se conserva en `server_crash_offscreen.json`. El cliente terminó con
código 1 y no dejó `capture_summary.json` ni un índice final; las imágenes
existentes no constituyen una captura íntegra.

El estudiante pidió continuar **sin cámaras** y preparó nuevamente Town01.
Se añadió `--no-cameras` al script de revisión, conservando observaciones por
tick, fases, semáforos y vehículos cercanos. Los sensores originales de
colisión/invasión permanecen activos. El modo deja explícitamente
`image_capture_enabled: false`, sin cámaras ni evidencia visual, y conserva
el renderizado del mundo. Se mantienen tres vehículos, semilla, clima,
duración, ritmo y conducción.

La comprobación técnica sin cámaras de 15 s
(`town01_random_baseline_seed_42_20260916T011125028094Z`) produjo 300 registros
por vehículo y dejó cero vehículos/sensores, mundo asíncrono y renderizado
activo. Las versiones de código y entradas anteriores y posteriores al cambio
de instrumentación se conservan separadas en `source_snapshot/` y
`source_snapshot_no_cameras/` dentro de la carpeta de revisión.

## Resultados y decisión

Las corridas completas sin cámaras usan Audi e-tron (001), Volkswagen T2
2021 (002) y Audi TT (003). Los hashes de código/entradas y las condiciones
ambientales coinciden entre tratamientos; se conserva la semilla 42.

Baseline completó los 600 s sin cámaras:
`town01_random_baseline_seed_42_20260916T011215560060Z`.
Histórico completó también 600 s:
`town01_history_80_20_seed_42_20260916T012237341817Z`.
Los nombres usan UTC del día 16; las ejecuciones fueron la noche del día 15
en Guatemala.

| Escenario | Completados 001 / 002 / 003 | Activos al corte | Fallos de ruta / blocked / timeout | Colisiones / invasiones | Errores de integridad |
|---|---|---:|---|---|---:|
| random_baseline | 5 / 4 / 2 | 3 | 0 / 0 / 0 | 0 / 0 | 0 |
| history_80_20 | 4 / 4 / 3 | 3 | 0 / 0 / 0 | 0 / 0 | 0 |

Baseline registra 12,000 observaciones por vehículo (36,000 en total), frames
consecutivos comunes a los tres actores, once llegadas y once ciclos
llegada/espera/nuevo viaje completos en logs. Las once posiciones de llegada
proyectan sobre los carriles registrados del OpenDRIVE instalado. Los tres
`aborted` llevan motivo `simulation_end`; no fueron `blocked` ni se originaron
por destruir los actores.

Tiempo medio de completados: 137.209 s; velocidad de presencia, incluyendo
esperas: 11.565 km/h; distancia: 5.782 km. Durante las esperas de destino,
la velocidad máxima fue 0.000497 m/s y el desplazamiento entre primera y
última muestra fue como máximo 0.000314 m. Se registraron 23 intervalos de
baja velocidad de al menos 10 s; máximos por vehículo: 32.20 / 27.50 / 31.95 s.
Son intervalos bajo 0.2 m/s, no conteos automáticos de atascos.

Histórico también registra 36,000 observaciones, once ciclos completos y
once llegadas válidas sobre los carriles registrados. Tiempo medio de
completados: 142.205 s; velocidad de presencia: 11.332 km/h. Durante la espera,
velocidad máxima 0.000656 m/s y desplazamiento máximo 0.000306 m. Hubo 23
intervalos de baja velocidad de al menos 10 s; máximos por vehículo:
30.75 / 30.55 / 32.15 s. Los tres incompletos son igualmente `simulation_end`.

En total se auditaron **72,000 observaciones y 22 ciclos**. No hubo `blocked`;
los seis `aborted` se registraron al alcanzar la duración, antes de destruir
actores. El umbral de bloqueo permaneció en 60 s. La limpieza de ambas
corridas se comprobó aparte: cero vehículos/sensores, mundo asíncrono y
renderizado activo. No se reinició el servidor entre estas dos corridas.

Ejemplo de interacción sin colisión: en t≈265 s de baseline, el vehículo 002
está detenido detrás del 003 cerca de `(130.15, 326.59)`, orientados en el
mismo sentido. La separación entre centros es 7.225 m; en los ejes del 002,
el 003 está 7.225 m delante y 0.011 m a un lado. Esto documenta seguimiento
de otro vehículo incluso con solo tres actores; no demuestra por sí solo
congestión de la red ni la causa inicial de la parada del líder.

La comparación con la ejecución manual del 14 de septiembre conserva los
14 pares vehículo/viaje con los mismos destinos, estados, motivos de cierre,
duraciones y distancias registradas. Es repetibilidad de esos resultados;
la corrida anterior no tiene hashes de código y no se certifica determinismo
por frame. Detalle: `baseline_vs_manual.json`.

La auditoría, métricas y figura están en
`data/output/visual_review_20260915/baseline_no_cameras_review/`.
El equivalente del histórico está en `history_no_cameras_review/`; el
[informe comparativo](../data/output/visual_review_20260915/metrics/report.md)
y `metrics/destinations.csv` contienen las cuatro métricas y distribuciones.
Las condiciones registradas pasan la comprobación de comparabilidad. Una
pareja con semilla 42 no establece superioridad estadística de un selector.

![Trayectorias y velocidades de baseline, sin cámaras](../data/output/visual_review_20260915/baseline_no_cameras_review/trajectories.png)

![Trayectorias y velocidades del histórico, sin cámaras](../data/output/visual_review_20260915/history_no_cameras_review/trajectories.png)

Las dos secuencias visuales que sí se conservaron pertenecen al primer intento
interrumpido (vehículos 002 y 001, primer viaje). Muestran aproximación,
espera y reinicio, pero no cubren el vehículo 003 ni el histórico:

![Evidencia visual parcial del intento interrumpido](../data/output/visual_review_20260915/live_arrivals.png)

El criterio para avanzar es integridad de registros y ausencia de errores
de implementación que impidan interpretar los viajes. **Se puede pasar al
piloto de cinco vehículos con base en esta revisión de logs**, manteniendo
explícita la revisión visual pendiente. No se exige cero
invasiones ni conducción perfecta: los eventos son parte de las métricas
del tercer objetivo específico.

La revisión visual completa del plan original queda **pendiente** por el cambio
de alcance autorizado. Las imágenes parciales solo documentan los intentos
interrumpidos. Las corridas sin cámaras permitieron auditar todas las llegadas,
esperas y reinicios registrados, además de las paradas de al menos 10 s y los
eventos. Los gráficos de posiciones y velocidades no sustituyen imágenes
del simulador ni miden la holgura de la huella respecto de cada objeto.

El estado semafórico se registra cuando `vehicle.is_at_traffic_light()` es
verdadero. Un valor vacío significa que esa API no identificó un semáforo
afectando al vehículo en ese tick; **no descarta una espera semafórica**.
En la SDK instalada, `BasicAgent._affected_by_traffic_light` usa el waypoint
del trigger, un umbral de distancia y su último semáforo rojo, por lo que puede
frenar antes de que aquella API lo considere dentro de la zona. La atribución
exclusiva de cada parada no se deduce de este registro. Si resulta necesaria
en los pilotos, habrá que observar también el semáforo retenido por el agente,
con idéntica instrumentación para ambos tratamientos.

## Siguiente etapa

1. Preparar una configuración separada para cinco vehículos, spawns válidos
   e historiales completos. Conservar una flota comparable entre selectores.
2. Ejecutar ambos escenarios como pilotos, manteniendo criterios de métricas,
   duración y tratamiento de incompletos. Revisar interacciones, paradas,
   incidentes y capacidad del equipo; no ajustar para forzar cero eventos.
3. Continuar con diez y veinte si los resultados se pueden interpretar.
   Estos escalones sirven para explorar carga, no fijan todavía demanda baja
   y alta. Definir las dos cantidades después de reunir esa evidencia.

No se crearon configuraciones de mayor flota ni se ejecutaron esos pilotos
en esta revisión. No se hicieron commits. Se conservaron los resultados
anteriores y las modificaciones preexistentes del repositorio.

Actualización posterior: el estudiante autorizó guardar los Markdown/Python
pendientes y ejecutar el piloto de cinco, dejando preparados diez y veinte.
El avance, configuraciones, historiales y resultados de esa etapa se registran
en [pilotos de escalamiento](pilotos_escalamiento.md). Los resultados de tres
vehículos descritos arriba permanecen como antecedente independiente.

El piloto de cinco completó ambos escenarios: 17 y 19 llegadas, cinco viajes
activos al corte por escenario, sin errores de integridad ni `blocked`.
Las configuraciones e historiales de 10/20 quedaron preparados en esa etapa.
No se fijaron demandas finales.

Actualización del **2026-09-17**: se completaron diez y después veinte, ambos
selectores, 600 s, semilla 42 y sin cámaras. Llegadas: 28/33 con diez y 55/63
con veinte. Las cuatro auditorías pasaron, sin bloqueos, fallos de ruta ni
colisiones. Veinte registró dos invasiones NONE por escenario del Cybertruck;
se conservaron y contextualizaron sin modificar conducción. Se auditaron
179 llegadas, 175 ciclos completos y 720,000 observaciones. Los cuatro ciclos
restantes terminaron en espera al corte de duración. El informe de pilotos
incluye resultados por vehículo, comparación 5/10/20 y próximos pasos.
La evidencia sigue siendo de registros; la revisión visual permanece pendiente.

Ampliación posterior del mismo día: se completaron cuatro corridas de veinte
con semillas 210/109, ambos selectores y 1,800 s a ritmo solicitado 5×.
Se auditaron 783 llegadas y 781 ciclos; las dos esperas finales quedaron
cortadas por duración. Hubo dos episodios de contacto entre vehículos
(524 callbacks) en baseline, conservados sin ajustar conducción. Resultados,
reconstrucciones y límites en la
[campaña larga de veinte](campana_larga_veinte_vehiculos.md). Sigue pendiente
la revisión con imágenes; esta ampliación no la declara completada.
