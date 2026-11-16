import csv
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PATHWAY_FILE = BASE_DIR / "data/processed/learning_pathways.csv"
EVALUATION_FILE = BASE_DIR / "data/processed/pathway_evaluation.csv"
SKILL_GAP_FILE = BASE_DIR / "data/processed/skill_gap.csv"

OUTPUT_FILE = BASE_DIR / "data/processed/pathway_explanations.csv"

PROFILE_FILE = BASE_DIR / "data/candidate_profile.json"


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if value is None:
        return ""

    return str(value).strip()


def to_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================================
# LOAD PROFILE
# ============================================================

print("Loading candidate profile...")

with open(
    PROFILE_FILE,
    "r",
    encoding="utf-8"
) as f:

    profile = json.load(f)


target_occupation = profile[
    "target_occupation"
]

time_budget = float(
    profile["time_budget_hours"]
)


# ============================================================
# LOAD PATHWAYS
# ============================================================

print("Loading pathways...")

with open(
    PATHWAY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    pathway_rows = list(
        csv.DictReader(f)
    )


# ============================================================
# LOAD EVALUATION
# ============================================================

print("Loading pathway evaluation...")

with open(
    EVALUATION_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    evaluation_rows = list(
        csv.DictReader(f)
    )


evaluation = {}

for row in evaluation_rows:

    pathway = clean(
        row["pathway"]
    )

    evaluation[pathway] = row


# ============================================================
# LOAD SKILL GAP
# ============================================================

print("Loading skill gaps...")

with open(
    SKILL_GAP_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    skill_gap_rows = list(
        csv.DictReader(f)
    )


missing_skills = [
    clean(row.get("skill", ""))
    for row in skill_gap_rows
    if clean(row.get("skill", ""))
    and clean(row.get("gap_status", "")).lower() == "skill gap"
]
# ============================================================
# GROUP PATHWAYS
# ============================================================

pathways = {}

for row in pathway_rows:

    pathway_name = clean(
        row["pathway"]
    )

    if pathway_name not in pathways:

        pathways[pathway_name] = []

    pathways[pathway_name].append(row)


# ============================================================
# CREATE EXPLANATIONS
# ============================================================

results = []


for pathway_name, courses in pathways.items():

    stats = evaluation[pathway_name]

    total_time = to_float(
        stats["total_time_hours"]
    )

    skills_covered = int(
        to_float(
            stats["skills_covered"]
        )
    )

    total_missing = int(
        to_float(
            stats["total_missing_skills"]
        )
    )

    skill_coverage = to_float(
        stats["skill_coverage_percentage"]
    )

    demand_coverage = to_float(
        stats["demand_coverage_percentage"]
    )

    rating = to_float(
        stats["average_course_rating"]
    )

    quality_score = to_float(
        stats["quality_score"]
    )

    # --------------------------------------------------------
    # Course descriptions
    # --------------------------------------------------------

    course_descriptions = []

    all_covered_skills = []

    for course in courses:

        course_name = clean(
            course["course_name"]
        )

        covers = clean(
            course["covers"]
        )

        duration = to_float(
            course["duration_hours"]
        )

        all_covered_skills.append(
            covers
        )

        course_descriptions.append(
            f"{course_name} "
            f"({duration:.0f} hours) "
            f"covers {covers}."
        )

    # --------------------------------------------------------
    # Pathway-specific explanation
    # --------------------------------------------------------

    if pathway_name.upper() == "FASTEST":

        explanation = (
            f"The Fastest pathway is designed to "
            f"minimize learning time while still "
            f"addressing important skill gaps for "
            f"{target_occupation}. "
            f"It requires {total_time:.0f} hours, "
            f"which is within the candidate's "
            f"{time_budget:.0f}-hour learning budget. "
            f"It covers {skills_covered} of "
            f"{total_missing} identified skill gaps "
            f"and achieves {demand_coverage:.2f}% "
            f"demand coverage."
        )

    elif pathway_name.upper() == "COMPREHENSIVE":

        explanation = (
            f"The Comprehensive pathway is designed "
            f"to maximize skill coverage within the "
            f"candidate's available learning time. "
            f"It uses {total_time:.0f} of the "
            f"{time_budget:.0f} available hours and "
            f"covers {skills_covered} of "
            f"{total_missing} identified skill gaps. "
            f"It achieves the highest demand coverage "
            f"among the generated pathways at "
            f"{demand_coverage:.2f}%. "
            f"This makes it the strongest option when "
            f"the candidate prioritizes broader "
            f"job-readiness over minimum study time."
        )

    elif pathway_name.upper() == "BALANCED":

        explanation = (
            f"The Balanced pathway provides a compromise "
            f"between learning time and skill coverage. "
            f"It requires {total_time:.0f} hours, leaving "
            f"{time_budget - total_time:.0f} hours "
            f"within the candidate's learning budget. "
            f"It covers {skills_covered} of "
            f"{total_missing} identified skill gaps "
            f"and achieves {demand_coverage:.2f}% "
            f"demand coverage."
        )

    else:

        explanation = (
            f"This pathway requires "
            f"{total_time:.0f} hours and covers "
            f"{skills_covered} of "
            f"{total_missing} identified skill gaps, "
            f"with {demand_coverage:.2f}% demand coverage."
        )

    # --------------------------------------------------------
    # Why these courses?
    # --------------------------------------------------------

    course_reason = (
        " ".join(course_descriptions)
    )

    # --------------------------------------------------------
    # Overall explanation
    # --------------------------------------------------------

    overall_explanation = (
        f"{explanation} "
        f"The average course rating is "
        f"{rating:.2f}/5 and the pathway evaluation "
        f"score is {quality_score:.2f}/100."
    )

    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    results.append({

        "pathway":
            pathway_name,

        "target_occupation":
            target_occupation,

        "time_budget_hours":
            time_budget,

        "total_time_hours":
            total_time,

        "skills_covered":
            skills_covered,

        "total_missing_skills":
            total_missing,

        "skill_coverage_percentage":
            skill_coverage,

        "demand_coverage_percentage":
            demand_coverage,

        "average_course_rating":
            rating,

        "quality_score":
            quality_score,

        "explanation":
            overall_explanation,

        "course_reason":
            course_reason
    })


# ============================================================
# SAVE
# ============================================================

fieldnames = [

    "pathway",

    "target_occupation",

    "time_budget_hours",

    "total_time_hours",

    "skills_covered",

    "total_missing_skills",

    "skill_coverage_percentage",

    "demand_coverage_percentage",

    "average_course_rating",

    "quality_score",

    "explanation",

    "course_reason"
]


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 40)
print("STEP 20 COMPLETE")
print("=" * 40)


for result in results:

    print()
    print(
        result["pathway"].upper()
    )

    print("-" * 40)

    print(
        "Explanation:"
    )

    print(
        result["explanation"]
    )

    print()

    print(
        "Course reasoning:"
    )

    print(
        result["course_reason"]
    )


print()
print("Saved:")
print(OUTPUT_FILE)
