# Actividad 4 — Nodo urbano IoT (ESP32 + Wokwi + PlatformIO)

Sistema embebido que interpreta luz, temperatura, humedad y distancia, y activa ventilación, paso peatonal, semáforo y alarma según reglas urbanas. El firmware está modularizado; la simulación corre en Wokwi.

## Enlace Wokwi

El circuito está en [`diagram.json`](../diagram.json) (copia idéntica en esta carpeta). Para obtener el enlace público:

1. Compila con PlatformIO y abre **Wokwi: Start Simulator** en Cursor/VS Code, **o**
2. En [wokwi.com/projects/new/esp32](https://wokwi.com/projects/new/esp32) sustituye el `diagram.json` y pega un sketch (o usa el firmware local).
3. **Save** el proyecto. El URL queda en la barra (`https://wokwi.com/projects/...`).

Sustituye este placeholder cuando lo publiques:

```
https://wokwi.com/projects/NUEVO_ID
```

## Cómo correrlo con PlatformIO

Desde la raíz del repo (`IoT-Labs`) o desde `Activity-4`:

```bash
pio run
pio run -t upload    # hardware real
pio device monitor   # 115200 baud
```

Simulación (extensión Wokwi):

1. `pio run` (debe existir `.pio/build/esp32dev/firmware.bin`).
2. Paleta de comandos → **Wokwi: Start Simulator**.
3. En el monitor serial: `1`, `2` o `3` para los escenarios; `0` para sliders en vivo.

## Mapa de pines

| Señal | GPIO | Notas |
|-------|------|--------|
| DHT22 DATA | 4 | 3,3 V |
| LDR AO | 34 | ADC1, solo entrada |
| HC-SR04 TRIG | 5 | VCC del módulo a 5 V |
| HC-SR04 ECHO | 18 | En hardware real: divisor 1 kΩ / 2 kΩ |
| LED rojo | 25 | + 220 Ω |
| LED verde | 26 | + 220 Ω |
| LED azul | 27 | + 220 Ω |
| Buzzer | 14 | |
| LCD I2C SDA / SCL | 21 / 22 | Dirección 0x27 |

## Reglas de control

| ID | Condición | Respuesta |
|----|-----------|-----------|
| C1 | Luz < 300 y T > 30 °C | LED azul (ventilación) + LED verde (paso) |
| C2 | Distancia < 30 cm | LED rojo (semáforo) + buzzer |
| C3 | T > 35 °C y H < 40 % | Alerta combinada (3 LED + buzzer intermitentes) |

La intensidad de luz es 0–1023 (**mayor = más luz**). El módulo LDR de Wokwi sube el voltaje en oscuridad; el firmware lo invierte.

## Tres escenarios urbanos

| Tecla | Escenario | Valores inyectados | Resultado esperado |
|-------|-----------|--------------------|--------------------|
| `1` | Anochecer caluroso en cruce | L=180, T=32,5 °C, H=55 %, D=150 cm | C1: azul + verde |
| `2` | Objeto en zona de detención | L=700, T=24 °C, H=60 %, D=18 cm | C2: rojo + alarma |
| `3` | Ola de calor seca | L=650, T=37,2 °C, H=28 %, D=200 cm | C3: parpadeo + buzzer |
| `0` | Live | Sliders DHT / LDR / HC-SR04 | Según umbrales |

En modo live: clic en cada sensor de Wokwi para mover temperatura, humedad, lux y distancia.

## Estructura del código

```
Activity-4/
  include/config.h      umbrales y pines
  include/types.h       SensorData, ControlState
  src/sensors.cpp       LDR, DHT22, HC-SR04 + validación
  src/control.cpp       C1 / C2 / C3 + histéresis
  src/actuators.cpp     LED y buzzer
  src/display.cpp       LCD 16x2 + Serial
  src/main.cpp          setup / loop cooperativo
  docs/                 informe técnico PDF
```

## Entregables

- Informe: [`docs/Informe_Tecnico_Nodo_Urbano_IoT.pdf`](docs/Informe_Tecnico_Nodo_Urbano_IoT.pdf)
- Requisitos, historias de usuario y criterios de aceptación: en el informe y en [`docs/requisitos.md`](docs/requisitos.md)
