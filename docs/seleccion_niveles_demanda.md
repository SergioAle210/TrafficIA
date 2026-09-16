# Revisión de la corrida manual y selección de niveles de demanda

Fecha del análisis: 2026-09-15. Corrida del estudiante: 2026-09-14.
Estado: análisis offline y propuesta experimental; no se ejecutaron pilotos
con más vehículos ni se fijaron cantidades finales. No se inició CARLA.

## Resultado de la corrida manual

Fuente: `data/output/town01_random_baseline_seed_42_20260914T215949497576Z/`.
Town01, CARLA 0.9.15, tres vehículos, semilla 42, 600 s simulados, ritmo
solicitado 1×, renderizado activo, diagnósticos de navegación y delta 0.05 s.
El estudiante confirmó que comprobó la finalización; queda pendiente observar
en detalle el comportamiento y ejecutar manualmente `history_80_20`.

| Comprobación | Resultado |
|---|---:|
| Viajes iniciados / completados | 14 / 11 |
| Viajes activos al corte (`aborted`, motivo `simulation_end`) | 3 |
| `route_failed` / `blocked` / `timeout` | 0 / 0 / 0 |
| Callbacks de colisión / invasión | 0 / 0 |
| Errores del analizador de integridad | 0 |
| Tiempo medio de viajes completados, incluidas esperas | 137.209 s |
| Mediana / desviación muestral entre viajes completados | 161.700 / 84.624 s |
| Velocidad de toda la presencia vehicular, incluidas esperas | 11.565 km/h |
| Distancia / exposición total | 5.782 km / 0.500 vehículo-hora |
| Destinos alcanzados: residencia / trabajo-educación / servicios-ocio | 3 / 4 / 4 |

Los tres `aborted` terminan exactamente al final de los 600 s: vehículo 001,
viaje 006, 21.40 s transcurridos; vehículo 002, viaje 005, 41.05 s; vehículo
003, viaje 003, 173.25 s. No son llegadas fallidas ni bloqueos diagnosticados;
son observaciones incompletas por el horizonte de la corrida.

Los vehículos 001, 002 y 003 completaron cinco, cuatro y dos viajes,
respectivamente. El 003 es un Audi TT en esta semilla, no el Cybertruck de
semilla 123. Llegó a T01_030 y T01_050; su último viaje hacia T01_006 quedó
activo al corte. Su mayor intervalo continuo observado por debajo de 0.2 m/s
fue 31.90 s. En toda la flota, 33.18 % del tiempo de viajes activos estuvo
por debajo de ese umbral: esta medida no identifica la causa de la parada.
No se puede atribuir ese porcentaje a congestión solo con estos logs.

Las once llegadas cumplen los umbrales registrados: velocidad máxima de
llegada 0.000925 m/s, error angular absoluto máximo 0.613°, error lateral
máximo 0.0054 m y distancia máxima al destino 0.500 m. Sus IDs de carril
coinciden con la proyección de sus posiciones sobre el OpenDRIVE local.
Esta auditoría offline no reproduce sensores ni sustituye una inspección
visual de la huella durante todo el recorrido.

El resumen antiguo de velocidad de viajes activos da 11.929 km/h. No es un
error: excluye las pausas entre viajes. La métrica de presencia completa de
la versión 3 es 11.565 km/h y es la usada en este informe.

El catálogo tiene 42 destinos (18 residenciales, 18 servicios/ocio y seis
trabajo/educación). Baseline elige entre IDs elegibles; no obliga a obtener
un tercio de viajes por categoría. Once llegadas no bastan para caracterizar
la distribución ni para concluir que la probabilidad de incidentes sea cero.

## Comparación con la ejecución previa

Referencia: `town01_random_baseline_seed_42_20260909T182939437792Z/`.
Coinciden las 14 combinaciones vehículo/viaje/destino/estado, las condiciones
ambientales registradas y la flota. El tiempo medio pasa de 137.241 a
137.209 s (diferencia −0.0318 s), la velocidad de 11.566 a 11.565 km/h y
la distancia total difiere en −0.582 m. La mayor diferencia de duración
entre viajes completados correspondientes es 0.500 s.

Es evidencia de repetibilidad funcional cercana, no identidad física por
frame: la corrida anterior usó ritmo 5× y no-rendering. Además, la corrida
manual no guardó hashes del código utilizado, por lo que no puede verificarse
retroactivamente su identidad exacta. Los hashes calculados ahora preservan
los archivos de resultados revisados, no acreditan el código usado el día 14.

El clima registrado incluye precipitación 40, mojado 80 y altura solar 20°,
igual que la corrida previa. No describir estas pruebas como clima seco.
Antes de la campaña final, fijar explícitamente el clima del ODD; cambiarlo
requiere repetir los tratamientos afectados bajo la nueva condición.

Evidencia derivada, sin modificar los originales, en
`data/output/manual_review_20260915/`: `analysis.json`, `audit.json`,
`comparison.json`, `map_context.json`, `review_offline.py` y
`trajectories_and_speed.png`. El script importa `carla.Map` para leer el
archivo local; no crea `carla.Client`, mundo, actores ni conexiones.

