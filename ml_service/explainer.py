"""
Explainability engine.

Converts a DetailedScore into human-readable feedback:
  ✅ Matched Skills
  ❌ Missing Skills
  📈 Experience Gap
  🎯 Fit Category
  📝 Summary paragraph (template-based, no external LLM required)
"""

from __future__ import annotations

from dataclasses import dataclass

from scorer import DetailedScore


# ─────────────────────────────────────────────
# Fit categories (based on total score)
# ─────────────────────────────────────────────

FIT_THRESHOLDS = [
    (0.85, "Excellent Match",   "This candidate is an outstanding fit for the role."),
    (0.70, "Strong Match",      "This candidate meets most requirements and is a strong contender."),
    (0.55, "Good Match",        "This candidate fits several key requirements but has some gaps."),
    (0.40, "Partial Match",     "This candidate meets some criteria. Worth considering after stronger applicants."),
    (0.0,  "Weak Match",        "This candidate does not closely match the job requirements."),
]


def classify_fit(score: float) -> tuple[str, str]:
    """Return (fit_label, fit_description) for a total score."""
    for threshold, label, desc in FIT_THRESHOLDS:
        if score >= threshold:
            return label, desc
    return "Weak Match", "This candidate does not closely match the job requirements."


# ─────────────────────────────────────────────
# Output structure
# ─────────────────────────────────────────────

@dataclass
class Explanation:
    fit_category: str
    fit_description: str
    summary: str
    matched_skills: list[str]
    missing_skills: list[str]
    skill_match_pct: float        # 0–100
    experience_status: str        # "Meets", "Exceeds", "Short by X years"
    experience_gap: float
    education_entries: list[str]
    score_breakdown: dict[str, float]
    recommendations: list[str]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _experience_status(gap: float, required: float, candidate: float) -> str:
    if required == 0:
        return f"No specific experience requirement (candidate has {candidate:.1f} yrs)"
    if gap >= 0:
        return f"Meets requirement ({candidate:.1f} / {required:.1f} yrs)"
    return f"Short by {abs(gap):.1f} year(s) ({candidate:.1f} / {required:.1f} yrs)"


def _recommendations(score: DetailedScore) -> list[str]:
    recs: list[str] = []
    if score.missing_skills:
        top_missing = score.missing_skills[:5]
        recs.append(f"Candidate is missing key skills: {', '.join(top_missing)}.")
    if score.experience_gap < -1:
        recs.append(
            f"Candidate is {abs(score.experience_gap):.1f} years short on experience. "
            "Consider if their other strengths compensate."
        )
    if score.education_score < 0.6:
        recs.append("Candidate's education may not fully meet the stated requirements.")
    if score.semantic_score < 0.4:
        recs.append(
            "Low semantic similarity — the candidate's background may be in a different domain."
        )
    if not recs:
        recs.append("Candidate profile aligns well. Proceed to the next screening stage.")
    return recs


def _build_summary(
    score: DetailedScore,
    fit_label: str,
    exp_status: str,
) -> str:
    n_matched = len(score.matched_skills)
    n_required = len(score.required_skills)
    skill_pct = round((n_matched / n_required * 100) if n_required else 0, 1)

    lines = [
        f"Overall fit: {fit_label} (composite score {score.total_score:.0%}).",
        f"Semantic alignment with the job description: {score.semantic_score:.0%}.",
    ]

    if n_required:
        lines.append(
            f"Skill coverage: {n_matched}/{n_required} required skills matched ({skill_pct}%)."
        )
        if score.matched_skills:
            lines.append(f"Matched: {', '.join(score.matched_skills[:8])}.")
        if score.missing_skills:
            lines.append(f"Missing: {', '.join(score.missing_skills[:5])}.")

    lines.append(f"Experience: {exp_status}.")

    if score.education_entries:
        lines.append(f"Education: {score.education_entries[0]}.")

    return " ".join(lines)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def explain(score: DetailedScore) -> Explanation:
    """Build a full Explanation from a DetailedScore."""
    fit_label, fit_desc = classify_fit(score.total_score)
    n_req = len(score.required_skills)
    n_matched = len(score.matched_skills)
    skill_pct = round((n_matched / n_req * 100) if n_req else 0.0, 1)

    exp_status = _experience_status(
        score.experience_gap,
        score.required_experience,
        score.candidate_experience,
    )

    return Explanation(
        fit_category=fit_label,
        fit_description=fit_desc,
        summary=_build_summary(score, fit_label, exp_status),
        matched_skills=score.matched_skills,
        missing_skills=score.missing_skills,
        skill_match_pct=skill_pct,
        experience_status=exp_status,
        experience_gap=score.experience_gap,
        education_entries=score.education_entries,
        score_breakdown={
            "semantic":   score.semantic_score,
            "skill":      score.skill_score,
            "experience": score.experience_score,
            "education":  score.education_score,
            "total":      score.total_score,
        },
        recommendations=_recommendations(score),
    )
