import csv
import re
from collections import Counter

CLEAN_SKILLS_FILE = "data/processed/clean_job_skills.csv"
JOB_SKILLS_FILE = "data/processed/job_skills.csv"

CATEGORIZED_FILE = "data/processed/categorized_skills.csv"
TECHNICAL_FILE = "data/processed/technical_job_skills.csv"
TRANSFERABLE_FILE = "data/processed/transferable_job_skills.csv"
EXCLUDED_FILE = "data/processed/excluded_job_skills.csv"


# =========================================================
# 1. Normalize common skill names
# =========================================================

NORMALIZATION = {
    "python programming": "Python",
    "python development": "Python",
    "python scripting": "Python",

    "java programming": "Java",
    "java development": "Java",

    "javascript programming": "JavaScript",
    "javascript development": "JavaScript",
    "js": "JavaScript",

    "typescript programming": "TypeScript",
    "ts": "TypeScript",

    "c plus plus": "C++",
    "c++ programming": "C++",

    "c sharp": "C#",
    "c# programming": "C#",

    "structured query language": "SQL",
    "sql programming": "SQL",

    "react.js": "React",
    "reactjs": "React",

    "nodejs": "Node.js",
    "node js": "Node.js",

    "nextjs": "Next.js",
    "next js": "Next.js",

    "vuejs": "Vue.js",
    "vue js": "Vue.js",

    "angular.js": "Angular",
    "angularjs": "Angular",

    "postgres": "PostgreSQL",
    "postgresql database": "PostgreSQL",

    "mongo": "MongoDB",
    "mongodb database": "MongoDB",

    "amazon web services": "AWS",
    "amazon aws": "AWS",

    "microsoft azure": "Azure",
    "google cloud": "GCP",
    "google cloud platform": "GCP",

    "k8s": "Kubernetes",

    "ci cd": "CI/CD",
    "ci/cd pipeline": "CI/CD",

    "rest apis": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",

    "machine learning algorithms": "Machine Learning",
    "ml": "Machine Learning",

    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",

    "natural language processing": "NLP",

    "data analytics": "Data Analysis",
    "data analysis skills": "Data Analysis",

    "data visualisation": "Data Visualization",
    "data visualization": "Data Visualization",

    "power bi": "Power BI",
    "microsoft power bi": "Power BI",

    "tableau software": "Tableau",

    "apache spark": "Apache Spark",
    "spark": "Apache Spark",

    "apache kafka": "Apache Kafka",
    "kafka": "Apache Kafka",

    "apache airflow": "Apache Airflow",
    "airflow": "Apache Airflow",

    "py spark": "PySpark",

    "version control": "Git",
    "git version control": "Git",

    "linux administration": "Linux",
    "linux operating system": "Linux",

    "bash scripting": "Bash",
    "shell scripting": "Shell Scripting",

    "information security": "Cybersecurity",
    "cyber security": "Cybersecurity",
}


# =========================================================
# 2. Transferable skills
# =========================================================

TRANSFERABLE = {
    "communication",
    "communication skills",
    "written communication",
    "verbal communication",
    "teamwork",
    "team work",
    "collaboration",
    "leadership",
    "problem solving",
    "problemsolving",
    "analytical skills",
    "critical thinking",
    "time management",
    "project management",
    "stakeholder management",
    "presentation skills",
    "interpersonal skills",
    "customer service",
    "attention to detail",
    "adaptability",
    "organization",
    "organizational skills",
    "decision making",
}


# =========================================================
# 3. Things to exclude
# =========================================================

EXCLUDED_PATTERNS = [
    r"\bbachelor",
    r"\bmaster",
    r"\bphd\b",
    r"\bdegree\b",
    r"\bdiploma\b",
    r"\bcertification\b",
    r"\bcertified\b",
    r"\blicense\b",
    r"\blicensed\b",

    r"\byears? of experience\b",
    r"\byear experience\b",
    r"\bexperience in\b",

    r"\bsalary\b",
    r"\$\d",
    r"\bper hour\b",
    r"\bpay range\b",

    r"\bwork authorization\b",
    r"\bvisa sponsorship\b",
    r"\bauthorized to work\b",

    r"\bfull[- ]time\b",
    r"\bpart[- ]time\b",
    r"\bremote\b",
    r"\bon[- ]site\b",

    r"\bdriver'?s license\b",
]


# =========================================================
# 4. Known technical skills
# =========================================================

