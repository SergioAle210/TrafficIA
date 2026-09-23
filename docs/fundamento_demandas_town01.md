# Fundamento para seleccionar dos demandas en Town01

Fecha: 2026-09-17. Investigación bibliográfica y comprobaciones de solo lectura.
**Recomendación: veinte como candidato menor y cien como referencia publicada
para el candidato mayor, condicionado a pilotos propios. No se han fijado ni
validado las dos cantidades definitivas.**

**Actualización del 2026-09-18:** el estudiante solicita pasar directamente a
20/100, semilla 210, ambos selectores, 1,800 s y 5× solicitado. Esta decisión
sustituye el barrido intermedio como siguiente acción. La
[campaña de 20/100](campana_demanda_20_100.md) prepara entradas completas,
pruebas técnicas breves y un comando para que el estudiante deje las cuatro
corridas largas ejecutándose. Los criterios de interpretación de este documento
se mantienen: no se asume flujo libre con veinte ni congestión con cien.

**Resultados revisados el 2026-09-19:** la campaña larga 20/100 fue ejecutada
por el estudiante el día 18. Las [gráficas](graficas_demandas_20_100.md)
muestran un contraste claro, pero cien acumula bloqueos, rechazos de rutas y
contactos, y su velocidad casi se anula al final. La integridad de archivos
está comprobada; falta explicar las secuencias de bloqueo antes de identificar
una congestión representativa o congelar cien como demanda mayor definitiva.

La justificación combina antecedente bibliográfico, geometría del mapa,
viabilidad computacional y respuesta observada. Ninguna fuente consultada
establece un número universal de vehículos que sature Town01 con cualquier
controlador. Tampoco los FPS ni el número de puntos de aparición equivalen
a capacidad vial.

## 1. Un antecedente con cantidades concretas

