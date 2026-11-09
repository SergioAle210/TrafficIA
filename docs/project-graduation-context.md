# Contexto del trabajo de graduación

Actualizado: 2026-09-23. Este documento orienta las decisiones de desarrollo,
validación y análisis de TrafficIA. Distingue los objetivos del protocolo,
las decisiones del estudiante y las propuestas pendientes. No sustituye el
protocolo ni acredita objetivos como cumplidos sin evidencia.

Decisión del 2026-09-23: comparar el cierre `blocked` con una política que
conserva viaje y destino tras 60 s sin superar 0.2 m/s. Experimento diagnóstico
de 100 vehículos, baseline, semilla 210, **300 s por política a 1x**, observando
el espectador sin cámaras. No redefine las demandas ni el controlador común.
La opción predeterminada permanece `terminate`; no adoptar `keep_trip` en
campañas académicas sin revisar resultados y separar avisos, esperas y viajes
completados. Cero cierres `blocked` bajo esa opción no acredita una mejora.
[Protocolo, semántica y resultados](diagnostico_blocked.md).
Estado: implementación y 144 pruebas unitarias disponibles. La técnica de
15 s produjo registros íntegros y vista confirmada por el estudiante, pero
CARLA falló gráficamente durante el cierre. Las dos corridas de 300 s siguen
pendientes; no hay todavía evidencia para comparar o adoptar las políticas.

Presentación de resultados (2026-09-23): [colección de imágenes](../images/README.md)
con pilotos 3/5/10/20 y campañas 20/100, incluidas ambas repeticiones de 3600 s.
El cuerpo sugerido conserva las cuatro métricas del objetivo 3; `blocked`
queda en respaldo diagnóstico. Esto no autoriza ocultar viajes incompletos
al interpretar medias ni convertir los diagramas exploratorios en una
estimación de capacidad. Se añadieron nombres, pies y fragmentos LaTeX sin
modificar los documentos académicos del estudiante.

## Fuentes y prioridad

- [protocolo-final.tex](../../Trabajo-Profesional/protocolo-final.tex), sección «Objetivos»: fuente de los
  objetivos transcritos abajo. Su resumen y metodología delimitan el proyecto.
- [i-marco_teorico.tex](../../Trabajo-Profesional/i-marco_teorico.tex), apartados de ODD, trazabilidad,
  métricas de movilidad y comparación descriptiva: fundamentos conceptuales.
  Esta síntesis no supone una verificación independiente de su bibliografía.
- [README.md](../README.md) y [bitácora](bitacora_simulacion.md): estado de la
  implementación, evidencia experimental y limitaciones técnicas.
- Aclaración del estudiante del 2026-09-09: las invasiones de carril pueden
  formar parte de las métricas; la conducción no necesita ser perfecta.
  Esta decisión actualiza la recomendación técnica anterior de corregir las
  invasiones del Cybertruck como requisito previo para continuar.

Los objetivos académicos se toman del protocolo. Las decisiones posteriores
del estudiante orientan la implementación y deben quedar identificadas como
tales, sin reescribir silenciosamente los objetivos.

## Tema y propósito

**Desarrollo de un generador de tráfico urbano en CARLA mediante un modelo
estocástico de elección de destinos y planificación de rutas para análisis
de movilidad en escenarios simulados.**

Según el protocolo, es un estudio aplicado, experimental y cuantitativo basado
en simulación, con evaluación preliminar y descriptiva. Produce un generador,
configuraciones del ODD, escenarios, datos sintéticos y resultados de análisis.
La comparación estudia el efecto del modelo de elección de destinos sobre la
movilidad. No requiere demostrar que el modelo propuesto mejore todas las
métricas, ni desarrollar autonomía universal o certificar seguridad vial.

## Objetivos del protocolo — transcripción literal

### Objetivo general

