# Laboratorio de Humedad con ESP32 y DHT22

En este laboratorio uso un ESP32 junto con un sensor DHT22 para leer la humedad y la temperatura del ambiente. Los datos se muestran por el monitor serial y también se envían a un canal de ThingSpeak mediante HTTP GET. El proyecto está configurado con PlatformIO (placa `esp32dev`, framework Arduino) y se puede simular en Wokwi.

## Qué hice

- Conecté un sensor DHT22 al ESP32 (pin de datos `15`).
- Configuré PlatformIO en `platformio.ini` con las librerías del DHT.
- Leí humedad y temperatura y las mostré por el puerto serie.
- Conecté el ESP32 a WiFi.
- Publiqué los valores en ThingSpeak con una petición HTTP GET (`field1` = temperatura, `field2` = humedad).

## Componentes

- ESP32 (placa de desarrollo) o simulación en Wokwi
- Sensor DHT22
- Cables de conexión (solo en hardware real)
- Fuente de alimentación USB (solo en hardware real)
- Cuenta y canal en [ThingSpeak](https://thingspeak.com)

## Cableado

- `VCC` del DHT22 → `5V` o `3.3V` del ESP32
- `GND` del DHT22 → `GND` del ESP32
- `DATA` del DHT22 → pin `15` del ESP32

> En el código, el pin del sensor está definido como `DHTPIN 15`.

## Configuración de ThingSpeak

1. Crea una cuenta en ThingSpeak y un canal nuevo.
2. Activa al menos dos campos:
   - **Field 1** → Temperatura (°C)
   - **Field 2** → Humedad (%)
3. En la pestaña **API Keys**, copia el **Write API Key**.
4. Coloca esa clave en `src/main.cpp`, en la variable `TS_API_KEY`.

La URL de actualización tiene esta forma:

```text
http://api.thingspeak.com/update?api_key=TU_WRITE_API_KEY&field1=TEMP&field2=HUM
```

Si la respuesta del servidor es un número mayor que `0`, el dato se guardó correctamente. Si es `0`, la actualización fue rechazada (API key inválida o intervalo menor a ~15 s en cuenta gratuita).

## Configuración de WiFi

En `src/main.cpp` debes definir:

```cpp
const char* WIFI_SSID     = "";
const char* WIFI_PASSWORD = "";
const char* TS_API_KEY    = "";
```

### Simulación en Wokwi (sin hardware)

Usa la red virtual de Wokwi:

| Variable | Valor |
|----------|--------|
| `WIFI_SSID` | `Wokwi-GUEST` |
| `WIFI_PASSWORD` | `""` (vacío) |
| `TS_API_KEY` | Tu Write API Key real de ThingSpeak |

### Hardware real

Usa las credenciales de tu red WiFi (preferiblemente **2.4 GHz**; el ESP32 no usa 5 GHz) y la misma Write API Key de ThingSpeak.

> No subas SSID, contraseña ni API key a un repositorio público.

## Cómo usarlo

### Con Wokwi + PlatformIO

1. Abre el proyecto en VS Code / Cursor con PlatformIO.
2. Completa `WIFI_SSID`, `WIFI_PASSWORD` y `TS_API_KEY` en `src/main.cpp`.
3. Compila el proyecto (`PlatformIO: Build`).
4. Inicia la simulación Wokwi (usa `diagram.json` y `wokwi.toml`).
5. Abre el monitor serial a `115200` baudios.
6. Verifica en serial: conexión WiFi, lecturas del DHT y respuesta HTTP de ThingSpeak.
7. Revisa el canal en ThingSpeak → **Private View** para ver los gráficos.

### Con hardware real

1. Conecta el ESP32 por USB.
2. Completa las credenciales WiFi reales y la API key.
3. Sube el firmware (`PlatformIO: Upload`).
4. Abre el monitor serie a `115200`.
5. Confirma los mismos mensajes y los datos en ThingSpeak.

## Qué hace el programa

1. Inicializa el DHT22 y el puerto serie.
2. Se conecta a WiFi (`conectarWiFi()`).
3. En cada ciclo del `loop()`:
   - Lee humedad y temperatura.
   - Si la lectura falla, muestra error y reintenta.
   - Si es válida, imprime los valores en el monitor serial.
   - Envía los datos a ThingSpeak con HTTP GET (`enviarThingSpeak()`).
   - Espera **16 segundos** antes del siguiente envío (límite de la cuenta gratuita de ThingSpeak: ~15 s entre updates).

Ejemplo de salida esperada en serial:

```text
WiFi conectado
IP: ...
Humedad: 60.00 %
Temperatura: 34.10 °C
GET -> http://api.thingspeak.com/update?api_key=...&field1=34.10&field2=60.00
HTTP 200 | respuesta: 5
```

`HTTP 200` y una respuesta numérica `> 0` confirman que ThingSpeak aceptó el dato.

## Archivos principales

- `platformio.ini`: placa, framework y dependencias.
- `src/main.cpp`: lectura del DHT, WiFi y envío HTTP a ThingSpeak.
- `diagram.json` / `wokwi.toml`: simulación en Wokwi.
- `.gitignore`: evita subir archivos generados por PlatformIO y VS Code.

## Notas

- El sensor DHT22 puede tardar unos segundos en entregar la primera lectura válida.
- Si ves `Error leyendo el sensor`, revisa el cableado (o el diagrama en Wokwi) y reinicia.
- Si el WiFi no conecta en Wokwi, confirma que usas `Wokwi-GUEST` con password vacío.
- Si ThingSpeak responde `0`, revisa la API key y que el intervalo sea ≥ 15 s.

## Capturas

![alt text](/imgs/diagraam.png)

![alt text](/imgs/outputs.png)

## Demo Video

![alt text](/imgs/preview.png)

[Ir al video](https://drive.google.com/drive/folders/1DuEENFiGhsPQ8bfkrApgRG3ui8Knil6r?usp=sharing)
