#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <math.h>

// --- Configuracion NTC ---
#define NTC_PIN     A0
#define BETA        3950        // coeficiente Beta del NTC
#define R0          10000.0     // resistencia nominal a 25 C (10k ohm)
#define T0          298.15      // 25 C en Kelvin
#define R_FIXED     10000.0     // resistencia del divisor de tension (10k ohm)

// --- LCD I2C: direccion 0x27, 16 columnas, 2 filas ---
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Convierte lectura ADC a temperatura en Celsius usando ecuacion Beta
float leerTemperatura() {
  int adc = analogRead(NTC_PIN);

  // Calcula resistencia del NTC desde divisor de tension
  float resistencia = R_FIXED * (float)adc / (1023.0 - (float)adc);

  // Ecuacion de Steinhart-Hart simplificada (Beta)
  float tempK = 1.0 / (1.0 / T0 + log(resistencia / R0) / BETA);

  return tempK - 273.15; // Kelvin a Celsius
}

void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("  Lab IoT NTC   ");
  lcd.setCursor(0, 1);
  lcd.print(" Iniciando...   ");
  delay(2000);
  lcd.clear();
}

void loop() {
  float temperatura = leerTemperatura();

  // --- Monitor serial ---
  Serial.print("Temperatura: ");
  Serial.print(temperatura, 1);
  Serial.println(" C");

  // --- LCD ---
  lcd.setCursor(0, 0);
  lcd.print("Temperatura:    ");
  lcd.setCursor(0, 1);
  lcd.print(temperatura, 1);
  lcd.print(" C          ");

  delay(2000);
}