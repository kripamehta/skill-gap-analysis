import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE = BASE_DIR / "data" / "processed" / "skill_demand_normalized.csv"
OUTPUT = BASE_DIR / "data" / "processed" / "occupation_skill_relevance.csv"

with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise ValueError(f"No records found in {SOURCE}")

required = {"occupation", "skill", "demand_percentage"}
missing = required - set(rows[0].keys())
if missing:
    raise ValueError(f"Missing columns in source CSV: {missing}")

output_rows = []
seen = set()

for row in rows:
    occupation = row.get("occupation", "").strip()
    skill = row.get("skill", "").strip()

    if not occupation or not skill:
        continue

    key = (occupation.lower(), skill.lower())
    if key in seen:
        continue
    seen.add(key)

    output_rows.append({
        "occupation": occupation,
        "onet_code": "",
        "onet_title": "",
        "skill": skill,
        "demand_percentage": row.get("demand_percentage", ""),
        "jobs_requiring_skill": row.get("jobs_requiring_skill", ""),
        "total_jobs": row.get("total_jobs", ""),
        "relevance": "Market Supported",
        "onet_matched_skill": "",
        "onet_importance": "",
        "skill_category": row.get("skill_category", ""),
    })

fields = [
    "occupation", "onet_code", "onet_title", "skill",
    "demand_percentage", "jobs_requiring_skill", "total_jobs",
    "relevance", "onet_matched_skill", "onet_importance",
    "skill_category",
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"Saved {len(output_rows)} relevance records to {OUTPUT}")
print("\nOccupation counts:")

counts = {}
for row in output_rows:
    counts[row["occupation"]] = counts.get(row["occupation"], 0) + 1

for occupation, count in sorted(counts.items()):
    print(f"{occupation}: {count} skills")
