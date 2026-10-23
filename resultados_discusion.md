# Plan para elaborar Resultados y Discusión

Preparado el 28 de septiembre de 2026 para trabajar en `C:/CARLA/Trabajo-Profesional`.
Este archivo contiene instrucciones de redacción, fuentes y criterios de revisión;
no constituye el capítulo ni acredita trabajo que todavía no se haya realizado.

## 1. Encargo y producto esperado

Elaborar un borrador académico de **Resultados y Discusión** del generador de
tráfico urbano en CARLA, respetando el diseño experimental descrito en este
plan. Describir procedimientos, observaciones e interpretaciones
**en tiempo pasado**: «se ejecutaron», «se registró», «se observó», «los resultados
sugirieron» o «no se pudo determinar».

Separar los resultados observados de sus posibles explicaciones. No convertir
hipótesis en causas comprobadas ni afirmar superioridad general del modelo.
Su propósito fue introducir una selección estocástica estructurada de destinos
y producir datos sintéticos útiles para analizar movilidad; no necesariamente
minimizar tiempos, aumentar velocidades o eliminar incidentes.

Antes de redactar, construir las tablas resumen y verificar la procedencia de
las cifras. Entregar el borrador, las tablas, la selección de figuras con pies
y un registro breve de fuentes y limitaciones pendientes.

La redacción se realizará en estos archivos del proyecto del documento:

- [j-resultados.tex](C:/CARLA/Trabajo-Profesional/j-resultados.tex).
- [j-discusion.tex](C:/CARLA/Trabajo-Profesional/j-discusion.tex).

Conservar los comandos de capítulo, etiquetas y convenciones LaTeX existentes.
No escribir números de sección o figura manualmente. Mantener intactos los
demás capítulos y archivos ajenos a esta redacción.

No ejecutar CARLA, generar nuevas corridas, cambiar parámetros, sobrescribir
datos o figuras originales ni hacer commits. Las fuentes experimentales se
consultarán en modo de lectura; la escritura de capítulos y la incorporación
de las figuras seleccionadas corresponderán a Trabajo-Profesional.

## 2. Proyecto de redacción y fuentes de datos

**Directorio de trabajo y de entrega: `C:/CARLA/Trabajo-Profesional`.**

Este plan es autocontenido respecto al diseño experimental y los criterios
de análisis. No requiere consultar archivos de contexto del proyecto que
generó las simulaciones ni reconstruir conversaciones anteriores.

Las rutas de datos y gráficas indicadas en las secciones 4 y 8 son fuentes
externas al documento. Al preparar esta revisión, los CSV, manifiestos y la
colección de figuras se localizaron en `C:/CARLA/TrafficIA/data/output` y
`C:/CARLA/TrafficIA/images`; no se encontraron copias equivalentes en
Trabajo-Profesional. Esas rutas se conservan para acceder a evidencia real,
no como ubicación de trabajo para redactar.

Las rutas de corridas dentro de `campaign.json` se resuelven bajo
`C:/CARLA/TrafficIA/data/output`. Las rutas del catálogo de figuras que
comienzan con `images/` o `data/output/` se resuelven bajo
`C:/CARLA/TrafficIA`. Si se trasladan los datos, comprobar su nueva ubicación
y actualizar las referencias; no sustituir todas las raíces suponiendo que
los archivos ya fueron copiados.

Si la otra sesión no tiene acceso al disco local, adjuntar o trasladar los
archivos correspondientes. No afirmar que se inspeccionó un archivo solo
porque se recibió su ruta. Si falta evidencia necesaria, solicitarla y
declarar el punto pendiente, sin reconstruir cifras a partir de suposiciones.

Utilizar configuraciones, manifiestos y registros de las corridas para
establecer lo efectivamente ejecutado. Los informes derivados ayudarán a
localizar y contrastar cifras. Los dos niveles del análisis principal serán
20 y 100 vehículos; esta elección no equivale a demostrar capacidad máxima
del mapa o del equipo.

## 3. Diseño experimental que debe describirse

El análisis principal comprendió cuatro configuraciones y **dos ejecuciones
de cada configuración: ocho corridas**, todas de 3600 segundos simulados y
semilla 210.

| Demanda | Vehículos simultáneos | Selector | Identificador técnico | Semilla | Duración |
|---|---:|---|---|---:|---:|
| Baja | 20 | Asignación aleatoria | `random_baseline` | 210 | 3600 s simulados |
| Baja | 20 | Modelo estocástico con historial 80/20 | `history_80_20` | 210 | 3600 s simulados |
| Alta | 100 | Asignación aleatoria | `random_baseline` | 210 | 3600 s simulados |
| Alta | 100 | Modelo estocástico con historial 80/20 | `history_80_20` | 210 | 3600 s simulados |

