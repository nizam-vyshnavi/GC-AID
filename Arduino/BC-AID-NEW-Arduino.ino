#define LIGHT_PIN 7
#define FAN_PIN 6
#include <SoftwareSerial.h>

SoftwareSerial gsm(10,11); // RX, TX

String phoneNumber = "+919848214132";  // your number
bool emergency_in_progress = false;

void setup() {
  Serial.begin(9600);
  gsm.begin(9600);

  delay(5000);
  Serial.println("GSM Ready");

  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(LIGHT_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  //Serial.begin(9600);
}

void loop() {
  if (Serial.available() && !emergency_in_progress) {
    delay(50);
    char cmd = Serial.read();
       

    // 🚫 Ignore newline / carriage return
    if (cmd == '\n' || cmd == '\r') return;

    Serial.print("Received: ");
    Serial.println(cmd);

    if (cmd == '1') digitalWrite(LIGHT_PIN, HIGH);
    else if (cmd == '0') digitalWrite(LIGHT_PIN, LOW);
    else if (cmd == '2') digitalWrite(FAN_PIN, HIGH);
    else if (cmd == '3') digitalWrite(FAN_PIN, LOW);

    else if (cmd == 'E') {
      emergency_in_progress = true;
      Serial.println("🚨 Emergency Triggered");
      delay(2000);
      sendSMS();
      delay(8000);
      makeCall();
      delay(10000);
      emergency_in_progress = false;
      

    }
  }
}

void sendSMS() {
  Serial.println("Sending SMS...");

  gsm.println("AT");
  delay(2000);

  gsm.println("AT+CMGF=1");
  delay(2000);

  gsm.print("AT+CMGS=\"");
  gsm.print(phoneNumber);
  gsm.println("\"");
  delay(2000);

  gsm.print("EMERGENCY ALERT: Patient needs help!");
  delay(1000);

  gsm.write(26); // CTRL+Z
  delay(6000);   // 🔥 VERY IMPORTANT

  Serial.println("SMS Sent");
}

void makeCall() {
  Serial.println("Calling...");

  gsm.print("ATD");
  gsm.print(phoneNumber);
  gsm.println(";");
  delay(2000);

  while (gsm.available()) Serial.write(gsm.read());

  delay(15000);

  gsm.println("ATH");
  Serial.println("Call Ended");
}