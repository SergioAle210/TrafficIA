# Destinos de Town01

Cada lugar tiene un `destination_id` que se conserva en los viajes y en el historial del vehículo. El catálogo asocia ese identificador con una ubicación de CARLA y una categoría de actividad. Consulta los identificadores y puntos de aparición disponibles en el [catálogo de Town01](../../data/input/catalogs/Town01/destinations_config.csv).

| Categoría | Lugares que agrupa |
|---|---|
| `residential` | Casas y apartamentos. |
| `work_education` | Oficinas y centros educativos. |
| `services_leisure` | Restaurantes, hoteles, servicios de salud y lugares de recreación. |

## Referencias viales

El lector selecciona las filas habilitadas para el mapa activo y exige identificadores únicos y al menos dos destinos. El campo `reference_type` determina cómo se obtiene el punto vial. [Lector del catálogo](../../src/demand/destinations.py)

| Valor de `reference_type` | Campos y resolución |
|---|---|
| `spawn_point` | `spawn_point_index` es un índice de la lista que devuelve `get_spawn_points()`. El simulador proyecta su posición sobre un carril de conducción. |
| `coordinates` | `x`, `y` y `z` indican la posición que se proyecta sobre un carril de conducción. |

Con cualquiera de las dos referencias, los valores opcionales `road_id` y `lane_id` deben coincidir con el punto proyectado. Para incorporar un lugar, localízalo con el espectador, comprueba el carril y valida las rutas en ambos sentidos. Si vas a usar un historial existente, verifica que sus visitas sigan apuntando a identificadores habilitados. [Inspección del mapa y validación de rutas](../guias/manual.md#inspeccionar-el-mapa)
