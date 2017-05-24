#include <TAP_ADXL345.h>

// EXPERIMENT VARIABLES
const int maxFingers = 5;
int nFingers = 5; //2
String fingerName[maxFingers] = {"thumb","index","middle","ring","pinky"};
long tapTimeout = 5000;       // ms time to wait for a tap before timing out
long samplingTime = 2000;     // ms time to keep sampling after tap detected
const int maxTaps = 3;        // number of taps to record per finger for a single cue
long tapDebounce = 200;       // ms window to ignore tap triggers after a trigger

// ACCELEROMETER VARIABLES
ADXL345 accelerometer[maxFingers] = {}; 
int chipSelect[maxFingers] = {22,24,26,28,30}; //{9,10};
int interruptPin[maxFingers] = /{3,21,20,19,18}; //{2,3};
volatile long interruptTime[maxFingers][maxTaps] = {};
volatile long interruptN[maxFingers] = {};
int accelerometerRange = 16;  // 2G, 4G, 8G, 16G
int tapThreshold = 50;        // minimum amplitude for a tap (0-255), 62.5 mG per increment (LSB)
int maxTapDuration = 32;      // time exceeding threshold must be shorter than this (0-255), 0.625 ms per increment (LSB); 16 is 10ms

// MOTOR VARIABLES
int motor[maxFingers] = {4,5,6,7,8};
long motorDuration = 100;     // ms
int motorPWM = 255;

// SERIAL COMMUNICATION VARIABLES
String pythonSays;            // for reading commands from python
const bool echoSerial = true; //send back to python any commands received
const int serialBaudRate = 9600; // should match python
const int serialTimeOut = 10; // ms

// SETUP TO RUN ONCE AT THE BEGINNING

void setup(){  
  for (int finger=0; finger<nFingers; finger++) {
    // create accelerometer objects according to CS pin
    // SPI data mode, pull CS high etc. set when ADXL345 objects created
    accelerometer[finger] = ADXL345(chipSelect[finger]);
    // set motor pins to output
    pinMode(motor[finger], OUTPUT);
    // populate interrupt data arrays with default values
    interruptN[finger] = -1;
    for (int tap=0; tap<maxTaps; tap++) {
      interruptTime[finger][tap] = 0;   
    }
  }
  // make serial connection
  Serial.begin(serialBaudRate);
  Serial.setTimeout(serialTimeOut);
}

// MAIN LOOP WAITS FOR SERIAL INPUT COMMANDS FROM PYTHON THEN ACTS ACCORDINGLY

void loop(){
  int accel;
  int tapFinger;
  while (Serial.available() <= 0) {
    // wait for serial input
  }
  
  // get instructions from python over serial connection
  pythonSays = Serial.readString();
  
  // CHECK SERIAL CONNECTION
  if (pythonSays == "ping") {
    Serial.println("ack");

  // CHANGE/SET EXPERIMENT VARIABLES
  } else if (pythonSays == "nFingers") {
    nFingers = serial_get_int(echoSerial);
  } else if (pythonSays == "tapTimeout") {
    tapTimeout = serial_get_int(echoSerial);
  } else if (pythonSays == "samplingTime") {
    samplingTime = serial_get_int(echoSerial);
  } else if (pythonSays == "tapDebounce") {
    tapDebounce = serial_get_int(echoSerial);
  
  // SETUP ACCELEROMETER
  } else if (pythonSays == "range") {
    accelerometerRange = serial_get_int(echoSerial);
  } else if (pythonSays == "threshold") {
    tapThreshold = serial_get_int(echoSerial);
  } else if (pythonSays == "duration") {
    maxTapDuration = serial_get_int(echoSerial);
  } else if (pythonSays == "setup") {
    accel = serial_get_int(echoSerial); // which accelerometer to setup
    setup_accelerometer(accelerometer[accel],accelerometerRange,tapThreshold,maxTapDuration);

  // PROMPTED FOR A TAP
  } else if (pythonSays == "tap") {
    tapFinger = serial_get_int(echoSerial); // which finger should tap
    get_finger_tap(tapFinger, motorDuration*1000, tapTimeout*1000, samplingTime*1000); // convert ms to us
  
  // PUT ACCELEROMETER IN STANDBY
  } else if (pythonSays=="standby") {
    accel = serial_get_int(echoSerial);
    accelerometer[accel].standby();
  
  // UNRECOGNISED INSTRUCTIONS
  } else {
    Serial.print("I don't understand: ");
    Serial.println(pythonSays);
  }  
}

//  FUNCTIONS

