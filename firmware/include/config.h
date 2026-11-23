#pragma once


#define WIFI_SSID "GestureDrive"
#define WIFI_PASSWORD "GestureDrive1"
#define UDP_PORT 8888

#define DRIVE_ACKERMANN 1
#define DRIVE_DIFFERENTIAL 0
#define DRIVE_MODE DRIVE_ACKERMANN

#define PIN_ENA 25
#define PIN_IN1 26
#define PIN_IN2 27
#define PIN_ENB 33
#define PIN_IN3 14
#define PIN_IN4 12
#define PIN_SERVO 18

#define MOTOR_PWM_FREQ_HZ 1000
#define MOTOR_PWM_RES_BITS 8
#define MOTOR_PWM_CH_A 4
#define MOTOR_PWM_CH_B 5
#define PWM_MAX 255
#define PWM_FORWARD 220
#define PWM_REVERSE 160
#define PWM_TURN 160
#define PWM_DIFF_INSIDE 70

#define SERVO_CENTER 90
#define SERVO_MIN 50
#define SERVO_MAX 130
#define SERVO_LEFT 130
#define SERVO_RIGHT 50

#define COMMAND_TIMEOUT_MS 300
#define SERIAL_BAUD 115200
