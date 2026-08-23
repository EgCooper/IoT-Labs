/**
 * @file main.cpp
 * @brief Nodo urbano IoT: sensores → control → actuadores + visualización.
 *
 * Flujo: leer entorno, evaluar reglas C1/C2/C3, accionar salidas y mostrar
 * estado. El lazo es cooperativo (millis): no se bloquea en delay(), salvo
 * los microsegundos del pulso ultrasónico.
 *
 * Validación: enviar 1 / 2 / 3 por Serial para los tres escenarios urbanos;
 * 0 vuelve a los sliders de Wokwi.
 */

#include "actuators.h"
#include "config.h"
#include "control.h"
#include "display.h"
#include "sensors.h"

static SensorData gSensors{};
static ControlState gControl{};
static DemoScenario gScenario = DemoScenario::LiveSensors;

static uint32_t lastSampleMs = 0;
static uint32_t lastDisplayMs = 0;

static void pollSerialCommands() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '0') {
      gScenario = DemoScenario::LiveSensors;
      controlReset(gControl);
      Serial.print(F("[CMD] LIVE: sliders Wokwi / sensores fisicos\r\n"));
    } else if (c == '1') {
      gScenario = DemoScenario::DuskHeat;
      controlReset(gControl);
      Serial.print(F("[CMD] Escenario 1: anochecer caluroso (C1)\r\n"));
    } else if (c == '2') {
      gScenario = DemoScenario::NearObject;
      controlReset(gControl);
      Serial.print(F("[CMD] Escenario 2: proximidad en cruce (C2)\r\n"));
    } else if (c == '3') {
      gScenario = DemoScenario::HeatWave;
      controlReset(gControl);
      Serial.print(F("[CMD] Escenario 3: ola de calor seca (C3)\r\n"));
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);

  sensorsBegin();
  actuatorsBegin();
  displayBegin();
  controlReset(gControl);

  lastSampleMs = millis();
  lastDisplayMs = millis();
}

void loop() {
  pollSerialCommands();

  const uint32_t now = millis();

  if ((now - lastSampleMs) >= SAMPLE_INTERVAL_MS) {
    lastSampleMs = now;

    if (gScenario == DemoScenario::LiveSensors) {
      sensorsRead(gSensors);
    } else {
      sensorsInjectDemo(gSensors, gScenario);
    }

    controlEvaluate(gSensors, gControl);
  }

  actuatorsApply(gControl);

  if ((now - lastDisplayMs) >= DISPLAY_INTERVAL_MS) {
    lastDisplayMs = now;
    displayUpdate(gSensors, gControl, gScenario);
  }
}
