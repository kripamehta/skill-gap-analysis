import csv
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROFILE_FILE = BASE_DIR / "data/candidate_profile.json"

RELEVANCE_FILE = (
    BASE_DIR
    / "data/processed/occupation_skill_relevance.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data/processed/skill_gap.csv"
)


# ============================================================
# SETTINGS
# ============================================================

# Only skills appearing in at least this percentage
# of job postings are considered core market requirements.
MIN_DEMAND_PERCENTAGE = 5.0


# ============================================================
# LOAD CANDIDATE PROFILE
# ============================================================

print("Loading candidate profile...")

with open(
    PROFILE_FILE,
    "r",
    encoding="utf-8"
) as f:

    profile = json.load(f)


TARGET_OCCUPATION = profile["target_occupation"].strip()

CANDIDATE_SKILLS = profile["current_skills"]

TIME_BUDGET = float(profile["time_budget_hours"])


# Normalize candidate skills for comparison.
candidate_skill_set = {
    skill.strip().lower()
    for skill in CANDIDATE_SKILLS
    if skill.strip()
}


print()
print("Candidate profile")
print("----------------------------------------")
print("Target occupation:", TARGET_OCCUPATION)
print("Time budget:", TIME_BUDGET, "hours")

print("Current skills:")

for skill in sorted(candidate_skill_set):
    print("  -", skill)


# ============================================================
# LOAD OCCUPATION RELEVANCE DATA
# ============================================================

print()
print("Loading occupation skill relevance...")

market_requirements = []

with open(
    RELEVANCE_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        # Safety check: only use the selected occupation.
        if (
            row["occupation"].strip().lower()
            != TARGET_OCCUPATION.lower()
        ):
            continue

        demand = float(row["demand_percentage"])

        # Ignore low-frequency market noise.
        if demand < MIN_DEMAND_PERCENTAGE:
            continue

        skill = row["skill"].strip()

        if not skill:
            continue

        market_requirements.append(
            {
                "skill": skill,
                "demand_percentage": demand,
                "jobs_requiring_skill": int(
                    row["jobs_requiring_skill"]
                ),
                "total_jobs": int(
                    row["total_jobs"]
                ),
                "relevance": row["relevance"].strip(),
                "onet_matched_skill": (
                    row["onet_matched_skill"].strip()
                ),
                "onet_importance": (
                    row["onet_importance"].strip()
                ),
                "skill_category": (
                    row["skill_category"].strip()
                )
            }
        )


# Remove accidental duplicate skill names.
unique_requirements = {}

for item in market_requirements:

    key = item["skill"].lower()

    if key not in unique_requirements:

        unique_requirements[key] = item

    else:

        # Keep the higher-demand occurrence.
        if (
            item["demand_percentage"]
            > unique_requirements[key]["demand_percentage"]
        ):

            unique_requirements[key] = item


market_requirements = list(
    unique_requirements.values()
)


# Sort by market demand.
market_requirements.sort(
    key=lambda x: x["demand_percentage"],
    reverse=True
)


print(
    "Core market requirements:",
    len(market_requirements)
)


# ============================================================
# BUILD SKILL GAP
# ============================================================

skill_gap = []

for requirement in market_requirements:

    skill = requirement["skill"]

    skill_lower = skill.lower()

    # --------------------------------------------------------
    # Candidate skill matching
    # --------------------------------------------------------
    #
    # The market dataset has already been normalized.
    # Candidate skills are therefore compared using a
    # case-insensitive normalized form.
    #
    candidate_has_skill = (
        skill_lower in candidate_skill_set
    )

    # --------------------------------------------------------
    # Priority based on market demand
    # --------------------------------------------------------

    demand = requirement["demand_percentage"]

    if demand >= 20:

        priority = "High"

    elif demand >= 10:

        priority = "Medium"

    else:

        priority = "Low"

    # --------------------------------------------------------
    # Gap status
    # --------------------------------------------------------

    if candidate_has_skill:

        gap_status = "Skill Present"

    else:

        gap_status = "Skill Gap"

    skill_gap.append(
        {
            "occupation": TARGET_OCCUPATION,
            "skill": skill,
            "demand_percentage": demand,
            "jobs_requiring_skill": (
                requirement["jobs_requiring_skill"]
            ),
            "total_jobs": (
                requirement["total_jobs"]
            ),
            "relevance": (
                requirement["relevance"]
            ),
            "onet_matched_skill": (
                requirement["onet_matched_skill"]
            ),
            "onet_importance": (
                requirement["onet_importance"]
            ),
            "skill_category": (
                requirement["skill_category"]
            ),
            "candidate_has_skill": (
                "Yes"
                if candidate_has_skill
                else "No"
            ),
            "gap_status": gap_status,
            "priority": priority,
            "time_budget_hours": TIME_BUDGET
        }
    )


# ============================================================
# SAVE SKILL GAP
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = [
        "occupation",
        "skill",
        "demand_percentage",
        "jobs_requiring_skill",
        "total_jobs",
        "relevance",
        "onet_matched_skill",
        "onet_importance",
        "skill_category",
        "candidate_has_skill",
        "gap_status",
        "priority",
        "time_budget_hours"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(skill_gap)


# ============================================================
# CREATE SUMMARY
# ============================================================

present_skills = [
    row
    for row in skill_gap
    if row["gap_status"] == "Skill Present"
]

missing_skills = [
    row
    for row in skill_gap
    if row["gap_status"] == "Skill Gap"
]


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("========================================")
print("STEP 15 COMPLETE")
print("========================================")

print("Target occupation:", TARGET_OCCUPATION)

print(
    "Core market requirements:",
    len(skill_gap)
)

print(
    "Candidate skills already present:",
    len(present_skills)
)

print(
    "Missing skills:",
    len(missing_skills)
)


print()
print("CURRENT SKILLS ALREADY SATISFYING REQUIREMENTS")
print("----------------------------------------")

if present_skills:

    for row in present_skills:

        print(
            f"{row['skill']:<30}"
            f"{row['demand_percentage']:>7.2f}%   "
            f"{row['relevance']}"
        )

else:

    print("None")


print()
print("IDENTIFIED SKILL GAPS")
print("----------------------------------------")

for row in missing_skills:

    print(
        f"{row['skill']:<30}"
        f"{row['demand_percentage']:>7.2f}%   "
        f"{row['priority']:<8} "
        f"{row['relevance']}"
    )


print()
print("Saved:")
print(OUTPUT_FILE)