- **Repetición 1:** noche del 21 al 22 de septiembre de 2026.
- **Repetición 2:** noche del 22 al 23 de septiembre de 2026.

Estas fechas corresponden a Guatemala; los identificadores de carpetas
utilizaron UTC. Las repeticiones compartieron semilla; no fueron ejecuciones
con semillas independientes ni una simulación concatenada de 7200 segundos.
Presentar ambas, sin seleccionar únicamente la que favorezca a un modelo.

Comparar primero aleatorio frente a histórico dentro de **la misma demanda
y repetición**. Después analizar el cambio observado entre 20 y 100 vehículos
y la variación entre repeticiones.

Las pruebas de 3, 5, 10 y 20 vehículos durante 600 s fueron antecedentes
funcionales o incrementales. Las campañas de 1800 s fueron exploratorias.
No incorporarlas como niveles adicionales de demanda ni como repeticiones
equivalentes de las campañas de 3600 s. La frase «única semilla experimental»
se refiere al experimento principal: antes sí se utilizaron otras semillas.

## 4. Ubicación exacta de campañas, tablas y corridas

### Repetición 1

- [Carpeta de campaña](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z).
- [Manifiesto campaign.json](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/campaign.json).
- [Análisis estructurado](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/metrics/analysis.json).
- [Tabla resumen](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/metrics/summary.csv).
- [Distribución de destinos](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260922T040147250610Z/metrics/destinations.csv).
- [Derivados, figuras y validaciones](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_20260922).

### Repetición 2

- [Carpeta de campaña](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260923T045032867422Z).
- [Manifiesto campaign.json](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260923T045032867422Z/campaign.json).
- [Análisis estructurado](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260923T045032867422Z/metrics/analysis.json).
- [Tabla resumen](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260923T045032867422Z/metrics/summary.csv).
- [Distribución de destinos](C:/CARLA/TrafficIA/data/output/demand20_100_seed_210_20260923T045032867422Z/metrics/destinations.csv).
- [Derivados, figuras y validaciones](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923).

### Comparación ya disponible

- [Diferencias numéricas entre repeticiones](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923/repeat_comparison.csv).
- [Comprobaciones de comparación](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923/repeat_comparison.json).
- [Informe comparativo](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923/comparacion_repeticiones.md).
- [Auditoría de la segunda campaña](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923/chart_input_review.json).
- [Reauditoría de la primera campaña](C:/CARLA/TrafficIA/data/output/visual_analysis20_100_3600_repeat_20260923/previous_review/chart_input_review.json).

Las carpetas de derivados incluyen `time_series.csv`, `flow_cells.csv`,
`flow_guides.csv`, `guide_method.json`, `half_comparison.csv`,
`derivation_manifest.json` y `validation.json`. Consultar estos archivos al
describir series temporales, mitades o relaciones de tráfico.

### Directorios originales de las ocho corridas

| Repetición | Vehículos | Selector | Carpeta original |
|---|---:|---|---|
| 1 | 20 | Aleatorio | [Corrida R1-20-A](C:/CARLA/TrafficIA/data/output/town01_random_baseline_seed_210_20260922T040147474227Z) |
| 1 | 20 | Histórico | [Corrida R1-20-H](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260922T043508477380Z) |
| 1 | 100 | Aleatorio | [Corrida R1-100-A](C:/CARLA/TrafficIA/data/output/town01_random_baseline_seed_210_20260922T050808887501Z) |
| 1 | 100 | Histórico | [Corrida R1-100-H](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260922T081339893367Z) |
| 2 | 20 | Aleatorio | [Corrida R2-20-A](C:/CARLA/TrafficIA/data/output/town01_random_baseline_seed_210_20260923T045033104234Z) |
| 2 | 20 | Histórico | [Corrida R2-20-H](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260923T052437426599Z) |
| 2 | 100 | Aleatorio | [Corrida R2-100-A](C:/CARLA/TrafficIA/data/output/town01_random_baseline_seed_210_20260923T060003686823Z) |
| 2 | 100 | Histórico | [Corrida R2-100-H](C:/CARLA/TrafficIA/data/output/town01_history_80_20_seed_210_20260923T090349910948Z) |

Dentro de cada directorio, consultar según la métrica:

