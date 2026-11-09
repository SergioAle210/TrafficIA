# Bitácora de simulación y validación

Este archivo conserva el contexto técnico entre sesiones. En cada ajuste del
runner o del controlador, añadir fecha, síntoma, evidencia, causa confirmada o
hipótesis, archivos afectados, pruebas realizadas, rutas de resultados y
limitaciones pendientes. No reemplazar resultados antiguos ni presentar pruebas
unitarias como validación de física real.

## 2026-09-28 - Revisión de archivos y exclusión de imágenes de Git

Se revisaron el estado de Git, los scripts, las referencias de configuración
y las reglas de exclusión. Se añadió `/images/` a `.gitignore`: la colección
generada, su galería, catálogo y fragmentos LaTeX quedan locales. No tenía
archivos versionados, por lo que no fue necesario modificar el índice de Git.
Se conservaron las exclusiones de resultados, entorno virtual y cachés.

README documenta qué conservar: implementación, pruebas, configuraciones,
manifiestos e historiales de entrada, análisis y generadores de gráficas.
No se añadió una exclusión global de CSV ni se modificaron entradas o TeX.
Se recomienda separar la redacción académica en Trabajo-Profesional, sin
mover ni retirar archivos en esta revisión. El diagnóstico de detenciones
sigue siendo experimental y la comparación de 300 s permanece pendiente.

Verificación con `git check-ignore`: `images/` queda excluida y los scripts,
entradas, configuración, documentación y `data/output/.gitkeep` permanecen
disponibles para versionarse. Las fuentes históricas de las figuras requieren
respaldo separado: el generador no las reconstruye solo a partir del código.
No se ejecutó CARLA ni se hicieron commits.

## 2026-09-23 - Colección de imágenes para resultados y LaTeX

El estudiante solicitó reunir las figuras de 3/5/10/20 y 20/100 vehículos,
incluidas las dos campañas de 3600 s, con nombres entendibles y sin adoptar
`blocked` como métrica académica. Se creó `images/`: 59 figuras de resultados
y 18 de respaldo técnico (77 PNG y 56 SVG), organizadas por etapa, duración,
semilla y repetición. Las láminas de blocked/fallos se conservan como respaldo
opcional y están ocultas inicialmente en la galería; no se borraron originales.

Se copiaron 68 figuras y se generaron nueve: dos resúmenes por piloto 3/5/10/20
(tiempo/velocidad/tasas y categorías de destinos), más una comparación de las
dos repeticiones de 3600 s sin panel blocked. Los resúmenes parten de análisis
auditados; las poblaciones de completados e incompletos siguen explícitas.
La repetición 1 es la noche local 21-22 septiembre y la 2 la noche 22-23.

`images/README.md` incluye índice, método, procedencia y uso sugerido;
`images/index.html` ofrece búsqueda y filtro; `images/figuras_resultados.tex`
contiene 59 fragmentos independientes y `catalogo.json` registra hashes.
Verificación: 133 archivos de imagen, fuentes y copias cotejadas, PNG legibles,
SVG válidos y 59 referencias LaTeX existentes. Revisión visual de los nueve
resúmenes nuevos; se corrigió el solapamiento de etiquetas de la comparación.
Registro: `data/output/results_images_collection_20260923/validation.json`.

Sin CARLA, sin nuevas corridas, sin cambios a documentos TeX ni commits.
Se excluyen duplicados de QA, frames RGB y smoke tests de la selección.
Se preserva la nube antigua sin guías como antecedente; el cuerpo de resultados
usa la versión con guías. Generador: `scripts/prepare_results_images.py`.

## 2026-09-23 - Comparación diagnóstica de detenciones

Se implementó `--blocked-policy terminate|keep_trip` con `terminate` por defecto.
La alternativa avisa a 60 s sin superar 0.2 m/s y mantiene el viaje/destino;
solo las llegadas completadas aumentan el historial. No se cambia controlador.
El nuevo seguimiento usa el espectador de CARLA, sin cámaras, y registra las
decisiones originales del agente sin ejecutar detectores adicionales. Se
distinguen avisos, terminaciones y episodios físicos a través de reintentos.

Validación inicial: 142 pruebas pasaron con carla-env/CARLA_PYTHONAPI. CARLA
0.9.15 respondió en Town01 limpio, asíncrono y con renderizado tras prepararlo
el estudiante. Se inicia prueba técnica de 15 s y se preparan dos corridas de
300 s (100 vehículos, baseline, semilla 210, 1x). [Detalles y cierre](diagnostico_blocked.md).
Conservar TeX y resultados anteriores. Sin commits.

Cierre provisional: la técnica alcanzó 15 s y 30,000 observaciones íntegras,
cero incidentes y 100 `aborted` por fin de simulación. El estudiante confirmó
vista clara. CARLA confirmó limpieza de actores, pero falló después durante
el cierre de campaña: assert `DXGI_ERROR_INVALID_CALL` en D3D11Query.cpp:356,
GPU Intel UHD Graphics 770, sin marca de OOM. Campaña conservada como
incompleta: `data/output/blocked_comparison_20260923T235312623044Z/`.
No se ejecutaron las dos corridas de 300 s. Causa del fallo gráfico no
aislada; no atribuirlo a blocked ni afirmar que quitar cámaras lo resuelve.
Se pidió al estudiante preparar otra vez CARLA/Town01. Suite final: 144
pruebas pasan; falta validar las políticas en corridas reales con avisos.

## 2026-09-23 - Gráficas y comparación de segunda campaña de 3600 s

Campaña `demand20_100_seed_210_20260923T045032867422Z`, iniciada el 22 a las
22:50 y terminada el 23 a las 06:10, hora local. Cuatro corridas completas;
20/100 vehículos, semilla 210, 3600 s, 5x solicitado y sin cámaras.
[Resultados y comparación](repetibilidad_demandas_3600.md). Derivados en
`data/output/visual_analysis20_100_3600_repeat_20260923/`.

Se reauditaron ambas campañas: 104 hashes de salida, instantáneas válidas,
27 archivos de código/entradas idénticos y condiciones comparables.
Veinte: 423/398 llegadas, cero blocked/route_failed, 12/0 callbacks de
colisión y 0/0 invasiones. Cien: 237/254 llegadas, 4154/4152 blocked,
804/235 route_failed, 542630/51473 callbacks y 72/8 invasiones.
Los grupos descriptivos de contacto con cien son 396/45; no accidentes
independientes. El patrón agregado persiste pero los incidentes no se
reproducen exactamente. Causa de divergencia no determinada en este análisis.

Se añadió `scripts/campaign_comparison.py` y opción `--compare-data` al
exportador para tablas y dos láminas comparativas. El emparejamiento verifica
cantidad/selector/semilla y condiciones; el porcentaje con base cero queda
indefinido. Tres pruebas de regresión nuevas: emparejamiento fuera de orden,
base cero y rechazo de datos incompatibles. 135 pruebas pasaron con
carla-env/CARLA_PYTHONAPI. No se cambió conducción ni blocked; no se ejecutó
CARLA ni se hicieron commits. README y contexto académico actualizados;
figuras anteriores y documentos TeX del estudiante conservados.

Cierre de validación: 17.28 millones de observaciones, 9120 celdas,
4253 ocupadas, 33 bandas guía con soporte; conservación y q=k*v verificadas.
Los 44 deltas entre campañas y hashes de sus entradas coinciden. Catorce
páginas renderizadas y revisadas. Segunda mitad de cien aleatorio: 17
llegadas y 0.196 km/h, frente a 46 y 0.628 en la primera campaña.
Muestras fuera de proyección driving: 293857 frente a 102060; permanecen
en registros y series globales, excluidas solo de las celdas locales.

## 2026-09-22 - Gráficas de la campaña de 3600 segundos

El estudiante terminó las cuatro corridas de `demand20_100_seed_210_20260922T040147250610Z`
en 7 h 17 min aproximadamente. Se validaron 52 hashes y la instantánea de
fuentes; auditorías y métricas recalculadas sin errores, parejas comparables.
[Resultados y límites](graficas_demandas_3600.md). Nuevos derivados en
`data/output/visual_analysis20_100_3600_20260922/`; resultados previos intactos.

Se corrigieron etiquetas de duración, fecha y porcentajes históricos en
`plot_demand_campaign.py`. Histograma ahora conserva ventanas de 60 s:
31 bordes fijos habrían dado 120 s por ventana para esta duración.
`tests/test_demand_plotting.py` comprueba duración, límites y ventana parcial.
Se añadió comparación de mitades con medias ponderadas por exposición,
identificando desfase de 0.05 s de las ventanas. No son réplicas independientes.
La suite completa, con CARLA_PYTHONAPI, pasó 132 pruebas. La primera ejecución
sin esa variable omitió pruebas del SDK; se repitió correctamente. Pytest no
está instalado; la suite del proyecto usa unittest y no se instalaron paquetes.

Con veinte: 422/397 llegadas, cero blocked/route_failed/colisiones y 2/0
invasiones. Con cien: 252/252 llegadas, 3932/4147 blocked, 1280/235 route_failed,
160955/77904 callbacks de colisión y 30/17 invasiones. Los grupos descriptivos
de contacto (173/65) no equivalen a accidentes independientes. El próximo
paso sigue siendo investigar primeras secuencias de bloqueo/rechazo/contacto,
sin exigir cero incidentes. No hubo simulaciones nuevas, cambios de conducción
ni commits en esta entrega. README y contexto académico actualizados.

Cierre: 9120 celdas, 4437 ocupadas, 37 bandas guía con soporte. Conservación
de exposición/distancia y recuentos verificada. Doce páginas renderizadas y
revisadas; leyenda de la lámina 12 ajustada para no ocultar valores. En la
segunda media hora, cien baja a 0.63/0.80 km/h y produce 46/67 llegadas,
frente a 206/185 en la primera; veinte mantiene 215/207 y 195/202 llegadas.
No se infiere automáticamente causa ni capacidad del mapa.

## 2026-09-20 — Explicación y líneas guía de relaciones de tráfico

El estudiante compara la nube con dos esquemas teóricos y solicita una guía
visual y valoración del avance. Se consultó FHWA (metodología, sección 3)
para distinguir identidad q=k*v, forma funcional y calibración estacionaria.
Las imágenes aportadas muestran hipótesis distintas; una relación lineal
v(k) produce una parábola q(k), mientras otra referencia incluye q(k)
triangular. La orientación de ejes q/v también cambia entre imágenes.

Se añadió `density_band_guides` a `src/traffic_flow_analysis.py` y se adaptó
`scripts/plot_demand_campaign.py`. Por cada corrida se agrupan celdas ocupadas
en bandas fijas de 10 veh/km/carril; se suman S, D y A=L*T para obtener
k=1000S/A, q=3600D/A y v=3.6D/S. Se conservan los triples en los tres paneles,
ordenados por densidad. Se trazan solo bandas con diez o más celdas y se
interrumpe al faltar soporte; parámetros de visualización, no significancia.
No se extrapola ni se ajusta forma. q=k*v se garantiza en los marcadores,
no en cada punto de sus uniones visuales. Se mantienen los puntos originales.

Nueva salida: `data/output/visual_analysis20_100_guides_20260920/`, con
once PNG/SVG, PDF/HTML actualizados, `flow_guides.csv`, `guide_method.json`
y copias con hashes de los insumos del día 19. La salida anterior permanece
intacta. La lámina 09 tiene 3/4/9/8 marcadores con soporte según corrida;
los restantes resúmenes se conservan en CSV. No se releen millones de filas
ni se ejecuta CARLA: se usan los mismos 4,560 registros de celdas derivadas.

Pasaron 130 pruebas con carla-env, cuatro nuevas de ponderación/identidad,
bandas escasas o ausentes, fronteras, celdas vacías/paradas y entradas inválidas.
Se renderizó e inspeccionó la página modificada del PDF. Se documentaron
procedimiento, lectura y límites en [la guía nueva](lectura_diagramas_y_guias.md),
README y contexto académico. Las 78.14 %/79.18 % decisiones de rutina son
cercanas al 80 % esperado; no implican una cuota exacta ni validación del
diagrama. Sigue pendiente explicar los bloqueos/contactos de cien antes
de calibrar capacidad o fijar la demanda definitiva. Sin commits ni cambios
en conducción, simulación, TeX o CSV originales.

## 2026-09-19 — Gráficas de la campaña 20/100 ejecutada el día 18

El estudiante terminó la campaña y solicita regenerar las figuras con las
dos cantidades. Se identificó
`data/output/demand20_100_seed_210_20260918T190119084914Z/campaign.json`:
estado completed, cuatro casos de 1,800 s, semilla 210, ambos selectores.
Se verificaron 52 archivos originales contra sus hashes y la instantánea de
fuentes, y se recalcularon las métricas: sin errores, parejas comparables.
No se creó cliente CARLA ni se avanzó la simulación.

