"""
Python ML Microservice — Resume Intelligence Engine
Exposes:
  POST /parse          – parse a PDF, store its embedding in FAISS
  POST /rank           – rank uploaded PDF resumes against a JD
  POST /rank/stored    – rank embeddings stored in FAISS against a JD
  GET  /health         – liveness probe
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Allow imports from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from embeddings import embed, get_store
from explainer import explain
from parser import parse_resume
from scorer import score_resume

app = FastAPI(
    title="Resume ML Service",
    version="2.0.0",
    description="NLP-powered resume parsing, scoring and explainability engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent / "tmp_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ───────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────

def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "resume.pdf").suffix or ".pdf"
    tmp = UPLOAD_DIR / (file.filename or "resume.pdf")
    with tmp.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return tmp


# ───────────────────────────────────────────────────────────────────────
# Endpoints
# ───────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "ml"}


@app.post("/parse")
async def parse_endpoint(
    resume: UploadFile = File(...),
    resume_id: str | None = Form(None),
):
    """
    Parse a PDF resume and store its embedding in FAISS.
    Returns structured resume data + embedding stored confirmation.
    """
    path = _save_upload(resume)
    try:
        parsed = parse_resume(str(path))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        path.unlink(missing_ok=True)

    rid = resume_id or path.stem
    vec = embed(parsed.cleaned_text or parsed.raw_text[:3000])

    store = get_store()
    store.add(
        rid,
        vec,
        meta={
            "filename": resume.filename,
            "name": parsed.name,
            "skills": parsed.skills[:20],
            "experience_years": parsed.experience_years,
        },
    )

    return {
        "resume_id": rid,
        "name": parsed.name,
        "email": parsed.email,
        "phone": parsed.phone,
        "skills": parsed.skills,
        "experience_years": parsed.experience_years,
        "experience_entries": parsed.experience_entries[:5],
        "education": parsed.education,
        "certifications": parsed.certifications,
        "projects": parsed.projects[:5],
        "sections_detected": list(parsed.sections.keys()),
        "embedding_stored": True,
    }


@app.post("/rank")
async def rank_endpoint(
    jd: str = Form(...),
    resumes: list[UploadFile] = File(...),
    weights: str = Form(None),   # JSON string {"semantic":0.5,"skill":0.25,...}
):
    """
    Upload PDFs + JD, get back a ranked list with detailed scores & explanations.
    """
    import json

    if not resumes:
        raise HTTPException(400, "No resume files provided.")
    if len(resumes) > 20:
        raise HTTPException(400, "Maximum 20 resumes per request.")

    weight_override = None
    if weights:
        try:
            weight_override = json.loads(weights)
        except Exception:
            raise HTTPException(400, "Invalid weights JSON.")

    jd_vec = embed(jd)
    results = []

    for upload in resumes:
        path = _save_upload(upload)
        try:
            parsed = parse_resume(str(path))
            score = score_resume(parsed, jd, jd_vec, weight_override)
            exp = explain(score)
        except Exception as e:
            results.append({"resume": upload.filename, "error": str(e)})
            continue
        finally:
            path.unlink(missing_ok=True)

        results.append({
            "resume": upload.filename,
            "candidate_name": parsed.name,
            "total_score": score.total_score,
            "fit_category": exp.fit_category,
            "fit_description": exp.fit_description,
            "summary": exp.summary,
            "score_breakdown": exp.score_breakdown,
            "matched_skills": exp.matched_skills,
            "missing_skills": exp.missing_skills,
            "skill_match_pct": exp.skill_match_pct,
            "experience_status": exp.experience_status,
            "experience_gap": exp.experience_gap,
            "education": exp.education_entries,
            "recommendations": exp.recommendations,
            "parsed": {
                "skills": parsed.skills,
                "experience_years": parsed.experience_years,
                "projects": parsed.projects[:5],
                "certifications": parsed.certifications,
            },
        })

    results.sort(key=lambda r: r.get("total_score", -1), reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return {"count": len(results), "rankings": results}


@app.post("/rank/stored")
async def rank_stored(
    jd: str = Form(...),
    top_k: int = Form(20),
):
    """
    Rank resumes already stored in FAISS against a new job description.
    Useful when resumes have been pre-indexed via /parse.
    """
    jd_vec = embed(jd)
    store = get_store()

    if store.count() == 0:
        return {"count": 0, "rankings": [], "message": "Vector store is empty. Upload resumes via /parse first."}

    matches = store.search(jd_vec, top_k=top_k)
    for i, m in enumerate(matches, 1):
        m["rank"] = i
        m["total_score"] = round(m.pop("score"), 4)

    return {"count": len(matches), "rankings": matches}


@app.delete("/store/{resume_id}")
async def delete_from_store(resume_id: str):
    store = get_store()
    store.remove(resume_id)
    return {"deleted": resume_id, "remaining": store.count()}


@app.get("/store/stats")
async def store_stats():
    store = get_store()
    return {"total_indexed": store.count(), "ids": store.get_all_ids()}
