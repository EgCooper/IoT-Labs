# Laboratorio 7 — Actividad 2  
Analítica histórica, alertas predictivas y MQTT

Python procesa un CSV de temperatura/humedad, aplica dos reglas de inferencia, exporta JSON y publica en `test.mosquitto.org` (`/iot/alertas`). Un ESP32 en Wokwi **publica** las mismas reglas; otro **se suscribe** y enciende LED + LCD.

## Cómo correr el análisis (Python 3)

```bash
cd Laboratorio-7/Activity-2
python -m pip install -r requirements.txt
python python/generate_dataset.py
python python/analyze.py
```

Sin broker (solo gráficas + JSON):

```bash
python python/analyze.py --no-mqtt
```

Validar recepción (una terminal escucha, otra publica):

```bash
python python/mqtt_listener.py --seconds 40
# en otra terminal:
python python/analyze.py
```

Salidas en `output/`:

| Archivo | Contenido |
|---------|-----------|
| `eventos.json` | Alertas con justificación |
| `figuras/*.png` | Cuatro gráficas |
| `mqtt_publicacion.json` | Acuses de `publish` QoS 1 |
| `mqtt_recepcion.json` | Mensajes capturados por el listener |

## ESP32 en Wokwi (red virtual → Internet)

SSID `Wokwi-GUEST`, contraseña vacía, **canal 6**. Eso es la red virtual de Wokwi: el firmware llega a `test.mosquitto.org:1883`.

| Nodo | Carpeta | Rol |
|------|---------|-----|
| Publicador | `firmware/publisher` | Replay de días + reglas → publica `/iot/alertas` (LED rojo parpadea) |
| Suscriptor | `firmware/subscriber` | Subscribe `/iot/alertas` → LED rojo (sobrecalor), naranja (sequía), LCD |

En cada carpeta:

```bash
pio run
# Wokwi: Start Simulator  (abrir esa carpeta o seleccionar su wokwi.toml)
```

Hay que **simular los dos proyectos a la vez** (dos ventanas Wokwi) o publicar con Python y dejar solo el suscriptor.

## Tópico y broker

- Broker: `test.mosquitto.org`
- Tópico: `/iot/alertas` (tal como pide el enunciado)
- Puerto de laboratorio: **1883** (sin cifrado). El informe describe 8883/TLS, autenticación y ACL.

## Informe

[`docs/Informe_Tecnico_Analitica_MQTT.pdf`](docs/Informe_Tecnico_Analitica_MQTT.pdf)