Desarrollar un generador de tráfico urbano en CARLA, basado en un modelo estocástico de elección de destinos y planificación de rutas dentro de un dominio operacional definido (ODD), capaz de producir corridas reproducibles y datos sintéticos útiles para el análisis preliminar de movilidad en escenarios urbanos simulados.

### Objetivos específicos

1. Caracterizar el ODD mediante condiciones ambientales, infraestructurales y operacionales del escenario de simulación, con un modelo probabilístico de movilidad basado en tres categorías de destinos y dos niveles de demanda de tráfico.
2. Implementar el modelo propuesto en CARLA mediante la Python API y los módulos básicos de gestión de tráfico, de manera que el escenario soporte agentes vehiculares simultáneos.
3. Comparar el comportamiento del generador contra un escenario base de asignación aleatoria mediante cuatro métricas: distribución de destinos, tiempo promedio de viaje, velocidad media y tasa de incidentes o invasiones de carril.

## Alcance operativo y correspondencia con los objetivos

El protocolo delimita vías urbanas estructuradas, señalización y geometría
consistentes, datos del entorno disponibles, iluminación adecuada, tráfico
controlado y ausencia de fenómenos extremos. Los valores concretos utilizados
deben documentarse; esa descripción general no demuestra que cualquier clima,
mapa o flota esté validado.

| Objetivo | Evidencia actual | Trabajo pendiente |
|---|---|---|
| 1: ODD, categorías y demanda | Town01 y condiciones de corrida registradas; configuración con tres categorías de destinos | Consolidar el ODD experimental y operacionalizar/comparar dos niveles de demanda |
| 2: agentes simultáneos | Pilotos de 5/10/20 vehículos completados en ambos escenarios con semilla 42 y 600 s; rutas de retorno y continuidad de llegada implementadas | Repetir condiciones, otras semillas y mayor duración bajo las flotas candidatas |
| 3: comparación de cuatro métricas | Análisis descriptivo implementado y probado sobre logs; se distinguen poblaciones y exposición | Ejecutar la comparación final de ambos selectores bajo los dos niveles de demanda |

En `config/trips/multi_vehicle_trip.json`, las categorías implementadas son
`residential`, `work_education` y `services_leisure` (residencia,
trabajo/educación y servicios/ocio). Estos nombres proceden de la configuración;
el objetivo específico solo exige tres categorías.

Los dos niveles de demanda no equivalen a los dos selectores de destinos:
`random_baseline` e `history_80_20` son tratamientos que deben compararse bajo
cada nivel de demanda. El estudiante confirmó que los niveles serán
**distintas cantidades de vehículos simultáneos**. Sus dos valores finales
siguen pendientes. El 2026-09-15 se propusieron cinco y veinte como candidatos,
con pilotos de cinco, diez y veinte; la selección se justificará por el ODD,
la respuesta observada y la viabilidad técnica. No son cantidades ya validadas.
Los 20/70 de las configuraciones antiguas corresponden a Town03 y no justifican
directamente los niveles del runner actual en Town01. La definición de demanda
por población simultánea no equivale a flujo de entrada en vehículos/hora.
Procedimiento y fuentes: [selección de demanda](seleccion_niveles_demanda.md).

Actualización bibliográfica del 2026-09-17: se verificó el antecedente
NoCrash, con 20/100 vehículos de fondo en Town01 y 15/70 en Town02. Se
propone revisar los candidatos previos hacia **20 como menor y 100 como
referencia mayor**, con exploración intermedia y posible reducción justificada
por viabilidad medida. Es una adaptación a agentes totales, sin peatones y
otro controlador; no adopción literal ni decisión final del estudiante.
La [justificación y regla de selección](fundamento_demandas_town01.md)
distingue rendimiento del equipo, evidencia vial y datos faltantes. El
barrido no equivale a la comparación definitiva de dos demandas.

