import csv
from pathlib import Path

file = Path("data/raw/job_skills.csv")

with open(
    file,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as f:

    reader = csv.DictReader(f)

    print("=" * 60)
    print("JOB SKILLS DATASET")
    print("=" * 60)

    print("\nColumns:")
    print(reader.fieldnames)

    print("\nFirst 5 rows:")

    for i, row in enumerate(reader):

        print("\nROW", i + 1)

        for column, value in row.items():
            print(f"{column}: {str(value)[:300]}")

        if i == 4:
            break
