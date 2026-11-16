import csv
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

PROCESSED.mkdir(parents=True, exist_ok=True)

POSTINGS_FILE = RAW / "linkedin_job_postings.csv"


# =========================================================
# OCCUPATIONS SUPPORTED BY OUR PROJECT
# =========================================================

ROLE_KEYWORDS = {

    # More specific roles FIRST
    # so they are not incorrectly classified as
    # generic Software Developer.

    "Full Stack Developer": [
        "full stack",
        "full-stack"
    ],

    "Frontend Developer": [
        "frontend",
        "front end",
        "front-end"
    ],

    "Backend Developer": [
        "backend",
        "back end",
        "back-end"
    ],

    "Mobile App Developer": [
        "mobile developer",
        "mobile app developer",
        "android developer",
        "android engineer",
        "ios developer",
        "ios engineer"
    ],

    "Machine Learning Engineer": [
        "machine learning engineer",
        "machine learning developer",
        "ml engineer"
    ],

    "AI Engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "ai developer"
    ],

    "Data Engineer": [
        "data engineer"
    ],

    "Data Scientist": [
        "data scientist"
    ],

    "Data Analyst": [
        "data analyst",
        "business analyst",
        "reporting analyst",
        "bi analyst"
    ],

    "Cybersecurity Analyst": [
        "cybersecurity analyst",
        "cyber security analyst",
        "information security analyst",
        "security analyst"
    ],

    "DevOps Engineer": [
        "devops engineer",
        "dev ops engineer"
    ],

    "Cloud Engineer": [
        "cloud engineer",
        "cloud developer",
        "cloud architect"
    ],

    "Network Engineer": [
        "network engineer",
        "network administrator"
    ],

    "Database Administrator": [
        "database administrator",
        "database admin",
        "dba"
    ],

    "QA / Software Test Engineer": [
        "qa engineer",
        "quality assurance engineer",
        "software test engineer",
        "test engineer",
        "automation test engineer",
        "qa tester"
    ],

    # Generic role LAST
    "Software Developer": [
        "software developer",
        "software engineer",
        "application developer",
        "application engineer"
    ]
}


def classify_job(title):

    title = title.lower().strip()

    for occupation, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in title:
                return occupation

    return None


# =========================================================
# READ LINKEDIN POSTINGS
# =========================================================

print("\nReading LinkedIn job postings...")

with open(
    POSTINGS_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    columns = reader.fieldnames

    print("\nColumns found:")
    print(columns)

    link_column = "job_link"
    title_column = "job_title"

    if link_column not in columns:
        raise Exception("job_link column not found.")

    if title_column not in columns:
        raise Exception("job_title column not found.")


# =========================================================
# FILTER JOBS
# =========================================================

selected_jobs = []

seen_links = set()

with open(
    POSTINGS_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        title = row.get(title_column, "")

        occupation = classify_job(title)

        if occupation is None:
            continue

        job_link = row.get(link_column, "")

        # Remove duplicate job postings
        if not job_link or job_link in seen_links:
            continue

        seen_links.add(job_link)

        selected_jobs.append({
            "job_link": job_link,
            "job_title": title,
            "occupation": occupation,

            # Correct column names from your dataset
            "company": row.get("company", ""),
            "location": row.get("job_location", "")
        })


# =========================================================
# SAVE
# =========================================================

output_file = PROCESSED / "filtered_jobs.csv"

with open(
    output_file,
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
            "company",
            "location"
        ]
    )

    writer.writeheader()
    writer.writerows(selected_jobs)


# =========================================================
# RESULTS
# =========================================================

print("\n" + "=" * 60)
print("FILTERING COMPLETE")
print("=" * 60)

print("Selected unique jobs:", len(selected_jobs))
print("Saved to:", output_file)

print("\nOccupation counts:")

counts = {}

for job in selected_jobs:

    occupation = job["occupation"]

    counts[occupation] = counts.get(
        occupation,
        0
    ) + 1

for occupation, count in sorted(
    counts.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(f"{occupation}: {count}")
