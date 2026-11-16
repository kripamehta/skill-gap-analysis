from __future__ import annotations

import csv
import difflib
import functools
import itertools
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
COURSES_FILE = RAW_DIR / "courses.csv"
SKILL_DEMAND_FILE = PROCESSED_DIR / "skill_demand_normalized.csv"
DEPENDENCIES_FILE = DATA_DIR / "skill_dependencies.csv"
CANDIDATE_FILE = DATA_DIR / "candidate_profile.json"
RELEVANCE_FILE = PROCESSED_DIR / "occupation_skill_relevance.csv"

# Only these columns/fields are used for course -> skill matching.
# Course name, provider, URL and description are NEVER parsed as skills.
SKILL_ALIASES = {
    "data models": "data modeling",
    "data model": "data modeling",
    "statistical analysis": "statistics",
    "statistical analyses": "statistics",
    "statistical modeling": "statistical modeling",
    "power bi": "power bi",
    "data visualization": "data visualization",
    "data analysis": "data analysis",
    "sql": "sql",
    "python": "python",
    "pandas": "pandas",
    "tableau": "tableau",
    "machine learning": "machine learning",
    "software testing": "software testing",
    "git": "git & version control",
    "version control": "git & version control",
    # course wording -> job-demand wording
    "terraform (iac": "terraform",
    "ci/cd pipelines": "ci/cd",
    "google cloud platform": "gcp",
    "cloud architecture (aws/gcp": "cloud architecture",
    "computer networking": "networking",
    "rest api design": "rest api",
    "rest api integration": "rest api",
    "bash scripting": "bash",
    "unix/linux": "linux",
}

# Display names: acronyms and special casing that str.title() gets wrong
DISPLAY_NAMES = {
    "sql": "SQL", "nosql": "NoSQL", "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD",
    "r": "R", "c": "C", "c++": "C++", "c#": "C#", "go": "Go", "nlp": "NLP",
    "iam": "IAM", "siem": "SIEM", "dns": "DNS", "dhcp": "DHCP", "bgp": "BGP",
    "ospf": "OSPF", "tcp/ip": "TCP/IP", "html": "HTML", "css": "CSS",
    "rest api": "REST API", "apis": "APIs", "mongodb": "MongoDB",
    "postgresql": "PostgreSQL", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "javascript": "JavaScript", "typescript": "TypeScript", "power bi": "Power BI",
    "node.js": "Node.js", "vue.js": "Vue.js", "git & version control": "Git",
    "scikit-learn": "Scikit-Learn", "etl pipeline development": "ETL Pipelines",
    "apache spark": "Apache Spark", "apache kafka": "Apache Kafka",
}


ENGINE_VERSION = "3"

# Things people type -> the skill name used in the data (applied to user input only)
USER_SKILL_ALIASES = {
    "node": "node.js", "nodejs": "node.js", "node js": "node.js",
    "js": "javascript", "ts": "typescript", "py": "python", "golang": "go",
    "postgres": "postgresql", "mongo": "mongodb", "k8s": "kubernetes",
    "ml": "machine learning", "network": "networking", "rest": "rest api",
    "amazon web services": "aws", "google cloud": "gcp", "powerbi": "power bi",
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
}


def display_skill(skill: Any) -> str:
    key = normalize_skill(skill)
    return DISPLAY_NAMES.get(key) or key.title()


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@functools.lru_cache(maxsize=None)
def _normalize_cached(skill: Any) -> str:
    text = clean(skill).lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,;|[](){}\"")
    return SKILL_ALIASES.get(text, text)


def normalize_skill(skill: Any) -> str:
    try:
        return _normalize_cached(skill)
    except TypeError:  # unhashable input such as a list
        return _normalize_cached(str(skill))


