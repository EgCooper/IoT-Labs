// Monitor ambiental de invernadero (cooperativa)
// Lee temperatura (TMP36) y humedad de suelo (potenciómetro = sensor analogico),
// compara contra umbrales y avisa con LEDs + LCD. MQTT es extra: publica el estado.

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

// --- Pines ---
#define PIN_TMP36      34   // ADC1, solo entrada. TMP36 VOUT
#define PIN_SUELO      35   // ADC1. Sensor analogico de suelo
#define PIN_LED_VERDE  25   // todo en rango
#define PIN_LED_AMAR   26   // problema de temperatura
#define PIN_LED_AZUL   27   // problema de suelo
#define PIN_LED_ROJO   13   // critico / los dos mal
#define PIN_BUZZER     12
#define PIN_BTN_SILENC 14
#define PIN_LED_MQTT    2   // onboard: MQTT conectado

// --- Umbrales (los puse pensando en tomate / lechuga de invernadero) ---
const float TEMP_OPT_MIN   = 20.0;  // C
const float TEMP_OPT_MAX   = 25.0;
const float TEMP_CRIT_MIN  = 12.0;  // frio que ya daña
const float TEMP_CRIT_MAX  = 32.0;  // calor fuerte

const int SUELO_OPT_MIN    = 60;    // %
const int SUELO_OPT_MAX    = 80;
const int SUELO_SECO_CRIT  = 30;    // casi polvo, hay que regar ya

// WiFi de Wokwi (en hardware real iria el SSID del invernadero)
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";
const int   WIFI_CH   = 6;

#define NS "/invernadero"
const char* MQTT_HOST    = "c287e7e3a5b74342a4db805cf2247e3e.s1.eu.hivemq.cloud";
const uint16_t MQTT_PORT = 8883;
const char* TOPIC_ESTADO = NS "/panel/estado";
const char* MQTT_USER    = "cooper";
const char* MQTT_PASS    = "12345678";

WiFiClientSecure net;
PubSubClient mqtt(net);
LiquidCrystal_I2C lcd(0x27, 16, 2);

enum Estado { OPTIMO, ADVERTENCIA, CRITICO };

Estado estadoTemp  = OPTIMO;
Estado estadoSuelo = OPTIMO;
float  tempC = 22.0;
int    sueloPct = 70;
bool   silenciada = false;
bool   ledRojoOn = false;
bool   beepOn = false;
bool   buzzerListo = false;
bool   buzzerSonando = false;

unsigned long tLeds = 0, tLcd = 0, tMqtt = 0, tReconnect = 0, tBeep = 0, tSerial = 0;

const char* nombreEstado(Estado e) {
  if (e == OPTIMO) return "OK";
  if (e == ADVERTENCIA) return "ADV";
  return "CRIT";
}

// Promedio porque el ADC del ESP32 es ruidoso
int leerADC(int pin) {
  long acc = 0;
  for (int i = 0; i < 8; i++) acc += analogRead(pin);
  return (int)(acc / 8);
}

// TMP36: 0.5 V = 0 C, 10 mV por grado. VCC a 3.3 V (ESP32).
float leerTemperatura() {
  float v = leerADC(PIN_TMP36) * 3.3f / 4095.0f;
  return (v - 0.5f) * 100.0f;
}

// En Wokwi el pote simula el sensor de suelo (0 = seco, 100 = empapado)
int leerSueloPct() {
  int pct = map(leerADC(PIN_SUELO), 0, 4095, 0, 100);
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return pct;
}

Estado clasificarTemp(float t) {
  if (t < TEMP_CRIT_MIN || t > TEMP_CRIT_MAX) return CRITICO;
  if (t < TEMP_OPT_MIN || t > TEMP_OPT_MAX) return ADVERTENCIA;
  return OPTIMO;
}

Estado clasificarSuelo(int pct) {
  if (pct < SUELO_SECO_CRIT) return CRITICO;
  if (pct < SUELO_OPT_MIN || pct > SUELO_OPT_MAX) return ADVERTENCIA;
  return OPTIMO;
}

// Critico combinado: los dos fuera de optimo, o uno ya en critico
bool alertaCombinada() {
  bool tempMal  = estadoTemp  != OPTIMO;
  bool sueloMal = estadoSuelo != OPTIMO;
  bool algunoCrit = (estadoTemp == CRITICO) || (estadoSuelo == CRITICO);
  return (tempMal && sueloMal) || algunoCrit;
}

void buzzerInit() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUZZER, 2000, 8);
  ledcWriteTone(PIN_BUZZER, 0);
#else
  ledcSetup(0, 2000, 8);
  ledcAttachPin(PIN_BUZZER, 0);
  ledcWriteTone(0, 0);
#endif
  buzzerListo = true;
  buzzerSonando = false;
}

void buzzerOn(uint32_t freq) {
  if (!buzzerListo) return;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteTone(PIN_BUZZER, freq);
#else
  ledcWriteTone(0, freq);
#endif
  buzzerSonando = true;
}

void buzzerOff() {
  if (!buzzerListo || !buzzerSonando) {
    digitalWrite(PIN_BUZZER, LOW);
    return;
  }
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteTone(PIN_BUZZER, 0);
#else
  ledcWriteTone(0, 0);
#endif
  digitalWrite(PIN_BUZZER, LOW);
  buzzerSonando = false;
}

void lcdLinea(uint8_t fila, const String& txt) {
  lcd.setCursor(0, fila);
  String s = txt;
  while (s.length() < 16) s += ' ';
  lcd.print(s.substring(0, 16));
}

