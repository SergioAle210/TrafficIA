# Contexto del trabajo de graduación

Actualizado: 2026-09-09. Este documento orienta las decisiones de desarrollo,
validación y análisis de TrafficIA. Distingue los objetivos del protocolo,
las decisiones del estudiante y las propuestas pendientes. No sustituye el
protocolo ni acredita objetivos como cumplidos sin evidencia.

## Fuentes y prioridad

- [protocolo-final.tex](protocolo-final.tex), sección «Objetivos»: fuente de los
  objetivos transcritos abajo. Su resumen y metodología delimitan el proyecto.
- [i-marco_teorico.tex](i-marco_teorico.tex), apartados de ODD, trazabilidad,
  métricas de movilidad y comparación descriptiva: fundamentos conceptuales.
  Esta síntesis no supone una verificación independiente de su bibliografía.
- [README.md](README.md) y [bitácora](docs/bitacora_simulacion.md): estado de la
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
| 2: agentes simultáneos | Tres vehículos realizan viajes sucesivos; existen rutas, sensores e historiales individuales | Corregir los fallos identificados de planificación y reconocimiento de llegada |
| 3: comparación de cuatro métricas | Ambos escenarios generan logs; campaña de seis corridas largas revisada | Definir unidades y agregación, implementar el análisis comparable y presentar resultados descriptivos |

En `config/multi_vehicle_trip.json`, las categorías implementadas son
`residential`, `work_education` y `services_leisure` (residencia,
trabajo/educación y servicios/ocio). Estos nombres proceden de la configuración;
el objetivo específico solo exige tres categorías.

Los dos niveles de demanda no equivalen a los dos selectores de destinos:
`random_baseline` e `history_80_20` son tratamientos que deben compararse bajo
cada nivel de demanda. El estudiante confirmó que los niveles serán
**distintas cantidades de vehículos simultáneos**. Sus dos valores y su
justificación quedan para después de los puntos 1–3 (correcciones, límites
temporales y métricas). No se da por decidido que sean tres y cinco vehículos.

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
marcadas como propuestas deben fijarse antes de la campaña comparativa final.

| Métrica | Base conceptual y criterio de análisis |
|---|---|
| Distribución de destinos | Frecuencia relativa `n_j / N`. Separar destinos asignados y alcanzados; no mezclar sus denominadores. Reportar por ID y, cuando proceda, por categoría. |
| Tiempo promedio de viaje | Promedio de llegada menos salida para viajes completados, en segundos simulados, incluyendo detenciones durante el viaje. Acompañar con cantidad de completados, dispersión y proporción de incompletos. |
| Velocidad media | Cociente entre distancia total y tiempo total del mismo conjunto/ámbito. Precisar si incluye todo el periodo de presencia o solo viajes; conservar las detenciones del ámbito escogido. No mezclarlo con velocidad media en movimiento. |
| Tasa de incidentes o invasiones | Eventos de una clase divididos por exposición de esa población. Propuesta: callbacks de invasión por vehículo-kilómetro recorrido y colisiones por separado, conservando también conteos absolutos. |

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

En la campaña actual, 1.800 s es la duración total de cada corrida y 300 s es
el máximo por viaje. «Presupuesto temporal» significa ese límite por viaje;
incluye movimiento y esperas. `timeout` no implica por sí mismo atasco.

Pendiente: decidir y documentar una política uniforme que permita viajes
largos con esperas razonables y distinga falta de progreso. No aumentar el
límite hasta que desaparezcan los fallos sin evaluar su efecto. Aunque se use
un contador separado para detectar estancamiento, **el tiempo de viaje usado
en la métrica debe seguir incluyendo las esperas**, tal como define el marco.

## Estado comprobado al 2026-09-09

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

## Próximo trabajo propuesto

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

## Restricciones de trabajo vigentes

- El estudiante autorizó Conventional Commits del estado acumulado el
  2026-09-09 antes de continuar los puntos 1–3. Los cambios posteriores
  quedan sin commit hasta una nueva indicación.
- Conservar corridas y logs originales; crear nuevos directorios para versiones
  o diagnósticos. Documentar cambios de significado de las métricas.
- No modificar los CSV genéricos ni `i-marco_teorico.tex` en tareas de simulación.
  El protocolo y el marco se consultaron como fuentes para este documento.
- Consultar este contexto antes de proponer prioridades y registrar nuevos
  hallazgos en la bitácora. No convertir observaciones de seguridad en objetivos
  académicos adicionales sin acordarlo con el estudiante.
