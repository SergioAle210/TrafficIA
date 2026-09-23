# Gráficas de 3600 segundos - 22 de septiembre de 2026

Campaña ejecutada por el estudiante entre el 21 y el 22 de septiembre
(hora de Guatemala), Town01, 20/100 vehículos, semilla 210, ambos selectores,
sin cámaras y 5x solicitado. Duración de pared: 7 h 17 min aproximadamente.
Cada combinación arranca de nuevo y dura 3600 s simulados; no prolonga los
archivos de la campaña de 1800 s ni constituye una réplica con otra semilla.

- [Galería de doce láminas](../data/output/visual_analysis20_100_3600_20260922/index.html).
- [PDF](../data/output/visual_analysis20_100_3600_20260922/graficas_campana.pdf).
- [Informe con método, tablas y reproducción](../data/output/visual_analysis20_100_3600_20260922/informe_graficas.md).
- [Primera y segunda mitad](../data/output/visual_analysis20_100_3600_20260922/half_comparison.csv).
- [Paquete de figuras y derivados](../data/output/graficas_20_100_3600_20260922.zip).

## Resultados completos

| Vehículos | Selector | Llegadas | Tiempo medio completado (s) | Velocidad de presencia (km/h) | Blocked | Ruta rechazada | Corte final | Callbacks de colisión | Invasiones |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | Aleatorio | 422 | 161.59 | 10.42 | 0 | 0 | 19 | 0 | 2 |
| 20 | Historial | 397 | 171.86 | 10.64 | 0 | 0 | 20 | 0 | 0 |
| 100 | Aleatorio | 252 | 171.05 | 1.75 | 3932 | 1280 | 92 | 160955 | 30 |
| 100 | Historial | 252 | 183.30 | 1.68 | 4147 | 235 | 96 | 77904 | 17 |

Los 173/65 grupos descriptivos de contacto con cien no son accidentes
verificados. Un contacto persistente puede emitir muchos callbacks y ambos
sensores pueden registrar un mismo contacto. Hay 20617/728 callbacks sin
viaje activo: siguen incluidos en las tasas globales por exposición.
Blocked no significa eliminación del vehículo; puede repetirse después de
reasignaciones. Los viajes interrumpidos al corte se muestran aparte.

Rutina histórica: 327/417 decisiones (78.42 %) con veinte y 3721/4730
(78.67 %) con cien. Historial inicial/final: 600/997 y 3000/3252 visitas.
El historial aumenta solo por llegadas, no por intentos fallidos.

## Qué aporta la segunda media hora

| Vehículos | Selector | Llegadas 0-30 min | Llegadas 30-60 min | Blocked 0-30 min | Blocked 30-60 min |
|---:|---|---:|---:|---:|---:|
| 20 | Aleatorio | 215 | 207 | 0 | 0 |
| 20 | Historial | 195 | 202 | 0 | 0 |
| 100 | Aleatorio | 206 | 46 | 1521 | 2411 |
| 100 | Historial | 185 | 67 | 1781 | 2366 |

Veinte mantiene una producción similar. Cien pierde llegadas y acumula
más bloqueos en la segunda mitad: prolongar no produjo recuperación en
estos indicadores. Esto no establece por sí solo la causa física ni una
capacidad de Town01. La primera mitad de esta nueva campaña no reproduce
exactamente los resultados del 18 de septiembre pese a compartir semilla;
no debe concatenarse con ellos ni asumirse determinismo físico por semilla.

## Cambios de análisis y validación

Se ajustó `scripts/plot_demand_campaign.py` para eliminar referencias fijas
a treinta minutos, a la fecha anterior y a sus porcentajes 80/20. Los
histogramas conservan ventanas de 60 s al ampliar la duración: anteriormente
31 bordes repartidos por toda la corrida habrían producido ventanas de
120 s rotuladas incorrectamente como minutos. La regresión se comprueba
con eventos en límites de ventana y con una última ventana parcial.

La nueva lámina 12 compara las dos mitades. Velocidad y baja velocidad se
ponderan por exposición; las ventanas se asignan por su centro, con un
desfase de 0.05 s respecto al corte nominal. El CSV conserva los límites
observados. Llegadas y blocked se cuentan por tiempo de terminación exacto.
Las dos mitades son dependientes y no ofrecen intervalos entre réplicas.

Las relaciones de tráfico mantienen las guías por bandas y los puntos
originales: no se fuerza una parábola ni se estima capacidad. Las figuras
previas permanecen intactas. Esta entrega es offline: no se ejecutó CARLA,
no se cambió conducción y no se hicieron commits.

Se verificaron 52 hashes de salida y la instantánea de fuentes; las cuatro
auditorías conservadas y las métricas recalculadas no presentan errores de
integridad. Pasaron 132 pruebas en carla-env con CARLA_PYTHONAPI configurado.
La derivación procesa 17.28 millones de observaciones por bloques.

El siguiente diagnóstico debe explicar los bloqueos y rechazos de cien
antes de considerar ese régimen una capacidad vial representativa. No se
exige cero invasiones ni una ventaja del selector histórico.

## Cierre de la derivación y revisión visual

Se generaron 9120 celdas de 50 m / 60 s, 4437 con presencia. Las guías
incluyen 48 bandas y dibujan 37 con soporte; error máximo de q-k*v menor
que 1e-12. Se conservaron tiempos y distancias al agrupar; los recuentos de
las mitades y de los histogramas coinciden con los totales originales.
102060 muestras fuera de proyección driving se excluyen de las celdas
locales, conservándose en registros y series globales.

Velocidad de presencia por mitades: veinte aleatorio 10.38/10.45 km/h e
histórico 10.70/10.57; cien aleatorio 2.87/0.63 e histórico 2.56/0.80.
Con cien, la segunda mitad acumula 95.85 %/94.29 % de exposición a menos
de 0.2 m/s. Baja velocidad describe el estado, no demuestra la causa.

Se renderizaron las doce páginas del PDF y se revisó su composición,
incluidas las láminas 09 y 12 a mayor resolución. Se corrigió una leyenda
que tapaba dos valores en la comparación de mitades. Validación registrada
en `validation.json`. No se sobrescribieron figuras anteriores.
