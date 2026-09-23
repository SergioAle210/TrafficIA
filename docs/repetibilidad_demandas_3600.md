# Repetición de 3600 segundos y comparación - 23 de septiembre de 2026

La segunda campaña comenzó el 22 de septiembre a las 22:50 y terminó el 23 a las 06:10, hora de Guatemala (7 h 20 min aproximadamente). La primera fue la noche del 21 al 22. Ambas: Town01, semilla 210, 20/100 vehículos, ambos selectores, 3600 s por combinación y 5x solicitado, sin cámaras.

- [Galería de catorce láminas](../data/output/visual_analysis20_100_3600_repeat_20260923/index.html).
- [PDF completo](../data/output/visual_analysis20_100_3600_repeat_20260923/graficas_campana.pdf).
- [Comparación detallada y diferencias porcentuales](../data/output/visual_analysis20_100_3600_repeat_20260923/comparacion_repeticiones.md).
- [Informe de la segunda campaña](../data/output/visual_analysis20_100_3600_repeat_20260923/informe_graficas.md).
- [Paquete descargable](../data/output/graficas_20_100_3600_repeticion_20260923.zip).

## Comparación directa

En cada celda: primera / repetición. Las tasas incluyen toda la exposición, no solo viajes completados.

| Vehículos | Selector | Llegadas | Velocidad (km/h) | Tiempo completado (s) | Blocked | Rutas rechazadas | Colisiones (callbacks) | Invasiones |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 20 | random_baseline | 422 / 423 | 10.416 / 10.410 | 161.59 / 161.58 | 0 / 0 | 0 / 0 | 0 / 12 | 2 / 0 |
| 20 | history_80_20 | 397 / 398 | 10.637 / 10.685 | 171.86 / 171.31 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 100 | random_baseline | 252 / 237 | 1.748 / 1.520 | 171.05 / 169.98 | 3932 / 4154 | 1280 / 804 | 160955 / 542630 | 30 / 72 |
| 100 | history_80_20 | 252 / 254 | 1.678 / 1.702 | 183.30 / 188.98 | 4147 / 4152 | 235 / 235 | 77904 / 51473 | 17 / 8 |

## Qué se repite y qué cambia

- Con veinte, las llegadas aumentan en una por escenario (menos de 0.3 %) y la velocidad varía menos de 0.5 %. Sigue sin blocked ni route_failed. Aleatorio pasa de cero a 12 callbacks de colisión, agrupados en un episodio descriptivo; invasiones de dos a cero. Histórico conserva cero colisiones e invasiones.
- Con cien aleatorio: llegadas -5.95 %, velocidad -13.08 %, blocked 3932 a 4154 y rechazos 1280 a 804. La tasa de colisiones pasa de 920.69 a 3570.84 callbacks/vehículo-km (+287.85 %); grupos descriptivos 173 a 396. El conteo bruto sube de 160955 a 542630 (+237.13 %). La exposición por distancia también cambia.
- Con cien histórico: llegadas +0.79 %, velocidad +1.44 %, blocked 4147 a 4152; rechazos permanecen en 235. La tasa de colisiones baja de 464.23 a 302.39 callbacks/vehículo-km (-34.86 %); grupos descriptivos 65 a 45. Invasiones 17 a 8.
- Se mantiene el contraste agregado entre las flotas en estas dos ejecuciones, pero no hay repetibilidad exacta de eventos ni trayectorias demostrada. Las mayores diferencias están en incidentes del aleatorio con cien. No se identificó aquí el mecanismo de divergencia.
- Dos repeticiones con la misma semilla no sustituyen una campaña con semillas independientes ni permiten declarar superioridad causal del selector. Se preservan incidentes como métricas; no se exige conducción perfecta.

## Comparabilidad y trazabilidad

Se volvieron a verificar 52 archivos de salida de cada campaña (104 en total) y las dos instantáneas de fuentes. Sus 27 archivos de código e inputs coinciden exactamente. Las cuatro comparaciones por cantidad/selector tienen igual mapa, duración, semilla, modelos/spawns, condiciones ambientales registradas, parámetros de llegada/ruta/tiempo y semántica de métricas. Sin errores en auditorías conservadas ni métricas recalculadas.
El historial se reinició desde el mismo bootstrap, no continuó desde la campaña anterior. En histórico termina en 998 visitas con veinte y 3254 con cien.
El detector blocked sigue cerrando el intento tras 60 s sin superar 0.2 m/s. La propuesta de mantener el viaje durante esperas aún no se implementó. Esta comparación estudia el modelo actual, no esa alternativa.

## Cambios y reproducción

Se reutiliza el generador de doce láminas con guías; la opción --compare-data incorpora las láminas 13 (métricas entre repeticiones) y 14 (evolución de velocidad y llegadas). scripts/campaign_comparison.py empareja casos, rechaza condiciones incompatibles y registra deltas. Si la base es cero, el cambio porcentual queda indefinido, sin inventar un porcentaje.
Las gráficas de flujo conservan tramos, ventanas, bandas y método de agregación. No ajustan curvas a una forma teórica ni estiman capacidad.
Pasaron 135 pruebas en carla-env con CARLA_PYTHONAPI. Se conservan resultados anteriores y TeX del estudiante. No se inició CARLA ni se cambió controlador o detector; sin commits.

```powershell
.\carla-env\Scripts\python.exe scripts/build_campaign_plot_data.py --campaign data/output/demand20_100_seed_210_20260923T045032867422Z/campaign.json --output data/output/NUEVA_CARPETA
.\carla-env\Scripts\python.exe scripts/review_demand_chart_inputs.py --campaign data/output/demand20_100_seed_210_20260923T045032867422Z/campaign.json --output data/output/NUEVA_CARPETA
.\carla-env\Scripts\python.exe scripts/review_demand_chart_inputs.py --campaign data/output/demand20_100_seed_210_20260922T040147250610Z/campaign.json --output data/output/NUEVA_CARPETA/previous_review
.\carla-env\Scripts\python.exe scripts/plot_demand_campaign.py --data data/output/NUEVA_CARPETA --compare-data data/output/visual_analysis20_100_3600_20260922
```

## Evolución y cierre de validación

En la repetición, las llegadas por mitad (0-30 / 30-60 min) son:
20 aleatorio 215/208, 20 histórico 195/203, 100 aleatorio 220/17 y
100 histórico 183/71. En la primera campaña, cien aleatorio produjo
206/46 e histórico 185/67. En aleatorio de cien la segunda mitad cae
respecto a la campaña anterior de 0.628 a 0.196 km/h y sube a 98.37 % de
exposición bajo 0.2 m/s. Son medias ponderadas por exposición en ventanas
asignadas por su centro; desfase de 0.05 s documentado, sin inferencia causal.

Derivación de 17.28 millones de observaciones: 9120 celdas, 4253 ocupadas,
45 bandas guía y 33 con soporte; q=k*v en marcadores con error menor que
1e-12. Se excluyen de las celdas locales 293857 muestras sin proyección
driving; permanecen en registros y series globales. Esta exclusión es mayor
que las 102060 muestras de la primera campaña y limita interpretar toda
la nube como circulación normal. La causa de salida de calzada no se
investigó en esta entrega.

Los 44 deltas de comparación se verificaron contra los valores originales;
recuentos de mitades e histogramas conservan totales. Se renderizaron y
revisaron las catorce páginas del PDF, con inspección ampliada de las
láminas 09, 13 y 14. `validation.json` conserva comprobaciones.
