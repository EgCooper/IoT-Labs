/**
 * @file control.cpp
 * @brief Lógica condicional urbana con histéresis y prioridad de seguridad.
 *
 * C1  luz < 300 y T > 30 °C     → ventilación (azul) + paso peatonal (verde)
 * C2  distancia < 30 cm         → semáforo rojo + alarma
 * C3  T > 35 °C y H < 40 %      → alerta combinada (los tres LED + buzzer)
 *
 * Prioridad: C2 (colisión inminente) > C3 (emergencia climática) > C1.
 * Las reglas pueden coexistir: un cruce caluroso con un objeto cerca
 * enciende ventilación, paso, rojo y alarma a la vez.
 */

#include "config.h"
#include "control.h"

void controlReset(ControlState& state) {
  state = ControlState{};
}

void controlEvaluate(const SensorData& data, ControlState& state) {
  /* --- C1: anochecer caluroso ------------------------------------------- */
  if (data.ldrValid && data.dhtValid) {
    const int lightExit = LIGHT_DARK_MAX + LIGHT_HYSTERESIS;
    const bool dark = state.condVentilacion
                          ? (data.lightIntensity < lightExit)
                          : (data.lightIntensity < LIGHT_DARK_MAX);
    state.condVentilacion = dark && (data.temperatureC > TEMP_VENT_MIN_C);
  } else {
    /* Fail-safe: sin clima o luz válidos no se activa ventilación. */
    state.condVentilacion = false;
  }

  /* --- C2: proximidad --------------------------------------------------- */
  if (data.usValid) {
    const float exitCm = DIST_ALARM_CM + DIST_HYSTERESIS_CM;
    state.condProximidad = state.condProximidad ? (data.distanceCm < exitCm)
                                                : (data.distanceCm < DIST_ALARM_CM);
  } else {
    /* No se mantiene alarma por un eco perdido (evita sirena continua). */
    state.condProximidad = false;
  }

  /* --- C3: ola de calor seca -------------------------------------------- */
  if (data.dhtValid) {
    state.condAlertaComb = (data.temperatureC > TEMP_ALERT_MIN_C) &&
                           (data.humidityPct < HUM_ALERT_MAX_PCT);
  } else {
    state.condAlertaComb = false;
  }

  /* --- Mapeo a actuadores ----------------------------------------------- */
  state.ledBlue = state.condVentilacion || state.condAlertaComb;
  state.ledGreen = state.condVentilacion || state.condAlertaComb;
  state.ledRed = state.condProximidad || state.condAlertaComb;
  state.buzzer = state.condProximidad || state.condAlertaComb;

  /* Proximidad: luz y tono continuos (máxima atención).
   * Solo C3: patrón intermitente para distinguir la emergencia climática. */
  state.blinkPattern = state.condAlertaComb && !state.condProximidad;
}
