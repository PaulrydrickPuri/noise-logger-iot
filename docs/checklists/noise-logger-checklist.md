# Work Package Checklist: Noise Complaint Logger
**Plan:** docs/plans/noise-logger.md
**Branch:** main
**Status:** 🔴 Not started

---

## 🔧 Firmware (Arduino-ESP32)
**Assignee:** @paulrydrickpuri
- [ ] Task 1: Initialize Arduino project — `Arduino IDE compiles`
- [ ] Task 2: I2S audio sampling — `Serial monitor prints audio samples`
- [ ] Task 3: RMS to dB SPL calculation — `Serial prints dB values`
- [ ] Task 4: OLED display initialization — `OLED shows boot message`
- [ ] Task 5: OLED real-time dB display — `OLED updates dB every 500ms`
- [ ] Task 6: WiFi connection — `Serial prints IP address`
- [ ] Task 7: Noise event detection — `Event counter increments on sustained noise`
- [ ] Task 8: HTTP POST events to server — `Server receives POST with event JSON`
- [ ] Task 22: Calibration factor — `dB matches phone SPL meter within ±3 dB`
- [ ] Task 23: Watchdog timer — `ESP32 auto-reboots on hang`
- [ ] Task 25: OLED sparkline mini-graph — `OLED shows dB history sparkline`

## 🐍 Backend (Python Flask)
**Assignee:** @paulrydrickpuri
- [ ] Task 9: Initialize Flask project — `flask run starts without errors`
- [ ] Task 10: SQLite schema and db.py — `test_db.py passes`
- [ ] Task 11: POST /api/events endpoint — `curl returns 201`
- [ ] Task 12: GET /api/events endpoint — `curl returns JSON array`
- [ ] Task 13: GET /api/latest endpoint — `Returns most recent event`
- [ ] Task 14: Web dashboard (HTML + Chart.js) — `Browser shows timeline chart`
- [ ] Task 15: Report generation structure — `report.py imports without errors`
- [ ] Task 16: Report summary stats — `test_report.py passes`
- [ ] Task 17: Timeline chart (matplotlib) — `PNG chart image created`
- [ ] Task 18: Top 10 worst incidents table — `Function returns sorted list`
- [ ] Task 19: PDF assembly — `generate_report() returns valid PDF bytes`
- [ ] Task 20: GET /api/report endpoint — `curl downloads PDF file`
- [ ] Task 21: Dashboard "Generate Report" button — `Clicking button downloads PDF`

## 📚 Documentation
**Assignee:** @paulrydrickpuri
- [ ] Task 24: README.md with setup instructions — `User can follow README end-to-end`

---

## How to Start

**Step 1 — Set up Arduino IDE:**
1. Install Arduino IDE
2. Add ESP32 board support: File → Preferences → Additional Board Manager URLs → `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install board: Tools → Board → Board Manager → search "esp32" → Install
4. Install libraries: Sketch → Include Library → Manage Libraries → Install `Adafruit SSD1306` and `Adafruit GFX`

**Step 2 — Wire the hardware:**
Follow the pin mapping in `docs/plans/noise-logger.md` (Task 1 section).

**Step 3 — Start Task 1:**
```bash
cd firmware/noise-logger
# Open noise-logger.ino in Arduino IDE
# Select board: ESP32 Dev Module
# Compile (should succeed with 0 errors)
```

**Step 4 — Work through tasks sequentially:**
Each task builds on the previous. Test after each task before moving to the next.

**Step 5 — When OLED arrives:**
Complete Tasks 4-5 and Task 25 (OLED features).

**Step 6 — After all tasks:**
```bash
/simplify     # Reduce duplication
/review       # Self code-review
```

---

## Progress Tracking

Update this checklist as you complete tasks:
- Change `[ ]` to `[x]` when done
- Update status at top: 🔴 Not started → 🟡 In progress → 🟢 Done
