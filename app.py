from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ranker import rank_resumes

app = FastAPI(title="Resume Checker")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploaded_resumes"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Resume Ranking API is running.", "hint": "Create static/index.html"}


def _safe_filename(name: str) -> str:
    name = os.path.basename(name)
    name = name.replace("\x00", "")
    return name or "resume.pdf"


def _unique_upload_path(upload_dir: Path, filename: str) -> Path:
    candidate = upload_dir / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    for i in range(2, 10_000):
        alt = upload_dir / f"{stem}_{i}{suffix}"
        if not alt.exists():
            return alt
    raise HTTPException(status_code=500, detail="Could not allocate a unique filename for upload.")

@app.post("/api/rank")
async def api_rank(
    jd: str = Form(...),
    resumes: list[UploadFile] = File([]),
    resumes_alt: list[UploadFile] = File([], alias="resumes[]"),
    resume1: UploadFile | None = File(None),
    resume2: UploadFile | None = File(None),
    resume3: UploadFile | None = File(None),
    resume4: UploadFile | None = File(None),
):
    single_resumes = [r for r in (resume1, resume2, resume3, resume4) if r is not None]
    all_resumes = [*resumes, *resumes_alt, *single_resumes]
    if not all_resumes:
        raise HTTPException(status_code=400, detail="No resumes uploaded. Use field name 'resumes' (repeat it for multiple files).")

    if len(all_resumes) > 4:
        raise HTTPException(status_code=400, detail="You can upload at most 4 resumes at a time.")

    file_paths: list[str] = []

    for resume in all_resumes:
        filename = _safe_filename(resume.filename)
        file_path = _unique_upload_path(UPLOAD_DIR, filename)
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        file_paths.append(str(file_path))

    ranked = rank_resumes(file_paths, jd)

    return {
        "rankings": [
            {"resume": os.path.basename(f), "score": round(score, 4)}
            for f, score in ranked
        ]
    }


@app.post("/rank")
async def rank_compat(
    jd: str = Form(...),
    resumes: list[UploadFile] = File(...),
):
    return await api_rank(jd=jd, resumes=resumes)
