# IoT Labs — Monitoring Data

Práctica de visualización IoT: temperatura y humedad con DHT22 (Wokwi + PlatformIO), telemetría JSON por MQTT, histórico en SQLite y dashboard web (gauges, líneas y barras).

## Arquitectura

```text
ESP32 + DHT22 (Wokwi)
    → JSON telemetry
    → MQTT (broker.hivemq.com)
    → Flask subscriber + SQLite
    → Dashboard Chart.js (http://127.0.0.1:5000)
```

## Rango de confort

| Variable   | Mín | Máx |
|------------|-----|-----|
| Temperatura | 20 °C | 26 °C |
| Humedad     | 40 %  | 60 %  |

Estados: `OK`, `TEMP_LOW`, `TEMP_HIGH`, `HUM_LOW`, `HUM_HIGH`, `SENSOR_ERROR`.

## Hardware simulado (Wokwi)

- ESP32 DevKit
- DHT22 en **GPIO 15**
- Archivos: `diagram.json`, `wokwi.toml`

## Firmware (PlatformIO)

```bash
cd Monitoring-Data
# Build (desde la UI de PlatformIO o CLI)
```

Configuración en `src/main.cpp`:

- WiFi Wokwi: `Wokwi-GUEST` (sin password)
- Broker: `broker.hivemq.com:1883`
- Topic: `iot/labs/monitoring-data/telemetry`
- Device: `lab-01`

Payload de ejemplo:

```json
{"device_id":"lab-01","temp":24.5,"hum":55.0,"status":"OK","ts":42}
```

## Dashboard / backend

```bash
cd Monitoring-Data/server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000).

El servidor:

1. Se suscribe al topic MQTT y guarda en `telemetry.db`
2. Expone APIs `/api/latest`, `/api/history`, `/api/hourly`, `/api/stats`
3. Acepta inyección manual: `POST /api/telemetry`

### Probar sin ESP

```bash
curl -X POST http://127.0.0.1:5000/api/telemetry ^
  -H "Content-Type: application/json" ^
  -d "{\"device_id\":\"lab-01\",\"temp\":24.5,\"hum\":55,\"status\":\"OK\"}"
```

## Demo sugerida (3–5 min)

1. Arrancar `python app.py`
2. Build + Start Simulator en Wokwi
3. Ver JSON en Serial y puntos en el dashboard
4. Cambiar temp/humedad en el DHT22 de Wokwi y mostrar gauges/alertas
5. Señalar línea histórica y barras por hora

## Fases cubiertas

1. Entorno PlatformIO + Wokwi
2. Lectura DHT + umbrales
3. Telemetría JSON
4. MQTT
5. Persistencia SQLite
6. Dashboard (gauges, histórico, barras)
7. Documentación / demo
