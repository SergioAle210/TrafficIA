# Gráficas de 20 y 100 vehículos - análisis del 2026-09-19

**Nueva campaña:** [gráficas de 3600 segundos del 22 de septiembre](graficas_demandas_3600.md), con resultados propios y comparación entre medias horas.

**Actualización del 20 de septiembre:** hay una
[versión con líneas guía y explicación de las imágenes teóricas](lectura_diagramas_y_guias.md).
Conserva los mismos puntos y resultados, y añade promedios por bandas de
densidad a la lámina 09. Esta versión del día 19 permanece intacta.

Se revisó la campaña que el estudiante ejecutó el **18 de septiembre de
2026**: dos cantidades, cada una con `random_baseline` y `history_80_20`,
semilla 210 y 1,800 s simulados. Son cuatro ejecuciones, una por combinación.
Los resultados anteriores permanecen intactos. No se ejecutó CARLA.

- [Galería con once láminas](../data/output/visual_analysis20_100_20260919/index.html).
- [PDF completo](../data/output/visual_analysis20_100_20260919/graficas_campana.pdf).
- [Método, tablas y reproducción](../data/output/visual_analysis20_100_20260919/informe_graficas.md).
- [Resumen numérico](../data/output/visual_analysis20_100_20260919/summary.csv).
- [Paquete de figuras y datos derivados](../data/output/graficas_20_100_20260919.zip).

PNG para consulta, SVG vectorial para el documento académico y CSV derivados
quedan en `data/output/visual_analysis20_100_20260919/`. La campaña original
está en `data/output/demand20_100_seed_210_20260918T190119084914Z/`.

## Qué muestra cada lámina

| Lámina | Contenido |
|---|---|
| 01 | Las cuatro métricas: destinos, tiempo completo, velocidad y tasa de colisión |
| 02 | Tiempos de llegadas, distribución acumulada y llegadas por vehículo |
| 03 | Completados, blocked, rutas rechazadas y viajes cortados al terminar |
| 04 | Categorías de destinos asignados y alcanzados |
| 05 | Frecuencias de los 42 destinos con escala común |
| 06 | Velocidad y fracción de tiempo a baja velocidad por minuto |
| 07 | Colisiones, invasiones, tasas por vehículo-km y episodios descriptivos |
| 08 | Historial total, historial medio por vehículo y ramas 80/20 |
| 09 | Velocidad-densidad, flujo-densidad y velocidad-flujo |
| 10 | Mapa de medición y cobertura de densidades de ambas demandas |
| 11 | Llegadas acumuladas, blocked y route_failed por minuto |

## Resultados principales

| Vehículos | Selector | Llegadas | Media completa (s) | Velocidad de presencia (km/h) | Blocked | Route failed | Corte final | Colisiones (callbacks) | Invasiones |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | Aleatorio | 215 | 155.49 | 10.38 | 0 | 0 | 20 | 18 | 0 |
| 20 | Histórico | 196 | 168.59 | 10.71 | 0 | 0 | 19 | 0 | 0 |
| 100 | Aleatorio | 173 | 173.97 | 2.47 | 1,673 | 340 | 87 | 48,814 | 7 |
| 100 | Histórico | 183 | 204.47 | 2.55 | 1,787 | 77 | 90 | 19,768 | 3 |

Los 4,860 intentos suman 767 completados, 3,460 `blocked`, 417
`route_failed` y 216 `aborted` con motivo `simulation_end`. Estos últimos
son cortes al cerrar la corrida; no explican los blocked. El mismo vehículo
puede acumular varios intentos, por lo que 1,673 bloqueos no significa
1,673 carros distintos.

Con cien, las llegadas por vehículo caen de 10.75/9.80 a 1.73/1.83.
En los últimos cinco minutos, la media de las cinco ventanas de velocidad
es 0.529/0.223 km/h y el tiempo bajo 0.2 m/s alcanza 96.28/98.52 %.
Veinte mantiene 10.215/10.221 km/h en ese mismo período. El orden es siempre
aleatorio/histórico. La media de tiempos completos por sí sola oculta
buena parte del deterioro porque excluye los viajes sin llegada.

