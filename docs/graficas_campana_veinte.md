# Gráficas de objetivos y tráfico — 2026-09-17

Las cuatro corridas largas ya permiten visualizar las métricas del objetivo
específico 3 y explorar las relaciones de flujo de tráfico. Son resultados
descriptivos de **veinte vehículos, 1,800 s por corrida, semillas 210/109 y
ambos selectores**. No constituyen aún el contraste de dos demandas ni una
calibración de capacidad vial.

- [PDF con las nueve láminas](../data/output/visual_analysis20_20260917/graficas_campana.pdf).
- [Galería local con filtros y descargas](../data/output/visual_analysis20_20260917/index.html): abrir `index.html` en un navegador; funciona sin servidor.
- [Método completo, figuras y reproducción](../data/output/visual_analysis20_20260917/informe_graficas.md).
- [Resumen numérico](../data/output/visual_analysis20_20260917/summary.csv),
  [frecuencias de destinos](../data/output/visual_analysis20_20260917/destinations.csv),
  [celdas de flujo](../data/output/visual_analysis20_20260917/flow_cells.csv) y
  [series temporales](../data/output/visual_analysis20_20260917/time_series.csv).

Los artefactos quedan en `data/output/visual_analysis20_20260917/`, excluido
de Git como los demás resultados. Los PNG sirven para consulta y los SVG
permiten incorporar las figuras vectoriales al documento académico.

## Qué responde cada figura

| Lámina | Contenido | Relación con los objetivos |
|---|---|---|
| 01 | Destinos, tiempo, velocidad y tasa de colisiones | Vista conjunta de las cuatro métricas del objetivo 3; invasiones cero señaladas |
| 02 | Cajas, distribución acumulada y viajes al corte | Tiempo de viaje completo y censura por duración de simulación |
| 03 | Categorías asignadas y alcanzadas | Tres categorías del objetivo 1 y distribución del objetivo 3 |
| 04 | Frecuencias de los 42 destinos | Concentración de visitas por selector, sin ocultar destinos con cero visitas |
| 05 | Velocidad y fracción de tiempo a baja velocidad por minuto | Velocidad y contexto de las detenciones |
| 06 | Callbacks, tasas, episodios y sus tiempos | Incidentes e interpretación de registros persistentes |
| 07 | Historial acumulado y proporciones de ramas | Funcionamiento de los agentes y del selector 80/20 |
| 08 | Velocidad–densidad, flujo–densidad y velocidad–flujo | Exploración de los diagramas solicitados |
| 09 | Mapa de tramos y cobertura de densidades | Ámbito de medición y suficiencia de los datos |

Todas las barras comparativas representan una corrida. Las cajas describen
viajes de una misma ejecución; no son intervalos de confianza entre réplicas.

## Lo que ya se observa

| Semilla | Selector | Llegadas | Tiempo medio completo (s) | Velocidad de presencia (km/h) | Callbacks de colisión | Episodios descriptivos |
|---|---|---:|---:|---:|---:|---:|
| 210 | Aleatorio | 215 | 155.49 | 10.38 | 14 | 1 |
| 210 | Historial 80/20 | 196 | 168.56 | 10.71 | 0 | 0 |
| 109 | Aleatorio | 181 | 182.19 | 10.36 | 510 | 1 |
| 109 | Historial 80/20 | 191 | 174.06 | 10.28 | 0 | 0 |

El histórico tarda más en promedio con 210 y menos con 109. Estas medias
corresponden a recorridos distintos y todavía no establecen una mejora
consistente del selector. La velocidad usa distancia dividida entre tiempo
total de presencia, incluidas detenciones y espera en destino. Los 78 viajes
activos al corte no se introducen como tiempos de viaje completo.

Trabajo/educación concentra 28.4–28.8 % de las asignaciones históricas frente
a 11.5–12.8 % de las aleatorias. El catálogo contiene 18 destinos residenciales,
18 de servicios/ocio y 6 de trabajo/educación: uniformidad entre destinos
elegibles no significa un tercio de elecciones por categoría. El 80/20 es
la probabilidad de ramas del selector, no un reparto por categoría.

Las cuatro corridas registraron **cero invasiones**. Los 524 callbacks de
colisión de baseline se agrupan descriptivamente en dos episodios: misma
pareja de actores, sin distinguir el sensor emisor, y separación entre
callbacks consecutivos de hasta 1 s. No se presentan como 524 accidentes.
La tasa principal conserva los callbacks por vehículo-km; antes de usar la
tasa por episodio como métrica definitiva se debe formalizar esa definición.

Los historiales crecen de 600 visitas iniciales a 796/791. Las ramas de rutina
se eligieron en 78.14 % y 81.52 % de las decisiones, compatibles con que 80 %
sea una probabilidad, sin exigir una cuota exacta en cada corrida.

## Cómo leer las gráficas parecidas a la imagen de referencia

