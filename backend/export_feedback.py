"""Export the user/expert feedback stored in the database to reports/feedback.csv.

Usage (from the project root):  python -m backend.export_feedback
"""
import csv
from pathlib import Path

from backend import database

REPORTS = Path(__file__).resolve().parent.parent / "reports"

with database.connect() as conn:
    rows = conn.execute(
        "SELECT f.id, f.created_at, a.occupation, a.budget_hours, f.relevance, f.clarity, f.role, f.comment "
        "FROM feedback f LEFT JOIN analyses a ON a.id = f.analysis_id ORDER BY f.id").fetchall()

REPORTS.mkdir(exist_ok=True)
with open(REPORTS / "feedback.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "created_at", "occupation", "budget_hours", "relevance", "clarity", "role", "comment"])
    writer.writerows([tuple(r) for r in rows])
print(f"Exported {len(rows)} responses to {REPORTS / 'feedback.csv'}")
print(database.feedback_summary())
