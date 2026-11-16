"""Run every career at several budgets and report problems.

Usage (from the project root):  python -m backend.test_all_careers
"""
import time

from backend.recommendation_engine import generate_dynamic_recommendations

CAREERS = [
    "AI Engineer", "Backend Developer", "Cloud Engineer", "Cybersecurity Analyst",
    "Data Analyst", "Data Engineer", "Data Scientist", "Database Administrator",
    "DevOps Engineer", "Frontend Developer", "Full Stack Developer",
    "Machine Learning Engineer", "Mobile App Developer", "Network Engineer",
    "QA / Software Test Engineer", "Software Developer",
]
BUDGETS = [20, 80, 300]
SKILLS = ["Git"]

problems = []
print(f"{'career':30}{'gaps':>5}  coverage % at " +
      " / ".join(f"{b}h" for b in BUDGETS) + "   seconds")
for career in CAREERS:
    coverage, seconds, gaps = [], 0.0, 0
    for hours in BUDGETS:
        start = time.time()
        try:
            result = generate_dynamic_recommendations(career, SKILLS, hours)
        except Exception as error:
            problems.append(f"{career} @ {hours}h: {error}")
            coverage.append("ERR")
            continue
        seconds += time.time() - start
        gaps = len(result["skill_gaps"])
        evaluations = result["evaluations"]
        if not result["pathways"]:
            problems.append(f"{career} @ {hours}h: no pathways")
        for name, ev in evaluations.items():
            if not ev["strict_prerequisites_valid"]:
                problems.append(
                    f"{career} @ {hours}h {name}: prerequisite violation")
            if not ev["time_feasible"]:
                problems.append(f"{career} @ {hours}h {name}: over budget")
        coverage.append(max((e["skill_coverage_percentage"]
                        for e in evaluations.values()), default=0))
    print(f"{career:30}{gaps:>5}  " +
          " / ".join(f"{c:>6}" for c in coverage) + f"   {seconds:.1f}")

print("\nPROBLEMS:", problems if problems else "none")
