# proyecto.md

# Contexto general del proyecto

Este archivo proporciona el contexto funcional, académico y técnico del proyecto para que Codex pueda comprender qué se está desarrollando, por qué se está desarrollando, cuáles son los objetivos que no deben modificarse y cómo debe evolucionar la implementación en CARLA.

Codex debe utilizar este documento junto con `instrucciones.md`.

- `proyecto.md` explica **qué es el proyecto, qué debe lograr y cómo se evaluará**.
- `instrucciones.md` explica **cómo organizar e implementar técnicamente el repositorio**.

Si existe una duda entre una decisión de implementación y los objetivos académicos del proyecto, los objetivos y el alcance descritos en este archivo tienen prioridad.

---

# 1. Nombre del proyecto

**Desarrollo de un generador de tráfico urbano en CARLA mediante un modelo estocástico de elección de destinos y planificación de rutas para análisis de movilidad en escenarios simulados.**

---

# 2. Plataforma principal

El proyecto utiliza:

```text
CARLA Simulator 0.9.15
Python API de CARLA
Traffic Manager
Python
CSV/JSON para configuración y almacenamiento
```

CARLA se utiliza como plataforma de simulación urbana y generación de datos.

CARLA no representa por sí solo el modelo de movilidad que se desea estudiar. La lógica de selección de destinos, clasificación de destinos, generación de viajes, planificación de rutas, control de semillas, registro de datos y análisis comparativo forman parte del software desarrollado en este proyecto.

---

# 3. Idea central del proyecto

El proyecto no consiste únicamente en crear vehículos dentro de CARLA y activar `autopilot`.

El objetivo es construir un **generador de viajes vehiculares** que permita que los actores tengan:

```text
origen
→ destino
→ ruta
→ viaje
→ resultado medible
```

El generador debe permitir representar movilidad sintética dentro de un mapa urbano de CARLA.

La lógica general será:

```text
Definición del ODD
        ↓
Configuración del escenario
        ↓
Definición de zonas origen-destino
        ↓
Modelo de elección de destinos
        ↓
Generación de vehículos
        ↓
Planificación de rutas
        ↓
Control vehicular mediante CARLA
        ↓
Ejecución de la corrida
        ↓
Registro de datos
        ↓
Cálculo de métricas
        ↓
Comparación de escenarios
```

---

# 4. Problema que aborda el proyecto

Una simulación de tráfico en la que los vehículos simplemente aparecen y circulan utilizando decisiones aleatorias del controlador puede ser útil para pruebas iniciales, pero dificulta analizar patrones de movilidad con una finalidad de viaje definida.

Este proyecto busca incorporar una lógica mínima de movilidad mediante:

- zonas de origen;
- zonas de destino;
- categorías de destino;
- destinos frecuentes y no frecuentes;
- probabilidades de elección;
- niveles de demanda;
- planificación de rutas;
- semillas de aleatoriedad;
- viajes medibles.

El propósito no es reproducir exactamente la movilidad de una ciudad real.

El propósito es generar **tráfico urbano sintético, controlado, reproducible y medible dentro de un ODD definido**.

---

# 5. Objetivos académicos

## 5.1. Objetivo general

> Desarrollar un generador de tráfico urbano en CARLA, basado en un modelo estocástico de elección de destinos y planificación de rutas dentro de un dominio operacional definido (ODD), capaz de producir corridas reproducibles y datos sintéticos útiles para el análisis preliminar de movilidad en escenarios urbanos simulados.

Este objetivo no debe ser modificado por Codex.

---

## 5.2. Objetivos específicos

### Objetivo específico 1

> Caracterizar el ODD mediante la delimitación formal de condiciones ambientales, infraestructurales y operacionales del escenario de simulación, con un modelo probabilístico de movilidad basado en destinos frecuentes y no frecuentes, tres categorías de destino y dos niveles de demanda de tráfico.

### Objetivo específico 2

> Implementar el modelo propuesto en CARLA mediante la Python API y los módulos básicos de gestión de tráfico, de manera que el escenario soporte agentes vehiculares simultáneos.

### Objetivo específico 3

> Comparar el comportamiento del generador contra un escenario base de asignación aleatoria mediante cuatro métricas: distribución de destinos, tiempo promedio de viaje, velocidad media y tasa de incidentes o invasiones de carril.

Estos tres objetivos son restricciones académicas del proyecto y no deben cambiarse aunque durante el desarrollo se encuentren alternativas técnicas diferentes.

---

# 6. Naturaleza del estudio

El protocolo define el trabajo como:

```text
aplicado
experimental
cuantitativo
basado en simulación computacional
```

El proyecto debe permitir ejecutar experimentos comparables y repetir corridas bajo configuraciones controladas.

---

# 7. Alcance del proyecto

El proyecto sí busca:

- desarrollar un generador de tráfico urbano;
- trabajar dentro de CARLA;
- utilizar múltiples agentes vehiculares;
- definir un ODD;
- definir zonas origen-destino;
- elegir destinos probabilísticamente;
- generar rutas;
- controlar vehículos mediante herramientas de CARLA;
- producir datos sintéticos;
- ejecutar corridas reproducibles;
- comparar dos modelos de asignación de destinos;
- calcular métricas descriptivas de movilidad;
- generar tablas y gráficas para interpretar los resultados.

El proyecto no busca:

- desarrollar un vehículo autónomo completo;
- entrenar una red neuronal para conducción autónoma;
- implementar percepción mediante visión artificial como objetivo principal;
- validar movilidad real de una ciudad específica;
- reproducir exactamente la conducta humana;
- construir una plataforma universal de simulación de tráfico;
- reemplazar herramientas especializadas de tráfico como SUMO, Vissim o Aimsun;
- afirmar que los resultados de CARLA equivalen automáticamente a tráfico real.

---

# 8. Dominio operacional definido — ODD

El ODD delimita las condiciones bajo las cuales se considera válido el funcionamiento del generador.

Debe contener, como mínimo, condiciones:

## 8.1. Ambientales

Ejemplos:

```text
clima permitido
iluminación
visibilidad
ausencia de fenómenos extremos
condiciones meteorológicas utilizadas
```

## 8.2. Infraestructurales

Ejemplos:

```text
mapa utilizado
vías habilitadas
carriles
intersecciones
semáforos
señalización
geometría vial
conectividad entre zonas
```

## 8.3. Operacionales

Ejemplos:

```text
cantidad de vehículos
niveles de demanda
rango de velocidades
duración de corrida
tipos de actores
zonas habilitadas
reglas generales de circulación
criterios de llegada
criterios de timeout
```