**Dwell significa sin viaje activo**, incluyendo pausas tras llegadas y
tras fallos. No se interpreta como estancia exclusivamente en destino.
Puede coincidir con baja velocidad; sus porcentajes no se suman.

Las colisiones se agrupan descriptivamente por par de actores sin distinguir
sensor emisor y separación consecutiva máxima de 1 s: 1/0/57/15 grupos.
Se conservan todos los callbacks y sus tasas brutas. Hay 24 grupos con
identificador ajeno no positivo, que pueden agrupar objetos estáticos
distintos: no son un conteo de accidentes verificados. Los contactos incluyen
vehículos y objetos estáticos, no únicamente interacciones normales de cola.

Las consolas conservadas aportan causas de rechazo, sin demostrar aún su
origen físico: en cien/aleatorio, 129 rutas comienzan demasiado lejos del
origen real y 211 rechazos indican distancia excesiva al carril; en
cien/histórico, 73 son por origen desalineado y cuatro por no alcanzar
un tramo anterior al destino en su carril. Se necesita reconstruir las
secuencias previas para explicar por qué se llegó a esas posiciones.

El histórico crece de 600 a 796 visitas con veinte y de 3,000 a 3,183 con
cien. La rama de rutina aparece en 78.14 % y 79.18 % de las decisiones;
80 % es una probabilidad, no una cuota exacta. Los fallos y reasignaciones
aumentan decisiones sin aumentar visitas completadas.

## Relaciones de tráfico y alcance

La figura 09 conserva el método previo: 38 tramos rectos de 50 m fuera de
intersecciones (1.9 km-carril), ventanas de 60 s y última parcial. Con tiempo
vehicular S, distancia longitudinal D, longitud L y ventana T:
`k=1000*S/(L*T)`, `q=3600*D/(L*T)`, `v=3.6*D/S`. Se incluyen todas las fases,
paradas y distancias longitudinales absolutas; no se impone una curva teórica.

De 4,560 celdas, 2,330 tienen presencia: 611/644/551/524 por corrida.
Las densidades locales máximas pasan de 51.14/62.91 a 140/140 vehículos/km/carril;
los máximos muestrales de flujo son 390.83/345.36/466.22/506.48 vehículos/h/carril.
**Ninguno de esos máximos es una capacidad estimada.** La nube ahora cubre
densidades mayores y muchos puntos de baja velocidad, pero mezcla lugares,
semáforos, contactos y bloqueos; no acredita una rama congestionada estable.

Cien/aleatorio tiene 47,648 de 3,600,000 muestras sin proyección driving
(1.324 %). No entran en celdas longitudinales; permanecen en logs y series
globales. Las otras corridas no tienen esas muestras. El ámbito excluye
cruces y segmentos parciales; tampoco representa toda la red. Menos celdas
ocupadas con cien puede coexistir con acumulación localizada y calles sin
circulación. Los períodos/tramos no son réplicas independientes.

## Verificación y siguientes pasos

Se verificaron los hashes de 52 archivos de salida y la instantánea de
fuentes/entradas; se recalcularon las métricas y ambas parejas resultan
comparables. Las auditorías guardadas no tienen errores. La derivación
procesó 8,640,000 filas por bloques, sin huecos entre frames; faltan solo
los primeros 0.05 s por vehículo por no haber observación previa. Se conservan
las cotas de transiciones entre road/lane. El error máximo de `q=k*v` es
1.14e-13. Pasaron 126 pruebas con `carla-env`, incluidas tres nuevas de
agrupación de contactos. Se revisaron visualmente las once páginas del PDF.

El ritmo solicitado fue 5×, pero el tiempo real de proceso dio
1.349/1.533/0.314/0.320×, incluyendo preparación y cierre. Esto mide el costo
computacional de esta instrumentación, no capacidad vial. No se modificó
conducción ni ningún registro fuente para elaborar las gráficas.

El siguiente paso es investigar las primeras secuencias que desencadenan
paradas persistentes, contactos y rutas rechazadas con cien. Después
determinar si ese régimen sirve como demanda mayor o conviene ensayar
cantidades intermedias, y repetir con más semillas. No se exige cero
invasiones: siguen siendo una métrica. Una semilla no permite establecer
significancia ni declarar superioridad del selector.
