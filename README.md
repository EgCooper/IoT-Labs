# L5-A1 — Red IoT MQTT (Publicador y Suscriptor)

Dos ESP32 en Wokwi se conectan a la WiFi `Wokwi-GUEST` y al broker público **HiveMQ**. El publicador envía lecturas simuladas al tópico `home/hall/temperature1`; el suscriptor las muestra en Serial y en un LCD I2C.

Informe técnico: [INFORME.md](INFORME.md)

## Estructura

```
publisher/src/publisher.ino     # ESP32 publicador
subscriber/src/subscriber.ino   # ESP32 suscriptor + LCD
tools/mqtt_subscriber.py        # suscriptor opcional en Python
INFORME.md
```

## Cómo ejecutar

```powershell
# 1) Publicador
cd publisher
pio run
# Abrir diagram.json y Start simulation (Wokwi)

# 2) Suscriptor (otra terminal / otra ventana Wokwi)
cd subscriber
pio run
# Abrir diagram.json y Start simulation
```

WiFi Wokwi: SSID `Wokwi-GUEST`, password vacía.  
Broker: `broker.hivemq.com:1883`.  
Tópico: `home/hall/temperature1`.

## Monitoreo de red

En Wokwi: icono WiFi → descargar PCAP → abrir en Wireshark.  
Filtros: `mqtt` o `tcp.port == 1883`. Detalle en el informe.