La [guía nueva](graficas_demandas_20_100.md) enlaza once láminas PNG/SVG,
PDF, galería HTML, CSV y manifiestos en
`data/output/visual_analysis20_100_20260919/`. Se preservó la galería anterior.
`build_campaign_plot_data.py` ahora procesa observaciones por bloques y
calcula hashes por bloques para evitar cargar millones de filas/bytes en
RAM; incorpora cantidad de vehículos a las salidas. Se conserva la misma
selección de 38 tramos de 50 m y ventanas de 60 s. La plantilla anterior
era específica de veinte y semillas 210/109: se añadió
`plot_demand_campaign.py` para cantidades distintas con una semilla, sin
reutilizar títulos, cifras fijas ni etiquetas de cortes de aquella campaña.

`review_demand_chart_inputs.py` verifica entradas y resume historiales,
estados y episodios. `src/incident_analysis.py` agrupa callbacks por par
de actores y separación máxima consecutiva de 1 s; no sustituye la métrica
bruta ni define accidentes. Pasaron 126 pruebas, incluidas tres para
sensores opuestos, parejas diferentes, IDs ambiguos y tiempos inválidos.

Veinte/baseline: 215 llegadas, 155.49 s de media completa, 10.38 km/h,
18 callbacks de colisión. Veinte/histórico: 196, 168.59 s, 10.71 km/h,
cero eventos. Cien/baseline: 173 llegadas, 173.97 s, 2.47 km/h, 1,673
blocked, 340 route_failed, 48,814 callbacks de colisión y siete invasiones.
Cien/histórico: 183, 204.47 s, 2.55 km/h, 1,787 blocked, 77 route_failed,
19,768 callbacks y tres invasiones. Los 20/19/87/90 aborted son cortes
simulation_end, separados de bloqueos y rutas rechazadas. Total: 767
completados de 4,860 intentos. Un vehículo puede acumular muchos intentos.

Los contactos forman 1/0/57/15 grupos descriptivos; 24 grupos tienen ID
ajeno no positivo y pueden mezclar objetos estáticos. Las consolas explican
los rechazos de cien/baseline: 129 inicios de ruta demasiado lejos del origen
y 211 distancias excesivas al carril. Cien/histórico: 73 inicios desalineados
y cuatro rutas sin tramo anterior al destino. No se investigó aún la
secuencia física causante de esas posiciones.

Las once páginas del PDF fueron renderizadas e inspeccionadas. Las láminas
separan incompletos, tasas por exposición, decisiones sin llegada y crecimiento
de historial. Se corrigió una etiqueta analítica: dwell significa sin viaje
activo e incluye pausas tras fallos, no exclusivamente espera en destino.
Histórico crece 600→796 y 3,000→3,183; rutina 78.14 %/79.18 %.

Se derivaron 8,640,000 observaciones, 4,560 celdas, 2,330 con presencia y
sin huecos entre frames. El primer intervalo no observado suma 1/1/5/5
vehículo-segundos; no se inventa. Cien/baseline tiene 47,648 muestras fuera
de proyección driving; las demás cero. Se conserva esa limitación y las
transiciones entre road/lane. Error máximo q-k*v: 1.14e-13. Densidad máxima
con cien: 140 vehículos/km/carril, sin interpretarla como densidad crítica.
La media de velocidad de las últimas cinco ventanas es 0.529/0.223 km/h
con cien, con 96.28/98.52 % de presencia bajo 0.2 m/s. Esto es deterioro
grave de circulación, pero no demuestra una rama congestionada estable.

Pendiente: reconstruir primeras secuencias de bloqueo/contacto/rechazo antes
de decidir cien como demanda mayor definitiva o nuevos pilotos intermedios.
Después, réplicas con más semillas. No se cambió conducción, no se ejecutaron
simulaciones ni commits, y se preservaron TeX, CSV originales y cambios
anteriores. README, contexto, fundamento y guía de campaña actualizados.

## 2026-09-18 — Preparación directa de la campaña 20/100

El estudiante solicita probar directamente veinte como carga menor y cien
como mayor, semilla 210 y ritmo 5×; ofrece dejar ejecutándose los comandos.
Se prepara una campaña secuencial de ambos selectores, 1,800 s por caso,
sin cámaras. Este encargo sustituye el barrido intermedio como siguiente
acción. La duración coincide con la ampliación previa de veinte; no acredita
equilibrio ni suficiencia estadística. Detalle y comando en
[campaña de 20/100](campana_demanda_20_100.md).

Se verificó CARLA cliente/servidor 0.9.15 en localhost:2000, Town01 limpio y
asíncrono. `prepare_demand_campaign.py` crea configuraciones separadas,
historial de 3,000 visitas y manifiesto geométrico/hashes. Cien conserva
spawns e historiales de veinte; mínima separación entre centros 16.1605 m.
La semilla inicial de historiales sigue siendo 42; la de ejecución es 210.
Baseline no usa el bootstrap. `run_demand_campaign.py` comprueba entradas,
mapa y limpieza, fija el clima anterior común, guarda fuentes/entradas,
ejecuta y audita cada caso, y restaura el mundo al terminar. Los eventos y
viajes incompletos no se convierten en fallos técnicos automáticamente.

Antes de escalar se confirmó en `visual_review.py` que se conservaban en RAM
todas las observaciones incluso sin cámaras: 3.6 millones de filas para
cien durante 1,800 s. Se eliminó esa copia exclusivamente en modo sin RGB;
el CSV y los contadores permanecen. `audit_observation_stream.py` comprueba
las observaciones de forma secuencial. No se modificaron decisiones de
conducción: runner, planificador y agente coinciden byte a byte con la
instantánea de `reliability20_20260917_seeds210_109_x5/source_snapshot/`.

El primer ensayo de 15 s de veinte terminó físicamente y limpió CARLA, pero
falló el auditor nuevo porque `arrival_log.csv` no existe antes de la primera
llegada. Se conservó ese intento como `incomplete`, se corrigió el auditor
para aceptar ausencia solo cuando no hay completados y se añadió regresión.
Resultados iniciales: `data/output/demand20_100_technical_20260918/`.

Pasaron 123 pruebas con `carla-env`. La campaña técnica corregida,
`data/output/demand20_100_technical_20260918_v2/`, completó cuatro casos de
15 s: 6,000/6,000/30,000/30,000 observaciones, cero errores de integridad,
cero eventos y parejas comparables. Veinte no completó viajes en ese período;
cien histórico completó uno y aumentó su historial de 3,000 a 3,001 visitas.
Los 20/20/100/100 viajes restantes se cortaron por `simulation_end`, no
`blocked`. Tiempos reales de proceso 11.891/11.796/53.344/53.969 s, incluidos
preparación y cierre; no se extrapolan a rendimiento estable. Se crearon
y retiraron cien vehículos en ambos selectores. Estado final: Town01,
cero vehículos/sensores/peatones, asíncrono, clima y renderizado restaurados.

La campaña larga queda lista para el estudiante, **aún sin ejecutar**.
Después corresponde auditar sus cuatro casos, ampliar gráficas de métricas
y relaciones locales de tráfico, investigar incompletos/colas y decidir
réplicas o demandas intermedias. Cien no se etiqueta como saturación por
su cantidad. README, fundamento y contexto académico quedan actualizados.
Se conservan modificaciones anteriores; sin commits ni cambios a los TeX
o CSV genéricos. Log de pruebas:
`data/output/demand_preparation_20260918/unit_tests_final.txt`.

## 2026-09-17 — Referencias para justificar las dos demandas

El estudiante solicita una justificación bibliográfica o experimental para
las cantidades, considerando equipo, mapa y diagramas de tráfico, e informa
que CARLA/Town01 están listos. Se verificó cliente/servidor 0.9.15, Town01,
cero vehículos/sensores/peatones, modo asíncrono y renderizado activo.
Solo consultas: no se avanzaron frames ni se crearon actores.

La [investigación](fundamento_demandas_town01.md) contrasta NoCrash, FHWA 2019,
benchmark de rendimiento de CARLA y diagramas macroscópicos urbanos. Se
verificó por descarga de código de CARLA, commit
`1614d19581d43eac9966e4001611cc8341bf5319`, que sus cargas son 20/100 para
Town01 y 15/70 para Town02. Se documentan versión 0.8.4, peatones y vehículo
protagonista como diferencias frente a TrafficIA; no se copian etiquetas
de congestión ni se afirma el origen de los antiguos 20/70 de Town03.

Propuesta todavía no adoptada: menor veinte, mayor con referencia cien,
explorando 30/40/60/80/100 y congelando la pareja después de los pilotos.
La regla usa antecedente bibliográfico y viabilidad ensayada; incidentes no
son criterio de descarte. La capacidad computacional y la vial se miden
por separado. El ritmo 1.730–1.832× de veinte no prueba su máximo.

Se revisaron 255 spawns proyectados en carril driving fuera de cruces.
La extensión espacial conserva los primeros veinte; cien candidatos tienen
16.16 m de separación mínima entre centros. Es geometría, no prueba de
creación o circulación. Se midieron 24 procesadores lógicos y 31.77 GiB
de RAM física. WMI denegó datos detallados de CPU/GPU; no se infiere una
GPU activa. Evidencia en `data/output/demand_basis_20260917/`.

Se actualizaron README, contexto y documento previo de selección, conservando
sus antecedentes. No hay nuevas corridas, cambios del controlador, ajustes
del mundo ni commits. El siguiente experimento propuesto es el escalón de
treinta con historial completo, ambos selectores, semilla 42 y 600 s a 5×
solicitado. El barrido y confirmación larga siguen pendientes.

## 2026-09-17 — Gráficas de objetivos y relaciones de tráfico

El estudiante solicita visualizar sus métricas y explorar los diagramas
velocidad–densidad, flujo–densidad y velocidad–flujo de una imagen conceptual.
Se analizaron offline las cuatro corridas largas de veinte, semillas 210/109,
sin ejecutar CARLA, modificar el controlador ni reescribir logs originales.
Se entregan nueve láminas PNG/SVG, PDF, galería HTML y CSV derivados en
`data/output/visual_analysis20_20260917/`. La
[guía de lectura](graficas_campana_veinte.md) relaciona las figuras con los
objetivos y explica sus límites; el paquete conserva método y manifiestos.

El nuevo módulo `src/traffic_flow_analysis.py` divide trayectorias en celdas
espacio-temporales y calcula medidas compatibles de Edie. El script
`scripts/build_campaign_plot_data.py` selecciona geometría recta de Town01
fuera de intersecciones usando OpenDRIVE offline: 38 tramos completos de
50 m, ventanas de 60 s y última ventana con su duración real. Se incluyen
paradas y esperas. Se conservan 4,560 celdas, 2,458 con presencia; cero huecos
de observación. Se cuantifican transiciones de carril/carretera excluidas,
primer intervalo no observado y pequeños desplazamientos en reversa.
La identidad q=k*v tiene error numérico máximo menor que 1e-12; cumplirla
no demuestra que exista una curva fundamental calibrada.

`scripts/plot_mobility_campaign.py` exporta las cuatro métricas del objetivo 3,
tiempos censurados separados, destinos asignados/alcanzados, historial creciente,
ramas 80/20, nubes locales y cobertura. Se distingue callback de episodio:
524 callbacks pertenecen a dos contactos persistentes; cero invasiones.
El tiempo medio cambia en sentidos opuestos entre semillas. La nube muestra
velocidades menores en celdas más densas, con pocas observaciones altas;
no permite estimar capacidad ni fijar las dos demandas. Los veinte vehículos
globales no equivalen a la densidad local de un carril.

Pasaron 118 pruebas con `carla-env` y SDK, incluidas siete nuevas sobre
unidades, conservación en fronteras, detenciones, reversa y ventana parcial.
Se inspeccionaron las nueve imágenes. README y contexto académico enlazan
los resultados; no se hicieron commits ni se modificaron los documentos TeX.
Quedan pendientes repeticiones y comparación de cantidades simultáneas con
las mismas duraciones, semillas y definiciones de medición.

## 2026-09-17 — Campaña larga de veinte: semillas 210 y 109

Se autorizan cuatro corridas de 1,800 s simulados, ambos selectores y veinte
vehículos, conservando el controlador. Al inicio el estudiante solicita
cambiar 1× por 5×. Se conserva el intento parcial a 1×, se limpian sus actores
residuales por ID y se inicia una campaña independiente a 5×. No se cambia
el paso físico de 0.05 s ni se reinicia CARLA o Town01. Las entradas de
historial se conservan; cada corrida acumula solo sus propias llegadas.

Protocolo, limitaciones y resultados en
[campaña larga de veinte](campana_larga_veinte_vehiculos.md). Evidencia en
`data/output/reliability20_20260917_seeds210_109_x5/`. Estado: completada.
Las semillas varían también la flota, que se registra por vehículo. Sin
cambios de conducción ni commits; se conservan archivos previos y TeX.

Las cuatro corridas terminaron los 1,800 s. Llegadas baseline/histórico:
215/196 con 210 y 181/191 con 109; activos cortados: 20/19 y 19/20.
Total: 783 llegadas válidas, 781 ciclos completos, 861 decisiones reproducidas,
2,880,000 observaciones y cero errores de integridad. No hubo blocked,
route_failed, timeout ni invasiones. Baseline registró 14 y 510 callbacks
de colisión: dos episodios entre 003/007 (0.30 s, cerca de 95,200) y 001/018
(12.95 s, cerca de 92,5), respectivamente. Son contactos entre vehículos
en intersecciones, no 524 accidentes independientes ni objetos estáticos.
Todos los viajes implicados llegaron después. Histórico no registró eventos.