TECHNICAL_SKILLS = {
    # Programming
    "python", "java", "c", "c++", "c#", "go", "golang",
    "rust", "kotlin", "swift", "ruby", "php", "scala",
    "r", "perl", "matlab", "typescript", "javascript",

    # Web
    "html", "css", "react", "vue.js", "angular", "next.js",
    "jquery", "bootstrap", "tailwind css",
    "django", "flask", "fastapi", "spring", "spring boot",
    ".net", ".net core", "asp.net",

    # Backend
    "node.js", "express", "graphql", "rest api",
    "api development", "microservices", "web services",

    # Database
    "sql", "mysql", "postgresql", "mongodb", "redis",
    "cassandra", "oracle", "sql server", "nosql",
    "database administration", "data modeling",

    # Cloud
    "aws", "azure", "gcp", "cloud computing",
    "amazon ec2", "amazon s3", "lambda",
    "cloud architecture",

    # DevOps
    "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "gitlab", "github actions",
    "ci/cd", "devops", "grafana", "prometheus",
    "infrastructure as code",

    # Data
    "data analysis", "data analytics", "data visualization",
    "power bi", "tableau", "excel",
    "statistics", "statistical analysis",
    "data warehousing", "etl",
    "etl pipeline development",
    "apache spark", "pyspark", "apache kafka",
    "apache airflow", "airflow",
    "snowflake", "databricks",

    # AI
    "machine learning", "deep learning",
    "artificial intelligence", "generative ai",
    "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn",
    "keras", "hugging face",

    # Cybersecurity
    "cybersecurity", "network security",
    "vulnerability assessment",
    "incident response", "siem",
    "penetration testing", "cryptography",
    "iam", "identity management",

    # Networking
    "networking", "network engineering",
    "tcp/ip", "dns", "dhcp", "bgp", "ospf",
    "routing", "switching",

    # Operating systems
    "linux", "unix", "windows", "bash",
    "shell scripting", "system administration",

    # Software engineering
    "software engineering", "software development",
    "object oriented programming", "oop",
    "algorithms", "data structures",
    "git", "github", "testing",
    "selenium", "unit testing",
    "automation testing",

    "computer science",
    "debugging",
    "troubleshooting",
    "api",
    "sdk",
}


# =========================================================
# 5. Functions
# =========================================================

def normalize_name(skill):
    skill = skill.strip()
    key = skill.lower()

    return NORMALIZATION.get(key, skill)


def is_excluded(skill):
    text = skill.lower()

    for pattern in EXCLUDED_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


def is_transferable(skill):
    return skill.lower().strip() in TRANSFERABLE


def is_technical(skill):
    text = skill.lower().strip()

    if text in TECHNICAL_SKILLS:
        return True

    indicators = [
        ".js",
        ".net",
        "api",
        "sdk",
        "sql",
        "database",
        "programming",
        "scripting",
        "framework",
        "library",
        "cloud",
        "devops",
        "machine learning",
        "deep learning",
        "cybersecurity",
        "cyber security",
        "networking",
        "software",
        "data engineering",
        "data science",
        "data analysis",
        "data visualization",
        "automation",
        "container",
        "kubernetes",
        "docker",
        "terraform",
        "linux",
    ]

    return any(indicator in text for indicator in indicators)


def get_category(skill):

    text = skill.lower()

    if any(x in text for x in [
        "python", "java", "javascript", "typescript", "c++",
        "c#", "golang", "go", "rust", "kotlin", "swift",
        "ruby", "php", "scala", "programming"
    ]):
        return "Programming"

    if any(x in text for x in [
        "html", "css", "react", "angular", "vue",
        "django", "flask", "fastapi", "spring",
        ".net", "jquery", "frontend", "web development"
    ]):
        return "Web Development"

    if any(x in text for x in [
        "sql", "mysql", "postgres", "mongodb", "oracle",
        "database", "nosql", "redis", "cassandra"
    ]):
        return "Database"

    if any(x in text for x in [
        "aws", "azure", "gcp", "cloud", "ec2", "s3"
    ]):
        return "Cloud"

    if any(x in text for x in [
        "docker", "kubernetes", "terraform", "jenkins",
        "ansible", "devops", "ci/cd", "gitlab",
        "github actions", "grafana", "prometheus"
    ]):
        return "DevOps"

    if any(x in text for x in [
        "data analysis", "data analytics", "power bi",
        "tableau", "statistics", "data visualization",
        "excel", "business intelligence"
    ]):
        return "Data & Analytics"

    if any(x in text for x in [
        "machine learning", "deep learning",
        "artificial intelligence", "generative ai",
        "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn"
    ]):
        return "AI & Machine Learning"

    if any(x in text for x in [
        "spark", "pyspark", "kafka", "airflow",
        "etl", "data engineering", "snowflake",
        "databricks", "data warehousing"
    ]):
        return "Data Engineering"

    if any(x in text for x in [
        "rest api", "graphql", "node.js", "express",
        "microservices", "api development", "web services"
    ]):
        return "Backend & APIs"

    if any(x in text for x in [
        "cybersecurity", "cyber security", "security",
        "vulnerability", "incident response", "siem",
        "cryptography", "penetration"
    ]):
        return "Cybersecurity"

    if any(x in text for x in [
        "linux", "unix", "windows", "bash",
        "shell", "operating system", "system administration"
    ]):
        return "Operating Systems"

    if any(x in text for x in [
        "network", "tcp/ip", "dns", "dhcp",
        "bgp", "ospf", "routing", "switching"
    ]):
        return "Networking"

    if any(x in text for x in [
        "software engineering", "software development",
        "testing", "selenium", "git", "github",
        "algorithms", "data structures", "debugging"
    ]):
        return "Software Engineering"

    return "Other Technical"


