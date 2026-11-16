import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

EVALUATION_DIR = BASE_DIR / "data" / "evaluation"


def normalize_skill(skill):
    """
    Normalize skill names for comparison.
    """

    if skill is None:
        return ""

    return (
        str(skill)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def calculate_skill_coverage(
    covered_skills,
    missing_skills
):
    """
    Calculate percentage of missing skills covered
    by a pathway.
    """

    required = {
        normalize_skill(skill)
        for skill in missing_skills
        if normalize_skill(skill)
    }

    covered = {
        normalize_skill(skill)
        for skill in covered_skills
        if normalize_skill(skill)
    }

    if not required:
        return 0.0

    matched = required.intersection(covered)

    return round(
        len(matched) / len(required) * 100,
        2
    )


def calculate_demand_coverage(
    covered_skills,
    skill_demand
):
    """
    Calculate percentage of total job-demand represented
    by the skills covered by a pathway.

    skill_demand format:

        {
            "skill": demand_percentage
        }
    """

    normalized_demand = {}

    for skill, demand in skill_demand.items():
        normalized_demand[
            normalize_skill(skill)
        ] = float(demand)

    total_demand = sum(
        normalized_demand.values()
    )

    if total_demand == 0:
        return 0.0

    covered_demand = sum(
        normalized_demand.get(
            normalize_skill(skill),
            0
        )
        for skill in covered_skills
    )

    return round(
        covered_demand / total_demand * 100,
        2
    )


def validate_pathway_time(
    courses,
    time_budget_hours
):
    """
    Check whether total pathway time is within
    candidate learning budget.
    """

    total_time = sum(
        float(course["duration_hours"])
        for course in courses
    )

    return {
        "total_time_hours": round(total_time, 2),
        "time_budget_hours": time_budget_hours,
        "time_remaining_hours": round(
            time_budget_hours - total_time,
            2
        ),
        "time_feasible":
            total_time <= time_budget_hours
    }


def evaluate_pathway(
    pathway_name,
    courses,
    missing_skills,
    skill_demand,
    prerequisite_validation,
    time_budget_hours
):
    """
    Evaluate one generated pathway.

    This is an evaluation report, not an ML accuracy score.
    """

    covered_skills = set()

    for course in courses:
        for skill in course.get("covers", []):
            covered_skills.add(
                normalize_skill(skill)
            )

    missing_normalized = {
        normalize_skill(skill)
        for skill in missing_skills
    }

    covered_missing = (
        covered_skills.intersection(
            missing_normalized
        )
    )

    time_result = validate_pathway_time(
        courses,
        time_budget_hours
    )

    demand_coverage = calculate_demand_coverage(
        covered_missing,
        skill_demand
    )

    skill_coverage = (
        round(
            len(covered_missing)
            / len(missing_normalized)
            * 100,
            2
        )
        if missing_normalized
        else 0.0
    )

    ratings = [
        float(course["rating"])
        for course in courses
        if course.get("rating") is not None
    ]

    average_rating = (
        round(sum(ratings) / len(ratings), 2)
        if ratings
        else 0.0
    )

    return {
        "pathway": pathway_name,

        "total_time_hours":
            time_result["total_time_hours"],

        "time_budget_hours":
            time_result["time_budget_hours"],

        "time_remaining_hours":
            time_result["time_remaining_hours"],

        "time_feasible":
            time_result["time_feasible"],

        "course_count":
            len(courses),

        "skills_covered":
            len(covered_missing),

        "total_missing_skills":
            len(missing_normalized),

        "skill_coverage_percentage":
            skill_coverage,

        "demand_coverage_percentage":
            demand_coverage,

        "covered_skills":
            sorted(covered_missing),

        "average_course_rating":
            average_rating,

        "strict_prerequisites_valid":
            prerequisite_validation["valid"],

        "prerequisite_violations":
            prerequisite_validation[
                "missing_strict_prerequisites"
            ]
    }


# ============================================================
# PRECISION / RECALL / F1
# ============================================================

def precision_recall_f1(
    predicted,
    actual
):
    """
    Calculate Precision, Recall and F1.

    predicted = skills predicted by the system
    actual    = manually verified ground-truth skills
    """

    predicted = {
        normalize_skill(skill)
        for skill in predicted
    }

    actual = {
        normalize_skill(skill)
        for skill in actual
    }

    true_positive = len(
        predicted.intersection(actual)
    )

    false_positive = len(
        predicted - actual
    )

    false_negative = len(
        actual - predicted
    )

    precision = (
        true_positive /
        (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0
    )

    recall = (
        true_positive /
        (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall)
        else 0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,

        "precision": round(
            precision * 100,
            2
        ),

        "recall": round(
            recall * 100,
            2
        ),

        "f1_score": round(
            f1 * 100,
            2
        )
    }


def evaluate_skill_ground_truth(
    ground_truth_file
):
    """
    Evaluate the system's normalized skills against
    manually annotated ground truth.

    Expected CSV:

        job_id,predicted_skill,actual_skill

    Multiple rows can belong to the same job.

    Example:

        1001,sql,sql
        1001,data analysis,data analysis
        1001,tableau,tableau
        1001,power bi,
        1002,python,python

    Empty actual_skill means the prediction is a
    false positive.

    Empty predicted_skill means the ground-truth skill
    is a false negative.
    """

    predicted = []
    actual = []

    with open(
        ground_truth_file,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            predicted_skill = normalize_skill(
                row.get("predicted_skill", "")
            )

            actual_skill = normalize_skill(
                row.get("actual_skill", "")
            )

            if predicted_skill:
                predicted.append(
                    predicted_skill
                )

            if actual_skill:
                actual.append(
                    actual_skill
                )

    return precision_recall_f1(
        predicted,
        actual
    )


# ============================================================
# COMPLETE EVALUATION
# ============================================================

def evaluate_all_pathways(
    pathways,
    missing_skills,
    skill_demand,
    prerequisite_map,
    candidate_skills,
    time_budget_hours
):
    """
    Evaluate all generated pathways.
    """

    results = {}

    available_skills = {
        normalize_skill(skill)
        for skill in candidate_skills
    }

    for pathway_name, courses in pathways.items():

        # Import here to avoid circular imports
        from recommendation_engine import (
            validate_course_combination
        )

        prerequisite_validation = (
            validate_course_combination(
                courses,
                available_skills,
                prerequisite_map
            )
        )

        results[pathway_name] = evaluate_pathway(
            pathway_name=pathway_name,
            courses=courses,
            missing_skills=missing_skills,
            skill_demand=skill_demand,
            prerequisite_validation=prerequisite_validation,
            time_budget_hours=time_budget_hours
        )

    return results
