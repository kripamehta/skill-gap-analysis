import csv
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

JOBS_FILE = PROCESSED / "jobs.csv"
LINKEDIN_SKILLS_FILE = RAW / "job_skills.csv"

OUTPUT_FILE = PROCESSED / "job_skills.csv"


# =========================================================
# STEP 1
# Get the job links that belong to our project
# =========================================================

project_jobs = {}

with open(
    JOBS_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        project_jobs[row["job_link"]] = {
            "job_title": row["job_title"],
            "occupation": row["occupation"]
        }


print("Project jobs:", len(project_jobs))


# =========================================================
# STEP 2
# Read LinkedIn's original skill information
# =========================================================

skill_rows = []

with open(
    LINKEDIN_SKILLS_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    print("\nColumns:")
    print(reader.fieldnames)

    for row in reader:

        job_link = row.get("job_link", "")

        # Only keep jobs that belong to our project
        if job_link not in project_jobs:
            continue

        skills = row.get("job_skills", "")

        if not skills.strip():
            continue

        job_info = project_jobs[job_link]

        # LinkedIn has stored multiple skills in one cell.
        # Separate them into individual skills.

        individual_skills = [
            skill.strip()
            for skill in skills.split(",")
            if skill.strip()
        ]

        for skill in individual_skills:

            skill_rows.append({
                "job_link": job_link,
                "job_title": job_info["job_title"],
                "occupation": job_info["occupation"],
                "skill": skill
            })


# =========================================================
# STEP 3
# Remove duplicate job-skill combinations
# =========================================================

unique_rows = {}

for row in skill_rows:

    key = (
        row["job_link"],
        row["skill"].lower()
    )

    unique_rows[key] = row


skill_rows = list(unique_rows.values())


# =========================================================
# STEP 4
# Save
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "job_link",
            "job_title",
            "occupation",
            "skill"
        ]
    )

    writer.writeheader()
    writer.writerows(skill_rows)


print("\n" + "=" * 60)
print("JOB SKILL DATASET CREATED")
print("=" * 60)

print("Job-skill records:", len(skill_rows))
print("Saved to:", OUTPUT_FILE)

print("\nFirst 10 records:")

for row in skill_rows[:10]:
    print(
        row["occupation"],
        "|",
        row["skill"]
    )
