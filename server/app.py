from flask import Flask, request, jsonify, render_template
from db import init_db, add_event, get_events, get_latest_event, get_event_stats

app = Flask(__name__)

# Initialize database
init_db()

@app.route("/")
def dashboard():
    """Serve the web dashboard."""
    return render_template("dashboard.html")

@app.route("/api/events", methods=["POST"])
def receive_event():
    """Receive a noise event from the ESP32 device."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ["device_id", "timestamp", "peak_db", "duration_sec"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    event_id = add_event(
        device_id=data["device_id"],
        timestamp=data["timestamp"],
        peak_db=data["peak_db"],
        duration_sec=data["duration_sec"]
    )

    return jsonify({
        "status": "success",
        "event_id": event_id
    }), 201

@app.route("/api/events", methods=["GET"])
def list_events():
    """List noise events with optional date filtering."""
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    events = get_events(from_date=from_date, to_date=to_date)

    return jsonify({
        "events": events,
        "count": len(events)
    })

@app.route("/api/latest", methods=["GET"])
def latest_event():
    """Get the most recent noise event."""
    event = get_latest_event()

    if event:
        return jsonify(event)
    else:
        return jsonify({"message": "No events recorded yet"}), 404

@app.route("/api/stats", methods=["GET"])
def event_stats():
    """Get statistics for noise events."""
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    stats = get_event_stats(from_date=from_date, to_date=to_date)

    if stats:
        return jsonify(stats)
    else:
        return jsonify({"message": "No events recorded yet"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
