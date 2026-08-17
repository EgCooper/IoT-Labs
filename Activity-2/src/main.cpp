#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";

// CONSUMO ENDPOINT FOR GET DATA 
const char* apiUrl = "https://callback-iot.up.railway.app/data";

#define LED_ROJO   25
#define LED_AZUL   26
#define BUZZER     27

LiquidCrystal_I2C lcd(0x27, 20, 4);

const unsigned long INTERVALO = 5000;
unsigned long ultimaConsulta = 0;

void conectarWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi conectado. IP: ");
  Serial.println(WiFi.localIP());
}

// Estructura para agrupar todos los datos que trae el sensor
struct DatosSensor {
  float temperatura;
  float humedad;
  float presion;
  int bateria;
  int senal;
};

bool obtenerDatosSensor(DatosSensor &datos) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi no conectado.");
    return false;
  }

  HTTPClient http;
  http.begin(apiUrl);
  int httpCode = http.GET();

  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    Serial.println("Respuesta API: " + payload);

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
      Serial.print("Error al parsear JSON: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }

    // La API devuelve un ARRAY: [ { "temperature": 22.8, ... } ]
    // Por eso se accede primero al indice [0] y luego a cada campo.
    JsonObject obj = doc.is<JsonArray>() ? doc[0].as<JsonObject>() : doc.as<JsonObject>();

    datos.temperatura = obj["temperature"] | 0.0;
    datos.humedad     = obj["humidity"]    | 0.0;
    datos.presion     = obj["pressure"]    | 0.0;
    datos.bateria     = obj["battery"]     | 0;
    datos.senal       = obj["signal"]      | 0;

    http.end();
    return true;
  } else {
    Serial.printf("Error HTTP, codigo: %d\n", httpCode);
    http.end();
    return false;
  }
}

void aplicarLogicaControl(const DatosSensor &datos) {
  lcd.clear();

  // Linea 0: Temperatura y Humedad
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(datos.temperatura, 1);
  lcd.print((char)223); // simbolo de grado
  lcd.print("C H:");
  lcd.print(datos.humedad, 1);
  lcd.print("%");

  // Linea 1: Estado segun la logica de control
  lcd.setCursor(0, 1);
  if (datos.temperatura > 30.0) {
    digitalWrite(LED_ROJO, HIGH);
    digitalWrite(LED_AZUL, LOW);
    digitalWrite(BUZZER, HIGH);
    lcd.print("ALERTA: Caliente");
    Serial.println(">> Temp > 30C -> LED ROJO + BUZZER ON");
  } else {
    digitalWrite(LED_ROJO, LOW);
    digitalWrite(LED_AZUL, HIGH);
    digitalWrite(BUZZER, LOW);
    lcd.print("Normal: Frio");
    Serial.println(">> Temp < 30C -> LED AZUL + BUZZER OFF");
  }

  // Linea 2: Presion y Bateria
  lcd.setCursor(0, 2);
  lcd.print("P:");
  lcd.print(datos.presion, 1);
  lcd.print("hPa B:");
  lcd.print(datos.bateria);
  lcd.print("%");

  // Linea 3: Senal WiFi/radio del sensor
  lcd.setCursor(0, 3);
  lcd.print("Senal: ");
  lcd.print(datos.senal);
  lcd.print(" dBm");
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_AZUL, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(LED_AZUL, LOW);
  digitalWrite(BUZZER, LOW);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Iniciando...");

  conectarWiFi();
}

void loop() {
  if (millis() - ultimaConsulta >= INTERVALO) {
    ultimaConsulta = millis();

    DatosSensor datos;
    if (obtenerDatosSensor(datos)) {
      aplicarLogicaControl(datos);
    } else {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Error API");
      Serial.println("No se pudo obtener la temperatura.");
    }
  }
}