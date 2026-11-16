import csv
import re
from collections import defaultdict

JOB_SKILLS_FILE = "data/processed/clean_job_skills.csv"
ESCO_FILE = "data/processed/esco_skills.csv"

OUTPUT_FILE = "data/processed/skill_normalization_exact.csv"


def normalize_text(text):
    """
    Convert text into a consistent form for matching.
    """

    text = text.lower().strip()

    # Normalize different apostrophe characters
    text = text.replace("’", "'")

    # Replace punctuation with spaces
    text = re.sub(r"[^a-z0-9+#.\- ]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------
# 1. Load ESCO skills
# ---------------------------------------------------------

esco_skills = []

exact_map = {}

with open(
    ESCO_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        skill_id = row["skill_id"].strip()
        preferred_label = row["preferred_label"].strip()
        alternative_labels = row["alternative_labels"].strip()

        if not preferred_label:
            continue

        esco_skills.append({
            "skill_id": skill_id,
            "preferred_label": preferred_label
        })

        # Preferred ESCO label
        normalized_label = normalize_text(preferred_label)

        if normalized_label:
            exact_map[normalized_label] = {
                "skill_id": skill_id,
                "preferred_label": preferred_label
            }

        # ESCO alternative labels
        if alternative_labels:

            alternatives = alternative_labels.split("|")

            for alternative in alternatives:

                alternative = alternative.strip()

                if not alternative:
                    continue

                normalized_alternative = normalize_text(
                    alternative
                )

                if normalized_alternative:
                    exact_map[normalized_alternative] = {
                        "skill_id": skill_id,
                        "preferred_label": preferred_label
                    }


print("=" * 60)
print("ESCO SKILL DICTIONARY")
print("=" * 60)

print(f"ESCO skills loaded: {len(esco_skills)}")
print(f"Exact/alternative labels: {len(exact_map)}")


# ---------------------------------------------------------
# 2. Read cleaned job skills
# ---------------------------------------------------------

results = []

exact_matches = 0
unmatched = 0

with open(
    JOB_SKILLS_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        skill = row["skill"].strip()

        if not skill:
            continue

        normalized = normalize_text(skill)

        match = exact_map.get(normalized)

        if match:

            results.append({
                "job_skill": skill,
                "normalized_skill": match["preferred_label"],
                "esco_skill_id": match["skill_id"],
                "method": "exact"
            })

            exact_matches += 1

        else:

            results.append({
                "job_skill": skill,
                "normalized_skill": "",
                "esco_skill_id": "",
                "method": "unmatched"
            })

            unmatched += 1


# ---------------------------------------------------------
# 3. Remove duplicate skill expressions
# ---------------------------------------------------------

unique_results = {}

for row in results:

    key = row["job_skill"].lower()

    unique_results[key] = row


# ---------------------------------------------------------
# 4. Save
# ---------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    fieldnames = [
        "job_skill",
        "normalized_skill",
        "esco_skill_id",
        "method"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(unique_results.values())


# ---------------------------------------------------------
# 5. Statistics
# ---------------------------------------------------------

total = len(unique_results)

matched = sum(
    1
    for row in unique_results.values()
    if row["method"] == "exact"
)

unmatched_count = total - matched

print("\n" + "=" * 60)
print("EXACT NORMALIZATION COMPLETE")
print("=" * 60)

print(f"Unique job skills processed: {total}")
print(f"Exact/alias matches: {matched}")
print(f"Unmatched: {unmatched_count}")

if total > 0:

    percentage = (
        matched / total
    ) * 100

    print(
        f"Exact normalization coverage: "
        f"{percentage:.2f}%"
    )

print(f"\nSaved to: {OUTPUT_FILE}")


# ---------------------------------------------------------
# 6. Show examples
# ---------------------------------------------------------

print("\nExamples of matched skills:\n")

shown = 0

for row in unique_results.values():

    if row["method"] == "exact":

        print(
            f"{row['job_skill']} "
            f"-> "
            f"{row['normalized_skill']}"
        )

        shown += 1

        if shown >= 20:
            break


print("\nExamples of unmatched skills:\n")

shown = 0

for row in unique_results.values():

    if row["method"] == "unmatched":

        print(row["job_skill"])

        shown += 1

        if shown >= 30:
            break
