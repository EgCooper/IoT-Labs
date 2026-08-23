/**
 * @file actuators.cpp
 * @brief Salidas con resistencias de 220 Ω en los LED (ver diagram.json).
 *
 * El buzzer usa digitalWrite, no tone()/noTone(). En Arduino-ESP32 esas
 * funciones llaman a LEDC sin setup y Wokwi llena el log con
 * "LEDC is not initialized", lo que además rompe el timing del DHT22.
 */

#include "actuators.h"
#include "config.h"

static uint32_t lastBlinkMs = 0;
static bool blinkOn = true;

void actuatorsBegin() {
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  actuatorsAllOff();
}

void actuatorsAllOff() {
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_BUZZER, LOW);
}

void actuatorsApply(const ControlState& state) {
  const uint32_t now = millis();
  if ((now - lastBlinkMs) >= BLINK_INTERVAL_MS) {
    lastBlinkMs = now;
    blinkOn = !blinkOn;
  }

  const bool gate = state.blinkPattern ? blinkOn : true;

  digitalWrite(PIN_LED_RED, (state.ledRed && gate) ? HIGH : LOW);
  digitalWrite(PIN_LED_GREEN, (state.ledGreen && gate) ? HIGH : LOW);
  digitalWrite(PIN_LED_BLUE, (state.ledBlue && gate) ? HIGH : LOW);
  digitalWrite(PIN_BUZZER, (state.buzzer && gate) ? HIGH : LOW);
}
