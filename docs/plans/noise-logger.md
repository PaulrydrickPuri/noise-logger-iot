## Plan: Noise Complaint Logger
**Goal:** Build an ESP32-based noise monitoring device that logs noise events and generates PDF reports for Malaysian JMB/MC complaints
**Tech stack:** Arduino-ESP32 v3.x (C++) + Python Flask + SQLite + Chart.js + matplotlib + fpdf2
**Related skills needed:** tdd (for server-side tests)
**Estimated tasks:** 25

### Assumptions
- User has Arduino IDE or PlatformIO installed
- User has Python 3.9+ installed
- User has a smartphone with an SPL meter app for calibration
- User's laptop will run the Flask server (local network only for v1)
- OLED arrives within 1 week (optional enhancement)

### Simpler Alternative Considered
We considered using a Raspberry Pi Zero 2W (full Linux stack), but it's unavailable in Malaysia and costs RM 190. The ESP32 + Flask architecture is 3x cheaper (RM 63), uses proven I2S mic libraries, and separates concerns cleanly (ESP32 = data collection, Flask = storage + reporting). This IS the simplest approach for the hardware constraints.

---

## File Map

```
CREATE  firmware/noise-logger/noise-logger.ino
CREATE  firmware/noise-logger/config.h
CREATE  server/app.py
CREATE  server/db.py
CREATE  server/report.py
CREATE  server/requirements.txt
CREATE  server/templates/dashboard.html
CREATE  server/tests/test_db.py
CREATE  server/tests/test_report.py
CREATE  config.yaml
CREATE  README.md
```

---

## Task Breakdown

### Task 1: Initialize Arduino project
**Files:** `firmware/noise-logger/noise-logger.ino`, `firmware/noise-logger/config.h`
**Success criteria:** Arduino IDE opens project without errors
**Steps:**
1. Create `firmware/noise-logger/` directory
2. Create `noise-logger.ino` with empty `setup()` and `loop()` functions
3. Create `config.h` with pin definitions:
   ```cpp
   #define I2S_BCLK_PIN 26
   #define I2S_LRCLK_PIN 25
   #define I2S_DIN_PIN 33
   #define I2C_SDA_PIN 21
   #define I2C_SCL_PIN 22
   ```
4. Verify: Arduino IDE → Open → select ESP32 Dev Module → Compile (0 errors)
5. `git commit -m "feat: init Arduino project structure"`

---

### Task 2: I2S audio sampling
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** Serial monitor prints raw audio samples (16-bit integers)
**Steps:**
1. Add I2S initialization in `setup()`:
   ```cpp
   #include <driver/i2s.h>
   
   i2s_config_t i2s_config = {
     .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
     .sample_rate = 16000,
     .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
     .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
     .communication_format = I2S_COMM_FORMAT_STAND_I2S,
     .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
     .dma_buf_count = 8,
     .dma_buf_len = 64,
     .use_apll = false
   };
   i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
   i2s_pin_config_t pin_config = {
     .bck_io_num = I2S_BCLK_PIN,
     .ws_io_num = I2S_LRCLK_PIN,
     .data_out_num = I2S_PIN_NO_CHANGE,
     .data_in_num = I2S_DIN_PIN
   };
   i2s_set_pin(I2S_NUM_0, &pin_config);
   ```
2. In `loop()`, read 512 samples and print first 10 to Serial:
   ```cpp
   int16_t buffer[512];
   size_t bytes_read;
   i2s_read(I2S_NUM_0, buffer, sizeof(buffer), &bytes_read, portMAX_DELAY);
   for (int i = 0; i < 10; i++) {
     Serial.println(buffer[i]);
   }
   delay(1000);
   ```
3. Flash ESP32, open Serial Monitor (115200 baud)
4. Verify: Prints integers (clap hands → values spike from ~0 to ±10000+)
5. `git commit -m "feat: I2S audio sampling from INMP441"`

---

### Task 3: RMS to dB SPL calculation
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** Serial monitor prints dB SPL value (ambient ~30-40 dB)
**Steps:**
1. Add function to calculate RMS and dB:
   ```cpp
   float calculateDB(int16_t* buffer, size_t num_samples) {
     float sum = 0;
     for (size_t i = 0; i < num_samples; i++) {
       sum += buffer[i] * buffer[i];
     }
     float rms = sqrt(sum / num_samples);
     if (rms < 1) rms = 1;  // Avoid log(0)
     return 20.0 * log10(rms * 1.0);  // calibration_factor = 1.0 for now
   }
   ```
