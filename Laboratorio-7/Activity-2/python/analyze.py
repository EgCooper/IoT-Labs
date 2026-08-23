"""
Laboratorio 7 · Actividad 2
Análisis histórico (T/H) → reglas predictivas → gráficos/JSON → MQTT.

Uso:
  python python/analyze.py              # analiza, grafica, JSON y publica
  python python/analyze.py --no-mqtt    # solo análisis local
  python python/analyze.py --listen 20  # publica y escucha 20 s (validación)
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data" / "clima_historico.csv"
OUT_DIR = ROOT / "output"
FIG_DIR = OUT_DIR / "figuras"

BROKER = "test.mosquitto.org"
PORT_PLAIN = 1883
TOPIC = "/iot/alertas"
NODO_ID = "lab7-a2-cruce-norte"

# Umbrales de las reglas (documentados en el informe).
TEMP_MIN_SOBRECALOR_C = 28.0
TEMP_SEQUIA_C = 32.0
HUM_SEQUIA_PCT = 35.0
MA_CORTA = 3
MA_LARGA = 7


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["t_ma3"] = out["temperatura_c"].rolling(MA_CORTA, min_periods=MA_CORTA).mean()
    out["t_ma7"] = out["temperatura_c"].rolling(MA_LARGA, min_periods=MA_LARGA).mean()
    out["h_ma3"] = out["humedad_pct"].rolling(MA_CORTA, min_periods=MA_CORTA).mean()
    out["h_ma7"] = out["humedad_pct"].rolling(MA_LARGA, min_periods=MA_LARGA).mean()
    out["t_delta"] = out["temperatura_c"].diff()
    # Pendiente de 3 días (°C/día) sobre la ventana [i-2, i].
    out["t_pendiente_3d"] = (
        out["temperatura_c"]
        .rolling(MA_CORTA, min_periods=MA_CORTA)
        .apply(lambda w: float(np.polyfit(np.arange(len(w)), w, 1)[0]), raw=True)
    )
    return out


def detect_overheating(df: pd.DataFrame) -> pd.Series:
    """T en aumento 3 días: T[d] > T[d-1] > T[d-2] y T actual >= 28 °C."""
    t = df["temperatura_c"]
    rising = (t > t.shift(1)) & (t.shift(1) > t.shift(2))
    return rising & (t >= TEMP_MIN_SOBRECALOR_C)


def detect_drought(df: pd.DataFrame) -> pd.Series:
    """Temperatura alta y humedad baja el mismo día."""
    return (df["temperatura_c"] > TEMP_SEQUIA_C) & (df["humedad_pct"] < HUM_SEQUIA_PCT)


def build_events(df: pd.DataFrame) -> list[dict]:
    events: list[dict] = []
    over = detect_overheating(df)
    dry = detect_drought(df)

    for i, row in df.iterrows():
        fecha = row["fecha"].strftime("%Y-%m-%d")
        if over.iloc[i]:
            events.append(
                {
                    "id": f"OVH-{fecha}",
                    "tipo": "SOBRECALENTAMIENTO",
                    "fecha": fecha,
                    "temperatura_c": round(float(row["temperatura_c"]), 2),
                    "humedad_pct": round(float(row["humedad_pct"]), 1),
                    "t_ma3": None if pd.isna(row["t_ma3"]) else round(float(row["t_ma3"]), 2),
                    "t_pendiente_3d": None
                    if pd.isna(row["t_pendiente_3d"])
                    else round(float(row["t_pendiente_3d"]), 3),
                    "severidad": "alta" if row["temperatura_c"] >= 34 else "media",
                    "justificacion": (
                        f"Temperatura en aumento tres días consecutivos "
                        f"({df.loc[i - 2, 'temperatura_c']:.1f} → "
                        f"{df.loc[i - 1, 'temperatura_c']:.1f} → "
                        f"{row['temperatura_c']:.1f} °C) y T≥{TEMP_MIN_SOBRECALOR_C:.0f} °C."
                    ),
                }
            )
        if dry.iloc[i]:
            events.append(
                {
                    "id": f"DRY-{fecha}",
                    "tipo": "SEQUIA",
                    "fecha": fecha,
                    "temperatura_c": round(float(row["temperatura_c"]), 2),
                    "humedad_pct": round(float(row["humedad_pct"]), 1),
                    "h_ma3": None if pd.isna(row["h_ma3"]) else round(float(row["h_ma3"]), 1),
                    "severidad": "alta" if row["humedad_pct"] < 28 else "media",
                    "justificacion": (
                        f"T={row['temperatura_c']:.1f} °C > {TEMP_SEQUIA_C:.0f} °C y "
                        f"H={row['humedad_pct']:.1f} % < {HUM_SEQUIA_PCT:.0f} % "
                        "(aire caliente y seco: estrés hídrico / incendio de vegetación)."
                    ),
                }
            )
    return events


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#F8FAFC",
            "axes.edgecolor": "#94A3B8",
            "axes.grid": True,
            "grid.color": "#E2E8F0",
            "font.size": 10,
            "axes.titlesize": 13,
            "figure.dpi": 140,
        }
    )


def plot_temperature(df: pd.DataFrame, over: pd.Series, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.plot(df["fecha"], df["temperatura_c"], color="#0F2C59", lw=1.8, label="T diaria")
    ax.plot(df["fecha"], df["t_ma3"], color="#1D4ED8", lw=1.6, ls="--", label="Media móvil 3 d")
    ax.plot(df["fecha"], df["t_ma7"], color="#0EA5E9", lw=1.4, ls=":", label="Media móvil 7 d")
    ax.axhline(TEMP_MIN_SOBRECALOR_C, color="#C97800", ls="-.", lw=1, label="Umbral 28 °C")
    hits = df[over]
    ax.scatter(hits["fecha"], hits["temperatura_c"], c="#B42318", s=46, zorder=5, label="Alerta sobrecalentamiento")
    ax.set_title("Regla 1 — Temperatura y tendencia (aumento 3 días)")
    ax.set_ylabel("°C")
    ax.legend(loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_humidity(df: pd.DataFrame, dry: pd.Series, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.plot(df["fecha"], df["humedad_pct"], color="#1B7A4E", lw=1.8, label="H diaria")
    ax.plot(df["fecha"], df["h_ma3"], color="#22C55E", lw=1.6, ls="--", label="Media móvil 3 d")
    ax.axhline(HUM_SEQUIA_PCT, color="#C97800", ls="-.", lw=1, label="Umbral sequía 35 %")
    hits = df[dry]
    ax.scatter(hits["fecha"], hits["humedad_pct"], c="#C97800", s=46, zorder=5, label="Día de sequía (H baja)")
    ax.set_title("Regla 2 — Humedad (componente seco de la sequía)")
    ax.set_ylabel("% HR")
    ax.legend(loc="upper right", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_combined(df: pd.DataFrame, over: pd.Series, dry: pd.Series, path: Path) -> None:
    _style()
    fig, ax1 = plt.subplots(figsize=(10.5, 4.8))
    ax2 = ax1.twinx()
    ax1.plot(df["fecha"], df["temperatura_c"], color="#B42318", lw=1.7, label="Temperatura")
    ax2.plot(df["fecha"], df["humedad_pct"], color="#1D4ED8", lw=1.5, label="Humedad")
    ax1.fill_between(df["fecha"], 20, 42, where=over, color="#B42318", alpha=0.12, label="Racha calor")
    ax1.fill_between(df["fecha"], 20, 42, where=dry, color="#C97800", alpha=0.18, label="Sequía")
    ax1.set_ylabel("Temperatura (°C)", color="#B42318")
    ax2.set_ylabel("Humedad (%)", color="#1D4ED8")
    ax1.set_title("Ambas reglas sobre la serie — bandas de alerta")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_scatter(df: pd.DataFrame, over: pd.Series, dry: pd.Series, path: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    estado = np.where(dry, "SEQUIA", np.where(over, "SOBRECALOR", "NORMAL"))
    colors = {"NORMAL": "#94A3B8", "SOBRECALOR": "#B42318", "SEQUIA": "#C97800"}
    for key, col in colors.items():
        mask = estado == key
        ax.scatter(
            df.loc[mask, "humedad_pct"],
            df.loc[mask, "temperatura_c"],
            c=col,
            s=52,
            label=key,
            edgecolors="white",
            linewidths=0.6,
        )
    ax.axhline(TEMP_SEQUIA_C, color="#B42318", ls="--", lw=1)
    ax.axvline(HUM_SEQUIA_PCT, color="#C97800", ls="--", lw=1)
    ax.set_xlabel("Humedad relativa (%)")
    ax.set_ylabel("Temperatura (°C)")
    ax.set_title("Plano T–H: cuadrante seco-caliente = sequía")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def export_json(events: list[dict], path: Path) -> dict:
    payload = {
        "nodo_id": NODO_ID,
        "topic": TOPIC,
        "broker": BROKER,
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "reglas": {
            "sobrecalentamiento": f"T[d]>T[d-1]>T[d-2] y T≥{TEMP_MIN_SOBRECALOR_C}°C",
            "sequia": f"T>{TEMP_SEQUIA_C}°C y H<{HUM_SEQUIA_PCT}%",
        },
        "total_eventos": len(events),
        "eventos": events,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _make_client(client_id: str):
    import paho.mqtt.client as mqtt

    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        return mqtt.Client(client_id=client_id)


def publish_mqtt(events: list[dict], timeout_s: float = 8.0) -> list[dict]:
    """Publica cada evento en /iot/alertas (QoS 1). Devuelve acuses locales."""
    client_id = f"{NODO_ID}-pub-{uuid.uuid4().hex[:6]}"
    client = _make_client(client_id)
    acks: list[dict] = []

    def on_connect(c, userdata, flags, reason_code, properties=None):
        userdata["ok"] = int(reason_code) == 0

    client.user_data_set({"ok": False})
    client.on_connect = on_connect
    client.connect(BROKER, PORT_PLAIN, 60)
    client.loop_start()
    deadline = time.time() + timeout_s
    while not client._userdata["ok"] and time.time() < deadline:
        time.sleep(0.05)
    if not client._userdata["ok"]:
        client.loop_stop()
        client.disconnect()
        raise ConnectionError(f"No se pudo conectar a {BROKER}:{PORT_PLAIN}")

    for ev in events:
        envelope = {
            "nodo_id": NODO_ID,
            "origen": "python-analitica",
            "topic": TOPIC,
            "publicado_utc": datetime.now(timezone.utc).isoformat(),
            **ev,
        }
        body = json.dumps(envelope, ensure_ascii=False)
        info = client.publish(TOPIC, body, qos=1)
        info.wait_for_publish(timeout=5)
        acks.append(
            {
                "id": ev["id"],
                "tipo": ev["tipo"],
                "rc": int(info.rc),
                "bytes": len(body.encode("utf-8")),
            }
        )
        time.sleep(0.15)

    client.loop_stop()
    client.disconnect()
    return acks


def listen_and_capture(seconds: int, path: Path) -> list[dict]:
    """Suscriptor Python para validar que el broker reenvía /iot/alertas."""
    received: list[dict] = []
    client_id = f"{NODO_ID}-sub-{uuid.uuid4().hex[:6]}"
    client = _make_client(client_id)

    def on_connect(c, userdata, flags, reason_code, properties=None):
        if int(reason_code) == 0:
            c.subscribe(TOPIC, qos=1)

    def on_message(c, userdata, msg):
        try:
            received.append(json.loads(msg.payload.decode("utf-8")))
        except json.JSONDecodeError:
            received.append({"raw": msg.payload.decode("utf-8", errors="replace")})

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT_PLAIN, 60)
    client.loop_start()
    time.sleep(seconds)
    client.loop_stop()
    client.disconnect()
    path.write_text(json.dumps(received, ensure_ascii=False, indent=2), encoding="utf-8")
    return received


def main() -> None:
    parser = argparse.ArgumentParser(description="Analítica histórica + MQTT")
    parser.add_argument("--no-mqtt", action="store_true", help="No publicar al broker")
    parser.add_argument("--listen", type=int, default=0, help="Segundos de escucha tras publicar")
    args = parser.parse_args()

    if not DATA_CSV.exists():
        from generate_dataset import main as gen

        gen()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    df = add_features(load_dataset(DATA_CSV))
    over = detect_overheating(df)
    dry = detect_drought(df)
    events = build_events(df)

    plot_temperature(df, over, FIG_DIR / "01_temperatura_tendencia.png")
    plot_humidity(df, dry, FIG_DIR / "02_humedad.png")
    plot_combined(df, over, dry, FIG_DIR / "03_series_combinadas.png")
    plot_scatter(df, over, dry, FIG_DIR / "04_plano_th.png")

    payload = export_json(events, OUT_DIR / "eventos.json")
    df.to_csv(OUT_DIR / "serie_con_features.csv", index=False)

    print(f"Filas            : {len(df)}")
    print(f"Sobrecalentamiento: {int(over.sum())} días")
    print(f"Sequía           : {int(dry.sum())} días")
    print(f"Eventos JSON     : {payload['total_eventos']}  -> {OUT_DIR / 'eventos.json'}")
    print(f"Figuras          : {FIG_DIR}")

    if args.no_mqtt:
        return

    listener_client = None
    received: list[dict] = []
    if args.listen > 0:
        import uuid as _uuid

        try:
            listener_client = _make_client(f"{NODO_ID}-sub-{_uuid.uuid4().hex[:6]}")

            def _on_connect(c, userdata, flags, reason_code, properties=None):
                if int(reason_code) == 0:
                    c.subscribe(TOPIC, qos=1)

            def _on_message(c, userdata, msg):
                try:
                    received.append(json.loads(msg.payload.decode("utf-8")))
                except json.JSONDecodeError:
                    received.append({"raw": msg.payload.decode("utf-8", errors="replace")})

            listener_client.on_connect = _on_connect
            listener_client.on_message = _on_message
            listener_client.connect(BROKER, PORT_PLAIN, 60)
            listener_client.loop_start()
            time.sleep(1.2)
            print(f"MQTT listener    : suscrito a {TOPIC} (captura {args.listen}s)")
        except OSError as exc:
            print(f"MQTT listener    : sin red ({exc})")
            listener_client = None

    try:
        acks = publish_mqtt(events)
        (OUT_DIR / "mqtt_publicacion.json").write_text(
            json.dumps(
                {"broker": BROKER, "topic": TOPIC, "publicados": acks},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"MQTT publicados  : {len(acks)} mensajes QoS1 en {BROKER} {TOPIC}")
    except Exception as exc:
        print(f"MQTT publicación : FALLO ({exc})")
        print("  Reintenta o usa --no-mqtt. El análisis local ya está completo.")
        if listener_client is not None:
            listener_client.loop_stop()
            listener_client.disconnect()
        return

    if listener_client is not None:
        time.sleep(max(1.0, float(args.listen)))
        listener_client.loop_stop()
        listener_client.disconnect()
        (OUT_DIR / "mqtt_recepcion.json").write_text(
            json.dumps(received, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"MQTT recibidos   : {len(received)} (eco de nuestras alertas y/o del aula)")


if __name__ == "__main__":
    main()