def parse_skill_list(value: Any) -> List[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,;|]", clean(value))
    result: List[str] = []
    seen: Set[str] = set()
    compound_skills = {
        "html & css": ["html", "css"],
        "linux & bash scripting": ["linux", "bash scripting"],
        "siem & log analysis": ["siem", "log analysis"],
        "routing & switching": ["routing", "switching"],
        "cloud architecture (aws/gcp)": ["cloud architecture", "aws", "gcp"],
    }
    for item in raw:
        raw_skill = re.sub(r"\\s+", " ", clean(item).lower()).strip()
        expanded = compound_skills.get(raw_skill, [item])
        for part in expanded:
            skill = normalize_skill(part)
            if skill and skill not in seen:
                result.append(skill)
                seen.add(skill)
    return result


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_courses() -> List[Dict[str, Any]]:
    rows = read_csv(COURSES_FILE)
    courses: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    for row in rows:
        skills = parse_skill_list(row.get("skills", ""))
        if not skills:
            continue
        # Course IDs must be unique. Repair duplicates/blanks instead of silently mixing courses up.
        course_id = clean(row.get("course_id")) or "COURSE"
        unique_id, copy = course_id, 1
        while unique_id in seen_ids:
            copy += 1
            unique_id = f"{course_id}-{copy}"
        seen_ids.add(unique_id)
        courses.append(
            {
                "course_id": unique_id,
                "course_name": clean(row.get("course_name")),
                "provider": clean(row.get("provider")),
                "skills": skills,
                "duration_hours": safe_float(row.get("duration_hours")),
                "level": clean(row.get("level")),
                "url": clean(row.get("url")),
                "rating": safe_float(row.get("rating")),
                "description": clean(row.get("description")),
                "relevant_occupations": [
                    normalize_occupation(item)
                    for item in re.split(r"[;|]", clean(row.get("relevant_occupations", "")))
                    if clean(item)
                ],
            }
        )
    return courses


def load_dependencies() -> List[Dict[str, str]]:
    rows = read_csv(DEPENDENCIES_FILE)
    deps = []
    for row in rows:
        prerequisite = normalize_skill(row.get("prerequisite_skill"))
        dependent = normalize_skill(row.get("dependent_skill"))
        strength = clean(row.get("dependency_strength")).upper()
        if prerequisite and dependent:
            deps.append(
                {
                    "prerequisite": prerequisite,
                    "dependent": dependent,
                    "strength": strength,
                    "rationale": clean(row.get("rationale")),
                }
            )
    return deps


def load_skill_demand() -> List[Dict[str, Any]]:
    rows = read_csv(SKILL_DEMAND_FILE)
    result = []
    for row in rows:
        skill = clean(row.get("skill"))
        if not skill:
            continue
        item = dict(row)
        item["skill"] = skill
        item["normalized_skill"] = normalize_skill(skill)
        item["demand_percentage"] = safe_float(row.get("demand_percentage"))
        result.append(item)
    return result


OCCUPATION_ALIASES = {
    "data analyst": "data analyst",
    "business intelligence analyst": "data analyst",
    "data scientist": "data scientist",
    "software developer": "software developer",
    "software engineer": "software developer",
    "qa engineer": "qa / software test engineer",
    "qa / software test engineer": "qa / software test engineer",
    "network engineer": "network engineer",
    "data engineer": "data engineer",
    "cybersecurity analyst": "cybersecurity analyst",
    "database administrator": "database administrator",
    "machine learning engineer": "machine learning engineer",
    "devops engineer": "devops engineer",
    "cloud / devops engineer": "devops engineer",
    "cloud engineer": "cloud engineer",
    "full stack developer": "full stack developer",
    "frontend developer": "frontend developer",
    "backend developer": "backend developer",
    "mobile app developer": "mobile app developer",
    "ai engineer": "ai engineer",
}


def normalize_occupation(value):
    key = re.sub(r"\s+", " ", clean(value).lower()).strip()
    return OCCUPATION_ALIASES.get(key, key)


def course_is_relevant(course: Dict[str, Any], target_occupation: str) -> bool:
    """Return True only when the course is explicitly mapped to this occupation."""
    target = normalize_occupation(target_occupation)
    allowed = {
        normalize_occupation(item)
        for item in course.get("relevant_occupations", [])
    }
    return target in allowed


# Market-supported skills need an occupation-specific check.
# These are manually reviewed for the current Data Analyst prototype.
MARKET_APPROVED_SKILLS = {
    "data analyst": {
        "tableau",
        "r",
        "data models",
        "data modeling",
        "statistics",
    },
}


def load_relevance_lookup(target_occupation):
    rows = read_csv(RELEVANCE_FILE)
    target = normalize_occupation(target_occupation)

    matching_rows = [
        row for row in rows
        if normalize_occupation(row.get("occupation", "")) == target
    ]

    if not matching_rows:
        raise ValueError(
            f"No Step 14.5 relevance data found for "
            f"'{target_occupation}'. Generate relevance data "
            "for this occupation before recommending skills."
        )

    lookup = {}
    for row in matching_rows:
        skill = normalize_skill(row.get("skill", ""))
        relevance = clean(row.get("relevance", "")).lower()

        if skill:
            lookup[skill] = relevance

    return lookup