2. In `loop()`, replace sample printing with dB calculation:
   ```cpp
   float db = calculateDB(buffer, 512);
   Serial.print("dB: ");
   Serial.println(db);
   ```
3. Flash and verify: Ambient room shows 30-45 dB, clap shows 60-70 dB
4. `git commit -m "feat: RMS to dB SPL calculation"`

---

### Task 4: OLED display initialization
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** OLED shows "Noise Logger" boot message
**Steps:**
1. Install Arduino libraries: `Adafruit_SSD1306` and `Adafruit_GFX`
2. Add OLED initialization in `setup()`:
   ```cpp
   #include <Adafruit_SSD1306.h>
   
   Adafruit_SSD1306 display(128, 64, &Wire, -1);
   
   if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
     Serial.println("SSD1306 allocation failed");
     for(;;);
   }
   display.clearDisplay();
   display.setTextSize(1);
   display.setTextColor(SSD1306_WHITE);
   display.setCursor(0, 0);
   display.println("Noise Logger");
   display.println("Booting...");
   display.display();
   ```
3. Flash and verify: OLED shows "Noise Logger" and "Booting..."
4. `git commit -m "feat: OLED display initialization"`

---

### Task 5: OLED real-time dB display
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** OLED updates dB reading every 500ms
**Steps:**
1. Add function to update OLED:
   ```cpp
   void updateOLED(float db) {
     display.clearDisplay();
     display.setTextSize(3);
     display.setCursor(0, 10);
     display.print(db, 1);
     display.setTextSize(1);
     display.setCursor(0, 50);
     display.print("dB SPL");
     display.display();
   }
   ```
2. In `loop()`, call `updateOLED(db)` after dB calculation
3. Flash and verify: OLED shows live dB value, updates smoothly
4. `git commit -m "feat: real-time dB display on OLED"`

---

### Task 6: WiFi connection
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** Serial monitor prints "WiFi connected" and IP address
**Steps:**
1. Add WiFi connection in `setup()`:
   ```cpp
   #include <WiFi.h>
   
   const char* ssid = "YOUR_SSID";  // TODO: move to config
   const char* password = "YOUR_PASSWORD";
   
   WiFi.begin(ssid, password);
   Serial.print("Connecting to WiFi");
   while (WiFi.status() != WL_CONNECTED) {
     delay(500);
     Serial.print(".");
   }
   Serial.println("\nWiFi connected");
   Serial.println(WiFi.localIP());
   ```
2. Add WiFi status indicator to OLED:
   ```cpp
   void updateWiFiStatus() {
     display.setCursor(100, 0);
     if (WiFi.status() == WL_CONNECTED) {
       display.print("WiFi:OK");
     } else {
       display.print("WiFi:--");
     }
   }
   ```
3. Flash and verify: Serial shows IP, OLED shows "WiFi:OK"
4. `git commit -m "feat: WiFi connection and status display"`

---

### Task 7: Noise event detection
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** Event counter increments after sustained noise > threshold
**Steps:**
1. Add event detection logic:
   ```cpp
   #define DB_THRESHOLD 55.0
   #define EVENT_DURATION_MS 2000
   
   unsigned long noise_start_time = 0;
   int event_count = 0;
   bool event_active = false;
   
   void detectNoiseEvent(float db) {
     if (db > DB_THRESHOLD) {
       if (!event_active) {
         noise_start_time = millis();
         event_active = true;
       } else if (millis() - noise_start_time > EVENT_DURATION_MS) {
         event_count++;
         Serial.print("Event #");
         Serial.println(event_count);
         event_active = false;  // Reset to avoid duplicate counts
         delay(5000);  // Debounce: ignore for 5 seconds
       }
     } else {
       event_active = false;
       noise_start_time = 0;
     }
   }
   ```
2. Add event counter to OLED display:
   ```cpp
   display.setCursor(0, 40);
   display.print("Events: ");
   display.print(event_count);
   ```
