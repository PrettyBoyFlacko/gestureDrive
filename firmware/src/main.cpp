#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include <esp_arduino_version.h>

#include "config.h"

WiFiUDP udp;
Servo steering;
char packet[64];
String serialBuf;
String lastCommand = "STOP";
uint32_t lastPacketMs = 0;
bool motorsEnabled = false;
bool lastWasUdp = false;

static String normalize(String raw) {
  raw.trim();
  raw.toUpperCase();
  if (raw.startsWith("SERVO")) {
    return raw;
  }
  raw.replace(" ", "");
  if (raw == "S") return "STOP";
  if (raw == "C") return "CENTER";
  if (raw == "F") return "FORWARD";
  if (raw == "B") return "REVERSE";
  if (raw == "L") return "LEFT";
  if (raw == "R") return "RIGHT";
  if (raw == "FL" || raw == "FORWARD_LEFT") return "FORWARD-LEFT";
  if (raw == "FR" || raw == "FORWARD_RIGHT") return "FORWARD-RIGHT";
  if (raw == "BL" || raw == "REVERSE_LEFT") return "REVERSE-LEFT";
  if (raw == "BR" || raw == "REVERSE_RIGHT") return "REVERSE-RIGHT";
  return raw;
}

static int clampServo(int angle) {
  if (angle < SERVO_MIN) return SERVO_MIN;
  if (angle > SERVO_MAX) return SERVO_MAX;
  return angle;
}

static void motorPwmWrite(int enPin, int duty) {
#if defined(ESP_ARDUINO_VERSION) && ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
  ledcWrite(enPin, (uint32_t)duty);
#else
  const int ch = (enPin == PIN_ENA) ? MOTOR_PWM_CH_A : MOTOR_PWM_CH_B;
  ledcWrite(ch, (uint32_t)duty);
#endif
}

static void motorPwmInit() {
#if defined(ESP_ARDUINO_VERSION) && ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
  ledcAttach(PIN_ENA, MOTOR_PWM_FREQ_HZ, MOTOR_PWM_RES_BITS);
  ledcAttach(PIN_ENB, MOTOR_PWM_FREQ_HZ, MOTOR_PWM_RES_BITS);
#else
  ledcSetup(MOTOR_PWM_CH_A, MOTOR_PWM_FREQ_HZ, MOTOR_PWM_RES_BITS);
  ledcAttachPin(PIN_ENA, MOTOR_PWM_CH_A);
  ledcSetup(MOTOR_PWM_CH_B, MOTOR_PWM_FREQ_HZ, MOTOR_PWM_RES_BITS);
  ledcAttachPin(PIN_ENB, MOTOR_PWM_CH_B);
#endif
  motorPwmWrite(PIN_ENA, 0);
  motorPwmWrite(PIN_ENB, 0);
}

static void setMotor(int inA, int inB, int en, int pwm, bool forward) {
  pwm = constrain(pwm, 0, PWM_MAX);
  if (pwm <= 0) {
    digitalWrite(inA, LOW);
    digitalWrite(inB, LOW);
    motorPwmWrite(en, 0);
    return;
  }
  digitalWrite(inA, forward ? HIGH : LOW);
  digitalWrite(inB, forward ? LOW : HIGH);
  motorPwmWrite(en, pwm);
}

static void stopMotors() {
  setMotor(PIN_IN1, PIN_IN2, PIN_ENA, 0, true);
  setMotor(PIN_IN3, PIN_IN4, PIN_ENB, 0, true);
  steering.write(SERVO_CENTER);
  motorsEnabled = false;
}

