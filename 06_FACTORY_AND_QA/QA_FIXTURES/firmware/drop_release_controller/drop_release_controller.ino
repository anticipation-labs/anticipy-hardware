/*
  Anticipy drop-release controller, revision 1.0

  This drives a MOSFET module; it MUST NOT drive a solenoid directly from an
  Arduino pin. Fit a flyback diode at the coil, a 12 V fuse, a normally-closed
  guard switch and a physical ARM switch. The operator stays outside the guard.

  Arduino Nano pin map
    D6  GUARD_N  (LOW only when guard is closed)
    D7  ARM_N    (LOW when deliberately armed)
    D8  DROP_N   (momentary button to GND)
    D9  SOLENOID (to logic-level MOSFET input, active HIGH)
    D10 READY_LED
*/

#include <Arduino.h>

constexpr uint8_t PIN_GUARD_N = 6;
constexpr uint8_t PIN_ARM_N = 7;
constexpr uint8_t PIN_DROP_N = 8;
constexpr uint8_t PIN_SOLENOID = 9;
constexpr uint8_t PIN_READY_LED = 10;
constexpr unsigned long MAX_PULSE_MS = 250UL;
constexpr unsigned long DEBOUNCE_MS = 40UL;

enum class ReleaseState : uint8_t { SAFE, READY, FIRING, LOCKOUT };
ReleaseState state = ReleaseState::SAFE;
unsigned long pulseStartedMs = 0;
unsigned long dropChangedMs = 0;
bool previousDrop = HIGH;

bool guardClosed() { return digitalRead(PIN_GUARD_N) == LOW; }
bool armed() { return digitalRead(PIN_ARM_N) == LOW; }

void coilOff() { digitalWrite(PIN_SOLENOID, LOW); }

bool dropPressedOnce() {
  const bool now = digitalRead(PIN_DROP_N);
  const unsigned long t = millis();
  bool event = false;
  if (now != previousDrop && (t - dropChangedMs) >= DEBOUNCE_MS) {
    dropChangedMs = t;
    previousDrop = now;
    if (now == LOW) event = true;
  }
  return event;
}

void setup() {
  pinMode(PIN_GUARD_N, INPUT_PULLUP);
  pinMode(PIN_ARM_N, INPUT_PULLUP);
  pinMode(PIN_DROP_N, INPUT_PULLUP);
  pinMode(PIN_SOLENOID, OUTPUT);
  pinMode(PIN_READY_LED, OUTPUT);
  coilOff();
  digitalWrite(PIN_READY_LED, LOW);
  previousDrop = digitalRead(PIN_DROP_N);
  Serial.begin(115200);
  Serial.println(F("ANTICIPY_DROP_FIXTURE,SAFE"));
}

void loop() {
  const bool dropEvent = dropPressedOnce();

  // Opening the guard always removes coil power in software as a second layer.
  if (!guardClosed()) {
    coilOff();
    digitalWrite(PIN_READY_LED, LOW);
    state = ReleaseState::SAFE;
    return;
  }

  if (state == ReleaseState::SAFE) {
    if (armed() && digitalRead(PIN_DROP_N) == HIGH) {
      state = ReleaseState::READY;
      digitalWrite(PIN_READY_LED, HIGH);
      Serial.println(F("READY"));
    }
    return;
  }

  if (state == ReleaseState::READY) {
    if (!armed()) {
      digitalWrite(PIN_READY_LED, LOW);
      state = ReleaseState::SAFE;
      return;
    }
    if (dropEvent) {
      digitalWrite(PIN_READY_LED, LOW);
      digitalWrite(PIN_SOLENOID, HIGH);
      pulseStartedMs = millis();
      state = ReleaseState::FIRING;
      Serial.println(F("DROP_PULSE_START"));
    }
    return;
  }

  if (state == ReleaseState::FIRING) {
    if (!armed() || millis() - pulseStartedMs >= MAX_PULSE_MS) {
      coilOff();
      state = ReleaseState::LOCKOUT;
      Serial.println(F("DROP_PULSE_END,LOCKOUT"));
    }
    return;
  }

  // One release per arm cycle.  ARM must be turned off and DROP released.
  if (state == ReleaseState::LOCKOUT && !armed() && digitalRead(PIN_DROP_N) == HIGH) {
    state = ReleaseState::SAFE;
    Serial.println(F("RESET_SAFE"));
  }
}
