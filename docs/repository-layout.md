# Organización del repositorio

Reorganización del 9 de noviembre de 2026. Se trasladaron seis documentos y 25 archivos JSON/CSV. Los parámetros, los datos y los manifiestos preparados conservan exactamente sus bytes originales.

## Carpetas de trabajo

```text
TrafficIA/
├── README.md                       Entrada principal y comandos
├── docs/
│   ├── README.md                    Índice de documentación
│   ├── project-graduation-context.md
│   ├── rutas.md                     Catálogo documentado de destinos
│   ├── archive/                     Propuestas y redacción de etapas anteriores
│   └── relocation-manifest.json     Ubicación anterior, nueva y SHA-256
├── config/
│   ├── trips/                       Demostraciones de uno o varios vehículos
│   ├── experiments/
│   │   ├── scaling_pilots/          Pilotos de 5, 10 y 20 vehículos
│   │   └── demand_20_100/           Comparación principal, clima y manifiesto
│   └── examples/                    Escenarios iniciales y Traffic Manager
├── data/
│   ├── input/
│   │   ├── catalogs/Town01/         Catálogo utilizado en la evaluación
│   │   ├── catalogs/Town03/         Catálogo del otro mapa
│   │   ├── histories/Town01/
│   │   │   ├── bootstrap/          Historial sintético inicial compartido
│   │   │   ├── scaling_pilots/     Historiales de 5, 10 y 20 vehículos
│   │   │   └── demand_20_100/      Historial de 100 vehículos
│   │   └── examples/               CSV de zonas, demanda y destinos iniciales
│   └── output/                     Corridas y campañas con sus nombres originales
├── scripts/                        Comandos ejecutables
├── src/                            Implementación
└── tests/                          Pruebas sin ejecutar una campaña real
```

## Reproducir las configuraciones conservadas

Los JSON y los manifiestos mantienen las rutas escritas antes de la reorganización. Por ejemplo, el campo `destinations_config` sigue indicando `data/input/Town01/destinations_config.csv`. No hay que editarlo: [project_path](../src/project_paths.py) lo resuelve como `data/input/catalogs/Town01/destinations_config.csv` al leerlo.

También se admiten los nombres anteriores al ejecutar los scripts del proyecto. Las ubicaciones nuevas son las que deben usarse al navegar en el explorador o crear enlaces. La compatibilidad se aplica en Python; no crea duplicados ni accesos directos en las carpetas antiguas.

Si existe un archivo en una ruta original, se utiliza ese archivo antes de buscar su nueva ubicación. Así, una copia histórica completa conserva sus propias entradas. No se buscan archivos fuera del proyecto ni se sustituye un dato ausente por otro parecido.

Las verificaciones de SHA-256 y la captura de fuentes de las campañas utilizan el mismo mecanismo. Las claves guardadas en los manifiestos no se reescriben. Los scripts de preparación conservan el formato y las referencias de esas entradas y siguen rechazando sustituir un archivo existente por contenido diferente.

Ejemplo de comando con la ubicación actual:

```powershell
.\carla-env\Scripts\python.exe scripts/run_trip_simulation.py --config config/trips/single_vehicle_trip.json
```

La comparación de 20 y 100 se configura en [config/experiments/demand_20_100](../config/experiments/demand_20_100/). Sus JSON base siguen indicando 1800 segundos; las campañas de 3600 emplearon el ajuste de duración de ejecución. La reorganización no cambia esa distinción.

## Evidencia conservada

[relocation-manifest.json](relocation-manifest.json) registra los 25 archivos de entrada con su ubicación anterior, ubicación actual, tamaño y SHA-256 original. La prueba `test_project_paths.py` comprueba esos valores y la compatibilidad de las rutas. Las entradas antiguas se respaldaron localmente en `data/output/repository_layout_20261109/originals/` junto al plan de traslado; esa copia local no se incorpora a Git.

Las carpetas históricas de `data/output` mantienen sus nombres y ubicación. Allí los identificadores de corrida, las rutas relativas, las instantáneas de código, los resúmenes y las figuras forman parte de la evidencia. Se conservan también los resultados y los archivos de configuración efectivos de cada ejecución.

Los documentos de la tesis y las presentaciones son externos a este repositorio. Cuando se quiera abrir manualmente una entrada trasladada desde un enlace antiguo, su ubicación actual se puede consultar en el manifiesto. No es necesario cambiar el contenido de los JSON o CSV para usarla en los scripts de TrafficIA.
