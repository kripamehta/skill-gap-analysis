import csv
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

SUMMARY_FILE = RAW / "job_summary.csv"
FILTERED_FILE = PROCESSED / "filtered_jobs.csv"

OUTPUT_FILE = PROCESSED / "jobs.csv"


# ---------------------------------------------------------
# Load only the job links we actually need
# ---------------------------------------------------------

wanted_jobs = {}

with open(
    FILTERED_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        wanted_jobs[row["job_link"]] = row


print("Jobs we need:", len(wanted_jobs))


# ---------------------------------------------------------
# Stream through the huge summary file
# ---------------------------------------------------------

found = 0

with open(
    SUMMARY_FILE,
    "r",
    encoding="utf-8-sig",
    errors="replace",
    newline=""
) as summary_file:

    reader = csv.DictReader(summary_file)

    print("\nSummary columns:")
    print(reader.fieldnames)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as output_file:

        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "job_link",
                "job_title",
                "occupation",
                "company",
                "location",
                "job_summary"
            ]
        )

        writer.writeheader()

        for row in reader:

            link = row.get("job_link", "")

            if link in wanted_jobs:

                job = wanted_jobs[link]

                writer.writerow({
                    "job_link": link,
                    "job_title": job["job_title"],
                    "occupation": job["occupation"],
                    "company": job["company"],
                    "location": job["location"],
                    "job_summary": row.get(
                        "job_summary",
                        ""
                    )
                })

                found += 1

                if found % 1000 == 0:

                    print(
                        f"Found {found} matching job descriptions..."
                    )


print("\n" + "=" * 60)
print("SUMMARY EXTRACTION COMPLETE")
print("=" * 60)

print("Matching descriptions:", found)
print("Output:", OUTPUT_FILE)