La lámina 08 contiene las tres relaciones solicitadas, separadas por semilla
y coloreadas por selector. Cada punto representa un **carril de 50 m observado
durante 60 s**, salvo la última ventana, de aproximadamente 59.95 s. Se usan
38 tramos rectos fuera de cruces: 1.9 km-carril. La selección es geométrica;
no depende de que un tramo produzca el resultado esperado.

Si S es tiempo vehicular acumulado en segundos, D distancia longitudinal en
metros, L longitud del tramo y T duración de ventana, se calcula:

- Densidad `k = 1000 S / (L T)`, en vehículos/km/carril.
- Flujo `q = 3600 D / (L T)`, en vehículos/h/carril.
- Velocidad `v = 3.6 D / S`, en km/h, si hay presencia.

Son medidas espacio-temporales compatibles: `q = k v`. Esa identidad no
demuestra que se haya identificado una curva, capacidad o densidad crítica.
La diferencia entre medición y ajuste de un modelo está explicada en
[FHWA: variables y estados de tráfico](https://ops.fhwa.dot.gov/publications/weatherempirical/sect3.htm)
y en el marco teórico local; también se conserva la referencia a
[Traffic Stream Characteristics](https://www.fhwa.dot.gov/publications/research/operations/tft/chap2.pdf).

De las 4,560 celdas posibles, 2,458 tienen presencia. La densidad local máxima
observada es 62.92 vehículos/km/carril y el flujo máximo muestral es 390.97
vehículos/h/carril; **ese máximo no es capacidad vial**. En celdas con densidad
de 0–5, la mediana de velocidad es 19.29 km/h (991 celdas); entre 10–20 baja
a 6.45 km/h (523 celdas). Solo 49 celdas superan 30 vehículos/km/carril.
Esto muestra una tendencia local compatible con menor velocidad a mayor
presencia vehicular, con cobertura escasa en densidades altas.

Todavía no se distingue una rama congestionada suficiente para estimar el
diagrama completo. Las celdas mezclan ubicaciones, fases semafóricas y esperas;
no son observaciones independientes ni estados estacionarios seleccionados.
No se ajustó Greenshields ni una parábola para imitar la imagen. Las bandas
de flujo responden también a la ventana finita: atravesar 50 m completos
aporta 60 vehículos/h a una celda de 50 m por 60 s. El flujo no es el número
de viajes completados por hora.

Tener veinte carros simultáneos en Town01 no significa densidad de veinte
vehículos/km en cada calle. Los registros sí permiten medir variación local,
pero las cuatro ejecuciones no varían el tamaño global de la flota.

## Validación y límites de la derivación

Se procesaron las 2,880,000 observaciones con la API de mapa offline. No se
creó un cliente CARLA ni se avanzaron frames. Se incluyen todas las fases,
paradas y esperas. Las celdas vacías conservan flujo/densidad cero y velocidad
indefinida; no se dibujan como si un vehículo parado estuviera presente.

No hubo huecos de frames ni posiciones sin proyección en carril driving.
No se inventa el primer intervalo de 0.05 s por vehículo: falta un
vehículo-segundo de exposición por corrida en la derivación temporal.
Las transiciones de carretera/carril no se interpolan longitudinalmente;
su cota temporal es 40.35–43.40 vehículo-segundos por corrida y queda en el
manifiesto. Los pequeños desplazamientos en reversa se cuantifican y su
distancia absoluta se conserva. La identidad `q=k*v` tiene error máximo
menor que `1e-12` en las celdas. Las métricas del resumen principal mantienen
la exposición completa del cálculo oficial auditado.

Pasaron **118 pruebas** con `carla-env`, incluidas siete nuevas de unidades,
conservación al cruzar fronteras de tramo/tiempo, detenciones, reversa,
ventana parcial y entradas inválidas. Se inspeccionaron las nueve imágenes.
Los manifiestos conservan hashes de fuentes, entradas y datos de las figuras.
No se modificó conducción, historiales de entrada, TeX ni logs originales.

Para regenerar las figuras desde los CSV derivados:

```powershell
.\carla-env\Scripts\python.exe scripts/plot_mobility_campaign.py --data data/output/visual_analysis20_20260917
```

La derivación completa, en una carpeta nueva, está documentada en el informe
del paquete. Requiere el OpenDRIVE local de Town01 y `carla-env`, sin servidor.

## Lo siguiente para justificar las dos demandas

Definir la unidad de incidente, repetir condiciones idénticas y contrastar
cantidades simultáneas candidatas con las mismas semillas, duración y tramos
de medición. Los pilotos 5/10/20 sirven como antecedente técnico, pero no
conviene mezclar directamente sus 600 s con estas corridas de 1,800 s para
atribuir diferencias solo a demanda. La flota cambia entre semillas, aunque
cada pareja de selectores comparte sus modelos y condiciones.

Las cantidades finales deben mostrar un contraste interpretable de operación
dentro del ODD. No es necesario encontrar saturación ni reproducir exactamente
la imagen teórica para cumplir el objetivo; si se pretende estimar capacidad,
harán falta datos de más estados y un diseño específico para esa estimación.