## 8.4. Condiciones experimentales

Deben registrarse aparte de las condiciones viales del ODD:

```text
versión de CARLA
modo síncrono
fixed_delta_seconds
semilla
modo rendering/no-rendering
puerto de CARLA
puerto de Traffic Manager
configuración del Traffic Manager
```

Estas condiciones son fundamentales para la reproducibilidad.

---

# 9. Metodología establecida en el protocolo

La metodología académica del proyecto se divide de la siguiente manera.

---

## 9.1. Definición de condiciones de operación

Se establecen las condiciones ambientales, infraestructurales y operacionales bajo las cuales funciona el generador.

Se consideran:

```text
mapa urbano
zonas habilitadas
número de vehículos
condiciones ambientales
iluminación
rango de velocidades
duración de corrida
restricciones del escenario
```

---

## 9.2. Configuración del entorno de simulación

Se prepara CARLA de acuerdo con las condiciones establecidas.

Esto incluye:

```text
cargar mapa
configurar parámetros de simulación
habilitar componentes de circulación
establecer modo de ejecución
permitir repetición de escenarios
```

---

## 9.3. Definición de zonas de origen y destino

El mapa se divide en zonas o puntos de interés.

Las zonas deben considerar:

```text
estructura vial
conectividad
distribución espacial
spawn points
waypoints
accesibilidad por carretera
```

El objetivo es que los vehículos no circulen indefinidamente sin una finalidad de viaje.

---

## 9.4. Diseño del modelo estocástico

Cada destino o zona recibe una probabilidad de elección.

El modelo debe permitir:

```text
destinos con diferentes probabilidades
destinos frecuentes
destinos no frecuentes
tres categorías de destino
semillas de aleatoriedad
variabilidad controlada
corridas reproducibles
```

El protocolo plantea una lógica general de:

```text
80 % de viajes hacia destinos de rutina
20 % de viajes hacia destinos de exploración
```

Esta proporción debe mantenerse configurable y no quedar codificada rígidamente en múltiples archivos.

---

## 9.5. Planificación y asignación de rutas

Una vez definidos origen y destino:

```text
origen
→ planificación
→ ruta válida
→ destino
```

Cada vehículo debe contar con una ruta definida.

El proyecto debe evitar depender exclusivamente de las decisiones aleatorias que Traffic Manager realiza por defecto en las intersecciones.

La planificación de rutas debe integrarse con las herramientas de navegación y control disponibles en CARLA.

---

## 9.6. Implementación del generador

La implementación se realiza mediante Python y la API de CARLA.

Debe incluir progresivamente:

```text
creación de vehículos
asignación de origen
selección de destino
planificación de ruta
activación del control vehicular
ejecución de corridas
parámetros configurables
```

Parámetros que deben poder configurarse:

```text
cantidad de vehículos
duración
semilla
mapa
nivel de demanda
distribución de destinos
Traffic Manager
modo de simulación
```

---

## 9.7. Registro de datos por corrida

Cada simulación debe producir datos estructurados.

Variables previstas en el protocolo:

```text
identificador del vehículo
origen asignado
destino seleccionado
tiempo de salida
tiempo de llegada
distancia recorrida
velocidad media
estado final del viaje
colisiones
viajes incompletos
```

El proyecto puede registrar variables adicionales cuando sean útiles, siempre que no sustituyan las métricas obligatorias.

---

## 9.8. Ejecución de escenarios de prueba

Se deben ejecutar dos configuraciones principales:

```text
Escenario A:
asignación aleatoria simple

Escenario B:
modelo estocástico propuesto
```

Las corridas deben repetirse con parámetros y semillas controladas.

---

## 9.9. Procesamiento y análisis de datos

El análisis contempla:

```text
viajes completados
tiempo promedio de viaje
velocidad media
distancia recorrida
distribución de destinos
concentración de viajes
incidencias
```

Las cuatro métricas obligatorias del objetivo específico 3 son:

```text
1. distribución de destinos
2. tiempo promedio de viaje
3. velocidad media
4. tasa de incidentes o invasiones de carril
```

---

## 9.10. Integración del producto final

El producto final debe integrar:

```text
generador de tráfico
scripts de configuración
scripts de ejecución
ODD documentado
escenarios de prueba
datos sintéticos
resultados descriptivos
resultados visuales
```

---

# 10. Rol de CARLA dentro del proyecto

CARLA es la plataforma que ejecuta el escenario.

Debe pensarse conceptualmente así:

```text
CARLA
│
├── mundo simulado
├── mapa
├── red vial
├── actores
├── física
├── sensores
├── semáforos
├── Traffic Manager
└── Python API
```

El código del proyecto agrega:

```text
Generador desarrollado
│
├── ODD
├── zonas
├── demanda
├── elección de destinos
├── frecuencias
├── probabilidades
├── semillas
├── rutas
├── viajes
├── logging
├── métricas
└── comparación experimental
```

CARLA no debe confundirse con el generador propuesto.

---

# 11. Conceptos importantes de CARLA

## 11.1. Actor

Un actor es una entidad existente dentro del mundo de CARLA.

Ejemplos:

```text
vehículo
peatón
sensor
semáforo
```

---

## 11.2. Blueprint

Un blueprint es la plantilla utilizada para crear un actor.

Para un vehículo define aspectos como:

```text
modelo
tipo
atributos
color
cantidad de ruedas
role_name
```

La lógica general es:

```text
Blueprint
→ spawn
→ Actor
```

---

## 11.3. Spawn point

Representa una posición y orientación recomendada para crear un actor dentro del mapa.

Los spawn points pueden utilizarse inicialmente para:

```text
crear vehículos
definir orígenes
agrupar zonas
relacionar puntos de interés
```

No debe suponerse que todos los spawn points estarán disponibles durante una corrida.

---

## 11.4. Waypoint

Un waypoint representa una posición sobre la red vial.

Los waypoints serán importantes para:

```text
conectividad
rutas
seguimiento de carril
identificación de road/lane
validación origen-destino
```

---

## 11.5. Traffic Manager

Traffic Manager debe entenderse como el sistema que administra el comportamiento básico de múltiples vehículos.

Su responsabilidad principal es:

```text
cómo circula el vehículo
```

El generador desarrollado debe encargarse de:

```text
a dónde va el vehículo
```

Separación conceptual:

```text
Modelo estocástico
        ↓
elige destino
        ↓
Planificador
        ↓
genera ruta
        ↓
Traffic Manager / controlador
        ↓
ejecuta circulación
```

Traffic Manager puede utilizarse para:

