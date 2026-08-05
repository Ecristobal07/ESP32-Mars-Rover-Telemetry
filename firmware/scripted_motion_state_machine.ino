// =====================================================
// ESP32 Rover: Non-Blocking Motion State Machine
// TB6612FNG + four TT motors
// =====================================================

// Left side — TB6612 Channel A
#define PWMA 25
#define AIN1 26
#define AIN2 27

// Right side — TB6612 Channel B
#define PWMB 33
#define BIN1 32
#define BIN2 13

#define STBY 14

const int MOTOR_SPEED = 180;

// Every possible rover state
enum RoverState {
  FORWARD,
  STOP_AFTER_FORWARD,
  BACKWARD,
  STOP_AFTER_BACKWARD,
  TURN_LEFT,
  STOP_AFTER_LEFT,
  TURN_RIGHT,
  FINAL_STOP
};

RoverState currentState = FORWARD;

unsigned long stateStartTime = 0;
unsigned long lastTelemetryTime = 0;

// =====================================================
// Individual motor-side functions
// =====================================================

void leftForward(int speed) {
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, speed);
}

void leftBackward(int speed) {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, speed);
}

void leftStop() {
  analogWrite(PWMA, 0);
}

void rightForward(int speed) {
  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMB, speed);
}

void rightBackward(int speed) {
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, HIGH);
  analogWrite(PWMB, speed);
}

void rightStop() {
  analogWrite(PWMB, 0);
}

// =====================================================
// High-level rover commands
// =====================================================

void moveForward() {
  leftForward(MOTOR_SPEED);
  rightForward(MOTOR_SPEED);
}

void moveBackward() {
  leftBackward(MOTOR_SPEED);
  rightBackward(MOTOR_SPEED);
}

void pivotLeft() {
  leftBackward(MOTOR_SPEED);
  rightForward(MOTOR_SPEED);
}

void pivotRight() {
  leftForward(MOTOR_SPEED);
  rightBackward(MOTOR_SPEED);
}

void stopRover() {
  leftStop();
  rightStop();
}

// =====================================================
// State helper functions
// =====================================================

void enterState(RoverState newState) {
  currentState = newState;
  stateStartTime = millis();

  switch (currentState) {
    case FORWARD:
      moveForward();
      break;

    case BACKWARD:
      moveBackward();
      break;

    case TURN_LEFT:
      pivotLeft();
      break;

    case TURN_RIGHT:
      pivotRight();
      break;

    default:
      stopRover();
      break;
  }
}

const char* getStateName() {
  switch (currentState) {
    case FORWARD:
      return "FORWARD";

    case STOP_AFTER_FORWARD:
    case STOP_AFTER_BACKWARD:
    case STOP_AFTER_LEFT:
    case FINAL_STOP:
      return "STOPPED";

    case BACKWARD:
      return "BACKWARD";

    case TURN_LEFT:
      return "TURN_LEFT";

    case TURN_RIGHT:
      return "TURN_RIGHT";

    default:
      return "UNKNOWN";
  }
}

// =====================================================
// Setup
// =====================================================

void setup() {
  Serial.begin(115200);

  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);

  pinMode(PWMB, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);

  pinMode(STBY, OUTPUT);

  digitalWrite(STBY, HIGH);

  enterState(FORWARD);
}

// =====================================================
// Main loop
// =====================================================

void loop() {
  unsigned long now = millis();
  unsigned long timeInState = now - stateStartTime;

  // Change movement states without delay()
  switch (currentState) {
    case FORWARD:
      if (timeInState >= 2000) {
        enterState(STOP_AFTER_FORWARD);
      }
      break;

    case STOP_AFTER_FORWARD:
      if (timeInState >= 1000) {
        enterState(BACKWARD);
      }
      break;

    case BACKWARD:
      if (timeInState >= 2000) {
        enterState(STOP_AFTER_BACKWARD);
      }
      break;

    case STOP_AFTER_BACKWARD:
      if (timeInState >= 1000) {
        enterState(TURN_LEFT);
      }
      break;

    case TURN_LEFT:
      if (timeInState >= 1500) {
        enterState(STOP_AFTER_LEFT);
      }
      break;

    case STOP_AFTER_LEFT:
      if (timeInState >= 1000) {
        enterState(TURN_RIGHT);
      }
      break;

    case TURN_RIGHT:
      if (timeInState >= 1500) {
        enterState(FINAL_STOP);
      }
      break;

    case FINAL_STOP:
      if (timeInState >= 2000) {
        enterState(FORWARD);
      }
      break;
  }

  // Placeholder telemetry task
  // This continues running while the motors move.
  if (now - lastTelemetryTime >= 500) {
    lastTelemetryTime = now;

    Serial.print("time_ms=");
    Serial.print(now);
    Serial.print(", rover_state=");
    Serial.println(getStateName());
  }
}