3. In `loop()`, call `detectNoiseEvent(db)` after dB calculation
4. Flash, play loud music for 3+ seconds, verify event counter increments
5. `git commit -m "feat: noise event detection with threshold and debounce"`

---

### Task 8: HTTP POST events to server
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** Server receives POST request with event JSON
**Steps:**
1. Add HTTP client and POST function:
   ```cpp
   #include <HTTPClient.h>
   
   const char* server_url = "http://192.168.1.100:5000/api/events";  // TODO: config
   
   void postEvent(float peak_db, int duration_sec) {
     if (WiFi.status() != WL_CONNECTED) return;
     
     HTTPClient http;
     http.begin(server_url);
     http.addHeader("Content-Type", "application/json");
     
     String json = "{\"device_id\":\"ESP32-001\",\"peak_db\":" + String(peak_db, 1) + ",\"duration\":" + String(duration_sec) + "}";
     int httpCode = http.POST(json);
     
     Serial.print("POST response: ");
     Serial.println(httpCode);
     http.end();
   }
   ```
2. In `detectNoiseEvent()`, call `postEvent(peak_db, duration_sec)` when event is logged
3. Track peak dB and duration during event:
   ```cpp
   float peak_db = 0;
   // Update peak during event:
   if (db > peak_db) peak_db = db;
   // Calculate duration:
   int duration_sec = (millis() - noise_start_time) / 1000;
   ```
4. Flash and verify: Serial shows "POST response: 200" (server must be running)
5. `git commit -m "feat: HTTP POST events to Flask server"`

---

### Task 9: Initialize Flask project
**Files:** `server/app.py`, `server/requirements.txt`
**Success criteria:** `flask run` starts server without errors
**Steps:**
1. Create `server/` directory
2. Create `requirements.txt`:
   ```
   flask==3.0.0
   matplotlib==3.8.0
   fpdf2==2.7.6
   ```
3. Create `app.py` skeleton:
   ```python
   from flask import Flask, jsonify, request
   
   app = Flask(__name__)
   
   @app.route('/')
   def index():
       return 'Noise Logger Server'
   
   if __name__ == '__main__':
       app.run(debug=True, host='0.0.0.0', port=5000)
   ```
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python app.py`
6. Verify: Browser shows "Noise Logger Server" at `http://localhost:5000`
7. `git commit -m "feat: init Flask project"`

---

### Task 10: SQLite schema and db.py
**Files:** `server/db.py`, `server/tests/test_db.py`
**Success criteria:** `test_db.py` passes — events can be inserted and queried
**Steps:**
1. Create `db.py`:
   ```python
   import sqlite3
   from datetime import datetime
   
   def init_db():
       conn = sqlite3.connect('noise_events.db')
       c = conn.cursor()
       c.execute('''
           CREATE TABLE IF NOT EXISTS events (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               device_id TEXT NOT NULL,
               timestamp TEXT NOT NULL,
               peak_db REAL NOT NULL,
               duration_sec INTEGER NOT NULL,
               created_at TEXT DEFAULT CURRENT_TIMESTAMP
           )
       ''')
       conn.commit()
       conn.close()
   
   def insert_event(device_id: str, peak_db: float, duration_sec: int):
       conn = sqlite3.connect('noise_events.db')
       c = conn.cursor()
       c.execute('''
           INSERT INTO events (device_id, timestamp, peak_db, duration_sec)
           VALUES (?, ?, ?, ?)
       ''', (device_id, datetime.now().isoformat(), peak_db, duration_sec))
       conn.commit()
       conn.close()
   
   def get_events(limit: int = 100):
       conn = sqlite3.connect('noise_events.db')
       c = conn.cursor()
       c.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT ?', (limit,))
       rows = c.fetchall()
       conn.close()
       return rows
   ```
2. Create `tests/test_db.py`:
   ```python
   import sys
   sys.path.insert(0, '..')
   from db import init_db, insert_event, get_events
   
   def test_insert_and_get():
       init_db()
       insert_event('TEST-001', 82.5, 5)
       events = get_events()
       assert len(events) == 1
       assert events[0][1] == 'TEST-001'
       assert events[0][3] == 82.5
   
   if __name__ == '__main__':
       test_insert_and_get()
       print("✓ test_insert_and_get passed")
   ```