El 2026-09-18 el estudiante adopta **20/100 como candidatos a ensayar
directamente**, sin exigir primero el barrido intermedio: semilla 210,
1,800 segundos simulados por escenario y ritmo solicitado 5×. Se prepara una
[campaña secuencial](campana_demanda_20_100.md) para que pueda dejarla
ejecutándose. La prueba técnica corta verifica creación/limpieza y registros;
no sustituye las corridas largas ni establece saturación. Tras analizar esta
semilla se decidirán réplicas y, si hace falta, niveles intermedios. La
comparación conserva el controlador y el historial inicial por vehículo;
cien tiene 3,000 visitas iniciales y veinte 600 para el selector histórico,
que crecen dentro de cada caso. Baseline registra sus nuevas llegadas sin
usar ese bootstrap para decidir destinos. Pasaron 123 pruebas y cuatro casos
técnicos reales de 15 s, con 72,000 observaciones íntegras y limpieza correcta.
Las cuatro corridas largas fueron ejecutadas por el estudiante el día 18;
su análisis del día 19 se registra a continuación.

## Modelo y comparación

- `random_baseline`: asignación aleatoria uniforme entre destinos elegibles.
- `history_80_20`: elección de rutina/exploración apoyada en el historial de
  cada vehículo; el protocolo describe probabilidades 80 % y 20 %.
- Las ramas rutina/exploración no son las tres categorías de destino.
  Tampoco se exige que una muestra finita produzca exactamente 80/20.
- El historial dummy actual es una entrada sintética; no acredita calibración
  frente a una población urbana real.
- Comparar cada par con el mismo mapa, clima, flota, spawns, duración, límites
  temporales y controlador. La regla de destinos y su historial inicial son
  las diferencias previstas entre tratamientos.
- La semilla actual también cambia los modelos vehiculares. Cada par de la
  campaña conserva los mismos modelos, pero las diferencias entre semillas
  mezclan variación de destinos y de flota. Documentarlo; si se desea aislar
  cada efecto, separar semillas o fijar la flota en un diseño posterior.
- Las repeticiones de 600 s con semilla 42 reprodujeron resultados funcionales,
  pero mostraron pequeñas diferencias físicas. No afirmar determinismo exacto
  por frame. Una corrida larga por combinación no mide por sí sola su
  repetibilidad ni justifica conclusiones causales o significancia estadística.

## Criterio acordado sobre incidentes e invasiones

**No exigir cero invasiones ni ajustar el controlador solo para reducir esta
métrica a cero.** Registrar e interpretar el comportamiento observado con
condiciones comparables. No provocar incidentes para obtener variación ni
eliminar vehículos/eventos porque empeoren los resultados.

Separar dos clases de observaciones:

- **Resultados de movilidad:** tiempos, velocidades, destinos, esperas y
  eventos de circulación del modelo. Pueden variar entre escenarios y no
  tienen que ser perfectos para ser analizables.
- **Fallos de implementación o de registro:** rutas truncadas pese a existir
  un recorrido, llegada bloqueada por IDs del mapa, visitas falsas, pérdida
  de eventos o inconsistencias de conteo. Deben corregirse o delimitarse
  explícitamente porque alteran qué viajes y eventos se observan.

Una marca `Broken` o `NONE` no clasifica automáticamente el evento como
infracción, accidente o defecto del programa. Conservar tipo, vehículo, viaje,
posición y fase. Si el seguimiento presenta un comportamiento incompatible
con el ODD o impide ejecutar viajes, investigarlo por esa razón y documentar
cualquier cambio; las invasiones aisladas no son un veto automático al avance.

## Definición de las cuatro métricas

El marco teórico proporciona las siguientes bases. Las decisiones operativas
implementadas para esta etapa se describen abajo. Su uso en la campaña final
debe conservar idéntica definición entre tratamientos.