| Archivo | Uso |
|---|---|
| `run_config.json` | Configuración efectiva, flota, ambiente y semántica de las métricas |
| `trips_log.csv` | Viajes, destinos, tiempos, estados y motivos de terminación |
| `metrics_summary.csv` | Agregados y exposición total |
| `vehicle_history.csv` | Historial inicial y visitas completadas |
| `events_log.csv` | Callbacks de colisiones e invasiones, incluidos eventos sin viaje activo |
| `observation_log.csv` | Observaciones por frame, fases y contexto; archivo grande |
| `trajectory_log.csv` | Trayectorias muestreadas durante los viajes |
| `arrival_log.csv` | Evidencia de llegadas |
| `route_log.csv` y `control_log.csv` | Revisión técnica de rutas y controles si surge una discrepancia |

Las campañas conservan auditorías y hashes para verificar la procedencia.
Utilizar las condiciones registradas de cada ejecución al explicar los datos;
no atribuirles cambios posteriores que no formaron parte del experimento.

## 5. Condiciones que deben verificarse

Comprobar igualdad, dentro de cada par, de cantidad de vehículos, mapa Town01,
condiciones ambientales, modelos vehiculares, posiciones iniciales, duración,
parámetros generales de conducción y reglas de terminación. Describir el ODD
registrado, sin sustituirlo por condiciones ideales no comprobadas.

La diferencia prevista entre tratamientos fue la selección de destinos y el
uso del historial. El modelo histórico comenzó con 30 visitas sintéticas por
vehículo y agregó solo las llegadas completadas; el aleatorio no utilizó ese
bootstrap para elegir destinos. Cada repetición reinició sus entradas, sin
continuar el historial final de la anterior.

La misma semilla fue un mecanismo de control pseudoaleatorio; no garantizó
igualdad de trayectorias, incidentes ni secuencias físicas entre ejecuciones.

En estas campañas se utilizó la regla que terminó el intento tras 60 s sin
superar 0.2 m/s. El vehículo no se eliminó por ese estado; pudo recibir otro
viaje después de la espera. Describir la política registrada sin incorporar
pruebas técnicas o alternativas ajenas a las ocho corridas principales.

Distinguir 3600 s simulados del tiempo real de procesamiento. El ritmo de 5x
fue solicitado, no garantizado. Las horas de ejecución de la campaña completa
no equivalieron a la duración de una sola corrida y no fueron una métrica de
movilidad. Describir restricciones de hardware solo como contexto y limitación,
salvo que exista una medición específica de rendimiento.

## 6. Preparación de tablas y revisión de datos

Inventariar los archivos de las ocho corridas y revisar esquemas, unidades,
configuraciones y auditorías. Utilizar los resúmenes estructurados como punto
de partida y contrastarlos con los registros pertinentes. Procesar archivos
grandes por bloques cuando haga falta; no cargar indiscriminadamente todos
los CSV de pruebas antiguas ni sumar registros duplicados de derivados.

Preparar una tabla principal de **ocho filas**, identificando repetición,
demanda y selector. Incluir semilla, duración simulada, viajes iniciados,
completados e incompletos, tiempo medio de completados, velocidad media,
conteos y tasas de colisión e invasión por separado, y sus denominadores
de distancia y tiempo de exposición. Dividirla en dos tablas si es necesario
para que sea legible, conservando los identificadores de corrida.

Preparar otra tabla de destinos asignados y alcanzados, por categoría y por
identificador cuando aporte información. Registrar la población de cada
porcentaje y diferenciar decisiones, visitas y vehículos.

Revisar valores atípicos y discrepancias antes de explicarlos. Los resúmenes
incluyeron viajes completados extremadamente breves, de aproximadamente
0.05 s en algunos casos de cien vehículos: contrastar su secuencia antes de
interpretarlos. No eliminarlos ni calificarlos automáticamente como errores.
Si no se resuelve una anomalía, declararla como limitación pendiente.

Mantener un registro de qué archivo y campo respaldaron cada tabla. Si un
indicador no estuvo registrado, marcarlo como no disponible; no inferirlo
solo de la apariencia de una gráfica. Evitar precisión decimal injustificada.

## 7. Definiciones de las cuatro métricas principales

| Métrica | Definición y límites |
|---|---|
| Distribución de destinos | Frecuencias de asignación y de llegada, con denominadores separados. El 80/20 describió ramas del selector, no cuotas exactas entre categorías o llegadas. |
| Tiempo promedio de viaje | Promedio de viajes completados, incluyendo sus detenciones. Acompañar con cantidad de completados y proporción de incompletos; no representó tiempos completos de quienes no llegaron. |
| Velocidad media | Distancia total dividida entre tiempo total de presencia vehicular, incluidas esperas. No fue velocidad media exclusivamente en movimiento. |
| Tasa de incidentes/invasiones | Conteos y tasas por vehículo-kilómetro, con colisiones e invasiones separadas y exposición coherente. Si se utiliza vehículo-hora, declararlo como denominador complementario. |

