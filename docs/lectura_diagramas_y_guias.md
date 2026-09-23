# Lectura de los diagramas y líneas guía — 2026-09-20

El estudiante solicita entender por qué la nube observada no coincide con
sus dos esquemas de referencia y añadir guías de lectura. Se reutilizaron
los mismos datos de la campaña del 18 de septiembre, sin nuevas simulaciones,
cambios del controlador ni eliminación de observaciones.

- [Galería completa con guías](../data/output/visual_analysis20_100_guides_20260920/index.html).
- [Lámina 09 con guías](../data/output/visual_analysis20_100_guides_20260920/09_flujo_densidad_velocidad.png).
- [PDF de once láminas](../data/output/visual_analysis20_100_guides_20260920/graficas_campana.pdf).
- [Valores y soporte de las guías](../data/output/visual_analysis20_100_guides_20260920/flow_guides.csv).
- [Paquete completo](../data/output/graficas_20_100_guias_20260920.zip).

Las versiones sin guías del día 19 se conservan. Solo cambia la representación
de la lámina 09 y la explicación; las otras diez láminas usan los mismos datos.

## ¿Vamos bien?

Sí hay avance respecto a los objetivos: se comparan dos cantidades, dos
selectores, historiales crecientes y las cuatro métricas. El 78.14 % de
decisiones de rutina con veinte y 79.18 % con cien son frecuencias cercanas
a la probabilidad configurada de 80 %. Eso no exige exactamente 80 de cada
100 decisiones ni garantiza 80 % de llegadas a una categoría particular.
Los intentos fallidos también implican decisiones, pero no visitas completas.

La selección probabilística de destinos y el diagrama fundamental son
comprobaciones distintas. El primero puede funcionar mientras el controlador,
interacciones, geometría o semáforos generan problemas en la circulación.
El tercer objetivo no exige cero incidentes ni una curva perfecta; sí requiere
interpretar correctamente las métricas y sus causas.

Con cien aparece mayor densidad local y menor velocidad. Sin embargo, también
hay muchos bloqueos, rechazos de rutas y contactos, y casi se detiene la
circulación al final. Se necesita explicar esas secuencias antes de atribuir
el resultado a una congestión representativa o estimar capacidad. Una semilla
sigue sin medir variabilidad entre réplicas.

## Por qué los esquemas se ven diferentes

La primera imagen muestra la hipótesis lineal de Greenshields:
`v = vf (1 - k/kj)`. Al usar `q = k v`, el flujo resulta parabólico:
`q = vf k (1 - k/kj)`. La línea recta y la parábola proceden de esa hipótesis;
la identidad `q = k v` por sí sola no obliga a tener esas formas.

La segunda imagen incluye un diagrama triangular de flujo-densidad y otras
curvas posibles. Además, su panel central tiene velocidad horizontal y flujo
vertical: es la orientación inversa a nuestro panel velocidad-flujo, que
coincide con la primera imagen. Son referencias conceptuales, no un patrón
que toda nube observada deba copiar. Los valores de velocidad de carretera
de su pie tampoco se transfieren a Town01 con nuestro controlador.

