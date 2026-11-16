from __future__ import annotations

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.recommendation_engine import (
    generate_dynamic_recommendations,
    normalize_skill,
)

OUTPUT = BASE_DIR / "reports" / "occupation_test_matrix.csv"
TIME_BUDGET = 40

TEST_PROFILES = {
    "Data Analyst": ["Python", "Git", "Excel"],
    "Data Scientist": ["Python", "SQL", "Statistics"],
    "Software Developer": ["Python", "Git"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript"],
    "QA / Software Test Engineer": ["Python", "SQL"],
    "Network Engineer": ["Networking", "Linux"],
    "Data Engineer": ["Python", "SQL"],
    "Cybersecurity Analyst": ["Networking", "Linux"],
    "Database Administrator": ["SQL", "Linux"],
    "Machine Learning Engineer": ["Python", "SQL"],
    "DevOps Engineer": ["Linux", "Git", "Python"],
    "Cloud Engineer": ["Linux", "Python"],
    "Frontend Developer": ["HTML", "CSS", "JavaScript"],
    "Backend Developer": ["Python", "SQL"],
    "Mobile App Developer": ["Java"],
    "AI Engineer": ["Python", "Machine Learning"],
}


def main() -> None:
    rows = []

    for occupation, current_skills in TEST_PROFILES.items():
        try:
            result = generate_dynamic_recommendations(
                target_occupation=occupation,
                current_skills=current_skills,
                time_budget_hours=TIME_BUDGET,
            )

            current = {normalize_skill(s) for s in current_skills}
            gaps = result.get("skill_gaps", [])
            gap_skills = {normalize_skill(g["skill"]) for g in gaps}
            pathways = result.get("pathways", {})
            evaluations = result.get("evaluations", {})

            errors = []
            if current & gap_skills:
                errors.append("Current skill incorrectly listed as a gap")

            for name, evaluation in evaluations.items():
                if not evaluation.get("time_feasible", False):
                    errors.append(f"{name} exceeds time budget")
                if not evaluation.get("strict_prerequisites_valid", False):
                    errors.append(f"{name} has strict prerequisite violations")

            if not pathways:
                status = "FAIL: no pathways"
            elif errors:
                status = "FAIL: " + "; ".join(errors)
            elif len(pathways) < 3:
                status = "PARTIAL: fewer than 3 distinct feasible pathways"
            else:
                status = "PASS"

            fastest = pathways.get("FASTEST", [])
            fastest_skills = sorted({
                normalize_skill(skill)
                for course in fastest
                for skill in course.get("covers", [])
            })
            top_gap = gaps[0] if gaps else {}

            rows.append({
                "occupation": occupation,
                "status": status,
                "current_skills": "; ".join(current_skills),
                "skill_gap_count": len(gaps),
                "top_missing_skill": top_gap.get("skill", ""),
                "top_missing_demand_pct": top_gap.get("demand_percentage", ""),
                "fastest_courses": "; ".join(c["course_name"] for c in fastest),
                "fastest_covers": "; ".join(fastest_skills),
                "fastest_hours": evaluations.get("FASTEST", {}).get("total_time_hours", ""),
                "pathway_types_returned": "; ".join(pathways.keys()),
                "prerequisites_valid": all(
                    e.get("strict_prerequisites_valid", False)
                    for e in evaluations.values()
                ) if evaluations else False,
                "time_feasible": all(
                    e.get("time_feasible", False)
                    for e in evaluations.values()
                ) if evaluations else False,
                "notes": " | ".join(errors),
            })

        except Exception as exc:
            rows.append({
                "occupation": occupation,
                "status": "ERROR",
                "current_skills": "; ".join(current_skills),
                "notes": f"{type(exc).__name__}: {exc}",
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "occupation", "status", "current_skills", "skill_gap_count",
        "top_missing_skill", "top_missing_demand_pct", "fastest_courses",
        "fastest_covers", "fastest_hours", "pathway_types_returned",
        "prerequisites_valid", "time_feasible", "notes",
    ]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Tested {len(rows)} occupations.")
    print(f"Saved report to: {OUTPUT}")
    for row in rows:
        print(f"{row['occupation']}: {row['status']}")
        if row.get("notes"):
            print(f"  {row['notes']}")


if __name__ == "__main__":
    main()