```text
autopilot
velocidad
distancia de seguimiento
cambio de carril
interacción con vehículos
interacción con semáforos
control básico de circulación
```

---

# 12. Estrategia de ejecución de CARLA

Para este proyecto se recomienda utilizar modo síncrono como base experimental.

Configuración conceptual:

```text
synchronous_mode = True
fixed_delta_seconds = valor fijo
```

El cliente debe controlar el avance mediante ticks.

Esto facilita:

```text
reproducibilidad
logging
medición temporal
comparación entre corridas
control experimental
```

---

## 12.1. Renderizado

Durante desarrollo:

```text
modo síncrono
+
renderizado visible
```

Esto permite inspeccionar visualmente problemas.

Durante múltiples corridas:

```text
modo síncrono
+
no-rendering
```

El modo no-rendering no reemplaza al modo síncrono.

Son configuraciones diferentes y pueden utilizarse simultáneamente.

---

# 13. Primera prioridad técnica

Antes de implementar el modelo completo, el proyecto debe conseguir una simulación base estable.

La primera fase debe poder:

```text
conectarse a CARLA
cargar mapa
activar modo síncrono
configurar Traffic Manager
crear vehículos
hacer que circulen
evitar caos inmediato
registrar velocidad
detectar vehículos detenidos
limpiar actores
restaurar configuración
```

El script inicial recomendado es:

```text
scripts/stable_traffic.py
```

No avanzar directamente al generador final mientras esta base no sea razonablemente estable.

---

# 14. Problemas observados durante pruebas iniciales

En pruebas previas con una implementación básica:

```text
50 vehículos
autopilot
Traffic Manager
time.sleep()
```

se observaron comportamientos como:

```text
colisiones
bloqueos
vehículos incapaces de continuar
movimientos oscilantes o inestables
```

Por ello, el proyecto debe priorizar inicialmente:

```text
modo síncrono
paso temporal fijo
menor número de vehículos
blueprints vehiculares controlados
mayor distancia de seguimiento
velocidad conservadora
cambio de carril controlado
limpieza de actores
```

No introducir complejidad adicional hasta estabilizar esta capa.

---

# 15. Estructura lógica del generador

La arquitectura conceptual debe mantenerse separada por responsabilidades.

```text
Configuración
      ↓
ODD
      ↓
Zonas
      ↓
Demanda
      ↓
Modelo estocástico
      ↓
Selección de destino
      ↓
Planificador de rutas
      ↓
Vehicle Manager
      ↓
Traffic Manager
      ↓
Simulación
      ↓
Logging
      ↓
Análisis
```

---

# 16. Módulos conceptuales esperados

## 16.1. Configuración

Responsabilidad:

```text
centralizar parámetros del experimento
```

Ejemplos:

```text
mapa
clima
duración
número de vehículos
demanda
semilla
fixed_delta_seconds
rendering/no-rendering
categorías
probabilidades
Traffic Manager
```

No dispersar parámetros constantes por múltiples scripts.

---

## 16.2. Módulo ODD

Responsabilidad:

```text
validar las condiciones bajo las cuales puede ejecutarse un escenario
```

Debe conocer:

```text
mapas permitidos
zonas permitidas
condiciones ambientales
límites operacionales
restricciones de actores
niveles de demanda
```

---

## 16.3. Módulo de zonas

Responsabilidad:

```text
transformar puntos físicos del mapa en zonas lógicas de movilidad
```

Debe poder:

```text
cargar spawn points
cargar waypoints
agrupar puntos
asignar identificadores
asignar categorías
validar conectividad
seleccionar puntos internos
```

---

## 16.4. Módulo de demanda

Responsabilidad:

```text
representar diferentes cantidades o intensidades de viajes
```

El objetivo académico requiere dos niveles de demanda.

Ejemplo conceptual:

```text
low
high
```

Los valores numéricos exactos se decidirán experimentalmente y deberán ser configurables.

No codificar como verdad académica valores temporales usados durante pruebas.

---

## 16.5. Módulo estocástico

Responsabilidad:

```text
seleccionar destinos de acuerdo con una distribución controlada
```

Proceso conceptual:

```text
vehículo
    ↓
seleccionar frecuente/no frecuente
    ↓
seleccionar categoría
    ↓
seleccionar destino
```

Debe controlar semillas.

Debe admitir al menos:

```text
stochastic_model
random_baseline
```

---

## 16.6. Módulo de rutas

Responsabilidad:

```text
convertir origen + destino en una ruta válida
```

Debe:

```text
validar origen
validar destino
validar conectividad
calcular ruta
rechazar rutas imposibles
entregar ruta al controlador correspondiente
```

---

## 16.7. Módulo de vehículos

Responsabilidad:

```text
administrar el ciclo de vida de los actores vehiculares
```

Debe poder:

```text
seleccionar blueprint
crear vehículo
asignar identificador lógico
asignar origen
asignar destino
asignar ruta
activar controlador
detectar llegada
destruir actor
```

---

## 16.8. Módulo de sensores/eventos

Se implementará cuando la simulación base sea estable.

Debe permitir registrar, como mínimo:

```text
colisiones
invasiones de carril
```

No utilizar una invasión de carril como sinónimo automático de accidente.

Cada tipo de evento debe registrarse independientemente.

---

## 16.9. Módulo de simulación

Responsabilidad:

```text
orquestar una corrida completa
```

Debe:

```text
inicializar escenario
crear actores
ejecutar ticks
actualizar estados
detectar llegadas
detectar timeouts
registrar datos
cerrar corrida
limpiar actores
restaurar configuración
```

---

## 16.10. Módulo de logging

Responsabilidad:

```text
guardar datos sin contaminar la lógica del modelo
```

Debe separar:

```text
configuración
viajes
trayectorias
eventos
métricas
```

---

## 16.11. Módulo de análisis

Responsabilidad:

```text
procesar datos después de la simulación
```

Debe calcular métricas y generar posteriormente:

```text
tablas
resúmenes
gráficas
comparaciones
```

El simulador no debe asumir directamente que un escenario es mejor que otro.

El análisis debe reportar los resultados observados.

---

# 17. Datos dummy

El proyecto utilizará inicialmente datos sintéticos/dummy para definir posibles destinos y probabilidades.

Estos datos dummy no representan viajes observados.

Representan la **configuración del modelo**.

Ejemplo:

```text
destination_id
zone_id
category
frequency_class
weight
```

---

# 18. Separación entre datos de entrada y resultados

Mantener estrictamente:

```text
data/input/
```

para configuración y:

```text
data/output/
```

para resultados.

Ejemplo:

```text
data/input/destinations_config.csv
data/input/zones_config.csv
data/input/demand_profiles.csv
```