[FHWA, metodología de variables y modelos de tráfico](https://ops.fhwa.dot.gov/publications/weatherempirical/sect3.htm)
distingue la identidad entre variables de la forma funcional y de la
calibración en estados estacionarios. Nuestros puntos reúnen calles y momentos
distintos: paso con verde, detención por rojo, espera sin viaje activo,
interacción con otros vehículos, contactos y cambios de régimen. Dos celdas
con densidad parecida pueden mostrar velocidades muy distintas.

Un punto pequeño **no es un carro**: es un carril de 50 m observado durante
60 s, salvo la última ventana parcial. Tampoco el eje de densidad equivale
a la flota total de veinte/cien. La selección cubre 38 tramos rectos y no
toda la red. Las 47,648 muestras sin proyección driving de cien/aleatorio
siguen excluidas de las celdas locales y conservadas en los registros.

## Cómo se construyeron las guías

Se fijaron bandas comunes `[0,10)`, `[10,20)`, etc., en vehículos/km/carril,
por separado para cada corrida. Dentro de cada banda se suman tiempo
vehicular `S`, distancia longitudinal `D` y área espacio-temporal `A=L*T`:

- `k_guía = 1000 sum(S) / sum(A)`.
- `q_guía = 3600 sum(D) / sum(A)`.
- `v_guía = 3.6 sum(D) / sum(S)`.

La duración real de cada ventana aporta su peso. La velocidad resultante
no es la media aritmética de velocidades de celda. Los mismos triples se
proyectan en los tres paneles y conservan `q_guía = k_guía v_guía` en cada
marcador. Los segmentos rectos que unen marcadores son solo ayudas visuales;
no son estados calculados ni garantizan esa identidad en su interior.

Se dibuja una banda con al menos diez celdas y se conectan únicamente bandas
consecutivas que cumplen ese umbral. Las ausentes o escasas rompen la línea;
no se extrapola hasta densidad cero ni hasta un atasco supuesto. Los puntos
originales permanecen incluso donde no se dibuja guía. No se agregan celdas
vacías con una velocidad artificial de cero.

El ancho de diez y el mínimo de diez son criterios de legibilidad explícitos,
no parámetros calibrados, número suficiente de réplicas ni umbrales de
congestión. Las celdas siguen siendo dependientes. `flow_guides.csv` incluye
también bandas no dibujadas, sus cantidades y sumas; `guide_method.json`
registra el procedimiento. Se obtuvieron 3/4/9/8 marcadores respaldados
para veinte/aleatorio, veinte/histórico, cien/aleatorio y cien/histórico.

En velocidad-flujo las guías se recorren por **densidad creciente**, no
ordenando por flujo. Un mismo flujo bajo puede corresponder a pocos carros
rápidos o a muchos casi parados. Forzar una única velocidad promedio para
cada flujo ocultaría esa diferencia.

## Qué se puede leer ahora

Las guías muestran menor velocidad al aumentar densidad. Con veinte, su
soporte alcanza pocas bandas: faltan observaciones suficientes para dibujar
una rama completa de alta densidad. Con cien aparecen acumulaciones casi
inmóviles y descenso del flujo en sectores de alta densidad. También hay
zigzags y huecos; reflejan heterogeneidad/cobertura de estos datos, no se
suavizaron para parecer una parábola.

Que el primer marcador esté cerca de 15 km/h y haya puntos cerca de 20 no
es una contradicción: resume una banda con distintas velocidades y paradas.
No representa la velocidad libre en densidad cero ni el límite configurado.

Por ejemplo, cien/aleatorio resume su banda 20–30 en `k≈24.14`, `v≈10.37`,
`q≈250.31`; su banda 140–150 resume `k=140`, `v≈0.018`, `q≈2.58`.
El primer valor no es una capacidad estimada y el segundo no establece una
densidad de atasco calibrada. Hace falta revisar causas y tramos comparables.

## Validación y continuación

Pasaron 130 pruebas con `carla-env`, cuatro nuevas sobre ponderación por
exposición, conservación de identidad, bandas escasas/ausentes, límites,
paradas y entradas inválidas. La lectura parte de copias idénticas de los
CSV derivados/auditorías del día 19; se verifican hashes en
`inherited_inputs.json`. Se inspeccionó la página PDF modificada y se
conservan los resultados previos.

El paso siguiente sigue siendo reconstruir el inicio de bloqueos/contactos
con cien y separar condiciones de medición. Después evaluar demandas
intermedias y otras semillas, y solo entonces plantear ajuste/calibración
de un modelo fundamental si aporta a los objetivos. No se requieren incidentes
cero ni reproducir una forma dibujada para que el experimento sea útil.
