#include <Arduino.h>
#include <DHT.h>

#define DHTPIN 15
#define DHTTYPE DHT22

#define TEMP_MIN 20.0
#define TEMP_MAX 26.0
#define HUM_MIN 40.0
#define HUM_MAX 60.0

#define READ_INTERVAL_MS 5000

DHT dht(DHTPIN, DHTTYPE);

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

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();
  Serial.println("IoT Lab - Data Monitoring");
  Serial.println("DHT22 on GPIO 15 | Comfort: 20-26 C, 40-60 %RH");
}

void loop() {
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  const char *status = classifyStatus(temp, hum);

  if (isnan(temp) || isnan(hum)) {
    Serial.println("T=nan,H=nan,STATUS=SENSOR_ERROR");
  } else {
    Serial.print("T=");
    Serial.print(temp, 1);
    Serial.print(",H=");
    Serial.print(hum, 1);
    Serial.print(",STATUS=");
    Serial.println(status);
  }

  delay(READ_INTERVAL_MS);
}