3. Run test: `cd server/tests && python test_db.py`
4. Verify: Test passes
5. `git commit -m "feat: SQLite schema and db.py with tests"`

---

### Task 11: POST /api/events endpoint
**Files:** `server/app.py`
**Success criteria:** `curl -X POST` returns 201 and event is stored
**Steps:**
1. Add endpoint to `app.py`:
   ```python
   from db import init_db, insert_event
   
   init_db()
   
   @app.route('/api/events', methods=['POST'])
   def create_event():
       data = request.get_json()
       if not data or 'peak_db' not in data:
           return jsonify({'error': 'missing peak_db'}), 400
       
       device_id = data.get('device_id', 'unknown')
       peak_db = float(data['peak_db'])
       duration_sec = int(data.get('duration', 0))
       
       insert_event(device_id, peak_db, duration_sec)
       return jsonify({'status': 'ok'}), 201
   ```
2. Test with curl:
   ```bash
   curl -X POST http://localhost:5000/api/events \
     -H "Content-Type: application/json" \
     -d '{"device_id":"ESP32-001","peak_db":82.5,"duration":5}'
   ```
3. Verify: Returns `{"status":"ok"}` with status 201
4. Check database: `sqlite3 server/noise_events.db "SELECT * FROM events"`
5. Verify: Event row exists
6. `git commit -m "feat: POST /api/events endpoint"`

---

### Task 12: GET /api/events endpoint
**Files:** `server/app.py`
**Success criteria:** `curl` returns JSON array of events
**Steps:**
1. Add endpoint to `app.py`:
   ```python
   from db import get_events
   
   @app.route('/api/events', methods=['GET'])
   def list_events():
       limit = request.args.get('limit', 100, type=int)
       events = get_events(limit)
       return jsonify([
           {
               'id': e[0],
               'device_id': e[1],
               'timestamp': e[2],
               'peak_db': e[3],
               'duration_sec': e[4]
           }
           for e in events
       ])
   ```
2. Test with curl:
   ```bash
   curl http://localhost:5000/api/events
   ```
3. Verify: Returns JSON array with the event from Task 11
4. `git commit -m "feat: GET /api/events endpoint"`

---

### Task 13: GET /api/latest endpoint
**Files:** `server/app.py`
**Success criteria:** Returns most recent event or null
**Steps:**
1. Add endpoint:
   ```python
   @app.route('/api/latest', methods=['GET'])
   def latest_event():
       events = get_events(limit=1)
       if not events:
           return jsonify(None)
       e = events[0]
       return jsonify({
           'id': e[0],
           'device_id': e[1],
           'timestamp': e[2],
           'peak_db': e[3],
           'duration_sec': e[4]
       })
   ```
2. Test: `curl http://localhost:5000/api/latest`
3. Verify: Returns the most recent event
4. `git commit -m "feat: GET /api/latest endpoint"`

---

### Task 14: Web dashboard (HTML + Chart.js)
**Files:** `server/templates/dashboard.html`, `server/app.py`
**Success criteria:** Browser shows dashboard with event timeline chart
**Steps:**
1. Update `app.py` to serve template:
   ```python
   @app.route('/')
   def index():
       return render_template('dashboard.html')
   ```
2. Create `templates/dashboard.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Noise Logger Dashboard</title>
       <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   </head>
   <body>
       <h1>Noise Logger Dashboard</h1>
       <canvas id="timeline" width="800" height="400"></canvas>
       <script>
           fetch('/api/events')
               .then(r => r.json())
               .then(events => {
                   const ctx = document.getElementById('timeline').getContext('2d');
                   new Chart(ctx, {
                       type: 'bar',
                       data: {
                           labels: events.map(e => e.timestamp.slice(11, 16)),
                           datasets: [{
                               label: 'Peak dB',
                               data: events.map(e => e.peak_db),
                               backgroundColor: 'rgba(255, 99, 132, 0.5)'
                           }]
                       }
                   });
               });
       </script>
   </body>
   </html>
   ```
3. Restart Flask, open `http://localhost:5000`
4. Verify: Dashboard loads with bar chart of events
5. `git commit -m "feat: web dashboard with Chart.js timeline"`

---

