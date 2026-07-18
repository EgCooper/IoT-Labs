# Laboratorio de Humedad con ESP32 y DHT22

En este pequeño laboratorio, uso un ESP32 junto con un sensor DHT22 para leer la humedad y la temperatura del ambiente. El proyecto está configurado con PlatformIO y la placa `esp32dev` en el framework Arduino.

## Qué hice

- Conecté un sensor DHT22 al ESP32.
- Configuré PlatformIO en `platformio.ini` para usar la placa `esp32s3` y las librerías necesarias.
- Escribí el programa en `src/main.cpp` para leer la humedad y la temperatura y mostrarlas por el puerto serie.

## Componentes

- ESP32 (placa de desarrollo)
- Sensor DHT22
- Cables de conexión
- Fuente de alimentación USB

## Cableado

- `VCC` del DHT22 → `5V` o `3.3V` del ESP32
- `GND` del DHT22 → `GND` del ESP32
- `DATA` del DHT22 → pin `15` del ESP32

> En el código, el pin del sensor está definido como `DHTPIN 15`.

## Cómo usarlo

1. Abrí VS Code y cargué este proyecto.
2. Verifiqué que PlatformIO reconozca la placa y la configuración en `platformio.ini`.
3. Conecté el ESP32 por USB al equipo.
4. Cargué el programa al ESP32 usando PlatformIO.
   - En VS Code, usé la opción `PlatformIO: Upload`.
5. Abrí el monitor serie a `115200` baudios.
6. Observé los valores de humedad y temperatura en la salida serie.

## Qué hace el programa

- Inicializa el sensor DHT22.
- Lee la humedad y la temperatura cada 2 segundos.
- Si la lectura falla, muestra un mensaje de error.
- Si la lectura es correcta, muestra en el puerto serie:
  - `Humedad: XX %`
  - `Temperatura: XX °C`

## Archivos principales

- `platformio.ini`: configuración de la placa, framework y dependencias.
- `src/main.cpp`: código que inicializa el sensor y lee los datos.
- `.gitignore`: evita subir archivos generados por PlatformIO y VS Code.

## Notas

- El sensor DHT22 puede tardar unos segundos en entregar la primera lectura válida.
- Si ves `Error leyendo el sensor`, revisa el cableado y reinicia el ESP32.
