import csv
from collections import defaultdict

INPUT_FILE = "data/processed/job_skills.csv"
OUTPUT_FILE = "data/processed/skill_demand.csv"


# ---------------------------------------------------------
# 1. Store skills for each occupation
# ---------------------------------------------------------

occupation_skill_jobs = defaultdict(lambda: defaultdict(set))
occupation_jobs = defaultdict(set)

with open(INPUT_FILE, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        occupation = row["occupation"].strip()
        job_link = row["job_link"].strip()
        skill = row["skill"].strip()

        if not occupation or not job_link or not skill:
            continue

        # Store the job once for this occupation
        occupation_jobs[occupation].add(job_link)

        # Store which jobs require this skill
        occupation_skill_jobs[occupation][skill].add(job_link)


# ---------------------------------------------------------
# 2. Calculate percentage demand for each skill
# ---------------------------------------------------------

results = []

for occupation in occupation_skill_jobs:

    total_jobs = len(occupation_jobs[occupation])

    for skill in occupation_skill_jobs[occupation]:

        jobs_requiring_skill = len(
            occupation_skill_jobs[occupation][skill]
        )

        demand_percentage = (
            jobs_requiring_skill / total_jobs
        ) * 100

        results.append({
            "occupation": occupation,
            "skill": skill,
            "jobs_requiring_skill": jobs_requiring_skill,
            "total_jobs": total_jobs,
            "demand_percentage": round(demand_percentage, 2)
        })


# ---------------------------------------------------------
# 3. Sort by occupation and demand
# ---------------------------------------------------------

results.sort(
    key=lambda x: (
        x["occupation"],
        -x["demand_percentage"]
    )
)


# ---------------------------------------------------------
# 4. Save results
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    fieldnames = [
        "occupation",
        "skill",
        "jobs_requiring_skill",
        "total_jobs",
        "demand_percentage"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)


# ---------------------------------------------------------
# 5. Display a small preview
# ---------------------------------------------------------

print("=" * 60)
print("SKILL DEMAND CALCULATION COMPLETE")
print("=" * 60)

print(f"Skill-demand records: {len(results)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nTop skills for each occupation:\n")

current_occupation = None
count = 0

for row in results:

    if row["occupation"] != current_occupation:
        current_occupation = row["occupation"]
        count = 0

        print(f"\n{current_occupation}")

    if count < 5:
        print(
            f"  {row['skill']} -> "
            f"{row['demand_percentage']}%"
        )

        count += 1
