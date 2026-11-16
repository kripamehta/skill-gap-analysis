import csv
import re

INPUT_FILE = "data/processed/job_skills.csv"
OUTPUT_FILE = "data/processed/clean_job_skills.csv"


def clean_text(skill):
    """
    Basic text cleanup.
    """

    skill = skill.strip()

    # Remove surrounding quotation marks
    skill = skill.strip('"').strip("'")

    # Remove bullets at the beginning
    skill = re.sub(r"^[*•\-]+\s*", "", skill)

    # Normalize whitespace
    skill = re.sub(r"\s+", " ", skill)

    return skill.strip()


def is_noise(skill):
    """
    Detect obvious non-skill phrases.
    We keep this conservative so legitimate technical
    skills are not accidentally removed.
    """

    text = skill.lower().strip()

    # --------------------------------------------------
    # Salary / compensation
    # --------------------------------------------------

    if "$" in skill:
        return True

    if re.search(r"\b\d+\s*(k|usd)\b", text):
        return True

    if "salary" in text:
        return True

    if "hourly pay" in text:
        return True

    if "per hour" in text:
        return True

    if "hourly rate" in text:
        return True

    if "base pay" in text:
        return True

    # --------------------------------------------------
    # Experience requirements
    # --------------------------------------------------

    if re.search(
        r"\+?\d+\+?\s*years?\s*(of)?\s*(professional\s*)?"
        r"(experience|exp)\b",
        text
    ):
        return True

    if re.search(
        r"\+?\d+\+?\s*years?['’]?\s*(experience|exp)\b",
        text
    ):
        return True

    if re.search(
        r"\b\d+\+?\s*years?\s+in\s+",
        text
    ):
        return True

    if "years of experience" in text:
        return True

    if "years' experience" in text:
        return True

    if "years’ experience" in text:
        return True

    # --------------------------------------------------
    # Employment / eligibility statements
    # --------------------------------------------------

    noise_phrases = [
        "ability to work",
        "authorized to work",
        "authorization to work",
        "work authorization",
        "employee network",
        "equal opportunity",
        "background check",
        "drug test",
        "employment eligibility",
        "full-time employment",
        "part-time employment",
        "valid driver's license",
        "valid driver license",
        "must be willing to",
        "willingness to relocate",
        "ability to relocate",
        "work location",
        "job location",
    ]

    for phrase in noise_phrases:
        if phrase in text:
            return True

    # --------------------------------------------------
    # Obvious job-description sentences
    # --------------------------------------------------

    if len(text.split()) > 15:
        return True

    return False


cleaned_skills = set()

original_count = 0
removed_count = 0


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        skill = row["skill"].strip()

        if not skill:
            continue

        original_count += 1

        skill = clean_text(skill)

        if not skill:
            continue

        if is_noise(skill):
            removed_count += 1
            continue

        cleaned_skills.add(skill)


# --------------------------------------------------
# Save cleaned skills
# --------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow(["skill"])

    for skill in sorted(cleaned_skills):
        writer.writerow([skill])


# --------------------------------------------------
# Print results
# --------------------------------------------------

print("=" * 60)
print("JOB SKILL CLEANING COMPLETE")
print("=" * 60)

print(f"Input skill records: {original_count}")
print(f"Removed obvious noise: {removed_count}")
print(f"Unique cleaned skills: {len(cleaned_skills)}")

print(f"\nSaved to: {OUTPUT_FILE}")

print("\nFirst 100 cleaned skills:\n")

for skill in sorted(cleaned_skills)[:100]:
    print(skill)
