# Pilotos de escalamiento en Town01

Inicio: 2026-09-15, Guatemala. Cierre actualizado: 2026-09-17. **Los pilotos
de cinco, diez y veinte están completados y auditados en ambos escenarios**.
Los resultados de cinco se conservan abajo; diez, veinte, la comparación y
los siguientes pasos se encuentran al final.

## Alcance y condiciones

Estos pilotos investigan el escalamiento antes de elegir las dos cantidades
definitivas de demanda. Se conserva Town01, semilla 42, 600 s por escenario,
delta 0.05 s, ritmo 1×, renderizado y conducción actuales. Se ejecutan
`random_baseline` e `history_80_20` con **cinco vehículos y sin cámaras RGB**.
Los sensores de colisión e invasión permanecen activos. No se exige cero
eventos para aceptar una corrida íntegra.

CARLA 0.9.15 respondió en localhost:2000, Town01, sin vehículos/sensores,
asíncrono y con renderizado. El clima conserva precipitación 40 y mojado 80.
No se cambió el mapa ni se reinició el servidor durante la preparación.

## Configuraciones e historiales

| Vehículos | Configuración | Historial | Visitas previas |
|---:|---|---|---:|
| 5 | `config/experiments/scaling_pilots/town01_05.json` | `data/input/histories/Town01/scaling_pilots/vehicle_history_05.csv` | 150 |
| 10 | `config/experiments/scaling_pilots/town01_10.json` | `data/input/histories/Town01/scaling_pilots/vehicle_history_10.csv` | 300 |
| 20 | `config/experiments/scaling_pilots/town01_20.json` | `data/input/histories/Town01/scaling_pilots/vehicle_history_20.csv` | 600 |

Cada vehículo tiene 30 visitas sintéticas usando el generador existente,
semilla 42 y tres anclas iniciales de categorías distintas. Los primeros
cinco historiales coinciden con el archivo existente; los vehículos comunes
conservan su historial y sus secuencias aleatorias al ampliar la flota.
El 80/20 define probabilidades del selector, no garantiza una proporción
exacta en una muestra pequeña de viajes.

Las flotas son prefijos de una lista única de spawns. Se conservan
`[133, 6, 101]` y se añaden candidatos del catálogo, sobre carriles driving
fuera de intersecciones, eligiendo cada vez el de mayor distancia XY al
punto seleccionado más cercano. Los empates usan el índice menor. Cinco
usa `[133, 6, 101, 67, 43]`. Distancias mínimas iniciales entre centros:
75.09 m para 5/10 y 49.81 m para 20. Este criterio dispersa los orígenes;
no demuestra capacidad de la red ni representa demanda urbana calibrada.

`scripts/prepare_pilots.py` reproduce la preparación leyendo el mapa, sin
avanzar ticks ni crear actores. Rechaza un mapa distinto y archivos de salida
existentes con contenido diferente. `config/experiments/scaling_pilots/preparation_manifest.json`
conserva la lista de puntos, criterios y hashes. El catálogo y el historial
original permanecen intactos. La validez geométrica de 10/20 no equivale a
una prueba real de spawn y circulación de esas flotas.

## Registro y verificación

Se amplió únicamente la instrumentación: durante paradas con viaje activo,
se registra el semáforo que BasicAgent guardó en el paso de control anterior
y su estado actual. No se vuelve a ejecutar su detector ni se cambia su
decisión. Durante la espera en destino no se atribuye un semáforo de un viaje
anterior. Esta información complementa `is_at_traffic_light()` y la proximidad
de otros vehículos; no identifica automáticamente una causa exclusiva.

Pasaron **111 pruebas** con `carla-env`, incluyendo preservación de flotas e
historiales, secuencias aleatorias y lectura pasiva del semáforo del agente.
Registro: `data/output/pilot5_20260915/unit_tests.txt`.

La comprobación técnica histórica de 15 s creó correctamente los cinco
vehículos, cargó sus historiales y produjo 1,500 observaciones sin errores
de integridad. Al terminar quedaron cero vehículos/sensores. El semáforo
retenido por el agente del 003 aparece en 175 muestras de parada, aun antes
de entrar en el trigger: el nuevo dato cubre la limitación identificada en
la revisión anterior. No se considera una corrida de evaluación de 600 s.

