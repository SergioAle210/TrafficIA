# Destinos candidatos de Town01

Los números corresponden a `spawn_point_index` de CARLA. No describen una ruta
prefijada: `GlobalRoutePlanner` calcula la ruta entre el origen y el destino.

Se usan exactamente tres categorías normalizadas:

- `residential`: casas y apartamentos.
- `work_education`: oficinas y centros educativos.
- `services_leisure`: salud, comercio, turismo, alimentación y recreación.

| ID | Descripción | Categoría normalizada |
|---:|---|---|
| 0 | Parque | services_leisure |
| 3 | Casa | residential |
| 4 | Casa | residential |
| 5 | Casa | residential |
| 6 | Casa | residential |
| 10 | Cabaña para turistas | services_leisure |
| 11 | Casa | residential |
| 14 | Casa | residential |
| 15 | Hospital | services_leisure |
| 17 | Casa | residential |
| 18 | Clínica | services_leisure |
| 20 | Apartamento | residential |
| 22 | Apartamento | residential |
| 23 | Restaurante | services_leisure |
| 27 | Apartamento | residential |
| 30 | Oficina | work_education |
| 32 | Hotel | services_leisure |
| 33 | Tienda | services_leisure |
| 35 | Hotel | services_leisure |
| 37 | Oficina | work_education |
| 39 | Oficina | work_education |
| 41 | Hotel | services_leisure |
| 43 | Hotel | services_leisure |
| 44 | Oficina | work_education |
| 45 | Apartamento | residential |
| 50 | Clínica | services_leisure |
| 52 | Hotel | services_leisure |
| 54 | Oficina | work_education |
| 55 | Hotel | services_leisure |
| 58 | Casa | residential |
| 60 | Casa | residential |
| 67 | Restaurante | services_leisure |
| 68 | Apartamento | residential |
| 69 | Clínica | services_leisure |
| 74 | Área de juegos | services_leisure |
| 84 | Apartamento | residential |
| 91 | Restaurante | services_leisure |
| 93 | Casa para turistas | services_leisure |
| 94 | Casa | residential |
| 95 | Casa | residential |
| 101 | Jardín de niños | work_education |
| 133 | Casa / origen habitual de prueba | residential |

## Correcciones realizadas

- Se eliminó la aparición duplicada del ID 54.
- Se excluyeron los IDs 24 y 49 porque son puentes y no representan una
  actividad de destino. Pueden conservarse como infraestructura del ODD.
- Se excluyó el ID 75: desde el origen 133, CARLA devuelve una ruta degenerada
  de 0 m aunque los puntos están separados físicamente 62.5 m sobre el mismo
  tramo. No es segura para entregarla a `BasicAgent`.
- Todos los restaurantes comparten categoría.
- El jardín de niños se clasificó como trabajo/educación.
- Parque y área de juegos se conservaron como destinos de ocio.
