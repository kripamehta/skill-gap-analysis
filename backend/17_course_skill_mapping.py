import csv
import json
import re
from pathlib import Path

# Safe replacement for Step 17.
# Keeps the existing output columns expected by Step 18.
# It does not modify source files or other pipeline steps.

BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_GAP_FILE = BASE_DIR / "data/processed/skill_gap.csv"
COURSE_FILE = BASE_DIR / "data/raw/courses.csv"
OUTPUT_FILE = BASE_DIR / "data/processed/course_skill_mapping.csv"


def normalize_skill(skill):
    value = re.sub(r"\s+", " ", (skill or "").strip().lower())
    aliases = {
        "data modeling": "data models",
        "data model": "data models",
        "data models": "data models",
        "data visualisation": "data visualization",
        "statistical analysis": "statistics",
        "statistical modeling": "statistics",
        "statistical modelling": "statistics",
        "r programming": "r",
        "r programming language": "r",
        "etl": "etl pipeline development",
        "etl pipeline development": "etl pipeline development",
        "rest api": "rest api design",
        "rest apis": "rest api design",
        "restful api": "rest api design",
        "restful apis": "rest api design",
        "rest api design": "rest api design",
        "javascript programming": "javascript",
        "js": "javascript",
        "react.js": "react",
        "reactjs": "react",
        "nodejs": "node.js",
        "node js": "node.js",
        "k8s": "kubernetes",
        "amazon web services": "aws",
        "google cloud platform": "gcp",
        "google cloud": "gcp",
        "microsoft power bi": "power bi",
        "data analytics": "data analysis",
        "data analytics skills": "data analysis",
    }
    return aliases.get(value, value)


def normalize_occupation(value):
    value = re.sub(r"\s+", " ", (value or "").strip().lower())
    aliases = {
        "qa engineer": "qa / software test engineer",
        "quality assurance engineer": "qa / software test engineer",
        "software test engineer": "qa / software test engineer",
        "qa tester": "qa / software test engineer",
        "database admin": "database administrator",
        "dba": "database administrator",
        "dev ops engineer": "devops engineer",
        "cyber security analyst": "cybersecurity analyst",
        "front-end developer": "frontend developer",
        "front end developer": "frontend developer",
        "back-end developer": "backend developer",
        "back end developer": "backend developer",
        "full-stack developer": "full stack developer",
    }
    return aliases.get(value, value)


def parse_relevant_occupations(raw):
    # Catalogue convention: semicolon-separated occupation labels.
    return {
        normalize_occupation(item)
        for item in (raw or "").split(";")
        if item.strip()
    }


def parse_optional_rating(raw, course_id):
    value = (raw or "").strip()
    if not value:
        return 0.0  # Unknown rating; 0 is retained for Step 18 compatibility.
    rating = float(value)
    if not 0 <= rating <= 5:
        raise ValueError(
            f"Rating for {course_id} must be between 0 and 5; got {rating}")
    return rating