### Task 15: Report generation structure
**Files:** `server/report.py`
**Success criteria:** `report.py` imports without errors
**Steps:**
1. Create `report.py` skeleton:
   ```python
   from fpdf import FPDF
   import matplotlib.pyplot as plt
   from db import get_events
   
   def generate_report(date_from: str, date_to: str) -> bytes:
       """Generate PDF report for noise events between date_from and date_to."""
       events = get_events(limit=1000)
       # TODO: Filter by date range
       # TODO: Build PDF
       pass
   ```
2. Import and verify no syntax errors:
   ```bash
   python -c "from report import generate_report"
   ```
3. `git commit -m "feat: report.py skeleton"`

---

### Task 16: Report summary stats
**Files:** `server/report.py`, `server/tests/test_report.py`
**Success criteria:** `test_report.py` passes — summary stats are correct
**Steps:**
1. Add summary calculation to `report.py`:
   ```python
   def calculate_summary(events):
       if not events:
           return {'total': 0, 'avg_db': 0, 'peak_db': 0, 'total_duration': 0}
       
       total = len(events)
       avg_db = sum(e[3] for e in events) / total
       peak_db = max(e[3] for e in events)
       total_duration = sum(e[4] for e in events)
       
       return {
           'total': total,
           'avg_db': round(avg_db, 1),
           'peak_db': peak_db,
           'total_duration': total_duration
       }
   ```
2. Create `tests/test_report.py`:
   ```python
   import sys
   sys.path.insert(0, '..')
   from report import calculate_summary
   
   def test_summary_stats():
       events = [
           (1, 'ESP32-001', '2026-06-10T10:00:00', 80.0, 5),
           (2, 'ESP32-001', '2026-06-10T11:00:00', 90.0, 10),
           (3, 'ESP32-001', '2026-06-10T12:00:00', 70.0, 3),
       ]
       summary = calculate_summary(events)
       assert summary['total'] == 3
       assert summary['avg_db'] == 80.0
       assert summary['peak_db'] == 90.0
       assert summary['total_duration'] == 18
   
   if __name__ == '__main__':
       test_summary_stats()
       print("✓ test_summary_stats passed")
   ```
3. Run test: `cd server/tests && python test_report.py`
4. Verify: Test passes
5. `git commit -m "feat: report summary stats calculation"`

---

### Task 17: Timeline chart (matplotlib)
**Files:** `server/report.py`
**Success criteria:** `generate_report()` creates PNG chart image
**Steps:**
1. Add chart generation to `report.py`:
   ```python
   def create_timeline_chart(events):
       timestamps = [e[2] for e in events]
       peak_dbs = [e[3] for e in events]
       
       fig, ax = plt.subplots(figsize=(10, 4))
       ax.bar(timestamps, peak_dbs, color='red', alpha=0.7)
       ax.set_xlabel('Time')
       ax.set_ylabel('Peak dB')
       ax.set_title('Noise Event Timeline')
       plt.xticks(rotation=45, ha='right')
       plt.tight_layout()
       
       chart_path = '/tmp/timeline_chart.png'
       plt.savefig(chart_path, dpi=150)
       plt.close()
       return chart_path
   ```
2. Test manually:
   ```python
   from report import create_timeline_chart
   events = [(1, 'ESP32-001', '2026-06-10T10:00:00', 80.0, 5)]
   chart_path = create_timeline_chart(events)
   print(f"Chart saved to: {chart_path}")
   ```
3. Verify: PNG file exists at `/tmp/timeline_chart.png`
4. `git commit -m "feat: timeline chart generation with matplotlib"`

---

### Task 18: Top 10 worst incidents table
**Files:** `server/report.py`
**Success criteria:** Function returns sorted list of top 10 events
**Steps:**
1. Add function to `report.py`:
   ```python
   def get_top_incidents(events, n=10):
       sorted_events = sorted(events, key=lambda e: e[3], reverse=True)
       return sorted_events[:n]
   ```
2. Test manually:
   ```python
   from report import get_top_incidents
   events = [
       (1, 'ESP32-001', '2026-06-10T10:00:00', 80.0, 5),
       (2, 'ESP32-001', '2026-06-10T11:00:00', 95.0, 10),
       (3, 'ESP32-001', '2026-06-10T12:00:00', 70.0, 3),
   ]
   top = get_top_incidents(events)
   assert top[0][3] == 95.0  # Highest dB first
   ```
