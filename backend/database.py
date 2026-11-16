"""SQLite storage for user data: analysis history and evaluation feedback.

Reference data (courses, skill demand, dependencies) stays in versioned CSV files.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("SKILLPATH_DB", Path(__file__).resolve().parent.parent / "data" / "skillpath.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    occupation TEXT NOT NULL,
    skills TEXT NOT NULL,
    budget_hours REAL NOT NULL,
    gap_count INTEGER NOT NULL,
    result TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER REFERENCES analyses(id),
    created_at TEXT NOT NULL,
    relevance INTEGER NOT NULL CHECK (relevance BETWEEN 1 AND 5),
    clarity INTEGER NOT NULL CHECK (clarity BETWEEN 1 AND 5),
    role TEXT,
    comment TEXT
);
"""


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_analysis(result):
    candidate = result["candidate"]
    stored = {k: v for k, v in result.items() if k != "course_recommendations"}
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO analyses (created_at, occupation, skills, budget_hours, gap_count, result)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (now(), candidate["target_occupation"], json.dumps(candidate["current_skills"]),
             candidate["time_budget_hours"], len(result["skill_gaps"]), json.dumps(stored)),
        )
        return cursor.lastrowid


def list_history(limit=10):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, occupation, skills, budget_hours, gap_count"
            " FROM analyses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "skills": json.loads(r["skills"])} for r in rows]


def get_analysis(analysis_id):
    with connect() as conn:
        row = conn.execute("SELECT result FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        return None
    result = json.loads(row["result"])
    result["analysis_id"] = analysis_id
    return result


def save_feedback(analysis_id, relevance, clarity, role, comment):
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO feedback (analysis_id, created_at, relevance, clarity, role, comment)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (analysis_id, now(), relevance, clarity, role, comment))
        return cursor.lastrowid


def feedback_summary():
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()["n"]
        stats = conn.execute(
            "SELECT COUNT(*) AS n, AVG(relevance) AS relevance, AVG(clarity) AS clarity FROM feedback").fetchone()
        by_role = conn.execute(
            "SELECT COALESCE(role, 'unspecified') AS role, COUNT(*) AS n, AVG(relevance) AS relevance,"
            " AVG(clarity) AS clarity FROM feedback GROUP BY role").fetchall()
    rnd = lambda x: round(x, 2) if x is not None else None
    return {
        "analyses_run": total,
        "responses": stats["n"],
        "avg_relevance": rnd(stats["relevance"]),
        "avg_explanation_clarity": rnd(stats["clarity"]),
        "by_role": [{"role": r["role"], "responses": r["n"], "avg_relevance": rnd(r["relevance"]),
                     "avg_explanation_clarity": rnd(r["clarity"])} for r in by_role],
    }