Un callback de colisión no equivalió a un accidente independiente. Los
contactos persistentes y la observación por más de un sensor pudieron generar
múltiples registros. Si se presentan episodios agrupados, explicar la regla
documentada y conservar la distinción respecto al conteo bruto.

`blocked`, `route_failed` y `aborted` serán información de terminación y
limitaciones, **no una quinta métrica académica**. No será necesario incluir
todas sus gráficas en el cuerpo, pero sí declarar su efecto sobre intentos,
asignaciones y selección de viajes que lograron llegar. No ocultar datos
desfavorables al retirar una lámina diagnóstica.

## 8. Figuras: rutas, selección y uso

| Recurso | Ruta |
|---|---|
| Índice y explicación | [images/README.md](C:/CARLA/TrafficIA/images/README.md) |
| Galería con filtros | [images/index.html](C:/CARLA/TrafficIA/images/index.html) |
| Catálogo de procedencia, pies y hashes | [images/catalogo.json](C:/CARLA/TrafficIA/images/catalogo.json) |
| Fragmentos LaTeX | [images/figuras_resultados.tex](C:/CARLA/TrafficIA/images/figuras_resultados.tex) |
| Figuras de repetición 1 | [07_demanda_20_100_3600s_repeticion_1](C:/CARLA/TrafficIA/images/resultados/07_demanda_20_100_3600s_repeticion_1) |
| Figuras de repetición 2 | [08_demanda_20_100_3600s_repeticion_2](C:/CARLA/TrafficIA/images/resultados/08_demanda_20_100_3600s_repeticion_2) |
| Comparación de repeticiones | [09_comparacion_dos_repeticiones](C:/CARLA/TrafficIA/images/resultados/09_comparacion_dos_repeticiones) |
| Antecedentes y diagnósticos | [images/respaldo_tecnico](C:/CARLA/TrafficIA/images/respaldo_tecnico) |

El catálogo reunió 59 figuras de resultados y 18 de respaldo. No insertar
automáticamente las 77: seleccionar por función explicativa y evitar
repetir la misma información en una tabla y varias figuras.

Priorizar estos sufijos de archivo, disponibles para cada repetición:

- `distribucion_destinos_por_categoria`: comparación de asignados y alcanzados.
- `tiempos_de_viajes_completados_y_cobertura_de_llegadas`: tiempos y población observada.
- `evolucion_velocidad_y_tiempo_a_baja_velocidad`: comportamiento temporal.
- `colisiones_e_invasiones_conteos_y_tasas`: incidentes por exposición.

Usar la comparación conjunta
`n020_100_3600s_semilla210_comparacion_movilidad_incidentes_y_cobertura.png`
y la figura de velocidad/llegadas entre repeticiones de la carpeta 09 para
evitar seleccionar una ejecución favorable. El catálogo proporciona sus
rutas completas y fuentes.

El detalle de los 42 destinos y el crecimiento del historial servirán como
apoyo cuando expliquen un hallazgo; los pilotos irán en una síntesis funcional
breve o en anexos. Los diagramas `relaciones_flujo_densidad_velocidad_con_lineas_guia`
deberán acompañarse de `mapa_de_tramos_y_cobertura_de_densidades` y de los
límites del método. No convertirlos en una quinta métrica principal.

Cada figura deberá indicar población, demanda, selector, repetición, semilla,
duración y unidades pertinentes. Adaptar sus pies al pasado y a la numeración
del manuscrito: las referencias internas a «lámina 03», por ejemplo, pertenecieron
al informe original. PNG y SVG son formatos de una misma figura, no evidencias
distintas. Los PNG pueden insertarse con `graphicx`.

Para la integración, copiar únicamente las figuras seleccionadas a
`C:/CARLA/Trabajo-Profesional/images/resultados/`, creando esa carpeta si
no existe y conservando sus nombres descriptivos. No reemplazar imágenes
existentes con contenido diferente. Adaptar los fragmentos preparados para
usar `images/resultados/<nombre>.png` al compilar desde Trabajo-Profesional;
sus rutas originales no son automáticamente válidas en este proyecto.

## 9. Estructura propuesta del capítulo

### Resultados

1. Evidencia breve de implementación y funcionamiento simultáneo: pilotos
   y crecimiento del historial, vinculados al objetivo de agentes múltiples.
