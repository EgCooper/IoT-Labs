#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Keypad.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>

// ---- Red (Wokwi: Wokwi-GUEST / pass vacía) ----
static const char *WIFI_SSID = "Wokwi-GUEST";
static const char *WIFI_PASS = "";

static const char *MQTT_BROKER = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const char *MQTT_TOPIC = "monitoreo/puerta-acceso1332";

// Contraseña mutable (6 caracteres)
char password[7] = "123456";

// Pines
static const int PIN_SERVO = 13;
static const int PIN_LED_VERDE = 25;
static const int PIN_LED_ROJO = 26;
static const int PIN_POT = 34;

static const int SERVO_CERRADO = 0;
static const int SERVO_ABIERTO = 180;
static const unsigned long TIEMPO_RESULTADO_MS = 3000;
static const unsigned long MQTT_RETRY_MS = 3000;

// Keypad 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};
byte rowPins[ROWS] = {19, 18, 5, 17};
byte colPins[COLS] = {16, 4, 15, 23};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servoPuerta;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

char entrada[7];
byte indice = 0;
bool accesoBloqueado = false;
bool esperandoResultado = false;
unsigned long resultadoDesdeMs = 0;

void imprimirMensajes(const char *linea1, const char *linea2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(linea1);
  lcd.setCursor(0, 1);
  lcd.print(linea2);
}

void estadoInicial() {
  accesoBloqueado = false;
  esperandoResultado = false;
  servoPuerta.write(SERVO_CERRADO);
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);
  memset(entrada, 0, sizeof(entrada));
  indice = 0;
  imprimirMensajes("Bienvenido", "Clave (6):");
}

void bloquearAcceso() {
  accesoBloqueado = true;
  esperandoResultado = false;
  memset(entrada, 0, sizeof(entrada));
  indice = 0;
  servoPuerta.write(SERVO_CERRADO);
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_ROJO, HIGH);
  imprimirMensajes("BLOQUEADO", "Acceso denegado");
  Serial.println("Acceso bloqueado remotamente");
}

void abrirPuertaRemoto() {
  accesoBloqueado = false;
  esperandoResultado = false;
  memset(entrada, 0, sizeof(entrada));
  indice = 0;
  servoPuerta.write(SERVO_ABIERTO);
  digitalWrite(PIN_LED_VERDE, HIGH);
  digitalWrite(PIN_LED_ROJO, LOW);
  imprimirMensajes("Remoto OK", "Bienvenido!");
  Serial.println("Puerta abierta remotamente");
}

bool actualizarPassword(const char *nueva) {
  if (nueva == nullptr || strlen(nueva) != 6) {
    Serial.println("Password invalida (debe tener 6 caracteres)");
    return false;
  }
  strncpy(password, nueva, 6);
  password[6] = '\0';
  Serial.print("Password actualizada: ");
  Serial.println(password);
  imprimirMensajes("Clave nueva", password);
  delay(1500);
  if (!accesoBloqueado) {
    estadoInicial();
  } else {
    bloquearAcceso();
  }
  return true;
}

void publicarEventoAcceso(const char *evento, const char *claveUsada) {
  JsonDocument doc;
  doc["evento"] = evento;
  doc["clave"] = claveUsada;
  doc["ts"] = (uint32_t)(millis() / 1000);

  char payload[160];
  serializeJson(doc, payload, sizeof(payload));
  Serial.print("MQTT publish: ");
  Serial.println(payload);

  if (mqtt.connected()) {
    mqtt.publish(MQTT_TOPIC, payload);
  }
}

bool leerSeisCaracteres() {
  if (accesoBloqueado || esperandoResultado) {
    return false;
  }

  char tecla = keypad.getKey();
  if (tecla == NO_KEY) {
    return false;
  }

  entrada[indice] = tecla;
  lcd.setCursor(indice, 1);
  lcd.print('*');
  indice++;

  Serial.print("Tecla: ");
  Serial.println(tecla);

  if (indice >= 6) {
    entrada[6] = '\0';
    return true;
  }
  return false;
}

