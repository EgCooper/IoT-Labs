"""
Suscriptor MQTT opcional en Python.
Útil para verificar el tópico sin abrir el segundo ESP32.

  pip install paho-mqtt
  python tools/mqtt_subscriber.py
"""

import json
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "home/hall/temperature1"


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[PY] Conectado rc={reason_code} -> subscribe {TOPIC}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    stamp = datetime.now().strftime("%H:%M:%S")
    payload = msg.payload.decode("utf-8", errors="replace")
    print(f"[PY {stamp}] {msg.topic} => {payload}")
    try:
        data = json.loads(payload)
        print(f"         temp={data.get('temp')} C  hum={data.get('hum')} %")
    except json.JSONDecodeError:
        pass


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="py-sub-hall")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    main()
