# Documentación de TrafficIA

## Ejecución y configuración

| Tarea | Guía |
|---|---|
| Instalar el entorno y conectar el cliente a CARLA | [Preparar el entorno](guias/manual.md#preparar-el-entorno) |
| Ejecutar una primera simulación y localizar sus registros | [Primera simulación en Town01](../README.md#primera-simulación-en-town01) |
| Elegir una flota, un catálogo y un historial inicial | [Configuración de viajes y campañas](../config/README.md) y [entradas de simulación](../data/README.md#entradas-de-simulación) |
| Localizar un punto de aparición o comprobar rutas entre destinos | [Inspección del mapa](guias/manual.md#inspeccionar-el-mapa) y [catálogo de Town01](referencia/destinos-town01.md) |
| Ejecutar ambos selectores con las flotas configuradas | [Comandos de campaña](guias/manual.md#ejecutar-una-campaña) |
| Obtener métricas, gráficas y una galería de una campaña guardada | [Análisis y gráficas](guias/manual.md#analizar-y-graficar) |

## Funcionamiento y registros

- La [arquitectura del simulador](referencia/arquitectura.md) sigue un viaje desde la lectura del escenario hasta la llegada y la siguiente elección de destino.
- La [referencia de registros y métricas](referencia/datos-y-metricas.md) explica cómo relacionar intentos, visitas y observaciones, y qué viajes entran en cada cálculo.
- La [bitácora técnica](historial/bitacora.md) sigue la incorporación de la navegación por destinos, la observación por vehículo y la ejecución de campañas.
