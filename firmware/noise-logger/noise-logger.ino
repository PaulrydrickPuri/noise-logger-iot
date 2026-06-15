#include "config.h"
#include <driver/i2s.h>

// I2S buffer for audio samples
int16_t audioBuffer[BUFFER_SIZE];
size_t bytesRead = 0;

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

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Noise Logger Starting ===");
  Serial.println("Device ID: " DEVICE_ID);

  initI2S();
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
    Serial.printf("dB: %.1f (RMS: %.1f, Samples: %d)\n", dbSPL, rms, samplesRead);
  }

  delay(100); // Update 10 times per second
}