`scripts/audit_observations.py` generaliza la auditoría anterior a la cantidad
de vehículos del registro. Revisa frames, fases, historial/llegadas, carriles,
esperas y contexto de paradas, y genera figuras. Los ciclos observados se
reportan; no tener una llegada no convierte por sí solo una corrida íntegra
en un error. `--minimum-cycles` permite exigir una cobertura explícita cuando
corresponda. Los estados semafóricos y vehículos cercanos pueden coincidir;
sus tiempos no se suman como causas excluyentes.

Antes de esta etapa se crearon los Conventional Commits solicitados:
`e94fe4e` (instrumentación), `433bd8d` (análisis) y `77d08bf` (documentación).
Los cambios nuevos del piloto quedan sin commit.

## Ejecución

Con CARLA/Town01 preparado, ejecutar un escenario y después el otro:

```powershell
.\carla-env\Scripts\python.exe -u scripts/review_trip_simulation.py `
  --no-cameras --config config/experiments/scaling_pilots/town01_05.json `
  --scenario random_baseline --seed 42 --seconds 600 --simulation-speed 1 `
  --navigation-diagnostics `
  --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

Para histórico, cambiar `--scenario history_80_20`. Para futuros pilotos,
usar el JSON de 10 o 20; cada uno ya apunta a su historial correspondiente.
El runner valida el mapa, conserva resultados anteriores y usa un único
cliente para avanzar la simulación.

La auditoría de una carpeta terminada se puede repetir en un directorio
nuevo (reemplazar `CARPETA_CORRIDA` por el nombre real):

```powershell
.\carla-env\Scripts\python.exe scripts/audit_observations.py `
  data/output/CARPETA_CORRIDA data/output/auditoria_nueva --minimum-cycles 1
```

Ese requisito de un ciclo por vehículo verifica cobertura; no es un filtro
para descartar corridas con incidentes. El archivo `audit.json` conserva
estados, errores, paradas y limitaciones. Los logs originales no se editan.

## Resultados y siguiente decisión

Baseline completó 600 s: **17 llegadas y cinco viajes activos al corte**,
sin errores de integridad, `blocked`, `route_failed`, `timeout`, colisiones
ni invasiones. Llegadas por vehículo 001–005: **5 / 4 / 2 / 3 / 3**.
Se auditaron 60,000 observaciones, 17 ciclos completos y 17 llegadas
proyectadas sobre los carriles registrados. El servidor quedó limpio antes
de iniciar el histórico.

Tiempo medio de completados 152.476 s; velocidad de presencia 11.619 km/h;
distancia 9.683 km; exposición 0.833 vehículo-hora. La instrumentación midió
600.172 s de pared desde su preparación hasta finalizar la limpieza: ritmo
cercano a 1×, que no mide la capacidad máxima del equipo.

Hubo 39 intervalos bajo 0.2 m/s de al menos 10 s, con máximo de 32.20 s.
Treinta y siete tienen alguna muestra de semáforo rojo retenido por el
agente y doce incluyen vehículos cercanos. Estas categorías se superponen
y no constituyen una atribución causal exclusiva. La fracción de presencia
a baja velocidad fue 35.15 %, incluyendo las esperas en destino.

Las dos paradas largas sin rojo retenido incluyen un vehículo detenido
delante: 002 detrás de 003 a unos 7.224 m, y 005 detrás de 004 a unos
7.417 m entre centros, con escasa separación lateral. Son compatibles con
seguimiento; la evidencia está en `stop_examples.json`. Se conservaron las
dos observaciones y no se ajustó el controlador para eliminarlas.

En los 14 pares vehículo/viaje comunes con baseline de tres vehículos,
las duraciones registradas coinciden. La presencia a baja velocidad cambia
de 35.22 % a 35.15 % para toda la flota. Estos números, junto con los
nuevos recorridos de 004/005, no respaldan atribuir el aumento del tiempo
medio por viaje a congestión. Es una comparación exploratoria de una semilla,
no una estimación calibrada de capacidad.

