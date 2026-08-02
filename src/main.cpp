#include <Arduino.h>
#include <Wire.h>
#include <Keypad.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>

// Contraseña almacenada (6 caracteres)
const char PASSWORD[7] = "123456";

// Pines de conexión
static const int PIN_SERVO = 13;
static const int PIN_LED_VERDE = 25;
static const int PIN_LED_ROJO = 26;
static const int PIN_POT = 34;  // potenciómetro (ADC), material del lab

// Ángulos del servo
static const int SERVO_CERRADO = 0;
static const int SERVO_ABIERTO = 180;

static const unsigned long TIEMPO_RESULTADO_MS = 3000;

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

char entrada[7];
byte indice = 0;

/**
 * Imprime dos mensajes de cadena en el LCD (línea 0 y línea 1).
 */
void imprimirMensajes(const char* linea1, const char* linea2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(linea1);
  lcd.setCursor(0, 1);
  lcd.print(linea2);
}

/**
 * Estado inicial: servo cerrado, LEDs apagados, entrada vacía,
 * mensaje de bienvenida solicitando contraseña.
 */
void estadoInicial() {
  servoPuerta.write(SERVO_CERRADO);
  digitalWrite(PIN_LED_VERDE, LOW);
  digitalWrite(PIN_LED_ROJO, LOW);

  memset(entrada, 0, sizeof(entrada));
  indice = 0;

  imprimirMensajes("Bienvenido", "Clave (6):");
}

/**
 * Lee caracteres del panel matricial hasta completar 6.
 * Devuelve true cuando ya hay 6 caracteres en `entrada`.
 */
bool leerSeisCaracteres() {
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

void setup() {
  Serial.begin(115200);

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

  estadoInicial();
  Serial.println("Sistema de acceso listo. Clave por defecto: 123456");
}

void loop() {
  if (!leerSeisCaracteres()) {
    return;
  }

  Serial.print("Clave ingresada: ");
  Serial.println(entrada);

  if (strcmp(entrada, PASSWORD) == 0) {
    imprimirMensajes("Acceso OK", "Bienvenido!");
    servoPuerta.write(SERVO_ABIERTO);
    digitalWrite(PIN_LED_VERDE, HIGH);
    digitalWrite(PIN_LED_ROJO, LOW);
  } else {
    imprimirMensajes("ALERTA", "Clave invalida");
    servoPuerta.write(SERVO_CERRADO);
    digitalWrite(PIN_LED_ROJO, HIGH);
    digitalWrite(PIN_LED_VERDE, LOW);
  }

  delay(TIEMPO_RESULTADO_MS);
  estadoInicial();
}
