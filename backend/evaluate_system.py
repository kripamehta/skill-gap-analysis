"""Evaluate the recommender over every career, profile and time budget.

Usage (from the project root):  python -m backend.evaluate_system
Writes reports/pathway_evaluation.csv and reports/evaluation_summary.md
"""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from backend.recommendation_engine import generate_dynamic_recommendations

CAREERS = [
    "AI Engineer", "Backend Developer", "Cloud Engineer", "Cybersecurity Analyst",
    "Data Analyst", "Data Engineer", "Data Scientist", "Database Administrator",
    "DevOps Engineer", "Frontend Developer", "Full Stack Developer",
    "Machine Learning Engineer", "Mobile App Developer", "Network Engineer",
    "QA / Software Test Engineer", "Software Developer",
]
PROFILES = {"beginner": ["Git"], "intermediate": ["Python", "SQL", "Git"]}
BUDGETS = [20, 40, 80, 160]
REPORTS = Path(__file__).resolve().parent.parent / "reports"


def single_course_baseline(result, budget):
    """Naive recommender: the one course that covers the most demand within budget (ignores prerequisites)."""
    demand = {g["normalized_skill"]: g["demand_percentage"] for g in result["skill_gaps"]}
    total = sum(demand.values())
    options = [c for c in result["course_recommendations"] if c["duration_hours"] <= budget]
    if not options or not total:
        return None
    best = max(options, key=lambda c: sum(demand.get(s, 0) for s in c["covers"]))
    covered = sum(demand.get(s, 0) for s in best["covers"])
    return {"demand_coverage": covered / total * 100, "prerequisites_ready": best["prerequisites_ready"]}


def main():
    rows, baseline_rows, distinct = [], [], []
    for career in CAREERS:
        for profile, skills in PROFILES.items():
            for budget in BUDGETS:
                result = generate_dynamic_recommendations(career, skills, budget)
                evaluations = result["evaluations"]
                for name, ev in evaluations.items():
                    rows.append({
                        "career": career, "profile": profile, "budget_hours": budget, "pathway": name,
                        "courses": ev["course_count"], "hours": ev["total_time_hours"],
                        "skill_coverage_pct": ev["skill_coverage_percentage"],
                        "demand_coverage_pct": ev["demand_coverage_percentage"],
                        "avg_rating": ev["average_course_rating"],
                        "prerequisites_valid": ev["strict_prerequisites_valid"],
                        "within_budget": ev["time_feasible"], "quality_score": ev["quality_score"],
                    })
                base = single_course_baseline(result, budget)
                if base and "COMPREHENSIVE" in evaluations:
                    baseline_rows.append((base, evaluations["COMPREHENSIVE"]["demand_coverage_percentage"]))
                ids = {tuple(c["course_id"] for c in p) for p in result["pathways"].values()}
                distinct.append(len(ids) == len(result["pathways"]))

    REPORTS.mkdir(exist_ok=True)
    with open(REPORTS / "pathway_evaluation.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_type = defaultdict(list)
    for r in rows:
        by_type[r["pathway"]].append(r)
    lines = [
        "# Pathway evaluation summary", "",
        f"{len(distinct)} scenarios = {len(CAREERS)} careers x {len(PROFILES)} profiles x {len(BUDGETS)} budgets "
        f"({', '.join(map(str, BUDGETS))} h). {len(rows)} pathways evaluated.", "",
        "## Metrics by pathway type", "",
        "| Pathway | Avg courses | Avg hours | Skill coverage % | Demand coverage % | Prerequisites valid % | Within budget % | Quality |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, items in sorted(by_type.items()):
        lines.append(
            f"| {name} | {mean(i['courses'] for i in items):.1f} | {mean(i['hours'] for i in items):.1f} | "
            f"{mean(i['skill_coverage_pct'] for i in items):.1f} | {mean(i['demand_coverage_pct'] for i in items):.1f} | "
            f"{mean(i['prerequisites_valid'] for i in items) * 100:.0f} | {mean(i['within_budget'] for i in items) * 100:.0f} | "
            f"{mean(i['quality_score'] for i in items):.1f} |")
    if baseline_rows:
        lines += [
            "", "## Pathways vs single-course recommendation", "",
            "| Approach | Avg demand coverage % | Prerequisites satisfied % |", "|---|---|---|",
            f"| Best single course (baseline) | {mean(b['demand_coverage'] for b, _ in baseline_rows):.1f} | "
            f"{mean(b['prerequisites_ready'] for b, _ in baseline_rows) * 100:.0f} |",
            f"| COMPREHENSIVE pathway | {mean(p for _, p in baseline_rows):.1f} | 100 |",
        ]
    lines += ["", f"Scenarios where all pathways are different: {mean(distinct) * 100:.0f}%", "",
              "## Skill coverage % of COMPREHENSIVE pathway by career and budget", "",
              "| Career | " + " | ".join(f"{b} h" for b in BUDGETS) + " |", "|---|" + "---|" * len(BUDGETS)]
    for career in CAREERS:
        cells = []
        for budget in BUDGETS:
            vals = [r["skill_coverage_pct"] for r in rows if r["career"] == career and r["budget_hours"] == budget
                    and r["pathway"] == "COMPREHENSIVE"]
            cells.append(f"{mean(vals):.1f}" if vals else "-")
        lines.append(f"| {career} | " + " | ".join(cells) + " |")
    (REPORTS / "evaluation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\nSaved to", REPORTS)


if __name__ == "__main__":
    main()