def is_relevant_for_occupation(skill, relevance, target_occupation):
    """Accept explicit O*NET or market-supported labels for this occupation."""
    relevance = clean(relevance).lower()
    return relevance in {"o*net supported", "market supported"}


def actionable_skill_set(courses, dependencies):
    """
    A skill is actionable in this prototype when at least one course's
    explicit `skills` field teaches it. This uses the course-skill vocabulary
    as the learnable-skill catalogue rather than maintaining a growing
    blacklist of broad labels. Broad labels such as 'Cybersecurity' and
    'computer science' are excluded unless a course explicitly teaches them.
    """
    return {
        normalize_skill(skill)
        for course in courses
        for skill in course.get("skills", [])
        if normalize_skill(skill)
    }


def calculate_skill_gaps(
    target_occupation: str,
    current_skills: Sequence[str],
) -> List[Dict[str, Any]]:
    rows = load_skill_demand()
    target = normalize_occupation(target_occupation)
    occupation_values = {
        normalize_occupation(row.get("occupation", ""))
        for row in rows if clean(row.get("occupation", ""))
    }
    if target not in occupation_values:
        raise ValueError(
            f"Occupation '{target_occupation}' was not found "
            "in skill_demand_normalized.csv."
        )

    rows = [
        row for row in rows
        if normalize_occupation(row.get("occupation", "")) == target
    ]
    relevance_lookup = load_relevance_lookup(target_occupation)

    # Only report actionable skills with an explicit course mapping.
    courses = [
        course for course in load_courses()
        if course_is_relevant(course, target_occupation)
    ]
    actionable = actionable_skill_set(courses, load_dependencies())

    best_by_skill = {}
    for row in rows:
        skill = normalize_skill(row.get("skill", ""))
        demand = safe_float(row.get("demand_percentage", 0))
        if not skill or demand < 5.0 or skill not in actionable:
            continue

        relevance = relevance_lookup.get(skill, "")
        if not is_relevant_for_occupation(skill, relevance, target_occupation):
            continue

        if skill not in best_by_skill or demand > best_by_skill[skill]["demand_percentage"]:
            best_by_skill[skill] = {
                "skill": clean(row.get("skill")),
                "normalized_skill": skill,
                "demand_percentage": demand,
            }

    current = {normalize_skill(skill) for skill in current_skills}
    output = []
    for row in sorted(
        best_by_skill.values(),
        key=lambda item: (-item["demand_percentage"],
                          item["normalized_skill"]),
    ):
        skill = row["normalized_skill"]
        demand = row["demand_percentage"]
        priority = "High" if demand >= 15 else "Medium" if demand >= 10 else "Low"
        output.append({
            "skill": row["skill"],
            "normalized_skill": skill,
            "demand_percentage": round(demand, 2),
            "priority": priority,
            "gap_status": "Skill Present" if skill in current else "Skill Gap",
        })

    if not output:
        raise ValueError(
            f"No actionable, relevant skills passed the demand and relevance "
            f"filters for '{target_occupation}'. Check demand data and course mappings."
        )
    return output


# ============================================================
# PREREQUISITE LOGIC
# ============================================================


# How strongly COMPREHENSIVE favours the highest-demand skills (1 = proportional to demand).
DEMAND_WEIGHT_POWER = 1.0

_PREREQ_CACHE: Dict[str, Any] = {"deps": None, "map": None}


def get_prerequisite_relationships(dependencies):
    # The same dependency list is passed thousands of times per request while
    # pathways are generated, so build the map once per list.
    if _PREREQ_CACHE["deps"] is dependencies:
        return _PREREQ_CACHE["map"]
    relationships = {}

    for row in dependencies:
        prerequisite = normalize_skill(
            row.get("prerequisite", row.get("prerequisite_skill"))
        )
        dependent = normalize_skill(
            row.get("dependent", row.get("dependent_skill"))
        )
        strength = clean(
            row.get("strength", row.get("dependency_strength"))
        ).upper()

        if not prerequisite or not dependent:
            continue

        relationships.setdefault(dependent, []).append({
            "prerequisite": prerequisite,
            "strength": strength,
            "rationale": clean(row.get("rationale", ""))
        })

    _PREREQ_CACHE["deps"], _PREREQ_CACHE["map"] = dependencies, relationships
    return relationships


def get_strict_prerequisites(skill, prerequisite_map):
    skill = normalize_skill(skill)

    return {
        item["prerequisite"]
        for item in prerequisite_map.get(skill, [])
        if item["strength"] == "STRICT"
    }


