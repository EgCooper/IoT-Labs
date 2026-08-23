"""
Suscriptor de validación: escucha /iot/alertas en test.mosquitto.org
y guarda lo recibido en output/mqtt_recepcion.json.

  python python/mqtt_listener.py --seconds 40
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from analyze import BROKER, NODO_ID, PORT_PLAIN, TOPIC, _make_client

OUT = Path(__file__).resolve().parent.parent / "output" / "mqtt_recepcion.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()

    received: list[dict] = []
    client = _make_client(f"{NODO_ID}-listen-{uuid.uuid4().hex[:6]}")

    def on_connect(c, userdata, flags, reason_code, properties=None):
        print(f"Conectado rc={reason_code} → subscribe {TOPIC}")
        if int(reason_code) == 0:
            c.subscribe(TOPIC, qos=1)

    def on_message(c, userdata, msg):
        stamp = datetime.now(timezone.utc).isoformat()
        try:
            body = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            body = {"raw": msg.payload.decode("utf-8", errors="replace")}
        item = {"recibido_utc": stamp, "topic": msg.topic, "payload": body}
        received.append(item)
        tipo = body.get("tipo", "?") if isinstance(body, dict) else "?"
        print(f"  ← {tipo}  {body.get('id', '')}  {body.get('fecha', '')}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT_PLAIN, 60)
    client.loop_start()
    print(f"Escuchando {BROKER}{TOPIC} durante {args.seconds}s …")
    time.sleep(args.seconds)
    client.loop_stop()
    client.disconnect()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(received, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {OUT}  ({len(received)} mensajes)")


if __name__ == "__main__":
    main()
