# Datos de entrada y salida

## Entradas de simulación

Los catálogos vinculan cada destino con una posición del mapa. Un historial inicial contiene una fila por visita previa, con el identificador del vehículo, el destino y el orden de la visita. El selector uniforme elige entre los destinos habilitados. El selector histórico también consulta las visitas del vehículo.

| Datos | Uso |
|---|---|
| [Catálogo de Town01](input/catalogs/Town01/destinations_config.csv) | Define los destinos disponibles, sus categorías y los índices de aparición correspondientes. |
| [Catálogo de Town03](input/catalogs/Town03/destinations_config.csv) | Contiene destinos de ejemplo para ese mapa. |
| [Historial inicial de ejemplo](input/histories/Town01/bootstrap/vehicle_history_dummy.csv) | Ofrece visitas sintéticas para las configuraciones de viaje individual y de varios vehículos. Cada vehículo lee sus propias filas. |
| [Historiales por flota](input/histories/Town01/) | Cada configuración de flota indica su CSV en `vehicle_history_config`. En `run_trips.py` y `observe_trips.py`, `--history-in` permite sustituir el CSV de los modos que cargan visitas iniciales. |
| [Ejemplos por zonas](input/examples/) | Ilustran cómo describir zonas, destinos y perfiles de demanda. Los viajes en Town01 utilizan el catálogo del mapa. |

## Salidas de una corrida o campaña

Con la configuración distribuida, los ejecutores de viajes y campañas de demanda guardan sus registros en [data/output/](output/). La carpeta de cada corrida tiene un identificador propio. En una campaña, el ejecutor crea además una carpeta de coordinación que apunta a las corridas de sus casos.

| Directorio | Qué encontrarás |
|---|---|
| Carpeta de corrida | La configuración efectiva en `run_config.json` y los CSV de viajes, trayectorias, eventos, visitas y métricas. La observación por paso y la captura de imágenes dependen del ejecutor y sus opciones. |
| Carpeta de campaña | El manifiesto JSON de los casos, las auditorías, las huellas de integridad y una copia del código y de las entradas. Una campaña completada contiene también el análisis de movilidad. |
| Carpeta de análisis | Los informes y las tablas que solicites. Si generas gráficas, su directorio contiene las figuras y una galería HTML. Tú eliges el directorio de destino al ejecutar las herramientas de análisis. |

`run_trips.py` indica la carpeta tras **Salida guardada en** y `observe_trips.py` tras **Revisión guardada en**. En una campaña de demanda, la última línea indica el estado y la ruta de su manifiesto. Busca el caso por `vehicle_count` y `scenario` y resuelve las rutas de `cases[].run_directories` desde `data/output/`. [Cómo leer los registros](../docs/referencia/datos-y-metricas.md#seguir-un-viaje)