vs.

```text
data/output/run_xxx/trips_log.csv
data/output/run_xxx/trajectory_log.csv
data/output/run_xxx/events_log.csv
data/output/run_xxx/metrics_summary.csv
```

No escribir resultados de simulación dentro del mismo archivo que controla probabilidades.

---

# 19. Filosofía de los datos dummy

No generar inicialmente un perfil individual fijo para cada carro.

La configuración debe describir:

```text
qué destinos existen
qué categoría tienen
qué clase de frecuencia tienen
qué peso tienen
```

Posteriormente, cada vehículo selecciona probabilísticamente un destino.

Eso genera datos por carro.

Separación conceptual:

```text
destinations_config.csv
        ↓
modelo probabilístico
        ↓
vehículo selecciona destino
        ↓
trips_log.csv
```

---

# 20. Categorías de destino

El objetivo académico establece exactamente:

```text
tres categorías de destino
```

Codex no debe cambiar esta cantidad de forma definitiva.

Los nombres exactos de las tres categorías deben mantenerse configurables mientras se define la clasificación final.

Pueden utilizarse categorías provisionales durante el desarrollo, pero deben quedar claramente marcadas como datos de prueba.

No agregar una cuarta categoría definitiva sin decisión explícita del responsable del proyecto.

---

# 21. Destinos frecuentes y no frecuentes

La clasificación debe permitir:

```text
frecuente
no_frecuente
```

No significa necesariamente que una categoría completa sea frecuente.

Idealmente:

```text
categoría
    ├── destinos frecuentes
    └── destinos no frecuentes
```

Esto permite analizar:

```text
distribución por categoría
distribución por destino específico
distribución por clase de frecuencia
```

---

# 22. Dos niveles de demanda

El objetivo específico 1 exige exactamente:

```text
dos niveles de demanda
```

Inicialmente pueden denominarse:

```text
low
high
```

Los valores de cantidad de vehículos o tasa de generación deberán determinarse mediante pruebas.

No asumir que:

```text
20 vehículos = baja
70 vehículos = alta
```

son valores académicos definitivos.

Son posibles configuraciones experimentales y deben poder modificarse.

---

# 23. Modelo estocástico

Sea un conjunto de destinos:

```text
D = {d1, d2, ..., dm}
```

El modelo propuesto asigna:

```text
P(D = dj) = pj
```

con:

```text
sum(pj) = 1
```

Los pesos pueden almacenarse en configuración y normalizarse antes de realizar la selección.

El modelo debe ser reproducible mediante una semilla.

---

# 24. Lógica 80/20

El protocolo describe una lógica general:

```text
80 % rutina
20 % exploración
```

Puede representarse como:

```text
P(routine) = 0.80
P(exploration) = 0.20
```

Después puede realizarse otra selección dentro del grupo correspondiente.

Ejemplo conceptual:

```text
routine/exploration
        ↓
category
        ↓
destination
```

La implementación debe permitir cambiar estas probabilidades desde configuración.

---

# 25. Escenario base aleatorio

El escenario base es una referencia experimental.

No debe utilizar los mismos pesos del modelo propuesto.

Conceptualmente:

```text
random_baseline
```

utiliza una elección uniforme:

```text
P(D = dj) = 1 / m
```

para todos los destinos elegibles.

---

# 26. Modelo estocástico propuesto

Conceptualmente:

```text
stochastic_model
```

utiliza:

```text
P(D = dj) = pj
```

con pesos definidos previamente.

Los pesos reflejan:

```text
frecuencia
categoría
configuración del escenario
```

---

# 27. Comparación experimental

La comparación del objetivo específico 3 debe aislar la lógica de elección de destino.

Se deben mantener constantes, cuando sea posible:

```text
mapa
clima
iluminación
duración
número de vehículos
nivel de demanda
parámetros de Traffic Manager
fixed_delta_seconds
criterios de llegada
criterios de timeout
tipos de vehículos
método de logging
```

La diferencia experimental central debe ser:

```text
random_baseline
vs.
stochastic_model
```

---

# 28. Qué busca demostrar la comparación

La comparación no busca demostrar automáticamente que el modelo estocástico:

```text
reduce congestión
aumenta velocidad
reduce accidentes
```

No se debe programar ni redactar el análisis suponiendo esos resultados.

La comparación busca responder:

```text
¿Qué patrones produce cada lógica de destinos?
```

y observar sus efectos sobre:

```text
distribución de destinos
tiempo de viaje
velocidad media
incidencias
```

El modelo estocástico incluso podría producir:

```text
mayor concentración
mayores tiempos
menor velocidad
```

si dirige más tráfico hacia zonas comunes.

Eso seguiría siendo un resultado válido.

---

# 29. Métrica 1 — distribución de destinos

Para cada destino:

```text
P(dj) = nj / N
```

donde:

```text
nj = número de viajes hacia el destino j
N  = número total de viajes considerados
```

Debe ser posible comparar:

```text
distribución esperada
distribución observada
base aleatoria
modelo estocástico
```

También puede analizarse por categoría.

---

# 30. Métrica 2 — tiempo promedio de viaje

Por viaje:

```text
travel_time = arrival_time - departure_time
```

Promedio:

```text
avg_travel_time =
sum(travel_time_completed) / completed_trips
```

Los viajes incompletos deben conservarse como información y no desaparecer silenciosamente del dataset.

---

# 31. Métrica 3 — velocidad media

Preferentemente calcular por viaje:

```text
avg_speed = traveled_distance / travel_time
```

También pueden almacenarse velocidades instantáneas.

Es importante distinguir:

```text
velocidad instantánea
velocidad media temporal
velocidad media por viaje
velocidad media agregada
```

La definición usada en el resultado final debe quedar documentada.

---

# 32. Métrica 4 — incidentes o invasiones de carril

Deben registrarse separadamente:

```text
collision
lane_invasion
```

Posibles normalizaciones:

```text
incidentes / viajes
incidentes / viajes completados
incidentes / distancia recorrida
```

La normalización definitiva debe quedar documentada.

No contar repetidamente un mismo evento debido a callbacks duplicados.

---

# 33. Métricas complementarias

Aunque no forman parte de las cuatro métricas obligatorias, pueden resultar útiles:

```text
viajes completados
viajes incompletos
tasa de finalización
distancia recorrida
cantidad de vehículos activos
vehículos detenidos
concentración de destinos
flujo aproximado
densidad aproximada
```

Estas métricas no deben reemplazar a las cuatro métricas obligatorias.

---

# 34. Teoría del flujo de tráfico relacionada