print("Loading candidate skill gaps...")
skill_requirements = {}
target_occupations = set()
with SKILL_GAP_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    required = {"gap_status", "skill",
                "demand_percentage", "priority", "occupation"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(
            f"skill_gap.csv is missing required columns: {sorted(missing)}")
    for row in reader:
        occupation = row.get("occupation", "").strip()
        if occupation:
            target_occupations.add(normalize_occupation(occupation))
        if row.get("gap_status", "").strip().lower() != "skill gap":
            continue
        original_skill = row.get("skill", "").strip()
        normalized = normalize_skill(original_skill)
        if not normalized:
            continue
        demand = float(row.get("demand_percentage", 0) or 0)
        # Preserve one record per normalized skill; keep the strongest demand.
        old = skill_requirements.get(normalized)
        if old is None or demand > old["demand_percentage"]:
            skill_requirements[normalized] = {
                "original_skill": original_skill,
                "demand_percentage": demand,
                "priority": row.get("priority", "").strip(),
            }

if len(target_occupations) != 1:
    raise ValueError(
        "Expected skill_gap.csv to contain exactly one target occupation; "
        f"found {sorted(target_occupations)}. Run Step 15 for one candidate profile first."
    )
TARGET_OCCUPATION = next(iter(target_occupations))
print("Target occupation:", TARGET_OCCUPATION)
print("Missing skills:", len(skill_requirements))

print("\nLoading course catalogue...")
courses = []
seen_ids = set()
skipped_missing_duration = []
skipped_wrong_role = []
unknown_role_metadata = []
with COURSE_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    required = {"course_id", "course_name", "provider",
                "skills", "duration_hours", "level", "rating", "url"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(
            f"courses.csv is missing required columns: {sorted(missing)}")
    has_role_column = "relevant_occupations" in (reader.fieldnames or [])

    for row in reader:
        course_id = (row.get("course_id") or "").strip()
        if not course_id:
            continue
        if course_id in seen_ids:
            raise ValueError(f"Duplicate course_id in catalogue: {course_id}")
        seen_ids.add(course_id)

        duration_raw = (row.get("duration_hours") or "").strip()
        if not duration_raw:
            skipped_missing_duration.append(course_id)
            continue
        duration = float(duration_raw)
        if duration <= 0:
            skipped_missing_duration.append(course_id)
            continue

        if has_role_column:
            raw_roles = (row.get("relevant_occupations") or "").strip()
            if raw_roles:
                roles = parse_relevant_occupations(raw_roles)
                if TARGET_OCCUPATION not in roles:
                    skipped_wrong_role.append(course_id)
                    continue
            else:
                # Blank role metadata means role-unspecified/general course;
                # keep it for compatibility but flag it for manual review.
                unknown_role_metadata.append(course_id)
        else:
            unknown_role_metadata.append(course_id)

        course_skills = {
            normalize_skill(skill)
            for skill in (row.get("skills") or "").split(",")
            if normalize_skill(skill)
        }
        if not course_skills:
            continue

        courses.append({
            "course_id": course_id,
            "course_name": (row.get("course_name") or "").strip(),
            "provider": (row.get("provider") or "").strip(),
            "skills": course_skills,
            "duration_hours": duration,
            "level": (row.get("level") or "").strip(),
            "rating": parse_optional_rating(row.get("rating"), course_id),
            "url": (row.get("url") or "").strip(),
        })

print("Courses eligible after duration and occupation checks:", len(courses))
if skipped_missing_duration:
    print("Skipped courses with missing/non-positive duration:",
          ", ".join(skipped_missing_duration))
if skipped_wrong_role:
    print("Skipped courses not tagged for this occupation:",
          ", ".join(skipped_wrong_role))
if unknown_role_metadata:
    print("Review courses with blank/missing occupation metadata:",
          ", ".join(unknown_role_metadata))

mappings = []
for course in courses:
    for missing_skill, requirement in skill_requirements.items():
        if missing_skill not in course["skills"]:
            continue
        mappings.append({
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "provider": course["provider"],
            "matched_skill": requirement["original_skill"],
            "normalized_skill": missing_skill,
            "skill_demand": requirement["demand_percentage"],
            "skill_priority": requirement["priority"],
            "course_duration_hours": course["duration_hours"],
            "course_level": course["level"],
            "rating": course["rating"],
            "url": course["url"],
        })

# Stable de-duplication by course and normalized skill.
unique = {}
for item in mappings:
    unique[(item["course_id"], item["normalized_skill"])] = item
mappings = list(unique.values())

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
fields = [
    "course_id", "course_name", "provider", "matched_skill",
    "normalized_skill", "skill_demand", "skill_priority",
    "course_duration_hours", "course_level", "rating", "url"
]
with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(mappings)

mapped_skills = {item["normalized_skill"] for item in mappings}
unmapped = [info["original_skill"]
            for key, info in skill_requirements.items() if key not in mapped_skills]
print("\nSTEP 17 COMPLETE")
print("Target occupation:", TARGET_OCCUPATION)
print("Missing skills:", len(skill_requirements))
print("Skills with at least one eligible course:", len(mapped_skills))
print("Skills without an eligible course:", len(unmapped))
print("Course-skill mappings:", len(mappings))
if unmapped:
    print("Unmapped skills:", ", ".join(unmapped))
print("Saved:", OUTPUT_FILE)
