import csv
import json
from itertools import combinations
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SKILL_GAP_FILE = (
    BASE_DIR / "data/processed/skill_gap.csv"
)

DEPENDENCY_FILE = (
    BASE_DIR / "data/processed/skill_gap_dependencies.csv"
)

MAPPING_FILE = (
    BASE_DIR / "data/processed/course_skill_mapping.csv"
)

PROFILE_FILE = (
    BASE_DIR / "data/candidate_profile.json"
)

OUTPUT_FILE = (
    BASE_DIR / "data/processed/learning_pathways.csv"
)


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

TIME_BUDGET = float(
    profile["time_budget_hours"]
)

candidate_skills = {
    skill.strip().lower()
    for skill in profile["current_skills"]
    if skill.strip()
}


print(
    "Time budget:",
    TIME_BUDGET,
    "hours"
)


# ============================================================
# LOAD SKILL GAP
# ============================================================

print()
print("Loading skill gap...")

missing_skills = {}

with open(
    SKILL_GAP_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        if row["gap_status"].strip() != "Skill Gap":
            continue

        skill = row["skill"].strip()

        if not skill:
            continue

        missing_skills[skill.lower()] = {
            "skill": skill,
            "demand": float(
                row["demand_percentage"]
            ),
            "priority": row["priority"].strip()
        }


print(
    "Missing skills:",
    len(missing_skills)
)


# ============================================================
# LOAD PREREQUISITES
# ============================================================

print()
print("Loading prerequisite graph...")

dependencies = []

with open(
    DEPENDENCY_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        dependencies.append(
            {
                "prerequisite": (
                    row["prerequisite"]
                    .strip()
                    .lower()
                ),
                "dependent": (
                    row["dependent"]
                    .strip()
                    .lower()
                ),
                "strength": (
                    row["strength"]
                    .strip()
                    .upper()
                ),
                "rationale": (
                    row["rationale"]
                    .strip()
                )
            }
        )


print(
    "Prerequisite relationships:",
    len(dependencies)
)


# ============================================================
# LOAD COURSE MAPPINGS
# ============================================================

print()
print("Loading course-skill mappings...")

course_mappings = {}

with open(
    MAPPING_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        course_id = row["course_id"].strip()

        if course_id not in course_mappings:

            course_mappings[course_id] = {
                "course_id": course_id,
                "course_name": row["course_name"].strip(),
                "provider": row["provider"].strip(),
                "duration": float(
                    row["course_duration_hours"]
                ),
                "level": row["course_level"].strip(),
                "rating": float(row["rating"]),
                "url": row["url"].strip(),
                "skills": set()
            }

        course_mappings[course_id]["skills"].add(
            row["normalized_skill"].strip().lower()
        )


print(
    "Courses with skill mappings:",
    len(course_mappings)
)


# ============================================================
# REMOVE IRRELEVANT COURSE MAPPINGS
# ============================================================

# SQL appearing in the metadata of a Node.js/MongoDB course
# is an incidental match for a Data Analyst pathway.
#
# We therefore remove only that specific incidental mapping.
# SQL itself remains fully valid.

for course in course_mappings.values():

    if "node.js" in course["course_name"].lower():

        course["skills"].discard("sql")


# ============================================================
# SELECT RELEVANT COURSES
# ============================================================

relevant_courses = []

for course in course_mappings.values():

    relevant_skills = (
        course["skills"]
        & set(missing_skills.keys())
    )

    if not relevant_skills:
        continue

    course["relevant_skills"] = relevant_skills

    relevant_courses.append(course)


print(
    "Relevant courses after filtering:",
    len(relevant_courses)
)


# ============================================================
# PREREQUISITE VALIDATION
# ============================================================

def check_prerequisites(selected_courses):
    """
    Validate STRICT prerequisite relationships.

    A prerequisite is satisfied when:

    1. Candidate already knows it.
    2. An earlier selected course teaches it.
    3. The same course teaches both prerequisite and
       dependent skill.

    Course order is determined before validation.
    """

    # --------------------------------------------------------
    # Start with candidate's existing skills.
    # --------------------------------------------------------

    learned = set(candidate_skills)

    violations = []

    # --------------------------------------------------------
    # We order courses so that a course teaching prerequisites
    # comes before the dependent course.
    #
    # For the current small course catalogue, repeatedly move
    # courses that satisfy prerequisites earlier.
    # --------------------------------------------------------

    remaining = list(selected_courses)
    ordered = []

    while remaining:

        progress = False

        for course in list(remaining):

            can_start = True

            for dependency in dependencies:

                if dependency["strength"] != "STRICT":
                    continue

                prerequisite = dependency["prerequisite"]
                dependent = dependency["dependent"]

                if dependent not in course["skills"]:
                    continue

                # Already known.
                if prerequisite in learned:
                    continue

                # Same course teaches prerequisite.
                if prerequisite in course["skills"]:
                    continue

                # Another selected course must teach it.
                teaches_prerequisite = any(
                    prerequisite in other["skills"]
                    for other in remaining
                    if other["course_id"]
                    != course["course_id"]
                )

                if teaches_prerequisite:
                    can_start = False
                    break

                # No selected course teaches it.
                can_start = False
                break

            if can_start:

                ordered.append(course)

                learned.update(
                    course["skills"]
                )

                remaining.remove(course)

                progress = True

                break

        if not progress:

            # Remaining courses have unresolved strict
            # prerequisites.
            for course in remaining:

                for dependency in dependencies:

                    if dependency["strength"] != "STRICT":
                        continue

                    prerequisite = dependency["prerequisite"]
                    dependent = dependency["dependent"]

                    if dependent not in course["skills"]:
                        continue

                    if prerequisite in learned:
                        continue

                    if prerequisite in course["skills"]:
                        continue

                    violations.append(
                        {
                            "prerequisite": prerequisite,
                            "dependent": dependent,
                            "course": course["course_name"]
                        }
                    )

            return None, violations

    return ordered, violations


# ============================================================
# GENERATE FEASIBLE COMBINATIONS
# ============================================================

print()
print("Generating feasible course combinations...")

feasible = []

for size in range(
    1,
    min(4, len(relevant_courses)) + 1
):

    for combination in combinations(
        relevant_courses,
        size
    ):

        total_time = sum(
            course["duration"]
            for course in combination
        )

        if total_time > TIME_BUDGET:
            continue

        ordered, violations = (
            check_prerequisites(
                combination
            )
        )

        if ordered is None:
            continue

        covered_skills = set()

        for course in ordered:

            covered_skills.update(
                course["relevant_skills"]
            )

        if not covered_skills:
            continue

        demand_coverage = sum(
            missing_skills[skill]["demand"]
            for skill in covered_skills
        )

        total_market_demand = sum(
            item["demand"]
            for item in missing_skills.values()
        )

        coverage_percentage = (
            demand_coverage
            / total_market_demand
            * 100
        )

        average_rating = (
            sum(
                course["rating"]
                for course in ordered
            )
            / len(ordered)
        )

        feasible.append(
            {
                "courses": ordered,
                "total_time": total_time,
                "covered_skills": covered_skills,
                "demand_coverage": demand_coverage,
                "coverage_percentage": (
                    coverage_percentage
                ),
                "average_rating": average_rating
            }
        )


print(
    "Feasible course combinations:",
    len(feasible)
)


if not feasible:

    print()
    print(
        "ERROR: No feasible pathway found."
    )

    raise SystemExit


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def fastest_score(pathway):

    if pathway["total_time"] == 0:
        return 0

    return (
        pathway["demand_coverage"]
        /
        pathway["total_time"]
    )


def comprehensive_score(pathway):

    return (
        pathway["demand_coverage"],
        len(pathway["covered_skills"]),
        pathway["average_rating"],
        -pathway["total_time"]
    )


def balanced_score(pathway):

    return (
        pathway["demand_coverage"] * 0.60
        +
        len(pathway["covered_skills"]) * 8
        +
        pathway["average_rating"] * 5
        -
        pathway["total_time"] * 0.25
    )


# ============================================================
# SELECT FASTEST
# ============================================================

fastest = max(
    feasible,
    key=fastest_score
)


# ============================================================
# SELECT COMPREHENSIVE
# ============================================================

comprehensive = max(
    feasible,
    key=comprehensive_score
)


# ============================================================
# SELECT BALANCED
# ============================================================

# Prefer a pathway that is different from the comprehensive
# pathway when another good feasible option exists.

different_from_comprehensive = [
    pathway
    for pathway in feasible
    if {
        course["course_id"]
        for course in pathway["courses"]
    }
    != {
        course["course_id"]
        for course in comprehensive["courses"]
    }
]

if different_from_comprehensive:

    balanced = max(
        different_from_comprehensive,
        key=balanced_score
    )

else:

    balanced = comprehensive


# ============================================================
# PATHWAY RESULTS
# ============================================================

pathways = {
    "FASTEST": fastest,
    "COMPREHENSIVE": comprehensive,
    "BALANCED": balanced
}


# ============================================================
# SAVE OUTPUT
# ============================================================

output_rows = []

for pathway_name, pathway in pathways.items():

    for order, course in enumerate(
        pathway["courses"],
        start=1
    ):

        covers = sorted(
            course["relevant_skills"]
            & pathway["covered_skills"]
        )

        output_rows.append(
            {
                "pathway": pathway_name,
                "order": order,
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "provider": course["provider"],
                "duration_hours": course["duration"],
                "rating": course["rating"],
                "covers": ", ".join(covers),
                "total_pathway_time": (
                    pathway["total_time"]
                ),
                "skills_covered": len(
                    pathway["covered_skills"]
                ),
                "demand_coverage": (
                    pathway["demand_coverage"]
                ),
                "demand_coverage_percentage": (
                    pathway["coverage_percentage"]
                ),
                "url": course["url"]
            }
        )


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = [
        "pathway",
        "order",
        "course_id",
        "course_name",
        "provider",
        "duration_hours",
        "rating",
        "covers",
        "total_pathway_time",
        "skills_covered",
        "demand_coverage",
        "demand_coverage_percentage",
        "url"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(output_rows)


# ============================================================
# DISPLAY
# ============================================================

print()
print("========================================")
print("STEP 18 COMPLETE")
print("========================================")

print(
    "Time budget:",
    TIME_BUDGET,
    "hours"
)

for pathway_name, pathway in pathways.items():

    print()
    print(pathway_name)
    print("----------------------------------------")

    print(
        "Total time:",
        pathway["total_time"],
        "hours"
    )

    print(
        "Skills covered:",
        len(pathway["covered_skills"])
    )

    print(
        "Demand coverage:",
        round(
            pathway["demand_coverage"],
            2
        )
    )

    print(
        "Demand coverage percentage:",
        round(
            pathway["coverage_percentage"],
            2
        ),
        "%"
    )

    print(
        "Average course rating:",
        round(
            pathway["average_rating"],
            2
        )
    )

    print()

    for order, course in enumerate(
        pathway["courses"],
        start=1
    ):

        print(
            f"{order}. "
            f"{course['course_name']} "
            f"({course['duration']}h)"
        )

        print(
            "   Covers:",
            ", ".join(
                sorted(
                    course["relevant_skills"]
                )
            )
        )


# ============================================================
# UNAVAILABLE SKILLS
# ============================================================

mapped_skills = set()

for course in relevant_courses:

    mapped_skills.update(
        course["relevant_skills"]
    )

unavailable = [
    info["skill"]
    for skill, info in missing_skills.items()
    if skill not in mapped_skills
]


print()
print("SKILLS WITHOUT CURRENT COURSE COVERAGE")
print("----------------------------------------")

if unavailable:

    for skill in unavailable:
        print("-", skill)

else:

    print("None")


print()
print("Saved:")
print(OUTPUT_FILE)
