# Campaña exploratoria de 20 y 100 vehículos

Preparada el 2026-09-18 a solicitud del estudiante y ejecutada ese día por él.
Actualización del 2026-09-19: las cuatro corridas largas terminaron y sus
[gráficas y análisis](graficas_demandas_20_100.md) ya están disponibles.
Las pruebas técnicas iniciales se documentan por separado. No se hicieron
commits ni cambios de conducción para este análisis.

## Diseño y alcance

| Orden | Vehículos totales | Selector | Semilla | Duración simulada |
|---|---:|---|---:|---:|
| 1 | 20 | `random_baseline` | 210 | 1,800 s |
| 2 | 20 | `history_80_20` | 210 | 1,800 s |
| 3 | 100 | `random_baseline` | 210 | 1,800 s |
| 4 | 100 | `history_80_20` | 210 | 1,800 s |

CARLA 0.9.15, Town01, cero peatones, paso fijo 0.05 s, ritmo solicitado
5×, renderizado activo y sin cámaras RGB. Se conserva el clima lluvioso de
la campaña anterior, con plantilla explícita en `config/experiments/demand_20_100/weather.json`.
Se restaura el clima previo al terminar. El controlador, rutas, llegadas,
velocidad objetivo, detector `blocked`, pausas e incidentes no se ajustan.
Los sensores existentes de colisión/invasión sí permanecen.

Los 1,800 s permiten comparar con la campaña larga previa de veinte y observar
varios viajes por vehículo cuando la circulación lo permita. No garantizan
equilibrio, convergencia ni precisión estadística. Una semilla ofrece un primer
contraste; no basta para concluir superioridad de un selector. Se conservan
el arranque y las esperas; cualquier exclusión de calentamiento en un análisis
posterior deberá justificarse y etiquetarse sin reescribir los registros.

La [investigación bibliográfica](fundamento_demandas_town01.md) respalda 20/100
como candidatos adaptados de NoCrash para Town01. Aquí son agentes totales;
la referencia usa tráfico de fondo, otra versión y peatones. Veinte es la
carga menor y cien la mayor por construcción; las etiquetas flujo libre y
congestión requieren evidencia propia. El estudiante decidió probar
directamente cien, sustituyendo como siguiente acción el barrido intermedio.

## Entradas y reproducibilidad

- `config/experiments/demand_20_100/town01_020.json` conserva los veinte spawns existentes.
- `config/experiments/demand_20_100/town01_100.json` extiende ese prefijo mediante máxima
  distancia mínima entre centros, desempate determinista y spawns únicos en
  carriles de circulación fuera de intersecciones. Separación mínima: 16.1605 m.
  Es un filtro geométrico; por sí solo no prueba capacidad ni circulación.
- Veinte usa sus 600 visitas iniciales; cien usa las 3,000 de
  `data/input/histories/Town01/demand_20_100/vehicle_history_100.csv`. Cada vehículo tiene
  30 visitas, generadas con semilla de bootstrap 42. **La semilla de corrida
  es 210**; son funciones distintas. Los primeros veinte historiales coinciden
  exactamente y se preservan sus flujos aleatorios individuales.
- El historial crece con viajes completados dentro de cada corrida. Cada caso
  vuelve a las mismas entradas iniciales; no hereda aprendizajes del anterior.
  El bootstrap de 30 visitas se carga en `history_80_20`. Baseline mantiene
  selección uniforme y comienza con un historial de salida vacío, al que
  añade sus llegadas; no usa las visitas iniciales para elegir destinos.
- Se mantienen los 42 destinos. Los nuevos puntos de aparición son orígenes,
  no destinos adicionales.
- `preparation_manifest.json` registra geometría, OpenDRIVE y hashes. La
  preparación se puede reproducir con `scripts/prepare_demand_campaign.py`
  y el `run_config.json` de la corrida del 17 de septiembre usado como clima.
  Rechaza sobrescribir entradas diferentes.

## Ejecución

Preparar **una sola instancia** de CARLA en Town01. Puede usarse el comando
habitual `CarlaUE4.exe -quality-level=Low -dx11 -RenderOffScreen`; cambiar el
mapa antes de comenzar. El mundo debe estar vacío y asíncrono. El script no
reinicia el servidor, no cambia mapas ni elimina actores de otras sesiones.

Desde PowerShell:

```powershell
cd C:\CARLA\TrafficIA
.\carla-env\Scripts\python.exe -u scripts/run_demand_campaign.py --seed 210 --seconds 1800 --simulation-speed 5
```

El comando ejecuta las cuatro filas secuencialmente. No se requiere cambiar
de mapa ni lanzar un segundo proceso entre veinte y cien. No ejecutar otro
cliente que avance la simulación ni modificar fuentes/entradas durante la
campaña. El ritmo real queda medido; 5× es el objetivo máximo solicitado,
no una promesa de terminar las cuatro corridas en 24 minutos.

Comprobación opcional de solo lectura:

```powershell
.\carla-env\Scripts\python.exe scripts/run_demand_campaign.py --check-only
```

Si se necesitan dos sesiones separadas, ejecutar el mismo comando largo
añadiendo `--counts 20` o `--counts 100`. Cada invocación crea una campaña
nueva: **no reanuda** una corrida interrumpida. Conservar todas las carpetas
para reunir posteriormente los análisis.

## Registros y fallos

