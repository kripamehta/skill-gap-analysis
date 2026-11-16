
import re
import unicodedata

SKILL_ALIASES = {
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "python3": "python",
    "py": "python",
    "amazon web services": "aws",
    "amazon aws": "aws",
    "powerbi": "power bi",
    "ms power bi": "power bi",
    "reactjs": "react",
    "react.js": "react",
    "ts": "typescript",
    "golang": "go",
    "mongo": "mongodb",
}


def clean_skill(skill):
    skill = unicodedata.normalize("NFKC", str(skill))
    skill = skill.strip().lower()
    skill = re.sub(r"\s+", " ", skill)
    return skill


def normalize_skill(skill):
    cleaned = clean_skill(skill)

    if not cleaned:
        return ""

    return SKILL_ALIASES.get(cleaned, cleaned)


def normalize_skill_list(skills):
    normalized = {
        normalize_skill(skill)
        for skill in skills
        if normalize_skill(skill)
    }

    return sorted(normalized)