3. Verify: Test passes
4. `git commit -m "feat: top 10 worst incidents function"`

---

### Task 19: PDF assembly
**Files:** `server/report.py`
**Success criteria:** `generate_report()` returns valid PDF bytes
**Steps:**
1. Complete `generate_report()` in `report.py`:
   ```python
   def generate_report(date_from: str = None, date_to: str = None) -> bytes:
       events = get_events(limit=1000)
       summary = calculate_summary(events)
       chart_path = create_timeline_chart(events)
       top_incidents = get_top_incidents(events)
       
       pdf = FPDF()
       pdf.add_page()
       
       # Cover page
       pdf.set_font('Arial', 'B', 24)
       pdf.cell(0, 20, 'Noise Disturbance Report', ln=True, align='C')
       pdf.set_font('Arial', '', 12)
       pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
       
       # Summary table
       pdf.ln(10)
       pdf.set_font('Arial', 'B', 16)
       pdf.cell(0, 10, 'Summary', ln=True)
       pdf.set_font('Arial', '', 12)
       pdf.cell(0, 10, f'Total Events: {summary["total"]}', ln=True)
       pdf.cell(0, 10, f'Average dB: {summary["avg_db"]}', ln=True)
       pdf.cell(0, 10, f'Peak dB: {summary["peak_db"]}', ln=True)
       pdf.cell(0, 10, f'Total Duration: {summary["total_duration"]} seconds', ln=True)
       
       # Timeline chart
       pdf.ln(10)
       pdf.set_font('Arial', 'B', 16)
       pdf.cell(0, 10, 'Event Timeline', ln=True)
       pdf.image(chart_path, x=10, w=190)
       
       # Top 10 worst incidents
       pdf.add_page()
       pdf.set_font('Arial', 'B', 16)
       pdf.cell(0, 10, 'Top 10 Worst Incidents', ln=True)
       pdf.set_font('Arial', '', 10)
       for i, event in enumerate(top_incidents, 1):
           pdf.cell(0, 8, f'{i}. {event[2]} - {event[3]} dB ({event[4]}s)', ln=True)
       
       # Legal reference
       pdf.ln(10)
       pdf.set_font('Arial', 'B', 14)
       pdf.cell(0, 10, 'Legal Reference', ln=True)
       pdf.set_font('Arial', '', 10)
       pdf.multi_cell(0, 5, 
           'This report documents noise disturbances under the Strata Management Act 2013 (Act 757), '
           'Third Schedule, By-law 4 (Noise): "An owner or occupier shall not create any noise likely '
           'to disturb the peaceful enjoyment of other owners or occupiers."\n\n'
           'WHO residential noise guideline: 55 dB maximum during daytime, 45 dB at night.'
       )
       
       return pdf.output()
   ```
2. Test manually:
   ```python
   from report import generate_report
   pdf_bytes = generate_report()
   with open('/tmp/test_report.pdf', 'wb') as f:
       f.write(pdf_bytes)
   print(f"PDF saved to /tmp/test_report.pdf ({len(pdf_bytes)} bytes)")
   ```
3. Verify: PDF opens and contains all sections
4. `git commit -m "feat: PDF report assembly with fpdf2"`

---

### Task 20: GET /api/report endpoint
**Files:** `server/app.py`
**Success criteria:** `curl` downloads PDF file
**Steps:**
1. Add endpoint to `app.py`:
   ```python
   from report import generate_report
   from flask import send_file
   import io
   
   @app.route('/api/report', methods=['GET'])
   def download_report():
       date_from = request.args.get('from')
       date_to = request.args.get('to')
       pdf_bytes = generate_report(date_from, date_to)
       return send_file(
           io.BytesIO(pdf_bytes),
           mimetype='application/pdf',
           as_attachment=True,
           download_name='noise_report.pdf'
       )
   ```
2. Test with curl:
   ```bash
   curl http://localhost:5000/api/report -o report.pdf
   ```
3. Verify: `report.pdf` downloads and opens correctly
4. `git commit -m "feat: GET /api/report endpoint for PDF download"`

---

