import csv
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROFILE_FILE = BASE_DIR / "data/candidate_profile.json"

SKILL_GAP_FILE = (
    BASE_DIR
    / "data/processed/skill_gap.csv"
)

DEPENDENCY_FILE = (
    BASE_DIR
    / "data/skill_dependencies.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data/processed/skill_gap_dependencies.csv"
)


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

candidate_skills = {
    skill.strip().lower()
    for skill in profile["current_skills"]
    if skill.strip()
}


print()
print("Target occupation:", TARGET_OCCUPATION)

print("Candidate skills:")

for skill in sorted(candidate_skills):
    print("  -", skill)


# ============================================================
# LOAD SKILL GAP
# ============================================================

print()
print("Loading skill gap...")

missing_skills = set()

with open(
    SKILL_GAP_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        if (
            row["gap_status"].strip()
            == "Skill Gap"
        ):

            skill = row["skill"].strip().lower()

            if skill:
                missing_skills.add(skill)


print(
    "Missing skills:",
    len(missing_skills)
)


# ============================================================
# LOAD DEPENDENCY KNOWLEDGE BASE
# ============================================================

print()
print("Loading prerequisite knowledge base...")

dependencies = []

with open(
    DEPENDENCY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        prerequisite = (
            row["prerequisite_skill"]
            .strip()
        )

        dependent = (
            row["dependent_skill"]
            .strip()
        )

        strength = (
            row["dependency_strength"]
            .strip()
        )

        rationale = (
            row["rationale"]
            .strip()
        )

        if not prerequisite or not dependent:
            continue

        dependencies.append(
            {
                "prerequisite": prerequisite,
                "dependent": dependent,
                "strength": strength,
                "rationale": rationale
            }
        )


print(
    "Dependency relationships loaded:",
    len(dependencies)
)


# ============================================================
# BUILD RELEVANT DEPENDENCY GRAPH
# ============================================================

graph_rows = []

for dependency in dependencies:

    prerequisite = dependency["prerequisite"]

    dependent = dependency["dependent"]

    prerequisite_lower = prerequisite.lower()

    dependent_lower = dependent.lower()

    # --------------------------------------------------------
    # We only need dependencies that affect a missing skill.
    #
    # Example:
    #
    # Excel -> SQL
    #
    # If SQL is missing, this relationship matters.
    # --------------------------------------------------------

    if dependent_lower not in missing_skills:
        continue

    # --------------------------------------------------------
    # Determine prerequisite status.
    # --------------------------------------------------------

    if prerequisite_lower in candidate_skills:

        prerequisite_status = "Already Satisfied"

    elif prerequisite_lower in missing_skills:

        prerequisite_status = "Skill Gap"

    else:

        prerequisite_status = "External Prerequisite"

    graph_rows.append(
        {
            "prerequisite": prerequisite,
            "dependent": dependent,
            "strength": dependency["strength"],
            "rationale": dependency["rationale"],
            "prerequisite_status": prerequisite_status
        }
    )


# ============================================================
# SAVE GRAPH
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = [
        "prerequisite",
        "dependent",
        "strength",
        "rationale",
        "prerequisite_status"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(graph_rows)


# ============================================================
# SUMMARIZE GRAPH
# ============================================================

skill_gap_prerequisites = [
    row
    for row in graph_rows
    if row["prerequisite_status"]
    == "Skill Gap"
]

satisfied_prerequisites = [
    row
    for row in graph_rows
    if row["prerequisite_status"]
    == "Already Satisfied"
]

external_prerequisites = [
    row
    for row in graph_rows
    if row["prerequisite_status"]
    == "External Prerequisite"
]


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("========================================")
print("STEP 16 COMPLETE")
print("========================================")

print("Target occupation:", TARGET_OCCUPATION)

print(
    "Missing skills:",
    len(missing_skills)
)

print(
    "Relevant prerequisite relationships:",
    len(graph_rows)
)

print(
    "Prerequisites that are also skill gaps:",
    len(skill_gap_prerequisites)
)

print(
    "Prerequisites already satisfied:",
    len(satisfied_prerequisites)
)

print(
    "External prerequisites:",
    len(external_prerequisites)
)


print()
print("PREREQUISITE GRAPH")
print("----------------------------------------")

if graph_rows:

    for row in graph_rows:

        print(
            f"{row['prerequisite']}"
            f" -> "
            f"{row['dependent']}"
            f" | {row['strength']}"
            f" | {row['prerequisite_status']}"
        )

else:

    print(
        "No prerequisite relationships "
        "were found for the current skill gaps."
    )


print()
print("Saved:")
print(OUTPUT_FILE)
