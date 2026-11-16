import csv
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer
import numpy as np


TECHNICAL_FILE = "data/processed/technical_job_skills.csv"
ESCO_FILE = "data/processed/esco_skills.csv"
OUTPUT_FILE = "data/processed/skill_normalization.csv"


# =========================================================
# 1. PROJECT-SPECIFIC NORMALIZATION
# =========================================================

ALIASES = {

    # Programming
    "python": "Python",
    "python programming": "Python",
    "java": "Java",
    "java programming": "Java",
    "javascript": "JavaScript",
    "javascript programming": "JavaScript",
    "typescript": "TypeScript",
    "c++": "C++",
    "c#": "C#",
    "golang": "Go",

    # Web
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "angular": "Angular",
    "angularjs": "Angular",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "jquery": "jQuery",

    "html": "HTML",
    "css": "CSS",
    "bootstrap": "Bootstrap",
    "tailwind css": "Tailwind CSS",

    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    ".net": ".NET",
    ".net core": ".NET Core",
    "asp.net": "ASP.NET",

    # Backend
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "graphql": "GraphQL",
    "rest api": "REST API",
    "rest apis": "REST API",
    "restful api": "REST API",
    "api development": "API Development",
    "microservices": "Microservices",

    # Databases
    "sql": "SQL",
    "structured query language": "SQL",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "nosql": "NoSQL",
    "oracle": "Oracle",
    "sql server": "SQL Server",

    # Cloud
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "amazon ec2": "Amazon EC2",
    "amazon s3": "Amazon S3",

    # DevOps
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "gitlab": "GitLab",
    "github actions": "GitHub Actions",
    "ci/cd": "CI/CD",
    "ci cd": "CI/CD",
    "devops": "DevOps",
    "grafana": "Grafana",
    "prometheus": "Prometheus",

    # Data
    "data analysis": "Data Analysis",
    "data analysis skills": "Data Analysis",
    "data analytics": "Data Analysis",
    "data visualization": "Data Visualization",
    "data visualisation": "Data Visualization",
    "power bi": "Power BI",
    "microsoft power bi": "Power BI",
    "tableau": "Tableau",
    "excel": "Excel",
    "statistics": "Statistics",
    "statistical analysis": "Statistical Analysis",

    # Data engineering
    "apache spark": "Apache Spark",
    "spark": "Apache Spark",
    "pyspark": "PySpark",
    "apache kafka": "Apache Kafka",
    "kafka": "Apache Kafka",
    "apache airflow": "Apache Airflow",
    "airflow": "Apache Airflow",
    "etl": "ETL",
    "snowflake": "Snowflake",
    "databricks": "Databricks",

    # AI / ML
    "machine learning": "Machine Learning",
    "machine learning algorithms": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "generative ai": "Generative AI",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "scikit-learn": "Scikit-learn",
    "keras": "Keras",

    # Security
    "cybersecurity": "Cybersecurity",
    "cyber security": "Cybersecurity",
    "information security": "Cybersecurity",
    "network security": "Network Security",
    "incident response": "Incident Response",
    "vulnerability assessment": "Vulnerability Assessment",
    "cryptography": "Cryptography",
    "siem": "SIEM",
    "penetration testing": "Penetration Testing",

    # Operating systems
    "linux": "Linux",
    "linux administration": "Linux",
    "unix": "Unix",
    "windows": "Windows",
    "bash": "Bash",
    "shell scripting": "Shell Scripting",
    "system administration": "System Administration",

    # Networking
    "tcp/ip": "TCP/IP",
    "dns": "DNS",
    "dhcp": "DHCP",
    "bgp": "BGP",
    "ospf": "OSPF",
    "networking": "Networking",
    "network engineering": "Network Engineering",
    "routing": "Routing",
    "switching": "Switching",

    # Software engineering
    "software engineering": "Software Engineering",
    "software development": "Software Development",
    "git": "Git",
    "github": "GitHub",
    "testing": "Software Testing",
    "selenium": "Selenium",
    "unit testing": "Unit Testing",
    "automation testing": "Automation Testing",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "object oriented programming": "Object-Oriented Programming",
    "oop": "Object-Oriented Programming",
    "debugging": "Debugging",
    "troubleshooting": "Troubleshooting",
}


# =========================================================
# 2. LOAD TECHNICAL SKILLS
# =========================================================

technical_skills = set()