def get_recommended_prerequisites(skill, prerequisite_map):
    skill = normalize_skill(skill)

    return {
        item["prerequisite"]
        for item in prerequisite_map.get(skill, [])
        if item["strength"] == "RECOMMENDED"
    }


_COURSE_PREREQ_CACHE: Dict[str, Any] = {"map": None, "items": {}}


def get_course_prerequisites(course, prerequisite_map):
    cache = _COURSE_PREREQ_CACHE
    if cache["map"] is not prerequisite_map:
        cache["map"], cache["items"] = prerequisite_map, {}
    key = tuple(course["skills"])
    if key not in cache["items"]:
        strict = set()
        recommended = set()
        for skill in key:
            skill = normalize_skill(skill)
            strict.update(get_strict_prerequisites(skill, prerequisite_map))
            recommended.update(
                get_recommended_prerequisites(skill, prerequisite_map))
        cache["items"][key] = (frozenset(strict), frozenset(recommended))
    strict, recommended = cache["items"][key]
    return set(strict), set(recommended)


def course_prerequisite_status(
    course, candidate_skills, prerequisite_map
):
    candidate_skills = {
        normalize_skill(skill) for skill in candidate_skills
    }

    strict, recommended = get_course_prerequisites(
        course, prerequisite_map
    )

    taught = {
        normalize_skill(skill) for skill in course["skills"]
    }

    strict_missing = sorted(
        skill for skill in strict
        if skill not in candidate_skills and skill not in taught
    )

    recommended_missing = sorted(
        skill for skill in recommended
        if skill not in candidate_skills and skill not in taught
    )

    return {
        "prerequisites_ready": len(strict_missing) == 0,
        "missing_strict_prerequisites": strict_missing,
        "missing_recommended_prerequisites": recommended_missing
    }


def prerequisites_ready_for_course(
    course, learned_skills, dependencies
):
    prerequisite_map = get_prerequisite_relationships(dependencies)

    return course_prerequisite_status(
        course, learned_skills, prerequisite_map
    )["prerequisites_ready"]


def prerequisite_valid_sequence(
    courses, current_skills, dependencies
):
    prerequisite_map = get_prerequisite_relationships(dependencies)
    available = {
        normalize_skill(skill) for skill in current_skills
    }
    violations = []

    for course in courses:
        status = course_prerequisite_status(
            course, available, prerequisite_map
        )

        for skill in status["missing_strict_prerequisites"]:
            violations.append({
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "missing_prerequisite": skill
            })

        # The skills from this course are available to
        # subsequent courses in the pathway.
        available.update(
            normalize_skill(skill) for skill in course["skills"]
        )

    return {
        "valid": len(violations) == 0,
        "missing_strict_prerequisites": violations
    }


def course_covers(course: Dict[str, Any], missing: Set[str]) -> Set[str]:
    # IMPORTANT: only the explicit `skills` column is used.
    return {normalize_skill(s) for s in course["skills"] if normalize_skill(s) in missing}


def order_courses(
    courses: Sequence[Dict[str, Any]],
    current_skills: Set[str],
    dependencies: List[Dict[str, str]],
) -> Optional[List[Dict[str, Any]]]:
    remaining = list(courses)
    ordered: List[Dict[str, Any]] = []
    learned = set(current_skills)

    while remaining:
        valid = [
            c for c in remaining
            if prerequisites_ready_for_course(c, learned, dependencies)
        ]
        if not valid:
            return None
        valid.sort(
            key=lambda c: (-len(c["skills"]), c["duration_hours"], -c["rating"], c["course_id"]))
        chosen = valid[0]
        ordered.append(chosen)
        learned.update(normalize_skill(s) for s in chosen["skills"])
        remaining.remove(chosen)
    return ordered


def find_courses_for_skills(
    missing_skills: Sequence[str],
    courses: Sequence[Dict[str, Any]],
    time_budget: float,
    current_skills: Sequence[str],
    dependencies: List[Dict[str, str]],
) -> List[Dict[str, Any]]:

    missing = {normalize_skill(s) for s in missing_skills}
    current = {normalize_skill(s) for s in current_skills}
    prerequisite_map = get_prerequisite_relationships(dependencies)

    recommendations = []

    for course in courses:
        duration = course["duration_hours"]

        # Exclude courses that teach no missing skills.
        covered = course_covers(course, missing)
        if not covered:
            continue

        # Exclude courses that exceed the candidate's time budget.
        if duration > time_budget:
            continue

        prerequisite_status = course_prerequisite_status(
            course, current, prerequisite_map
        )

        recommendations.append({
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "provider": course["provider"],
            "duration_hours": duration,
            "rating": course["rating"],
            "url": course["url"],
            "description": course["description"],
            "covers": sorted(covered),
            "prerequisites_ready": prerequisite_status[
                "prerequisites_ready"
            ],
            "missing_strict_prerequisites": prerequisite_status[
                "missing_strict_prerequisites"
            ],
            "missing_recommended_prerequisites": prerequisite_status[
                "missing_recommended_prerequisites"
            ],
            "within_budget": True,
        })

    recommendations.sort(
        key=lambda course: (
            not course["prerequisites_ready"],
            -len(course["covers"]),
            course["duration_hours"],
            -course["rating"],
            course["course_id"],
        )
    )

    return recommendations