Los historiales crecieron de 600 a 796/791 visitas. Ambas parejas conservan
modelos, spawns, clima, paso y controlador; entre semillas cambian 18 modelos.
Las salidas y los 18 archivos congelados conservaron sus hashes. El ritmo
real fue 1.730–1.832× con 5× solicitado, unos 69 minutos para la campaña.
CARLA quedó en Town01, asíncrono, renderizado activo y cero actores de prueba.
Pasaron las comprobaciones numéricas de llegada y proyección de carriles;
las 111 pruebas unitarias previas del mismo día siguen referidas a fuentes
idénticas, sin nueva modificación de conducción. Las figuras reconstruyen
logs y no completan la revisión visual. Faltan definición formal de episodio,
repetición de condiciones idénticas y comparación de demandas candidatas.

## 2026-09-17 — Revisión del controlador antes del piloto de diez

El estudiante preguntó si las correcciones sesgan las tasas de incidentes.
Se revisaron commits, código, resultados anteriores y criterios de eventos.
La síntesis [control e incidentes](control_e_incidentes.md) detalla el detector
colineal, `distance_ratio` 0.5 → 0.1, aproximación y alineación de llegada,
comparaciones y límites. Sí afectan las métricas: estas describen el generador
con ese controlador común, no un efecto aislado del selector. No se cambió
la conducción ni se filtraron registros para responder esta consulta.

Se autorizó el piloto de diez en ambos escenarios, semilla 42, 600 s a 1×,
sin cámaras, con entradas ya preparadas. El estudiante prepara el servidor
con `CarlaUE4.exe -quality-level=Low -dx11 -RenderOffScreen` y Town01.
La primera comprobación de `localhost:2000` agotó ocho segundos de timeout;
todavía no acredita mapa ni permite iniciar las corridas. Se pidió aviso de
disponibilidad. La suite offline pasó 111 pruebas con `carla-env` y la SDK.
La preparación queda registrada en `data/output/pilot10_20260917/`.
Veinte sigue pendiente. No se hicieron commits ni cambios a los CSV de entrada.

### Inicio autorizado de los pilotos de diez y veinte

El estudiante autorizó ejecutar diez y después veinte conservando el modelo.
La nueva comprobación encontró CARLA 0.9.15 en Town01, cero vehículos,
sensores y peatones, modo asíncrono y renderizado activo. El clima coincide
con el piloto de cinco (precipitación 40, mojado 80 y resto de campos).
La orden de arranque Low/DX11/RenderOffScreen procede del estudiante; la
consulta de la línea de proceso por Windows no estuvo disponible y no se
presenta como verificada. La API sí confirma el estado del mundo.

Se ejecutan ambos selectores por flota, 600 s, 1×, semilla 42, sin cámaras,
con sensores de incidentes activos y diagnósticos. Se congelan fuentes y
entradas antes de correr; la conducción y los umbrales permanecen iguales.
El script local `data/output/pilot10_20260917/run_pilots.py` conserva consolas,
manifiestos, hashes y auditorías. No exige cero incidentes ni un mínimo de
llegadas para considerar íntegros los registros. Se revisará diez antes de
iniciar veinte; un fallo técnico conserva la carpeta y detiene la secuencia.

### Cierre de diez y paso a veinte

Ambos escenarios de diez completaron 600 s y pasaron auditorías y comparación
de condiciones. Baseline: 28 completed / 10 aborted. Histórico: 33 completed /
9 aborted; el 009 estaba en espera tras llegar a t=597.35 s. No hubo blocked,
route_failed, timeout, colisiones, invasiones ni errores de integridad.
Se conservaron 240,000 observaciones, 61 llegadas y 60 ciclos completos; el
último ciclo del 009 queda cortado por la duración. La reproducción offline
de las decisiones no presenta diferencias. Los hashes permanecen intactos.
CARLA quedó limpio antes de comenzar veinte. Detalle y nombres de corrida en
[pilotos de escalamiento](pilotos_escalamiento.md).

### Cierre de veinte y balance de la etapa

Baseline de veinte: 55 completed / 20 aborted / 2 invasiones / 0 colisiones.
Histórico: 63 completed / 17 aborted / 2 invasiones / 0 colisiones; 004, 009 y
014 estaban en espera después de llegar a t=595.55, 597.25 y 597.35 s.
Ambos avanzaron 600 s y pasaron auditoría y comparación de condiciones, sin
blocked, route_failed, timeout o errores de integridad. El tiempo del observador
fue aproximadamente 600.42/600.45 s, con ritmo limitado a 1×.

Los cuatro callbacks de invasión son del Cybertruck 011 en su tercer viaje,
marca NONE, en la curva cerca de (8–11, 2–3). Baseline: t=318.70/319.35 s;
histórico: t=236.60/237.00 s. Circulaba cerca de 20 km/h, con más de 170/283 m
de ruta restante. Los otros vehículos más cercanos estaban a más de 55/41 m.
Los registros no respaldan atribuirlos a una cola cercana o al frenado de
llegada. Los eventos se conservan y no equivalen a accidentes/infracciones.
El Cybertruck forma parte de los modelos añadidos: población, modelos y
recorridos cambian conjuntamente al ampliar la flota.

Las cuatro corridas nuevas suman **179 llegadas, 175 ciclos completos, 56
interrupciones por fin de simulación y 720,000 observaciones**. Las cuatro
esperas restantes quedaron cortadas por duración. Cada vehículo tiene al
menos un ciclo completo por escenario. Las 179 llegadas cumplen umbrales y
las proyecciones de carril coinciden con el mapa. Las 235 decisiones se
reprodujeron sin diferencias. Historiales históricos finales: 333 y 663
visitas; entradas y fuentes intactas, comprobadas por SHA-256. Pasaron las
111 pruebas previas y no hubo cambios posteriores de conducción.

Campañas completas: `data/output/pilot10_20260917/` y
`data/output/pilot20_20260917/`. La comparación con cinco, auditoría final,
distribuciones y figura están en `data/output/scaling_pilots_20260917/`.
El informe de pilotos identifica las cuatro carpetas de corrida originales,
resultados individuales y contexto de eventos. Se revisaron las figuras de
comparación y reconstrucción de la curva; no son capturas del simulador.

Entre diez y veinte, los viajes completados comparables aumentan 2.383 s
en promedio en baseline (27 pares) y 2.841 s en histórico (33 pares), con
incrementos individuales de hasta 40.70/48.60 s. Ese subconjunto excluye los
incompletos y no es una estimación causal libre de censura. Los resultados
no prueban saturación ni superioridad estadística. Siguen repeticiones,
otras semillas y mayor duración antes de elegir las demandas definitivas;
no se ejecutaron esas ampliaciones en esta etapa.

La comprobación final encontró Town01, cero vehículos/sensores, modo
asíncrono y renderizado activo. No se reinició CARLA ni se cambió el mapa.
Se actualizaron README, informe de pilotos, seguimiento de la revisión de
tres y contexto académico. Sin commits, sin tocar CSV de entrada o LaTeX.

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

## 2026-09-08 — Diagnóstico de las dos invasiones durante llegada y arranque

**Alcance autorizado:** reproducir y medir antes de modificar la conducción.
No se hicieron commits. La corrección propuesta al final de esta entrada
todavía no está implementada. Se conservaron los CSV anteriores y los cambios
ajenos de `i-marco_teorico.tex`.

### Instrumentación y condiciones

Se comprobó CARLA 0.9.15 en `localhost:2000`, Town01, sin vehículos ni sensores.
El clima coincidía exactamente con la última validación. Se mantuvieron tres
vehículos, spawns `[133, 6, 101]`, semilla 42, modelos/colores, delta 0.05 s,
objetivo 20 km/h, `controller_distance_ratio=0.1`, llegada a 4 m y espera de
5 s. Se ejecutaron secuencialmente ambos escenarios durante 600 s simulados,
con `--simulation-speed 5 --no-rendering`. Se mantuvo no-rendering entre
corridas y al terminar se restauró el renderizado que estaba activo al inicio.

Se añadió `scripts/diagnose_destination_dwell.py`: subclase de observación
que delega en el runner existente, sin sobrescribir frenado, inicio del viaje,
contabilidad ni controles. Captura cada frame dentro de 25 m de T01_067,
incluyendo la espera y el frame en que se cierra el viaje. No se modificaron
`src/trip_runner.py`, `src/route_planner.py`, `src/carla_agent.py` ni sus parámetros.
Los hashes SHA-256 de esos archivos se guardaron por corrida y se verificaron
después del análisis.

Archivos adicionales por corrida:

- `dwell_log.csv`: fases antes/después de actualizar el viaje, contexto de
  viaje durante espera, pose, velocidad, dirección/freno ya aplicados, carril,
  orientación y huellas del vehículo. El control observado corresponde al
  frame recibido; `control_log.csv` conserva la orden para el siguiente tick.
- `dwell_geometry.json`: carriles/marcas cada 0.25 m, waypoint proyectado de
  T01_067 y cajas de los tres modelos. El destino proyectado es
  `(2.0284, 318.6042)`, road 20/lane -1, ancho de carril 4 m.
- `dwell_diagnostic_config.json`: semántica, alcance y hashes del código.

Se añadieron seis pruebas del observador: huella usada por el sensor,
delegación de conducción/contabilidad, registro de transición a espera,
observación sin viaje activo, actualización fuera de la zona y cierre del
archivo ante interrupción. **70 pruebas correctas, sin skips**, con
`carla-env` y `CARLA_PYTHONAPI`. Los comandos completos están en README.

### Reproducción real

| Medida | random_baseline | history_80_20 |
|---|---:|---:|
| Iniciados / completados / aborted | 14 / 11 / 3 | 14 / 11 / 3 |
| Colisiones | 0 | 0 |
| Invasiones | 0 | 2 |
| Distancia total (m) | 5559.38 | 5673.43 |
| Velocidad media agregada (km/h) | 11.47 | 11.70 |
| Muestras de diagnóstico cerca de T01_067 | 196 | 534 |
| Muestras durante espera en esa zona | 0 | 100 |
| Historial final por vehículo | 5, 4, 2 | 34, 34, 33 |

Resultados:

- `data/output/town01_random_baseline_seed_42_20260908T204535976323Z/`
- `data/output/town01_history_80_20_seed_42_20260908T205635754649Z/`

Ambos escenarios conservaron la secuencia de orígenes/destinos y los estados
de la última validación; coincidieron clima, semáforos y atributos de los
vehículos. No hubo `blocked`, `timeout`, `route_failed` ni crash. Los totales
coinciden con los callbacks y los historiales con las llegadas. En baseline
solo el vehículo 002 pasó por el radio de diagnóstico, sin detenerse allí:
las 196 filas no representan el total de frames de los tres vehículos.

### Secuencia medida de vehicle_002, trip_003 → espera → trip_004

Se toma como t=0 el cierre de `trip_003` en T01_067. Los errores de rumbo de
esta tabla son relativos a la tangente del carril en la posición del vehículo,
no al rumbo final del destino.

| Momento | Frame | t relativo | Velocidad | Error de rumbo | Control observado |
|---|---:|---:|---:|---:|---|
| Llegada registrada | 2103673 | 0.00 s | 19.21 km/h | -16.63° | acelerador 0.75, dirección 0.0617, freno 0 |
| Primer evento | 2103680 | 0.35 s | 14.06 km/h | -25.77° | acelerador 0, dirección 0, freno 1 |
| Detenido (<0.05 m/s) | 2103695 | 1.10 s | ≈0 km/h | -33.08° | acelerador 0, dirección 0, freno 1 |
| Primera muestra del nuevo viaje | 2103774 | 5.05 s | 0 km/h | -33.09° | todavía se observa el freno anterior |
| Segundo evento | 2103810 | 6.85 s | 8.71 km/h | -8.22° | acelerador 0.75, dirección 0.6247, freno 0 |

En t=0, el centro está en `(3.3414, 322.2326)`, a **3.954 m** del destino.
Cumple el umbral de 4 m y el carril correcto, pero sigue girando y circula
a 19.21 km/h. `_finish_trip()` elimina el agente activo; ese mismo frame
el bucle aplica `_brake()`, que fija dirección cero y freno completo. Las
100 muestras posteriores de espera confirman dirección 0/acelerador 0/freno 1.

Durante el frenado recorre **3.116 m**. Su rumbo apenas cambia, de -134.44°
a -134.12°, mientras la carretera continúa curvándose. Se detiene cerca de
`(1.1752, 319.9933)`, con el centro desplazado **1.022 m a la izquierda** del
carril y un error de rumbo de 33.08°. El temporizador ya estaba corriendo:
aproximadamente 1.1 s de los 5 s de espera se emplean en frenar; quedan unos
3.9 s de espera programada desde que se detiene.

