/**
 * @file sensors.h
 * @brief Adquisición y validación de LDR, DHT22 y HC-SR04.
 */

#pragma once

#include "types.h"

void sensorsBegin();

/** Lee LDR (siempre) y ultrasónico. El DHT22 solo se actualiza cada 2 s. */
void sensorsRead(SensorData& data);

/** Fuerza valores de un escenario urbano (validación / demostración). */
void sensorsInjectDemo(SensorData& data, DemoScenario scenario);
