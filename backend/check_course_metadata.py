from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
COURSES = BASE_DIR / "data" / "raw" / "courses.csv"
DEPENDENCIES = BASE_DIR / "data" / "skill_dependencies.csv"

EXPECTED_OCCUPATIONS = {
    "Data Analyst", "Data Scientist", "Software Developer",
    "Full Stack Developer", "QA / Software Test Engineer",
    "Network Engineer", "Data Engineer", "Cybersecurity Analyst",
    "Database Administrator", "Machine Learning Engineer",
    "DevOps Engineer", "Cloud Engineer", "Frontend Developer",
    "Backend Developer", "Mobile App Developer", "AI Engineer",
}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    problems = []
    courses = read_csv(COURSES)
    ids = set()
    role_coverage = {role.lower(): 0 for role in EXPECTED_OCCUPATIONS}

    for line, row in enumerate(courses, start=2):
        cid = row.get("course_id", "").strip()
        if not cid:
            problems.append(f"Course row {line}: missing course_id")
        elif cid in ids:
            problems.append(f"Course row {line}: duplicate course_id {cid}")
        ids.add(cid)

        for field in ("course_name", "provider", "skills", "description"):
            if not row.get(field, "").strip():
                problems.append(f"{cid}: missing {field}")

        try:
            duration = float(row.get("duration_hours", ""))
            if duration <= 0:
                problems.append(f"{cid}: duration_hours must be positive")
        except ValueError:
            problems.append(f"{cid}: invalid duration_hours")

        url = urlparse(row.get("url", "").strip())
        if url.scheme not in {"http", "https"} or not url.netloc:
            problems.append(f"{cid}: invalid URL")

        roles = [
            x.strip().lower()
            for x in row.get("relevant_occupations", "").split(";")
            if x.strip()
        ]
        if not roles:
            problems.append(f"{cid}: no relevant_occupations metadata")
        for role in roles:
            if role in role_coverage:
                role_coverage[role] += 1

    for role, count in role_coverage.items():
        if count == 0:
            problems.append(f"No courses mapped to occupation: {role}")

    dependencies = read_csv(DEPENDENCIES)
    for line, row in enumerate(dependencies, start=2):
        strength = row.get("dependency_strength", "").strip().upper()
        if strength not in {"STRICT", "RECOMMENDED"}:
            problems.append(
                f"Dependency row {line}: invalid strength {strength}")
        if not row.get("prerequisite_skill", "").strip():
            problems.append(
                f"Dependency row {line}: missing prerequisite_skill")
        if not row.get("dependent_skill", "").strip():
            problems.append(f"Dependency row {line}: missing dependent_skill")

    print(f"Courses checked: {len(courses)}")
    print(f"Dependency rows checked: {len(dependencies)}")
    print("Course counts by occupation:")
    for role, count in sorted(role_coverage.items()):
        print(f"  {role}: {count}")

    if problems:
        print(f"\nFound {len(problems)} issue(s):")
        for issue in problems:
            print(" -", issue)
        raise SystemExit(1)

    print("\nPASS: structural metadata checks succeeded.")
    print("Manual follow-up: open course URLs and verify claims against course pages.")


if __name__ == "__main__":
    main()
