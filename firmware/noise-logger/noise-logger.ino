#include "config.h"
#include <driver/i2s.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// I2S buffer for audio samples
int16_t audioBuffer[BUFFER_SIZE];
size_t bytesRead = 0;

// Noise event tracking
struct NoiseEvent {
  unsigned long timestamp;
  float peakDB;
  unsigned long durationMs;
  bool active;
};

NoiseEvent currentEvent = {0, 0, 0, false};
int eventCounter = 0;

void initI2S() {
  // I2S configuration
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  // Pin configuration
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCLK_PIN,
    .ws_io_num = I2S_LRCLK_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_DIN_PIN
  };

  // Install and start I2S driver
  esp_err_t err = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  if (err != ESP_OK) {
    Serial.printf("Failed to install I2S driver: %d\n", err);
    return;
  }

  err = i2s_set_pin(I2S_NUM_0, &pin_config);
  if (err != ESP_OK) {
    Serial.printf("Failed to set I2S pins: %d\n", err);
    return;
  }

  Serial.println("I2S initialized successfully");
}

void initWiFi() {
  Serial.printf("Connecting to WiFi: %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi");
  }
}

float calculateRMS(int16_t* samples, size_t count) {
  float sum = 0;
  for (size_t i = 0; i < count; i++) {
    sum += (float)samples[i] * samples[i];
  }
  return sqrt(sum / count);
}

float calculateDB(float rms) {
  if (rms < 1.0) rms = 1.0; // Prevent log(0)
  return 20.0 * log10(rms * CALIBRATION_FACTOR);
}

void processNoiseEvent(float dbSPL) {
  unsigned long currentTime = millis();

  // Check if dB exceeds threshold
  if (dbSPL > DB_THRESHOLD) {
    if (!currentEvent.active) {
      // Start new event
      currentEvent.active = true;
      currentEvent.timestamp = currentTime;
      currentEvent.peakDB = dbSPL;
      currentEvent.durationMs = 0;
      Serial.printf("Noise event started: %.1f dB\n", dbSPL);
    } else {
      // Update ongoing event
      currentEvent.durationMs = currentTime - currentEvent.timestamp;
      if (dbSPL > currentEvent.peakDB) {
        currentEvent.peakDB = dbSPL;
      }
    }
  } else {
    // dB below threshold - check if we have an active event
    if (currentEvent.active) {
      currentEvent.durationMs = currentTime - currentEvent.timestamp;

      // Only log if event lasted long enough (debouncing)
      if (currentEvent.durationMs >= EVENT_DURATION_MS) {
        eventCounter++;
        Serial.printf("=== NOISE EVENT #%d ===\n", eventCounter);
        Serial.printf("Peak dB: %.1f\n", currentEvent.peakDB);
        Serial.printf("Duration: %lu ms\n", currentEvent.durationMs);
        Serial.printf("Timestamp: %lu\n", currentEvent.timestamp);
        Serial.println("========================");

        // TODO: Send to server (Task 8)
      } else {
        Serial.printf("Event too short (%lu ms), ignored\n", currentEvent.durationMs);
      }

      // Reset event
      currentEvent.active = false;
      currentEvent.timestamp = 0;
      currentEvent.peakDB = 0;
      currentEvent.durationMs = 0;
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Noise Logger Starting ===");
  Serial.println("Device ID: " DEVICE_ID);

  initI2S();
  initWiFi();
}

void loop() {
  // Read audio samples from I2S
  esp_err_t result = i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytesRead, portMAX_DELAY);

  if (result == ESP_OK && bytesRead > 0) {
    size_t samplesRead = bytesRead / sizeof(int16_t);

    // Calculate RMS and dB
    float rms = calculateRMS(audioBuffer, samplesRead);
    float dbSPL = calculateDB(rms);

    // Print to Serial Monitor
    Serial.printf("dB: %.1f (RMS: %.1f)\n", dbSPL, rms);

    // Process noise event detection
    processNoiseEvent(dbSPL);
  }

  delay(100); // Update 10 times per second
}
