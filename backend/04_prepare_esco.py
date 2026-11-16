import csv
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

INPUT_FILE = RAW / "skills_en.csv"
OUTPUT_FILE = PROCESSED / "esco_skills.csv"


# =========================================================
# READ ESCO
# =========================================================

rows = []

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    print("ESCO columns:")
    print(reader.fieldnames)

    for row in reader:

        rows.append({
            "skill_id": row.get("conceptUri", ""),
            "skill_type": row.get("skillType", ""),
            "preferred_label": row.get(
                "preferredLabel",
                ""
            ),
            "alternative_labels": row.get(
                "altLabels",
                ""
            ),
            "description": row.get(
                "description",
                ""
            )
        })


# =========================================================
# REMOVE EMPTY SKILLS
# =========================================================

rows = [
    row
    for row in rows
    if row["preferred_label"].strip()
]


# =========================================================
# REMOVE DUPLICATES
# =========================================================

unique = {}

for row in rows:

    skill_id = row["skill_id"]

    if skill_id:
        unique[skill_id] = row


rows = list(unique.values())


# =========================================================
# SAVE
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "skill_id",
            "skill_type",
            "preferred_label",
            "alternative_labels",
            "description"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)


print("\n" + "=" * 60)
print("ESCO PROCESSING COMPLETE")
print("=" * 60)

print("Number of skills:", len(rows))
print("Saved to:", OUTPUT_FILE)

print("\nFirst 5 skills:")

for row in rows[:5]:

    print("\nSkill:", row["preferred_label"])
    print("Type:", row["skill_type"])
    print("ID:", row["skill_id"])