## Qué significa demanda en este experimento

Por decisión del estudiante, la variable controlada será **N vehículos
simultáneos** en una red fija, realizando viajes sucesivos. Es una definición
operativa de carga del generador. No equivale directamente a un caudal de
entrada en vehículos/hora: la red mantiene su población, y la frecuencia de
nuevos viajes depende de lo que duren los viajes y sus esperas.

Los objetivos requieren dos valores de N y comparar ambos selectores en
cada uno. No obligan a representar una hora pico real ni a producir congestión,
ni fijan 20 y 70. Sin datos de campo, la justificación será experimental y
relativa a este ODD, no una calibración de demanda urbana real.

Los archivos `config/scenario_low_demand.json` y
`config/scenario_high_demand.json` contienen 20 y 70, pero corresponden a
Town03, usan 90 y 120 s y distinto renderizado. Son configuraciones de otra
etapa y no tienen el esquema requerido por `run_trip_simulation.py`.
No se deben reutilizar directamente para comparar los selectores en Town01.

## Respaldo geométrico y sus límites

Se leyó el `Town01.xodr` instalado con CARLA 0.9.15 y se sumaron los centros
de carriles `driving` fuera de intersecciones, muestreados a pasos de hasta
1 m: **4.9596 km de carril**, en 52 secciones de carril. La suma independiente
de intervalos OpenDRIVE s da 4.9596 km. Se excluyen conectores de giro de
intersecciones porque varias trayectorias comparten espacio físico.

| Vehículos N | Índice nominal N / 4.9596 km de carril |
|---:|---:|
| 3 | 0.60 |
| 5 | 1.01 |
| 10 | 2.02 |
| 20 | 4.03 |
| 30 | 6.05 |
| 40 | 8.07 |
| 70 | 14.11 |

Es un **índice nominal de carga de red**, no densidad medida: el numerador
incluye vehículos que pueden estar en intersecciones o esperando en destinos,
mientras el denominador excluye conectores. No determina capacidad, nivel de
servicio ni longitud de cola. Para medir densidad real por tramo deben
coincidir el área del conteo, los carriles y el intervalo temporal. Tampoco
el número de spawn points equivale a capacidad vial.

El mismo N puede producir concentraciones diferentes según los destinos,
señales, tamaño de los vehículos y geometría. Por eso una cifra tomada de
otro mapa no basta para elegir los niveles.

## Propuesta de cantidades y regla de decisión

**Candidatos iniciales: cinco vehículos para carga menor y veinte para carga
mayor; diez como escalón intermedio. No son niveles finales validados.**

- Cinco permite ampliar gradualmente la base ya probada con tres; hay
  historiales sintéticos para los primeros cinco vehículos. Todavía hay que
  elegir y validar dos puntos de inicio adicionales y probar la flota completa.
- Veinte multiplica por cuatro la población y el índice nominal de cinco
  sobre la misma red. Ese contraste es una decisión de diseño explícita para
  explorar sensibilidad; no es un umbral de congestión publicado.
- Diez permite detectar problemas de configuración, interacción o rendimiento
  antes de probar veinte. Los pilotos no son niveles extra de la comparación
  final: esta mantendrá exactamente dos cantidades.

Antes de ver los resultados finales se documentará esta regla:

1. Conservar cinco como candidato menor si puede ejecutarse y medirse con
   entradas completas y ambas políticas. La escasez de viajes o categorías
   se aborda con duración y repeticiones, no descartando realizaciones.
2. Probar veinte como candidato mayor bajo las mismas condiciones. Separar
   integridad del software, rendimiento del equipo y comportamiento del tráfico.
   Los eventos y las colas son resultados; no motivos automáticos de exclusión.
3. Si el propósito adicional es contrastar circulación poco interferida y más
   interferida, comprobar colas persistentes, proximidad entre vehículos y
   esperas atribuibles al tráfico en varios pilotos. Si veinte no diferencia
   esos regímenes, explorar treinta y después cuarenta; ampliar a cincuenta
   o setenta solo si la evidencia y el equipo lo permiten. No hay obligación
   de llegar a setenta.
4. Dos cargas distintas siguen siendo válidas para estudiar sensibilidad si
   producen métricas parecidas. No elegir cantidades para forzar diferencias
   significativas, mejorar el histórico frente al baseline o eliminar eventos.
5. Congelar las dos cantidades antes de la evaluación final, dejando los
   pilotos separados. Si se exige llamar a un nivel «congestionado», justificar
   esa etiqueta mediante mediciones locales; «mayor N» por sí solo no la prueba.

No es posible elegir honestamente una pareja definitiva a partir de una sola
carga de tres vehículos. La evidencia actual permite formular candidatos y
el procedimiento para confirmarlos, no inventar una capacidad de Town01.

## Preparación necesaria y campaña propuesta

