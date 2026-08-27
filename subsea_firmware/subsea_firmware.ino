/*
  Controlador del ROV: protocolo binario de seis bytes, failsafe y telemetría.
  El mismo programa compila para ESP32 y para Arduino Uno/Nano.
*/
#include <Arduino.h>

#if defined(ARDUINO_ARCH_ESP32)
const uint8_t PIN_DE_RE = 4;
const uint8_t PIN_LIGHT = 23;
const uint8_t PIN_VIN = 34;
const uint8_t PIN_LEFT_EN = 25;
const uint8_t PIN_LEFT_IN1 = 26;
const uint8_t PIN_LEFT_IN2 = 27;
const uint8_t PIN_RIGHT_EN = 32;
const uint8_t PIN_RIGHT_IN1 = 33;
const uint8_t PIN_RIGHT_IN2 = 14;
const uint8_t PIN_VERTICAL_EN = 13;
const uint8_t PIN_VERTICAL_IN1 = 5;
const uint8_t PIN_VERTICAL_IN2 = 18;
#elif defined(ARDUINO_ARCH_AVR)
const uint8_t PIN_DE_RE = 3;
const uint8_t PIN_LIGHT = 5;
const uint8_t PIN_VIN = A0;
const uint8_t PIN_LEFT_EN = 9;
const uint8_t PIN_LEFT_IN1 = 2;
const uint8_t PIN_LEFT_IN2 = 4;
const uint8_t PIN_RIGHT_EN = 10;
const uint8_t PIN_RIGHT_IN1 = 7;
const uint8_t PIN_RIGHT_IN2 = 8;
const uint8_t PIN_VERTICAL_EN = 11;
const uint8_t PIN_VERTICAL_IN1 = 12;
const uint8_t PIN_VERTICAL_IN2 = 13;
// En AVR la UART hardware se comparte entre comandos y telemetría; es
// apropiado para RS-485 semidúplex con conmutación DE/RE.
#endif

const unsigned long FAILSAFE_MS = 500;
const unsigned long TELEMETRY_MS = 250;
const int8_t DEAD_BAND = 10;
const uint8_t FLAG_LIGHTS = 0x01;
const uint8_t FLAG_ARMED = 0x02;
const uint8_t FLAG_EMERGENCY = 0x04;
const uint8_t PWM_CHANNEL_LEFT = 0;
const uint8_t PWM_CHANNEL_RIGHT = 1;
const uint8_t PWM_CHANNEL_VERTICAL = 2;

uint8_t frame[6];
uint8_t frameIndex = 0;
unsigned long lastValidFrame = 0;
unsigned long lastTelemetry = 0;
uint16_t validFrames = 0;
bool emergencyActive = false;
bool armed = false;

#if defined(ARDUINO_ARCH_ESP32)
HardwareSerial rs485(2);
#else
#define rs485 Serial
#endif

#if defined(ARDUINO_ARCH_ESP32)
const uint32_t PWM_FREQUENCY = 20000;
const uint8_t PWM_RESOLUTION = 8;
#endif

int16_t ejeFirmado(uint8_t valor) {
  int16_t diferencia = static_cast<int16_t>(valor) - 128;
  if (abs(diferencia) <= DEAD_BAND) {
    return 0;
  }
  int16_t magnitud = (abs(diferencia) - DEAD_BAND) * 255 / (127 - DEAD_BAND);
  return diferencia < 0 ? -magnitud : magnitud;
}

void escribirPWM(uint8_t pin, uint8_t canal, uint8_t valor) {
#if defined(ARDUINO_ARCH_ESP32)
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, valor);
#else
  ledcWrite(canal, valor);
#endif
#else
  analogWrite(pin, valor);
#endif
}

void detenerMotores() {
  escribirPWM(PIN_LEFT_EN, PWM_CHANNEL_LEFT, 0);
  escribirPWM(PIN_RIGHT_EN, PWM_CHANNEL_RIGHT, 0);
  escribirPWM(PIN_VERTICAL_EN, PWM_CHANNEL_VERTICAL, 0);
#if !defined(ARDUINO_ARCH_ESP32)
  digitalWrite(PIN_LEFT_EN, LOW);
  digitalWrite(PIN_RIGHT_EN, LOW);
  digitalWrite(PIN_VERTICAL_EN, LOW);
#endif
  digitalWrite(PIN_RIGHT_IN1, LOW);
  digitalWrite(PIN_RIGHT_IN2, LOW);
  digitalWrite(PIN_LEFT_IN1, LOW);
  digitalWrite(PIN_LEFT_IN2, LOW);
  digitalWrite(PIN_VERTICAL_IN1, LOW);
  digitalWrite(PIN_VERTICAL_IN2, LOW);
}

void configurarMotor(uint8_t en, uint8_t in1, uint8_t in2, int16_t potencia,
                     uint8_t canal) {
  if (potencia == 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    escribirPWM(en, canal, 0);
#if !defined(ARDUINO_ARCH_ESP32)
    digitalWrite(en, LOW);
#endif
    return;
  }
  bool adelante = potencia > 0;
  digitalWrite(in1, adelante ? HIGH : LOW);
  digitalWrite(in2, adelante ? LOW : HIGH);
  escribirPWM(en, canal, static_cast<uint8_t>(constrain(abs(potencia), 0, 255)));
}