void procesarAccion(const char *action, const char *nuevaClave) {
  if (action == nullptr) {
    return;
  }

  if (strcmp(action, "bloquear") == 0) {
    bloquearAcceso();
  } else if (strcmp(action, "desbloquear") == 0) {
    estadoInicial();
    Serial.println("Acceso desbloqueado remotamente");
  } else if (strcmp(action, "abrir") == 0) {
    abrirPuertaRemoto();
  } else if (strcmp(action, "actualizar") == 0) {
    actualizarPassword(nuevaClave);
  } else {
    Serial.print("Accion MQTT desconocida: ");
    Serial.println(action);
  }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
  char mensaje[192];
  if (length >= sizeof(mensaje)) {
    length = sizeof(mensaje) - 1;
  }
  memcpy(mensaje, payload, length);
  mensaje[length] = '\0';

  Serial.print("MQTT [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(mensaje);

  // Ignorar eventos publicados por este mismo dispositivo
  if (strstr(mensaje, "\"evento\"") != nullptr) {
    return;
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, mensaje);
  if (!err) {
    const char *action = doc["action"] | "";
    const char *nueva = doc["password"] | "";
    if (strlen(action) > 0) {
      procesarAccion(action, nueva);
      return;
    }
  }

  // Comandos en texto plano (fáciles de probar en HiveMQ)
  // bloquear | desbloquear | abrir | actualizar:654321
  if (strncmp(mensaje, "actualizar:", 11) == 0) {
    procesarAccion("actualizar", mensaje + 11);
  } else if (strcmp(mensaje, "bloquear") == 0 ||
             strcmp(mensaje, "desbloquear") == 0 ||
             strcmp(mensaje, "abrir") == 0) {
    procesarAccion(mensaje, nullptr);
  }
}

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("Conectando WiFi SSID=%s\n", WIFI_SSID);
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
    Serial.print("WiFi OK, IP=");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi FALLIDO");
  }
}

void conectarMqtt() {
  if (mqtt.connected() || WiFi.status() != WL_CONNECTED) {
    return;
  }

  String clientId = String("esp32-acceso-") + String((uint32_t)ESP.getEfuseMac(), HEX);
  Serial.printf("Conectando MQTT %s:%u como %s\n", MQTT_BROKER, MQTT_PORT, clientId.c_str());

  if (mqtt.connect(clientId.c_str())) {
    Serial.println("MQTT OK");
    mqtt.subscribe(MQTT_TOPIC);
    Serial.print("Suscrito a: ");
    Serial.println(MQTT_TOPIC);
  } else {
    Serial.printf("MQTT FALLIDO, rc=%d\n", mqtt.state());
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIN_LED_VERDE, OUTPUT);
  pinMode(PIN_LED_ROJO, OUTPUT);
  pinMode(PIN_POT, INPUT);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  servoPuerta.setPeriodHertz(50);
  servoPuerta.attach(PIN_SERVO, 500, 2400);

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);

  imprimirMensajes("Conectando", "WiFi/MQTT...");
  conectarWiFi();
  conectarMqtt();

  estadoInicial();
  Serial.println("Sistema de acceso remoto listo");
  Serial.printf("Topic MQTT: %s\n", MQTT_TOPIC);
  Serial.println("Clave por defecto: 123456");
  Serial.println("Cmds: bloquear | desbloquear | abrir | actualizar:XXXXXX");
}

void loop() {
  conectarWiFi();
  if (!mqtt.connected()) {
    static unsigned long ultimoIntentoMqtt = 0;
    if (millis() - ultimoIntentoMqtt >= MQTT_RETRY_MS) {
      ultimoIntentoMqtt = millis();
      conectarMqtt();
    }
  }
  mqtt.loop();

  if (esperandoResultado) {
    if (millis() - resultadoDesdeMs >= TIEMPO_RESULTADO_MS) {
      if (!accesoBloqueado) {
        estadoInicial();
      }
    }
    return;
  }

  if (!leerSeisCaracteres()) {
    return;
  }

  Serial.print("Clave ingresada: ");
  Serial.println(entrada);

  if (strcmp(entrada, password) == 0) {
    imprimirMensajes("Acceso OK", "Bienvenido!");
    servoPuerta.write(SERVO_ABIERTO);
    digitalWrite(PIN_LED_VERDE, HIGH);
    digitalWrite(PIN_LED_ROJO, LOW);
    publicarEventoAcceso("acceso_concedido", entrada);
  } else {
    imprimirMensajes("ALERTA", "Clave invalida");
    servoPuerta.write(SERVO_CERRADO);
    digitalWrite(PIN_LED_ROJO, HIGH);
    digitalWrite(PIN_LED_VERDE, LOW);
    publicarEventoAcceso("acceso_denegado", entrada);
  }

  esperandoResultado = true;
  resultadoDesdeMs = millis();
}