| Métrica | Base conceptual y criterio de análisis |
|---|---|
| Distribución de destinos | Frecuencia relativa `n_j / N`. Separar destinos asignados y alcanzados; no mezclar sus denominadores. Reportar por ID y, cuando proceda, por categoría. |
| Tiempo promedio de viaje | Promedio de llegada menos salida para viajes completados, en segundos simulados, incluyendo detenciones durante el viaje. Acompañar con cantidad de completados, dispersión y proporción de incompletos. |
| Velocidad media | En registros versión 3, distancia total / tiempo total de presencia de los vehículos, incluyendo esperas. En versión 2 solo se dispone de intervalos de viajes activos y se informa ese ámbito diferente. No es velocidad media en movimiento. |
| Tasa de incidentes o invasiones | Callbacks de invasión por vehículo-kilómetro y colisiones por separado, con conteos absolutos y tasa complementaria por vehículo-hora. En versión 3 se incluyen todas las fases; en versión 2 las tasas se limitan a los eventos asignados a viajes, preservando aparte los demás. |

Para la tasa por distancia, el denominador es la suma de distancias de los
vehículos, expresada en km, bajo el mismo intervalo de observación. Si es cero,
la tasa queda no definida. Los eventos durante espera deben conservarse y su
inclusión debe coincidir con el ámbito declarado; puede añadirse una tasa por
vehículo-hora como análisis complementario.

Un callback, una marca atravesada y una maniobra no son la misma unidad.
La versión actual cuenta callbacks. Si se agrupan en episodios, definir una
regla reproducible, crear una métrica derivada y conservar el registro original.
No sumar colisiones e invasiones en una sola tasa sin justificar su significado.

Los viajes `aborted`, `timeout` o `blocked` no aportan tiempos completos de
llegada. Reportar sus duraciones parciales y frecuencias por separado; no
convertirlos en llegadas ni excluirlos silenciosamente del informe. El promedio
de completados es condicional a completar y puede favorecer a viajes cortos
si el límite temporal corta los largos.

## Tiempo de corrida y límite por viaje

En la campaña diagnóstica anterior, 1.800 s es la duración total de cada corrida
y 300 s era el máximo por viaje. «Presupuesto temporal» significa ese límite;
incluye movimiento y esperas. `timeout` no implica por sí mismo atasco.

Para esta etapa, la configuración multivehículo usa
`max_trip_time_seconds: null`: los viajes pueden continuar hasta el fin de la
corrida. Un viaje activo al corte es `aborted`, no una llegada. Se conserva el
detector de velocidad baja sostenida durante 60 s, que no identifica por sí
solo la causa de la parada. `--max-trip-seconds 300` permite reproducir el
límite anterior y `--max-trip-seconds 0` desactivarlo. **El tiempo de viaje de
la métrica sigue incluyendo todas las esperas**. La política debe ser común
a ambos tratamientos y quedar registrada antes de la comparación final.

## Antecedente diagnóstico al 2026-09-09

- CARLA 0.9.15, Town01; pruebas mediante `carla-env`.
- Tres vehículos; seis corridas de 1.800 s: ambos escenarios y semillas
  42, 7 y 123. Es una campaña diagnóstica, no la comparación final completa.
- 174 llegadas válidas, 0 colisiones, 10 callbacks de invasión; 9 `route_failed`,
  10 `timeout`, 1 `blocked` y 17 `aborted` al corte de duración.
- Las diez invasiones pertenecen al Cybertruck de semilla 123. Conservarlas
  como observaciones; no se exige eliminarlas para cumplir el objetivo 3.
- Los nueve fallos de ruta tienen destino detrás del origen en el mismo
  tramo; el barrido del catálogo encontró 60 pares fallidos de 1.722.
- El bloqueo en T01_067 procede de la igualdad de IDs de tramo/carril durante
  la alineación, pese a continuar sobre el carril dirigido de la ruta.
- La suite existente tiene 80 pruebas aprobadas; aún necesita regresiones
  específicas de esos errores nuevos.
- Evidencia detallada en la entrada del 2026-09-09 de la bitácora y en
  `data/output/reliability_campaign_20260908/long/review/`.

## Avance de los puntos 1–3 y trabajo restante

