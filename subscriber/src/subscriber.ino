/**
 * Suscriptor MQTT - ESP32 (Wokwi)
 *
 * Se suscribe al topico home/hall/temperature1.
 * Muestra el payload en el monitor serial y en un LCD I2C 16x2.
 */
#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

static const char *WIFI_SSID = "Wokwi-GUEST";
static const char *WIFI_PASS = "";

static const char *MQTT_BROKER = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const char *MQTT_TOPIC = "home/hall/temperature1";
static const char *DEVICE_ID = "sub-esp32-hall";

static const int PIN_LED = 2;
static const unsigned long MQTT_RETRY_MS = 3000;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
LiquidCrystal_I2C lcd(0x27, 16, 2);

void imprimirLcd(const char *l1, const char *l2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(l1);
  lcd.setCursor(0, 1);
  lcd.print(l2);
}

void mostrarPayload(const char *mensaje) {
  Serial.printf("[SUB] topic=%s payload=%s\n", MQTT_TOPIC, mensaje);

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, mensaje);
  if (!err) {
    float temp = doc["temp"] | NAN;
    float hum = doc["hum"] | NAN;
    char linea1[17];
    char linea2[17];
    snprintf(linea1, sizeof(linea1), "Temp: %.1f C", temp);
    snprintf(linea2, sizeof(linea2), "Hum:  %.1f %%", hum);
    imprimirLcd(linea1, linea2);
  } else {
    imprimirLcd("MQTT payload", mensaje);
  }

  digitalWrite(PIN_LED, HIGH);
  delay(60);
  digitalWrite(PIN_LED, LOW);
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  char mensaje[192];
  if (length >= sizeof(mensaje)) {
    length = sizeof(mensaje) - 1;
  }
  memcpy(mensaje, payload, length);
  mensaje[length] = '\0';
  mostrarPayload(mensaje);
}

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("[SUB] Conectando WiFi SSID=%s\n", WIFI_SSID);
  imprimirLcd("Conectando", "WiFi...");
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
    Serial.print("[SUB] WiFi OK, IP=");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[SUB] WiFi FALLIDO");
    imprimirLcd("WiFi", "FALLIDO");
  }
}

void conectarMqtt() {
  if (mqtt.connected() || WiFi.status() != WL_CONNECTED) {
    return;
  }

  String clientId = String(DEVICE_ID) + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.printf("[SUB] MQTT %s:%u como %s\n", MQTT_BROKER, MQTT_PORT, clientId.c_str());
  imprimirLcd("Conectando", "MQTT...");

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("[SUB] MQTT OK");
    mqtt.subscribe(MQTT_TOPIC);
    Serial.printf("[SUB] Suscrito a %s\n", MQTT_TOPIC);
    imprimirLcd("Suscrito MQTT", "hall/temp1");
  } else {
    Serial.printf("[SUB] MQTT FALLIDO, rc=%d\n", mqtt.state());
    imprimirLcd("MQTT", "FALLIDO");
  }
}

void setup() {
  Serial.begin(115200);
  delay(400);
  pinMode(PIN_LED, OUTPUT);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(256);

  Serial.println("=== Suscriptor MQTT ESP32 ===");
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
}