![Velocidades y trayectorias del piloto baseline](../data/output/pilot5_20260915/baseline_review/trajectories.png)

Carpeta baseline: `town01_random_baseline_seed_42_20260916T020205968035Z`,
bajo `data/output/`. La campaña, pruebas, snapshot y auditorías están en
`data/output/pilot5_20260915/`. Los nombres de corrida usan UTC del día 16;
la fecha local es 15 de septiembre.

Histórico completó también 600 s: **19 llegadas y cinco viajes activos al
corte**, sin errores de integridad, `blocked`, `route_failed`, `timeout`,
colisiones o invasiones. Llegadas por vehículo: **4 / 4 / 3 / 5 / 3**.
Se auditaron sus 60,000 observaciones, 19 ciclos y 19 llegadas sobre los
carriles registrados. Tiempo observado de pared: 600.094 s, próximo a 1×.

| Métrica | random_baseline | history_80_20 |
|---|---:|---:|
| Llegadas | 17 | 19 |
| Activos al corte, `simulation_end` | 5 | 5 |
| Tiempo medio de completados (s) | 152.476 | 124.595 |
| Velocidad de presencia, incluidas esperas (km/h) | 11.619 | 11.483 |
| Distancia de presencia (km) | 9.683 | 9.569 |
| Presencia bajo 0.2 m/s (%) | 35.15 | 36.02 |
| Paradas de al menos 10 s | 39 | 38 |
| Mayor parada continua (s) | 32.20 | 32.15 |
| Colisiones / invasiones | 0 / 0 | 0 / 0 |
| Errores de integridad | 0 | 0 |

Treinta y siete paradas largas del histórico incluyen rojo retenido por
el agente y diez tienen vehículos cercanos, con superposición entre grupos.
Respecto del histórico con tres vehículos, los 14 pares vehículo/viaje
comunes conservan destino y estado; el cambio máximo de duración es 0.25 s.
La fracción de presencia a baja velocidad pasa de 36.61 % a 36.02 %.
El promedio menor de viajes completados no implica superioridad estadística:
cambian destinos y longitudes de los viajes observados entre selectores.

![Velocidades y trayectorias del piloto histórico](../data/output/pilot5_20260915/history_review/trajectories.png)

Carpeta histórica: `town01_history_80_20_seed_42_20260916T021229659097Z`.
El [informe comparativo](../data/output/pilot5_20260915/metrics/report.md),
`metrics/destinations.csv` y las auditorías por escenario conservan las
distribuciones, poblaciones y contexto. Los dos tratamientos pasan la
comparación de ambiente, flota, parámetros y hashes. Se verificó que el
código y las entradas permanecieron idénticos durante ambas corridas.

En total: **36 llegadas, 36 ciclos completos y 120,000 observaciones**.
Los diez `aborted` se registran al llegar a los 600 s, antes de destruir
actores. Al final CARLA sigue en Town01, cero vehículos/sensores, asíncrono
y con renderizado. No se reinició CARLA entre los dos pilotos.

**Se puede pasar al piloto de diez**, usando la configuración e historial
ya preparados, y auditarlo antes de ejecutar veinte. La evidencia de cinco
no muestra un incremento sustancial de demora en los vehículos comunes
para esta semilla; tampoco establece un nivel alto de demanda. Un
`blocked` exige revisar contexto antes de cambiar el umbral. Los `aborted`
por duración son viajes aún activos al corte, no llegadas ni bloqueos.

La revisión visual completa sigue pendiente. Los registros y gráficos no
sustituyen imágenes del simulador. No se fijarán los dos niveles definitivos
con este único piloto ni se afirmará superioridad de un selector con una semilla.

## Pilotos de diez y veinte — 2026-09-17

El estudiante autorizó ambos tamaños, en ese orden. Se mantiene Town01,
semilla 42, 600 s por escenario, delta 0.05 s, ritmo 1×, sin cámaras RGB,
los sensores de incidentes y el controlador común. El servidor responde
0.9.15; conserva el clima del piloto de cinco y no tiene tráfico externo.
La orden Low/DX11/RenderOffScreen es la comunicada por el estudiante; la
línea del proceso de Windows no pudo verificarse. No se reinició el servidor.