No basta cambiar `vehicle_count`: el runner exige exactamente N puntos de
inicio distintos; el histórico exige entradas para cada vehículo. El archivo
actual tiene 30 visitas para cada uno de `vehicle_001` a `vehicle_005`, y
ninguna para el 006 en adelante. Crear configuraciones e historiales nuevos
de campaña, conservando los existentes y las primeras identidades. Mantener
los spawns y perfiles existentes al ampliar la flota cuando sea posible.
Usar ambas políticas con idéntica flota y condiciones dentro de cada semilla.

Antes de interpretar colas, registrar al menos el estado semafórico y la
presencia de un vehículo precedente, junto con posición, velocidad y duración
de la parada. Hoy `blocked` se dispara tras 60 s a baja velocidad y finaliza
el viaje; luego puede elegir otro destino desde la misma posición. No destruye
el actor ni demuestra un fallo. Bajo mayor carga puede interrumpir viajes por
colas normales y sesgar tiempos/distribuciones. Investigar su efecto en los
pilotos y fijar una política común antes de la campaña final; no aumentar el
umbral solo para ocultar estados `blocked`.

| Etapa | Cantidades | Escenarios / semillas | Duración propuesta | Propósito |
|---|---|---|---|---|
| Revisión visual | 3 | Ambos / 42 | 600 s | Observar curvas, esperas, llegadas y reinicios; el baseline ya terminó, falta su observación detallada y el histórico manual |
| Escalamiento inicial | 5 → 10 → 20 | Ambos / 42 | 600 s cada uno | Seis corridas para descubrir problemas y observar interacciones |
| Pilotos de selección | Dos candidatos; más cantidades solo si hacen falta | Ambos / 42, 7, 123, 2026 | 1.800 s cada uno | Estimar variabilidad, cantidad de viajes, esperas y viabilidad |
| Comparación final | Dos cantidades congeladas | Ambos / semillas y número de repeticiones fijados tras pilotos | Horizonte común | Cuatro métricas, incertidumbre y limitaciones, con pilotos identificados aparte |

Las semillas y duraciones de esta tabla son una propuesta, no una campaña
ya ejecutada. Cuatro semillas en dos escenarios y dos cantidades suponen 16
corridas, ocho horas de tiempo simulado a 1.800 s por corrida; el tiempo real
depende del equipo y del ritmo conseguido. Cuatro réplicas permiten una
estimación inicial de variabilidad, no garantizan precisión suficiente.
Si se requieren intervalos de confianza, fijar la precisión antes de la
comparación y determinar repeticiones a partir de la variación entre corridas.
No tratar los viajes de una misma corrida como réplicas independientes.

Conservar las cuatro métricas académicas y añadir diagnósticos: proporción
de tiempo a baja velocidad, duraciones de paradas, colas/interacciones,
motivos de fin y ritmo real de ejecución. Los dos últimos grupos ayudan a
separar problemas de simulación de movilidad; no sustituyen los objetivos.
La velocidad de las métricas siempre usa tiempo simulado, nunca FPS.

Definir si se estudian los 1.800 s desde el arranque o un intervalo después
de estabilización. No eliminar un calentamiento arbitrario: documentar la
decisión, aplicar el mismo intervalo a ambos tratamientos y alinear eventos,
distancias y tiempos. Los logs actuales describen toda la corrida.

Guardar versión/hash de código y entradas, clima explícito, flota, spawns,
semillas, delta fijo, renderizado, política de finalización y tiempos reales.
La semilla actual cambia destinos y modelos de vehículo: comparar tratamientos
emparejados y declarar esa variación conjunta entre semillas. Si se busca
aislarla, preparar semillas separadas o una flota fija antes de congelar.

## Fuentes y correspondencia con los objetivos

- El protocolo y el marco del proyecto son la fuente de objetivos y de la
  distinción entre flujo, densidad y velocidad; no se modificaron.
- La guía [FHWA 2019, capítulo 4](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter4.htm)
  respalda revisar la animación y comprobar errores con carga reducida antes
  de interpretar el comportamiento a mayor carga.
- [FHWA 2019, capítulo 6](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter6.htm)
  recomienda variar demanda para analizar sensibilidad y comenzar con cuatro
  semillas distintas para estimar variabilidad y calcular las réplicas necesarias.
  No prescribe cinco, veinte ni setenta vehículos para Town01. Las cantidades,
  semillas concretas y duraciones anteriores son propuestas de este proyecto.
- [CARLA 0.9.15, mapas](https://carla.readthedocs.io/en/0.9.15/core_map/)
  describe mapas y puntos recomendados de spawn; no fija capacidad de tráfico.
  La [API de Map](https://carla.readthedocs.io/en/0.9.15/python_api/#carlamap)
  permite consultar un OpenDRIVE local sin servidor.

Esto aporta al objetivo 1 una definición operativa de demanda y condiciones
del ODD; al objetivo 2, una validación gradual de agentes simultáneos; y al
objetivo 3, una comparación 2 cantidades × 2 selectores con repeticiones.
La meta general sigue siendo producir datos reproducibles para análisis
preliminar. No exige máximos de vehículos, congestión extrema ni conducción
perfecta.
