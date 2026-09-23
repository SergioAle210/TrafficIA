# Campaña larga con veinte vehículos — 2026-09-17

**Completada y auditada.** Cuatro corridas de 1,800 s, veinte vehículos,
ambos selectores y semillas 210/109. Ritmo solicitado 5×; alcanzado
1.730–1.832×. Las simulaciones y sus auditorías terminaron correctamente.
Se mantuvo la conducción y no se hicieron commits.

| Semilla | Escenario | Llegadas | Activos al corte | Callbacks de colisión | Invasiones |
|---:|---|---:|---:|---:|---:|
| 210 | random_baseline | 215 | 20 | 14 | 0 |
| 210 | history_80_20 | 196 | 19 | 0 | 0 |
| 109 | random_baseline | 181 | 19 | 510 | 0 |
| 109 | history_80_20 | 191 | 20 | 0 | 0 |

Los 524 callbacks se concentran en dos episodios entre pares de vehículos;
no representan 524 accidentes independientes. No hubo `blocked`,
`route_failed`, `timeout` ni errores de integridad. Las incidencias y sus
reconstrucciones se detallan más abajo.

## Protocolo autorizado

Ampliación de los pilotos de escalamiento: semillas **210 y 109**, veinte
vehículos y ambos selectores (`random_baseline`, `history_80_20`), durante
**1,800 segundos simulados por corrida**, sin cámaras RGB. El estudiante
cambió el ritmo solicitado de 1× a **5×** al comenzar. El paso físico sigue
siendo 0.05 s; 5× limita la espera de reloj, no multiplica ese paso. La meta
es seis minutos reales por corrida, sujeta al rendimiento del equipo.

Se conserva Town01, CARLA 0.9.15, clima, puntos de inicio, controlador,
sensores de incidentes y diagnósticos de navegación. Las semillas actuales
afectan tanto los destinos como los modelos vehiculares: no aíslan una
variación exclusiva del selector. Cada pareja baseline/histórico usa la
misma semilla y flota. No se exigen cero invasiones ni cero colisiones para
considerar íntegros los registros; se investigará el contexto de los eventos.

El histórico comienza con los mismos 600 registros sintéticos de entrada
(30 por vehículo, generados previamente con semilla 42), agrega cada visita
completada y se reinicia desde esa entrada en la siguiente corrida. No se
sobrescribe el CSV inicial ni se heredan visitas entre corridas. Baseline
registra sus llegadas, pero no consulta el historial para elegir destinos.

## Evidencia y estado

Campaña: `data/output/reliability20_20260917_seeds210_109_x5/`.
Estado final: **completada**. Orden: 210 baseline, 210 histórico,
109 baseline, 109 histórico. El manifiesto `campaign.json` registra comandos,
fechas, directorios, auditorías y estados; se conservan consolas y hashes de
fuentes, entradas y salidas. Las 111 pruebas unitarias pasaron anteriormente
el mismo día; los 18 archivos congelados de código/entradas siguen idénticos.
No se ha modificado la lógica de conducción para esta campaña.

El intento previo a 1×,
`town01_random_baseline_seed_210_20260917T192849256634Z`, se interrumpió por
la petición de cambiar el ritmo. Sus archivos parciales se conservan y se
excluyen de las métricas. La interrupción dejó 20 vehículos y 40 sensores;
se limpiaron solo los IDs registrados y sus sensores adjuntos, y se restauró
el modo asíncrono antes del nuevo inicio. La comprobación previa bloqueó un
primer arranque a 5× mientras persistían esos actores; no produjo una corrida.
La evidencia de limpieza está en la campaña anterior sin sufijo `_x5`.

La auditoría comprobó duración, continuidad de frames, fases, llegadas,
historiales, exposición y asociación de eventos. Los `aborted` al corte de
1,800 s se separaron de `blocked` y otros finales. La evidencia procede de
registros: esta campaña no completa la revisión visual pendiente ni fija
por sí sola las dos demandas definitivas del estudio.

