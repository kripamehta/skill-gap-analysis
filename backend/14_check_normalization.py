import csv
from collections import defaultdict


TECHNICAL_FILE = "data/processed/technical_job_skills.csv"
NORMALIZATION_FILE = "data/processed/skill_normalization.csv"
JOBS_FILE = "data/processed/jobs.csv"

OUTPUT_FILE = "data/processed/skill_demand_normalized.csv"


# =========================================================
# 1. Load skill normalization
# =========================================================

print("Loading skill normalization...")

normalization = {}

with open(
    NORMALIZATION_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        raw_skill = row["job_skill"].strip()
        normalized_skill = row["normalized_skill"].strip()

        if raw_skill and normalized_skill:

            normalization[
                raw_skill.lower()
            ] = normalized_skill


print(
    "Normalization mappings:",
    len(normalization)
)


# =========================================================
# 2. Load jobs
# =========================================================

print("Loading jobs...")

job_occupation = {}

with open(
    JOBS_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        job_link = row["job_link"].strip()
        occupation = row["occupation"].strip()

        if job_link and occupation:

            job_occupation[job_link] = occupation


# Count total jobs in each occupation
occupation_jobs = defaultdict(set)

for job_link, occupation in job_occupation.items():

    occupation_jobs[
        occupation
    ].add(job_link)


print(
    "Total jobs:",
    len(job_occupation)
)


# =========================================================
# 3. Read technical job skills
# =========================================================

print("Processing technical job skills...")

# occupation -> normalized skill -> set(job_links)
skill_jobs = defaultdict(
    lambda: defaultdict(set)
)


with open(
    TECHNICAL_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        job_link = row["job_link"].strip()
        occupation = row["occupation"].strip()
        raw_skill = row["skill"].strip()

        if not job_link or not occupation or not raw_skill:
            continue

        # -------------------------------------------------
        # Find normalized form
        # -------------------------------------------------

        normalized_skill = normalization.get(
            raw_skill.lower(),
            raw_skill
        )

        # -------------------------------------------------
        # Count each job only once for a skill
        # -------------------------------------------------

        skill_jobs[
            occupation
        ][
            normalized_skill
        ].add(job_link)


# =========================================================
# 4. Calculate demand percentage
# =========================================================

results = []


for occupation in sorted(skill_jobs.keys()):

    total_jobs = len(
        occupation_jobs[occupation]
    )

    if total_jobs == 0:
        continue

    for skill, job_links in skill_jobs[
        occupation
    ].items():

        jobs_requiring_skill = len(job_links)

        demand_percentage = (
            jobs_requiring_skill
            / total_jobs
        ) * 100

        results.append({
            "occupation": occupation,
            "skill": skill,
            "jobs_requiring_skill":
                jobs_requiring_skill,
            "total_jobs":
                total_jobs,
            "demand_percentage":
                round(demand_percentage, 2)
        })


# =========================================================
# 5. Sort
# =========================================================

results.sort(
    key=lambda x: (
        x["occupation"],
        -x["demand_percentage"]
    )
)


# =========================================================
# 6. Save
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "occupation",
            "skill",
            "jobs_requiring_skill",
            "total_jobs",
            "demand_percentage"
        ]
    )

    writer.writeheader()
    writer.writerows(results)


# =========================================================
# 7. Display top skills
# =========================================================

print("\n========================================")
print("STEP 14 COMPLETE")
print("========================================")

print(
    "Skill-demand records:",
    len(results)
)


print("\nTOP SKILLS BY OCCUPATION")
print("----------------------------------------")


occupations = sorted(
    set(row["occupation"] for row in results)
)


for occupation in occupations:

    occupation_results = [
        row
        for row in results
        if row["occupation"] == occupation
    ]

    occupation_results = sorted(
        occupation_results,
        key=lambda x: x["demand_percentage"],
        reverse=True
    )

    print(
        f"\n{occupation}"
    )

    for row in occupation_results[:10]:

        print(
            f"  {row['skill']:30}"
            f" {row['demand_percentage']:6.2f}%"
        )


print("\nSaved:")
print(OUTPUT_FILE)
