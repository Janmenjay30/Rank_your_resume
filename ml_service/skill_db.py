"""
Skill database used for skill extraction and matching.
Each category maps to a list of known skill keywords.
"""

SKILL_DB: dict[str, list[str]] = {
    "backend": [
        "node.js", "nodejs", "express", "fastapi", "flask", "django",
        "spring", "spring boot", "rails", "ruby on rails", "laravel",
        "rest", "restful", "graphql", "grpc", "microservices",
        "api", "websocket", "oauth", "jwt",
    ],
    "frontend": [
        "react", "reactjs", "angular", "vue", "vuejs", "svelte",
        "next.js", "nextjs", "nuxt", "html", "css", "javascript",
        "typescript", "tailwind", "bootstrap", "sass", "webpack", "vite",
        "redux", "zustand", "mobx",
    ],
    "database": [
        "mongodb", "mongoose", "postgresql", "postgres", "mysql", "sqlite",
        "redis", "cassandra", "dynamodb", "firebase", "firestore",
        "elasticsearch", "neo4j", "prisma", "sequelize", "orm",
        "sql", "nosql",
    ],
    "cloud": [
        "aws", "amazon web services", "gcp", "google cloud", "azure",
        "ec2", "s3", "lambda", "cloudfront", "rds", "ecs", "eks",
        "vercel", "netlify", "heroku", "digitalocean",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "ci/cd", "jenkins", "github actions",
        "gitlab ci", "terraform", "ansible", "helm", "nginx", "linux",
        "bash", "shell scripting", "prometheus", "grafana",
    ],
    "ml_ai": [
        "machine learning", "deep learning", "neural network", "tensorflow",
        "pytorch", "keras", "scikit-learn", "sklearn", "nlp",
        "natural language processing", "computer vision", "bert",
        "transformers", "hugging face", "openai", "langchain",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    ],
    "programming": [
        "python", "java", "c++", "c#", "go", "golang", "rust",
        "kotlin", "swift", "scala", "r", "php", "ruby", "elixir",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "tdd", "bdd", "ddd",
        "clean architecture", "solid", "design patterns", "git",
        "code review", "unit testing", "integration testing",
    ],
    "data": [
        "data analysis", "data science", "etl", "data pipeline",
        "apache spark", "kafka", "airflow", "dbt", "tableau",
        "power bi", "looker", "hadoop", "hive",
    ],
    "security": [
        "cybersecurity", "penetration testing", "owasp", "ssl", "tls",
        "encryption", "authentication", "authorization", "iam",
        "soc 2", "gdpr",
    ],
}

# Flat list of all skills for quick lookup
ALL_SKILLS: list[str] = [s for skills in SKILL_DB.values() for s in skills]


def get_category(skill: str) -> str | None:
    """Return the category of a skill, or None if not found."""
    skill_lower = skill.lower()
    for category, skills in SKILL_DB.items():
        if skill_lower in skills:
            return category
    return None


def extract_skills_from_text(text: str) -> list[str]:
    """Match skills from SKILL_DB against text using word-boundary regex."""
    import re
    text_lower = text.lower()
    found: list[str] = []
    for skill in ALL_SKILLS:
        pattern = r'(?<![a-z0-9])' + re.escape(skill) + r'(?![a-z0-9])'
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))  # deduplicate, preserve order
