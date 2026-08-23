/**
 * ESP32 publicador — Laboratorio 7 Actividad 2
 *
 * Red virtual Wokwi: SSID "Wokwi-GUEST" (sin clave, canal 6) sale a Internet.
 * Publica alertas JSON en test.mosquitto.org → tópico /iot/alertas
 *
 * Seguridad de esta demo: puerto 1883 en claro (laboratorio). En campo
 * usar 8883 + TLS (WiFiClientSecure) y credenciales fuera del firmware.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

static const char* WIFI_SSID = "Wokwi-GUEST";
static const char* WIFI_PASS = "";
static const char* MQTT_HOST = "test.mosquitto.org";
static const uint16_t MQTT_PORT = 1883;
static const char* TOPIC = "/iot/alertas";
static const char* NODO = "esp32-pub-cruce-norte";

static const uint8_t PIN_LED_WIFI = 25;
static const uint8_t PIN_LED_PUB = 26;

WiFiClient net;
PubSubClient mqtt(net);

static uint32_t lastPubMs = 0;
static uint8_t replayIndex = 0;

/** Serie corta que reproduce las dos reglas (el CSV completo vive en Python). */
struct Sample {
  float t;
  float h;
  const char* fecha;
};

static const Sample REPLAY[] = {
    {26.2f, 55.0f, "2026-07-11"},
    {28.5f, 50.0f, "2026-07-12"},
    {30.8f, 48.0f, "2026-07-13"},
    {33.1f, 44.0f, "2026-07-14"},
    {36.8f, 28.0f, "2026-07-17"},
    {38.1f, 24.0f, "2026-07-20"},
};
static const uint8_t REPLAY_N = sizeof(REPLAY) / sizeof(REPLAY[0]);

static void connectWifi() {
  Serial.print("WiFi ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  uint8_t n = 0;
  while (WiFi.status() != WL_CONNECTED && n < 40) {
    delay(400);
    Serial.print('.');
    n++;
  }
  Serial.print("\r\nIP ");
  Serial.println(WiFi.localIP());
  digitalWrite(PIN_LED_WIFI, WiFi.status() == WL_CONNECTED ? HIGH : LOW);
}

static void connectMqtt() {
  while (!mqtt.connected()) {
    String id = String(NODO) + "-" + String((uint32_t)esp_random(), HEX);
    Serial.print("MQTT ");
    Serial.println(id);
    /* Usuario/clave vacíos: puerto público 1883. No usar en producción. */
    if (mqtt.connect(id.c_str())) {
      Serial.println("MQTT conectado (1883, sin TLS)");
    } else {
      Serial.print("rc=");
      Serial.println(mqtt.state());
      delay(2500);
    }
  }
}

static bool publishAlert(const char* tipo, const char* fecha, float t, float h, const char* just) {
  JsonDocument doc;
  doc["nodo_id"] = NODO;
  doc["origen"] = "esp32-wokwi-publisher";
  doc["tipo"] = tipo;
  doc["fecha"] = fecha;
  doc["temperatura_c"] = t;
  doc["humedad_pct"] = h;
  doc["justificacion"] = just;
  doc["topic"] = TOPIC;

  char buf[384];
  const size_t n = serializeJson(doc, buf, sizeof(buf));
  const bool ok = mqtt.publish(TOPIC, buf, n);
  Serial.print(ok ? "PUB OK  " : "PUB FAIL ");
  Serial.println(buf);
  if (ok) {
    digitalWrite(PIN_LED_PUB, HIGH);
    delay(180);
    digitalWrite(PIN_LED_PUB, LOW);
  }
  return ok;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_WIFI, OUTPUT);
  pinMode(PIN_LED_PUB, OUTPUT);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  connectWifi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(PIN_LED_WIFI, LOW);
    connectWifi();
  }
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  if (millis() - lastPubMs < 6000) {
    return;
  }
  lastPubMs = millis();

  const Sample s = REPLAY[replayIndex];
  replayIndex = (replayIndex + 1) % REPLAY_N;

  static float prev2 = NAN;
  static float prev1 = NAN;
  const bool rising3 = !isnan(prev2) && !isnan(prev1) && (s.t > prev1) && (prev1 > prev2) && (s.t >= 28.0f);
  const bool drought = (s.t > 32.0f) && (s.h < 35.0f);

  if (rising3) {
    publishAlert("SOBRECALENTAMIENTO", s.fecha, s.t, s.h, "T en aumento 3 dias (nodo de campo)");
  }
  if (drought) {
    publishAlert("SEQUIA", s.fecha, s.t, s.h, "T alta y H baja (nodo de campo)");
  }
  if (!rising3 && !drought) {
    Serial.printf("Sin alerta  T=%.1f H=%.1f  %s\r\n", s.t, s.h, s.fecha);
  }

  prev2 = prev1;
  prev1 = s.t;
}