Se implementaron el retorno dirigido para destinos detrás del origen, la
llegada sobre continuación de carril, el límite temporal opcional y
`scripts/analyze_mobility.py`. El validador `scripts/validate_route_catalog.py`
pasa los 1.722 pares del catálogo y los nueve fallos registrados anteriormente.
Las corridas y resultados posteriores se documentan en la bitácora bajo
«Correcciones de movilidad y análisis de métricas», con fuente y versión.

El analizador entrega `analysis.json`, `summary.csv`, `destinations.csv` y
`report.md`; no sobrescribe logs ni permite reutilizar un directorio de salida.
Conserva las invasiones sin considerarlas por sí solas errores de integridad.
El informe de la campaña anterior sirve como diagnóstico de esa versión, no
como resultado final de la versión corregida. La comparación con distinta
definición de exposición requiere recalcular un ámbito común.

El estudiante ejecutó manualmente baseline/42 el 2026-09-14: 600 s, tres
vehículos, renderizado y ritmo 1×. La auditoría offline del día 15 encontró
11 llegadas, tres viajes activos al corte, cero errores de integridad y cero
colisiones/invasiones/fallos de ruta/bloqueos. Los resultados son muy cercanos
a la corrida del día 9, con diferencias físicas pequeñas. Confirmó que solo
comprobó la finalización: quedan pendientes la observación detallada y el
histórico manual. No tratar esa ejecución como aprobación visual de toda la
conducción ni como validación de mayor demanda.

Antes de escalar, preparar spawns e historiales por vehículo y revisar cómo
se distinguirán colas normales de paradas anómalas: el umbral `blocked` de
60 s termina viajes a baja velocidad sin clasificar la causa. La configuración
actual preserva el clima del servidor; los logs revisados incluyen lluvia.
Fijar explícitamente el clima del ODD y la política de espera antes de la
campaña final. No elegir cantidades por favorecer un selector ni por lograr
cero eventos. Pilotos y resultados finales deben quedar identificados aparte.

La secuencia acordada se conserva como referencia del alcance:

1. Conservar tres vehículos para corregir las rutas de retorno y la llegada
   en uniones de tramos, con regresiones unitarias y pruebas reales focalizadas
   de ambos escenarios. No añadir una campaña de ajustes para lograr cero invasiones.
2. Definir el límite temporal y el tratamiento de viajes incompletos; mantener
   criterios idénticos entre escenarios y registrar motivos de espera cuando
   haga falta distinguirlos.
3. Implementar/verificar las cuatro métricas con unidades, población,
   denominadores y tratamiento de eventos explícitos. Usar la campaña actual
   para probar el análisis, identificándola como diagnóstico de una versión
   con limitaciones conocidas.
4. Al terminar los puntos 1–3, consolidar el ODD, las tres categorías y los
   dos niveles de demanda mediante distintas cantidades de vehículos.
   Definir una matriz que cruce selector y demanda, con semillas/repeticiones
   y flotas comparables. Determinar cantidades según capacidad y propósito,
   no porque cinco vehículos sea un requisito del protocolo.
5. Congelar código y parámetros para la comparación; ejecutar y analizar
   la matriz con tablas, distribuciones y tasas. Si se cambia el controlador,
   versionar y repetir ambos tratamientos afectados. Informar resultados
   favorables, desfavorables y limitaciones sin seleccionar solo corridas limpias.

## Revisión instrumentada del 2026-09-15

Se acordó revisar ambos escenarios con tres vehículos, semilla 42, 600 s,
renderizado y ritmo 1× antes de los pilotos de escalamiento. La observación
con tres cámaras RGB pasó pruebas breves, pero dos intentos de baseline
terminaron por pérdida del dispositivo D3D de Unreal en Intel UHD 770,
incluido un intento con RenderOffScreen. Son resultados incompletos del
entorno de ejecución, no viajes `blocked` ni validaciones completas.

