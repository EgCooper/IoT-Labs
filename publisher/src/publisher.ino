/**
 * Publicador MQTT - ESP32 (Wokwi)
 * Publica lecturas simuladas de temperatura/humedad
 * al tópico home/hall/temperature1
 */
#include <WiFi.h>
#include <PubSubClient.h>

static const char *WIFI_SSID = "Wokwi-GUEST";
static const char *WIFI_PASS = "";

static const char *MQTT_BROKER = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const char *MQTT_TOPIC = "home/hall/temperature1";
static const char *DEVICE_ID = "pub-esp32-hall";

static const int PIN_LED = 2;
static const unsigned long PUBLISH_MS = 4000;
static const unsigned long MQTT_RETRY_MS = 3000;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
unsigned long lastPublishMs = 0;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("[PUB] Conectando WiFi SSID=%s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint8_t intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 40) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[PUB] WiFi OK, IP=");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[PUB] WiFi FALLIDO");
  }
}

void conectarMqtt() {
  if (mqtt.connected() || WiFi.status() != WL_CONNECTED) {
    return;
  }

  String clientId = String(DEVICE_ID) + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.printf("[PUB] MQTT %s:%u como %s\n", MQTT_BROKER, MQTT_PORT, clientId.c_str());

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("[PUB] MQTT OK");
  } else {
    Serial.printf("[PUB] MQTT FALLIDO, rc=%d\n", mqtt.state());
  }
}

void publicarLectura() {
  // Datos simulados (sensor ficticio): temperatura 18.0–32.9 °C, humedad 35–75 %
  float temperatura = 18.0f + (random(0, 150) / 10.0f);
  float humedad = 35.0f + (random(0, 401) / 10.0f);

  char payload[160];
  snprintf(
      payload,
      sizeof(payload),
      "{\"device\":\"%s\",\"temp\":%.1f,\"hum\":%.1f,\"unit\":\"C\"}",
      DEVICE_ID,
      temperatura,
      humedad);

  bool ok = mqtt.connected() && mqtt.publish(MQTT_TOPIC, payload);
  Serial.printf("[PUB] topic=%s payload=%s result=%s\n", MQTT_TOPIC, payload, ok ? "OK" : "FAIL");

  digitalWrite(PIN_LED, HIGH);
  delay(80);
  digitalWrite(PIN_LED, LOW);
}

void setup() {
  Serial.begin(115200);
  delay(400);
  pinMode(PIN_LED, OUTPUT);
  randomSeed(esp_random());

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setBufferSize(256);

  Serial.println("=== Publicador MQTT ESP32 ===");
  Serial.printf("Broker: %s:%u\n", MQTT_BROKER, MQTT_PORT);
  Serial.printf("Topic:  %s\n", MQTT_TOPIC);

  conectarWiFi();
  conectarMqtt();
}

void loop() {
  conectarWiFi();
  if (!mqtt.connected()) {
    static unsigned long lastMqttTry = 0;
    if (millis() - lastMqttTry >= MQTT_RETRY_MS) {
      lastMqttTry = millis();
      conectarMqtt();
    }
  }
  mqtt.loop();

  if (millis() - lastPublishMs >= PUBLISH_MS) {
    lastPublishMs = millis();
    publicarLectura();
  }
}