El proyecto puede interpretar resultados utilizando variables microscópicas:

```text
posición
trayectoria
velocidad
aceleración
separación
headway
```

y macroscópicas:

```text
flujo
densidad
velocidad media
ocupación
congestión
```

Relación fundamental:

```text
q = k * u
```

donde:

```text
q = flujo
k = densidad
u = velocidad media espacial
```

Estas variables pueden utilizarse como análisis complementario cuando los datos disponibles sean suficientes.

---

# 35. Datos por viaje

El dataset de viajes debe poder contener al menos:

```text
run_id
scenario
seed
vehicle_id
origin_zone
destination_id
destination_category
frequency_class
departure_time
arrival_time
travel_time
distance_m
avg_speed_kmh
status
```

Estados posibles sugeridos:

```text
completed
timeout
spawn_failed
route_failed
blocked
destroyed
```

No confundir fallos técnicos con viajes incompletos por comportamiento del tráfico.

---

# 36. Datos de trayectoria

Cuando sea necesario:

```text
run_id
frame
simulation_time
vehicle_id
x
y
z
speed_kmh
road_id
lane_id
```

No es obligatorio registrar todos los actores en todos los frames desde la primera versión.

Debe evaluarse costo de almacenamiento y frecuencia de muestreo.

---

# 37. Datos de eventos

Archivo conceptual:

```text
events_log.csv
```

Campos:

```text
run_id
frame
simulation_time
vehicle_id
event_type
other_actor_id
x
y
z
details
```

Tipos iniciales:

```text
collision
lane_invasion
```

---

# 38. Configuración por corrida

Toda corrida debe dejar evidencia de su configuración.

Ejemplo:

```text
run_config.json
```

Debe incluir:

```text
run_id
scenario
CARLA version
map
weather
duration
seed
vehicle count
demand level
fixed_delta_seconds
rendering mode
Traffic Manager settings
destination configuration
ODD configuration
```

Una corrida sin configuración asociada pierde trazabilidad.

---

# 39. Identificador de corrida

Cada ejecución experimental debe tener un `run_id`.

Ejemplo:

```text
random_low_seed_0042
stochastic_low_seed_0042
random_high_seed_0042
stochastic_high_seed_0042
```

Esto facilita comparar pares equivalentes.

No es obligatorio utilizar exactamente ese formato, pero debe ser claro y único.

---

# 40. Reproducibilidad

La reproducibilidad es fundamental.

Debe controlarse:

```text
random.seed(...)
NumPy seed si se utiliza NumPy
Traffic Manager seed
configuración del escenario
orden de generación
modo síncrono
fixed_delta_seconds
```

No asumir que una sola semilla garantiza automáticamente reproducibilidad absoluta.

Registrar siempre la configuración.

---

# 41. Múltiples semillas

No evaluar el modelo únicamente mediante una corrida.

La arquitectura debe permitir posteriormente:

```text
seed 1
seed 2
seed 3
...
```

y obtener resultados agregados.

El número definitivo de repeticiones se decidirá durante el diseño experimental.

---

# 42. Simulación estable antes de volumen alto

El proyecto requiere múltiples agentes simultáneos, pero no debe buscar inmediatamente el máximo número posible.

Proceso recomendado:

```text
10 vehículos
↓
20 vehículos
↓
30 vehículos
↓
incrementos controlados
↓
nivel de demanda definido
```

Antes de aumentar volumen, observar:

```text
colisiones
bloqueos
FPS/tick performance
vehículos detenidos
timeouts
comportamiento de intersecciones
```

---

# 43. Traffic Manager durante la fase inicial

Utilizar una configuración conservadora mientras se valida estabilidad.

Ejemplos configurables:

```text
distance_to_leading_vehicle
vehicle_percentage_speed_difference
auto_lane_change
ignore_lights_percentage
ignore_signs_percentage
ignore_vehicles_percentage
ignore_walkers_percentage
```

Estos parámetros no deben quedar dispersos en el código.

Centralizarlos en configuración.

---

# 44. Cambios de carril

Durante pruebas iniciales puede utilizarse:

```text
auto_lane_change = False
```

para reducir variabilidad.

Esto es una decisión de estabilización, no necesariamente una característica definitiva del ODD.

Si posteriormente se habilita, debe registrarse en la configuración del experimento.

---

# 45. Peatones

Los peatones no son el foco principal del proyecto.

No introducir peatones durante las primeras fases salvo necesidad explícita.

Agregar peatones modifica:

```text
interacciones
tiempos
incidencias
carga computacional
```

y por tanto debe considerarse una modificación experimental relevante.

---

# 46. Sensores visuales

Cámaras, LiDAR y otros sensores de percepción no son necesarios para cumplir los objetivos principales.

No incorporarlos inicialmente salvo que exista una necesidad específica.

Los sensores/eventos prioritarios son:

```text
collision sensor
lane invasion sensor
```

---

# 47. Google Maps y datos externos

La implementación inicial no debe depender de Google Maps.

El proyecto trabaja con mapas internos de CARLA.

Inicialmente, los destinos y pesos se definirán mediante datos sintéticos controlados.

Si posteriormente se utilizan datos externos, deben tratarse como una extensión explícita y no como dependencia central del generador.

---

# 48. Principio de no retroalimentación accidental

Los archivos resultantes de una corrida no deben modificar automáticamente las probabilidades del siguiente experimento.

Correcto:

```text
configuración fija
→ corrida
→ resultados
→ análisis
```

No hacer:

```text
configuración
→ corrida
→ resultados
→ modificar automáticamente pesos
→ nueva corrida
```

Eso transformaría el modelo en un sistema adaptativo y modificaría el alcance del proyecto.

---

# 49. No sesgar los experimentos

Las probabilidades y reglas deben definirse antes de ejecutar los experimentos que serán comparados.

No ajustar probabilidades con el objetivo de producir:

```text
menor tiempo
mayor velocidad
menos incidentes
```

El sistema debe registrar los resultados aunque contradigan la hipótesis esperada.

---

# 50. Planificación de rutas

La arquitectura debe poder evolucionar hacia:

```text
origin waypoint
        ↓
route planner
        ↓
ordered waypoints / route
        ↓
controller
        ↓
destination
```

Debe existir validación para evitar:

```text
rutas inexistentes
origen y destino incompatibles
destino no accesible
rutas vacías
```

---

# 51. Llegada al destino

Debe existir una definición explícita de viaje completado.

Ejemplo conceptual:

```text
distance(vehicle_location, destination_location) <= arrival_threshold
```

El umbral debe ser configurable.

