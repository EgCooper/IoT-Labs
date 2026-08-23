# Monitor de invernadero — cooperativa

## El problema

La cooperativa se está comiendo plata y plantas porque nadie se entera a tiempo si el invernadero se calentó de más o si el suelo se secó. Cultivos sensibles no perdonan: un rato de calor o de sequía y ya perdiste calidad o toda la tanda.

Lo que armé es un monitor barato que mide temperatura y humedad de suelo todo el tiempo. Si está bien, se ve un LED verde. Si algo se sale del rango, cambia de color. El agricultor no tiene que abrir una app ni saber de IoT: mira el tablero y listo. Si hay red, también mando el estado por MQTT por si el encargado no está al lado.

## Requisitos

Funcionales:

1. Medir temperatura ambiente.
2. Medir humedad del suelo.
3. Comparar las dos lecturas contra umbrales (óptimo, aviso, crítico).
4. Avisar con LEDs (y LCD con los números).

No funcionales:

1. Barato y fácil de armar (piezas de hobby, un solo micro).
2. Que un agricultor lo entienda en dos segundos, sin manual largo. Si algún día va a pila, el loop es liviano (sin delays trabando todo).

## Hardware (Wokwi)

Me quedé con ESP32 y no con Uno. El enunciado pide “tipo Arduino” y el ESP32 igual se programa así, pero me deja WiFi/MQTT sin shield extra. Para el prototipo me servía.

- **TMP36** en GPIO 34. Es analogico, sale en Wokwi y la fórmula es conocida (0.5 V = 0 °C). Lo alimenté a 3.3 V, no a 5 V, porque el ADC del ESP32 no aguanta 5 V.
- **Potenciómetro** en GPIO 35. Wokwi no trae un sensor de suelo de verdad; el pote hace de analogico (girás = cambia la humedad). En campo iría un capacitivo, misma idea: 0–3.3 V → 0–100 %.
- **LED verde (25), amarillo (26), azul (27), rojo (13)** con resistencia de 220 Ω cada uno. Un color = una cosa. No hay que leer un menú.
- **LCD I2C 16x2** (SDA 21, SCL 22). Los LEDs alcanzan para el aviso; el LCD es para ver el número (20.4 °C, 47 %). Eso el brief lo deja como mejora y yo lo puse ya.
- **Buzzer (12) + botón silenciar (14).** Extra. El rojo parpadeando ya es la alerta; el pitido es por si estás de espaldas.

Diagrama: está en `diagram.json`. Resumen de pines:

| Cosa        | Pin ESP32 |
|-------------|-----------|
| TMP36 VOUT  | 34        |
| Suelo SIG   | 35        |
| LED verde   | 25        |
| LED amarillo| 26        |
| LED azul    | 27        |
| LED rojo    | 13        |
| Buzzer      | 12        |
| Botón       | 14        |
| LCD SDA/SCL | 21 / 22   |

## Lógica

```
loop:
  leer TMP36 y suelo
  clasificar cada uno (optimo / aviso / critico)
  prender LEDs
  pintar LCD
  si hay WiFi, publicar MQTT cada 5 s
```

Umbrales que usé (razonables, no de laboratorio):

- Temperatura óptima: **20–25 °C**. Aviso si se sale. Crítico si baja de **12 °C** o pasa **32 °C**.
- Suelo óptimo: **60–80 %**. Aviso si está más seco o más empapado. Crítico si baja de **30 %**.

LEDs:

- Verde solo: las dos bien.
- Amarillo: la temperatura se salió.
- Azul: el suelo se salió (seco o muy mojado; el LCD dice el %).
- Rojo parpadeando: los dos mal **o** uno ya en crítico. Ahí también pita el buzzer.

Por qué Arduino/ESP32 y no un PLC o una Raspberry: este problema es “leer 2 analogicos y prender 4 LEDs”. Un PLC es overkill y caro. Una Pi consume más y es más cosa para mantener. Acá con un micro de unos dólares y sensores baratos ya cubrís el invernadero. Se replica nave por nave.

## El agricultor

Lo pongo a la entrada del invernadero, a la altura de los ojos, no escondido atrás de las macetas. Pasás, mirás:

- Verde → seguí.
- Amarillo → abrí ventilación o revisá el calor.
- Azul → regá (o dejá de regar si el LCD está en 90 %).
- Rojo titilando → las dos cosas o ya está feo: andá ya.

El LCD es lo que los LEDs no pueden decir: el valor. Después se puede sumar historial, WhatsApp o una electroválvula. Por ahora no hace falta.

## Wokwi y cómo probarlo

Lo que más usé: el diagrama visual, los sliders del TMP36 y del pote, y el Serial para ver si los umbrales cuadraban.

1. Build en PlatformIO y Start Simulator.
2. TMP36 en ~22 °C y pote tipo 70 % → verde.
3. Subí la temperatura a 28 °C → amarillo. A 33 °C → rojo.
4. Bajá el pote (suelo seco) → azul. Muy abajo → rojo.
5. Temperatura alta **y** suelo seco → rojo parpadea + buzzer. El botón lo calla; el LED no.

## El código (contra el flujo)

- `setup()`: pines, ADC a 12 bits, LCD, WiFi/MQTT. Equivale al “arrancar e inicializar” del flujo.
- `loop()`: el ciclo del diagrama (leer → clasificar → indicar → publicar).
- `leerTemperatura()` / `leerSueloPct()`: sensores. Promedio de 8 muestras porque el ADC del ESP32 salta.
- `clasificarTemp()` / `clasificarSuelo()`: los if de los umbrales.
- `actualizarLeds()` / `refrescarLcd()`: lo que ve el agricultor.
- `publicarEstado()`: extra IoT. Si HiveMQ falla, el tablero local igual sirve. Eso me importaba: no depender de la nube para avisar adentro del invernadero.
