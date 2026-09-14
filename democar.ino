
//in1 and in2 = left motor
//in3 and in4 = right motor
//battery connected to +12v and gnd
// vin on esp32 connected to +5v


const int IN1 = 26; // D26
const int IN2 = 27; // D27
const int IN3 = 14; // D14
const int IN4 = 12; // D12
const int ENA = 25; // D25
const int ENB = 33; // D33
const int speed = 160;

void stopMotors() {
  digitalWrite(IN1, LOW); 
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); 
  digitalWrite(IN4, LOW);
}

void forward() {
  digitalWrite(IN1, HIGH); 
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); 
  digitalWrite(IN4, LOW);
}

void backward() {
  digitalWrite(IN1, LOW); 
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); 
  digitalWrite(IN4, HIGH);
}

void left() {
  digitalWrite(IN1, LOW);  
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); 
  digitalWrite(IN4, LOW);
}

void right() {
  digitalWrite(IN1, HIGH); 
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  
  digitalWrite(IN4, LOW);
}

void setup() {
  pinMode(IN1, OUTPUT); 
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); 
  pinMode(IN4, OUTPUT);

  ledcAttach(ENA, 1000, 8);
  ledcAttach(ENB, 1000, 8);
  ledcWrite(ENA, speed);
  ledcWrite(ENB, speed);

  stopMotors();
}

void loop() {
  forward();
  delay(2000);
  backward();
  delay(2000);
  left();
  delay(2000);
  right();
  delay(2000);
  stopMotors();
  delay(3000);
}