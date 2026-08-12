# L5-A1 — Red IoT MQTT (Publicador / Suscriptor)

Red IoT minima con WiFi (Wokwi), broker MQTT publico (HiveMQ), un ESP32 publicador y un ESP32 suscriptor.

Informe tecnico: [INFORME.md](INFORME.md)

## Estructura

```
publisher/src/publisher.ino     # ESP32 publicador (.ino)
subscriber/src/subscriber.ino   # ESP32 suscriptor + LCD (.ino)
tools/mqtt_subscriber.py        # suscriptor opcional en Python
INFORME.md                      # informe tecnico
docs/capturas/                  # capturas serial / Wireshark
```

## Parametros

| Item | Valor |
|------|--------|
| WiFi | SSID `Wokwi-GUEST`, password vacia |
| Broker | `broker.hivemq.com:1883` |
| Topico | `home/hall/temperature1` |

## Como ejecutar

```powershell
# Publicador
cd publisher
pio run
# Abrir diagram.json -> Start simulation (Wokwi)

# Suscriptor (otra ventana)
cd ..\subscriber
pio run
# Abrir diagram.json -> Start simulation
```

Hacen falta **dos** simulaciones Wokwi al mismo tiempo.

### Cliente Python (opcional)

```powershell
pip install -r tools/requirements.txt
python tools/mqtt_subscriber.py
```

## Wireshark

Con la simulacion corriendo: icono WiFi en Wokwi -> descargar PCAP -> abrir en Wireshark.  
Filtros: `mqtt` o `tcp.port == 1883`. Detalle en el informe.
