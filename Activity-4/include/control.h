/**
 * @file control.h
 * @brief Motor de reglas: condiciones urbanas → actuadores.
 */

#pragma once

#include "types.h"

void controlReset(ControlState& state);

/**
 * Evalúa C1, C2 y C3 con histéresis y fail-safe.
 * Una lectura inválida no dispara la regla asociada.
 */
void controlEvaluate(const SensorData& data, ControlState& state);
