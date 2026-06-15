#ifndef CONFIG_H
#define CONFIG_H

// I2S Microphone Pins (INMP441)
#define I2S_BCLK_PIN 26    // Bit Clock
#define I2S_LRCLK_PIN 25   // Left/Right Clock (Word Select)
#define I2S_DIN_PIN 33     // Serial Data

// I2C OLED Display Pins (when available)
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

// Noise Detection Settings
#define DB_THRESHOLD 55.0           // dB SPL threshold (WHO residential guideline)
#define EVENT_DURATION_MS 2000      // Minimum duration for noise event (ms)
#define CALIBRATION_FACTOR 1.0      // Adjust this during calibration

// Audio Sampling Settings
#define SAMPLE_RATE 16000           // Samples per second
#define SAMPLE_BITS 16              // Bits per sample
#define CHANNEL_NUM 1               // Mono
#define BUFFER_SIZE 1024            // I2S buffer size in samples

// WiFi Settings
#define WIFI_SSID "Chevngko"
#define WIFI_PASSWORD "Summer1180"

// Server Settings
#define SERVER_URL "http://192.168.100.18:5000/api/events"
#define DEVICE_ID "noise-logger-001"

// Display Settings (when OLED available)
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

#endif
