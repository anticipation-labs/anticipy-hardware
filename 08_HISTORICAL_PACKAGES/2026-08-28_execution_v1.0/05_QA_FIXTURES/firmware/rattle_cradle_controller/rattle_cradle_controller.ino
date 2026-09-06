/*
  Anticipy slow rattle-cradle controller, revision 1.0

  This is a screening fixture, not a safety-rated machine controller.
  The polycarbonate guard, fuse, current limit and normally-closed hardware
  stop loop remain mandatory.  An experienced adult must build and operate it.

  Arduino Nano -> TMC2209 in STEP/DIR standalone mode
    D3  STEP
    D4  DIR
    D5  EN       (LOW enables driver)
    D6  HOME_NC  (LOW at home; INPUT_PULLUP)
    D7  GUARD_NC (LOW only when guard is closed; INPUT_PULLUP)
    D8  START    (momentary to GND)
    D9  STOP_NC  (LOW when healthy; opens HIGH to stop)
    D10 MARKER   (HIGH only during a quiet acoustic sample)
    D13 status LED

  Mechanics assumed by this file:
    200 full-step/rev motor, 1/16 microstepping, 20T:60T belt reduction.
    Therefore one cradle-shaft revolution = 9,600 STEP pulses.
*/

#include <Arduino.h>

constexpr uint8_t PIN_STEP = 3;
constexpr uint8_t PIN_DIR = 4;
constexpr uint8_t PIN_ENABLE_N = 5;
constexpr uint8_t PIN_HOME_N = 6;
constexpr uint8_t PIN_GUARD_N = 7;
constexpr uint8_t PIN_START_N = 8;
constexpr uint8_t PIN_STOP_N = 9;
constexpr uint8_t PIN_MARKER = 10;
constexpr uint8_t PIN_STATUS = LED_BUILTIN;

constexpr long SHAFT_STEPS_PER_REV = 200L * 16L * 3L;
constexpr long ENDPOINT_STEPS = (SHAFT_STEPS_PER_REV * 170L) / 360L;
constexpr uint16_t FULL_CYCLES = 10;
constexpr uint16_t HALF_CYCLES = FULL_CYCLES * 2;
constexpr unsigned long STEP_INTERVAL_US = 3125UL;  // 320 pulses/s = 2 shaft rpm
constexpr unsigned long HOME_STEP_INTERVAL_US = 4000UL;
constexpr unsigned long PAUSE_MS = 2000UL;
constexpr unsigned long DEBOUNCE_MS = 30UL;
constexpr long HOME_SEARCH_LIMIT = SHAFT_STEPS_PER_REV * 2L;

enum class State : uint8_t { IDLE, HOMING, MOVING, PAUSING, COMPLETE, FAULT };

State state = State::IDLE;
long positionSteps = 0;
long targetSteps = 0;
long homeSteps = 0;
uint16_t completedHalfCycles = 0;
bool nextDirectionPositive = true;
unsigned long lastStepUs = 0;
unsigned long pauseStartedMs = 0;
unsigned long lastStartChangeMs = 0;
bool previousStart = HIGH;

bool guardClosed() { return digitalRead(PIN_GUARD_N) == LOW; }
bool stopLoopHealthy() { return digitalRead(PIN_STOP_N) == LOW; }
bool homeActive() { return digitalRead(PIN_HOME_N) == LOW; }

void driverOff() {
  digitalWrite(PIN_ENABLE_N, HIGH);
  digitalWrite(PIN_MARKER, LOW);
}

void fault(const __FlashStringHelper *reason) {
  driverOff();
  state = State::FAULT;
  Serial.print(F("FAULT,"));
  Serial.println(reason);
}

void pulseStep(bool positive) {
  digitalWrite(PIN_DIR, positive ? HIGH : LOW);
  digitalWrite(PIN_STEP, HIGH);
  delayMicroseconds(4);
  digitalWrite(PIN_STEP, LOW);
  positionSteps += positive ? 1 : -1;
}

bool startPressedOnce() {
  const bool now = digitalRead(PIN_START_N);
  const unsigned long t = millis();
  bool event = false;
  if (now != previousStart && (t - lastStartChangeMs) >= DEBOUNCE_MS) {
    lastStartChangeMs = t;
    previousStart = now;
    if (now == LOW) event = true;
  }
  return event;
}