Las fuentes y entradas están congeladas en cada carpeta de campaña y se
comprueban antes y después de cada corrida. Se usa la suite de 111 pruebas
aprobada el mismo día; no se modificó la conducción después de esa prueba.
Los resultados adversos no se descartan y la auditoría no exige cero eventos.

Baseline de diez ya completó 600 s: **28 llegadas y diez activos al corte**,
sin bloqueos, fallos de ruta, timeout, colisiones ni invasiones. La auditoría
pasó: 120,000 observaciones y 28 ciclos completos. Tiempo medio de completados
168.155 s, velocidad de presencia 10.633 km/h, distancia 17.722 km, presencia
bajo 0.2 m/s 38.566 %. La mayor parada fue de 32.30 s; 83 de 87 paradas de
al menos 10 s incluyen rojo retenido por el agente y 44 tienen vehículos
cercanos, con superposición de contextos. Eso no atribuye causas exclusivas.

Los 17 viajes completados comparables de los primeros cinco vehículos
conservan orígenes/destinos; su cambio medio de duración es +0.018 s.
No atribuir el incremento del promedio de toda la flota a congestión sin
considerar los recorridos añadidos.

El histórico de diez completó **33 viajes y nueve activos al corte**, con
cero errores de integridad, bloqueos, fallos de ruta, timeout, colisiones e
invasiones. `vehicle_009` completó su tercer viaje a los 597.35 s y permanecía
en espera al corte; ese vehículo no tiene un viaje activo que abortar. Hay
120,000 observaciones y 32 ciclos completos de llegada/espera/reinicio; la
última espera está correctamente cortada por los 600 s. Tiempo medio de
completados 146.568 s, velocidad de presencia 11.125 km/h, distancia 18.541 km
y presencia bajo 0.2 m/s 35.556 %. La mayor parada continua fue 32.15 s.

La comparación de ambiente, flota, configuración y hashes entre ambos
selectores pasó. La reproducción offline de todas las decisiones con sus
semillas/historiales coincide. Son **61 llegadas y 60 ciclos completos en
240,000 observaciones**. El incremento del historial es individual y solo
añade las llegadas completadas. El piloto de veinte se inicia tras estas
comprobaciones, con los mismos parámetros y sin reiniciar CARLA.

Campaña: `data/output/pilot10_20260917/`. Baseline:
`town01_random_baseline_seed_42_20260917T180057492628Z`.
Histórico: `town01_history_80_20_seed_42_20260917T181109879090Z`.
La comparación con cinco está en `comparison_5_10/review.json` dentro de
la campaña; incluye viajes comunes, tiempos a baja velocidad y reproducción
del selector. No representa una estimación causal libre de sesgo de censura.

### Veinte: baseline y contexto de sus invasiones

Baseline de veinte completó **55 viajes y veinte activos al corte**. Pasaron
240,000 observaciones, 55 ciclos y la auditoría sin errores. Hubo cero
colisiones, bloqueos, fallos de ruta y timeout, y **dos callbacks de invasión**.
Tiempo medio completado 168.123 s; velocidad de presencia 10.595 km/h;
distancia 35.315 km; presencia bajo 0.2 m/s 38.306 %. La parada continua
más larga fue 32.70 s. El histórico de veinte también terminó; su cierre se
detalla a continuación.

Los dos callbacks son de `vehicle_011`, modelo `vehicle.tesla.cybertruck`,
`trip_003`, marca `NONE`. Se registraron a t=318.70 y 319.35 s, cerca de
(7.91, 2.83) y (11.41, 2.26), durante la misma curva. Velocidades 19.54 y
19.94 km/h; quedaban más de 170 m de ruta y el vehículo estaba en fase de
viaje. Son eventos distintos de las antiguas zonas (96,202)/(98,325) y del
frenado de llegada. El otro vehículo más cercano estaba a 56.99 y 55.19 m
entre centros, respectivamente. No hay evidencia local de una cola que
explique estos callbacks. No equivalen a dos accidentes ni acreditan una
infracción; tampoco se eliminaron por tener marca `NONE`.