No comparar directamente igualdad exacta de coordenadas.

---

# 52. Timeout

Cada viaje necesita protección frente a vehículos que nunca llegan.

Debe existir un límite configurable:

```text
max_trip_time
```

Si se excede:

```text
status = timeout
```

El vehículo puede destruirse de forma controlada después de registrar el estado.

---

# 53. Distancia recorrida

Puede estimarse acumulando desplazamiento:

```text
distance += distance(current_location, previous_location)
```

Debe evitarse sumar saltos artificiales después de teleportación, respawn o destrucción.

---

# 54. Estado del viaje

Cada vehículo debe contar con una máquina de estados simple.

Ejemplo:

```text
CREATED
↓
SPAWNED
↓
ROUTE_ASSIGNED
↓
RUNNING
├── COMPLETED
├── TIMEOUT
├── BLOCKED
├── COLLISION_END
└── FAILED
```

No es obligatorio implementar una clase formal de máquina de estados desde la primera versión, pero la lógica debe ser consistente.

---

# 55. Flujo esperado de una corrida

```text
1. cargar configuración
2. validar configuración
3. conectar con CARLA
4. cargar/configurar mapa
5. activar modo síncrono
6. configurar Traffic Manager
7. inicializar semilla
8. cargar zonas
9. cargar destinos
10. inicializar logger
11. generar vehículos
12. asignar orígenes
13. seleccionar destinos
14. calcular rutas
15. iniciar circulación
16. ejecutar ticks
17. actualizar estados
18. registrar eventos
19. detectar llegadas
20. detectar timeouts
21. cerrar corrida
22. destruir actores
23. restaurar world settings
24. generar resumen
```

---

# 56. Flujo del escenario aleatorio

```text
vehículo
↓
origen válido
↓
selección uniforme de destino
↓
ruta
↓
viaje
↓
logging
```

---

# 57. Flujo del escenario estocástico

```text
vehículo
↓
origen válido
↓
rutina/exploración
↓
categoría
↓
destino ponderado
↓
ruta
↓
viaje
↓
logging
```

---

# 58. Comparación entre escenarios

Idealmente ejecutar pares:

```text
same ODD
same map
same demand
same simulation duration
same seed
same Traffic Manager configuration
```

cambiando:

```text
destination_selection_strategy
```

Ejemplo:

```text
random_baseline
stochastic_model
```

---

# 59. Estructura general del repositorio

La estructura técnica detallada está en `instrucciones.md`.

La separación conceptual esperada es:

```text
config/
data/input/
data/output/
scripts/
src/
tests/
docs/
```

No concentrar toda la implementación en un único script.

---

# 60. Scripts iniciales

Los primeros scripts pueden incluir:

```text
change_map.py
stable_traffic.py
generate_dummy_data.py
log_basic_metrics.py
run_experiment.py
```

No utilizar prefijos numéricos en los nombres de archivo.

---

# 61. Generador de datos dummy

Debe existir:

```text
scripts/generate_dummy_data.py
```

Su responsabilidad inicial es generar:

```text
zones_config.csv
destinations_config.csv
demand_profiles.csv
```

No debe ejecutar CARLA.

No debe crear logs de viajes.

No debe modificar resultados de corridas.

---

# 62. Configuración de zonas

Ejemplo conceptual:

```text
zone_id
zone_name
category
spawn_indices
description
```

Los índices de spawn utilizados durante desarrollo deben validarse contra el mapa activo.

No asumir que un conjunto de índices válido para Town03 es válido para otro mapa.

---

# 63. Configuración de destinos

Ejemplo conceptual:

```text
destination_id
zone_id
destination_name
category
frequency_class
weight
description
```

La suma de pesos debe validarse o normalizarse.

No continuar silenciosamente con probabilidades inválidas.

---

# 64. Perfil de demanda

Ejemplo conceptual:

```text
profile_id
vehicles
spawn_interval_seconds
routine_probability
exploration_probability
```

Solo dos perfiles deben considerarse parte definitiva del objetivo experimental.

Perfiles adicionales pueden existir para depuración, pero no deben confundirse con los dos niveles finales de demanda.

---

# 65. Resultado académico esperado por objetivo

## Objetivo específico 1

Debe producir evidencia de:

```text
ODD definido
condiciones ambientales
condiciones infraestructurales
condiciones operacionales
tres categorías
frecuentes/no frecuentes
dos niveles de demanda
modelo probabilístico documentado
```

---

## Objetivo específico 2

Debe producir evidencia de:

```text
modelo implementado en CARLA
Python API utilizada
vehículos simultáneos
selección de destinos
rutas
control de circulación
corridas funcionales
```

---

## Objetivo específico 3

Debe producir evidencia de:

```text
escenario random_baseline
escenario stochastic_model
corridas comparables
distribución de destinos
tiempo promedio de viaje
velocidad media
tasa de incidentes/invasiones
resultados descriptivos y visuales
```

---

# 66. Resultados esperados del trabajo final

El índice preliminar del protocolo contempla presentar:

```text
generador implementado
escenarios configurados
corridas ejecutadas
datos sintéticos generados
métricas obtenidas
visualización de resultados
```

La arquitectura del repositorio debe facilitar generar estos entregables.

---

# 67. Discusión esperada

La discusión académica deberá contemplar:

```text
interpretación de resultados
comparación modelo estocástico vs base
relación con estudios previos
limitaciones
mejoras futuras
```

Por ello el software debe conservar información suficiente para reconstruir qué ocurrió durante cada experimento.

---

# 68. Limitaciones que deben reconocerse

El proyecto parte de las siguientes limitaciones conceptuales:

```text
datos de destinos inicialmente sintéticos
mapas de CARLA, no una ciudad real
comportamiento vehicular determinado en parte por CARLA
parámetros del Traffic Manager configurables
capacidad computacional limitada
ODD restringido
resultados preliminares de movilidad
```

No redactar mensajes o documentación afirmando que el generador representa exactamente la movilidad urbana real.

---

# 69. Principio de trazabilidad

Toda decisión experimental relevante debe poder rastrearse.

Ejemplo:

```text
resultado
↓
run_id
↓
run_config.json
↓
scenario config
↓
destination config
↓
seed
↓
software version
```

Codex debe favorecer una arquitectura que permita esta trazabilidad.

---

# 70. Principio de separación de responsabilidades

Evitar archivos que simultáneamente:

```text
generen vehículos
seleccionen destinos
calculen rutas
registren CSV
calculen estadísticas
generen gráficas
```

Los scripts pueden orquestar módulos, pero la lógica debe separarse.

---

# 71. Principio de configuración externa

