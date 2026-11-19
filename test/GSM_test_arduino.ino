#include <SoftwareSerial.h>

SoftwareSerial gsm(10,11);

void setup()
{
  Serial.begin(9600);
  gsm.begin(9600);

  delay(3000);

  Serial.println("Initializing GSM...");

  gsm.println("AT");
  delay(1000);
  readGSM();

  gsm.println("AT+CMGF=1");
  delay(1000);
  readGSM();

  Serial.println("Sending SMS...");

  gsm.println("AT+CMGS=\"+919848214132\"");
  delay(1000);
  readGSM();

  gsm.print("Hello from Arduino");

  gsm.write(26); // Ctrl+Z

  delay(5000); // wait for sending

  readGSM();

  Serial.println("Message sent (if OK received)");
}

void loop()
{
}

// Function to read GSM responses
void readGSM()
{
  while (gsm.available())
  {
    Serial.write(gsm.read());
  }
}


//TEST: 
//AT+CPIN?
//AT+CREG?