La consola muestra `CAMPAIGN` y una carpeta nueva
`data/output/demand20_100_seed_210_<fechaUTC>/`. Dentro quedan:

- `campaign.json`: estado, casos, rutas de resultados, tiempos y recuentos.
- `source_snapshot/`, `source_sha256.json` y verificación final de fuentes.
- Consolas, comprobaciones del servidor antes/después y auditorías por caso.
- `metrics/summary.csv`, `destinations.csv`, `analysis.json` y `report.md`.
- Hashes de resultados y `final_server_state.json`.

Los registros originales por corrida siguen en `data/output/town01_.../`,
referenciados por el manifiesto: viajes, llegadas, historial, eventos,
diagnóstico de navegación y observaciones de todos los vehículos por frame.
En total se esperan 8,640,000 observaciones en las cuatro corridas largas.
El observador sin cámaras ahora escribe al CSV sin conservar una copia de
cada fila en RAM. El auditor lee ese CSV secuencialmente y comprueba continuidad
de frames/tiempos, fases, vehículos, referencias a viajes y llegadas, junto con
la auditoría de métricas. No clasifica automáticamente colas ni verifica
geometría de carril o evidencia visual.

Una colisión, invasión, `blocked`, `timeout` o `route_failed` queda registrada
y no detiene por sí sola la campaña. Un fallo técnico o de integridad sí
detiene los siguientes casos y conserva las salidas parciales con estado
`incomplete` y `failure.txt`. `Ctrl+C` solicita el cierre y limpieza de actores
propios mientras el servidor responda. Una caída de CARLA puede impedir esa
limpieza; el manifiesto registra el fallo, no lo presenta como éxito.

Al finalizar correctamente aparece `COMPLETE ...\campaign.json`. Para la
revisión posterior basta indicar esa ruta y compartir el resumen de consola;
no borrar las carpetas `town01_...` a las que apunta.

## Comprobaciones realizadas

Pasaron **123 pruebas unitarias** con `carla-env`, incluida conservación de
historiales/prefijos, rechazo de mundo ajeno y detección de huecos en el
auditor. Log: `data/output/demand_preparation_20260918/unit_tests_final.txt`.

La campaña técnica `data/output/demand20_100_technical_20260918_v2/` completó
cuatro casos de **15 s**, semilla 210, ritmo solicitado 5×, con las entradas y
el comando nuevos. Las parejas tienen condiciones registradas comparables.

| Caso técnico | Observaciones | Llegadas | Cortes al terminar | Tiempo de proceso real |
|---|---:|---:|---:|---:|
| 20/baseline | 6,000 | 0 | 20 | 11.891 s |
| 20/histórico | 6,000 | 0 | 20 | 11.796 s |
| 100/baseline | 30,000 | 0 | 100 | 53.344 s |
| 100/histórico | 30,000 | 1 | 100 | 53.969 s |

Cero errores de integridad, colisiones o invasiones en estas pruebas breves.
Los cortes son `aborted` con motivo `simulation_end`; no son `blocked`.
La llegada del histórico de cien se asoció al frame correcto y su historial
terminó con 3,001 visitas. Los cien actores se crearon y retiraron en ambos
casos. Se verificó Town01 limpio, asíncrono, sin paso fijo, clima restaurado y
renderizado al cerrar. El tiempo de proceso incluye preparación/rutas/limpieza;
no se extrapola como duración exacta de 1,800 s ni prueba estabilidad larga.

El intento técnico inicial, conservado en
`data/output/demand20_100_technical_20260918/`, ejecutó 15 s de veinte/baseline
y limpió el servidor, pero el auditor nuevo solicitó un archivo de llegadas
que el runner solo crea al llegar por primera vez. Se corrigió el auditor:
permite ausencia del archivo únicamente con cero completados y exige
correspondencia de recuentos. Hay prueba de regresión para ambos casos.
Ese intento permanece marcado `incomplete` y no se mezcla con la campaña v2.

La única modificación nueva en `src/` es el almacenamiento del observador
sin cámaras: escritura al CSV y contadores por vehículo, sin copia acumulada
de filas en RAM. No se eliminaron registros. Los archivos `trip_runner.py`,
`route_planner.py` y `carla_agent.py` coinciden byte a byte con la instantánea
de la campaña larga del 17 de septiembre. En el cierre de esta preparación
todavía no se habían ejecutado las corridas largas; el estudiante las
completó después el mismo día 18.

## Siguiente análisis

Actualización del 19: el análisis de abajo ya se realizó y produjo
[once láminas](graficas_demandas_20_100.md). Las métricas y hashes son íntegros,
pero cien presenta bloqueos repetidos, rutas rechazadas y contactos. El
pendiente inmediato es reconstruir sus primeras secuencias antes de decidir
la demanda mayor definitiva o nuevas cantidades intermedias.

Auditar las cuatro corridas largas, revisar motivos de incompletos y episodios
de contacto; comparar destinos, duración de completados, velocidad de presencia
y eventos normalizados por exposición. Revisar también la evolución temporal,
paradas/colas y las relaciones locales v–k, q–k y v–q en las mismas celdas de
50 m y ventanas de 60 s usadas antes. El objetivo es ampliar la cobertura de
densidades observadas, sin forzar la forma de una curva fundamental.

Después decidir repeticiones con más semillas, suficiencia temporal y necesidad
de demandas intermedias. Un menor ritmo de ejecución con cien no prueba
congestión; una cola por rojo ni una espera en destino la prueban por sí solas.
