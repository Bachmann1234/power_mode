#define CLICKY_ONE 9
#define CLICKY_TWO 10
#define CLICKY_THREE 11
#define CLICKY_FOUR 12
#define NUM_CLICKYS 4
#define NUM_PARAMS 2

byte clickIndex = 0;
boolean keyDown = false;
boolean newData = false;
boolean readCmd = true;

byte keys[NUM_CLICKYS] = {
  CLICKY_ONE,
  CLICKY_TWO,
  CLICKY_THREE,
  CLICKY_FOUR
};
bool states[NUM_CLICKYS] = {
  false,
  false,
  false,
  false
};
void setup()
{
  pinMode(CLICKY_ONE, OUTPUT);
  pinMode(CLICKY_TWO, OUTPUT);
  pinMode(CLICKY_THREE, OUTPUT);
  pinMode(CLICKY_FOUR, OUTPUT);
  Serial.begin(9600);
  delay(2000);
}

void writeKey(int index, int level) {
  states[index] = level == HIGH;
  digitalWrite(keys[index], level);
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
    if (readCmd) {
      keyDown = recievedChar == '1';
      readCmd = false;
    } else {
      if (recievedChar == '0') {
        clickIndex = 0;
      } else if (recievedChar == '1') {
        clickIndex = 1;
      } else if (recievedChar == '2') {
        clickIndex = 2;
      } else {
        clickIndex = 3;
      }
      readCmd = true;
      newData = true;
    }
  }
}

void execute() {
  if (newData) {
    if (keyDown) {
      if (states[clickIndex]) {
        for (int i = 0; i < NUM_CLICKYS; i++) {
          if (!states[i]) {
            writeKey(i, HIGH);
            break;
          }
        }
      } else {
        writeKey(clickIndex, HIGH);
      }
    } else {
      if (!states[clickIndex]) {
        for (int i = 0; i < NUM_CLICKYS; i++) {
          if (states[i]) {
            writeKey(i, LOW);
            break;
          }
        }
      } else {
        writeKey(clickIndex, LOW);
      }
    }
    newData = false;
  }
}
