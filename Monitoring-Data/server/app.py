from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "telemetry.db"

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/labs/monitoring-data/telemetry"

TEMP_MIN = 20.0
TEMP_MAX = 26.0
HUM_MIN = 40.0
HUM_MAX = 60.0

app = Flask(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                temp REAL,
                hum REAL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def store_reading(device_id: str, temp, hum, status: str) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO readings (device_id, temp, hum, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (device_id, temp, hum, status, created_at),
        )
        conn.commit()


def on_mqtt_message(_client, _userdata, msg) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Invalid MQTT payload: {exc}")
        return

    device_id = payload.get("device_id", "unknown")
    temp = payload.get("temp")
    hum = payload.get("hum")
    status = payload.get("status", "UNKNOWN")
    store_reading(device_id, temp, hum, status)
    print(f"Stored MQTT reading: {payload}")


def start_mqtt_subscriber() -> None:
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        client = mqtt.Client()

    def on_connect(client, _userdata, _flags, reason_code, _properties=None):
        print(f"MQTT connected rc={reason_code}, subscribe {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)

    client.on_connect = on_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


@app.get("/")
def dashboard():
    return render_template(
        "dashboard.html",
        temp_min=TEMP_MIN,
        temp_max=TEMP_MAX,
        hum_min=HUM_MIN,
        hum_max=HUM_MAX,
        mqtt_topic=MQTT_TOPIC,
    )


@app.post("/api/telemetry")
def api_telemetry():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id", "manual")
    temp = data.get("temp")
    hum = data.get("hum")
    status = data.get("status", "OK")
    store_reading(device_id, temp, hum, status)
    return jsonify({"ok": True}), 201


@app.get("/api/latest")
def api_latest():
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT device_id, temp, hum, status, created_at
            FROM readings
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    if not row:
        return jsonify({"data": None})
    return jsonify({"data": dict(row)})


@app.get("/api/history")
def api_history():
    limit = min(int(request.args.get("limit", 120)), 500)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT temp, hum, status, created_at
            FROM readings
            WHERE temp IS NOT NULL AND hum IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    data = [dict(r) for r in reversed(rows)]
    return jsonify({"data": data})


@app.get("/api/hourly")
def api_hourly():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                strftime('%Y-%m-%d %H:00', created_at) AS hour,
                AVG(temp) AS avg_temp,
                AVG(hum) AS avg_hum,
                COUNT(*) AS samples
            FROM readings
            WHERE temp IS NOT NULL AND hum IS NOT NULL
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 12
            """
        ).fetchall()
    data = [dict(r) for r in reversed(rows)]
    return jsonify({"data": data})


@app.get("/api/stats")
def api_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
        ok = conn.execute(
            "SELECT COUNT(*) AS n FROM readings WHERE status = 'OK'"
        ).fetchone()["n"]
    comfort_pct = round((ok / total) * 100, 1) if total else 0.0
    return jsonify(
        {
            "total": total,
            "ok": ok,
            "comfort_pct": comfort_pct,
            "temp_min": TEMP_MIN,
            "temp_max": TEMP_MAX,
            "hum_min": HUM_MIN,
            "hum_max": HUM_MAX,
        }
    )


def main() -> None:
    init_db()
    thread = threading.Thread(target=start_mqtt_subscriber, daemon=True)
    thread.start()
    print(f"Dashboard: http://127.0.0.1:5000")
    print(f"MQTT topic: {MQTT_TOPIC}")
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
