# Laboratorio: Control de acceso remoto (MQTT)

Extiende la Actividad 1 con WiFi + MQTT: bloquear/desbloquear el keypad, abrir la puerta en remoto, actualizar la contraseña y publicar eventos de acceso.

## Componentes

Los mismos de la Actividad 1 (ESP32, keypad, LCD I2C, servo, LEDs, resistencias, potenciómetro) más conexión de red.

## Librerías

- Keypad, ESP32Servo, LiquidCrystal_I2C
- WiFi, PubSubClient, ArduinoJson

## Red / MQTT

| Parámetro | Valor |
|-----------|--------|
| WiFi (Wokwi) | SSID `Wokwi-GUEST`, password vacía |
| Broker | `broker.hivemq.com:1883` |
| Tópico | `monitoreo/puerta-acceso1332` |
| Clave por defecto | `123456` (6 caracteres) |

## Acciones remotas (callback MQTT)

Publicá en el tópico (texto plano o JSON):

| Acción | Texto plano | JSON |
|--------|-------------|------|
| Bloquear keypad + LED rojo + aviso | `bloquear` | `{"action":"bloquear"}` |
| Desbloquear y estado inicial | `desbloquear` | `{"action":"desbloquear"}` |
| Abrir puerta remota | `abrir` | `{"action":"abrir"}` |
| Actualizar contraseña | `actualizar:654321` | `{"action":"actualizar","password":"654321"}` |

## Eventos publicados por el ESP32

Tras validar una clave local:

```json
{"evento":"acceso_concedido","clave":"123456","ts":12}
{"evento":"acceso_denegado","clave":"000000","ts":15}
```

## Cómo probar con cliente MQTT

1. Compilá y simulá en Wokwi (`pio run` + extensión Wokwi).
2. Abrí [HiveMQ Web Client](https://www.hivemq.com/demos/websocket-client/).
3. Conectá a `broker.hivemq.com`.
4. Suscribite a `monitoreo/puerta-acceso1332`.
5. Publicá `bloquear`, luego `desbloquear`, `abrir`, `actualizar:654321`.
6. En el keypad de Wokwi probá claves y observá los eventos en el cliente.

## Cableado

Igual que Actividad 1 (servo 13, LEDs 25/26, LCD 21/22, keypad 19/18/5/17 y 16/4/15/23, pot 34).