def combination_metrics(
    courses: Sequence[Dict[str, Any]],
    missing: Set[str],
    demand_lookup: Dict[str, float],
    total_missing_demand: float,
) -> Dict[str, Any]:
    covered = set()
    for course in courses:
        covered.update(course["covers"])
    covered &= missing
    total_time = sum(c["duration_hours"] for c in courses)
    ratings = [c["rating"] for c in courses if c["rating"] > 0]
    demand = sum(demand_lookup.get(s, 0.0) for s in covered)
    skill_pct = (len(covered) / len(missing) * 100) if missing else 0.0
    demand_pct = (demand / total_missing_demand *
                  100) if total_missing_demand else 0.0
    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
    return {
        "total_time_hours": round(total_time, 2),
        "skills_covered": len(covered),
        "total_missing_skills": len(missing),
        "skill_coverage_percentage": round(skill_pct, 2),
        "demand_coverage_percentage": round(demand_pct, 2),
        "average_course_rating": round(avg_rating, 2),
        "course_count": len(courses),
        "covered_skills": sorted(covered),
    }


def generate_valid_combinations(
    missing_skills: Sequence[str],
    courses: Sequence[Dict[str, Any]],
    current_skills: Sequence[str],
    time_budget: float,
    dependencies: List[Dict[str, str]],
    max_courses: int = 4,
    max_candidates: int = 45,
) -> List[List[Dict[str, Any]]]:
    missing = {normalize_skill(s) for s in missing_skills}
    current = {normalize_skill(s) for s in current_skills}
    relevant = []
    for course in courses:
        if course["duration_hours"] > time_budget:
            continue
        covers = course_covers(course, missing)
        if covers:
            c = dict(course)
            c["covers"] = sorted(covers)
            relevant.append(c)

    # Remove exact duplicate course IDs defensively.
    by_id = {c["course_id"]: c for c in relevant if c["course_id"]}
    relevant = sorted(by_id.values(), key=lambda c: c["course_id"])

    # Safety valve: the number of combinations grows ~n^4, so for very large
    # candidate pools keep only the most useful courses (most gaps covered,
    # then best rated, then shortest) to keep the API responsive.
    if len(relevant) > max_candidates:
        relevant = sorted(
            sorted(
                relevant,
                key=lambda c: (-len(c["covers"]), -c["rating"],
                               c["duration_hours"], c["course_id"]),
            )[:max_candidates],
            key=lambda c: c["course_id"],
        )

    # Per-course data is computed once, so checking a combination is cheap.
    prereq_map = get_prerequisite_relationships(dependencies)
    info = {}
    for c in relevant:
        strict, _ = get_course_prerequisites(c, prereq_map)
        taught = frozenset(normalize_skill(s) for s in c["skills"])
        sort_key = (-len(c["skills"]), c["duration_hours"], -
                    c["rating"], c["course_id"])
        info[c["course_id"]] = (strict - taught, taught, sort_key)

    def order(combo):
        # Same greedy ordering as order_courses(), without recomputing sets.
        remaining, ordered, learned = list(combo), [], set(current)
        while remaining:
            best = None
            for c in remaining:
                needs, _, key = info[c["course_id"]]
                if needs <= learned and (best is None or key < best[0]):
                    best = (key, c)
            if best is None:
                return None
            ordered.append(best[1])
            learned |= info[best[1]["course_id"]][1]
            remaining.remove(best[1])
        return ordered

    combos: List[List[Dict[str, Any]]] = []
    for size in range(1, min(max_courses, len(relevant)) + 1):
        for combo in itertools.combinations(relevant, size):
            if sum(c["duration_hours"] for c in combo) > time_budget:
                continue
            ordered = order(combo)
            if ordered is not None:
                combos.append(ordered)
    return combos


