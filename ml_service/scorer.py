"""
Weighted scoring algorithm.

Final Score =
    0.50 * Semantic Similarity
  + 0.25 * Skill Match
  + 0.15 * Experience Match
  + 0.10 * Education Match

All weights are adjustable at call-time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from embeddings import cosine_similarity, embed
from parser import ParsedResume
from skill_db import extract_skills_from_text


# ─────────────────────────────────────────────
# Scoring weights (defaults)
# ─────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "semantic": 0.50,
    "skill": 0.25,
    "experience": 0.15,
    "education": 0.10,
}

# Education tier values
EDUCATION_TIERS: dict[str, float] = {
    "phd": 1.0, "doctorate": 1.0,
    "master": 0.85, "msc": 0.85, "mba": 0.85, "m.tech": 0.85, "m.e.": 0.85,
    "bachelor": 0.70, "bsc": 0.70, "b.tech": 0.70, "b.e.": 0.70, "be": 0.70,
    "associate": 0.50, "diploma": 0.40,
    "high school": 0.20,
}


@dataclass
class DetailedScore:
    # Composite
    total_score: float
    # Components
    semantic_score: float
    skill_score: float
    experience_score: float
    education_score: float
    # Used weights
    weights: dict[str, float]
    # Skill details
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    # Experience details
    required_experience: float
    candidate_experience: float
    experience_gap: float   # negative = short, 0+ = meets/exceeds
    # Education
    education_entries: list[str]


# ─────────────────────────────────────────────
# Sub-scorers
# ─────────────────────────────────────────────

def _semantic_score(resume: ParsedResume, jd_vector) -> float:
    """Cosine similarity between resume text embedding and JD embedding."""
    res_vec = embed(resume.cleaned_text or resume.raw_text[:3000])
    return max(0.0, cosine_similarity(res_vec, jd_vector))


def _skill_score(resume: ParsedResume, jd_text: str) -> tuple[float, list[str], list[str], list[str]]:
    """
    Fraction of JD-required skills that appear in the resume.
    Returns (score, required_skills, matched, missing)
    """
    required = extract_skills_from_text(jd_text)
    if not required:
        return 0.0, [], [], []

    resume_skill_set = {s.lower() for s in resume.skills}
    matched = [s for s in required if s.lower() in resume_skill_set]
    missing = [s for s in required if s.lower() not in resume_skill_set]

    score = len(matched) / len(required)
    return round(score, 4), required, matched, missing


def _experience_score(
    resume: ParsedResume,
    jd_text: str,
) -> tuple[float, float, float, float]:
    """
    Compare required years of experience (from JD) vs candidate years.
    Returns (score, required_years, candidate_years, gap)
    """
    # Extract required years from JD
    YEAR_RE = re.compile(
        r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
        re.IGNORECASE,
    )
    matches = YEAR_RE.findall(jd_text)
    required = max((float(m) for m in matches), default=0.0)
    candidate = resume.experience_years

    if required == 0:
        return 1.0, 0.0, candidate, 0.0

    gap = candidate - required   # negative = short
    if candidate >= required:
        score = 1.0
    else:
        # Partial credit: linearly scale up to required
        score = max(0.0, candidate / required)

    return round(score, 4), required, candidate, round(gap, 1)


def _education_score(resume: ParsedResume, jd_text: str) -> float:
    """
    Check if resume education tier meets the JD expectations.
    Returns a 0-1 score.
    """
    jd_lower = jd_text.lower()
    edu_text = " ".join(resume.education).lower()

    # Find highest tier in resume
    resume_tier = 0.0
    for keyword, value in EDUCATION_TIERS.items():
        if keyword in edu_text:
            resume_tier = max(resume_tier, value)

    # Find required tier in JD
    required_tier = 0.0
    for keyword, value in EDUCATION_TIERS.items():
        if keyword in jd_lower:
            required_tier = max(required_tier, value)

    if required_tier == 0.0:
        # JD doesn't specify → full credit if candidate has any degree
        return 1.0 if resume_tier > 0 else 0.7

    if resume_tier >= required_tier:
        return 1.0
    elif resume_tier > 0:
        return round(resume_tier / required_tier, 4)
    else:
        return 0.0


# ─────────────────────────────────────────────
# Main scorer
# ─────────────────────────────────────────────

def score_resume(
    resume: ParsedResume,
    jd_text: str,
    jd_vector=None,
    weights: dict[str, float] | None = None,
) -> DetailedScore:
    """
    Compute a detailed weighted score for a resume against a job description.

    Args:
        resume:    Parsed resume object.
        jd_text:   Raw job description text.
        jd_vector: Pre-computed JD embedding (pass to avoid recomputing).
        weights:   Override default scoring weights.

    Returns:
        DetailedScore with total and component scores.
    """
    from embeddings import embed as _embed
    if jd_vector is None:
        jd_vector = _embed(jd_text)

    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    # Normalise weights to sum to 1
    total_w = sum(w.values())
    w = {k: v / total_w for k, v in w.items()}

    # Component scores
    sem = _semantic_score(resume, jd_vector)
    skill_s, required, matched, missing = _skill_score(resume, jd_text)
    exp_s, req_exp, cand_exp, gap = _experience_score(resume, jd_text)
    edu_s = _education_score(resume, jd_text)

    total = (
        w["semantic"] * sem
        + w["skill"] * skill_s
        + w["experience"] * exp_s
        + w["education"] * edu_s
    )

    return DetailedScore(
        total_score=round(total, 4),
        semantic_score=round(sem, 4),
        skill_score=round(skill_s, 4),
        experience_score=round(exp_s, 4),
        education_score=round(edu_s, 4),
        weights=w,
        required_skills=required,
        matched_skills=matched,
        missing_skills=missing,
        required_experience=req_exp,
        candidate_experience=cand_exp,
        experience_gap=gap,
        education_entries=resume.education,
    )
