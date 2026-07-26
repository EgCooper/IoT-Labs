#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

#define DHTPIN 15
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// if you use real components change this to your wifi credentials
// also if you use wokwi and platform and you dont have real componentes, 
// you must use the wokwi wifi credentials : ssid : Wokwi-GUEST and password : empty
const char* WIFI_SSID     = "";
const char* WIFI_PASSWORD = "";
// Put your api key from thingspeak
const char* TS_API_KEY    = "";

void conectarWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void enviarThingSpeak(float temperatura, float humedad) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Sin WiFi, reintentando...");
    conectarWiFi();
    return;
  }

  HTTPClient http;
  String url = String("http://api.thingspeak.com/update?api_key=")
             + TS_API_KEY
             + "&field1=" + String(temperatura, 2)
             + "&field2=" + String(humedad, 2);

  Serial.print("GET -> ");
  Serial.println(url);

  http.begin(url);
  int code = http.GET();

  if (code > 0) {
    String body = http.getString();
    Serial.print("HTTP ");
    Serial.print(code);
    Serial.print(" | respuesta: ");
    Serial.println(body);
  } else {
    Serial.print("Error HTTP: ");
    Serial.println(code);
  }

  http.end();
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  delay(1000);
  Serial.begin(115200);
  dht.begin();
  Serial.println("=== Lab IoT: ESP32 + DHT22 + ThingSpeak ===");
  conectarWiFi();
}

void loop() {
  float humedad     = dht.readHumidity();
  float temperatura = dht.readTemperature();

  if (isnan(humedad) || isnan(temperatura)) {
    Serial.println("Error leyendo el sensor");
    delay(2000);
    return;
  }

  Serial.print("Humedad: ");
  Serial.print(humedad);
  Serial.println(" %");

  Serial.print("Temperatura: ");
  Serial.print(temperatura);
  Serial.println(" °C");

  enviarThingSpeak(temperatura, humedad);

  delay(16000);
}