## Primer resultado: baseline, semilla 210

Corrida: `town01_random_baseline_seed_210_20260917T193138078402Z`.
Completó 1,800 s: 215 llegadas y 20 viajes activos interrumpidos al corte,
sin `blocked`, `route_failed`, `timeout` ni errores de integridad. Hay
720,000 observaciones, 215 ciclos completos y 235 decisiones reproducidas
offline sin diferencias. El archivo de visitas contiene las 215 llegadas.
El observador midió 992.734 s reales: **1.813× alcanzado**, con 5× solicitado.
El equipo no sostuvo el límite de 5× bajo esta instrumentación.

Registró **14 callbacks de colisión y cero invasiones**. Son siete frames
consecutivos registrados por ambos vehículos del mismo par, 003 y 007,
entre t=1636.80 y 1637.10 s. Se conserva el conteo bruto; no son 14 choques
independientes. 003 es Mini Cooper S 2021 y 007 Mercedes Coupe 2020.
El mapa offline sitúa el contacto en una intersección, cerca de (95, 200).
Las trayectorias muestran giros desde sentidos opuestos hacia el mismo
carril. Es un contacto entre vehículos, distinto de los contactos históricos
contra objetos estáticos en esa zona. Ambos viajes terminaron en llegada.
No se ha probado una causa interna exclusiva del controlador ni se ha
corregido su comportamiento durante esta campaña.

![Reconstrucción del contacto entre 003 y 007](../data/output/reliability20_20260917_seeds210_109_x5/seed_210_baseline_incident_01.png)

`incident_review.json` conserva participantes, eventos, muestras de control
y contexto. La agrupación descriptiva une callbacks del mismo par separados
por no más de un segundo; no cambia la métrica original. La figura muestra
registros y centros de carril, no video ni la huella exacta de los vehículos.

## Pareja completa: semilla 210

Histórico: `town01_history_80_20_seed_210_20260917T194840351325Z`.
Completó 1,800 s con 196 llegadas, 19 viajes activos cortados, cero colisiones,
invasiones, bloqueos, fallos de ruta, timeout o errores de integridad.
El vehículo 004 terminó `trip_009` a t=1797.15 s y quedó esperando: por eso
hay 19, no 20, viajes activos al corte. Se registraron 195 ciclos completos
y 720,000 observaciones; todos los vehículos tienen al menos siete ciclos.
El historial creció de 600 a **796 visitas**, sin modificar la entrada.

Las 215 decisiones históricas se reprodujeron sin diferencias: 168 de rutina
y 47 de exploración (78.14 % / 21.86 %). El 80/20 es una probabilidad por
selección, no una cuota exacta. Sumando baseline e histórico, coinciden las
450 decisiones verificadas. Los modelos, semillas por vehículo, spawns,
clima, paso físico, ritmo solicitado, planificación y control de llegada
coinciden entre escenarios. Las fuentes y entradas conservan sus hashes.

| Métrica | Baseline 210 | Histórico 210 |
|---|---:|---:|
| Viajes completados | 215 | 196 |
| Tiempo medio de viaje completado (s) | 155.49 | 168.56 |
| Velocidad media durante presencia (km/h) | 10.38 | 10.71 |
| Distancia total (vehículo-km) | 103.835 | 107.135 |
| Tiempo de presencia a menos de 0.2 m/s (%) | 39.73 | 38.37 |
| Mayor intervalo continuo a baja velocidad (s) | 32.90 | 32.95 |
| Callbacks de colisión / invasión | 14 / 0 | 0 / 0 |
| Tiempo real observado (s) | 992.734 | 994.797 |
| Multiplicador alcanzado | 1.813× | 1.809× |