Codevilla, Santana, López y Gaidon (2019), *Exploring the Limitations of
Behavior Cloning for Autonomous Driving*, presentan NoCrash con condiciones
vacía, regular y densa. El artículo describe estos niveles; las cantidades
por mapa se verificaron directamente en su implementación conservada por
CARLA. [Artículo](https://arxiv.org/abs/1904.08980).

| Mapa del benchmark | Tráfico regular | Tráfico denso | Peatones regular / denso |
|---|---:|---:|---:|
| Town01 | 20 | 100 | 50 / 250 |
| Town02 | 15 | 70 | 50 / 150 |

Fuente numérica: [código de CARLA, líneas 88–110](https://github.com/carla-simulator/driving-benchmarks/blob/1614d19581d43eac9966e4001611cc8341bf5319/version084/driving_benchmarks/carla100/carla100.py#L88),
commit `1614d19581d43eac9966e4001611cc8341bf5319`. El repositorio presenta
este benchmark dentro de la versión **0.8.4**. El campo `NumberOfVehicles`
configura tráfico de fondo para evaluar un vehículo protagonista; no es
exactamente la población total de nuestro generador.

En TrafficIA se usa CARLA 0.9.15, veinte agentes de viajes equivalentes,
cero peatones, destinos y esperas propios, flota mixta y otro controlador.
Por tanto, 20/100 es un **antecedente para candidatos**, no reproducción
de NoCrash ni prueba de que veinte sea flujo libre o cien saturación.
Se conservará explícitamente la definición local de N como vehículos totales.

El 70 de ese benchmark pertenece a Town02. Esto no demuestra el origen de
nuestros antiguos 20/70 de Town03; sí impide presentarlos como la pareja
publicada de NoCrash para Town01. Cinco/veinte sigue siendo una alternativa
de contraste de carga apoyada en pilotos, pero carece de ese antecedente
numérico específico y hasta ahora presenta poco contraste de velocidad.

## 2. Qué aportan las guías de microsimulación

[FHWA, Traffic Analysis Toolbox III, actualización 2019, capítulo 6](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter6.htm)
respalda variar niveles de demanda en un análisis de sensibilidad. Propone
cuatro semillas iniciales para estimar variabilidad y calcular cuántas réplicas
se necesitan según la precisión elegida. No prescribe cantidades para Town01
ni garantiza suficiencia estadística con cuatro ejecuciones.

[FHWA 2019, capítulo 5](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm)
combina perfiles de velocidad/tiempo con dinámica del cuello de botella.
Incluye como regla orientativa una velocidad menor que un tercio de la
velocidad libre observada para identificar congestión, acompañada de revisión
de la evolución de velocidad y flujo. No debe aplicarse automáticamente a
una espera por rojo, a `dwell` o al promedio de toda la ciudad.

**Adaptación propuesta para TrafficIA:** medir velocidad libre en tramos y
períodos sin interferencia, después contrastar velocidad, densidad, descarga
y persistencia de colas en esos mismos lugares. Si la velocidad libre medida
fuera 20 km/h, un tercio sería 6.67 km/h; el límite configurado de 20 km/h no
es por sí mismo esa medición. En accesos semaforizados comprobar cola residual
después del verde y repetición de la situación, además de la velocidad.

El procedimiento de capacidad de la
[guía FHWA 2004, sección 5.3.2](https://ops.fhwa.dot.gov/trafficanalysistools/tat_vol3/sect5.htm)
considera el caudal descargado cuando existe cola y distingue intersecciones
semaforizadas. Es una referencia metodológica anterior a la actualización
2019, no una orden de cambiar nuestro controlador para generar congestión.
Una capacidad estimada aquí sería propia del ODD simulado, sin calibración
frente a tráfico de campo.

## 3. Computadora: límite de ejecución y presupuesto

La [documentación CARLA 0.9.15 de rendimiento](https://carla.readthedocs.io/en/0.9.15/adv_benchmarking/)
evalúa FPS al variar vehículos, física y Traffic Manager, e identifica la
máquina y versión usadas. Sus cifras no predicen directamente este equipo
ni el costo de veinte/cien `BasicAgent` y nuestros diagnósticos. La medición
relevante debe hacerse con el runner, sensores y registros que usará la tesis.

La campaña local de veinte sostuvo **1.730–1.832×** con 5× solicitado y
datos íntegros. Es un límite inferior de viabilidad conocido; no prueba
que veinte sea el máximo. No extrapolar linealmente ese rendimiento a cien.

En modo síncrono con delta físico fijo, una ejecución más lenta puede seguir
avanzando pasos de 0.05 s simulados. La duración real afecta el costo del
experimento, no convierte una velocidad física en otra. La documentación
separa explícitamente ambos relojes:
[sincronía y paso temporal](https://carla.readthedocs.io/en/0.9.15/adv_synchrony_timestep/).

Propuesta operativa, **no umbral publicado de tráfico**: usar al menos 1×
como preferencia inicial de presupuesto (30 minutos reales por 30 minutos
simulados). Si se acepta más tiempo, un nivel menor que 1× puede ser válido
si no pierde registros ni produce fallos técnicos. El máximo ensayado que
cumpla el presupuesto se llamará «mayor carga viable ensayada», nunca
«capacidad del mapa» ni límite absoluto de la computadora.

## 4. Geometría y evidencia disponibles

El OpenDRIVE local contiene **4.9596 km-carril de conducción fuera de cruces**,
según la medición previa conservada en `manual_review_20260915/map_context.json`.
Dividir toda la población por esa longitud produce solo un índice nominal;
el numerador también incluye vehículos temporalmente dentro de cruces.

| N simultáneo | Índice nominal N / 4.9596 km-carril |
|---:|---:|
| 20 | 4.03 |
| 30 | 6.05 |
| 40 | 8.07 |
| 60 | 12.10 |
| 80 | 16.13 |
| 100 | 20.16 |

No son densidades críticas ni medidas locales de las gráficas. La densidad
por tramo requiere contar tiempo y distancia dentro del mismo ámbito.

En los pilotos de semilla 42 y 600 s, la velocidad de presencia fue:

| N | Aleatorio (km/h) | Historial (km/h) |
|---:|---:|---:|
| 5 | 11.619 | 11.483 |
| 10 | 10.633 | 11.125 |
| 20 | 10.595 | 10.874 |

Entre diez y veinte el cambio fue pequeño: no basta para afirmar que ya
tenemos un régimen congestionado. Las cuatro corridas largas de veinte
aportan nubes locales y algunos contactos, pero todas mantienen el mismo N.

Comprobaciones nuevas, sin crear actores ni avanzar frames:

- CARLA cliente/servidor 0.9.15, `Carla/Maps/Town01`, cero vehículos, sensores
  y peatones; modo asíncrono, renderizado activo.
- 255 puntos de aparición distintos proyectados en carriles driving fuera
  de intersecciones. Extendiendo el prefijo de veinte con la misma regla de
  máxima distancia mínima hay candidatos hasta cien; separación mínima de
  centros de 41.02 m con cuarenta y 16.16 m con cien. No demuestra ausencia
  de conflictos de huella ni creación/circulación efectiva.
- Se consultaron 24 procesadores lógicos y 31.77 GiB de RAM física; 10.26 GiB
  disponibles en ese instante. La consulta WMI de CPU/GPU fue denegada; no
  se atribuye una GPU actualmente activa a partir de esta prueba. Los datos
  de memoria no predicen N máximo.

Evidencia: `data/output/demand_basis_20260917/`, con preflight, contexto de
hardware, spawns candidatos y copia/hash del código bibliográfico consultado.

## 5. Selección propuesta antes de ver nuevos resultados

1. **Candidato menor: N=20.** Tiene antecedente bibliográfico y corridas
   locales largas íntegras. La etiqueta provisional es «carga menor de la
   comparación», no «flujo libre garantizado».
2. **Referencia mayor: N=100.** Su antecedente es el nivel denso de NoCrash
   Town01. La propuesta de exploración es **30 → 40 → 60 → 80 → 100**,
   conservando veinte como referencia. Los escalones son una decisión
   práctica del proyecto para evitar un salto de carga, no cifras de FHWA.
3. **Prueba inicial por escalón:** ambos selectores, semilla 42, 600 s,
   5× solicitado, delta 0.05 s, sin cámaras y con el mismo controlador,
   clima, diagnósticos e historiales de treinta visitas por agente.
   Preparar N spawns e historiales completos; conservar prefijos.
4. **Separar decisiones:** fallos de creación, pérdida de logs o crash
   invalidan técnicamente esa ejecución y deben investigarse. Eventos,
   colas y `blocked` son resultados para revisar. No descartar un N por
   tener incidentes. El umbral `blocked` de 60 s puede reasignar viajes en
   colas; documentar su efecto antes de atribuir una curva al tráfico.
5. **Congelar la pareja tras los pilotos.** Si cien resulta ejecutable e
   interpretable dentro del presupuesto, 20/100 conserva el antecedente
   completo como adaptación. Si no, elegir 20 y el mayor N ensayado que
   cumpla los requisitos técnicos y el presupuesto previamente definido,
   citando el barrido y el motivo de reducción. No afirmar saturación si
   no se observó. Si solo veinte es viable, falta un candidato superior:
   se deberá reconsiderar el menor o los recursos, no inventar el segundo.
6. **Confirmación de la pareja:** ambos selectores, 1,800 s, inicialmente
   cuatro semillas predefinidas para estimar variabilidad (por ejemplo,
   42, 7, 210, 109). Son 16 corridas y ocho horas simuladas. Calcular la
   necesidad de más réplicas a partir de su variación y precisión objetivo;
   repetir además condiciones idénticas para evaluar repetibilidad física.
   Los pilotos utilizados para elegir N se identifican como exploratorios.

La regla privilegia un antecedente y una restricción medible. No escoge
la cantidad con más accidentes ni la que haga ganar al histórico. La
comparación final conserva dos niveles; el barrido puede tener más niveles
sin añadir objetivos específicos.

## 6. Qué falta para completar los diagramas de tráfico

Se mantendrán los mismos 38 tramos y ventanas de 60 s para comparar las
nubes locales entre cargas, incluidos los ceros y las esperas. Revisar por
tramo/sentido y contexto semafórico antes de juntar toda la red. Mayor N
puede ampliar la cobertura de densidad; no garantiza una parábola completa.

Geroliminis y Daganzo (2008) muestran en Yokohama una relación agregada entre
flujo, densidad y velocidad; la dispersión de detectores individuales y la
representatividad espacial importan para interpretar esa agregación.
[Artículo y resumen institucional](https://its.berkeley.edu/node/4651),
DOI `10.1016/j.trb.2008.02.002`. Es una base para estudiar una relación
macroscópica, no evidencia de que ya exista una curva equivalente en Town01.

La lámina actual mezcla celdas de diferentes calles: es una nube local, no
un diagrama macroscópico de toda la ciudad. Una variante de red necesitaría
definir un ámbito coherente y agregación espacial compatible. Si no aparecen
estados cercanos a capacidad o sobrecargados, se informará el rango observado;
no se forzará el controlador para completar la figura conceptual.

## Redacción académica utilizable ahora

> Se proponen niveles de población vehicular simultánea tomando como
> antecedente las cargas regular y densa de NoCrash en Town01. Las magnitudes
> se adaptarán al ODD y a la viabilidad computacional del generador mediante
> pilotos incrementales, con condiciones de ejecución comunes y medidas de
> velocidad, densidad, flujo e integridad. La selección definitiva se fijará
> antes de la evaluación comparativa. Los niveles no se interpretarán como
> demanda urbana calibrada ni como flujo libre y saturación sin evidencia
> operacional adicional.

Tras los pilotos se sustituirá la propuesta por los valores finalmente
seleccionados y su evidencia. **No se ejecutaron nuevas corridas en esta
investigación ni se cambió configuración de conducción o del mundo.**
