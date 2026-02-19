"""
Resume parsing pipeline.
PDF → Text → Cleaning → Section Detection → Structured Data
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber
import spacy

# Load spaCy model lazily
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ─────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────

@dataclass
class ParsedResume:
    raw_text: str = ""
    cleaned_text: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: float = 0.0
    experience_entries: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)


# ─────────────────────────────────────────────
# PDF Extraction
# ─────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise RuntimeError(f"Failed to extract PDF text from {pdf_path}: {e}") from e
    return text.strip()


# ─────────────────────────────────────────────
# Text Cleaning
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove special chars, lowercase, lemmatize, remove stopwords."""
    nlp = _get_nlp()
    text = re.sub(r'[^a-zA-Z0-9\s\.\,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and len(token.text) > 1]
    return " ".join(tokens)


# ─────────────────────────────────────────────
# Section Detection
# ─────────────────────────────────────────────

SECTION_PATTERNS: dict[str, list[str]] = {
    "skills": [
        r"(?i)(technical\s+skills?|skills?|core\s+competencies|technologies|tech\s+stack|expertise)",
    ],
    "experience": [
        r"(?i)(work\s+experience|professional\s+experience|experience|employment\s+history|career\s+history)",
    ],
    "education": [
        r"(?i)(education|academic\s+background|qualifications|degrees?)",
    ],
    "projects": [
        r"(?i)(projects?|personal\s+projects?|key\s+projects?|notable\s+projects?)",
    ],
    "certifications": [
        r"(?i)(certifications?|certificates?|licenses?|credentials?|accreditations?)",
    ],
    "summary": [
        r"(?i)(summary|objective|professional\s+summary|profile|about\s+me|overview)",
    ],
}


def detect_sections(text: str) -> dict[str, str]:
    """Split resume text into labeled sections."""
    lines = text.split("\n")
    sections: dict[str, str] = {}
    current_section: str = "header"
    buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        matched_section = None

        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, stripped) and len(stripped) < 60:
                    matched_section = section_name
                    break
            if matched_section:
                break

        if matched_section:
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = matched_section
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections


# ─────────────────────────────────────────────
# Entity Extraction
# ─────────────────────────────────────────────

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'[\+\(]?[0-9][0-9 \-\(\)]{7,}[0-9]')
EXPERIENCE_YEAR_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)?',
    re.IGNORECASE,
)


def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = PHONE_RE.search(text)
    return m.group(0) if m else ""


def extract_name(text: str) -> str:
    """Use spaCy NER to detect PERSON entities near the top of the text."""
    nlp = _get_nlp()
    header = text[:500]
    doc = nlp(header)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    # Fallback: first non-empty line
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and not EMAIL_RE.search(stripped) and not PHONE_RE.search(stripped):
            return stripped
    return ""


def extract_experience_years(text: str) -> float:
    """Extract total years of experience mentioned explicitly."""
    matches = EXPERIENCE_YEAR_RE.findall(text)
    if not matches:
        return 0.0
    return max(float(m) for m in matches)


def extract_education(sections: dict[str, str]) -> list[str]:
    """Extract education entries from the education section."""
    edu_text = sections.get("education", "")
    if not edu_text:
        return []
    entries = [line.strip() for line in edu_text.split("\n") if line.strip()]
    return entries[:10]


def extract_projects(sections: dict[str, str]) -> list[str]:
    proj_text = sections.get("projects", "")
    if not proj_text:
        return []
    entries = [line.strip() for line in proj_text.split("\n") if line.strip()]
    return entries[:10]


def extract_certifications(sections: dict[str, str]) -> list[str]:
    cert_text = sections.get("certifications", "")
    if not cert_text:
        return []
    entries = [line.strip() for line in cert_text.split("\n") if line.strip()]
    return entries[:10]


def extract_experience_entries(sections: dict[str, str]) -> list[str]:
    exp_text = sections.get("experience", "")
    if not exp_text:
        return []
    entries = [line.strip() for line in exp_text.split("\n") if line.strip()]
    return entries[:20]


# ─────────────────────────────────────────────
# Skill Extraction
# ─────────────────────────────────────────────

def extract_skills_from_text(text: str) -> list[str]:
    """Match skills from SKILL_DB against text."""
    from skill_db import extract_skills_from_text as _extract
    return _extract(text)


# ─────────────────────────────────────────────
# Main Parse Function
# ─────────────────────────────────────────────

def parse_resume(pdf_path: str) -> ParsedResume:
    """Full parsing pipeline for a single resume PDF."""
    raw_text = extract_text_from_pdf(pdf_path)
    sections = detect_sections(raw_text)
    cleaned = clean_text(raw_text)

    resume = ParsedResume(
        raw_text=raw_text,
        cleaned_text=cleaned,
        name=extract_name(raw_text),
        email=extract_email(raw_text),
        phone=extract_phone(raw_text),
        skills=extract_skills_from_text(raw_text),
        experience_years=extract_experience_years(raw_text),
        experience_entries=extract_experience_entries(sections),
        education=extract_education(sections),
        certifications=extract_certifications(sections),
        projects=extract_projects(sections),
        sections=sections,
    )
    return resume
