/**
 * @file types.h
 * @brief Tipos compartidos: lecturas, estado de control y modo de demostración.
 */

#pragma once

#include <Arduino.h>

/** Lecturas crudas ya validadas. Si un flag es false, el campo no se usa. */
struct SensorData {
  int lightIntensity;   /**< 0 = oscuridad, 1023 = máxima luz. */
  int lightRawAdc;      /**< ADC 12 bit (diagnóstico). */
  float temperatureC;
  float humidityPct;
  float distanceCm;
  bool ldrValid;
  bool dhtValid;
  bool usValid;
};

/** Resultado del motor de reglas (entradas → decisiones). */
struct ControlState {
  bool condVentilacion;   /**< C1: luz baja y temperatura alta. */
  bool condProximidad;    /**< C2: objeto a < 30 cm. */
  bool condAlertaComb;    /**< C3: calor extremo y aire seco. */
  bool ledRed;
  bool ledGreen;
  bool ledBlue;
  bool buzzer;
  bool blinkPattern;      /**< true: alerta combinada sin proximidad (intermitente). */
};

enum class DemoScenario : uint8_t {
  LiveSensors = 0,   /**< Lecturas reales / sliders de Wokwi. */
  DuskHeat = 1,      /**< Anochecer caluroso: C1. */
  NearObject = 2,    /**< Proximidad en cruce: C2. */
  HeatWave = 3,      /**< Ola de calor seca: C3. */
};

inline const char* scenarioName(DemoScenario s) {
  switch (s) {
    case DemoScenario::DuskHeat:
      return "S1 Anochecer caluroso";
    case DemoScenario::NearObject:
      return "S2 Proximidad en cruce";
    case DemoScenario::HeatWave:
      return "S3 Ola de calor seca";
    default:
      return "LIVE (sensores)";
  }
}
