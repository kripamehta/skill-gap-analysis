import csv
from collections import Counter

INPUT_FILE = "data/processed/job_skills.csv"
OUTPUT_FILE = "data/processed/skill_frequency.csv"

skill_counts = Counter()

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        skill = row["skill"].strip()

        if skill:
            skill_counts[skill] += 1


# Sort from most frequent to least frequent
sorted_skills = sorted(
    skill_counts.items(),
    key=lambda x: x[1],
    reverse=True
)


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "skill",
        "frequency"
    ])

    for skill, frequency in sorted_skills:
        writer.writerow([
            skill,
            frequency
        ])


print("=" * 60)
print("SKILL FREQUENCY CALCULATION")
print("=" * 60)

print(f"Unique skills: {len(sorted_skills)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nTop 50 skills:\n")

for skill, frequency in sorted_skills[:50]:

    print(
        f"{skill} -> {frequency}"
    )
