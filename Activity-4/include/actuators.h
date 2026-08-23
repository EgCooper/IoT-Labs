/**
 * @file actuators.h
 * @brief LEDs (rojo, verde, azul) y buzzer.
 */

#pragma once

#include "types.h"

void actuatorsBegin();

/** Aplica el estado. Si blinkPattern, conmuta cada BLINK_INTERVAL_MS. */
void actuatorsApply(const ControlState& state);

void actuatorsAllOff();
