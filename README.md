# Noise Complaint Logger

An ESP32-based noise monitoring device for Malaysian condo residents to document noise disturbances for JMB/MC complaints under the Strata Management Act 2013.

## Overview

This device runs 24/7, continuously monitors ambient noise levels, detects noise events, and logs them to a web server. You can then generate professional PDF reports with timestamped evidence to submit to your building management.

## Hardware (BOM)

| Item | Price (RM) | Notes |
|---|---|---|
| ESP32 DOIT Development Board (CH340 Type-C) + Expansion Base | 23.50 | Pre-soldered, dual-core |
| INMP441 I2S MEMS Microphone Module | 19.99 | Pre-soldered breakout board |
| OLED 0.96" I2C 128x64 Display (Blue) | 13.00 | Optional - arriving soon |
| Jumper Wires Female-to-Female 10cm (40pc) | ~2.00 |  |
| USB-C Cable | 3.47 | For power |
| **Total** | **~62.96** |  |

All components are pre-soldered — no soldering required.

## Wiring Diagram

### INMP441 Microphone → ESP32

| INMP441 Pin | ESP32 Pin | Wire Color (suggested) |
|---|---|---|
| VCC | 3.3V | Red |
| GND | GND | Black |
| SCK | GPIO 26 | Yellow |
| WS | GPIO 25 | Green |
| SD | GPIO 33 | Blue |

### OLED Display → ESP32 (Optional)

| OLED Pin | ESP32 Pin | Wire Color |
|---|---|---|
| VCC | 3.3V | Red |
| GND | GND | Black |
| SDA | GPIO 21 | Orange |
| SCL | GPIO 22 | White |

**Note:** I2S (microphone) and I2C (OLED) use separate buses — no pin conflicts.

## Firmware Setup (ESP32)

### Prerequisites
1. Install [Arduino IDE](https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install board: Tools → Board → Board Manager → search "esp32" → Install
4. Install libraries (Sketch → Include Library → Manage Libraries):
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`

### Flash Firmware
1. Open `firmware/noise-logger/noise-logger.ino` in Arduino IDE
2. Select board: Tools → Board → ESP32 Dev Module
3. Select port: Tools → Port → (your ESP32's COM port)
4. Upload (Ctrl+U or Cmd+U)

### Configure WiFi
Edit `config.h` and update:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* server_url = "http://YOUR_LAPTOP_IP:5000/api/events";
```

## Server Setup (Python Flask)

### Prerequisites
- Python 3.9+
- pip

### Install and Run
```bash
cd server
pip install -r requirements.txt
python app.py
```

The server will start at `http://localhost:5000`.

### Web Dashboard
Open `http://localhost:5000` in your browser to see:
- Live dB readings (polls every 5 seconds)
- Event timeline chart
- Recent events table
- "Generate Report" button

### Generate PDF Report
Click "Generate Report" on the dashboard, or:
```bash
curl http://localhost:5000/api/report -o noise_report.pdf
```

The PDF includes:
- Summary statistics (total events, average dB, peak dB)
- Event timeline chart
- Top 10 worst incidents table
- Legal reference (Strata Management Act 2013, By-law 4)

## Calibration

1. Place a smartphone with an SPL meter app (e.g., "Decibel X") next to the INMP441 microphone
2. Play steady white noise (YouTube "70 dB white noise")
3. Compare the ESP32 Serial Monitor output with the phone reading
4. Adjust `CALIBRATION_FACTOR` in `config.h` until readings match within ±3 dB
5. Re-flash the ESP32

Example: If phone shows 70 dB but ESP32 shows 65 dB, increase the factor from 1.0 to ~1.2.

## Usage

1. **Power on** the ESP32 (plug USB-C into a phone charger)
2. **Wait for WiFi** — OLED will show "WiFi:OK" when connected
3. **Monitor noise** — The device logs events automatically when noise exceeds the threshold (default: 55 dB for 2+ seconds)
4. **Generate report** — When ready to file a complaint, open the dashboard and click "Generate Report"
5. **Submit evidence** — Print the PDF and submit it to your JMB/MC office

## Project Structure

```
noise-logger/
├── firmware/
│   └── noise-logger/
│       ├── noise-logger.ino    # Main ESP32 firmware
│       └── config.h            # Pin definitions and WiFi config
├── server/
│   ├── app.py                  # Flask server
│   ├── db.py                   # SQLite database operations
│   ├── report.py               # PDF report generation
│   ├── requirements.txt        # Python dependencies
│   ├── templates/
│   │   └── dashboard.html      # Web dashboard
│   └── tests/
│       ├── test_db.py          # Database tests
│       └── test_report.py      # Report generation tests
├── docs/
│   ├── plans/
│   │   └── noise-logger.md     # Detailed implementation plan
│   └── checklists/
│       └── noise-logger-checklist.md  # Task checklist
└── README.md                   # This file
```

## Implementation Plan

See `docs/plans/noise-logger.md` for the full 25-task implementation plan with exact code snippets and verification steps.

See `docs/checklists/noise-logger-checklist.md` for the task checklist to track progress.

## Legal Context

This project is designed to help Malaysian condo residents document noise disturbances under the **Strata Management Act 2013 (Act 757)**, Third Schedule, **By-law 4 (Noise)**:

> "An owner or occupier shall not create any noise likely to disturb the peaceful enjoyment of other owners or occupiers."

The generated PDF reports reference this law and provide timestamped evidence suitable for submission to JMB/MC management or the Tribunal for Strata Management.

**WHO residential noise guideline:** 55 dB maximum during daytime, 45 dB at night.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Contributing

Pull requests welcome! Please follow the implementation plan in `docs/plans/noise-logger.md` and update the checklist in `docs/checklists/noise-logger-checklist.md` as you complete tasks.
