# Control de conducción e interpretación de incidentes

Revisión: 2026-09-17. Este documento explica los cambios que pueden reducir
colisiones e invasiones, y delimita lo que se puede concluir al comparar
`random_baseline` con `history_80_20`. No introduce cambios de conducción.

## Cambios aplicados y evidencia

| Cambio | Motivo y efecto esperado | Código / commit |
|---|---|---|
| Incluir un vehículo exactamente enfrente en la detección de obstáculos | El límite angular estricto de BasicAgent excluía 0°. La subclase cambia el límite inferior predeterminado a -0.001°; permite frenar ante ese vehículo. | `src/carla_agent.py`, `_vehicle_obstacle_detected`; `7e78670` |
| Reducir `distance_ratio` de 0.5 a 0.1 | El descarte de waypoints adelantaba el objetivo más allá de curvas cerradas. A 20 km/h, el radio de descarte pasa de unos 5.78 a 3.56 m, manteniendo la base de 3 m. Reduce el recorte por el interior. | `src/route_planner.py`, `build_basic_agent`; `483ee51` |
| Frenar siguiendo el carril antes de completar una llegada | Antes se declaraba la llegada todavía a unos 19 km/h en una curva y se ponía la dirección a cero. Ahora el viaje permanece activo durante desaceleración y alineación. | `src/arrival.py`, `src/trip_runner.py`; `a8e1d7b` |
| Conservar referencias laterales hasta la parada | El tramo final se muestrea cada 0.5 m, incorpora 6 m de continuación para guiar la dirección y reduce gradualmente el radio base de descarte de 3 a 1 m al aproximarse. | `src/route_planner.py`, `src/carla_agent.py`; `a8e1d7b` |
| Validar carril, parada y alineación de la llegada | Evita completar por proximidad desde el carril contrario. Actualmente exige velocidad ≤0.05 m/s, error angular ≤10° y lateral ≤0.5 m; contempla una continuación vial verificada de hasta 3 m en uniones de IDs. | `src/trip_runner.py`, `src/arrival.py`; `483ee51`, `a8e1d7b`, `5b53ca2` |

La aproximación limita la velocidad por distancia restante con desaceleración
de referencia de 1.5 m/s²; desde un crucero de 20 km/h comienza unos 10.8 m
antes del destino. Mantiene la dirección al frenar. La espera de cinco segundos
comienza después de completar la parada alineada. No se modificaron las
ganancias PID oficiales ni se añadieron decisiones dependientes del escenario.

La comparación del 8 de septiembre con tres vehículos, semilla 42, 600 s y
la misma regla de llegada aisló `distance_ratio`:

| Escenario | Colisiones 0.5 → 0.1 | Invasiones 0.5 → 0.1 |
|---|---:|---:|
| random_baseline | 6 → 0 | 10 → 0 |
| history_80_20 | 1 → 0 | 27 → 2 |

Son conteos de callbacks, no accidentes independientes. Las dos invasiones
restantes motivaron después el diagnóstico de llegada/espera. La bitácora
conserva los ensayos intermedios rechazados y las carpetas originales:
[contactos estáticos](bitacora_simulacion.md#2026-09-08--diagnóstico-de-contactos-estáticos-y-seguimiento-de-curvas)
y [aproximación y parada](bitacora_simulacion.md#2026-09-08--corrección-de-la-aproximación-parada-y-espera-en-destino).

La corrección del detector colineal tuvo otra validación: un contacto sostenido
entre dos carros generaba 852 callbacks de los 857 del baseline inicial.
Después del ajuste, la repetición tuvo siete callbacks y no repitió ese
contacto. No eran 857 accidentes. Ver el diagnóstico y sus límites en la
[primera investigación](bitacora_simulacion.md#problema-1-alcance-a-un-vehículo-detenido).

## Efecto sobre la comparación académica

Estos cambios sí modifican las tasas observadas. Son parte de la definición
del generador evaluado: elección de destinos, planificación y controlador
común corregido. No describen BasicAgent sin modificaciones ni conductores
humanos calibrados. Los ajustes se investigaron principalmente en Town01 y
semilla 42; repetir esa misma condición no prueba generalización.

Aplicar el mismo controlador a ambos selectores evita una diferencia de
implementación deliberada entre tratamientos. Sin embargo, el controlador
puede interactuar de manera distinta con las rutas elegidas y un conteo de
cero eventos ofrece poca información para distinguir sus tasas. No permite
afirmar que el 80/20 sea más seguro ni que el generador carezca de incidentes.

Otros elementos del ODD también limitan la interpretación: velocidad objetivo
de 20 km/h, detección de obstáculos y semáforos, selección de modelos, orígenes
dispersos, duración y semillas. Los pilotos no simulan deliberadamente una
población de conductores agresivos o distraídos. La flota depende de la semilla.
El cambio de renderizado/calidad del servidor debe registrarse como condición
de ejecución, sin atribuirle por adelantado un efecto sobre incidentes.

Se recomienda conservar este controlador durante los pilotos de 10/20 y la
comparación de selectores. No ajustarlo después de observar cada resultado
para eliminar eventos, ni reintroducir fallos para producirlos. La variación
entre semillas, flotas y duraciones debe estudiarse con un diseño registrado;
las dos demandas no deben elegirse solo por generar más incidentes.

Si posteriormente se necesita medir sensibilidad al controlador, realizar
una comparación separada con ambos selectores y condiciones emparejadas.
`--controller-distance-ratio 0.5` permite variar ese parámetro; **no restaura
todo el controlador antiguo**, porque mantiene las correcciones de detección
y llegada. Esa prueba no se ha solicitado ni ejecutado en esta revisión.

## Dónde inspeccionar cada corrida

- `run_config.json`: `route_planning.local_planner_options.distance_ratio`,
  `arrival_control`, `arrival_policy_version`, configuración y ambiente.
- `control_log.csv`: comandos, objetivo de seguimiento, radio de descarte,
  velocidad y error respecto al plan; requiere diagnósticos habilitados.
- `arrival_log.csv`: posición, carril, velocidad y alineación de cada llegada.
- `events_log.csv`: callbacks originales de colisión e invasión, incluidos
  los de espera sin viaje asociado; revisar marca, actor, frame y tiempo.
- `observation_log.csv`: fases, paradas, estado semafórico y vehículos cercanos
  cuando se utiliza el script de revisión sin cámaras.
- `metrics_summary.csv` y el informe de `scripts/analyze_mobility.py`: conteos
  y tasas con denominadores de exposición explícitos.

Los sensores de colisión e invasión permanecen activos. Se corrigió una
omisión anterior para incluir eventos durante las esperas; no se borran
marcas `Broken` o `NONE`. Una invasión no equivale automáticamente a infracción
o accidente. Las nueve invasiones conservadas en baseline/123 de 900 s del
9 de septiembre muestran que las correcciones no imponen cero eventos.

Los resultados históricos están bajo `data/output/`, excluido de Git. Para
una auditoría, conservar esas carpetas junto con código, configuración y
hashes; consultar solo los commits no recupera los datos experimentales.

Actualización del 2026-09-17: la
[campaña larga de veinte con 210/109](campana_larga_veinte_vehiculos.md)
conservó el controlador y registró 14/510 callbacks de colisión en baseline,
concentrados en dos episodios entre vehículos en intersecciones (0.30/12.95 s).
Ambos históricos registraron cero. Todos los viajes implicados llegaron y
las cuatro auditorías pasaron. Estos datos no demuestran una diferencia
estadística entre selectores; muestran por qué deben distinguirse callbacks,
episodios y exposición al definir la métrica, sin borrar los registros brutos.