Parámetros experimentales importantes deben estar en:

```text
JSON
CSV
argumentos CLI
```

y no repetidos como constantes en diferentes archivos.

---

# 72. Principio de errores explícitos

Si ocurre:

```text
spawn fallido
destino inválido
ruta inexistente
actor destruido
archivo ausente
configuración inválida
```

el sistema debe:

```text
registrar
informar
continuar de forma segura cuando sea posible
```

No ocultar errores importantes.

---

# 73. Principio de limpieza

Todo script que cree actores debe garantizar su eliminación.

Usar bloques:

```python
try:
    ...
finally:
    ...
```

o mecanismos equivalentes.

También restaurar:

```text
world settings
Traffic Manager synchronous mode
```

cuando corresponda.

---

# 74. Principio de ejecución incremental

No construir todas las funcionalidades de una sola vez.

Orden recomendado:

```text
Fase A
conexión + mapa

Fase B
tráfico estable

Fase C
logging básico

Fase D
zonas

Fase E
datos dummy

Fase F
selección estocástica

Fase G
rutas

Fase H
viajes completos

Fase I
sensores/eventos

Fase J
escenario aleatorio

Fase K
automatización de corridas

Fase L
métricas

Fase M
gráficas y análisis
```

---

# 75. Estado actual del desarrollo

Al momento de crear este documento:

- CARLA 0.9.15 ya ha sido utilizado de forma básica.
- Se ha probado creación de vehículos mediante Python.
- Se ha utilizado `vehicle.set_autopilot(...)`.
- Se ha utilizado Traffic Manager de forma inicial.
- Se ha utilizado un script simple para cambiar mapas.
- Se observaron problemas de tráfico inestable al utilizar muchos vehículos sin suficiente control.
- Se decidió comenzar por una simulación estable.
- Se definió una arquitectura escalable.
- Se definió que los nombres de archivos no tendrán prefijos numéricos.
- Se planea utilizar datos dummy como configuración inicial de destinos.
- Todavía no se encuentra implementado el generador estocástico completo.
- Todavía no se encuentra implementada la comparación experimental final.
- Todavía no se encuentran implementadas todas las métricas finales.

---

# 76. Primera tarea actual de Codex

Codex debe enfocarse primero en:

```text
stable_traffic.py
change_map.py
generate_dummy_data.py
estructura de proyecto
configuración base
README
```

Validar que:

```text
CARLA se conecta
Town03 puede cargarse
modo síncrono funciona
Traffic Manager funciona
10–30 vehículos pueden probarse
actores se limpian
datos dummy pueden generarse
```

Después avanzar al logging básico.

---

# 77. Cosas que Codex no debe hacer todavía sin instrucción explícita

No introducir prematuramente:

```text
Google Maps API
machine learning
deep learning
reinforcement learning
ROS
ROS Bridge
Docker
base de datos externa
servicios cloud
microservicios
frontend web
dashboard
cámaras
LiDAR
peatones masivos
optimización avanzada
algoritmos adaptativos
```

Estas tecnologías pueden resultar interesantes, pero no son necesarias para cumplir los objetivos actuales.

---

# 78. Cosas que Codex no debe cambiar

No modificar:

```text
objetivo general
objetivos específicos
CARLA 0.9.15 como versión base
tres categorías de destino
dos niveles de demanda
comparación contra escenario aleatorio
cuatro métricas obligatorias
uso de un ODD
necesidad de corridas reproducibles
generación de datos sintéticos
```

Si una decisión técnica parece entrar en conflicto con alguno de estos elementos, Codex debe señalar el problema antes de modificar la arquitectura.

---

# 79. Qué significa que el generador sea verosímil

En este proyecto, verosímil no significa:

```text
idéntico al tráfico de Guatemala
calibrado con una ciudad real
validado contra una matriz OD real
```

Significa, dentro del alcance actual:

```text
viajes con finalidad
destinos explícitos
distribuciones no puramente uniformes
rutas válidas
patrones observables
configuración controlada
resultados reproducibles
métricas interpretables
```

---

# 80. Definición práctica del producto final

El producto final debe poder ejecutar conceptualmente:

```powershell
python run_experiment.py --scenario random_baseline --demand low --seed 42
python run_experiment.py --scenario stochastic_model --demand low --seed 42

python run_experiment.py --scenario random_baseline --demand high --seed 42
python run_experiment.py --scenario stochastic_model --demand high --seed 42
```

Los nombres y argumentos exactos pueden evolucionar.

El objetivo arquitectónico es llegar a una interfaz equivalente.

---

# 81. Resultado esperado por corrida

Cada corrida debe terminar con algo equivalente a:

```text
Run completed

scenario: stochastic_model
map: Town03
seed: 42
demand: low

vehicles generated: ...
completed trips: ...
incomplete trips: ...
average travel time: ...
average speed: ...
collisions: ...
lane invasions: ...

output:
data/output/<run_id>/
```

No es necesario implementar este resumen completo en la primera fase.

---

# 82. Resultado esperado del análisis comparativo

Posteriormente debe ser posible obtener algo conceptualmente similar a:

```text
Scenario comparison

Metric                     Random baseline     Stochastic model
----------------------------------------------------------------
Destination distribution   ...                 ...
Average travel time        ...                 ...
Average speed              ...                 ...
Incident rate              ...                 ...
```

El análisis debe apoyarse en múltiples corridas, no únicamente en una ejecución aislada.

---

# 83. Gráficas futuras

El sistema de análisis debe poder generar posteriormente:

```text
distribución de destinos por escenario
tiempo de viaje por escenario
velocidad media por escenario
incidentes por escenario
viajes completados/incompletos
concentración de destinos
series temporales cuando sean útiles
```

No generar gráficas antes de que los datos estén correctamente definidos y validados.

---

# 84. Marco teórico relacionado

El trabajo de graduación contempla desarrollar fundamentos sobre:

```text
modelado y simulación
modelos basados en agentes
variables microscópicas
variables macroscópicas
flujo vehicular
densidad
velocidad
capacidad
congestión
modelos estocásticos
movilidad urbana
redes viales
planificación de rutas
ODD
CARLA
datos sintéticos
métricas
análisis de tráfico
```

La implementación debe utilizar conceptos consistentes con esas definiciones.

---

# 85. Vocabulario del proyecto

Usar de forma consistente:

```text
ODD
corrida
escenario
agente vehicular
origen
destino
zona
categoría
destino frecuente
destino no frecuente
nivel de demanda
ruta
viaje
semilla
reproducibilidad
Traffic Manager
baseline aleatorio
modelo estocástico
datos sintéticos
métrica
incidencia
```