void beginHoming() {
  if (!guardClosed() || !stopLoopHealthy()) {
    fault(F("GUARD_OR_STOP_OPEN"));
    return;
  }
  digitalWrite(PIN_ENABLE_N, LOW);
  digitalWrite(PIN_STATUS, HIGH);
  homeSteps = 0;
  lastStepUs = micros();
  state = State::HOMING;
  Serial.println(F("HOMING"));
}

void beginRunAtHome() {
  positionSteps = 0;
  completedHalfCycles = 0;
  nextDirectionPositive = true;
  targetSteps = ENDPOINT_STEPS;
  lastStepUs = micros();
  state = State::MOVING;
  Serial.print(F("MOTION,target_steps,"));
  Serial.println(targetSteps);
}

void enterPause() {
  digitalWrite(PIN_MARKER, HIGH);
  pauseStartedMs = millis();
  state = State::PAUSING;
  Serial.print(F("PAUSE,endpoint,"));
  Serial.print(completedHalfCycles + 1);
  Serial.print(F(",position_steps,"));
  Serial.println(positionSteps);
}

void setup() {
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_ENABLE_N, OUTPUT);
  pinMode(PIN_MARKER, OUTPUT);
  pinMode(PIN_STATUS, OUTPUT);
  pinMode(PIN_HOME_N, INPUT_PULLUP);
  pinMode(PIN_GUARD_N, INPUT_PULLUP);
  pinMode(PIN_START_N, INPUT_PULLUP);
  pinMode(PIN_STOP_N, INPUT_PULLUP);
  driverOff();
  digitalWrite(PIN_STATUS, LOW);
  previousStart = digitalRead(PIN_START_N);
  Serial.begin(115200);
  Serial.println(F("ANTICIPY_RATTLE_FIXTURE,READY"));
}

void loop() {
  const bool startEvent = startPressedOnce();

  if (state != State::IDLE && state != State::COMPLETE && state != State::FAULT) {
    if (!guardClosed()) {
      fault(F("GUARD_OPENED"));
      return;
    }
    if (!stopLoopHealthy()) {
      fault(F("STOP_OPENED"));
      return;
    }
  }

  if (state == State::IDLE && startEvent) {
    beginHoming();
    return;
  }

  if ((state == State::COMPLETE || state == State::FAULT) && startEvent) {
    if (guardClosed() && stopLoopHealthy()) {
      state = State::IDLE;
      digitalWrite(PIN_STATUS, LOW);
      Serial.println(F("RESET_TO_IDLE;PRESS_START_TO_HOME"));
    }
    return;
  }

  if (state == State::HOMING) {
    if (homeActive()) {
      Serial.println(F("HOME_FOUND"));
      beginRunAtHome();
      return;
    }
    if (homeSteps >= HOME_SEARCH_LIMIT) {
      fault(F("HOME_NOT_FOUND"));
      return;
    }
    const unsigned long nowUs = micros();
    if ((unsigned long)(nowUs - lastStepUs) >= HOME_STEP_INTERVAL_US) {
      lastStepUs = nowUs;
      pulseStep(false);
      ++homeSteps;
    }
    return;
  }

  if (state == State::MOVING) {
    if (positionSteps == targetSteps) {
      enterPause();
      return;
    }
    const unsigned long nowUs = micros();
    if ((unsigned long)(nowUs - lastStepUs) >= STEP_INTERVAL_US) {
      lastStepUs = nowUs;
      pulseStep(targetSteps > positionSteps);
    }
    return;
  }

  if (state == State::PAUSING && millis() - pauseStartedMs >= PAUSE_MS) {
    digitalWrite(PIN_MARKER, LOW);
    ++completedHalfCycles;
    if (completedHalfCycles >= HALF_CYCLES) {
      driverOff();
      digitalWrite(PIN_STATUS, LOW);
      state = State::COMPLETE;
      Serial.println(F("COMPLETE,10_FULL_CYCLES"));
      return;
    }
    nextDirectionPositive = !nextDirectionPositive;
    targetSteps = nextDirectionPositive ? ENDPOINT_STEPS : -ENDPOINT_STEPS;
    lastStepUs = micros();
    state = State::MOVING;
    Serial.print(F("MOTION,target_steps,"));
    Serial.println(targetSteps);
  }
}
