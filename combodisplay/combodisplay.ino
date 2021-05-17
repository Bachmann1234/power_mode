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


char modeParam;
String displayValueParam;
String percentParam;

int parameterIndex;
boolean newData;

char* wpm = "WPM";
char* combo = "COMBO";
char* stopped = "MAXC WPM";

void resetState() {
  newData = false;
  displayValueParam = String("");
  modeParam = 's';
  percentParam = String("");
  parameterIndex = 0;
}

void clearScreen() {
  matrix.fillScreen(matrix.Color333(0, 0, 0));
}

void drawWord(const char* wordToDraw) {
  uint8_t w = 0;
  for (w = 0; w < strlen(wordToDraw); w++) {
    matrix.print(wordToDraw[w]);
  }
}

void drawMode(const char* mode) {
  matrix.setTextSize(1);
  uint8_t w = 0;
  boolean modeIsCombo = mode[0] == 'C';
  boolean modeIsGameOver = mode[0] == 'M';
  uint8_t start;
  uint16_t color;
  if (modeIsCombo) {
    start = 18;
    color = matrix.Color333(0, 0, 7);
  } else if (modeIsGameOver) {
    start = 1;
    color = matrix.Color333(7,0,0);
  } else {
    start = 23;
    color = matrix.Color333(0,7,0);
  }
  matrix.setCursor(start, 0);
  matrix.setTextColor(color);
  drawWord(mode);
}

void drawDisplayValue(const char* displayValue) {
  int lenNumber = strlen(displayValue);
  if (lenNumber < 4) {
    matrix.setTextSize(3);
    matrix.setTextWrap(false);
    if (lenNumber == 1) {
      matrix.setCursor(25, 7);
    } else if (lenNumber == 2) {
      matrix.setCursor(18, 7);
    } else {
      matrix.setCursor(8, 7);
    }
  } else if (lenNumber < 5) {
    matrix.setTextSize(2);
    matrix.setCursor(10, 8);
  } else if (lenNumber < 6) {
    matrix.setTextSize(2);
    matrix.setCursor(3, 8);
  } else {
    matrix.setTextSize(1);
    matrix.setCursor(3, 12);  
  }
  matrix.setTextColor(matrix.Color333(1, 7, 2));
  drawWord(displayValue);
}

void drawTimeRemaining(float percent) {
  uint16_t color;
  if (percent > .8) {
    color = matrix.Color333(0, 7, 0);
  } else if (percent > .5) {
    color = matrix.Color333(7, 7, 0);
  } else {
    color = matrix.Color333(7, 0, 0);
  }
  matrix.setCursor(29, 0);
  uint8_t w = 0;
  for (w = 32 - (ceil(32 * percent)); w < 32; w++) {
    matrix.drawPixel(w, 29, color);
    matrix.drawPixel(w, 30, color);
  }
  for (w = 32; w < ceil(32 * percent) + 32; w++) {
    matrix.drawPixel(w, 29, color);
    matrix.drawPixel(w, 30, color);
  }
}

void drawPage(const char* mode, const char* displayValue, float percent) {
  clearScreen();
  drawMode(mode);
  drawDisplayValue(displayValue);
  drawTimeRemaining(percent);
}

void setup() {
  matrix.begin();
  drawPage(combo, "0", 1);
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
      parameterIndex += 1;
    } else {
      if (parameterIndex == 2) {
        displayValueParam += String(recievedChar);
      } else if (parameterIndex == 1) {
        percentParam += String(recievedChar);
      } else {
        modeParam = recievedChar;
      }
    }
  }
}

void execute() {
  if (newData) {
    const char* mode;
    if (modeParam == 'c') {
      mode = combo;
    } else if (modeParam == 'e') {
      mode = stopped;
    } else {
      mode = wpm;
    }
    drawPage(mode, displayValueParam.c_str(), percentParam.toFloat());
    resetState();
  }

}