void actualizarLeds() {
  bool todoOk = (estadoTemp == OPTIMO) && (estadoSuelo == OPTIMO);
  bool combo  = alertaCombinada();

  digitalWrite(PIN_LED_VERDE, todoOk ? HIGH : LOW);
  digitalWrite(PIN_LED_AMAR,  estadoTemp  != OPTIMO ? HIGH : LOW);
  digitalWrite(PIN_LED_AZUL,  estadoSuelo != OPTIMO ? HIGH : LOW);

  // Rojo parpadea solo en la alerta combinada / critica
  if (!combo) {
    digitalWrite(PIN_LED_ROJO, LOW);
    ledRojoOn = false;
    if (!silenciada) buzzerOff();
    return;
  }

  if (millis() - tLeds > 400) {
    tLeds = millis();
    ledRojoOn = !ledRojoOn;
    digitalWrite(PIN_LED_ROJO, ledRojoOn ? HIGH : LOW);
  }

  if (silenciada) {
    buzzerOff();
    return;
  }
  if (millis() - tBeep > 300) {
    tBeep = millis();
    beepOn = !beepOn;
    if (beepOn) buzzerOn(2000);
    else        buzzerOff();
  }
}

void refrescarLcd() {
  if (millis() - tLcd < 400) return;
  tLcd = millis();

  char l0[17], l1[17];
  snprintf(l0, sizeof(l0), "T:%4.1fC %s", tempC, nombreEstado(estadoTemp));
  snprintf(l1, sizeof(l1), "H:%3d%%  %s", sueloPct, nombreEstado(estadoSuelo));
  lcdLinea(0, l0);
  lcdLinea(1, l1);
}

void leerBoton() {
  static bool ultimo = HIGH;
  static unsigned long tDeb = 0;
  bool lectura = digitalRead(PIN_BTN_SILENC);
  if (lectura != ultimo && millis() - tDeb > 50) {
    tDeb = millis();
    ultimo = lectura;
    if (lectura == LOW && alertaCombinada()) {
      silenciada = true;
      buzzerOff();
      Serial.println("Buzzer silenciado (el LED rojo sigue)");
    }
  }
}

void conectarWifi() {
  lcdLinea(0, "Conectando WiFi");
  lcdLinea(1, WIFI_SSID);
  Serial.print("[WiFi] ");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CH);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 8000) {
    delay(200);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf(" OK %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println(" sin red (el monitor local sigue)");
  }
}

void conectarMqtt() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (millis() - tReconnect < 4000) return;
  tReconnect = millis();
  String id = "invernadero-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.print("[MQTT] ");
  if (mqtt.connect(id.c_str(), MQTT_USER, MQTT_PASS, TOPIC_ESTADO, 1, true, "{\"nodo\":\"offline\"}")) {
    Serial.println("OK");
    mqtt.publish(TOPIC_ESTADO, "{\"nodo\":\"online\"}", true);
  } else {
    Serial.printf("fallo rc=%d\n", mqtt.state());
  }
}

void publicarEstado() {
  if (!mqtt.connected()) return;
  if (millis() - tMqtt < 5000) return;
  tMqtt = millis();

  StaticJsonDocument<192> doc;
  doc["temp"] = tempC;
  doc["suelo"] = sueloPct;
  doc["temp_est"] = nombreEstado(estadoTemp);
  doc["suelo_est"] = nombreEstado(estadoSuelo);
  doc["alerta"] = alertaCombinada();
  char buf[192];
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_ESTADO, buf);
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_AMAR, OUTPUT);
  pinMode(PIN_LED_AZUL, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_LED_MQTT, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_BTN_SILENC, INPUT_PULLUP);
  analogSetAttenuation(ADC_11db);  // 0 .. ~3.3 V en el ADC
  analogReadResolution(12);
  buzzerInit();

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  Serial.println("\n=== MONITOR INVERNADERO ===");
  Serial.printf("Temp optimo %.0f-%.0f C | suelo %d-%d %%\n",
                TEMP_OPT_MIN, TEMP_OPT_MAX, SUELO_OPT_MIN, SUELO_OPT_MAX);

  conectarWifi();
  net.setInsecure();  // prototipo Wokwi: no valido el cert de HiveMQ
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setKeepAlive(30);
}

void loop() {
  // 1) sensores
  tempC    = leerTemperatura();
  sueloPct = leerSueloPct();

  Estado tAntes = estadoTemp;
  Estado sAntes = estadoSuelo;
  estadoTemp  = clasificarTemp(tempC);
  estadoSuelo = clasificarSuelo(sueloPct);

  // si vuelve a optimo, el mute ya no aplica
  if ((tAntes != OPTIMO || sAntes != OPTIMO) &&
      estadoTemp == OPTIMO && estadoSuelo == OPTIMO) {
    silenciada = false;
  }

  // 2) indicadores
  leerBoton();
  actualizarLeds();
  refrescarLcd();

  // 3) red (si falla, los LEDs igual funcionan)
  if (WiFi.status() == WL_CONNECTED && !mqtt.connected()) conectarMqtt();
  mqtt.loop();
  digitalWrite(PIN_LED_MQTT, mqtt.connected() ? HIGH : LOW);
  publicarEstado();

  if (millis() - tSerial > 1500) {
    tSerial = millis();
    Serial.printf("T=%.1fC (%s)  H=%d%% (%s)%s\n",
                  tempC, nombreEstado(estadoTemp),
                  sueloPct, nombreEstado(estadoSuelo),
                  alertaCombinada() ? "  [COMBINADA]" : "");
  }
}