void get_finger_tap(int tapFinger, long motorDuration, long tapTimeout, long samplingTime) {
  // This function uses micros() for timing so all input times should be in microseconds
  Serial.println("waiting for tap"); 
  int x,y,z; // axes sampled
  long t; //sample time
  long startTime; // time when prompted for a tap
  long firstTapTime = 0;
  bool sampling = true;
  bool motorOn = true;
  
  startTime = micros();
  clear_all_interrupts();
  attach_all_interrupts(); // attach interrupts and link to ISR
  analogWrite(motor[tapFinger], motorPWM); // buzz

  while (sampling) {
    // Sample accelerometer data, t gives us the current/sample time
    accelerometer[tapFinger].readAccel(&x, &y, &z, &t);
    Serial.print(t);
    Serial.print(",");
    Serial.print(x);
    Serial.print(",");
    Serial.print(y);
    Serial.print(",");
    Serial.println(z);
    
    // Check if the motor should switch off
    if (motorOn && (t - startTime > motorDuration)) {
      analogWrite(motor[tapFinger], 0); // no buzz
      motorOn = false;
    }
    
    // Tap Detection
    if (firstTapTime == 0) {
      for (int finger=0; finger<nFingers; finger++) {
        if(interruptTime[finger][0] > startTime) { //interruptTime is set in the ISRs
          firstTapTime = interruptTime[finger][0];
        }  
      }
    }
    
    // Check for timeout
    if ((firstTapTime == 0 && (t - startTime > tapTimeout)) || (firstTapTime > 0 && (t - firstTapTime > samplingTime)) ) {
      sampling = false;
    }
  }
  detach_all_interrupts();
  firstTapTime = 0;
  Serial.println("sampling finished");
  Serial.println("start time");
  Serial.println(startTime);
  Serial.println("tap times");
  for (int finger=0; finger<nFingers; finger++) {
    for (int tap=0; tap<maxTaps; tap++) {
      if (interruptTime[finger][tap] != 0) {
        Serial.print(fingerName[finger]);
        Serial.print(",");
        Serial.println(interruptTime[finger][tap]);
        interruptTime[finger][tap] = 0; // reset
      }
    }
  }
  Serial.println("end of data");
}

int serial_get_int(boolean echo){
  if (echo) Serial.println(pythonSays);
  int serialInt;
  while (Serial.available() <= 0){
    // wait
  }
  serialInt = Serial.parseInt();
  if (echo) Serial.println(serialInt);
  return serialInt;
}

void setup_accelerometer(ADXL345 adxl, int accelerometerRange, int tapThreshold, int maxTapDuration) {
  adxl.standby(); // put accelerometer in standby before configuring
  adxl.setSpiBit(0); //4 wire SPI mode
  adxl.setRate(3200); // fastest data rate
  
  // FIFO control could go here

  // set full res or 10 bit
  adxl.setRangeSetting(accelerometerRange);  // 2G, 4G, 8G, 16G  
  //setAxisOffset(int x, int y, int z);
  
  // minimum amplitude for a tap (0-255):
  adxl.setTapThreshold(tapThreshold);           // 62.5 mG per increment (LSB)
  // time exceeding threshold must be shorter than this (0-255):
  adxl.setTapDuration(maxTapDuration);          // 0.625 ms per increment (LSB); 16 is 10ms
  // latency after which a second tap can't be detected (0-255):
  adxl.setTapDetectionOnXYZ(1, 1, 1); //1 = ON, 0 = OFF

  // set pin and enable/disable for each interrupt:
  // single tap, double tap, free fall, activity, inactivity
  adxl.setImportantInterruptMapping(1, 2, 2, 2, 2); // 1 = INT1, 2 = INT2
  adxl.enableInterrupts(1,0,0,0,0); // 0 = OFF, 1 = ON

  adxl.measureMode();
}

void clear_all_interrupts() {
    for (int finger=0; finger<nFingers; finger++) {
      accelerometer[finger].getInterruptSource(); // clear in the accelerometer
      interruptN[finger] = -1; // reset tap count
    }  
}

void attach_all_interrupts() {
  attachInterrupt(digitalPinToInterrupt(interruptPin[0]), TAP_ISR_0, RISING);
  attachInterrupt(digitalPinToInterrupt(interruptPin[1]), TAP_ISR_1, RISING);
  attachInterrupt(digitalPinToInterrupt(interruptPin[2]), TAP_ISR_2, RISING);
  attachInterrupt(digitalPinToInterrupt(interruptPin[3]), TAP_ISR_3, RISING);
  attachInterrupt(digitalPinToInterrupt(interruptPin[4]), TAP_ISR_4, RISING);
}

void detach_all_interrupts() {
    for (int finger=0; finger<nFingers; finger++) {
      detachInterrupt(digitalPinToInterrupt(interruptPin[finger]));
    }
}

void record_interrupt(int finger) {
  // getInterruptSource clears all triggered actions after returning value
  byte interrupts = accelerometer[finger].getInterruptSource();
  if (accelerometer[finger].triggered(interrupts, ADXL345_SINGLE_TAP) && interruptN[finger] < maxTaps){
    long timeNow = micros();
    if (interruptN[finger] < 0 || timeNow > tapDebounce*1000 + interruptTime[finger][(interruptN[finger]-1) % maxTaps]) {
      interruptN[finger]++;
      interruptTime[finger][interruptN[finger]] = timeNow;      
    }
  }
}

// INTERRUPT SERVICE ROUTINES (ISRs), ONE FOR EACH ACCELEROMETER

void TAP_ISR_0() {
  record_interrupt(0);
}

void TAP_ISR_1() {
  record_interrupt(1);
}

void TAP_ISR_2() {
  record_interrupt(2);
}

void TAP_ISR_3() {
  record_interrupt(3);
}

void TAP_ISR_4() {
  record_interrupt(4);
}
