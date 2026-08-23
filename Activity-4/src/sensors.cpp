/**
 * @file sensors.cpp
 * @brief Lectura segura: rangos, timeouts y cadencia del DHT22.
 */

#include <DHTesp.h>

#include "config.h"
#include "sensors.h"

static DHTesp dht;
static SensorData lastValid = {};
static uint32_t lastDhtMs = 0;
static uint32_t lastDhtErrorMs = 0;

void sensorsBegin() {
  analogReadResolution(ADC_BITS);
  analogSetPinAttenuation(PIN_LDR, ADC_11db); /* 0–3,3 V */

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  dht.setup(PIN_DHT, DHTesp::DHT22);
  /* El DHT22 necesita ~2 s tras el encendido; no leer en el primer ciclo. */
  lastDhtMs = millis();
}

/**
 * El módulo LDR de Wokwi entrega más voltaje en oscuridad.
 * Se invierte a una intensidad 0–1023 (mayor = más luz) para que
 * el umbral "< 300" coincida con "poca luz" del enunciado.
 */
static int readLightIntensity(int& rawOut) {
  rawOut = analogRead(PIN_LDR);
  const int intensity = constrain(map(rawOut, 0, ADC_MAX, LIGHT_ABS_MAX, LIGHT_ABS_MIN),
                                  LIGHT_ABS_MIN, LIGHT_ABS_MAX);
  return intensity;
}

static float readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  const unsigned long duration = pulseIn(PIN_ECHO, HIGH, US_TIMEOUT_US);
  if (duration == 0) {
    return -1.0f;
  }
  /* pulseIn(us) / 58 ≈ cm (datasheet HC-SR04). */
  return static_cast<float>(duration) / 58.0f;
}

static bool inRange(float value, float minV, float maxV) {
  return !isnan(value) && value >= minV && value <= maxV;
}

void sensorsRead(SensorData& data) {
  data = lastValid;

  int raw = 0;
  data.lightIntensity = readLightIntensity(raw);
  data.lightRawAdc = raw;
  data.ldrValid = (data.lightIntensity >= LIGHT_ABS_MIN && data.lightIntensity <= LIGHT_ABS_MAX);

  const float cm = readDistanceCm();
  if (inRange(cm, DIST_ABS_MIN_CM, DIST_ABS_MAX_CM)) {
    data.distanceCm = cm;
    data.usValid = true;
  } else {
    data.usValid = false;
  }

  const uint32_t now = millis();
  if ((now - lastDhtMs) >= DHT_INTERVAL_MS) {
    lastDhtMs = now;
    const TempAndHumidity th = dht.getTempAndHumidity();
    const bool okTemp = inRange(th.temperature, TEMP_ABS_MIN_C, TEMP_ABS_MAX_C);
    const bool okHum = inRange(th.humidity, HUM_ABS_MIN_PCT, HUM_ABS_MAX_PCT);

    /* En Wokwi getStatus() a veces no es ERROR_NONE aunque T/H sean válidos. */
    if (okTemp && okHum) {
      data.temperatureC = th.temperature;
      data.humidityPct = th.humidity;
      data.dhtValid = true;
    } else {
      data.dhtValid = false;
      if ((now - lastDhtErrorMs) >= 5000) {
        lastDhtErrorMs = now;
        Serial.print(F("[DHT] lectura invalida: "));
        Serial.println(dht.getStatusString());
      }
    }
  }

  lastValid = data;
}

void sensorsInjectDemo(SensorData& data, DemoScenario scenario) {
  data.ldrValid = true;
  data.dhtValid = true;
  data.usValid = true;
  data.lightRawAdc = 0;

  switch (scenario) {
    case DemoScenario::DuskHeat:
      /* Luz < 300 y T > 30 °C; distancia segura; humedad normal. */
      data.lightIntensity = 180;
      data.temperatureC = 32.5f;
      data.humidityPct = 55.0f;
      data.distanceCm = 150.0f;
      break;
    case DemoScenario::NearObject:
      /* Distancia < 30 cm; clima y luz fuera de C1/C3. */
      data.lightIntensity = 700;
      data.temperatureC = 24.0f;
      data.humidityPct = 60.0f;
      data.distanceCm = 18.0f;
      break;
    case DemoScenario::HeatWave:
      /* T > 35 °C y H < 40 %; sin proximidad. */
      data.lightIntensity = 650;
      data.temperatureC = 37.2f;
      data.humidityPct = 28.0f;
      data.distanceCm = 200.0f;
      break;
    default:
      break;
  }
}
