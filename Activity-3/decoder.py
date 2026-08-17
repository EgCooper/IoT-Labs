"""
Decodificador de telemetría IoT (hexData).

Consulta el endpoint público, filtra objetos con hexData y convierte
los primeros 12 bytes en tres float32 little-endian:
temperatura, humedad y presión.
"""

from __future__ import annotations

import json
import struct
import sys
import urllib.error
import urllib.request
from typing import Any

ENDPOINT_URL = "https://mpab3475e4567ee98b2d.free.beeceptor.com/data"
TIMEOUT_S = 12
PAYLOAD_BYTES = 12  # 3 x float32
USER_AGENT = "IoT-Labs-L6-A3-decoder/1.0"


class DecodeError(Exception):
    """Error de payload hexData (formato o longitud)."""


def fetch_payload(url: str = ENDPOINT_URL) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        raw = response.read().decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"La respuesta no es JSON válido: {exc}") from exc


def as_record_list(payload: Any) -> list[dict[str, Any]]:
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


def records_with_hexdata(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("hexData")]


def decode_hexdata(hex_data: str) -> tuple[float, float, float]:
    cleaned = "".join(str(hex_data).split())
    try:
        raw = bytes.fromhex(cleaned)
    except ValueError as exc:
        raise DecodeError(f"hexData no es hexadecimal válido: {hex_data!r}") from exc

    if len(raw) < PAYLOAD_BYTES:
        raise DecodeError(
            f"hexData tiene {len(raw)} bytes; se necesitan al menos {PAYLOAD_BYTES}"
        )

    temperatura, humedad, presion = struct.unpack_from("<fff", raw, 0)
    return temperatura, humedad, presion


def format_record(record: dict[str, Any]) -> str:
    hex_data = record["hexData"]
    temperatura, humedad, presion = decode_hexdata(hex_data)
    return "\n".join(
        [
            f"Dispositivo : {record.get('device', '-')}",
            f"Estado      : {record.get('status', '-')}",
            f"Timestamp   : {record.get('timestamp', '-')}",
            f"hexData     : {hex_data}",
            f"Temperatura : {temperatura:.2f} °C",
            f"Humedad     : {humedad:.2f} %",
            f"Presión     : {presion:.2f} hPa",
        ]
    )


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> int:
    _configure_stdout()
    try:
        payload = fetch_payload()
    except urllib.error.HTTPError as exc:
        print(f"Error HTTP {exc.code} al consultar {ENDPOINT_URL}: {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"No se pudo consultar {ENDPOINT_URL}: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"Timeout al consultar {ENDPOINT_URL}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    records = records_with_hexdata(as_record_list(payload))
    if not records:
        print("No hay objetos con el campo hexData.", file=sys.stderr)
        return 1

    blocks: list[str] = []
    failed = False
    for index, record in enumerate(records, start=1):
        try:
            blocks.append(format_record(record))
        except DecodeError as exc:
            failed = True
            print(f"Registro {index}: {exc}", file=sys.stderr)

    if blocks:
        print("\n\n".join(blocks))

    return 1 if failed and not blocks else 0


if __name__ == "__main__":
    sys.exit(main())
