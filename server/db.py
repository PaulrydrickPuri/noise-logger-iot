import sqlite3
import os
from datetime import datetime

DB_PATH = "noise_events.db"

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            peak_db REAL NOT NULL,
            duration_sec INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized")

def add_event(device_id, timestamp, peak_db, duration_sec):
    """Add a new noise event to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (device_id, timestamp, peak_db, duration_sec)
        VALUES (?, ?, ?, ?)
    """, (device_id, timestamp, peak_db, duration_sec))

    conn.commit()
    event_id = cursor.lastrowid
    conn.close()

    return event_id

def get_events(from_date=None, to_date=None):
    """Get noise events, optionally filtered by date range."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if from_date:
        query += " AND timestamp >= ?"
        params.append(from_date)

    if to_date:
        query += " AND timestamp <= ?"
        params.append(to_date)

    query += " ORDER BY timestamp DESC"

    cursor.execute(query, params)
    events = cursor.fetchall()
    conn.close()

    return [dict(row) for row in events]

def get_latest_event():
    """Get the most recent noise event."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def get_event_stats(from_date=None, to_date=None):
    """Get statistics for noise events."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT
            COUNT(*) as total_events,
            AVG(peak_db) as avg_db,
            MAX(peak_db) as peak_db,
            SUM(duration_sec) as total_duration_sec
        FROM events
        WHERE 1=1
    """
    params = []

    if from_date:
        query += " AND timestamp >= ?"
        params.append(from_date)

    if to_date:
        query += " AND timestamp <= ?"
        params.append(to_date)

    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if row and row[0] > 0:
        return {
            "total_events": row[0],
            "avg_db": round(row[1], 1) if row[1] else 0,
            "peak_db": round(row[2], 1) if row[2] else 0,
            "total_duration_sec": row[3] if row[3] else 0
        }
    return None