Evitar utilizar términos diferentes para el mismo concepto en distintos módulos.

---

# 86. Distinción importante: vehículo vs viaje

No asumir que:

```text
1 vehículo = 1 actor eterno
```

La unidad analítica principal será el viaje.

Un vehículo puede conceptualmente:

```text
ser creado
realizar un viaje
llegar
registrar el resultado
ser destruido
```

El diseño futuro podría reutilizar actores, pero el logging debe mantener identidad de viaje claramente definida.

---

# 87. Distinción importante: destino vs zona

Una zona puede contener uno o más destinos.

Conceptualmente:

```text
Zone
├── Destination A
├── Destination B
└── Destination C
```

No mezclar necesariamente ambos identificadores.

Esto permitirá análisis más detallados si se requiere.

---

# 88. Distinción importante: ruta vs trayectoria

```text
ruta:
camino planificado

trayectoria:
movimiento realmente ejecutado por el vehículo
```

El sistema puede registrar ambos cuando sea necesario.

---

# 89. Distinción importante: configuración vs observación

Configuración:

```text
weight = 0.25
```

Observación:

```text
observed_destination_share = 0.236
```

No son lo mismo.

El análisis debe poder comparar probabilidades esperadas con frecuencias observadas.

---

# 90. Distinción importante: semilla vs resultado

Una semilla permite reproducir una secuencia pseudoaleatoria, pero no es una métrica.

No utilizar:

```text
seed 42
```

como escenario distinto.

Escenarios son:

```text
random_baseline
stochastic_model
```

y las semillas son repeticiones/configuraciones experimentales.

---

# 91. Criterios de calidad del código

El proyecto debe favorecer:

```text
claridad
modularidad
configurabilidad
reproducibilidad
trazabilidad
robustez
limpieza
documentación
pruebas incrementales
```

Evitar sobreingeniería.

---

# 92. Pruebas recomendadas

A medida que se desarrollen módulos, crear pruebas para lógica independiente de CARLA.

Ejemplos:

```text
probabilidades suman 1
selección reproducible con semilla
CSV válido
zona existente
destination_id único
route request válida
configuración requerida presente
```

Separar pruebas unitarias de pruebas que requieren un servidor CARLA activo.

---

# 93. Dependencia del servidor CARLA

Los módulos puramente lógicos no deberían necesitar que CARLA esté ejecutándose.

Ejemplos que pueden probarse sin CARLA:

```text
stochastic_model
config loader
dummy data generator
metrics
CSV validation
```

Ejemplos que necesitan CARLA:

```text
vehicle_manager
route planner integrado
sensors
simulation runner
world settings
```

---

# 94. Manejo de configuración por mapa

No asumir que:

```text
zones_config.csv
```

es universal para todos los mapas.

Las zonas dependen de:

```text
mapa
spawn points
topología
conectividad
```

Por ello puede evolucionarse posteriormente a:

```text
data/input/Town03/zones_config.csv
data/input/Town03/destinations_config.csv
```

si resulta útil.

No realizar esta reorganización prematuramente si todavía se trabaja únicamente con un mapa.

---

# 95. Mapa inicial

Durante estabilización se recomienda trabajar inicialmente con:

```text
Town03
```

El objetivo es controlar una sola variable antes de probar múltiples mapas.

Posteriormente pueden probarse otros mapas si el alcance lo requiere.

---

# 96. Condición para avanzar desde tráfico estable

No avanzar a rutas y modelo estocástico hasta comprobar:

```text
simulación síncrona funcional
creación y destrucción consistente
Traffic Manager estable
logging mínimo funcional
sin actores residuales
ejecuciones repetibles razonablemente
```

---

# 97. Condición para avanzar desde rutas

No avanzar al experimento final hasta comprobar:

```text
origen válido
destino válido
ruta válida
detección de llegada
timeout
distancia recorrida
tiempo de viaje
estado del viaje
```

---

# 98. Condición para ejecutar comparación final

Antes de comparar escenarios debe existir:

```text
random_baseline implementado
stochastic_model implementado
mismas condiciones experimentales
logging validado
métricas validadas
varias semillas
dos niveles de demanda
tres categorías definitivas
```

---

# 99. Cronograma conceptual del protocolo

El protocolo organiza el desarrollo en ocho fases:

```text
Fase 1: Condiciones de operación
Fase 2: Entorno de simulación
Fase 3: Zonas origen-destino
Fase 4: Modelo estocástico y rutas
Fase 5: Implementación del generador
Fase 6: Registro de datos
Fase 7: Pruebas y análisis
Fase 8: Integración del producto final
```

El repositorio debe evolucionar de manera compatible con esta secuencia.

---

# 100. Principio final para Codex

Antes de realizar cambios grandes, interpretar el proyecto de esta forma:

> CARLA proporciona el mundo, la red vial, los actores y el comportamiento operacional básico. El software desarrollado agrega una lógica reproducible de viajes urbanos basada en origen, destino, probabilidades y rutas, registra los resultados y compara ese generador contra una asignación aleatoria bajo condiciones equivalentes.

El proyecto debe permanecer:

```text
simple antes que complejo
medible antes que visualmente impresionante
reproducible antes que aleatorio
modular antes que monolítico
documentado antes que implícito
```

Cuando exista una decisión no definida por este documento o por `instrucciones.md`, Codex debe preferir una implementación mínima, configurable y fácilmente reversible, evitando ampliar el alcance académico sin autorización.

---

# 101. Decisión de diseño: frecuencia derivada del historial individual

La evolución autorizada para Town01 reemplaza los pesos manuales por recurrencia
observada en un historial sintético individual. El catálogo compartido describe
únicamente lugares, referencias viales y una de las tres categorías; no declara
que un destino sea intrínsecamente frecuente.

```text
catálogo general de destinos
        ↓
historial dummy reproducible por vehicle_id
        ↓
conteos personales de visitas
        ↓
80 % rutina / 20 % exploración
        ↓
viaje completado
        ↓
actualización del historial de ese vehículo
```

El 80 % selecciona dentro de los destinos más visitados por el vehículo y usa
sus conteos como pesos derivados. El 20 % selecciona entre los restantes y
prioriza destinos nunca visitados. Solo un viaje completado modifica el estado.

La entrada dummy permanece inmutable durante una corrida. Cada ejecución guarda
una copia evolucionada bajo su propio `data/output/<run_id>/`; reutilizarla en una
corrida posterior debe ser una acción explícita. Así se conserva la
reproducibilidad y se evita que un experimento anterior cambie silenciosamente
las condiciones del siguiente.