def pathway_signature(courses: Sequence[Dict[str, Any]]) -> Tuple[str, ...]:
    return tuple(sorted(c["course_id"] for c in courses))


def choose_pathways(
    combinations: Sequence[List[Dict[str, Any]]],
    missing_skills: Sequence[str],
    skill_gap_rows: Sequence[Dict[str, Any]],
    time_budget: float,
) -> Dict[str, List[Dict[str, Any]]]:
    missing = {normalize_skill(s) for s in missing_skills}
    demand_lookup = {normalize_skill(r["skill"]): safe_float(
        r["demand_percentage"]) for r in skill_gap_rows}
    total_demand = sum(demand_lookup.get(s, 0.0) for s in missing)

    scored = []
    for combo in combinations:
        m = combination_metrics(combo, missing, demand_lookup, total_demand)
        scored.append((combo, m))

    if not scored:
        return {}

    # Keep pathways anchored to the occupation's top three actionable gaps.
    # This prevents unrelated lower-ranked courses from dominating a pathway
    # merely to inflate total skill coverage.
    ranked_missing = sorted(
        missing, key=lambda skill: (-demand_lookup.get(skill, 0.0), skill)
    )
    top_role_skills = set(ranked_missing[:3])
    role_scored = [
        item for item in scored
        if set(item[1]["covered_skills"]) & top_role_skills
    ]
    if role_scored:
        scored = role_scored

    # FASTEST: first prioritize the highest-demand actionable missing skill
    # covered by any feasible, prerequisite-valid combination. If that skill
    # cannot fit with strict prerequisites in the budget, move to the next one.
    feasible_skill_order = sorted(
        missing, key=lambda skill: (-demand_lookup.get(skill, 0.0), skill)
    )
    priority_skill = next(
        (
            skill for skill in feasible_skill_order
            if any(skill in set(metrics["covered_skills"]) for _, metrics in scored)
        ),
        None,
    )
    priority_scored = [
        item for item in scored
        if priority_skill is None or priority_skill in set(item[1]["covered_skills"])
    ]
    fastest_combo, fastest_m = min(
        priority_scored,
        key=lambda x: (
            x[1]["total_time_hours"],
            -x[1]["demand_coverage_percentage"],
            -x[1]["skills_covered"],
            -x[1]["average_course_rating"],
            pathway_signature(x[0]),
        ),
    )

    # Demand-weighted score emphasizes the highest-demand missing skills
    # without letting many low-demand incidental skills dominate the pathway.
    def weighted_demand_score(metrics):
        return sum(
            demand_lookup.get(skill, 0.0) ** DEMAND_WEIGHT_POWER
            for skill in metrics["covered_skills"]
        )

    # COMPREHENSIVE: maximize weighted demand first, then broad skill coverage.
    comprehensive_combo, comprehensive_m = max(
        scored,
        key=lambda x: (
            weighted_demand_score(x[1]),
            x[1]["skills_covered"],
            x[1]["demand_coverage_percentage"],
            x[1]["average_course_rating"],
            -x[1]["total_time_hours"],
            tuple(reversed(pathway_signature(x[0]))),
        ),
    )

    selected: Dict[str, List[Dict[str, Any]]] = {
        "FASTEST": fastest_combo,
        "COMPREHENSIVE": comprehensive_combo,
    }

    used = {pathway_signature(fastest_combo),
            pathway_signature(comprehensive_combo)}
    distinct = [x for x in scored if pathway_signature(x[0]) not in used]

    if distinct:
        # BALANCED: genuinely different, feasible, and a compromise between
        # coverage and time. The score rewards both demand coverage and skill
        # coverage while penalizing excessive time.
        max_weighted = max(weighted_demand_score(m) for _, m in scored) or 1.0

        def balanced_score(item):
            combo, m = item
            time_utilization = m["total_time_hours"] / max(time_budget, 1)
            weighted_pct = weighted_demand_score(m) / max_weighted * 100
            return (
                0.40 * weighted_pct
                + 0.25 * m["skill_coverage_percentage"]
                + 0.15 * (m["average_course_rating"] / 5 * 100)
                + 0.20 * (100 - time_utilization * 100),
                m["skills_covered"],
                m["demand_coverage_percentage"],
                -m["total_time_hours"],
            )

        balanced_combo, _ = max(distinct, key=balanced_score)
        selected["BALANCED"] = balanced_combo

    return selected


