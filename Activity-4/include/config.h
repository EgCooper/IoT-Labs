/**
 * @file config.h
 * @brief Pines, umbrales y temporización del nodo urbano.
 *
 * Centralizar constantes permite escalar el sistema (otro cruce, otra ciudad)
 * sin reescribir la lógica de control. Los GPIO evitan pines solo-entrada
 * en salidas y reservan ADC1 para el LDR.
 */

#pragma once

#include <Arduino.h>

/* -------------------------------------------------------------------------- */
/* Pines ESP32 DevKit C V4                                                    */
/* -------------------------------------------------------------------------- */
constexpr uint8_t PIN_DHT = 4;       /**< DHT22 datos (bidireccional). */
constexpr uint8_t PIN_LDR = 34;      /**< LDR AO — GPIO ADC1, solo entrada. */
constexpr uint8_t PIN_TRIG = 5;      /**< HC-SR04 disparo. */
constexpr uint8_t PIN_ECHO = 18;     /**< HC-SR04 eco (en hardware real: divisor 5 V → 3,3 V). */
constexpr uint8_t PIN_LED_RED = 25;  /**< Semáforo / detención. */
constexpr uint8_t PIN_LED_GREEN = 26;/**< Paso peatonal. */
constexpr uint8_t PIN_LED_BLUE = 27; /**< Ventilación. */
constexpr uint8_t PIN_BUZZER = 14;   /**< Alarma sonora. */
constexpr uint8_t PIN_SDA = 21;      /**< I2C SDA (LCD). */
constexpr uint8_t PIN_SCL = 22;      /**< I2C SCL (LCD). */

constexpr uint8_t LCD_I2C_ADDR = 0x27;
constexpr uint8_t LCD_COLS = 16;
constexpr uint8_t LCD_ROWS = 2;

/* -------------------------------------------------------------------------- */
/* Umbrales del enunciado (ajustables sin tocar el motor de reglas)           */
/* -------------------------------------------------------------------------- */
constexpr int LIGHT_DARK_MAX = 300;       /**< Intensidad de luz (0–1023). Oscuro si < 300. */
constexpr int LIGHT_HYSTERESIS = 50;      /**< Evita parpadeo en el umbral de luz. */
constexpr float TEMP_VENT_MIN_C = 30.0f;  /**< Temperatura para ventilación + paso. */
constexpr float TEMP_ALERT_MIN_C = 35.0f; /**< Temperatura de alerta combinada. */
constexpr float HUM_ALERT_MAX_PCT = 40.0f;/**< Humedad baja de alerta combinada. */
constexpr float DIST_ALARM_CM = 30.0f;    /**< Proximidad crítica. */
constexpr float DIST_HYSTERESIS_CM = 5.0f;/**< Sale de alarma a 35 cm. */

/* -------------------------------------------------------------------------- */
/* Validación de rangos (fail-safe: lectura fuera de rango = inválida)        */
/* -------------------------------------------------------------------------- */
constexpr float TEMP_ABS_MIN_C = -20.0f;
constexpr float TEMP_ABS_MAX_C = 80.0f;
constexpr float HUM_ABS_MIN_PCT = 0.0f;
constexpr float HUM_ABS_MAX_PCT = 100.0f;
constexpr float DIST_ABS_MIN_CM = 2.0f;
constexpr float DIST_ABS_MAX_CM = 400.0f;
constexpr int LIGHT_ABS_MIN = 0;
constexpr int LIGHT_ABS_MAX = 1023;

/* -------------------------------------------------------------------------- */
/* Temporización (millis, no delay en el lazo principal)                      */
/* -------------------------------------------------------------------------- */
constexpr uint32_t DHT_INTERVAL_MS = 2000;     /**< DHT22 no admite lecturas más rápidas. */
constexpr uint32_t SAMPLE_INTERVAL_MS = 200;   /**< LDR + ultrasónico + control. */
constexpr uint32_t DISPLAY_INTERVAL_MS = 400;  /**< LCD + Serial. */
constexpr uint32_t BLINK_INTERVAL_MS = 250;    /**< Patrón de alerta combinada. */
constexpr uint32_t US_TIMEOUT_US = 30000;      /**< ~5 m; evita bloqueo si no hay eco. */
constexpr uint32_t SERIAL_BAUD = 115200;

constexpr uint8_t ADC_BITS = 12; /**< ESP32 ADC nativo. */
constexpr uint16_t ADC_MAX = 4095;