2. Escenarios evaluados: ODD registrado, demandas, ocho corridas y tabla resumen.
3. Distribución de destinos: categorías, asignaciones y llegadas.
4. Tiempo de viaje: medias y distribución de completados, con cobertura.
5. Velocidad media y evolución temporal de la circulación.
6. Colisiones e invasiones: conteos, tasas y unidad de observación.
7. Repetibilidad descriptiva: coincidencias y diferencias entre las dos ejecuciones.

Para cada métrica, presentar los pares 20 aleatorio/histórico y 100
aleatorio/histórico dentro de cada repetición. Analizar después el contraste
de demandas. Utilizar diferencias absolutas y porcentuales cuando proceda;
si el valor de referencia fue cero, el cambio porcentual quedó no definido.

### Discusión

Relacionar los hallazgos con las preguntas de análisis: caracterización
del ODD y de las dos demandas, implementación de agentes simultáneos y
comparación de las cuatro métricas. Explicar qué evidencia respaldó cada
aspecto y qué no pudo acreditarse.

Distinguir ejecución e integridad de registros de validez del comportamiento
vial. Finalizar una corrida y conservar archivos consistentes no demostró
por sí solo que todas las interacciones fueran representativas del tráfico real.
Discutir terminaciones, rechazos de ruta, contactos persistentes y selección
de viajes completados sin atribuir automáticamente su causa a congestión normal.

Como complemento, interpretar flujo, densidad y velocidad dentro del ámbito
medido: tramos y ventanas locales de Town01, no toda la red. Las guías fueron
resúmenes descriptivos; no constituyeron un ajuste a Greenshields ni una
estimación de capacidad. Explicar cobertura y exclusiones de proyección
driving a partir de los archivos del método. No forzar las gráficas a imitar
una parábola teórica ni afirmar que la identidad q=k·v validó el modelo completo.

Utilizar bibliografía existente y verificable cuando ayude a interpretar
los resultados. Distinguir antecedente, adaptación experimental e inferencia;
no inventar referencias, páginas, DOI ni apoyos bibliográficos.

## 10. Límites estadísticos y controles de interpretación

- Una semilla principal y dos repeticiones de esa semilla no representaron
  una campaña con semillas independientes. No generalizar a todas las semillas.
- No tratar vehículos, viajes, frames o ventanas de una corrida automáticamente
  como réplicas independientes. No aplicar pruebas de significancia ni
  intervalos que supongan un diseño inexistente.
- Sí pueden describirse mediana, cuartiles o desviación estándar de los viajes
  dentro de una corrida, identificando esa población. No presentarlos como
  variabilidad entre semillas o incertidumbre de una media poblacional general.
- No inventar repeticiones ni ignorar las dos que sí se ejecutaron. Conservar
  ambos resultados por separado; no sustituirlos por un único promedio global.
- No declarar superioridad general del selector: con cien vehículos el orden
  de velocidades entre modelos cambió entre las dos repeticiones. Verificar
  este y otros contrastes contra las tablas antes de redactar conclusiones.
- Evitar «se demostró congestión», «se alcanzó la capacidad del mapa» o
  «el generador funcionó perfectamente» sin evidencia específica suficiente.
- Emplear «bajo las condiciones evaluadas», «en las corridas realizadas» y
  «para la semilla 210» cuando delimiten una conclusión.

## 11. Secuencia de trabajo y criterios de entrega

1. Trabajar en `C:/CARLA/Trabajo-Profesional`; leer este plan, los manifiestos
   y los análisis disponibles, y confirmar acceso a los datos.
2. Inventariar los archivos de las ocho corridas y revisar sus auditorías.
3. Construir tablas con unidades, poblaciones y fuentes antes de redactar.
4. Contrastar anomalías y dejar explícitas las que no se hayan podido resolver.
5. Seleccionar figuras del catálogo y relacionarlas con cada pregunta de análisis.
6. Redactar Resultados en pasado, con comparaciones dentro de demanda/repetición.
7. Redactar Discusión en pasado, separando observaciones, hipótesis y limitaciones.
8. Revisar concordancia entre cifras, tablas, figuras, fuentes y conclusiones.

La entrega deberá contener un borrador conectado, no una sucesión de pies de
figura; tablas legibles de las ocho corridas; figuras seleccionadas con pies;
trazabilidad suficiente de las cifras; y limitaciones o datos faltantes.
Ningún resultado deberá presentarse como superioridad causal o generalización
estadística no respaldada. Omitir del capítulo los detalles de depuración,
pruebas unitarias, comandos o capturas de errores que no aporten al análisis.
