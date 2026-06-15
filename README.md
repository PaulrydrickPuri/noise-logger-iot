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
1. Install [Arduino IDE](https://www.arduino.cc/en/software) (version 2.0+)
2. Add ESP32 board support:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install board: Tools → Board → Board Manager → search "esp32" → Install "esp32 by Espressif Systems"
4. Install libraries (Sketch → Include Library → Manage Libraries):
   - `ArduinoJson` by Benoit Blanchon (version 6.x)
   - Note: I2S driver is built-in with ESP32 Arduino core

### Configure Before Flashing
**IMPORTANT:** Edit `firmware/noise-logger/config.h` before flashing:

```cpp
// Update these with your actual WiFi credentials
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Update this with your laptop's IP address (see "Finding Your IP" below)
#define SERVER_URL "http://192.168.1.100:5000/api/events"
```

**Finding your laptop's IP address:**
- **Mac/Linux:** Open Terminal → type `ifconfig | grep "inet "` → look for `192.168.x.x`
- **Windows:** Open Command Prompt → type `ipconfig` → look for IPv4 Address (e.g., `192.168.1.100`)

### Flash Firmware
1. Connect ESP32 to your computer via USB-C cable
2. Open `firmware/noise-logger/noise-logger.ino` in Arduino IDE
3. Select board: Tools → Board → ESP32 Arduino → **DOIT ESP32 DEVKIT V1**
4. Select port: Tools → Port → (choose the port with "CH340" or "CP2102" in the name)
   - Mac: `/dev/cu.wchusbserial*` or `/dev/cu.SLAB_USBtoUART`
   - Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
   - Windows: `COM3` (or similar)
5. Click **Upload** (→ arrow button) or press Ctrl+U (Cmd+U on Mac)
6. Wait for "Done uploading" message
7. Open Serial Monitor (Tools → Serial Monitor, 115200 baud) to see output:
   ```
   === Noise Logger Starting ===
   Device ID: noise-logger-001
   Watchdog timer initialized (30s timeout)
   I2S initialized successfully
   Connecting to WiFi: YOUR_WIFI_SSID....
   WiFi connected!
   IP address: 192.168.1.50
   Time synchronized via NTP
   dB: 45.2 (RMS: 123.4)
   ```

**Troubleshooting:**
- If upload fails, hold the **BOOT** button on ESP32 while clicking Upload
- If "Failed to connect" error, press the **EN (Reset)** button once
- If wrong port, try different USB ports or check Device Manager (Windows)

## Server Setup (Python Flask)

### Prerequisites
- Python 3.9+ (check with `python3 --version`)
- pip (Python package manager)

### Install and Run
```bash
# Navigate to server directory
cd server

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

You should see:
```
Database initialized
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

**Important:** The server must run on the same WiFi network as your ESP32. Use the IP address shown (e.g., `192.168.1.100`) in your ESP32's `config.h`.

### Keep Server Running 24/7
For continuous monitoring, keep the server running on a laptop or Raspberry Pi:
- **Mac/Linux:** `nohup python app.py &` (runs in background)
- **Windows:** Create a batch file: `start python app.py`
- **Advanced:** Use `systemd` service or Docker for production deployment

### Web Dashboard
Open `http://localhost:5000` (or your laptop's IP) in your browser to see:
- **Live dB gauge** — Current noise level (updates every 5 seconds)
- **Statistics** — Total events, average dB, peak dB, total duration
- **Event timeline chart** — Bar chart showing all noise events over time
- **Recent events table** — Detailed list with timestamps and durations
- **Generate Report button** — Download PDF evidence report

### Generate PDF Report
**From the dashboard:**
1. Select date range (optional) using "From" and "To" date pickers
2. Click "Generate PDF Report"
3. Download the PDF file

**From command line:**
```bash
# All events
curl http://localhost:5000/api/report -o noise_report_all.pdf

# Specific date range
curl "http://localhost:5000/api/report?from=2024-01-01&to=2024-01-31" -o noise_report_jan2024.pdf
```

**The PDF includes:**
- Cover page with report title and date range
- Summary statistics table (total events, average/peak dB, duration)
- Event timeline chart (visual graph of all events)
- Top 10 worst incidents table (highest dB readings)
- Legal reference box (Strata Management Act 2013, By-law 4)
- Footer with device ID and generation timestamp

## Calibration

The INMP441 microphone provides relative dB readings. Calibration makes them more accurate for legal evidence.

### Quick Calibration (Recommended)
1. **Install an SPL meter app** on your smartphone:
   - iOS: "Decibel X" or "NIOSH SLM"
   - Android: "Sound Meter" or "Decibel X"

2. **Set up calibration environment:**
   - Place ESP32 with INMP441 on a table
   - Position phone's microphone 10cm away from INMP441
   - Ensure quiet room (turn off AC, fans, TV)

3. **Generate steady noise:**
   - Play YouTube video: "70 dB white noise calibration tone"
   - Set phone volume to maximum
   - Place phone speaker 30cm from both microphones

4. **Compare readings:**
   - Open ESP32 Serial Monitor (115200 baud) → note the dB value (e.g., 65 dB)
   - Check phone app → note the dB value (e.g., 70 dB)
   - Calculate difference: 70 - 65 = 5 dB

5. **Adjust calibration factor:**
   - Open `firmware/noise-logger/config.h`
   - Update: `#define CALIBRATION_FACTOR 1.0` → `#define CALIBRATION_FACTOR 1.2`
   - Formula: `new_factor = old_factor * (phone_db / esp32_db)`
   - Example: `1.0 * (70 / 65) = 1.08` ≈ 1.1

6. **Re-flash and verify:**
   - Upload firmware again
   - Repeat step 3-4
   - Readings should now match within ±3 dB

### Calibration Tips
- **Don't need perfect accuracy** — ±5 dB is acceptable for evidence
- **Calibrate at multiple levels** if possible (50 dB, 60 dB, 70 dB)
- **Room acoustics matter** — calibrate in the room where you'll use the device
- **Skip calibration** if you just want to detect "loud vs quiet" events (default factor 1.0 works fine)

### Default Settings (No Calibration)
If you skip calibration, the device still works:
- Threshold: 55 dB (WHO residential guideline)
- Event detection: 2+ seconds above threshold
- Relative dB readings are consistent for trend analysis

## Usage

### Step 1: Initial Setup (One-Time)
1. **Wire the components** following the Wiring Diagram above
2. **Configure WiFi** in `config.h` (see Firmware Setup)
3. **Flash firmware** to ESP32 (see Firmware Setup)
4. **Start the server** on your laptop (see Server Setup)
5. **Verify connection** — ESP32 Serial Monitor should show "WiFi connected!"

### Step 2: Deploy the Device
1. **Choose location:**
   - Place ESP32 in the room where noise is most problematic (e.g., bedroom, living room)
   - Position INMP441 microphone facing the noise source (e.g., shared wall, ceiling)
   - Keep device 1-2 meters from walls for best acoustic pickup
   - Avoid placing near your own noise sources (TV, speakers)

2. **Power on:**
   - Plug USB-C cable into a 5V phone charger (any standard charger works)
   - ESP32 LED should light up
   - Serial Monitor shows boot sequence (if connected to computer)

3. **Wait for WiFi connection:**
   - Takes 10-30 seconds
   - Device automatically syncs time via NTP
   - Ready when Serial Monitor shows "dB: XX.X" readings

### Step 3: Monitor Noise (24/7 Operation)
- **Automatic detection:** Device logs events when noise exceeds 55 dB for 2+ seconds
- **Event logging:** Each event records timestamp, peak dB, and duration
- **Server storage:** Events sent to Flask server via WiFi (stored in SQLite database)
- **Auto-reconnect:** Device automatically reconnects if WiFi drops

**What gets logged:**
- Loud music, TV, parties (typically 70-90 dB)
- Construction/renovation noise (80-100 dB)
- Shouting, arguments (65-80 dB)
- Banging, stomping (60-75 dB)

**What doesn't get logged (below threshold):**
- Normal conversation (50-60 dB)
- Air conditioning (40-50 dB)
- Refrigerator hum (30-40 dB)
- Quiet background noise (20-30 dB)

### Step 4: Review Events
1. **Open dashboard:** `http://localhost:5000` on your laptop
2. **Check statistics:** See total events, average dB, peak dB
3. **View timeline:** Bar chart shows when events occurred
4. **Inspect details:** Table lists each event with timestamp and duration

### Step 5: Generate Evidence Report
When ready to file a complaint with JMB/MC:
1. Open dashboard
2. Select date range (e.g., "last 30 days")
3. Click "Generate PDF Report"
4. Download and print the PDF
5. Submit to your building management office with a written complaint

**Report contents:**
- Professional format suitable for legal proceedings
- Timestamped evidence with exact dB levels
- Visual timeline chart showing pattern of disturbances
- Reference to Strata Management Act 2013, By-law 4
- Device ID for verification

### Troubleshooting

**ESP32 won't connect to WiFi:**
- Double-check SSID and password in `config.h` (case-sensitive)
- Ensure laptop and ESP32 are on the same WiFi network (2.4 GHz, not 5 GHz guest network)
- Move ESP32 closer to WiFi router
- Check Serial Monitor for error messages

**Events not appearing on dashboard:**
- Verify server is running (`python app.py`)
- Check `SERVER_URL` in `config.h` matches your laptop's IP address
- Ensure firewall allows port 5000 (Mac: System Preferences → Security → Firewall → Allow incoming connections for Python)
- Test manually: `curl http://YOUR_IP:5000/api/events`

**False positives (logging normal sounds):**
- Increase threshold in `config.h`: `#define DB_THRESHOLD 65.0` (instead of 55.0)
- Reposition microphone away from your own noise sources
- Calibrate microphone (see Calibration section)

**No events detected (missing loud noises):**
- Decrease threshold: `#define DB_THRESHOLD 45.0`
- Check microphone wiring (SCK, WS, SD pins)
- Verify Serial Monitor shows dB readings changing
- Test with loud music or clapping near microphone

**PDF report is empty:**
- Ensure you have events in the database (check dashboard first)
- Try generating report without date filters
- Check server console for error messages

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
