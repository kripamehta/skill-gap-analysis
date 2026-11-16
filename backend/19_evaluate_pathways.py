import csv
import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PATHWAY_FILE = BASE_DIR / "data/processed/learning_pathways.csv"
SKILL_GAP_FILE = BASE_DIR / "data/processed/skill_gap.csv"
OUTPUT_FILE = BASE_DIR / "data/processed/pathway_evaluation.csv"
PROFILE_FILE = BASE_DIR / "data/candidate_profile.json"
MAPPING_FILE = BASE_DIR / "data/processed/course_skill_mapping.csv"
DEPENDENCY_FILE = BASE_DIR / "data/processed/skill_gap_dependencies.csv"


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
# LOAD CANDIDATE PROFILE
# ============================================================

print("Loading candidate profile...")

with open(
    PROFILE_FILE,
    "r",
    encoding="utf-8"
) as f:

    profile = json.load(f)


TIME_BUDGET = float(
    profile["time_budget_hours"]
)

print(
    f"Time budget: "
    f"{TIME_BUDGET} hours"
)


# ============================================================
# LOAD SKILL GAP
# ============================================================

print("\nLoading skill gap...")

with open(
    SKILL_GAP_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    skill_gap_rows = list(
        csv.DictReader(f)
    )


print(
    f"Skill-gap records: "
    f"{len(skill_gap_rows)}"
)


# Find actual missing skills
#
# skill_gap.csv contains both:
# - Skill Gap
# - Skill Present
#
# Only rows marked "Skill Gap" are counted.

missing_skills = {
    clean(row.get("skill", "")).lower()
    for row in skill_gap_rows
    if clean(row.get("skill", ""))
    and clean(row.get("gap_status", "")).lower() == "skill gap"
}

print(
    f"Missing skills: "
    f"{len(missing_skills)}"
)


# Load all normalized course-to-skill mappings. This is used to
# calculate catalogue coverage from the actual data, not a hardcoded count.
with open(MAPPING_FILE, "r", encoding="utf-8-sig", newline="") as f:
    mapping_rows = list(csv.DictReader(f))


def canonical_skill(value):
    value = clean(value).lower()
    aliases = {
        "data models": "data modeling",
        "data model": "data modeling",
        "statistical analysis": "statistics",
    }
    return aliases.get(value, value)


missing_canonical = {canonical_skill(s) for s in missing_skills}
course_skills = {}
for row in mapping_rows:
    cid = clean(row.get("course_id"))
    skill = canonical_skill(row.get("normalized_skill", ""))
    if cid and skill:
        course_skills.setdefault(cid, set()).add(skill)
all_mapped_skills = set().union(*course_skills.values()) if course_skills else set()
mapped_missing_skills = missing_canonical & all_mapped_skills

# Load strict prerequisite rules so each selected course sequence can be
# checked independently of the pathway generator.
with open(DEPENDENCY_FILE, "r", encoding="utf-8-sig", newline="") as f:
    dependency_rows = list(csv.DictReader(f))
strict_dependencies = [
    (canonical_skill(r.get("prerequisite", "")),
     canonical_skill(r.get("dependent", "")))
    for r in dependency_rows
    if clean(r.get("strength", "")).upper() == "STRICT"
]
candidate_skills = {canonical_skill(s) for s in profile.get(
    "current_skills", []) if clean(s)}


def validate_prerequisites(course_rows):
    """Return (valid, explanation); evaluate strict dependencies in course order."""
    learned = set(candidate_skills)
    for row in sorted(course_rows, key=lambda r: int(to_float(r.get("order", 0)))):
        cid = clean(row.get("course_id"))
        taught = course_skills.get(cid, set())
        for prerequisite, dependent in strict_dependencies:
            if dependent in taught and prerequisite not in learned and prerequisite not in taught:
                return False, f"{row.get('course_name', cid)} teaches '{dependent}' before prerequisite '{prerequisite}' is known or taught."
        learned.update(taught)
    return True, "All strict prerequisites checked against the candidate profile and ordered course mappings."

# ============================================================
# LOAD PATHWAYS
# ============================================================


print("\nLoading pathways...")

with open(
    PATHWAY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    pathway_rows = list(
        csv.DictReader(f)
    )


print(
    f"Pathway records: "
    f"{len(pathway_rows)}"
)


# ============================================================
# GROUP PATHWAYS
# ============================================================

pathways = {}

for row in pathway_rows:

    pathway_name = clean(
        row.get("pathway", "")
    )

    if not pathway_name:
        continue

    if pathway_name not in pathways:

        pathways[pathway_name] = []

    pathways[pathway_name].append(row)


print(
    f"Pathways found: "
    f"{len(pathways)}"
)


# ============================================================
# EVALUATE PATHWAYS
# ============================================================

results = []


for pathway_name, courses in pathways.items():

    # --------------------------------------------------------
    # Use the values already calculated by Step 18.
    # --------------------------------------------------------

    first_row = courses[0]

    total_time = to_float(
        first_row.get(
            "total_pathway_time",
            0
        )
    )

    skills_covered = int(
        to_float(
            first_row.get(
                "skills_covered",
                0
            )
        )
    )

    demand_coverage = to_float(
        first_row.get(
            "demand_coverage",
            0
        )
    )

    demand_coverage_percentage = to_float(
        first_row.get(
            "demand_coverage_percentage",
            0
        )
    )

    # --------------------------------------------------------
    # Number of missing skills
    # --------------------------------------------------------

    total_missing_skills = len(
        missing_skills
    )

    # --------------------------------------------------------
    # Skill coverage percentage
    # --------------------------------------------------------

    if total_missing_skills > 0:

        skill_coverage_percentage = (
            skills_covered
            / total_missing_skills
        ) * 100

    else:

        skill_coverage_percentage = 0

    # --------------------------------------------------------
    # Average course rating
    # --------------------------------------------------------

    ratings = []

    for row in courses:

        rating = to_float(
            row.get("rating", 0)
        )

        if rating > 0:

            ratings.append(rating)

    if ratings:

        average_rating = (
            sum(ratings)
            / len(ratings)
        )

    else:

        average_rating = 0

    # --------------------------------------------------------
    # Time feasibility
    # --------------------------------------------------------

    time_feasible = (
        total_time <= TIME_BUDGET
    )

    # --------------------------------------------------------
    # Course count
    # --------------------------------------------------------

    course_count = len(courses)

    # --------------------------------------------------------
    # Course availability (computed from actual mapping data)
    # --------------------------------------------------------

    if total_missing_skills > 0:
        course_availability = (
            len(mapped_missing_skills) / len(missing_canonical)
        ) * 100
    else:
        course_availability = 0.0

    # --------------------------------------------------------
    # Independently validate prerequisites for this pathway
    # --------------------------------------------------------

    prerequisites_valid, prerequisite_note = validate_prerequisites(courses)

    # --------------------------------------------------------
    # Quality score
    #
    # This is an evaluation indicator, NOT ML accuracy.
    # --------------------------------------------------------

    coverage_score = (
        skill_coverage_percentage / 100
    )

    demand_score = min(
        demand_coverage_percentage / 100,
        1
    )

    rating_score = (
        average_rating / 5
        if average_rating > 0
        else 0
    )

    prerequisite_score = (
        1
        if prerequisites_valid
        else 0
    )

    feasibility_score = (
        1
        if time_feasible
        else 0
    )

    quality_score = (

        0.35 * coverage_score

        + 0.25 * demand_score

        + 0.15 * rating_score

        + 0.15 * prerequisite_score

        + 0.10 * feasibility_score

    ) * 100

    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    results.append({

        "pathway":
            pathway_name,

        "total_time_hours":
            round(
                total_time,
                2
            ),

        "skills_covered":
            skills_covered,

        "total_missing_skills":
            total_missing_skills,

        "skill_coverage_percentage":
            round(
                skill_coverage_percentage,
                2
            ),

        "demand_coverage":
            round(
                demand_coverage,
                2
            ),

        "demand_coverage_percentage":
            round(
                demand_coverage_percentage,
                2
            ),

        "average_course_rating":
            round(
                average_rating,
                2
            ),

        "time_budget_hours":
            TIME_BUDGET,

        "time_feasible":
            "Yes"
            if time_feasible
            else "No",

        "prerequisites_valid":
            "Yes"
            if prerequisites_valid
            else "No",

        "course_count":
            course_count,

        "course_availability_percentage":
            round(
                course_availability,
                2
            ),

        "quality_score":
            round(
                quality_score,
                2
            ),

        "prerequisite_check_notes": prerequisite_note,

        "catalogue_mapped_missing_skills": len(mapped_missing_skills)
    })


# ============================================================
# SAVE
# ============================================================

fieldnames = [

    "pathway",

    "total_time_hours",

    "skills_covered",

    "total_missing_skills",

    "skill_coverage_percentage",

    "demand_coverage",

    "demand_coverage_percentage",

    "average_course_rating",

    "time_budget_hours",

    "time_feasible",

    "prerequisites_valid",

    "course_count",

    "course_availability_percentage",

    "quality_score",
    "prerequisite_check_notes",
    "catalogue_mapped_missing_skills"
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
print("STEP 19 COMPLETE")
print("=" * 40)


for result in results:

    print()

    print(
        result["pathway"].upper()
    )

    print("-" * 40)

    print(
        f"Total time: "
        f"{result['total_time_hours']} hours"
    )

    print(
        f"Skills covered: "
        f"{result['skills_covered']}/"
        f"{result['total_missing_skills']}"
    )

    print(
        f"Skill coverage: "
        f"{result['skill_coverage_percentage']}%"
    )

    print(
        f"Demand coverage: "
        f"{result['demand_coverage_percentage']}%"
    )

    print(
        f"Average course rating: "
        f"{result['average_course_rating']}"
    )

    print(
        f"Time feasible: "
        f"{result['time_feasible']}"
    )

    print(
        f"Prerequisites valid: "
        f"{result['prerequisites_valid']}"
    )

    print(
        f"Course availability: "
        f"{result['course_availability_percentage']}%"
    )

    print(
        f"Quality score: "
        f"{result['quality_score']}"
    )


print()
print("Saved:")
print(OUTPUT_FILE)
