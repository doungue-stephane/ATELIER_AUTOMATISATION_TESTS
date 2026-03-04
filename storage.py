import sqlite3

DB_PATH = "runs.db"

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