static void applyCommand(const String &cmd) {
  lastCommand = cmd;
  lastPacketMs = millis();

  if (cmd == "STOP" || cmd == "CENTER") {
    stopMotors();
    motorsEnabled = cmd == "CENTER";
    return;
  }

  int servo = SERVO_CENTER;
  int leftPwm = 0;
  int rightPwm = 0;
  bool forward = true;

  const bool hasForward = cmd.startsWith("FORWARD");
  const bool hasReverse = cmd.startsWith("REVERSE");
  const bool hasLeft = cmd.endsWith("LEFT") || cmd == "LEFT";
  const bool hasRight = cmd.endsWith("RIGHT") || cmd == "RIGHT";

  if (hasReverse) forward = false;
  const int drivePwm = hasForward ? PWM_FORWARD : PWM_REVERSE;
  if (hasForward || hasReverse) {
    leftPwm = drivePwm;
    rightPwm = drivePwm;
  }

#if DRIVE_MODE == DRIVE_ACKERMANN
  if (hasLeft) servo = SERVO_LEFT;
  if (hasRight) servo = SERVO_RIGHT;
  if (cmd == "LEFT" || cmd == "RIGHT") {
    leftPwm = 0;
    rightPwm = 0;
  }
#else
  if (cmd == "LEFT") {
    setMotor(PIN_IN1, PIN_IN2, PIN_ENA, PWM_TURN, false);
    setMotor(PIN_IN3, PIN_IN4, PIN_ENB, PWM_TURN, true);
    steering.write(SERVO_CENTER);
    motorsEnabled = true;
    return;
  }
  if (cmd == "RIGHT") {
    setMotor(PIN_IN1, PIN_IN2, PIN_ENA, PWM_TURN, true);
    setMotor(PIN_IN3, PIN_IN4, PIN_ENB, PWM_TURN, false);
    steering.write(SERVO_CENTER);
    motorsEnabled = true;
    return;
  }
  if (hasLeft) {
    leftPwm = PWM_DIFF_INSIDE;
    rightPwm = drivePwm;
  }
  if (hasRight) {
    leftPwm = drivePwm;
    rightPwm = PWM_DIFF_INSIDE;
  }
#endif

  steering.write(clampServo(servo));
  setMotor(PIN_IN1, PIN_IN2, PIN_ENA, leftPwm, forward);
  setMotor(PIN_IN3, PIN_IN4, PIN_ENB, rightPwm, forward);
  motorsEnabled = (leftPwm > 0 || rightPwm > 0);
}

static bool handleSpecial(const String &cmd) {
  if (cmd.startsWith("SERVO")) {
    int space = cmd.indexOf(' ');
    int angle = (space > 0) ? cmd.substring(space + 1).toInt() : SERVO_CENTER;
    int clamped = clampServo(angle);
    steering.write(clamped);
    Serial.printf("SERVO requested=%d clamped=%d\n", angle, clamped);
    lastPacketMs = millis();
    return true;
  }
  return false;
}

static void applyLine(const String &raw) {
  String cmd = normalize(raw);
  if (cmd.length() == 0) return;
  if (handleSpecial(cmd)) return;
  if (cmd == "STOP" || cmd == "CENTER" || cmd == "FORWARD" || cmd == "REVERSE" ||
      cmd == "LEFT" || cmd == "RIGHT" || cmd == "FORWARD-LEFT" || cmd == "FORWARD-RIGHT" ||
      cmd == "REVERSE-LEFT" || cmd == "REVERSE-RIGHT") {
    applyCommand(cmd);
    Serial.printf("CMD %s\n", cmd.c_str());
  } else {
    Serial.printf("IGN %s\n", cmd.c_str());
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  motorPwmInit();
  steering.setPeriodHertz(50);
  steering.attach(PIN_SERVO, 500, 2500);
  stopMotors();
  lastPacketMs = millis();

  WiFi.mode(WIFI_AP);
  WiFi.softAP(WIFI_SSID, WIFI_PASSWORD);
  udp.begin(UDP_PORT);
  Serial.print("SoftAP ");
  Serial.print(WIFI_SSID);
  Serial.print(" ");
  Serial.println(WiFi.softAPIP());
  Serial.println("UDP 8888  serial 115200  default STOP");
}

void loop() {
  int n = udp.parsePacket();
  if (n > 0) {
    int len = udp.read(packet, sizeof(packet) - 1);
    if (len > 0) {
      packet[len] = 0;
      lastWasUdp = true;
      applyLine(String(packet));
    }
  }

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuf.length()) {
        lastWasUdp = false;
        applyLine(serialBuf);
        serialBuf = "";
      }
    } else if (serialBuf.length() < 48) {
      serialBuf += c;
    }
  }

  if (lastWasUdp && WiFi.softAPgetStationNum() == 0 && motorsEnabled) {
    stopMotors();
    lastCommand = "STOP";
    lastWasUdp = false;
    Serial.println("WIFI DROP STOP");
  }

  if (millis() - lastPacketMs >= COMMAND_TIMEOUT_MS && lastCommand != "STOP") {
    applyCommand("STOP");
    Serial.println("TIMEOUT STOP");
  }
}
