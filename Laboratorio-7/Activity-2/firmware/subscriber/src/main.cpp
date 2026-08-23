/**
 * ESP32 suscriptor — Laboratorio 7 Actividad 2
 *
 * Se une a Wokwi-GUEST, se suscribe a /iot/alertas y actúa:
 *   SOBRECALENTAMIENTO → LED rojo + LCD
 *   SEQUIA             → LED naranja + LCD
 *
 * Recibe publicaciones del script Python o del ESP32 publicador.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

static const char* WIFI_SSID = "Wokwi-GUEST";
static const char* WIFI_PASS = "";
static const char* MQTT_HOST = "test.mosquitto.org";
static const uint16_t MQTT_PORT = 1883;
static const char* TOPIC = "/iot/alertas";
static const char* NODO = "esp32-sub-actuador";

static const uint8_t PIN_LED_MQTT = 25;
static const uint8_t PIN_LED_HOT = 26;
static const uint8_t PIN_LED_DRY = 27;

WiFiClient net;
PubSubClient mqtt(net);
LiquidCrystal_I2C lcd(0x27, 16, 2);

static uint32_t lastActMs = 0;
static bool showHot = false;
static bool showDry = false;

static void showLcd(const char* l1, const char* l2) {
  lcd.setCursor(0, 0);
  lcd.print("                ");
  lcd.setCursor(0, 0);
  lcd.print(l1);
  lcd.setCursor(0, 1);
  lcd.print("                ");
  lcd.setCursor(0, 1);
  lcd.print(l2);
}

static void applyAlert(const char* tipo, const char* fecha) {
  lastActMs = millis();
  if (strcmp(tipo, "SOBRECALENTAMIENTO") == 0) {
    showHot = true;
    showDry = false;
    digitalWrite(PIN_LED_HOT, HIGH);
    digitalWrite(PIN_LED_DRY, LOW);
    showLcd("SOBRECALOR", fecha);
  } else if (strcmp(tipo, "SEQUIA") == 0) {
    showDry = true;
    showHot = false;
    digitalWrite(PIN_LED_DRY, HIGH);
    digitalWrite(PIN_LED_HOT, LOW);
    showLcd("SEQUIA", fecha);
  } else {
    showLcd("ALERTA", tipo);
  }
}

static void onMessage(char* topic, byte* payload, unsigned int length) {
  char buf[400];
  if (length >= sizeof(buf)) {
    length = sizeof(buf) - 1;
  }
  memcpy(buf, payload, length);
  buf[length] = 0;

  Serial.print("RX ");
  Serial.print(topic);
  Serial.print(" ");
  Serial.println(buf);

  JsonDocument doc;
  const DeserializationError err = deserializeJson(doc, buf);
  if (err) {
    Serial.println("JSON invalido");
    return;
  }
  const char* tipo = doc["tipo"] | "?";
  const char* fecha = doc["fecha"] | "";
  applyAlert(tipo, fecha);
}

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
}

static void connectMqtt() {
  while (!mqtt.connected()) {
    String id = String(NODO) + "-" + String((uint32_t)esp_random(), HEX);
    Serial.print("MQTT ");
    Serial.println(id);
    if (mqtt.connect(id.c_str())) {
      mqtt.subscribe(TOPIC, 1);
      digitalWrite(PIN_LED_MQTT, HIGH);
      showLcd("MQTT OK", TOPIC);
      Serial.println("suscrito a /iot/alertas");
    } else {
      digitalWrite(PIN_LED_MQTT, LOW);
      Serial.print("rc=");
      Serial.println(mqtt.state());
      delay(2500);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_MQTT, OUTPUT);
  pinMode(PIN_LED_HOT, OUTPUT);
  pinMode(PIN_LED_DRY, OUTPUT);
  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  showLcd("Suscriptor IoT", "conectando...");
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setCallback(onMessage);
  connectWifi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }
  if (!mqtt.connected()) {
    digitalWrite(PIN_LED_MQTT, LOW);
    connectMqtt();
  }
  mqtt.loop();

  /* Apaga LEDs de alerta a los 8 s si no llega otra. */
  if ((showHot || showDry) && (millis() - lastActMs > 8000)) {
    showHot = false;
    showDry = false;
    digitalWrite(PIN_LED_HOT, LOW);
    digitalWrite(PIN_LED_DRY, LOW);
    showLcd("Esperando", "/iot/alertas");
  }
}
