# Diagnóstico de detenciones y comparación de políticas

Fecha: 2026-09-23. Experimento autorizado: 100 vehículos, `random_baseline`,
semilla 210, 300 s por política, ritmo solicitado 1x. Los modelos, spawns,
clima preparado e historial inicial se conservan. Límite por viaje desactivado.
No se modifican los parámetros de conducción ni se hacen commits.

## Qué significa el contador

La regla original mide el tiempo desde la salida o desde la última muestra
con velocidad **estrictamente mayor que 0.2 m/s** (0.72 km/h). Al llegar a
60 s termina el viaje como `blocked`, espera cinco segundos y puede elegir
otro destino desde su posición real. No destruye el vehículo.

`keep_trip` registra el mismo aviso una vez por episodio del contador y
conserva el viaje. Superar 0.2 m/s reinicia el contador y permite un aviso
posterior. La llegada tiene prioridad sobre el aviso. El tiempo medio de
viajes completados sigue excluyendo viajes pendientes; debe acompañarse de
su cantidad y del tiempo detenido, para evitar sesgo de supervivencia.

La igualdad exacta a 0.2 m/s no reinicia el contador. El campo histórico
`stopped_time_s` usa estrictamente menor que 0.2; se preserva esta convención
para no cambiar silenciosamente las métricas existentes. Los episodios
físicos nuevos usan menor o igual e integración por extremo derecho del tick.

## Cómo observar

Preparar CARLA en ventana normal, Town01 limpio, renderizado activo. Ejecutar:

```powershell
cd C:\CARLA\TrafficIA
.\carla-env\Scripts\python.exe -u scripts/run_blocked_comparison.py
```

Se ejecutan 15 s técnicos, 300 s `terminate` y 300 s `keep_trip`, en ese orden.
`--check-only` solo comprueba el servidor y las entradas. La prueba breve puede
ejecutarse sola con `--technical-only`; después usar `--skip-technical`.

Al principio se sigue al primer vehículo activo. Desde 30 s de detención se
sigue el contador mayor; al primer aviso de 60 s se fija ese vehículo hasta
el cierre, aunque cambie de viaje. La vista está 22 m arriba y 12 m detrás,
inclinada 60 grados. La consola muestra cada segundo simulado el estado.
Solo el runner hace tick. No se crean sensores RGB ni se guardan imágenes.

## Evidencia disponible

- `blocked_warnings.csv`: umbral alcanzado, vehículo/viaje, destino y política.
- `stop_thresholds.jsonl`: contexto exacto de cada aviso, incluso si termina
  el viaje en ese mismo frame.
- `stop_observations.jsonl`: contexto cada 0.5 s y en avisos/recuperaciones;
  posición, carril proyectado, fase, ruta restante, controles y contactos.
- `stop_episodes.jsonl`: detención física continua a través de cambios de viaje,
  con tiempo separado en circulación, espera en destino y espera de reintento.
  Recuperación o censura al cierre; no se supone que un episodio pendiente terminó.
- `spectator_log.json`: cambios de seguimiento, vehículo fijado. No demuestra
  por sí solo que una persona vio el evento ni que la imagen fuera legible.
- `stop_review_config.json`: semántica y hashes del código. La campaña conserva
  instantánea de código/entradas, auditorías, hashes de salida y consolas.

Los detectores oficiales se invocan una sola vez por control, como antes.
Se conserva su respuesta y el frame en que se emitió el comando; se observa
la física en el frame siguiente. `agent_vehicle_obstacle` y
`agent_traffic_light` son decisiones de frenado y pueden coexistir. Se separa
`arrival_brake` y `dwell_brake`. `insufficient_evidence` significa que esos
datos no explican el frenado, o que no hay un comando vigente; no prueba un fallo.

Vehículos cercanos: flota configurada, radio de 30 m, distancias entre centros,
no separación entre carrocerías. Contactos recientes: hasta 20 callbacks de
los últimos cinco segundos; el registro completo sigue en `events_log.csv`.
El carril es una proyección al mapa, no una prueba de permanencia sobre calzada.

## Interpretación y estado

La última campaña larga tuvo su primer `blocked` a 287.7 s, vehículo 084,
viaje 001. El ejemplo previo vehículo 027/viaje 014 era ilustrativo.
Una corrida de 300 s puede no reproducir ese evento o dejar poco tiempo para
observar su evolución. No se ampliará automáticamente.

Pasaron 142 pruebas antes de la ejecución y 144 tras añadir comprobaciones
de aborto sin visita y comparación de condiciones. Entorno carla-env y SDK
local; última salida en `data/output/blocked_unit_tests_after_crash.txt`.

### Prueba técnica y crash del servidor

Campaña: `data/output/blocked_comparison_20260923T235312623044Z/`.
Corrida: `data/output/town01_random_baseline_seed_210_20260923T235312884762Z/`.
Se alcanzaron los 15 s: 30,000 observaciones, cero errores de integridad,
cero colisiones/invasiones, cero avisos y 100 viajes pendientes terminados
como `aborted`. Velocidad de presencia 13.506 km/h. La ejecución y limpieza
de la corrida tomaron 54.656 s de pared (0.274x efectivo, aunque se solicitó 1x).
Se registraron decisiones de frenado por obstáculos. El estudiante confirmó
que la vista del espectador era clara.

A las 17:54:07 locales el preflight posterior a la corrida confirmó cero
vehículos/sensores, modo asíncrono y renderizado. Después falló por timeout
la verificación final/restauración de la campaña. El estudiante reportó la
ventana fatal de Unreal y el crash context confirma:

- `DXGI_ERROR_INVALID_CALL`, `D3D11Query.cpp:356`, assert de Unreal/D3D11.
- GPU utilizada: Intel UHD Graphics 770. `MemoryStats.bIsOOM=0`; no se
  registra como agotamiento de RAM.
- Inicio: `-quality-level=Low -dx11 -windowed -ResX=800 -ResY=600`.
- Resumen de evidencia en `crash_summary.json` dentro de la campaña.

El momento coincide con el cierre; **no está demostrado** que lo cause el
espectador, su restauración, el clima o la cantidad de vehículos. El mismo
tipo de error gráfico ya figuraba en la bitácora; ahora ocurrió sin RGB.
Se conserva `status=incomplete` en la campaña, aunque la corrida técnica y
su auditoría terminaron. No se iniciaron las dos corridas de 300 s.

Pendiente: que el estudiante reinicie CARLA/Town01, repetir la prueba breve
y, si completa el cierre, ejecutar la comparación. No reiniciar ni cambiar
mapa automáticamente. La decisión de adoptar `keep_trip` en las campañas
académicas queda pendiente; la opción predeterminada sigue siendo `terminate`.
