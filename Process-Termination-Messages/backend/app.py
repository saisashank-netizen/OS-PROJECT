# ============================================================
#  PROCESS TERMINATION MESSAGES
#  Flask Backend
#  Operating Systems and Systems Programming (25CS2104E)
#
#  Team:
#    K.V. KOUSHAL
#    Y. CHARAN SAI
#    B. SHASHANK
#
#  File   : app.py
#  Purpose: Read process_events.csv written by the C program,
#           synchronize the events into MySQL, and expose
#           GET /api/processes for the frontend dashboard.
#
#  Also serves the frontend (index.html) at http://localhost:5000/
# ============================================================

import os
import csv
from datetime import datetime

from flask import Flask, jsonify, send_from_directory
import mysql.connector

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

# Set your MySQL root password here (or use an environment variable).
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "YOUR_PASSWORD"   # <-- Replace with your MySQL password
DB_NAME     = "process_monitor"

# Path to the CSV event file produced by the C program.
# Adjust if you run app.py from a different working directory.
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_FILE = os.path.join(BASE_DIR, "process_events.csv")

# Frontend folder (served as static files)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# -------------------------------------------------------
# Flask app setup
# -------------------------------------------------------

app = Flask(__name__, static_folder=FRONTEND_DIR)

# -------------------------------------------------------
# Database helpers
# -------------------------------------------------------

def get_db_connection():
    """
    Open and return a new MySQL connection.
    Raises an exception if the connection fails.
    """
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn


def clear_processes(cursor):
    """Delete all rows from the processes table (called on RESET)."""
    cursor.execute("DELETE FROM processes")


def upsert_running(cursor, process_no, pid, duration, start_time):
    """
    Insert a new RUNNING row.
    If a row for process_no already exists (from a previous run that
    was not properly reset), replace it.
    """
    sql = """
        INSERT INTO processes
            (process_no, pid, status, duration, start_time, end_time, termination_message)
        VALUES
            (%s, %s, 'RUNNING', %s, %s, NULL, NULL)
        ON DUPLICATE KEY UPDATE
            pid                = VALUES(pid),
            status             = 'RUNNING',
            duration           = VALUES(duration),
            start_time         = VALUES(start_time),
            end_time           = NULL,
            termination_message = NULL
    """
    cursor.execute(sql, (process_no, pid, duration, start_time))


def update_completed(cursor, process_no, pid, end_time, message):
    """
    Mark a process as COMPLETED with an end_time and termination_message.
    """
    sql = """
        UPDATE processes
        SET
            status              = 'COMPLETED',
            end_time            = %s,
            termination_message = %s
        WHERE process_no = %s AND pid = %s
    """
    cursor.execute(sql, (end_time, message, process_no, pid))


# -------------------------------------------------------
# Event-file synchronisation
# -------------------------------------------------------

def sync_events_to_db():
    """
    Read process_events.csv and synchronise every event into MySQL.

    Event format:
      RESET
      CREATE,<process_no>,<pid>,<duration>,
      COMPLETE,<process_no>,<pid>,<duration>,<message>

    The RESET event clears the table so old records from the
    previous C run are removed before new ones are inserted.

    This function is called on every GET /api/processes request.
    Because there are at most ~200 events per run this is fast
    enough for a 1-second polling interval.
    """
    if not os.path.exists(EVENT_FILE):
        # Event file not yet created (C program not run yet)
        return

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        with open(EVENT_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            now    = datetime.now()  # used as fallback timestamp

            for row in reader:
                if not row:
                    continue

                event_type = row[0].strip()

                # ---- RESET ----
                if event_type == "RESET":
                    clear_processes(cursor)

                # ---- CREATE ----
                elif event_type == "CREATE" and len(row) >= 4:
                    process_no = int(row[1])
                    pid        = int(row[2])
                    duration   = int(row[3])
                    upsert_running(cursor, process_no, pid, duration, now)

                # ---- COMPLETE ----
                elif event_type == "COMPLETE" and len(row) >= 5:
                    process_no = int(row[1])
                    pid        = int(row[2])
                    # row[3] is duration (already stored on CREATE)
                    message    = row[4].strip()
                    update_completed(cursor, process_no, pid, now, message)

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"[sync_events_to_db] Error: {e}")

    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------
# API endpoint
# -------------------------------------------------------

@app.route("/api/processes", methods=["GET"])
def api_processes():
    """
    GET /api/processes

    1. Read and sync process_events.csv -> MySQL.
    2. Query all process rows.
    3. Return them as JSON.

    The frontend calls this endpoint every ~1 second to keep
    the dashboard live.
    """
    try:
        sync_events_to_db()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                process_no,
                pid,
                status,
                duration,
                start_time,
                end_time,
                termination_message
            FROM processes
            ORDER BY process_no ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Convert datetime objects to ISO strings so JSON serialisation works
    result = []
    for row in rows:
        result.append({
            "process_no"          : row["process_no"],
            "pid"                 : row["pid"],
            "status"              : row["status"],
            "duration"            : row["duration"],
            "start_time"          : row["start_time"].isoformat() if row["start_time"] else None,
            "end_time"            : row["end_time"].isoformat()   if row["end_time"]   else None,
            "termination_message" : row["termination_message"]
        })

    return jsonify(result)


# -------------------------------------------------------
# Frontend serving
# -------------------------------------------------------

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """Serve CSS, JS, and other static frontend files."""
    return send_from_directory(FRONTEND_DIR, filename)


# -------------------------------------------------------
# Entry point
# -------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  Process Termination Messages - Flask Backend")
    print("=" * 50)
    print(f"  Event file : {EVENT_FILE}")
    print(f"  Database   : {DB_NAME}@{DB_HOST}")
    print(f"  Dashboard  : http://localhost:5000/")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
