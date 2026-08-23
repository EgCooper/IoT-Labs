"""
Genera un CSV diario de temperatura y humedad (45 días) con dos
episodios claros: una racha de calor creciente y una sequía (T alta + H baja).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
OUT = Path(__file__).resolve().parent.parent / "data" / "clima_historico.csv"


def build_series() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    start = pd.Timestamp("2026-07-01")
    n = 45
    fechas = pd.date_range(start, periods=n, freq="D")

    # Perfil base (sin ruido) pensado para disparar las reglas.
    t_base = np.array(
        [
            25.1, 24.8, 25.5, 26.0, 25.2, 24.9, 25.8, 26.1, 25.4, 25.0,  # normal
            26.2, 28.5, 30.8, 33.1, 35.0, 36.4,  # racha creciente (sobrecalentamiento)
            36.8, 37.2, 35.5, 38.1, 37.6, 36.9,  # calor seco (sequía)
            31.0, 28.2, 25.1, 23.0, 22.5, 23.1, 24.0,  # enfriamiento húmedo
            24.5, 27.0, 29.8, 32.4, 34.6, 36.1, 37.0,  # segunda racha + sequía
            33.0, 30.2, 28.4, 27.1, 26.5, 26.8, 27.2, 26.9, 27.0,  # estabilización
        ],
        dtype=float,
    )
    h_base = np.array(
        [
            62, 65, 60, 58, 64, 67, 61, 59, 63, 66,
            55, 50, 48, 44, 40, 38,
            32, 28, 30, 24, 26, 29,
            58, 70, 78, 80, 75, 72, 68,
            60, 52, 45, 38, 31, 27, 25,
            40, 48, 55, 60, 62, 58, 61, 59, 60,
        ],
        dtype=float,
    )

    ruido_t = rng.normal(0, 0.12, n)
    ruido_h = rng.normal(0, 0.6, n)

    df = pd.DataFrame(
        {
            "fecha": fechas.strftime("%Y-%m-%d"),
            "temperatura_c": np.round(t_base + ruido_t, 2),
            "humedad_pct": np.round(np.clip(h_base + ruido_h, 5, 95), 1),
            "estacion": "Cruce-Norte",
        }
    )
    return df


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = build_series()
    df.to_csv(OUT, index=False)
    print(f"CSV escrito: {OUT}  ({len(df)} filas)")


if __name__ == "__main__":
    main()