with open(
    TECHNICAL_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        skill = row["skill"].strip()

        if skill:
            technical_skills.add(skill)


technical_skills = sorted(technical_skills)

print("Unique technical skills:", len(technical_skills))


# =========================================================
# 3. LOAD ESCO
# =========================================================

esco = []

with open(
    ESCO_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        label = row["preferred_label"].strip()

        if label:

            esco.append({
                "id": row["skill_id"],
                "label": label
            })


esco_labels = [
    item["label"]
    for item in esco
]

# Fast ESCO exact lookup
esco_exact = {
    label.lower(): item
    for item in esco
}

print("ESCO skills loaded:", len(esco))


# =========================================================
# 4. LOAD SENTENCE TRANSFORMER
# =========================================================

print("\nLoading Sentence Transformer...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Model loaded.")


# =========================================================
# 5. CREATE ESCO EMBEDDINGS
# =========================================================

print("\nEncoding ESCO skills...")

esco_embeddings = model.encode(
    esco_labels,
    batch_size=128,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("ESCO embeddings ready.")


# =========================================================
# 6. ENCODE PROJECT SKILLS IN BATCHES
# =========================================================

print("\nEncoding project skills...")

project_embeddings = model.encode(
    technical_skills,
    batch_size=128,
    show_progress_bar=True,
    normalize_embeddings=True
)

print("Project embeddings ready.")


# =========================================================
# 7. NORMALIZATION
# =========================================================

results = []

alias_count = 0
exact_count = 0
semantic_count = 0
retained_count = 0


for index, skill in enumerate(technical_skills):

    key = skill.lower().strip()

    # -----------------------------------------------------
    # A. Project alias
    # -----------------------------------------------------

    if key in ALIASES:

        results.append({
            "job_skill": skill,
            "normalized_skill": ALIASES[key],
            "esco_skill_id": "",
            "similarity": "",
            "method": "project_alias"
        })

        alias_count += 1
        continue

    # -----------------------------------------------------
    # B. Exact ESCO match
    # -----------------------------------------------------

    if key in esco_exact:

        item = esco_exact[key]

        results.append({
            "job_skill": skill,
            "normalized_skill": item["label"],
            "esco_skill_id": item["id"],
            "similarity": "1.0",
            "method": "esco_exact"
        })

        exact_count += 1
        continue

    # -----------------------------------------------------
    # C. Fuzzy candidates
    # -----------------------------------------------------

    matches = process.extract(
        skill,
        esco_labels,
        scorer=fuzz.token_set_ratio,
        limit=5
    )

    matches = [
        match
        for match in matches
        if match[1] >= 70
    ]

    # -----------------------------------------------------
    # D. Semantic matching
    # -----------------------------------------------------

    accepted = False

    if matches:

        candidate_labels = [
            match[0]
            for match in matches
        ]

        candidate_indices = [
            esco_labels.index(label)
            for label in candidate_labels
        ]

        candidate_embeddings = esco_embeddings[
            candidate_indices
        ]

        skill_embedding = project_embeddings[index]

        similarities = np.dot(
            candidate_embeddings,
            skill_embedding
        )

        best_position = int(
            np.argmax(similarities)
        )

        best_similarity = float(
            similarities[best_position]
        )

        best_fuzzy = matches[
            best_position
        ][1]

        best_index = candidate_indices[
            best_position
        ]

        # Strong threshold.
        #
        # We intentionally do NOT accept weak
        # semantic matches because technologies such
        # as Docker/Airflow can map to unrelated
        # ESCO concepts.

        if (
            best_similarity >= 0.82
            and best_fuzzy >= 75
        ):

            results.append({
                "job_skill": skill,
                "normalized_skill": esco[best_index]["label"],
                "esco_skill_id": esco[best_index]["id"],
                "similarity": round(
                    best_similarity,
                    4
                ),
                "method": "esco_semantic"
            })

            semantic_count += 1
            accepted = True

    # -----------------------------------------------------
    # E. Retain original skill
    # -----------------------------------------------------

    if not accepted:

        results.append({
            "job_skill": skill,
            "normalized_skill": skill,
            "esco_skill_id": "",
            "similarity": "",
            "method": "retained_project_skill"
        })

        retained_count += 1

    # Progress
    if (index + 1) % 500 == 0:

        print(
            f"Processed {index + 1}/"
            f"{len(technical_skills)}"
        )


# =========================================================
# 8. SAVE
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "job_skill",
            "normalized_skill",
            "esco_skill_id",
            "similarity",
            "method"
        ]
    )

    writer.writeheader()
    writer.writerows(results)


# =========================================================
# 9. RESULTS
# =========================================================

total = len(results)

print("\n========================================")
print("STEP 13 COMPLETE")
print("========================================")

print("Unique technical skills :", total)
print("Project aliases         :", alias_count)
print("ESCO exact matches      :", exact_count)
print("ESCO semantic matches   :", semantic_count)
print("Retained original       :", retained_count)

if total > 0:

    coverage = (
        (
            alias_count
            + exact_count
            + semantic_count
        )
        / total
    ) * 100

    print(
        f"Normalization coverage : "
        f"{coverage:.2f}%"
    )

print("\nSaved:")
print(OUTPUT_FILE)
