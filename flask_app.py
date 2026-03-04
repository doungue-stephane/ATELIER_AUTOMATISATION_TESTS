from flask import Flask, render_template, jsonify
from datetime import datetime, timezone
import sqlite3

# --- Config API ---
API_NAME = "Frankfurter"
BASE_URL = "https://api.frankfurter.app"
DB_PATH = "runs.db"

app = Flask(__name__)

# -------------------------
# SQLite helpers
# -------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            api TEXT NOT NULL,
            passed INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            error_rate REAL NOT NULL,
            latency_avg_ms REAL NOT NULL,
            latency_p95_ms REAL NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            latency_ms REAL,
            details TEXT,
            FOREIGN KEY(run_id) REFERENCES runs(id)
        )
        """)

def save_run(run: dict) -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        s = run["summary"]
        cur.execute(
            "INSERT INTO runs(ts, api, passed, failed, error_rate, latency_avg_ms, latency_p95_ms) VALUES(?,?,?,?,?,?,?)",
            (run["timestamp"], run["api"], s["passed"], s["failed"], s["error_rate"], s["latency_ms_avg"], s["latency_ms_p95"])
        )
        run_id = cur.lastrowid
        for t in run["tests"]:
            cur.execute(
                "INSERT INTO test_results(run_id, name, status, latency_ms, details) VALUES(?,?,?,?,?)",
                (run_id, t["name"], t["status"], t.get("latency_ms"), t.get("details", ""))
            )
        return run_id

def get_last_run():
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1")
        run = cur.fetchone()
        if not run:
            return None, []
        cur.execute("SELECT * FROM test_results WHERE run_id=? ORDER BY id ASC", (run["id"],))
        tests = cur.fetchall()
        return run, tests

def list_runs(limit=20):
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()

# -------------------------
# Import runner (tests)
# -------------------------
# On import ici pour que Flask démarre même si tu es encore en train de créer les fichiers.
def safe_import_runner():
    try:
        from tester.runner import run_suite
        return run_suite
    except Exception as e:
        return e

# -------------------------
# Routes
# -------------------------
@app.get("/")
def consignes():
    return render_template("consignes.html")

@app.get("/dashboard")
def dashboard():
    last, tests = get_last_run()
    runs = list_runs(20)
    return render_template("dashboard.html", last_run=last, last_tests=tests, runs=runs, api_name=API_NAME)

@app.get("/run")
def run_now():
    run_suite_or_error = safe_import_runner()
    if not callable(run_suite_or_error):
        return jsonify({"error": "runner import failed", "details": str(run_suite_or_error)}), 500

    run = run_suite_or_error(API_NAME, BASE_URL)
    save_run(run)
    return jsonify(run), 200

@app.get("/api/last")
def api_last():
    last, tests = get_last_run()
    if not last:
        return jsonify({"message": "no runs yet"}), 404
    return jsonify({
        "api": last["api"],
        "timestamp": last["ts"],
        "summary": {
            "passed": last["passed"],
            "failed": last["failed"],
            "error_rate": last["error_rate"],
            "latency_ms_avg": last["latency_avg_ms"],
            "latency_ms_p95": last["latency_p95_ms"],
        },
        "tests": [
            {"name": t["name"], "status": t["status"], "latency_ms": t["latency_ms"], "details": t["details"]}
            for t in tests
        ]
    })

@app.get("/health")
def health():
    last, _ = get_last_run()
    if not last:
        return jsonify({"status": "DEGRADED", "reason": "no runs yet"}), 200
    status = "OK" if int(last["failed"]) == 0 else "DEGRADED"
    return jsonify({
        "status": status,
        "last_run_ts": last["ts"],
        "failed": last["failed"],
        "error_rate": last["error_rate"]
    }), 200

if __name__ == "__main__":
    # utile en local uniquement
    app.run(host="0.0.0.0", port=5000, debug=True)