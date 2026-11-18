# Configuración de viajes y campañas

Los JSON de viajes definen el mapa, la flota, los puntos de aparición, el paso de simulación y la regla de selección de destinos. También indican dónde leer el catálogo. El selector uniforme empieza con un historial vacío y los demás modos cargan las visitas iniciales de cada vehículo desde `vehicle_history_config`. [Datos de entrada](../data/README.md#entradas-de-simulación)

| Configuración | Uso |
|---|---|
| [Viaje individual](trips/single_vehicle_trip.json) | Es la configuración predeterminada de `run_trips.py`. Define el origen del vehículo y usa el selector histórico. |
| [Viajes con varios vehículos](trips/multi_vehicle_trip.json) | Define la flota con `vehicle_count` y asigna un punto de aparición a cada vehículo mediante `initial_spawn_point_indices`. |
| [Recorrido cíclico](trips/single_vehicle_trip_cyclic.json) | Repite la secuencia de destinos de `destination_cycle_order` para comprobar la navegación. |
| [Flotas de tamaño creciente](experiments/scaling_pilots/) | Cada configuración indica su historial de entrada. Los vehículos que comparten dos configuraciones conservan su punto inicial. |
| [Campaña de demanda](experiments/demand_20_100/) | Reúne las configuraciones de flota, el clima común y el manifiesto que utiliza el ejecutor para verificar el mapa y sus entradas. |
| [Ejemplos](examples/) | Reúnen parámetros de referencia para escenarios de Town03 y Traffic Manager. El comando `run_traffic_manager.py` recibe sus parámetros en la línea de comandos. |

## Duración y parámetros efectivos

`duration_seconds` fija la duración total en segundos simulados. `max_trip_time_seconds` limita cada intento de viaje y admite `null` para dejarlo sin límite individual. `fixed_delta_seconds` fija el tiempo simulado que avanza el mundo en cada paso.

En `run_trips.py`, las opciones `--seed`, `--scenario` y `--seconds` tienen prioridad sobre el JSON para esa ejecución. En el ejecutor de campañas, `--seconds` se aplica a cada caso. Al finalizar puedes consultar los valores efectivos en el `run_config.json` de tu corrida. [Comandos de campaña](../docs/guias/manual.md#ejecutar-una-campaña)

## Integridad de las entradas

Las huellas SHA-256 incluyen los finales de línea. Si al clonar en Windows la campaña detecta una entrada distinta, comprueba el archivo señalado con `Get-FileHash -Algorithm SHA256` y consulta el [manifiesto de entradas](../docs/referencia/huellas-entradas.json). Los JSON de `config/trips/` y `config/examples/` y los CSV de `data/input/catalogs/` usan LF. Los JSON de `config/experiments/` y los CSV de `data/input/histories/` y `data/input/examples/` usan CRLF. Si el contenido coincide y solo cambió el formato, guarda el archivo con los finales de línea indicados y repite la comprobación.
