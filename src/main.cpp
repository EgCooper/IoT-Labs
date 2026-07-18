// Using libraries: DHT sensor library, Adafruit Unified Sensor
#include <Arduino.h>
#include <DHT.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// Define the pin and type of DHT sensor
#define DHTPIN 15
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Initialize the DHT sensor
void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // deshabilitar brownout detector
  delay(1000);
  Serial.begin(115200);
  dht.begin();
  Serial.println("=== Lab IoT: ESP32 + DHT22 ===");
}

// Main loop to read and print humidity and temperature values
void loop() {
  delay(2000);

  float humedad     = dht.readHumidity();
  float temperatura = dht.readTemperature();

  if (isnan(humedad) || isnan(temperatura)) {
    Serial.println("Error leyendo el sensor");
    return;
  }

  Serial.print("Humedad: ");
  Serial.print(humedad);
  Serial.println(" %");

  Serial.print("Temperatura: ");
  Serial.print(temperatura);
  Serial.println(" °C");
}