El estudiante autorizó continuar **sin cámaras**. El script de revisión
conserva las decisiones de conducción y registra fases, esperas, semáforos y
vehículos cercanos. Los registros permiten auditar las transiciones, pero no
sustituyen la revisión visual originalmente prevista, que queda pendiente.
No se cambió el detector `blocked`, no se aumentó la flota y no se hicieron
commits. Evidencia y resultados en el
[informe de revisión](revision_visual_tres_vehiculos.md).

Las dos corridas sin cámaras completaron 600 s cada una: once llegadas y
tres viajes activos al corte por escenario, cero `blocked`, fallos de ruta,
colisiones, invasiones o errores de integridad. Se validaron 22 ciclos de
llegada/espera/reinicio en 72,000 observaciones y 107 pruebas unitarias.
Esto permite pasar a pilotos según la integridad de los registros, sin
afirmar que se completó la cobertura visual ni la comparación académica final.

Los pilotos de 5 → 10 → 20 siguen siendo pruebas de escalamiento, no los dos
niveles definitivos del objetivo 1. Los incidentes se conservan como métricas
y las paradas necesitan contexto antes de interpretarse como congestión.
La estabilidad gráfica del equipo también limita qué instrumentación puede
usarse durante la campaña; no debe confundirse con estabilidad del modelo.

## Piloto de cinco y preparación de 10/20

El piloto de cinco del 2026-09-15 completó ambos escenarios (600 s, semilla
42, 1×, sin cámaras): 17/19 llegadas y cinco activos al corte por escenario,
sin errores de integridad, bloqueos, fallos de ruta, colisiones o invasiones.
Se auditaron 36 ciclos completos y pasaron 111 pruebas. Las configuraciones
e historiales de diez y veinte ya están preparados; sigue ejecutar diez y
auditar antes de veinte. Una sola semilla y estos resultados no establecen
capacidad, congestión ni las dos cantidades finales de demanda. Detalle en
[pilotos de escalamiento](pilotos_escalamiento.md).

## Pilotos de diez y veinte completados — 2026-09-17

Diez: 28/33 llegadas en baseline/histórico. Veinte: 55/63. Las cuatro corridas
de 600 s a 1×, semilla 42 y sin cámaras pasaron auditorías: 179 llegadas,
175 ciclos completos, 720,000 observaciones, cero errores de integridad,
bloqueos, fallos de ruta, timeout o colisiones. Hubo dos callbacks de invasión
NONE por escenario con veinte, del Cybertruck 011 en una curva, conservados
sin cambios de controlador. Las 235 decisiones coinciden con la reproducción
de sus semillas e historiales. Las entradas no se sobrescriben; el histórico
acumuló 333 visitas con diez y 663 con veinte, contando sus visitas iniciales.

El equipo sostuvo un ritmo cercano a 1× y no hubo crashes. Se acredita la
ejecución técnica de estos tamaños bajo estas condiciones, no saturación ni
demanda real calibrada. Los modelos/recorridos añadidos también influyen en
las métricas. Faltan repeticiones, semillas y mayor duración para elegir las
dos demandas finales. La revisión visual permanece pendiente. Resultados y
límites en [pilotos de escalamiento](pilotos_escalamiento.md).

## Ampliación larga de veinte completada — 2026-09-17

La ampliación larga de veinte del mismo día ya se completó: semillas 210/109,
ambos selectores, 1,800 s, sin cámaras, ritmo solicitado 5× y alcanzado
1.730–1.832×. Se auditaron 783 llegadas, 781 ciclos, 78 viajes cortados y
861 decisiones, sin errores de integridad. Los 524 callbacks de colisión
pertenecen a dos episodios de baseline; histórico no registró colisiones.
No hubo invasiones, bloqueos, fallos de ruta o timeout. El objetivo 3 debe
distinguir callback de episodio antes de inferir frecuencia de accidentes;
se conservan todas las métricas originales. Los historiales crecieron a
796/791 visitas. Cada tratamiento/semilla tiene una ejecución, por lo que
todavía falta repetición física idéntica y contraste de demandas candidatas.
[Resultados y próximos pasos](campana_larga_veinte_vehiculos.md).