El modelo aparece entre los diez vehículos añadidos. Por ello, el aumento
de incidentes respecto de las flotas menores no puede atribuirse solamente
a densidad: también cambian modelos y recorridos. El controlador permanece
igual para todos. `baseline_event_context.json` conserva el enlace exacto
evento/control/observación y las distancias a los demás carros.

![Reconstrucción de los dos callbacks del Cybertruck](../data/output/pilot20_20260917/baseline_invasions.png)

Esta figura deriva de registros; no es una captura de CARLA ni una medida
de separación física a la acera. Campaña: `data/output/pilot20_20260917/`.
Baseline: `town01_random_baseline_seed_42_20260917T182220237762Z`.

### Cierre de veinte y resumen de las cuatro corridas nuevas

Histórico de veinte: **63 llegadas, diecisiete viajes activos al corte y tres
vehículos esperando en destino**. Los vehículos 004, 009 y 014 llegaron a
t=595.55, 597.25 y 597.35 s; sus esperas no llegaron a generar otro viaje
antes del corte. Se auditaron 240,000 observaciones y 60 ciclos completos.
No hubo colisiones, bloqueos, fallos de ruta, timeout ni errores de integridad.
Carpeta: `town01_history_80_20_seed_42_20260917T183235794511Z`.

También registró **dos invasiones NONE** del Cybertruck 011/trip_003 en la
misma curva del baseline, a t=236.60 y 237.00 s. Circulaba a 19.38/19.70 km/h,
con más de 283 m restantes. El otro vehículo más cercano estaba a 41.09/44.02 m.
`history_event_context.json` conserva esos frames. Se mantienen los dos eventos
en las métricas; no se ajustó el controlador para eliminarlos.

