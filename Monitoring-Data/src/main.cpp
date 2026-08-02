#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ---- Hardware ----
#define DHTPIN 15
#define DHTTYPE DHT22

// ---- Comfort range ----
#define TEMP_MIN 20.0
#define TEMP_MAX 26.0
#define HUM_MIN 40.0
#define HUM_MAX 60.0

// ---- Timing ----
#define READ_INTERVAL_MS 5000
#define WIFI_RETRY_MS 500
#define MQTT_RETRY_MS 3000

// ---- Network (Wokwi: Wokwi-GUEST / empty password) ----
static const char *WIFI_SSID = "Wokwi-GUEST";
static const char *WIFI_PASS = "";

static const char *MQTT_BROKER = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const char *MQTT_TOPIC = "iot/labs/monitoring-data/telemetry";
static const char *DEVICE_ID = "lab-01";

DHT dht(DHTPIN, DHTTYPE);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

const char *classifyStatus(float temp, float hum) {
  if (isnan(temp) || isnan(hum)) {
    return "SENSOR_ERROR";
  }
  if (temp < TEMP_MIN) {
    return "TEMP_LOW";
  }
  if (temp > TEMP_MAX) {
    return "TEMP_HIGH";
  }
  if (hum < HUM_MIN) {
    return "HUM_LOW";
  }
  if (hum > HUM_MAX) {
    return "HUM_HIGH";
  }
  return "OK";
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("Connecting WiFi SSID=%s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint8_t attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(WIFI_RETRY_MS);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK, IP=");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi FAILED");
  }
}

void connectMqtt() {
  if (mqtt.connected()) {
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  String clientId = String("esp32-") + DEVICE_ID + "-" + String(random(0xffff), HEX);
  Serial.printf("Connecting MQTT %s:%u as %s\n", MQTT_BROKER, MQTT_PORT, clientId.c_str());

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("MQTT OK");
  } else {
    Serial.printf("MQTT FAILED, rc=%d\n", mqtt.state());
  }
}

bool publishTelemetry(float temp, float hum, const char *status) {
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  if (isnan(temp) || isnan(hum)) {
    doc["temp"] = nullptr;
    doc["hum"] = nullptr;
  } else {
    doc["temp"] = round(temp * 10.0) / 10.0;
    doc["hum"] = round(hum * 10.0) / 10.0;
  }
  doc["status"] = status;
  doc["ts"] = (uint32_t)(millis() / 1000);

  char payload[256];
  serializeJson(doc, payload, sizeof(payload));
  Serial.println(payload);

  if (!mqtt.connected()) {
    return false;
  }
  return mqtt.publish(MQTT_TOPIC, payload);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  randomSeed(esp_random());

  dht.begin();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setBufferSize(512);

  Serial.println("IoT Lab - Data Monitoring");
  Serial.println("DHT22 GPIO15 | Comfort 20-26C / 40-60%RH");
  Serial.printf("MQTT topic: %s\n", MQTT_TOPIC);

  connectWiFi();
  connectMqtt();
}

void loop() {
  connectWiFi();
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  const char *status = classifyStatus(temp, hum);

  publishTelemetry(temp, hum, status);

  delay(READ_INTERVAL_MS);
}
