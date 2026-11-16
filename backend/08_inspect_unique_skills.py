import csv

INPUT_FILE = "data/processed/job_skills.csv"

skills = set()

with open(INPUT_FILE, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        skill = row["skill"].strip()

        if skill:
            skills.add(skill)

print("=" * 60)
print("UNIQUE JOB SKILLS")
print("=" * 60)

print(f"Unique skills: {len(skills)}")

print("\nFirst 100 skills:\n")

for skill in sorted(skills)[:100]:
    print(skill)