| Vehículos / escenario | Llegadas | Activos al corte | Colisiones | Invasiones | Tiempo medio completado (s) | Velocidad de presencia (km/h) | Baja velocidad (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10 / random_baseline | 28 | 10 | 0 | 0 | 168.155 | 10.633 | 38.566 |
| 10 / history_80_20 | 33 | 9 | 0 | 0 | 146.568 | 11.125 | 35.556 |
| 20 / random_baseline | 55 | 20 | 0 | 2 | 168.123 | 10.595 | 38.306 |
| 20 / history_80_20 | 63 | 17 | 0 | 2 | 153.879 | 10.874 | 37.270 |

La presencia incluye las esperas en destino. Baja velocidad significa
<0.2 m/s. En veinte se recorrieron 35.315/36.245 vehículo-km: las tasas de
invasión fueron 0.05663/0.05518 callbacks por vehículo-km. No son accidentes
ni evidencia de diferencia estadística. Las mayores paradas continuas fueron
32.70/32.85 s; los estados semafóricos y la proximidad no se interpretan como
causas excluyentes. Se conservaron todas las paradas y los cuatro callbacks.

Llegadas por vehículo; el guion identifica vehículos ausentes de la flota de diez:

| Vehículo | 10 baseline | 10 histórico | 20 baseline | 20 histórico |
|---|---:|---:|---:|---:|
| 001 | 5 | 4 | 5 | 4 |
| 002 | 4 | 4 | 4 | 4 |
| 003 | 2 | 3 | 2 | 3 |
| 004 | 3 | 5 | 3 | 5 |
| 005 | 3 | 3 | 2 | 3 |
| 006 | 2 | 1 | 2 | 1 |
| 007 | 3 | 3 | 3 | 3 |
| 008 | 2 | 3 | 2 | 3 |
| 009 | 2 | 3 | 2 | 3 |
| 010 | 2 | 4 | 2 | 4 |
| 011 | — | — | 4 | 4 |
| 012 | — | — | 3 | 5 |
| 013 | — | — | 3 | 2 |
| 014 | — | — | 3 | 3 |
| 015 | — | — | 3 | 3 |
| 016 | — | — | 2 | 2 |
| 017 | — | — | 3 | 2 |
| 018 | — | — | 2 | 4 |
| 019 | — | — | 2 | 3 |
| 020 | — | — | 3 | 2 |

En total, las cuatro corridas nuevas contienen **179 llegadas, 175 ciclos
completos, 56 viajes interrumpidos por fin de simulación y 720,000 observaciones**.
Los cuatro ciclos restantes terminan en espera por el corte temporal. Cada
vehículo completó al menos un ciclo en cada escenario. Los historiales
históricos crecen de 300 a 333 y de 600 a 663 visitas respectivamente, sin
sobrescribir entradas ni heredar visitas entre corridas. Baseline registra
sus llegadas, pero no usa historial previo para decidir.

Las 179 llegadas cumplen los límites de velocidad, rumbo, lateralidad,
distancia y progreso; las proyecciones de carril coinciden con OpenDRIVE.
Las 235 decisiones nuevas se reprodujeron offline sin diferencias. Código,
entradas y salidas originales coinciden con sus hashes. Los pares de cada
flota pasan la comparación de condiciones. Las 111 pruebas unitarias previas
siguen respaldadas por fuentes inalteradas. El tiempo observado fue
600.20–600.45 s por corrida, cercano a 1×; esto no mide rendimiento máximo.

CARLA quedó disponible en Town01, con cero vehículos/sensores, modo asíncrono
y renderizado activo. No se reinició ni se cambió el mapa durante los pilotos.
No se hicieron commits ni cambios de conducción. Los nuevos scripts locales
solo orquestan corridas y analizan registros dentro de `data/output/`.

### Comparación 5 → 10 → 20 y siguiente etapa

![Comparación descriptiva de los tres tamaños de flota](../data/output/scaling_pilots_20260917/comparison.png)

El [informe de las seis corridas](../data/output/scaling_pilots_20260917/metrics/report.md)
y `metrics/destinations.csv` contienen las métricas y las distribuciones de
destinos asignados/alcanzados, por ID y categoría. `review/review.json`
añade reproducción de decisiones, paradas, eventos y pares de viajes comunes;
`final_integrity_checks.json` y `final_server_state.json` conservan las
comprobaciones finales. Todo está bajo `data/output/scaling_pilots_20260917/`.

Entre diez y veinte, los 27 viajes completados comparables de baseline
aumentan 2.383 s en promedio; los 33 de histórico, 2.841 s. Hay variación:
el mayor incremento individual es 40.70 s en baseline/005/trip_001 y 48.60 s
en histórico/004/trip_005. Esas medias excluyen los viajes sin pareja
completada y no constituyen estimadores causales libres de censura. Los
primeros diez conservan modelos; su fracción a baja velocidad pasa de
38.566 a 38.168 % y de 35.556 a 34.752 %. La media de toda la flota también
cambia por los modelos y recorridos añadidos. No se demuestra saturación.

La evidencia permite cerrar los pilotos técnicos de 5/10/20. Antes de fijar
las dos demandas definitivas conviene:

1. Registrar una matriz común de repeticiones y semillas para ambos selectores.
   Repetir 42 y añadir 7/123 permite revisar variabilidad; la semilla actual
   también cambia modelos y debe declararse esa limitación.
2. Validar una duración mayor bajo las flotas candidatas, conservando
   exposición, viajes censurados, incidentes y contexto de paradas.
3. Decidir si cinco y veinte dan un contraste útil para los objetivos. Pueden
   representar menor/mayor población simultánea dentro del ODD, pero no se
   han establecido como demanda urbana calibrada ni como libre flujo/saturación.
   Si se requiere ese contraste específico, habrá que investigarlo y justificarlo.

En estos pilotos de 600 s no se ejecutaron nuevas semillas ni duraciones
de 1,800 s. Posteriormente, el mismo 17 de septiembre, se completó la
[campaña larga de veinte con semillas 210/109](campana_larga_veinte_vehiculos.md):
783 llegadas, 78 viajes cortados, cero errores de integridad y 524 callbacks
de colisión agrupados descriptivamente en dos episodios de baseline.
No hubo invasiones ni bloqueos. Se mantuvo el controlador y el ritmo
solicitado fue 5× (1.730–1.832× alcanzado). La revisión visual sigue
pendiente; las figuras de registros no la sustituyen.