Cada corrida aporta diez horas-vehículo de exposición. Menos llegadas y
mayor duración media de viaje en histórico no prueban más congestión: cambia
la distribución de recorridos; aquí, además, la velocidad media es mayor
y la fracción a baja velocidad es menor. Son resultados descriptivos de una
pareja y los viajes activos al corte están censurados.

## Baseline, semilla 109

Corrida: `town01_random_baseline_seed_109_20260917T200543832202Z`.
Completó los 1,800 s con 181 llegadas, 19 viajes activos cortados, 180 ciclos
completos y 720,000 observaciones. Sin bloqueos, fallos de ruta, timeout o
errores de integridad. Las 200 decisiones se reprodujeron sin diferencias.
El vehículo 018 llegó en `trip_011` a t=1799.50 s y terminó esperando.
El mínimo por vehículo es siete ciclos completos. Ritmo alcanzado: 1.832×.

Los **510 callbacks de colisión**, sin invasiones, corresponden al par 001
(Lincoln MKZ 2017) y 018 (Tesla Model 3): ambos sensores registraron 255
frames entre t=111.00 y 123.95 s, un episodio de contacto de 12.95 s cerca
de (92, 5), dentro de una intersección. Sus giros cruzan trayectorias: 001
llega desde el sur y gira al oeste; 018 llega desde el este y gira al sur.
Ambos iban alrededor de 18–19 km/h en el frame anterior al primer evento.
El 001 registra freno 0.5 durante el contacto y el 018 se mueve lentamente;
los registros muestran una interacción prolongada, no 510 accidentes
independientes. Ambos viajes llegaron después a su destino. La parada
continua del 001 fue 13.35 s, por debajo del umbral `blocked` de 60 s.

![Reconstrucción del contacto entre 001 y 018](../data/output/reliability20_20260917_seeds210_109_x5/seed_109_baseline_incident_01.png)

No se eliminan eventos ni se modifica la conducción para reducirlos. Este
caso refuerza que, al formalizar el objetivo de incidentes, debe diferenciarse
el callback bruto de un episodio de contacto, con regla explícita y datos
originales conservados. La agrupación descriptiva de esta revisión no se
impone retroactivamente como la definición académica definitiva.

## Histórico 109 y cierre de la campaña

Corrida: `town01_history_80_20_seed_109_20260917T202234734504Z`.
Completó 1,800 s con 191 llegadas, 20 viajes activos cortados, 191 ciclos
completos y 720,000 observaciones. Cero callbacks de colisión o invasión,
bloqueos, fallos de ruta, timeout o errores de integridad. Las 211 decisiones
coinciden con la reproducción offline: 172 de rutina y 39 de exploración
(81.52 % / 18.48 %). El historial creció de 600 a **791 visitas**.

| Métrica | Baseline 109 | Histórico 109 |
|---|---:|---:|
| Viajes completados | 181 | 191 |
| Tiempo medio de viaje completado (s) | 182.19 | 174.06 |
| Velocidad media durante presencia (km/h) | 10.36 | 10.28 |
| Distancia total (vehículo-km) | 103.554 | 102.789 |
| Tiempo de presencia a menos de 0.2 m/s (%) | 39.59 | 39.18 |
| Mayor intervalo continuo a baja velocidad (s) | 32.95 | 32.90 |
| Callbacks de colisión / invasión | 510 / 0 | 0 / 0 |
| Tiempo real observado (s) | 982.469 | 1,040.453 |
| Multiplicador alcanzado | 1.832× | 1.730× |

El balance es **783 llegadas, 781 ciclos completos, 78 viajes cortados,
861 decisiones reproducidas sin diferencias y 2,880,000 observaciones**.
Las dos llegadas sin reinicio posterior corresponden a esperas al final de
la duración, identificadas arriba. Cada vehículo de cada corrida completó
al menos siete ciclos. Todas las llegadas cumplen velocidad, orientación,
desplazamiento lateral, distancia al destino y remanente de ruta exigidos
por el controlador actual; la proyección de carril también pasó.

