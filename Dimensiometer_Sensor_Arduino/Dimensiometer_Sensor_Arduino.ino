/*
  The circuit:
   Sonar RX is digital pin 10 (connect to TX of other device)
   HX711 DATA = A0
   HX711 SCK = A1
*/
#include <SoftwareSerial.h>
#include <HX711.h>
#include <ctype.h>

// HX711 circuit wiring
const byte LOADCELL_DOUT_PIN = A0;
const byte LOADCELL_SCK_PIN = A1;

const float refreshRate = 6.6; // Maximum refresh rate of the sonar
const int dt = (int) 1000.0 / (refreshRate); // Refresh interval in ms
unsigned long lastMillis = 0;

SoftwareSerial sonarSerial(10, 11, true); // RX, TX, use inverted logic
HX711 scale;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // set the data rate for the SoftwareSerial port
  sonarSerial.begin(9600);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
}

String sonarBuffer = "";
long scaleVal = 0;

void loop() { // run over and over
  if (abs(millis() - lastMillis) > dt) {
    lastMillis = millis();
    String output = "";
    String tempSonarBuffer = "";

    while (sonarSerial.available()) {
      char c = sonarSerial.read();
      if (c == 'R') {
        break;
      }
      else {
        tempSonarBuffer += c;
      }
    }
    if (tempSonarBuffer != "") {
      tempSonarBuffer = tempSonarBuffer.substring(0, 4); // substring takes out additional characters that occasionally happen in the UART
      boolean goodReading = true;
      for (int c = 0; c < 4; c++) {
        if (!isDigit(tempSonarBuffer[c])) {
          goodReading = false;
        }
      }
      if (goodReading) {
        sonarBuffer = tempSonarBuffer;
      }
    }

  }
  if (scale.is_ready()) {
    scaleVal = scale.read();
    //double scaleGrams = -0.05 * (double) scaleVal - 6598.3;
    Serial.print(millis());
    Serial.print(",");
    Serial.print(scaleVal);
    Serial.print(",");
    Serial.println(sonarBuffer);
  }

}
