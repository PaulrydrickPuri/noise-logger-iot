#include "config.h"

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Noise Logger Starting ===");
  Serial.println("Device ID: " DEVICE_ID);
}

void loop() {
  // Main loop will be implemented in subsequent tasks
  delay(1000);
  Serial.println("Noise Logger initialized - waiting for implementation");
}