## Gráficas exploratorias de objetivos — 2026-09-17

Se generaron [nueve láminas y una guía](graficas_campana_veinte.md)
con las cuatro corridas largas de veinte. Cubren las cuatro métricas del
objetivo 3, destinos por categoría/ID, tiempos completados y censurados,
velocidad incluyendo esperas y tasas de eventos por vehículo-km. El historial
creciente y las ramas del selector tienen gráficas separadas. Un callback
no es un accidente independiente; la definición formal de episodio sigue
pendiente y no se ocultan los registros originales.

Las relaciones locales v–k, q–k y v–q usan celdas de 50 m por 60 s y medidas
compatibles de distancia/tiempo. Son nubes exploratorias, sin curva impuesta,
capacidad ni densidad crítica estimadas. Cubren 38 tramos rectos, excluyendo
cruces; una parada no se clasifica automáticamente como congestión. Las
cuatro corridas tienen veinte vehículos: no satisfacen por sí solas la
comparación de dos demandas del objetivo 1. El siguiente diseño debe
contrastar cantidades simultáneas bajo condiciones comparables y repetir
las corridas, sin exigir conducción perfecta ni una forma teórica prefijada.

## Contraste 20/100 analizado — 2026-09-19

La campaña del día 18 completó ambos selectores, 1,800 s, semilla 210.
Los hashes de 52 salidas, métricas recalculadas y auditorías respaldan su
integridad; las parejas son comparables. El objetivo 1 ya tiene un contraste
exploratorio de dos cantidades simultáneas. Las [once láminas](graficas_demandas_20_100.md)
cubren las métricas del objetivo 3, el historial creciente y relaciones
locales de tráfico. Pasaron 126 pruebas. No se ejecutó CARLA en este análisis.

Veinte registra 215/196 llegadas y 10.38/10.71 km/h de presencia. Cien registra
173/183 y 2.47/2.55 km/h, con 1,673/1,787 blocked, 340/77 rutas rechazadas y
7/3 invasiones; se mantienen como resultados. La velocidad de los últimos
cinco minutos es 0.529/0.223 km/h con cien. El historial histórico crece de
600 a 796 y de 3,000 a 3,183. Las medias de completados excluyen muchos
intentos fallidos, por lo que deben leerse junto a los estados y la evolución.

Las nubes locales llegan a 140 vehículos/km/carril. No se interpreta ese
máximo ni el flujo máximo muestral como capacidad: hay contactos persistentes,
salidas de proyección driving en baseline y numerosos rechazos de rutas.
`Dwell` significa sin viaje activo e incluye pausas tras fallos. Los
episodios de contacto agrupados son descriptivos y algunos tienen actor ajeno
ambiguo; no son accidentes verificados. La siguiente prioridad es explicar
las primeras secuencias de bloqueo antes de fijar cien como demanda mayor
o planear cantidades intermedias/réplicas. Una semilla no establece
significancia ni superioridad del selector. No se exige cero invasiones.

## Actualización del 23 de septiembre: repetibilidad con semilla 210

La [segunda campaña de 3600 s](repetibilidad_demandas_3600.md) preserva
27 archivos de código/entradas de la primera y las condiciones registradas.
Veinte produce métricas agregadas cercanas (423/398 llegadas); cien alcanza
237/254 frente a 252/252, con variación importante de callbacks e invasiones.
No se demuestra determinismo exacto ni se estima variabilidad entre semillas
con estas dos repeticiones. Continúa pendiente explicar contactos y evaluar
la intervención del detector blocked: sigue terminando viajes por baja
velocidad prolongada; todavía no se implementó conservar el destino.
Los nuevos resultados no invalidan por sí solos las métricas ni certifican
capacidad vial; la interpretación debe conservar esta limitación.

## Actualización del 22 de septiembre: una hora por combinación

