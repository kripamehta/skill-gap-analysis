"""Regenerate frontend/demo-data.js (sample results shown when the API is offline).

Usage (from the project root):  python -m backend.build_demo_data
"""
import json
from pathlib import Path

from backend.recommendation_engine import generate_dynamic_recommendations

SAMPLES = {
    "AI Engineer": ["Python", "SQL", "Git"], "Backend Developer": ["Python", "SQL", "Git"],
    "Cloud Engineer": ["Linux", "Networking"], "Cybersecurity Analyst": ["Networking", "Linux"],
    "Data Analyst": ["Python", "Git"], "Data Engineer": ["Python", "SQL", "Git"],
    "Data Scientist": ["Python", "SQL", "Git"], "Database Administrator": ["SQL", "Linux"],
    "DevOps Engineer": ["Linux", "Git"], "Frontend Developer": ["HTML", "CSS", "Git"],
    "Full Stack Developer": ["HTML", "CSS", "Git"], "Machine Learning Engineer": ["Python", "SQL", "Git"],
    "Mobile App Developer": ["Java", "Git"], "Network Engineer": ["Networking", "Linux"],
    "QA / Software Test Engineer": ["Python", "Git"], "Software Developer": ["Python", "Git"],
}

demo = {}
for career, skills in SAMPLES.items():
    result = generate_dynamic_recommendations(career, skills, 40)
    result.pop("course_recommendations", None)
    demo[career] = result

target = Path(__file__).resolve().parent.parent / "frontend" / "demo-data.js"
target.write_text("const DEMO = " + json.dumps(demo, separators=(",", ":")) + ";\n", encoding="utf-8")
print("Wrote", target, f"({target.stat().st_size // 1024} KB)")
