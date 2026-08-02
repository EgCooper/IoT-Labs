# Laboratorio: Control de acceso (Keypad + Servo + LCD)

Sistema de acceso con ESP32: se ingresa una contraseña de 6 caracteres por el keypad, se valida y se controla un servo (cerradura), un LCD I2C y LEDs de estado. Proyecto con **PlatformIO** y simulación en **Wokwi**.

## Componentes

- ESP32 DevKit
- Keypad matricial 4x4
- LCD 1602 I2C
- Servo
- LED verde y LED rojo
- Resistencias 220 Ω
- Potenciómetro (conectado a ADC; material del lab)

## Librerías (`platformio.ini`)

- Keypad
- ESP32Servo
- LiquidCrystal_I2C

## Cableado

| Dispositivo | Señal | GPIO ESP32 |
|-------------|--------|------------|
| Servo | PWM | 13 |
| LED verde | vía 220 Ω | 25 |
| LED rojo | vía 220 Ω | 26 |
| LCD I2C | SDA / SCL | 21 / 22 |
| Keypad filas R1–R4 | | 19, 18, 5, 17 |
| Keypad columnas C1–C4 | | 16, 4, 15, 23 |
| Potenciómetro | SIG | 34 |

Servo: `V+` → 5V, `GND` → GND. LCD: `VCC` → 3V3, `GND` → GND. Dirección I2C del LCD: `0x27`.

## Contraseña

Almacenada en código, tamaño 6. Valor por defecto: `123456` (cambiar en `src/main.cpp`).

## Flujo

1. Estado inicial: servo en **0°** (cerrado), LEDs apagados, LCD pide la clave.
2. Se leen **6** caracteres del keypad (se muestran como `*`).
3. Si la clave es correcta: mensaje de bienvenida, servo a **180°**, LED verde ON.
4. Si es incorrecta: mensaje de alerta, servo en **0°**, LED rojo ON.
5. Tras **3 segundos** se vuelve al estado inicial.

## Cómo usarlo

1. Abrí el proyecto en VS Code / Cursor con la extensión PlatformIO.
2. Compilá con `PlatformIO: Build` (`pio run`).
3. Simulá con la extensión Wokwi (usa `diagram.json` y `wokwi.toml`).
4. Ingresá 6 teclas en el keypad del simulador.

## Funciones principales

- `leerSeisCaracteres()` — lee 6 caracteres del panel matricial.
- `imprimirMensajes(l1, l2)` — muestra dos cadenas en el LCD.
- `estadoInicial()` — servo cerrado, LEDs off, buffer vacío, mensaje de bienvenida.
