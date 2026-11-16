import csv

file = "data/processed/jobs.csv"

with open(
    file,
    "r",
    encoding="utf-8",
    errors="replace",
    newline=""
) as f:

    reader = csv.DictReader(f)

    print("COLUMNS:")
    print(reader.fieldnames)

    print("\nFIRST 5 JOBS:")

    for i, row in enumerate(reader):

        print("\nJOB", i + 1)

        print("Title:", row["job_title"])
        print("Occupation:", row["occupation"])
        print("Company:", row["company"])
        print("Location:", row["location"])

        summary = row["job_summary"]

        print(
            "Description:",
            summary[:500].replace("\n", " ")
        )

        if i == 4:
            break