void aplicarControl(uint8_t x, uint8_t y, uint8_t z, uint8_t flags) {
  int16_t avance = ejeFirmado(x);
  int16_t vertical = ejeFirmado(y);
  int16_t giro = ejeFirmado(z);
  int16_t izquierda = constrain(avance + giro, -255, 255);
  int16_t derecha = constrain(avance - giro, -255, 255);
  bool parada = (flags & FLAG_EMERGENCY) != 0;
  armed = (flags & FLAG_ARMED) != 0;
  emergencyActive = parada;
  digitalWrite(PIN_LIGHT, (flags & FLAG_LIGHTS) ? HIGH : LOW);
  if (parada || !armed) {
    detenerMotores();
    return;
  }
  configurarMotor(PIN_LEFT_EN, PIN_LEFT_IN1, PIN_LEFT_IN2, izquierda,
                  PWM_CHANNEL_LEFT);
  configurarMotor(PIN_RIGHT_EN, PIN_RIGHT_IN1, PIN_RIGHT_IN2, derecha,
                  PWM_CHANNEL_RIGHT);
  configurarMotor(PIN_VERTICAL_EN, PIN_VERTICAL_IN1, PIN_VERTICAL_IN2, vertical,
                  PWM_CHANNEL_VERTICAL);
}

void procesarTrama() {
  uint8_t checksum = static_cast<uint8_t>(
      (static_cast<uint16_t>(frame[1]) + frame[2] + frame[3] + frame[4]) & 0xFF);
  if (checksum != frame[5]) {
    frameIndex = 0;
    return;
  }
  lastValidFrame = millis();
  validFrames++;
  aplicarControl(frame[1], frame[2], frame[3], frame[4]);
  frameIndex = 0;
}

void leerSerie() {
  while (rs485.available() > 0) {
    uint8_t byteRecibido = static_cast<uint8_t>(rs485.read());
    if (frameIndex == 0) {
      if (byteRecibido == 0xAA) {
        frame[0] = byteRecibido;
        frameIndex = 1;
      }
    } else {
      frame[frameIndex++] = byteRecibido;
      if (frameIndex == 6) {
        procesarTrama();
      }
    }
  }
}

void emitirTelemetria() {
  unsigned long ahora = millis();
  if (ahora - lastTelemetry < TELEMETRY_MS) {
    return;
  }
  lastTelemetry = ahora;
  bool failsafe = (ahora - lastValidFrame > FAILSAFE_MS) ||
                  emergencyActive || !armed;
  uint16_t lectura = analogRead(PIN_VIN);
#if defined(ARDUINO_ARCH_ESP32)
  float vin = (static_cast<float>(lectura) / 4095.0f) * 3.3f * 11.0f;
#else
  float vin = (static_cast<float>(lectura) / 1023.0f) * 5.0f * 11.0f;
#endif
  digitalWrite(PIN_DE_RE, HIGH);
  rs485.print("TLM;vin=");
  rs485.print(vin, 1);
  rs485.print(";fps=");
  rs485.print(validFrames * 4);
  rs485.print(";fs=");
  rs485.print(failsafe ? 1 : 0);
  rs485.print('\n');
  rs485.flush();
  digitalWrite(PIN_DE_RE, LOW);
  validFrames = 0;
}

void configurarPWM() {
#if defined(ARDUINO_ARCH_ESP32)
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_LEFT_EN, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttach(PIN_RIGHT_EN, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttach(PIN_VERTICAL_EN, PWM_FREQUENCY, PWM_RESOLUTION);
#else
  ledcSetup(PWM_CHANNEL_LEFT, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_RIGHT, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_VERTICAL, PWM_FREQUENCY, PWM_RESOLUTION);
  ledcAttachPin(PIN_LEFT_EN, PWM_CHANNEL_LEFT);
  ledcAttachPin(PIN_RIGHT_EN, PWM_CHANNEL_RIGHT);
  ledcAttachPin(PIN_VERTICAL_EN, PWM_CHANNEL_VERTICAL);
#endif
#endif
}

void setup() {
  pinMode(PIN_DE_RE, OUTPUT);
  digitalWrite(PIN_DE_RE, LOW);
  pinMode(PIN_LIGHT, OUTPUT);
  pinMode(PIN_LEFT_EN, OUTPUT);
  pinMode(PIN_RIGHT_EN, OUTPUT);
  pinMode(PIN_VERTICAL_EN, OUTPUT);
  pinMode(PIN_LEFT_IN1, OUTPUT);
  pinMode(PIN_LEFT_IN2, OUTPUT);
  pinMode(PIN_RIGHT_IN1, OUTPUT);
  pinMode(PIN_RIGHT_IN2, OUTPUT);
  pinMode(PIN_VERTICAL_IN1, OUTPUT);
  pinMode(PIN_VERTICAL_IN2, OUTPUT);
  configurarPWM();
  detenerMotores();
#if defined(ARDUINO_ARCH_ESP32)
  rs485.begin(57600, SERIAL_8N1, 16, 17);
#else
  rs485.begin(57600);
#endif
  lastValidFrame = millis();
}

void loop() {
  leerSerie();
  if (millis() - lastValidFrame > FAILSAFE_MS) {
    emergencyActive = false;
    detenerMotores();
  }
  emitirTelemetria();
}