La [campaña de 3600 s](graficas_demandas_3600.md), semilla 210,
20/100 vehículos y ambos selectores, terminó con registros íntegros.
Veinte mantiene 422/397 llegadas sin blocked ni route_failed; cien produce
252/252 llegadas con 3932/4147 blocked y 1280/235 rechazos. La duración
adicional permite estudiar evolución temporal, pero no sustituye réplicas
ni valida como capacidad los estados con contactos persistentes. Se
conservan invasiones como métrica y todos los intentos fallidos.
Doce láminas incluyen una comparación entre mitades de las mismas corridas.
Son análisis descriptivos; no se declara superioridad causal ni se fija
la demanda definitiva. El controlador permanece intacto.

## Restricciones de trabajo vigentes

- El 2026-09-20 se añadió una [lectura con líneas guía](lectura_diagramas_y_guias.md)
  a la lámina de relaciones de tráfico, conservando datos y figuras previas.
  Son resúmenes de exposición por bandas de densidad, no un ajuste de modelo
  ni una estimación de capacidad. Las frecuencias 78.14 %/79.18 % de rutina
  respaldan el selector probabilístico; no validan por sí solas el diagrama
  fundamental. No se impone una forma teórica como criterio de éxito del
  objetivo 3. Pasaron 130 pruebas; sin simulaciones nuevas ni commits.

- Preparación autorizada el 2026-09-18 para 20/100, ambos selectores, semilla
  210, sin cámaras y 5× solicitado. La campaña larga queda al estudiante;
  las comprobaciones técnicas breves se identifican por separado. No se
  reinicia CARLA ni se cambia el mapa. No hay autorización nueva de commits.

- Ampliación autorizada el 2026-09-17: veinte vehículos, semillas 210/109,
  ambos selectores, 1,800 s simulados y ritmo 5× solicitado por el estudiante.
  Se mantiene el controlador; las semillas varían destinos y modelos.
  Los historiales iniciales permanecen fijos y crecen dentro de cada corrida.
  [Protocolo y resultados](campana_larga_veinte_vehiculos.md). Esta campaña
  sigue siendo validación exploratoria, sin fijar demandas definitivas.

- El 2026-09-17 el estudiante pidió explicitar la influencia de las correcciones
  de conducción sobre incidentes y autorizó el piloto de diez cuando prepare
  CARLA/Town01. Se mantiene el controlador común, sin exigir cero eventos;
  la interpretación y los cambios están en [control e incidentes](control_e_incidentes.md).
  Posteriormente autorizó ejecutar diez y después veinte, con auditoría entre
  flotas. No hay nueva autorización de commits ni de reinicio/cambio de mapa
  por el asistente. Los pilotos conservan 600 s, semilla 42 y ambos selectores.

- El 2026-09-15 se autorizó guardar los Markdown/Python pendientes antes
  del piloto de cinco. Se crearon `e94fe4e`, `433bd8d` y `77d08bf`.
  La preparación y los cambios posteriores del piloto quedan sin commit.
  Se autorizó ejecutar cinco y dejar configuraciones e historiales de diez
  y veinte listos; en esa etapa aún no se habían ejecutado. Su validación
  posterior del día 17 se documenta arriba.

- El estudiante autorizó el 2026-09-10 Conventional Commits de los cambios
  actualmente acumulados, agrupados por conjuntos de archivos. Esta indicación
  sucede a la autorización del 2026-09-09; no autoriza commits automáticos
  de trabajo futuro.
- Conservar corridas y logs originales; crear nuevos directorios para versiones
  o diagnósticos. Documentar cambios de significado de las métricas.
- No modificar los CSV genéricos ni `i-marco_teorico.tex` en tareas de simulación.
  El protocolo y el marco se consultaron como fuentes para este documento.
- Consultar este contexto antes de proponer prioridades y registrar nuevos
  hallazgos en la bitácora. No convertir observaciones de seguridad en objetivos
  académicos adicionales sin acordarlo con el estudiante.
