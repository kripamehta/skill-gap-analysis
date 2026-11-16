"""Validate the semantic skill-matching threshold and human agreement.

Usage (from the project root):
    python -m backend.evaluate_mapping data/evaluation/mapping_labels.csv

CSV columns: raw_skill,matched_skill,similarity,correct          (correct = 1 or 0, your judgement)
Optional columns: rater1,rater2 (1/0 each) to compute Cohen's kappa between two people.
"""
import csv
import sys


def kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    p1 = sum(a for a, _ in pairs) / n
    p2 = sum(b for _, b in pairs) / n
    expected = p1 * p2 + (1 - p1) * (1 - p2)
    return (observed - expected) / (1 - expected) if expected != 1 else 1.0


def main(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"{len(rows)} labelled pairs\n")
    print("threshold | pairs accepted | precision of accepted | share of all correct matches kept")
    total_correct = sum(int(r["correct"]) for r in rows) or 1
    for threshold in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
        accepted = [r for r in rows if float(r["similarity"]) >= threshold]
        correct = sum(int(r["correct"]) for r in accepted)
        precision = correct / len(accepted) * 100 if accepted else 0.0
        print(f"{threshold:9} | {len(accepted):14} | {precision:20.1f}% | {correct / total_correct * 100:.1f}%")
    if rows and "rater1" in rows[0] and "rater2" in rows[0]:
        pairs = [(int(r["rater1"]), int(r["rater2"])) for r in rows if r["rater1"] != "" and r["rater2"] != ""]
        agreement = sum(a == b for a, b in pairs) / len(pairs) * 100
        print(f"\nHuman agreement: {agreement:.1f}% raw, Cohen's kappa {kappa(pairs):.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
