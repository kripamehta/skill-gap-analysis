from recommendation_engine import get_recommendations


result = get_recommendations()

print("\n========================================")
print("RECOMMENDATION ENGINE TEST")
print("========================================")

print(
    "\nTarget occupation:",
    result["candidate"]["target_occupation"]
)

print(
    "Current skills:",
    result["candidate"]["current_skills"]
)

print(
    "Time budget:",
    result["candidate"]["time_budget_hours"]
)

print(
    "\nNumber of skill gaps:",
    len(result["skill_gaps"])
)

print("\nSkill gaps:")

for skill in result["skill_gaps"]:
    print(
        f"- {skill['skill']} "
        f"({skill['priority']})"
    )

print("\nPathways:")

for pathway, courses in result["pathways"].items():

    print(f"\n{pathway}")

    for course in courses:
        print(
            f"- {course['course_name']} "
            f"({course['duration_hours']} hours)"
        )

print("\n========================================")
print("ENGINE TEST COMPLETE")
print("========================================")
