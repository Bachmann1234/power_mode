#include <Adafruit_NeoPixel.h>
#define LED_PIN     6
#define LED_COUNT  144
#define BRIGHTNESS 50 // Set BRIGHTNESS to about 1/5 (max = 255)


Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRBW + NEO_KHZ800);

String END_CODE = String("e");

uint32_t COLOR_ARRAY[] = {
  strip.Color(  0, 255,   0),
  strip.Color(255,   0,   0),
  strip.Color(255, 80,   0),
  strip.Color(255, 255,   0),
  strip.Color(  0, 0,   255),
  strip.Color( 75, 0,   130),
  strip.Color(238, 130, 238),
  strip.Color(  0, 255, 60)
};

bool newData;

String colorModeParam;
String indexParam;
int parameterIndex;

void reset() {
  colorModeParam = String("");
  indexParam = String("");
  newData = false;
  parameterIndex = 0;
}

void setup() {
  reset();
  strip.begin();
  strip.show();
  strip.setBrightness(BRIGHTNESS);
  Serial.begin(9600);
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
      if (parameterIndex == 1) {
        colorModeParam += String(recievedChar);
      } else {
        indexParam += String(recievedChar);
      }
    }
  }
}

void execute() {
  if (newData) {
    if (colorModeParam == END_CODE) {
      strip.clear();
    } else {
      strip.setPixelColor(indexParam.toInt(), COLOR_ARRAY[colorModeParam.toInt()]);
    }
    strip.show();
    reset();
  }
}
