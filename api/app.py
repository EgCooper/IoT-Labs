"""
API propia para telemetría IoT (Sigfox / endpoint público).

GET  /data       -> consulta el endpoint externo y devuelve los últimos 2 registros
POST /visualize  -> recibe JSON y lo envía a la app de visualización (dashboard)
GET  /           -> dashboard con gauges
"""

from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

EXTERNAL_DATA_URL = "https://callback-iot.up.railway.app/data"
EXTERNAL_TIMEOUT_S = 12

app = Flask(__name__)
CORS(app)

# Estado en memoria para el dashboard (lo que llega por POST /visualize)
visualization_store = {
    "updated_at": None,
    "records": [],
}


def _as_record_list(payload):
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        nested = payload.get("data")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        return [payload]
    return []


def fetch_external_records():
    response = requests.get(EXTERNAL_DATA_URL, timeout=EXTERNAL_TIMEOUT_S)
    response.raise_for_status()
    return _as_record_list(response.json())


def last_two(records):
    return records[-2:]


def push_to_visualization(records):
    visualization_store["records"] = last_two(records)
    visualization_store["updated_at"] = datetime.now(timezone.utc).isoformat()
    return visualization_store


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/data")
def get_data():
    """Consulta el endpoint público y devuelve los últimos 2 objetos."""
    try:
        records = last_two(fetch_external_records())
        return jsonify(records)
    except requests.RequestException as exc:
        return (
            jsonify(
                {
                    "error": "No se pudo consultar el endpoint público",
                    "detail": str(exc),
                    "source": EXTERNAL_DATA_URL,
                }
            ),
            502,
        )


@app.post("/visualize")
def post_visualize():
    """Recibe datos JSON y los reenvía a la aplicación de visualización."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Body JSON requerido"}), 400

    records = _as_record_list(payload)
    if not records:
        return jsonify({"error": "No se encontraron objetos de telemetría"}), 400

    stored = push_to_visualization(records)
    return jsonify(
        {
            "ok": True,
            "message": "Datos enviados a la visualización",
            "count": len(stored["records"]),
            "updated_at": stored["updated_at"],
            "data": stored["records"],
        }
    )


@app.get("/visualize/latest")
def get_visualize_latest():
    """Lectura del último estado que el dashboard usa para los gauges."""
    return jsonify(visualization_store)


@app.post("/sync")
def sync_pipeline():
    """Útil para pruebas: GET externo -> últimos 2 -> POST a visualización."""
    try:
        records = last_two(fetch_external_records())
    except requests.RequestException as exc:
        return (
            jsonify(
                {
                    "error": "No se pudo consultar el endpoint público",
                    "detail": str(exc),
                }
            ),
            502,
        )

    if not records:
        return jsonify({"error": "El endpoint público no devolvió registros"}), 404

    stored = push_to_visualization(records)
    return jsonify(
        {
            "ok": True,
            "message": "Últimos 2 registros sincronizados con la visualización",
            "count": len(stored["records"]),
            "updated_at": stored["updated_at"],
            "data": stored["records"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
