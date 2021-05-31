#include <Adafruit_NeoPixel.h>
#define LED_PIN     6
#define LED_COUNT  144
#define BRIGHTNESS 50 // Set BRIGHTNESS to about 1/5 (max = 255)


Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRBW + NEO_KHZ800);

uint32_t colorArray[] = {
  strip.Color(  0, 255,   0),
  strip.Color(255,   0,   0),
  strip.Color(255, 80,   0),
  strip.Color(255, 255,   0),
  strip.Color(  0, 0,   255),
  strip.Color( 75, 0,   130),
  strip.Color(238, 130, 238),
  strip.Color(  0, 255, 60)
};

int index = 0;
char colorParam = '0';
bool newData = false;

void setup() {
  strip.begin();
  strip.show();
  strip.setBrightness(BRIGHTNESS);
  Serial.begin(9600);
}

void loop() {
  getData();
  execute();
}

// leaving in for color testing
void colorWipe(uint32_t color, int wait) {
  for (int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
    strip.show();
    delay(wait);
  }
}

void getData() {
  char recievedChar;

  while (Serial.available() > 0 && newData == false) {
    colorParam = Serial.read();
    newData = true;
  }
}

void execute() {
  if (newData) {
    if (colorParam == 'e') {
      index = 0;
      strip.clear();
    } else {
      strip.setPixelColor(index, colorArray[colorParam - '0']);
      index++;
    }
    strip.show();

    if (index > LED_COUNT) {
      index = 0;
    }
    newData = false;
  }
}