def evaluate_pathways(
    pathways: Dict[str, List[Dict[str, Any]]],
    missing_skills: Sequence[str],
    skill_gap_rows: Sequence[Dict[str, Any]],
    time_budget: float,
    current_skills: Sequence[str],
    dependencies: List[Dict[str, str]],
) -> Dict[str, Dict[str, Any]]:

    missing = {normalize_skill(s) for s in missing_skills}

    demand_lookup = {
        normalize_skill(r["skill"]): safe_float(r["demand_percentage"])
        for r in skill_gap_rows
    }

    total_demand = sum(demand_lookup.get(s, 0.0) for s in missing)
    current = {normalize_skill(s) for s in current_skills}

    evaluations = {}

    for name, courses in pathways.items():
        metrics = combination_metrics(
            courses, missing, demand_lookup, total_demand
        )

        prerequisite_result = prerequisite_valid_sequence(
            courses, current, dependencies
        )

        prerequisites_valid = prerequisite_result["valid"]
        time_feasible = metrics["total_time_hours"] <= time_budget

        # This is a heuristic comparison score, not ML accuracy.
        quality = (
            metrics["skill_coverage_percentage"] * 0.35
            + metrics["demand_coverage_percentage"] * 0.45
            + (metrics["average_course_rating"] / 5 * 100) * 0.10
            + (100 if prerequisites_valid else 0) * 0.10
        )

        evaluations[name] = {
            **metrics,
            "time_feasible": time_feasible,
            "strict_prerequisites_valid": prerequisites_valid,
            "prerequisite_violations": prerequisite_result[
                "missing_strict_prerequisites"
            ],
            "quality_score": round(quality, 2),
        }

    return evaluations


def build_explanations(
    pathways: Dict[str, List[Dict[str, Any]]],
    evaluations: Dict[str, Dict[str, Any]],
    target_occupation: str,
    time_budget: float,
) -> Dict[str, Dict[str, Any]]:
    explanations = {}
    for name, courses in pathways.items():
        e = evaluations[name]
        course_reasons = []
        for c in courses:
            covers = ", ".join(c["covers"])
            course_reasons.append(
                f"{c['course_name']} ({c['duration_hours']:.0f} hours) covers {covers}."
            )
        remaining = max(0.0, time_budget - e["total_time_hours"])
        if name == "FASTEST":
            reason = (
                "This pathway prioritizes the shortest feasible learning time while "
                "still covering relevant missing skills."
            )
        elif name == "COMPREHENSIVE":
            reason = (
                "This pathway maximizes useful missing-skill coverage and job-demand "
                "coverage within the available learning budget."
            )
        else:
            reason = (
                "This pathway is a distinct compromise between learning time and "
                "useful skill coverage."
            )
        explanations[name] = {
            "explanation": reason,
            "course_reason": " ".join(course_reasons),
            "courses": [c["course_name"] for c in courses],
            "skills_covered": e["covered_skills"],
            "total_time_hours": e["total_time_hours"],
            "time_budget_hours": time_budget,
            "time_remaining_hours": round(remaining, 2),
            "skill_coverage_percentage": e["skill_coverage_percentage"],
            "demand_coverage_percentage": e["demand_coverage_percentage"],
        }
    return explanations


