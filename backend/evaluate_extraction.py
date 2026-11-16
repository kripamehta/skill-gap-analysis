"""Precision / recall / F1 of skill extraction against manual labels.

Usage (from the project root):
    python -m backend.evaluate_extraction data/evaluation/skill_ground_truth.csv

CSV columns: job_id,predicted_skill,actual_skill
  - one skill per row; leave actual_skill empty for a wrong prediction,
    leave predicted_skill empty for a skill the system missed.
A skill is correct only if it is predicted AND labelled for the SAME job.
"""
import csv
import sys

from backend.recommendation_engine import normalize_skill


def evaluate(path):
    jobs = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            predicted, actual = jobs.setdefault(row["job_id"], (set(), set()))
            if row.get("predicted_skill", "").strip():
                predicted.add(normalize_skill(row["predicted_skill"]))
            if row.get("actual_skill", "").strip():
                actual.add(normalize_skill(row["actual_skill"]))
    tp = sum(len(p & a) for p, a in jobs.values())
    fp = sum(len(p - a) for p, a in jobs.values())
    fn = sum(len(a - p) for p, a in jobs.values())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"jobs": len(jobs), "true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": round(precision * 100, 2), "recall": round(recall * 100, 2), "f1": round(f1 * 100, 2)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for key, value in evaluate(sys.argv[1]).items():
        print(f"{key:16}{value}")