Se observaron **417.313 vehículo-km y 40 horas-vehículo**. Las dos parejas
pasaron comparabilidad de condiciones y controles. Entre semillas cambiaron
los modelos de 18 de los veinte vehículos: no se puede atribuir su diferencia
solo al azar de destinos. Los 18 archivos congelados y los hashes de salidas
permanecen intactos. Las cuatro corridas, incluidas las auditorías y la
comparación, ocuparon aproximadamente 69 minutos reales; el límite 5× no
garantiza que el equipo pueda avanzar a ese ritmo.

CARLA terminó disponible en `localhost:2000`, Town01, cero vehículos,
sensores o peatones, modo asíncrono y renderizado activo. No se reinició ni
se cambió el mapa. Se conservaron las modificaciones preexistentes, los CSV
de entrada y los documentos TeX. No hubo cambios de controlador ni commits.

### Dónde revisar la evidencia

La [guía de gráficas](graficas_campana_veinte.md) añade nueve láminas
de las métricas académicas y relaciones locales de tráfico, con
[PDF completo](../data/output/visual_analysis20_20260917/graficas_campana.pdf)
y [galería](../data/output/visual_analysis20_20260917/index.html).
Se generaron offline después de la auditoría, sin nuevas corridas.

Todo lo siguiente está en `data/output/reliability20_20260917_seeds210_109_x5/`:

- [Comparación de métricas](../data/output/reliability20_20260917_seeds210_109_x5/metrics/report.md),
  `metrics/summary.csv` y `metrics/destinations.csv`: métricas, exposición y
  distribuciones de destinos asignados/alcanzados por ID y categoría.
- [Llegadas por vehículo](../data/output/reliability20_20260917_seeds210_109_x5/vehicles.md)
  y `extended_review.json`: resultados individuales, modelos, reproducción
  de decisiones, contextos de eventos y comparabilidad.
- `seed_*_review/audit.json`: frames, fases, ciclos, paradas y carriles.
- `incident_review.json` y las dos figuras: los episodios descritos arriba.
- `final_integrity_checks.json`, `source_verification.json`,
  `*_output_sha256.json` y `final_server_state.json`: verificaciones finales.
- `run_campaign.py`, los scripts de análisis y sus hashes: orquestación y
  revisión conservadas junto con las consolas. El runner rechaza sobrescribir
  esta campaña terminada; una repetición debe usar un directorio nuevo.

### Interpretación y siguiente paso

Las semillas **210 y 109 son suficientes para esta ampliación exploratoria**;
no había necesidad de sustituirlas por otras. Se comprobó que veinte
vehículos pueden ejecutar 30 minutos simulados bajo las condiciones
registradas y producir datos íntegros, incluidos contactos en intersecciones.
Esto no demuestra conducción perfecta, ausencia general de incidentes ni
significancia estadística entre selectores. Tampoco prueba repetibilidad
física exacta: cada semilla/escenario se ejecutó una vez.

Antes de fijar las dos demandas definitivas conviene cerrar el protocolo:

1. Definir explícitamente la unidad de incidente: conservar callbacks y,
   si se añade una métrica por episodio, predefinir agrupación, participantes,
   duración y normalización por exposición. El episodio de 12.95 s muestra
   por qué el conteo bruto depende también de persistencia y sensores.
2. Ejecutar una repetición de condiciones idénticas para comprobar la
   repetibilidad física, y comparar las flotas candidatas con la misma
   duración, semillas e historiales iniciales. Cinco y veinte siguen siendo
   candidatos; no se declaran aquí como libre flujo o saturación.
3. Justificar las dos poblaciones simultáneas a partir del contraste de
   exposición, viajes y paradas, dentro del ODD académico. Cambiar semillas
   arbitrariamente o perseguir cero incidentes no resuelve esa justificación.

La revisión visual con cámaras sigue pendiente. Las figuras de registros
de esta campaña no la sustituyen.
