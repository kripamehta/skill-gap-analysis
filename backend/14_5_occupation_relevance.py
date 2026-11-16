import csv
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROFILE_FILE = BASE_DIR / "data/candidate_profile.json"

DEMAND_FILE = (
    BASE_DIR
    / "data/processed/skill_demand_normalized.csv"
)

OCCUPATIONS_FILE = (
    BASE_DIR
    / "data/onet/occupations.csv"
)

SKILLS_FILE = (
    BASE_DIR
    / "data/onet/skills.csv"
)

TECHNOLOGY_FILE = (
    BASE_DIR
    / "data/onet/technology_skills.csv"
)

ALTERNATE_TITLES_FILE = (
    BASE_DIR
    / "data/onet/alternate_titles.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data/processed/occupation_skill_relevance.csv"
)


# ============================================================
# LOAD CANDIDATE PROFILE
# ============================================================

print("Loading candidate profile...")

with open(PROFILE_FILE, "r", encoding="utf-8") as f:
    profile = json.load(f)

TARGET_OCCUPATION = profile["target_occupation"].strip()

print("Target occupation:", TARGET_OCCUPATION)


# ============================================================
# FIND O*NET OCCUPATION
# ============================================================

print("\nLoading O*NET occupation data...")

onet_code = None
onet_title = None


# First check alternate titles
with open(
    ALTERNATE_TITLES_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        alternate_title = row["alternate_title"].strip().lower()

        if alternate_title == TARGET_OCCUPATION.lower():

            onet_code = row["onet_code"].strip()
            onet_title = row["standard_title"].strip()

            break


# If not found, check official occupation title
if onet_code is None:

    with open(
        OCCUPATIONS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            title = row["title"].strip().lower()

            if title == TARGET_OCCUPATION.lower():

                onet_code = row["onet_code"].strip()
                onet_title = row["title"].strip()

                break


if onet_code is None:

    print()
    print("ERROR: Could not find O*NET occupation for:")
    print(TARGET_OCCUPATION)

    raise SystemExit


print("\nOccupation mapping")
print("----------------------------------------")
print("Target occupation:", TARGET_OCCUPATION)
print("O*NET title:", onet_title)
print("O*NET code:", onet_code)


# ============================================================
# LOAD O*NET SKILLS
# ============================================================

print("\nLoading O*NET skills...")

onet_skills = {}

with open(
    SKILLS_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        if row["onet_code"].strip() != onet_code:
            continue

        skill = row["skill_name"].strip()

        if not skill:
            continue

        onet_skills[skill.lower()] = {
            "skill": skill,
            "category": row["skill_category"].strip(),
            "importance": float(row["importance_score"]),
            "description": row["description"].strip()
        }


print("O*NET occupation skills found:", len(onet_skills))


# ============================================================
# LOAD O*NET TECHNOLOGY SKILLS
# ============================================================

print("\nLoading O*NET technology skills...")

technology_skills = {}

with open(
    TECHNOLOGY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        if row["onet_code"].strip() != onet_code:
            continue

        standard_skill = row["standard_skill"].strip()

        if standard_skill:

            technology_skills[
                standard_skill.lower()
            ] = standard_skill


print(
    "O*NET technology skills found:",
    len(technology_skills)
)


# ============================================================
# LOAD MARKET SKILL DEMAND
# ============================================================

print("\nLoading job-market demand...")

market_skills = []

with open(
    DEMAND_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        if (
            row["occupation"].strip().lower()
            != TARGET_OCCUPATION.lower()
        ):
            continue

        skill = row["skill"].strip()

        if not skill:
            continue

        demand = float(row["demand_percentage"])

        jobs = int(row["jobs_requiring_skill"])

        total = int(row["total_jobs"])

        market_skills.append(
            {
                "skill": skill,
                "demand_percentage": demand,
                "jobs_requiring_skill": jobs,
                "total_jobs": total
            }
        )


market_skills.sort(
    key=lambda x: x["demand_percentage"],
    reverse=True
)


print("Market skills found:", len(market_skills))


# ============================================================
# BUILD OCCUPATION RELEVANCE
# ============================================================

results = []

for item in market_skills:

    skill = item["skill"]

    skill_lower = skill.lower()

    if skill_lower in onet_skills:

        info = onet_skills[skill_lower]

        relevance = "O*NET Supported"

        importance = info["importance"]

        category = info["category"]

        matched_skill = info["skill"]

    elif skill_lower in technology_skills:

        relevance = "O*NET Technology Supported"

        importance = ""

        category = "Technology"

        matched_skill = technology_skills[skill_lower]

    else:

        relevance = "Market Supported"

        importance = ""

        category = ""

        matched_skill = ""

    results.append(
        {
            "occupation": TARGET_OCCUPATION,
            "onet_code": onet_code,
            "onet_title": onet_title,
            "skill": skill,
            "demand_percentage": item["demand_percentage"],
            "jobs_requiring_skill": item["jobs_requiring_skill"],
            "total_jobs": item["total_jobs"],
            "relevance": relevance,
            "onet_matched_skill": matched_skill,
            "onet_importance": importance,
            "skill_category": category
        }
    )


# ============================================================
# SAVE COMPLETE DATASET
# ============================================================

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
            "onet_code",
            "onet_title",
            "skill",
            "demand_percentage",
            "jobs_requiring_skill",
            "total_jobs",
            "relevance",
            "onet_matched_skill",
            "onet_importance",
            "skill_category"
        ]
    )

    writer.writeheader()

    writer.writerows(results)


# ============================================================
# TERMINAL SUMMARY
# ============================================================

# Only show meaningful market requirements in terminal.
# The complete dataset is still saved to CSV.

important_results = [
    row
    for row in results
    if row["demand_percentage"] >= 5.0
]


important_results.sort(
    key=lambda x: x["demand_percentage"],
    reverse=True
)


# Count evidence categories
onet_count = sum(
    1
    for row in results
    if row["relevance"] == "O*NET Supported"
)

technology_count = sum(
    1
    for row in results
    if row["relevance"] == "O*NET Technology Supported"
)

market_count = sum(
    1
    for row in results
    if row["relevance"] == "Market Supported"
)


print()
print("========================================")
print("STEP 14.5 COMPLETE")
print("========================================")

print("Target occupation:", TARGET_OCCUPATION)
print("O*NET occupation:", onet_title)
print("O*NET code:", onet_code)

print()
print("Total market skills:", len(results))
print(
    "Skills with demand >= 5%:",
    len(important_results)
)

print()
print("Evidence summary")
print("----------------------------------------")
print("O*NET supported:", onet_count)
print("O*NET technology supported:", technology_count)
print("Market supported:", market_count)


print()
print("IMPORTANT OCCUPATION SKILLS")
print("----------------------------------------")

for row in important_results:

    importance = row["onet_importance"]

    if importance == "":
        importance_display = "-"
    else:
        importance_display = str(
            int(float(importance))
        )

    print(
        f"{row['skill']:<35}"
        f"{row['demand_percentage']:>7.2f}%   "
        f"{row['relevance']:<30}"
        f"O*NET importance: {importance_display}"
    )


print()
print("Saved:")
print(OUTPUT_FILE)
