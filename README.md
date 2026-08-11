# Generador de tráfico urbano en CARLA

Base técnica para crear tráfico urbano controlado y reproducible en **CARLA
0.9.15**. Esta primera fase se concentra en una simulación estable con Python,
modo síncrono y Traffic Manager. El modelo estocástico de destinos, las rutas
completas, los sensores y el análisis comparativo quedan para fases posteriores.

## Requisitos

- Windows y CARLA 0.9.15 (`WindowsNoEditor`).
- Una versión de Python compatible con la distribución local de la Python API
  incluida con CARLA 0.9.15.
- La Python API de CARLA disponible en el entorno mediante el `.egg` o paquete
  local incluido en `PythonAPI/carla/dist`.

Instala las dependencias auxiliares desde la raíz del repositorio:

```powershell
python -m pip install -r .\requirements.txt
```

`carla` no se incluye en `requirements.txt`: se debe usar la distribución local
que acompaña a CARLA 0.9.15.

## Estructura principal

```text
config/       Configuraciones base de escenarios y Traffic Manager
data/input/   Configuración dummy reproducible
data/output/  Resultados de futuras corridas
scripts/      Puntos de entrada ejecutables
src/          Módulos compartidos para las siguientes fases
```

Los directorios heredados `configs/`, `data/raw/`, `data/processed/` y
`data/results/` no son usados por esta fase. La estructura activa sigue
`instrucciones.md`: `config/`, `data/input/` y `data/output/`.

## Iniciar CARLA

Abre PowerShell en el directorio de instalación de CARLA y ejecuta:

```powershell
cd C:\CARLA\WindowsNoEditor
.\CarlaUE4.exe -quality-level=Low
```

En un equipo con GPU integrada o recursos limitados, usa DirectX 11 y una ventana
pequeña:

```powershell
.\CarlaUE4.exe -quality-level=Low -dx11 -windowed -ResX=800 -ResY=600
```

Espera a que el simulador termine de cargar. Los scripts se conectan a
`localhost:2000` con un timeout de 30 segundos.

## Flujo recomendado en equipos con recursos limitados

El cambio de mapa y la creación del tráfico se ejecutan en pasos separados para
evitar encadenar ambas cargas. Después de iniciar CARLA, cambia el mapa desde la
raíz de este repositorio:

```powershell
python .\scripts\change_map.py --town Town01
```

Espera entre 10 y 15 segundos después de ver `Mapa cargado` para que el servidor se
estabilice. `change_map.py` no recarga el mapa si ya está activo.

## Ejecutar tráfico estable

Prueba inicial recomendada:

```powershell
python .\scripts\stable_traffic.py --town Town01 --vehicles 10 --seconds 60 --no-rendering
```

El script usa el mundo que ya está activo: nunca carga ni recarga mapas. El
argumento opcional `--town` solo comprueba que el mapa actual sea el esperado y
termina con un mensaje claro si no coincide. Después activa el modo síncrono con
un delta fijo de `0.05` segundos, habilita no-rendering cuando se solicita,
sincroniza Traffic Manager y crea solo vehículos de cuatro ruedas con parámetros
conservadores. Los vehículos se crean progresivamente, avanzando un tick entre
cada actor para evitar una ráfaga de carga.

Las métricas mostradas son:

- cantidad de vehículos activos;
- velocidad promedio en km/h;
- cantidad de vehículos detenidos (velocidad menor que 1 km/h).

Al finalizar, incluso después de `Ctrl+C`, elimina los vehículos creados,
desactiva el modo síncrono de Traffic Manager y restaura la configuración original
del mundo. Para corridas sin renderizado:

```powershell
python .\scripts\stable_traffic.py --town Town03 --vehicles 30 --seconds 120 --no-rendering
```

El script elimina al inicio cualquier vehículo que ya exista en el mapa para que
la corrida comience desde un estado controlado. No elimina peatones ni otros tipos
de actores.

## Generar datos dummy

Ejecuta:

```powershell
python .\scripts\generate_dummy_data.py
```

El comando valida que los pesos de destinos sumen `1.0` y regenera:

```text
data/input/zones_config.csv
data/input/destinations_config.csv
data/input/demand_profiles.csv
```

Estos CSV son configuración sintética fija; no contienen resultados ni viajes.
Los resultados futuros deberán guardarse exclusivamente bajo `data/output/`.

## Configuración base

Los archivos de `config/` documentan los parámetros previstos para escenarios
básico, de baja demanda y de alta demanda, además de los ajustes conservadores de
Traffic Manager. En esta fase `stable_traffic.py` expone sus valores operativos
por argumentos y constantes; la carga automática de escenarios se incorporará al
separar la lógica común hacia `src/`.

## Próximos pasos

Cuando las pruebas con 10, 20 y 30 vehículos sean estables, las siguientes fases
podrán separar la conexión y gestión de actores en módulos reutilizables, agregar
logs CSV, zonas origen-destino, selección estocástica y planificación de rutas.
Todavía no se implementan sensores de colisión o invasión de carril,
visualizaciones avanzadas, comparación estadística ni Google Maps API.