El nuevo viaje se crea a t=5.00 s desde la posición detenida. Su primer
waypoint está a 1.03 m del vehículo, por lo que pasa la validación de origen,
pero eso no exige alineación angular. En el primer control, t=5.05 s, el nuevo
agente ordena dirección 0.1 hacia `(2.0103, 315.6003)`; aumenta hasta 0.8 a
t=5.40 s para recuperar la trayectoria. No se observan opciones
`CHANGELANELEFT`/`CHANGELANERIGHT` en los planes de esos viajes.

### Qué significan los dos callbacks

El [sensor oficial 0.9.15](https://github.com/carla-simulator/carla/blob/0.9.15/LibCarla/source/carla/client/LaneInvasionSensor.cpp)
evalúa el cruce de cuatro esquinas entre frames. Su aproximación usa yaw y
añade el desplazamiento de la caja en ejes globales, sin rotarlo. Por eso el
observador conserva por separado esa aproximación y los vértices físicos
transformados de la caja. No se interpretan como posiciones de los neumáticos.

1. **Salida durante frenado**, t=0.35 s: la esquina delantera izquierda del
   sensor cambia de road 20/lane -1 a road 20/lane 1. La marca izquierda es
   `Broken`. El centro permanece en su carril; es la huella la que invade el
   contrario. El evento tiene `trip_id` vacío porque el viaje ya se cerró.
2. **Regreso durante la corrección de arranque**, t=6.85 s (1.85 s después de
   iniciar `trip_004`): la misma esquina vuelve al carril de la ruta. En ese
   punto delantero, la continuación vial es road 15/lane 1; la esquina pasa
   desde road 15/lane -1 a lane 1. Este callback corresponde a `trip_004`.

Se contrastaron también los ocho vértices físicos con la polilínea de road
20/lane -1 y su continuación road 15/lane 1. La caja física comienza a superar
el borde izquierdo aproximadamente a t=0.25 s y regresa completa a t=6.95 s;
la aproximación del sensor cruza a t=0.35 y 6.85 s. Las diferencias son
consistentes con sus geometrías distintas y el muestreo de 0.25 m. Por tanto
**no se atribuye el problema solo a un falso positivo del sensor**.

El centro nunca necesita cambiar al carril contrario y el plan no solicita
una maniobra de cambio de carril. La evidencia identifica un desvío de la
huella al interrumpir el seguimiento lateral durante la llegada y su posterior
recuperación. Esto no equivale a dos accidentes, ni determina por sí solo la
legalidad de atravesar una marca discontinua.

### Propuesta de corrección para la siguiente etapa, todavía no aplicada

Corregir la transición de llegada del runner, conservando los PID y
`distance_ratio=0.1` como referencia inicial:

1. Introducir una aproximación con desaceleración antes de cerrar el viaje,
   manteniendo el seguimiento lateral de la ruta mientras el vehículo frena.
   No reemplazarlo inmediatamente por dirección cero al entrar en el radio.
2. Revisar la cobertura del tramo final: el plan actual termina en
   `(2.6607, 321.4829)`, aproximadamente **2.95 m antes** del destino proyectado,
   todavía en curva. La guía lateral debe alcanzar el lugar donde se desea
   detener el vehículo; conservar el agente por sí solo no garantiza esto.
3. Cerrar el viaje e iniciar la espera cuando el vehículo esté detenido dentro
   del umbral, en el carril y alineado. Este cambio alteraría deliberadamente
   el instante de llegada y el inicio de los cinco segundos de espera, por lo
   que deberá documentarse su semántica antes de comparar tiempos e historiales.
4. Validar la llegada en curva y en recta, la continuidad de control, el inicio
   de espera después de detenerse y la ausencia de visitas duplicadas mediante
   pruebas unitarias. Repetir baseline e histórico con tres vehículos y semilla
   42, conservando los callbacks y verificando cero colisiones y llegadas correctas.

No se probó una intervención sobre el frenado en esta etapa. Las medidas
explican el mecanismo observado; no demuestran todavía que la propuesta elimine
las invasiones. No se ajustó velocidad, ganancias, umbral, duración de espera,
destinos o geometría, ni se aumentó la flota.

### Artefactos y cierre

`data/output/dwell_investigation_20260908/` contiene `preflight.json`,
`unit_tests.txt`, logs de consola, `summary.json`, `analysis_console.txt`,
`cleanup.json`, el analizador local `analyze.py` y
[el gráfico del diagnóstico](../data/output/dwell_investigation_20260908/dwell_diagnosis.png).
El gráfico se revisó visualmente. Para regenerar el resumen y la figura:

```powershell
.\carla-env\Scripts\python.exe data/output/dwell_investigation_20260908/analyze.py data/output/town01_random_baseline_seed_42_20260908T204535976323Z data/output/town01_history_80_20_seed_42_20260908T205635754649Z
```

El analizador usa Matplotlib de `carla-env` con caché local bajo la carpeta
de resultados, y no modifica logs de corrida. Al finalizar, CARLA seguía
disponible en Town01, sin vehículos ni sensores, modo asíncrono y renderizado
restaurado (`no_rendering_mode=False`). El siguiente paso queda pendiente de
revisar la propuesta con el usuario; no se creó ningún commit.

## 2026-09-08 — Corrección de la aproximación, parada y espera en destino

### Autorización y condiciones conservadas

El usuario autorizó implementar la propuesta de la investigación anterior y
pidió indicar el siguiente paso. Se mantiene la instrucción de **no hacer
commits**. Antes de modificar se comprobó con `carla-env`: CARLA 0.9.15 en
`localhost:2000`, Town01, cero vehículos y sensores, modo asíncrono y
renderizado activo. No se cambió mapa, clima, catálogo, CSV de entrada ni flota.

Todas las corridas de esta etapa usaron tres vehículos, semilla 42, 600 s
simulados, timestep 0.05 s, velocidad de crucero 20 km/h, `distance_ratio=0.1`,
espera 5 s, `--simulation-speed 5` y `--no-rendering`. Se preservaron los
modelos, atributos y spawns 133/6/101. El runner restauró las opciones del
mundo al finalizar cada corrida.

### Cambio implementado

- `src/arrival.py`: progreso ordenado a lo largo de la ruta y límite de
  velocidad `min(crucero, sqrt(2 * 1.5 * max(restante - 0.5, 0)))` en m/s.
  El objetivo comienza a reducirse unos 10.8 m antes del destino a 20 km/h.
  La búsqueda local del progreso evita saltar a una rama posterior cercana
  del recorrido. Al final se conserva la dirección mientras se frena.
- `src/route_planner.py`: reconstruye el tramo final sobre el carril cada
  0.5 m hasta el waypoint exacto de parada. Elimina un eventual extremo pasado
  y completa uno anticipado. Añade 6 m de continuación única para mantener
  objetivos laterales durante el frenado, sin sumarlos a la distancia
  planificada. Rechaza anclas incompatibles y continuaciones ambiguas.
- `src/carla_agent.py`: el radio base de descarte baja gradualmente desde 3 m
  a 1 m según la velocidad objetivo de aproximación. Se conserva el término
  `0.1 * velocidad_mps`, las ganancias PID oficiales, el límite de variación
  de dirección y las detecciones de obstáculos/semáforos. A velocidad de
  crucero recupera el radio base de 3 m.
- `src/trip_runner.py`: el viaje sigue activo durante la aproximación. Exige
  avance hasta el margen final, distancia ≤4 m, mismo road/lane del destino,
  velocidad ≤0.05 m/s, error de rumbo ≤10° y error lateral del centro ≤0.5 m.
  Si falta orientación o centrado al alcanzar el margen, permite un objetivo
  de 1 km/h mientras el actor permanezca en el radio y carril correctos; frena
  al cumplir ambos límites. No desactiva frenadas por obstáculos o semáforos.
- `src/navigation_diagnostics.py` y `src/run_logger.py`: diagnóstico versión 2;
  el control incluye velocidad objetivo y distancia restante, y el nuevo
  `arrival_log.csv` guarda cada llegada completa. La cola de `route_log.csv`
  incluye la continuación lateral, cuya semántica queda registrada.
- El observador de `scripts/diagnose_destination_dwell.py` sigue delegando la
  conducción y ahora incluye `src/arrival.py` entre los hashes de procedencia.

`arrival_policy_version=2` y `arrival_control` en `run_config.json` permiten
identificar la nueva política. El tiempo de viaje incluye desaceleración,
alineación y parada; los cinco segundos de espera empiezan después. Una visita
se agrega al historial una sola vez, al completar. No se reescribieron las
métricas antiguas ni se cambiaron sus callbacks. La corrección afecta a todos
los destinos, sin condiciones especiales por coordenadas de T01_067.

### Dos intentos intermedios que no se aceptaron como solución

Se preservaron dos corridas históricas completas de 600 s:

| Variante | Carpeta bajo `data/output/` | Resultado |
|---|---|---|
| Aproximación y guía completa con radio base fijo 3 m | `town01_history_80_20_seed_42_20260908T213300409794Z` | 9 completed, 1 blocked, 3 aborted; 0 colisiones, 0 invasiones |
| Radio base reducido con la velocidad, sin avance final de alineación | `town01_history_80_20_seed_42_20260908T213714649261Z` | 9 completed, 1 blocked, 3 aborted; 0 colisiones, 0 invasiones |

La primera variante detuvo al vehículo 002 con desplazamiento lateral de
0.569 m. No cumplía el centrado de 0.5 m y quedó `blocked`; no se relajó el
criterio para declarar éxito. La segunda redujo ese desplazamiento a 0.142 m,
pero se detuvo con 11.15° de error de rumbo, también fuera del límite de 10°.
La dirección aplicada a un actor inmóvil no puede corregir su orientación.
Esto motivó el avance final limitado a 1 km/h, manteniendo los límites de
llegada y las detecciones oficiales. Cero callbacks por sí solo no bastó
para aceptar esos intentos.

### Pruebas unitarias y comprobación del mapa

**80 pruebas correctas, sin skips**, ejecutadas con `carla-env` y
`CARLA_PYTHONAPI=C:\CARLA\WindowsNoEditor\PythonAPI\carla`. Se añadieron
regresiones en `tests/test_arrival_control.py`, `tests/test_agent_compatibility.py`
y se adaptó el doble del runner en `tests/test_scenario_runner.py`:

- extremo exacto en curva, ambos sentidos de s y recorte de extremos pasados;
- rechazo de carril final incompatible y progreso sin saltar a una rama cercana;
- desaceleración por distancia de ruta, frenado con dirección y prioridad de
  frenos por obstáculos;
- reducción/restauración del horizonte lateral sin modificar `distance_ratio`;
- parada, centrado, orientación y avance lento acotado al radio/carril;
- inicio de espera después de detenerse, sin duplicar visitas.

Se comprobó la nueva cobertura de las 28 rutas de referencia, y las 41 rutas
del catálogo desde T01_133: todas permitieron completar el extremo y añadir
guía lateral única. Esto comprueba geometría planificada; no es una prueba
de conducción de todos los pares posibles de destinos.

```powershell
$env:CARLA_PYTHONAPI = 'C:\CARLA\WindowsNoEditor\PythonAPI\carla'
.\carla-env\Scripts\python.exe -m unittest discover -s tests -v
.\carla-env\Scripts\python.exe scripts/diagnose_destination_dwell.py --config config/trips/multi_vehicle_trip.json --scenario history_80_20 --town Town01 --seed 42 --seconds 600 --simulation-speed 5 --no-rendering --controller-distance-ratio 0.1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
.\carla-env\Scripts\python.exe scripts/diagnose_destination_dwell.py --config config/trips/multi_vehicle_trip.json --scenario random_baseline --town Town01 --seed 42 --seconds 600 --simulation-speed 5 --no-rendering --controller-distance-ratio 0.1 --carla-pythonapi C:\CARLA\WindowsNoEditor\PythonAPI\carla
```

### Validación real final

| Medida | random_baseline | history_80_20 |
|---|---:|---:|
| Iniciados / completados / aborted al límite de duración | 14 / 11 / 3 | 14 / 11 / 3 |
| blocked / timeout / route_failed | 0 / 0 / 0 | 0 / 0 / 0 |
| Colisiones / invasiones | 0 / 0 | 0 / 0 |
| Distancia total (m) | 5784.41 | 5665.75 |
| Velocidad media agregada (km/h) | 11.93 | 11.69 |
| Máxima velocidad al completar (m/s) | 0.000925 | 0.008274 |
| Máximo error de rumbo al completar (°) | 0.463 | 9.965 |
| Máximo error lateral al completar (m) | 0.0054 | 0.0867 |
| Máxima distancia al destino al completar (m) | 0.500 | 0.692 |
| Historial final por vehículo 001/002/003 | 5 / 4 / 2 | 34 / 34 / 33 |

Resultados finales:

- `data/output/town01_random_baseline_seed_42_20260908T214348287830Z/`
- `data/output/town01_history_80_20_seed_42_20260908T214121761147Z/`

Las 22 llegadas coinciden con `trips_log.csv` y con las visitas añadidas a
historial. Todas cumplen los límites de llegada; las salidas posteriores
respetan los cinco segundos completos de espera. Coinciden entre ambos casos
clima, semáforos y atributos de actores. También coinciden con el diagnóstico
anterior el entorno, los modelos y la secuencia de orígenes, destinos y estados
por vehículo. Las distancias y tiempos pueden variar por las nuevas paradas
y su interacción con semáforos; no deben interpretarse como un efecto aislado
de la selección 80/20. No hubo crash ni contactos en las curvas estáticas
investigadas anteriormente, ni se eliminaron callbacks del registro.

### Llegada y huella en T01_067 después de corregir

`vehicle_002/trip_003` se completa en frame **2379470**, tiempo simulado
**6813.008466 s**, cerca de `(2.0966, 317.8168)`, road 20/lane -1:

- velocidad **0.000821 m/s**, aproximadamente **0.003 km/h**;
- error lateral **+0.08665 m** y error de rumbo **-9.965°**;
- distancia **0.692 m** al destino usado por el runner;
- cien muestras de espera (5 s), desplazamiento residual **0.000185 m**;
- nuevo `trip_004` desde T01_067 sin invasiones ni recuperación desde el carril
  contrario.

Al entrar en el radio de 4 m ya circula a **10.96 km/h**, frente a 19.21 km/h
antes. Ahora tarda **8.5 s** desde esa entrada hasta completar la parada y
alineación; después inicia los cinco segundos de espera. Antes cerraba el
viaje inmediatamente y empleaba los primeros 1.1 s de la espera en frenar.
La caja física permanece entre **-1.422 y +1.593 m** respecto al centro del
carril en la ventana de 15 s anteriores y 10 posteriores a la llegada;
los límites son ±2 m. La comparación usa la polilínea muestreada cada 0.25 m,
incluida la continuación road 15/lane 1; no representa posiciones de neumáticos.

### Artefactos, límites y siguiente paso

`data/output/arrival_correction_20260908/` conserva consolas, resultados de
pruebas unitarias, `route_preflight.json`, `catalog_route_validation.json`,
`summary.json`, `final_audit.txt`, `reference_comparison.json`, `cleanup.json`,
el analizador y la [figura antes/después](../data/output/arrival_correction_20260908/arrival_comparison.png)
con su script `plot_comparison.py`. La figura se revisó visualmente.

La limpieza final confirmó CARLA 0.9.15 disponible en Town01, cero vehículos
y sensores, modo asíncrono y renderizado restaurado. No se hicieron commits
ni se tocaron los CSV genéricos, `i-marco_teorico.tex` o `image.png`.

Sigue comprobar repetibilidad y corridas más largas conservando tres vehículos;
después, ampliar a otras semillas con ambos escenarios y los mismos criterios
de llegada, eventos e historial. Una vez estable esa base, probar cinco
vehículos antes de aumentar más la carga. Esta etapa no ejecutó esas pruebas
adicionales ni amplió la flota. Una pareja de 600 s con semilla 42 no demuestra
ausencia de fallos en cualquier ruta, modelo o densidad.

## 2026-09-08 — Repetición con semilla 42 y campaña larga preparada

### Alcance actualizado por el usuario

Se solicitó comprobar repetibilidad, mayor duración y otras semillas. Tras
proponer dos repeticiones de 600 s y seis corridas de 1.800 s con semillas
42/7/123, el usuario pidió limitar la ejecución actual a semilla 42 y dejar
las corridas largas para ejecutarlas después. Se realizaron **solo dos
repeticiones de 600 s**, una por escenario, siempre con tres vehículos.
Las pruebas de 1.800 s y las semillas 7/123 **no se ejecutaron**.

Preflight con `carla-env`: CARLA 0.9.15, `localhost:2000`, Town01, cero actores
de vehículo/sensor, modo asíncrono y renderizado activo. Las **80 pruebas
unitarias pasaron**, sin skips. No se modificó la conducción, la configuración
ni los datos de entrada; se guardaron y comprobaron sus hashes SHA-256.
Se respetó la prohibición de hacer commits.

### Resultados de las repeticiones

| Medida | random_baseline | history_80_20 |
|---|---:|---:|
| Iniciados / completados / aborted al finalizar 600 s | 14 / 11 / 3 | 14 / 11 / 3 |
| Colisiones / invasiones | 0 / 0 | 0 / 0 |
| blocked / timeout / route_failed | 0 / 0 / 0 | 0 / 0 / 0 |
| Llegadas auditadas | 11 | 11 |
| Distancia total (m) | 5784.023 | 5665.849 |
| Velocidad media agregada (km/h) | 11.9327 | 11.6889 |
| Máxima velocidad al completar (m/s) | 0.042504 | 0.049980 |
| Máximo error de rumbo al completar (°) | 0.4631 | 9.9652 |
| Máximo error lateral al completar (m) | 0.0054 | 0.0867 |

Carpetas:

- `data/output/town01_random_baseline_seed_42_20260908T220730234302Z/`
- `data/output/town01_history_80_20_seed_42_20260908T220937759845Z/`

Todas las llegadas cumplen velocidad ≤0.05 m/s, rumbo ≤10°, error lateral
≤0.5 m, radio ≤4 m y road/lane del destino. Las salidas siguientes respetan
cinco segundos completos de espera. Coinciden las claves y conteos entre
viajes, llegadas, visitas del historial y eventos; no se encontraron duplicados
ni errores de integridad. Los tres `aborted` de cada corrida corresponden a
los viajes todavía activos cuando finalizan los 600 s, no a un bloqueo.

### Qué se repite y qué varía

Se comparó cada escenario con la validación anterior:

- baseline: `town01_random_baseline_seed_42_20260908T214348287830Z`;
- histórico: `town01_history_80_20_seed_42_20260908T214121761147Z`.

Coinciden exactamente el entorno registrado, los modelos/atributos/spawns,
las semillas de actores y destinos, y la secuencia de origen, destino, clase
de selección y estado de cada viaje. También se repiten los resultados de
seguridad y las llegadas correctas. La física presenta diferencias:

| Diferencia máxima frente a referencia | baseline | histórico |
|---|---:|---:|
| Tiempo por viaje (s) | 0.5000 | 0.1500 |
| Distancia por viaje (m) | 0.3796 | 0.1373 |
| Pose al mismo frame relativo (m) | 3.1215 | 1.4110 |
| Velocidad al mismo frame relativo (m/s) | 5.7217 | 5.1586 |
| Control normalizado al mismo frame relativo | 1.0 | 1.0 |

Se normalizó el frame inicial para no confundir IDs o tiempos absolutos del
servidor con diferencias físicas. En baseline se compararon 34.876 muestras
comunes de control y quedaron diez exclusivas por ejecución; en histórico,
34.882 comunes y cuatro exclusivas por ejecución. Los controles no se
registran durante la espera, por lo que un cambio de instante de llegada
también cambia qué frames tienen fila de control.

Las distancias de la tabla comparan ejecuciones, **no miden invasión ni error
lateral respecto al carril**. En baseline el vehículo 001 no supera 1 mm de
diferencia de pose en los frames comparados; las primeras diferencias mayores
de 1 mm aparecen en el vehículo 003 a unos 247.2 s y en el 002 a 251.2 s,
cerca del tramo y≈326 durante frenadas/arranques. Se guardó
`baseline_divergence.json` con esas muestras. Estos registros no identifican
por sí solos un mecanismo único para la variación. No se ajustó el controlador
para forzar identidad numérica. Si el experimento exige determinismo exacto
por frame, queda pendiente investigarlo específicamente.

### Campaña larga lista para ejecución manual

Con CARLA y Town01 preparados, desde `C:\CARLA\TrafficIA`:

```powershell
.\carla-env\Scripts\python.exe -u .\data\output\reliability_campaign_20260908\run_campaign.py --long
```

Ejecutará secuencialmente 1.800 s con `random_baseline` e `history_80_20` para
cada semilla 42, 7 y 123: seis corridas, aproximadamente 36 minutos reales a
5× más inicialización. Mantiene tres vehículos y el historial dummy de entrada.
La semilla del runner afecta tanto a destinos como a los modelos sorteados.
Cada par de escenarios con la misma semilla conserva los mismos actores.

El script comprueba CARLA antes y después de cada corrida, conserva consolas
y hashes y ejecuta la auditoría al terminar. Los logs de cada corrida se
guardan en su carpeta habitual; manifiesto, consolas y `audit.json` se guardan
en `data/output/reliability_campaign_20260908/long/`. Si encuentra una campaña
ya existente, la preserva y rechaza sobrescribirla. La auditoría informa de
eventos o resultados incompletos; un callback de marca `Broken` requiere
interpretación de la maniobra y no se convierte automáticamente en accidente.

### Artefactos y cierre actual

`data/output/reliability_campaign_20260908/` conserva `campaign.json`,
`audit.json`, `audit_console.txt`, las dos consolas de corrida, `unit_tests.txt`,
`baseline_divergence.json`, una copia del código/datos usados y los scripts
`run_campaign.py` / `analyze_campaign.py`. Para regenerar la auditoría actual:

```powershell
.\carla-env\Scripts\python.exe .\data\output\reliability_campaign_20260908\analyze_campaign.py
```

El manifiesto confirma código/datos sin cambios y limpieza final: cero
vehículos/sensores, modo asíncrono y renderizado restaurado. No se hicieron
commits ni se tocaron los CSV genéricos, `i-marco_teorico.tex` o `image.png`.
Sigue ejecutar y revisar la campaña larga antes de aumentar a cinco vehículos.

## 2026-09-09 — Revisión de la campaña larga ejecutada por el usuario

### Alcance y consistencia

El usuario ejecutó `run_campaign.py --long` y pidió revisar los archivos.
Se analizaron las seis corridas existentes; no se volvió a ejecutar la campaña
ni se modificó la lógica de conducción. Continúa la instrucción de **no hacer
commits**. Se comprobó CARLA 0.9.15 en `localhost:2000`, Town01, sin vehículos
ni sensores. Las consultas posteriores al mapa no crearon actores ni aplicaron
controles.

La campaña abarcó 15:39:03–16:15:49 UTC, aproximadamente 36 min 46 s reales.
Cada caso contiene 1.800 s simulados, tres vehículos, velocidad objetivo de
20 km/h, paso fijo de 0.05 s y `controller_distance_ratio=0.1`. Se conservan
la configuración, el historial dummy y el clima de la validación anterior.
El entorno registrado, incluidos los semáforos reiniciados, coincide en las
seis corridas. Los modelos cambian con la semilla; cada par baseline/histórico
conserva exactamente modelos, atributos, spawns y semillas de actor/destino:

| Semilla | vehicle_001 | vehicle_002 | vehicle_003 |
|---|---|---|---|
| 42 | audi.etron | volkswagen.t2_2021 | audi.tt |
| 7 | dodge.charger_police | mini.cooper_s | mercedes.coupe |
| 123 | dodge.charger_police_2020 | lincoln.mkz_2017 | tesla.cybertruck |

Se recalculó la auditoría en `long/review/recomputed_audit.json`, sin
sobrescribir `long/audit.json`: coincide con las seis entradas originales.
Además se comprobaron hashes actuales de código/datos y archivos protegidos,
configuraciones entre escenarios, fin de los `aborted`, planes de los viajes
con eventos, controles durante las paradas y cobertura de las zonas originales.

### Resultados y carpetas

| Escenario | Semilla | completed | timeout | route_failed | blocked | aborted | Colisiones | Invasiones |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random_baseline | 42 | 34 | 1 | 1 | 0 | 2 | 0 | 0 |
| history_80_20 | 42 | 31 | 1 | 1 | 0 | 3 | 0 | 0 |
| random_baseline | 7 | 25 | 2 | 1 | 0 | 3 | 0 | 0 |
| history_80_20 | 7 | 31 | 1 | 2 | 0 | 3 | 0 | 0 |
| random_baseline | 123 | 26 | 3 | 2 | 1 | 3 | 0 | 8 |
| history_80_20 | 123 | 27 | 2 | 2 | 0 | 3 | 0 | 2 |

Carpetas, todas bajo `data/output/`, en el orden de la tabla:

- `town01_random_baseline_seed_42_20260909T153906001597Z/`
- `town01_history_80_20_seed_42_20260909T154514290754Z/`
- `town01_random_baseline_seed_7_20260909T155121892849Z/`
- `town01_history_80_20_seed_7_20260909T155729474918Z/`
- `town01_random_baseline_seed_123_20260909T160337039179Z/`
- `town01_history_80_20_seed_123_20260909T160944644590Z/`

Son 211 registros de viaje: 174 completados, 20 terminaciones por
`timeout`/`route_failed`/`blocked` y 17 activos al finalizar la duración
(`aborted`). Los 174 completados tienen una llegada y una visita nueva al
historial, sin duplicados ni errores de integridad. Máximos al completar:
velocidad **0.046718 m/s**, error de rumbo **9.996391°**, error lateral
**0.114617 m**. Todos cumplen radio ≤4 m, carril del destino y distancia
restante de ruta ≤0.5 m; las salidas posteriores respetan cinco segundos de
espera. Los 17 `aborted` coinciden con el corte temporal, no con un fallo.

`exit=0` acredita fin normal del proceso, no ausencia de incidencias de
comportamiento. La advertencia final de la auditoría es correcta.

### Nueve route_failed: destino detrás del origen en el mismo tramo

Los mensajes de consola rechazan planes cuyo punto final queda entre 23.20 y
175.06 m del destino. Se reprodujeron los nueve casos con el mapa real y la
SDK instalada, sin circular: `_localize` asigna origen y destino a la misma
arista dirigida del grafo y el destino está detrás en el sentido de marcha.
`_path_search` devuelve esa única arista. En `GlobalRoutePlanner.trace_route`,
la condición `closest_index > destination_index` termina el recorrido tras
añadir un solo waypoint próximo al origen.

| Escenario / semilla | Vehículo / viaje | Origen → destino | Error final (m) |
|---|---|---|---:|
| baseline / 42 | 002 / 009 | POSITION_AFTER_TRIP_008 → T01_027 | 175.06 |
| histórico / 42 | 002 / 010 | T01_045 → T01_084 | 87.85 |
| baseline / 7 | 002 / 002 | T01_032 → T01_041 | 142.88 |
| histórico / 7 | 002 / 005 | T01_020 → T01_084 | 151.85 |
| histórico / 7 | 003 / 007 | T01_030 → T01_037 | 56.23 |
| baseline / 123 | 003 / 007 | T01_032 → T01_039 | 112.48 |
| baseline / 123 | 003 / 010 | POSITION_AFTER_TRIP_009 → T01_037 | 26.23 |
| histórico / 123 | 001 / 004 | T01_010 → T01_006 | 69.13 |
| histórico / 123 | 003 / 007 | T01_032 → T01_030 | 23.20 |

El rechazo ocurre en `src/route_planner.py:plan_route`, antes de la cola de
llegada y de su continuación para orientar el vehículo. No lo causa el
frenado. El grafo contiene un camino dirigido de vuelta desde la salida del
tramo a su entrada en los nueve casos; no basta con declarar esos destinos
inaccesibles.

Se amplió la comprobación a **42 × 41 = 1.722 pares** distintos del catálogo,
con `plan_route`, `arrival_route` y `steering_continuation`: 1.662 válidos y
60 fallidos en el mismo tramo. La comprobación anterior desde un solo origen
no cubría este caso. Propuesta pendiente: construir el circuito hacia delante
cuando el destino queda detrás, conservando el rechazo de planes truncados y
la dirección legal del carril. No se relajó el umbral ni se quitaron destinos.

### Diez timeout: presupuesto de 300 s con esperas de tráfico

Los diez viajes duran 300.000004 s, el límite configurado. Sus controles
acumulan **82.70–167.25 s con velocidad <0.2 m/s**, pero ninguna parada
continua supera **32.35 s**; todos avanzaron en los últimos 30 s del viaje
(entre 12.96 y 160.52 m). En esos viajes no aparece velocidad objetivo cero
ni la fase de alineación a 1 km/h.

Entre el 97.96 % y el 98.80 % de las muestras casi detenidas coinciden con
`brake=0.5`, el freno de seguridad del BasicAgent instalado. Entre el 99.56 %
y el 100 % están a menos de 12 m de un punto de parada de semáforo. Es evidencia
consistente con esperas de tráfico repetidas que consumen el presupuesto; los
logs no registran el motivo de frenado ni el estado del semáforo en cada frame,
por lo que no se atribuye cada parada de manera concluyente a una luz roja.

El caso más próximo a llegar es baseline/123, vehículo 003, viaje 009 hacia
T01_035: termina con 1.75 m de ruta restante y 1.98 m/s. Los otros nueve
conservan entre 107.12 y 328.97 m de ruta. Aumentar indiscriminadamente el
límite podría ocultar otro fallo: queda distinguir tiempo total, espera por
tráfico y falta de progreso, y evaluar un presupuesto relacionado con la ruta.

### Un blocked: discontinuidad de IDs durante la alineación de llegada

Baseline/123, vehículo 003 (Cybertruck), viaje 004 de T01_068 a T01_067.
Tras 11.1 s con objetivo de alineación de 1 km/h, el centro cruza la unión
`road/lane=20/-1 → 15/+1`. Es la continuación dirigida del carril seguida por
el plan, aunque cambien los IDs y el signo de `lane_id`.

En el frame **161516**, a t=7999.271093 s del servidor, la consulta del mapa
pasa a `15/+1`, a unos 0.91 m del destino. El rumbo aún difiere 12.48° del
carril. `is_at_destination` exige igualdad exacta con `20/-1`, por lo que
`trip.approach.settling` pasa a falso. La distancia restante ya es cero y
`approach_control` ordena freno completo. Sin avance no puede terminar de
orientarse; aproximadamente 60 s después finaliza como `blocked`.

Pose final: `(2.071657, 317.599640)`, rumbo `-102.47199°`, error lateral
aproximado `+0.0617 m`, distancia al destino `0.906538 m`. No hay visita falsa
al historial. **Esta es una limitación de la corrección de llegada anterior**,
que no apareció con los modelos de semilla 42.

Propuesta pendiente: representar un corredor de llegada acotado sobre el
carril y su continuación dirigida verificada, manteniendo rechazo de carril
contrario/adyacente, parada, radio, centrado y orientación. También hay que
comprobar el límite de avance de alineación para impedir deriva indefinida.

### Diez invasiones del Cybertruck: dos maniobras distintas

Todas corresponden a `vehicle_003` con semilla 123. Su caja mide aproximadamente
**6.274 × 2.390 m**. Los planes implicados no contienen `CHANGELANELEFT` ni
`CHANGELANERIGHT`. No hay callbacks de colisión.

Ocho eventos de marca **NONE** se agrupan en cuatro pasos por la curva cerca
de `(8, 2)`, de `road/lane=13/-1` a `3/+1`:

| Escenario | Viaje | Frames de los callbacks |
|---|---|---|
| baseline | 004 | 158416, 158427 |
| baseline | 005 | 163986, 163996 |
| baseline | 009 | 172947, 172955 |
| histórico | 009 | 201115, 201128 |

Ocurren a unos 19.4–19.9 km/h, con objetivo 20 km/h y cientos de metros de
ruta restante: no son el frenado de llegada. La reconstrucción de las cuatro
esquinas XY del sensor, usando pose y caja registradas, coloca la esquina
trasera derecha fuera del borde exterior durante esos pasos. Frente a una
referencia del mapa muestreada cada 0.25 m, los máximos por paso exceden el
semiancho de 2 m en aproximadamente **2.3–6.5 cm**. La consulta puntual del
mapa ubica esa esquina en `Shoulder` o fuera de las superficies reconocidas
en parte de la ventana. `NONE` indica ausencia de marca pintada y no demuestra
una colisión; tampoco basta para descartar el cruce. Aquí se reconstruyó la
huella del sensor con yaw: no se guardaron los ocho vértices físicos en esta
zona y no se afirma esa precisión centimétrica para toda la carrocería real.

Los otros dos eventos son **Broken**, baseline/123, viaje 004 al llegar a
T01_067: frame **161256**, cerca de `(3.16, 321.79)`, a 10.72 km/h durante
desaceleración; frame **161369**, cerca de `(2.14, 318.58)`, a 1.20 km/h
durante alineación. La esquina delantera izquierda cruza al carril contrario
y regresa. En esta zona sí están registrados los ocho vértices físicos:
entre frames 161230–161420, su proyección lateral mínima es **-2.175118 m**,
frente a borde izquierdo de -2 m; máxima derecha +1.893712 m. La caja invade
transitoriamente unos **0.175 m** el carril contrario. Ambos callbacks son
durante viaje activo; no reaparece el mecanismo antiguo de terminar a
19 km/h y poner dirección cero durante la espera.

La evidencia identifica un problema de seguimiento/holgura para este modelo,
pero aún no establece qué ajuste lo resuelve. Antes de cambiar ganancias o
descartar el vehículo, se debe contrastar curvatura, puntos objetivo, velocidad
y dimensiones, y validar una aproximación que mantenga la huella en el carril.
No se filtraron callbacks ni se modificó el controlador en esta revisión.

### Zonas originales, pruebas y próximos pasos

Las seis corridas recorren ambas zonas originalmente investigadas, sin
contactos. Como medida de cobertura se contaron secuencias consecutivas de
frames de control dentro de un radio de 12 m por vehículo/viaje: 14–20 por
corrida cerca de `(96, 202)` y 10–13 cerca de `(98, 325)`. Es cobertura de zona,
no un conteo de giros idénticos.

Se ejecutó con `carla-env` y `CARLA_PYTHONAPI` la suite existente:
**80 pruebas, OK**, sin omisiones. Ese resultado no cubre todavía las nuevas
regresiones identificadas ni sustituye las seis corridas reales analizadas.
La revisión dejó CARLA disponible, Town01, cero vehículos/sensores, modo
asíncrono y renderizado activo. No se tocaron los CSV genéricos ni
`i-marco_teorico.tex` o `image.png`; sus hashes coinciden con los preservados.

Mantener **tres vehículos**. Orden propuesto para la siguiente corrección:

1. Resolver rutas de retorno en el mismo tramo y comprobar los 1.722 pares,
   también orígenes de recuperación tras un viaje fallido.
2. Corregir la continuidad de llegada en uniones de tramos, con regresión
   específica del Cybertruck en T01_067 y rechazo del carril contrario.
3. Validar el seguimiento y la huella del Cybertruck en las dos curvas con
   observación física ampliada; modificar la conducción solo con esa evidencia.
4. Distinguir y revisar los límites temporales para rutas largas con esperas.
5. Pasar pruebas unitarias y corridas reales focalizadas; después repetir ambos
   escenarios, semillas 42/7/123 y 1.800 s. No aumentar la flota todavía.

### Artefactos de esta revisión

Todo el diagnóstico adicional está bajo
`data/output/reliability_campaign_20260908/long/review/`:

- `review_summary.json`, `recomputed_audit.json`: consistencia, llegadas,
  configuraciones, paradas, cobertura y hashes de auditoría/manifiesto originales.
- `log_review.json` y dos CSV de aproximación: estados fallidos y ventanas de
  control alrededor de los eventos.
- `map_review.json`: reproducción de los nueve fallos, 1.722 pares del
  catálogo, semáforos y referencias geométricas.
- `geometry_review.json`, `northwest_footprint_review.json`: esquinas,
  transición de IDs y proyección de vértices físicos/huella reconstruida.
- [invasion_geometry.png](../data/output/reliability_campaign_20260908/long/review/invasion_geometry.png): vista de las dos maniobras.
- `unit_tests.txt`, `server_at_review_end.json`, scripts de inspección y
  consolas: permiten reproducir la revisión sin sobrescribir los logs originales.

Se actualizaron README y esta bitácora. No se hicieron commits ni cambios
adicionales en `src/`, `tests/`, `config/` o datos de entrada.

## 2026-09-09 — Alineación con los objetivos de graduación

Después de revisar la campaña, el estudiante aclaró que las invasiones de
carril son una métrica prevista y que la conducción no necesita ser perfecta.
Se consultaron `protocolo-final.tex` (objetivos y metodología) y
`i-marco_teorico.tex` (métricas, cobertura y comparación). El objetivo
específico 3 incluye expresamente distribución de destinos, tiempo promedio
de viaje, velocidad media y tasa de incidentes o invasiones de carril.

Se creó [project-graduation-context.md](project-graduation-context.md) con
los objetivos transcritos literalmente, alcance, fuentes, estado comprobado,
criterios de medición y propuestas pendientes. Se añadió su enlace al README
y se actualizaron las prioridades para futuras sesiones.

**Se sustituye la recomendación anterior de eliminar las invasiones del
Cybertruck como requisito previo para avanzar.** Se conservarán como
observaciones, con unidad de evento y exposición explícitas. No se ajustará
el controlador solo para lograr cero invasiones ni se excluirán corridas
por tener resultados desfavorables. Si un comportamiento impide los viajes
o incumple el ODD declarado, se investigará por esa razón.

Siguen siendo prioritarios los errores de rutas truncadas y de reconocimiento
de llegada: pueden alterar las distribuciones observadas y la finalización
de viajes. El límite de 300 s necesita una política común entre tratamientos;
las esperas seguirán contando en el tiempo de viaje, aunque se use otro
contador para detectar falta de progreso. Los viajes incompletos se informan
por separado y no se convierten en tiempos completos.

Tras esas correcciones y la definición/verificación de las métricas, queda
concretar el ODD experimental y **dos niveles de demanda**, exigidos por el
objetivo 1. Los selectores baseline/histórico no son esos dos niveles. No se
han fijado cantidades finales ni se da por acordado que sean tres y cinco
vehículos. La comparación deberá cruzar selector y demanda con condiciones
controladas y repeticiones documentadas.

En esta actualización solo se editó documentación. No se ejecutaron
simulaciones ni se modificaron el protocolo, el marco teórico, el controlador
o los datos de entrada. No se hicieron commits.

### Aclaración posterior y autorización de commits

El estudiante confirmó que los dos niveles de demanda corresponden a
distintas cantidades de vehículos simultáneos. Se pospone la elección de
esas cantidades hasta completar los puntos 1–3: correcciones de rutas y
llegadas, política temporal y cálculo de métricas.

Autorizó crear Conventional Commits del estado acumulado antes de continuar.
Se revisó el diff y se ejecutó la suite existente: 80 pruebas aprobadas con
`carla-env`. Se separan navegación/llegada, instrumentación de diagnóstico y
documentación; se excluyen los CSV genéricos, `i-marco_teorico.tex`,
`protocolo-final.tex`, `image.png` y resultados generados. Los cambios nuevos
de los puntos 1–3 quedarán sin commit hasta otra indicación.

## 2026-09-09 — Correcciones de movilidad y análisis de métricas

### Commits del estado previo y alcance nuevo

Se crearon los Conventional Commits autorizados antes de iniciar este trabajo:

- `a8e1d7b` — `fix(navigation): stop and align vehicles before completing trips`.
- `5915499` — `feat(diagnostics): trace vehicle footprints across destination dwell`.
- `760c1b1` — `docs(simulation): record validation and graduation criteria`.

Se excluyeron los CSV genéricos, marco teórico, protocolo, imagen y resultados
generados. Los cambios descritos a continuación **quedan sin commit**.
Se mantuvieron tres vehículos; el punto 4, elegir dos cantidades de vehículos
como niveles de demanda, permanece para el final. No se exigió cero invasiones.
Antes de circular se comprobó CARLA 0.9.15 en localhost:2000, Town01, sin
vehículos/sensores, modo asíncrono y renderizado activo.

### Punto 1: rutas de retorno y continuidad de llegada

`src/route_planner.py` construye ahora una subclase de `GlobalRoutePlanner`
que adapta `_path_search` para el caso confirmado: origen y destino sobre
la misma arista, con destino detrás según el sentido del carril. Recorre la
arista actual, busca el retorno dirigido desde su salida a su entrada y vuelve
a recorrer el tramo hasta el destino. Se conservan `trace_route`, decisiones
de giro, validación de extremos y cola final de CARLA. No se permite marcha
atrás ni se descartan destinos. La adaptación usa internals de la SDK 0.9.15;
debe revalidarse al actualizar CARLA.

`scripts/validate_route_catalog.py` comprueba todos los pares del catálogo
sobre el mapa real sin crear actores. Resultado: **1.722/1.722 válidos**, más
**9/9 orígenes de los route_failed anteriores**, incluidos los dos de
recuperación. Antes fallaban 60 pares del catálogo. La comprobación incluye
cola de llegada, continuación y proximidad de ambos extremos, no prueba la
circulación física de todas las rutas.

`ArrivalLaneCorridor` usa la continuación dirigida ya verificada, acotada a
3 m del destino y a los tramos/intervalos longitudinales muestreados. Permite
reconocer la unión `20/-1 → 15/+1` de T01_067, conservando progreso ordenado,
radio, parada, centrado y orientación. No cambia las ganancias PID ni el
objetivo de 20 km/h. `arrival_policy_version=3` identifica esta semántica.

El Cybertruck de baseline/123, viaje 004, **completó T01_067** en la
continuación `15/+1`, a 1.38956 m del destino, con velocidad 0.000746 m/s,
error de rumbo -9.97489° y error lateral +0.04035 m. Antes quedaba detenido
con 12.48° y terminaba bloqueado. La consulta posterior del mapa validó
las 48 llegadas de las cuatro corridas; esta fue la única en una continuación
con IDs distintos de los del destino.

### Punto 2: límite temporal y viajes incompletos

La configuración multivehículo cambia `max_trip_time_seconds` de 300 a
`null`: no hay corte independiente por viaje y se mantiene el fin de corrida
como límite global. El detector de velocidad baja durante 60 s se conserva;
no equivale a una clasificación del motivo de parada. El límite fijo sigue
disponible con `--max-trip-seconds 300`; `--max-trip-seconds 0` lo desactiva.
Otras configuraciones que conserven 300 mantienen ese comportamiento.

Todos los segundos desde salida hasta llegada, incluidas las esperas,
continúan en el tiempo de viaje. Los activos al corte son `aborted`, con
duración parcial y sin visita al historial. Se añaden al log de viajes
`end_sim_time_s`, `termination_reason`, `max_trip_time_seconds` y
`stopped_time_s`. La última variable integra cada intervalo de tick cuando
su velocidad final es menor del umbral; no atribuye cada parada a un semáforo.

Evidencia real: baseline/123, vehículo 002, viaje 002 a T01_037 completó
en **374.500006 s**, mientras que el caso anterior se había cortado a 300 s.
Es una comprobación de que el límite opcional permite acabar un viaje largo;
no implica que todos los viajes deban llegar dentro de cualquier horizonte.

### Punto 3: las cuatro métricas y sus denominadores

Se añadieron `src/mobility_analysis.py` y `scripts/analyze_mobility.py`.
Procesan corridas preservadas sin CARLA y escriben un directorio nuevo con
`analysis.json`, `summary.csv`, `destinations.csv` y `report.md`:

- Frecuencias de destinos asignados y alcanzados, por ID y categoría, con
  denominadores distintos y categorías sin observaciones conservadas.
- Media, mediana y desviación de tiempos completos, más estados y duraciones
  parciales de todos los incompletos. No se mezclan estos con las llegadas.
- Velocidad agregada como distancia total / tiempo total de la población
  observada, incluidas sus detenciones.
- Conteos y tasas de callbacks de invasión y colisión por separado, por
  vehículo-km y vehículo-hora. Exposición cero produce una tasa no definida.

`metrics_semantics_version=3` añade medición cada tick de distancia y tiempo
de toda la presencia de los vehículos, incluidas esperas entre viajes y
recuperaciones. Los campos nuevos son `total_observed_distance_m` y
`total_vehicle_time_s`; los campos anteriores conservan su ámbito de viajes
activos. La versión 3 alinea el denominador de tasas con los eventos de todas
las fases.

Para logs versión 2, el analizador utiliza distancia/tiempo de viajes activos
y solamente sus eventos asignados en las tasas; informa aparte todos los
callbacks observados, incluso los de espera. Advierte que ese ámbito no es
el de presencia completa de versión 3. No se reescribieron los logs anteriores.
El informe de la campaña larga previa se conservó en
`mobility_fixes_20260909/previous_campaign_metrics/` como análisis diagnóstico.

La auditoría revisa conteos, claves, tiempos, distancias, correspondencia de
historial/llegadas, umbrales de llegada y exposición. La verificación topológica
de carriles se hizo aparte sobre el mapa, porque un CSV de IDs no demuestra
continuidad dirigida. Se comparan entorno, flota, parámetros, versiones y
hashes de conducción disponibles entre ambos tratamientos; no se infiere
significancia estadística ni se exige cero eventos para aprobar integridad.

### Pruebas y resultados reales

**97 pruebas unitarias aprobadas**, sin omisiones, con `carla-env` y la SDK
de agents configurada. Cubren circuito dirigido, ambos sentidos de s,
destinos próximos dentro de un intervalo de muestreo, retorno inexistente,
continuación de llegada acotada, rechazo del carril contrario, deadline
opcional/CLI, detección de bloqueo, exposición durante espera y poblaciones
de las métricas. Registro: `mobility_fixes_20260909/unit_tests.txt`.

Corridas reales focalizadas con tres vehículos, ambos escenarios, clima
preservado, spawns `[133, 6, 101]`, 20 km/h, delta 0.05 s y ritmo 5×:

| Escenario | Semilla | Duración (s) | completed | aborted | route_failed / blocked / timeout | Colisiones | Invasiones |
|---|---:|---:|---:|---:|---|---:|---:|
| random_baseline | 42 | 600 | 11 | 3 | 0 / 0 / 0 | 0 | 0 |
| history_80_20 | 42 | 600 | 11 | 3 | 0 / 0 / 0 | 0 | 0 |
| random_baseline | 123 | 900 | 11 | 3 | 0 / 0 / 0 | 0 | 9 |
| history_80_20 | 123 | 900 | 15 | 3 | 0 / 0 / 0 | 0 | 0 |

Son 48 llegadas y 12 viajes activos al corte. Las nueve invasiones son del
Cybertruck de baseline/123, viajes 004/005: cinco callbacks `NONE` y cuatro
`Broken`, cerca de las dos curvas ya diagnosticadas. Se preservaron todos;
no se agruparon en accidentes ni se ajustó el seguimiento para eliminarlos.
Las nuevas rutas, finalizaciones y política temporal cambian los viajes
observados: no comparar sus conteos directamente con una corrida previa de
1.800 s como si solo hubiera variado un parámetro del controlador.

| Escenario / semilla | Tiempo medio de completados (s) | Velocidad de presencia (km/h) | Invasiones / vehículo-km |
|---|---:|---:|---:|
| baseline / 42 | 137.241 | 11.566 | 0.000 |
| histórico / 42 | 142.173 | 11.332 | 0.000 |
| baseline / 123 | 205.136 | 10.649 | 1.127 |
| histórico / 123 | 149.280 | 11.060 | 0.000 |

Las distribuciones por ID/categoría están en `metrics/destinations.csv`.
Todos los controles de integridad y ambos pares de condiciones registradas
pasaron. El código de conducción y los datos permanecieron idénticos durante
las cuatro corridas; el análisis y sus pruebas se desarrollaron en paralelo
sin modificar los módulos utilizados para circular.

Carpetas bajo `data/output/`:

- `town01_random_baseline_seed_42_20260909T182939437792Z/`
- `town01_history_80_20_seed_42_20260909T183146958730Z/`
- `town01_random_baseline_seed_123_20260909T183354436607Z/`
- `town01_history_80_20_seed_123_20260909T183701912794Z/`

`data/output/mobility_fixes_20260909/` conserva manifiesto, hashes y copia del
código/datos usados, consolas, `catalog.json`, `arrival_audit.json`, pruebas,
scripts de validación y `metrics/`. No se repitieron aquí seis corridas de
1.800 s ni se cambió la cantidad de vehículos. La limpieza final dejó Town01
disponible, cero vehículos/sensores, modo asíncrono y renderizado activo.

### Qué sigue

Los puntos 1–3 tienen implementación, pruebas y evidencia focalizada. El
siguiente punto es elegir las dos cantidades de vehículos y preparar la
matriz comparativa de ambos selectores, con duración y repeticiones comunes.
Las cantidades no se fijaron ni se aumentó la flota en esta etapa. La campaña
final debe usar una versión congelada y mantener los incidentes como métrica,
sin seleccionar únicamente resultados favorables.

## 2026-09-10 — Guardado de cambios y revisión manual pendiente

El estudiante autorizó Conventional Commits del estado acumulado, por conjuntos
de archivos: rutas de retorno y su validador; llegadas, política temporal y
registro de exposición; analizador de métricas; documentación. Se excluyen
los CSV genéricos, resultados generados, `i-marco_teorico.tex` y
`protocolo-final.tex`.

Se repitió la suite offline con `carla-env` y la SDK de agents disponible:
**97 pruebas aprobadas**, sin omisiones. Registro local en
`data/output/precommit_20260910_unit_tests.txt`. No se inició CARLA, no se
cambió el mapa ni se ejecutaron corridas reales en esta revisión.

El estudiante aún no ha realizado una prueba manual. El siguiente paso es
observar ambos escenarios con tres vehículos, semilla 42, 600 s, renderizado
activo y ritmo 1× cuando prepare CARLA/Town01. Revisar arranques, curvas,
esperas, llegadas y el siguiente viaje; conservar la carpeta de resultados y
anotar vehículo/momento ante dudas. Las invasiones se mantienen como métrica.

Después de contrastar esa revisión con los logs, elegir las dos cantidades
de vehículos que representarán la demanda, fijar condiciones y repeticiones
comunes y congelar la versión para la comparación final. La evidencia actual
demuestra estabilidad en los casos ensayados; aún no completa la validación
del modelo ni la comparación del tercer objetivo específico.

## 2026-09-15 — Auditoría de la ejecución manual y propuesta de demanda

Se revisó la corrida del estudiante del **2026-09-14**:
`data/output/town01_random_baseline_seed_42_20260914T215949497576Z/`.
El usuario confirmó que solo comprobó su finalización, aunque probó el script
de seguimiento del spectator. No se considera realizada una revisión visual
detallada; el spectator de ese ejemplo solo mueve la cámara y espera ticks.

La configuración registra Town01, CARLA 0.9.15, tres vehículos, semilla 42,
600 s, delta 0.05 s, renderizado y ritmo solicitado 1×. Hay 14 viajes iniciados:
11 completados y tres `aborted`, todos con `simulation_end` exactamente al
corte. Cero `route_failed`, `blocked`, `timeout`, colisiones o invasiones.
El analizador no encontró errores de integridad.

Tiempo medio de completados 137.209 s; velocidad de presencia completa
11.565 km/h; distancia 5.782 km; exposición 0.500 vehículo-hora. Categorías
alcanzadas: tres residencia, cuatro trabajo/educación y cuatro servicios/ocio.
Los vehículos 001/002/003 completaron 5/4/2 viajes. El 003 es Audi TT para esta
semilla; llegó a T01_030 y T01_050 y su viaje hacia T01_006 estaba activo al
cierre. Mayor parada muestreada bajo 0.2 m/s: 31.90 s para ese vehículo.
En la flota, 33.18 % del tiempo de viajes activos está bajo ese umbral;
no se identifica por ello la causa de las paradas.

Las once llegadas cumplen los umbrales; máximos absolutos: velocidad
0.000925 m/s, orientación 0.613°, desplazamiento lateral 0.0054 m y distancia
al destino 0.500 m. Las posiciones proyectadas en el OpenDRIVE instalado
coinciden con los IDs de carril registrados. No se reprodujeron sensores.

La comparación con baseline/42 del 2026-09-09 conserva las 14 combinaciones
vehículo/viaje/destino/estado, ambiente y flota. Diferencia del tiempo medio
−0.0318 s y distancia −0.582 m; máximo cambio de duración de un completado
0.500 s. Es repetibilidad funcional cercana, no determinismo por frame:
el día 9 se usaron 5× y no-rendering. La corrida manual no contiene hashes
históricos de código. El clima de ambas incluye precipitación 40 y mojado 80;
no documentarlo como seco.

Se creó `data/output/manual_review_20260915/` con análisis, auditoría, hashes
de los resultados revisados, comparación, contexto del mapa, figura de
trayectorias/velocidades y script de revisión offline. Se comprobó que los
archivos originales permanecieron idénticos. Se usó `carla-env`, sin cliente,
servidor, cambio de mapa ni simulaciones nuevas. La figura se generó con
Matplotlib y se revisó visualmente.

Para justificar demanda se consultaron las guías primarias FHWA 2019 y la
documentación CARLA 0.9.15, con enlaces y distinción entre fuentes y propuesta
en [selección de niveles](seleccion_niveles_demanda.md). Los JSON 20/70 son
de Town03, con 90/120 s y distinto renderizado: no constituyen respaldo
experimental para Town01 ni configuraciones utilizables por este runner.

El OpenDRIVE local da aproximadamente 4.9596 km de centros de carriles
`driving` fuera de intersecciones, muestreados hasta cada metro. N dividido
por esa longitud solo es un índice nominal de carga; no prueba capacidad,
densidad observada, nivel de servicio ni congestión. Se excluyen conectores
de giro superpuestos y se documentan las limitaciones del denominador.

Propuesta pendiente de pilotos: **cinco y veinte como candidatos**, diez
como escalón intermedio. La diferencia por factor cuatro es un contraste de
diseño, no un umbral bibliográfico. Si se requieren regímenes de interacción
distintos y veinte no los representa, explorar treinta/cuarenta antes de
considerar cantidades mayores. No es obligatorio llegar a setenta ni obtener
diferencias significativas. Conservar resultados adversos y las invasiones.

Antes de escalar hay que completar N spawns e historiales: el archivo actual
solo cubre cinco vehículos. El detector `blocked` termina viajes tras 60 s
a baja velocidad sin distinguir semáforo/cola/obstáculo y luego puede iniciar
otro desde la misma posición; estudiar este efecto y fijar su política común
antes de comparar cargas. Registrar motivos de espera y rendimiento real,
fijar clima, flota, duración y código, separar pilotos de evaluación final.
La propuesta de réplicas iniciales con cuatro semillas estima variabilidad;
no garantiza suficiencia estadística.

Se actualizaron README y contexto académico. No se modificaron módulos de
conducción, configuraciones, entradas originales, protocolo ni marco teórico.
No se hicieron commits ni se ejecutaron las pruebas de 5/10/20 vehículos.

## 2026-09-15 — Revisión instrumentada; continuación sin cámaras

Se implementó `scripts/review_trip_simulation.py` con
`src/visual_review.py`, heredando las decisiones de `TripSimulation`.
Registra posición, orientación, velocidad y fases por tick, incluyendo
esperas; añade semáforo y vehículos de la flota a menos de 30 m durante
paradas bajo 0.2 m/s. El modo visual añade tres RGB cenitales de 640 × 360,
18 m de altura y periodo 0.5 s, cola de guardado, índice exacto por
vehículo/frame, hashes y resumen de pérdidas/cadencia. Los sensores quedan
bajo la limpieza del runner. Solo un cliente avanza la simulación.

El timestamp RGB puede diferir del tiempo del mundo del frame declarado.
Se conservan ambos y no se asocia por proximidad temporal. Los intervalos
ocasionales 11/9 frames no se reportan como pérdidas demostradas; los errores
de cola/guardado se distinguen de esa alerta de cadencia. El primer smoke
permitió corregir esa interpretación y se conservaron sus originales.

Las pruebas técnicas con cámaras de 15 s produjeron 90 imágenes cada una,
con vistas legibles de los tres vehículos y limpieza comprobada. Sin embargo,
dos intentos largos de baseline fallaron por `GPUCrash` de Unreal:
`0x887A0020 INTERNAL_ERROR`, pérdida de dispositivo D3D, Intel UHD 770.
El primero guardó 1,179 imágenes y 196.20 s de observación; el segundo,
con RenderOffScreen confirmado en el crash context, dejó 89 PNG y unos
14.15 s de registros parciales, sin índice ni resumen final de captura.
No se consideran corridas completas ni se inventan cierres de sus viajes.

El estudiante preparó CARLA/Town01 y solicitó **continuar sin cámaras**.
Se añadió `--no-cameras`, conservando todos los diagnósticos de fases/paradas
y los sensores de colisión/invasión. La API de argumentos compartida acepta
el parser del script de revisión; el analizador reconoce los hashes de
`visual_review_config.json`. No se cambiaron rutas, controlador, política de
llegada, umbral `blocked`, flota, semilla, clima ni parámetros de conducción.

**107 pruebas aprobadas** con `carla-env` y la SDK de agents. La comprobación
real sin cámaras de 15 s produjo 300 observaciones por vehículo y limpieza
correcta. Después se completaron los dos escenarios a 1×, con renderizado,
semilla 42, tres vehículos y 600 s cada uno:

| Escenario | Completados 001 / 002 / 003 | aborted | blocked / route_failed / timeout | Colisiones / invasiones | Integridad |
|---|---|---:|---|---|---|
| random_baseline | 5 / 4 / 2 | 3 | 0 / 0 / 0 | 0 / 0 | sin errores |
| history_80_20 | 4 / 4 / 3 | 3 | 0 / 0 / 0 | 0 / 0 | sin errores |

Son **22 llegadas, 22 ciclos de llegada/espera/nuevo viaje y 72,000
observaciones**. Los seis `aborted` llevan motivo `simulation_end` y se
registran antes de destruir actores; no son `blocked`. Todas las llegadas
cumplen los umbrales y proyectan sobre los carriles registrados en el
OpenDRIVE local. Máxima parada por escenario: 32.20 y 32.15 s; el umbral
`blocked` permaneció en 60 s. Se revisaron los gráficos de trayectorias y
velocidades de los seis casos vehículo/escenario.

Tiempo medio de completados: 137.209 / 142.205 s; velocidad de presencia
completa: 11.565 / 11.332 km/h (baseline / histórico). La comparación de
condiciones y hashes pasó. Baseline coincide con el manual del 14 de
septiembre en los 14 pares vehículo/viaje, destinos, estados, duraciones y
distancias registradas; no se certifica por ello determinismo por frame.

Ejemplo de interacción: en baseline t≈265 s, el 002 espera 7.225 m detrás
del 003, medidos entre centros, sin colisión. La proximidad y el estado
semafórico aportan contexto, no una clasificación automática de congestión.
`is_at_traffic_light()` puede ser falso mientras BasicAgent frena antes del
trigger; los estados vacíos no descartan una espera semafórica. Esta
limitación está detallada en el informe.

Corridas completas bajo `data/output/`:

- `town01_random_baseline_seed_42_20260916T011215560060Z/`
- `town01_history_80_20_seed_42_20260916T012237341817Z/`

Los nombres usan UTC; fecha local 15 de septiembre. La carpeta
`data/output/visual_review_20260915/` conserva intentos, crash contexts
resumidos, consolas, pruebas, manifiesto, snapshots de código/entradas,
auditorías, hashes de salidas, comparación y figuras. El detalle está en
[el informe](revision_visual_tres_vehiculos.md). CARLA quedó en Town01,
cero vehículos/sensores, modo asíncrono y renderizado activo.

La revisión visual completa queda **pendiente**, por el cambio de alcance
autorizado. Se puede pasar al piloto de cinco vehículos con la evidencia de
integridad de logs, después a diez y veinte. Aún no se fijan los dos niveles
definitivos ni se afirma superioridad de un selector con una sola semilla.
No se exigen cero invasiones. No se aumentó la flota, no se alteraron CSV
genéricos ni documentos TeX y no se hicieron commits.

## 2026-09-15 — Inicio del piloto de cinco y preparación de 10/20

Antes de continuar, el estudiante autorizó Conventional Commits de los
Markdown/Python pendientes. Se revisaron los archivos y se repitieron las
107 pruebas; quedaron `e94fe4e` (instrumentación), `433bd8d` (análisis) y
`77d08bf` (documentación). No se incluyeron TeX, CSV ni resultados generados.

CARLA 0.9.15 respondió en localhost:2000 con Town01, cero vehículos/sensores,
renderizado y el mismo clima lluvioso. Se prepararon configuraciones
separadas para 5/10/20 y sus historiales de 30 visitas por vehículo, en
`config/experiments/scaling_pilots/` y `data/input/histories/Town01/scaling_pilots/`. Los primeros cinco historiales
se preservan y las flotas mayores extienden las menores. El script
`prepare_pilots.py` selecciona spawns dispersos del catálogo, sin crear
actores ni cambiar mapa; conserva manifiesto con criterios, posiciones y
hashes. Cinco usa `[133,6,101,67,43]`; no se fijan demandas definitivas.

Se añadió observación pasiva del semáforo retenido por BasicAgent durante
paradas, sin invocar su detector ni cambiar conducción o umbral `blocked`.
Pasaron 111 pruebas y una comprobación histórica real de 15 s con cinco:
1,500 observaciones, historiales completos y limpieza correcta. Se inició
baseline de 600 s a 1×, sin cámaras; después corresponde histórico con las
mismas condiciones. Diez y veinte solo quedan preparados, sin corridas.

Detalle y resultados de cierre en [pilotos de escalamiento](pilotos_escalamiento.md).
Los cambios nuevos de esta etapa permanecen sin commit.

### Cierre del piloto de cinco

Se completaron ambas corridas de 600 s a 1×, sin cámaras y sin reiniciar el
servidor entre ellas. Baseline: 17 llegadas (5/4/2/3/3 por vehículo) y cinco
`aborted`; histórico: 19 llegadas (4/4/3/5/3) y cinco `aborted`. Todos los
incompletos llevan motivo `simulation_end`. Cero `blocked`, `route_failed`,
`timeout`, colisiones, invasiones o errores de integridad en ambos casos.

`scripts/audit_observations.py` adapta la auditoría a N vehículos y revisó
120,000 observaciones, 36 ciclos completos y las 36 llegadas contra el
OpenDRIVE local. También se inspeccionaron ambas figuras de velocidad y
trayectoria. El registro del semáforo retenido por el agente es pasivo y no
modifica decisiones. Baseline tuvo 39 paradas de al menos 10 s y el histórico
38; máximos 32.20/32.15 s. En cada escenario 37 intervalos incluyen rojo
retenido, y 12/10 incluyen otros vehículos cercanos; los grupos se superponen.
Dos ejemplos de baseline muestran al 002 detrás del 003 y al 005 detrás del
004, con unos 7.2/7.4 m entre centros, sin atribuir congestión automáticamente.

Tiempo medio de completados: 152.476 / 124.595 s. Velocidad de presencia:
11.619 / 11.483 km/h. Presencia bajo 0.2 m/s: 35.15 / 36.02 %.
La menor duración media del histórico no demuestra superioridad con una
semilla y distinta población de recorridos. Los vehículos comunes con las
corridas de tres conservan destinos/estados: duraciones iguales en baseline
y variación máxima de 0.25 s en histórico. El piloto no demuestra todavía
un régimen de alta demanda ni una capacidad máxima del simulador.

Las condiciones y hashes coinciden entre tratamientos. Se preservaron una
copia del código/entradas y hashes de salidas en `data/output/pilot5_20260915/`,
junto con auditorías, consolas, figuras y `metrics/`. Corridas completas:

- `town01_random_baseline_seed_42_20260916T020205968035Z/`
- `town01_history_80_20_seed_42_20260916T021229659097Z/`

La fecha de carpetas es UTC; fecha local 15 de septiembre. El tiempo de pared
observado fue 600.172/600.094 s, próximo a 1×; no se mide rendimiento máximo.
CARLA quedó en Town01, sin vehículos/sensores, asíncrono y con renderizado.

Se puede avanzar al piloto de diez, que tiene 300 visitas de historial;
veinte tiene 600. Ambas configuraciones preservan los vehículos, spawns e
historiales de los prefijos menores. Sus puntos tienen validación geométrica,
pero aún necesitan pruebas reales de creación y circulación. La revisión
visual completa sigue pendiente. Los resultados no cambian el criterio de
conservar invasiones como métrica. No se modificaron los CSV originales ni
los documentos TeX; los nuevos CSV son entradas específicas de estos pilotos.
