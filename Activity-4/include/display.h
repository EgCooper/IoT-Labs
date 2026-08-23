/**
 * @file display.h
 * @brief LCD 16x2 I2C y monitor serial (valores + estado del sistema).
 */

#pragma once

#include "types.h"

void displayBegin();

void displayUpdate(const SensorData& data, const ControlState& state, DemoScenario scenario);

/** Etiqueta corta (máx. 16 caracteres) para el LCD. */
const char* controlLabel(const ControlState& state, const SensorData& data);