# =========================================================
# 6. Load cleaned skill vocabulary
# =========================================================

clean_skills = set()

with open(
    CLEAN_SKILLS_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        skill = row["skill"].strip()

        if skill:
            clean_skills.add(skill)


print("Clean skill vocabulary:", len(clean_skills))


# =========================================================
# 7. Classify the cleaned vocabulary
# =========================================================

skill_classification = {}

for skill in clean_skills:

    normalized = normalize_name(skill)

    if is_excluded(normalized):
        skill_classification[skill] = (
            "Excluded",
            normalized
        )

    elif is_transferable(normalized):
        skill_classification[skill] = (
            "Transferable",
            normalized
        )

    elif is_technical(normalized):
        skill_classification[skill] = (
            "Technical",
            normalized
        )
    # Fast case-insensitive lookup
skill_classification_lower = {
    skill.lower(): classification
    for skill, classification
    in skill_classification.items()
}


print(
    "Recognized skills:",
    len(skill_classification)
)


# =========================================================
# 8. Stream through job-level data
# =========================================================

technical = []
transferable = []
excluded = []
categorized = []

seen_technical = set()
seen_transferable = set()
seen_categorized = set()
seen_excluded = set()


with open(
    JOB_SKILLS_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        raw_skill = row["skill"].strip()

        if not raw_skill:
            continue

            # Fast case-insensitive lookup
        classification = skill_classification.get(
            raw_skill
        )

        if classification is None:
            classification = skill_classification.get(
                raw_skill.lower()
            )

        if classification is None:
            continue

        skill_type, normalized = classification

        base = {
            "job_link": row["job_link"],
            "job_title": row["job_title"],
            "occupation": row["occupation"],
            "skill": normalized
        }

        # -----------------------------------------
        # Technical
        # -----------------------------------------

        if skill_type == "Technical":

            category = get_category(normalized)

            key = (
                row["job_link"],
                normalized
            )

            if key not in seen_technical:

                seen_technical.add(key)

                technical.append({
                    **base,
                    "category": category
                })

                categorized.append({
                    **base,
                    "category": category
                })

        # -----------------------------------------
        # Transferable
        # -----------------------------------------

        elif skill_type == "Transferable":

            key = (
                row["job_link"],
                normalized
            )

            if key not in seen_transferable:

                seen_transferable.add(key)

                transferable.append(base)

                categorized.append({
                    **base,
                    "category": "Transferable"
                })

        # -----------------------------------------
        # Excluded
        # -----------------------------------------

        elif skill_type == "Excluded":

            key = (
                row["job_link"],
                raw_skill
            )

            if key not in seen_excluded:

                seen_excluded.add(key)

                excluded.append({
                    "job_link": row["job_link"],
                    "job_title": row["job_title"],
                    "occupation": row["occupation"],
                    "skill": raw_skill
                })


# =========================================================
# 9. Save
# =========================================================

def write_csv(filename, rows):

    if not rows:
        print("Nothing to write:", filename)
        return

    with open(
        filename,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


write_csv(CATEGORIZED_FILE, categorized)
write_csv(TECHNICAL_FILE, technical)
write_csv(TRANSFERABLE_FILE, transferable)
write_csv(EXCLUDED_FILE, excluded)


# =========================================================
# 10. Results
# =========================================================

category_counts = Counter(
    row["category"]
    for row in technical
)

skill_counts = Counter(
    row["skill"]
    for row in technical
)

print("\n========================================")
print("STEP 12 COMPLETE")
print("========================================")

print("Technical records    :", len(technical))
print("Transferable records :", len(transferable))
print("Excluded records     :", len(excluded))

print(
    "Unique technical skills:",
    len(skill_counts)
)

print("\nTechnical categories:")

for category, count in category_counts.most_common():

    print(
        f"{category:25} -> {count}"
    )

print("\nTop technical skills:")

for skill, count in skill_counts.most_common(40):

    print(
        f"{skill:30} -> {count}"
    )

print("\nFiles created:")
print(TECHNICAL_FILE)
print(TRANSFERABLE_FILE)
print(EXCLUDED_FILE)
print(CATEGORIZED_FILE)
