# Bitácora técnica de TrafficIA

## Catálogo y primeros viajes

La primera modalidad de circulación usó el autopiloto de Traffic Manager. El ejecutor de viajes incorporó después un catálogo de lugares de Town01 y la posibilidad de reutilizar un mismo vehículo en una secuencia de destinos. La configuración cíclica conserva esa modalidad para comprobar rutas conocidas. [Catálogo](../referencia/destinos-town01.md) y [configuraciones de viaje](../../config/README.md)

## Elección de destinos y navegación

Al recorrido cíclico se añadieron la elección uniforme y la elección basada en las visitas de cada vehículo. Se separó la selección del destino de la planificación de la ruta para que ambos selectores compartieran el controlador. La navegación incorporó la sincronización de los actores antes de planificar, la búsqueda de retornos y la confirmación de parada y alineación al llegar. [Arquitectura del simulador](../referencia/arquitectura.md)

## Registro de la movilidad

El registro inicial seguía cada intento mediante sus eventos y su trayectoria. La observación por paso añadió las esperas y los cambios de fase. Los identificadores de corrida, vehículo y viaje permiten relacionar esas observaciones con los intentos y las visitas que se incorporan al historial. [Registros y métricas](../referencia/datos-y-metricas.md)

## Ejecución de campañas

El ejecutor de campañas incorporó la coordinación de varias flotas y selectores. Para poder revisar una ejecución, guarda los parámetros efectivos de cada caso, una copia de las entradas y el código empleado, y las rutas de los registros que necesita el análisis. [Ejecutar una campaña](../guias/manual.md#ejecutar-una-campaña)