def generate_dynamic_recommendations(
    target_occupation: str,
    current_skills: Sequence[str],
    time_budget_hours: float,
) -> Dict[str, Any]:
    time_budget = max(0.0, safe_float(time_budget_hours))
    typed_skills = [clean(s) for s in current_skills if clean(s)]
    vocab = build_skill_vocabulary()
    current_skills = [resolve_user_skill(s, vocab) for s in typed_skills]
    skills_interpreted = [
        {"typed": typed, "matched": display_skill(found)}
        for typed, found in zip(typed_skills, current_skills)
        if normalize_skill(typed) != found
    ]
    skills_unrecognized = [
        typed for typed, found in zip(typed_skills, current_skills) if found not in vocab
    ]

    skill_gap_rows = calculate_skill_gaps(target_occupation, current_skills)
    missing_rows = [
        r for r in skill_gap_rows if r["gap_status"] == "Skill Gap"]
    missing_skills = [r["skill"] for r in missing_rows]

    courses = [
        course for course in load_courses()
        if course_is_relevant(course, target_occupation)
    ]
    dependencies = load_dependencies()

    course_recommendations = find_courses_for_skills(
        missing_skills,
        courses,
        time_budget,
        current_skills,
        dependencies,
    )
    demand_lookup = {
        normalize_skill(row["skill"]): safe_float(row["demand_percentage"])
        for row in missing_rows
    }
    top_five_skills = {
        normalize_skill(row["skill"])
        for row in sorted(
            missing_rows,
            key=lambda row: (-safe_float(row["demand_percentage"]),
                             normalize_skill(row["skill"])),
        )[:5]
    }
    course_recommendations = [
        course for course in course_recommendations
        if set(course["covers"]) & top_five_skills
    ]
    course_recommendations.sort(
        key=lambda course: (
            -sum(demand_lookup.get(normalize_skill(skill), 0.0)
                 for skill in course["covers"]),
            not course["prerequisites_ready"],
            course["duration_hours"],
            -course["rating"],
        )
    )

    combinations = generate_valid_combinations(
        missing_skills,
        courses,
        current_skills,
        time_budget,
        dependencies,
        max_courses=4,
    )
    pathways = choose_pathways(
        combinations, missing_skills, skill_gap_rows, time_budget)
    evaluations = evaluate_pathways(
        pathways,
        missing_skills,
        skill_gap_rows,
        time_budget,
        current_skills,
        dependencies,
    )
    explanations = build_explanations(
        pathways, evaluations, target_occupation, time_budget)

    skill_gaps = [
        {
            "skill": display_skill(r["normalized_skill"]),
            "normalized_skill": r["normalized_skill"],
            "demand_percentage": r["demand_percentage"],
            "priority": r["priority"],
            "gap_status": r["gap_status"],
        }
        for r in skill_gap_rows
        if r["gap_status"] == "Skill Gap"
    ]

    skill_graph = build_skill_graph(
        [r["normalized_skill"] for r in missing_rows], current_skills, dependencies)
    used = {n["id"] for n in skill_graph["nodes"]}
    for course in courses:
        used.update(course["skills"])
    return {
        "engine_version": ENGINE_VERSION,
        "skills_interpreted": skills_interpreted,
        "skills_unrecognized": skills_unrecognized,
        "candidate": {
            "target_occupation": target_occupation,
            "current_skills": typed_skills,
            "time_budget_hours": time_budget,
        },
        "skill_gaps": skill_gaps,
        "skill_graph": skill_graph,
        "skill_labels": {s: display_skill(s) for s in used},
        "course_recommendations": course_recommendations,
        "pathways": pathways,
        "evaluations": evaluations,
        "explanations": explanations,
    }


def build_skill_graph(missing, current, dependencies):
    """Missing skills plus every prerequisite they depend on, with the edges between them."""
    needs: Dict[str, List[Dict[str, str]]] = {}
    for d in dependencies:
        needs.setdefault(d["dependent"], []).append(d)
    keep, stack = set(missing), list(missing)
    while stack:
        for d in needs.get(stack.pop(), []):
            if d["prerequisite"] not in keep:
                keep.add(d["prerequisite"])
                stack.append(d["prerequisite"])
    have = {normalize_skill(s) for s in current}
    edges = [
        {"from": d["prerequisite"], "to": d["dependent"],
         "strength": d["strength"], "rationale": d["rationale"]}
        for d in dependencies
        if d["prerequisite"] in keep and d["dependent"] in keep
    ]
    nodes = [
        {"id": s, "label": display_skill(s),
         "status": "have" if s in have else "gap" if s in missing else "prerequisite"}
        for s in sorted(keep)
    ]
    return {"nodes": nodes, "edges": edges}


def build_skill_vocabulary() -> Set[str]:
    """Skills we can recognise: everything a course teaches plus skills with real job demand."""
    vocab = {
        r["normalized_skill"] for r in load_skill_demand()
        if safe_float(r["demand_percentage"]) >= 5
    }
    for course in load_courses():
        vocab.update(course["skills"])
    return vocab


def resolve_user_skill(text: Any, vocab: Set[str]) -> str:
    """Map what the user typed to a known skill: exact, alias, 'x' -> 'x.js', then close spelling."""
    key = normalize_skill(text)
    if key in vocab:
        return key
    key = USER_SKILL_ALIASES.get(key, key)
    if key in vocab:
        return key
    if key + ".js" in vocab:
        return key + ".js"
    close = difflib.get_close_matches(key, sorted(vocab), n=1, cutoff=0.84)
    return close[0] if close else key


def list_known_skills() -> List[str]:
    return sorted({display_skill(s) for s in build_skill_vocabulary()}, key=str.lower)


def get_recommendations() -> Dict[str, Any]:
    with CANDIDATE_FILE.open("r", encoding="utf-8") as f:
        profile = json.load(f)
    return generate_dynamic_recommendations(
        profile["target_occupation"],
        profile.get("current_skills", []),
        profile.get("time_budget_hours", 40),
    )