### Task 21: Dashboard "Generate Report" button
**Files:** `server/templates/dashboard.html`
**Success criteria:** Clicking button downloads PDF
**Steps:**
1. Add button to `dashboard.html`:
   ```html
   <button onclick="generateReport()">Generate PDF Report</button>
   <script>
       function generateReport() {
           window.location.href = '/api/report';
       }
   </script>
   ```
2. Restart Flask, open dashboard
3. Verify: Clicking button downloads `noise_report.pdf`
4. `git commit -m "feat: Generate Report button on dashboard"`

---

### Task 22: Calibration factor in firmware
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** dB readings match phone SPL meter app within ±3 dB
**Steps:**
1. Add calibration constant to `config.h`:
   ```cpp
   #define CALIBRATION_FACTOR 1.0
   ```
2. Update `calculateDB()` to use it:
   ```cpp
   return 20.0 * log10(rms * CALIBRATION_FACTOR);
   ```
3. Place phone with SPL meter app next to INMP441
4. Play steady white noise (YouTube "70 dB white noise")
5. Compare ESP32 Serial output with phone reading
6. Adjust `CALIBRATION_FACTOR` until readings match (e.g., 1.2, 0.8)
7. Flash and verify: Readings match within ±3 dB
8. `git commit -m "feat: calibration factor for accurate dB readings"`

---

### Task 23: Watchdog timer for ESP32
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** ESP32 auto-reboots if `loop()` hangs
**Steps:**
1. Add watchdog initialization in `setup()`:
   ```cpp
   #include <esp_task_wdt.h>
   
   esp_task_wdt_init(10, true);  // 10 second timeout
   esp_task_wdt_add(NULL);
   ```
2. Add watchdog reset in `loop()`:
   ```cpp
   esp_task_wdt_reset();
   ```
3. Flash and verify: ESP32 runs continuously without hanging
4. `git commit -m "feat: watchdog timer for reliability"`

---

### Task 24: README.md with setup instructions
**Files:** `README.md`
**Success criteria:** User can follow README to wire, flash, and run the system
**Steps:**
1. Create `README.md` with sections:
   - Overview (what this project does)
   - BOM list (hardware with Shopee links)
   - Wiring diagram (pin table)
   - Firmware setup (Arduino libraries, flash instructions)
   - Server setup (Python install, run command)
   - Calibration guide
   - Usage (how to generate reports)
2. Include the pin mapping table from the plan
3. Add example commands for flashing and running server
4. `git commit -m "docs: README with setup instructions"`

---

### Task 25: OLED sparkline mini-graph (optional enhancement)
**Files:** `firmware/noise-logger/noise-logger.ino`
**Success criteria:** OLED shows last 30 seconds of dB as a sparkline
**Steps:**
1. Add circular buffer for dB history:
   ```cpp
   float db_history[30];
   int history_index = 0;
   
   void updateHistory(float db) {
       db_history[history_index] = db;
       history_index = (history_index + 1) % 30;
   }
   ```
2. Add sparkline drawing function:
   ```cpp
   void drawSparkline() {
       int y_base = 60;
       int height = 20;
       for (int i = 0; i < 30; i++) {
           int index = (history_index + i) % 30;
           int bar_height = map(db_history[index], 30, 100, 0, height);
           display.drawLine(i * 4, y_base, i * 4, y_base - bar_height, SSD1306_WHITE);
       }
   }
   ```
3. Call `drawSparkline()` in `updateOLED()`
4. Flash and verify: OLED shows sparkline that updates in real-time
5. `git commit -m "feat: OLED sparkline mini-graph of dB history"`

---

## How to Pick Up This Plan

**Step 1 — Install tools:**
```bash
# Arduino IDE with ESP32 board support
# OR PlatformIO (recommended for CLI workflow)

# Python 3.9+
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
```

**Step 2 — Start with Task 1:**
```bash
git init
git add .
git commit -m "feat: init Arduino project structure"
```

Then work through Tasks 1-25 sequentially. Each task is independently testable.

**Step 3 — When OLED arrives:**
Skip to Task 4-5 and Task 25.

**Step 4 — After all tasks:**
```bash
/tdd          # If adding more tests
/simplify     # Reduce duplication
/review       # Self code-review
```
