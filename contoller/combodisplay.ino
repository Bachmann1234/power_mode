#include <RGBmatrixPanel.h>
#include <math.h>
#define CLK A4 // USE THIS ON METRO M4 (not M0)
#define OE   9
#define LAT 10
#define A   A0
#define B   A1
#define C   A2
#define D   A3

RGBmatrixPanel matrix(A, B, C, D, CLK, LAT, OE, false, 64);

boolean newData;
String comboStr;
String percentParam;
boolean readCombo;
float percentTimeLeft;

void resetState() {
  newData = false;
  comboStr = String("");
  percentParam = String("");
  readCombo = false;
}


void drawPage(const char* number, float percent) {
  matrix.fillScreen(matrix.Color333(0, 0, 0));
  int lenNumber = strlen(number);
  if (lenNumber < 4) {
    matrix.setTextSize(3);
    matrix.setTextWrap(false);
    if (lenNumber == 1) {
      matrix.setCursor(22, 4);
    } else if (lenNumber == 2) {
      matrix.setCursor(15, 4);
    } else {
      matrix.setCursor(5, 4);
    }
  } else if (lenNumber < 5) {
    matrix.setTextSize(2);
    matrix.setTextWrap(false);
    matrix.setCursor(10, 8);
  } else {
    matrix.setTextSize(2);
    matrix.setTextWrap(false);
    matrix.setCursor(3, 8);

  }
  uint8_t w = 0;
  for (w = 0; w < lenNumber; w++) {
    matrix.setTextColor(matrix.Color333(1, 7, 2));
    matrix.print(number[w]);
  }

  uint16_t color;
  if (percent > .8) {
    color = matrix.Color333(0, 7, 0);
  } else if (percent > .5) {
    color = matrix.Color333(7, 7, 0);
  } else {
    color = matrix.Color333(7, 0, 0);
  }
  matrix.setCursor(29, 0);
  for (w = 32 - (ceil(32 * percent)); w < 32; w++) {
    matrix.drawPixel(w, 29, color);
    matrix.drawPixel(w, 30, color);
  }
  for (w = 32; w < ceil(32 * percent) + 32; w++) {
    matrix.drawPixel(w, 29, color);
    matrix.drawPixel(w, 30, color);
  }
}

void setup() {
  matrix.begin();
  drawPage("0", 1);
  resetState();
  Serial.begin(9600);
  delay(2000);
}


void loop() {
  getData();
  execute();
}

void getData() {
  static byte index = 0;
  char recievedChar;
  while (Serial.available() > 0 && newData == false) {
    recievedChar = Serial.read();
    if (recievedChar == ';') {
      newData = true;
    } else if (recievedChar == ',') {
      readCombo = true;
    } else {
      if (readCombo) {
        comboStr += String(recievedChar);
      } else {
        percentParam += String(recievedChar);
      }
    }
  }
}

void execute() {
  if (newData) {
    drawPage(comboStr.c_str(), percentParam.toFloat());
    resetState();
  }

}
