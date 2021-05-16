#define CLICKY_ONE 8
#define CLICKY_TWO 9
#define CLICKY_THREE 10
#define CLICKY_FOUR 11
#define NUM_CLICKYS 4
#define NUM_PARAMS 2

boolean newData = false;
int indexRead = 0;

boolean params[NUM_CLICKYS] = {
  false,
  false,
  false,
  false
};

byte keys[NUM_CLICKYS] = {
  CLICKY_ONE,
  CLICKY_TWO,
  CLICKY_THREE,
  CLICKY_FOUR
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

void writeKey(int index, boolean state) {
  digitalWrite(keys[index], state ? HIGH : LOW);
}

void loop() {
  getData();
  execute();
}

void writeKeys() {
  for (int i = 0; i < NUM_CLICKYS; i++) {
    //Serial.println(params[i] ? "ON " : "OFF "); 
    writeKey(i, params[i]);
  }
}

void getData() {
  char recievedChar;

  while (Serial.available() > 0 && newData == false) {
    recievedChar = Serial.read();
    params[indexRead] = recievedChar == '1';
    indexRead += 1;
    if (indexRead == 4) {
      newData = true;
    }
  }
}

void execute() {
  if (newData) {
    writeKeys();
    newData = false;
    indexRead = 0;
  }
}
