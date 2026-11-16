from pathlib import Path
import csv
import os

RAW_FOLDER = Path("data/raw")

print("\n" + "=" * 70)
print("CHECKING RAW DATASETS")
print("=" * 70)

csv_files = list(RAW_FOLDER.glob("*.csv"))

if not csv_files:
    print("No CSV files found in data/raw")
    exit()

for file in csv_files:

    print("\n" + "-" * 70)
    print(f"FILE: {file.name}")

    # File size
    size_mb = os.path.getsize(file) / (1024 * 1024)
    print(f"SIZE: {size_mb:.2f} MB")

    try:
        with open(
            file,
            "r",
            encoding="utf-8-sig",
            errors="replace",
            newline=""
        ) as f:

            reader = csv.reader(f)

            # Read only the header
            header = next(reader)

            print("\nCOLUMNS:")
            for i, column in enumerate(header, start=1):
                print(f"{i}. {column}")

            # Read only ONE data row
            try:
                first_row = next(reader)

                print("\nFIRST ROW:")
                for column, value in zip(header, first_row):
                    value = value[:150]  # don't print huge text
                    print(f"{column}: {value}")

            except StopIteration:
                print("\nNo data rows found.")

    except Exception as e:
        print("\nCOULD NOT READ FILE:")
        print(type(e).__name__, "-", e)

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
