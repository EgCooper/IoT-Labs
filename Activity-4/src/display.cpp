/**
 * @file display.cpp
 * @brief Visualización dual: LCD 16x2 (campo) y Serial (laboratorio / depuración).
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include "config.h"
#include "display.h"

static LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);
static bool lcdOk = false;

static void serialLine(const String& text) {
  /* Wokwi / algunos monitores no vuelven a columna 0 con solo '\\n'. */
  Serial.print(text);
  Serial.print("\r\n");
}

void displayBegin() {
  Wire.begin(PIN_SDA, PIN_SCL);
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Nodo urbano IoT");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  lcdOk = true;

  serialLine("");
  serialLine("================================================");
  serialLine("  Nodo urbano IoT  |  ESP32 + Wokwi + PIO");
  serialLine("  Teclas:  1=S1  2=S2  3=S3  0=sensores live");
  serialLine("================================================");
}

const char* controlLabel(const ControlState& state, const SensorData& data) {
  if (!data.dhtValid && !data.usValid && !data.ldrValid) {
    return "FAULT SENSORES";
  }
  if (state.condProximidad && state.condAlertaComb) {
    return "PROX+ALERTA";
  }
  if (state.condProximidad && state.condVentilacion) {
    return "PROX+VENT+PASO";
  }
  if (state.condAlertaComb && state.condVentilacion) {
    return "ALERTA+VENT";
  }
  if (state.condProximidad) {
    return "PROX ALARMA";
  }
  if (state.condAlertaComb) {
    return "ALERTA COMB.";
  }
  if (state.condVentilacion) {
    return "VENT+PASO";
  }
  if (!data.dhtValid) {
    return "OK (DHT FAULT)";
  }
  if (!data.usValid) {
    return "OK (US FAULT)";
  }
  return "OK NORMAL";
}

static void lcdWriteLine(uint8_t row, const char* text) {
  lcd.setCursor(0, row);
  lcd.print("                ");
  lcd.setCursor(0, row);
  lcd.print(text);
}

void displayUpdate(const SensorData& data, const ControlState& state, DemoScenario scenario) {
  char line1[17] = {0};
  char line2[17] = {0};

  if (data.dhtValid) {
    snprintf(line1, sizeof(line1), "T%4.1f H%02.0f L%3d", data.temperatureC, data.humidityPct,
             data.lightIntensity);
  } else {
    snprintf(line1, sizeof(line1), "T---- H-- L%3d", data.lightIntensity);
  }

  const char* label = controlLabel(state, data);
  if (data.usValid) {
    snprintf(line2, sizeof(line2), "D%03.0f %s", data.distanceCm, label);
  } else {
    snprintf(line2, sizeof(line2), "D--- %s", label);
  }

  if (lcdOk) {
    lcdWriteLine(0, line1);
    lcdWriteLine(1, line2);
  }

  serialLine("------------------------------------------------");
  serialLine(String("Modo     : ") + scenarioName(scenario));
  serialLine(String("Luz      : ") + data.lightIntensity + " / 1023  (ADC raw " + data.lightRawAdc +
             ")  LDR=" + (data.ldrValid ? "OK" : "FAULT"));
  if (data.dhtValid) {
    serialLine(String("Clima    : ") + String(data.temperatureC, 1) + " C   humedad " +
               String(data.humidityPct, 1) + " %   DHT=OK");
  } else {
    serialLine("Clima    : DHT=FAULT (C1 y C3 inhibidas)");
  }
  if (data.usValid) {
    serialLine(String("Distancia: ") + String(data.distanceCm, 1) + " cm   US=OK");
  } else {
    serialLine("Distancia: US=FAULT (C2 inhibida)");
  }
  serialLine(String("C1 VENT+PASO     : ") + (state.condVentilacion ? "ON" : "off"));
  serialLine(String("C2 PROXIMIDAD    : ") + (state.condProximidad ? "ON" : "off"));
  serialLine(String("C3 ALERTA COMB.  : ") + (state.condAlertaComb ? "ON" : "off"));
  serialLine(String("Actuadores: R=") + (state.ledRed ? "1" : "0") + " G=" +
             (state.ledGreen ? "1" : "0") + " B=" + (state.ledBlue ? "1" : "0") + "  Buzzer=" +
             (state.buzzer ? "1" : "0") + "  blink=" + (state.blinkPattern ? "1" : "0"));
  serialLine(String("Estado   : ") + label);
}
