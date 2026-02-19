# Resume Checker — Full Stack AI System

An enterprise-grade resume ranking platform built as a microservice architecture.

```
Frontend (React + Vite)
        ↓
Node.js Backend (API + JWT Auth + MongoDB)
        ↓
Python ML Service (NLP Engine + FastAPI)
        ↓  ↓
Sentence Transformers   FAISS Vector DB
```

---

## Project Structure

```
resumeChecker/
├── frontend/          # React + Vite + Tailwind
├── backend/           # Node.js + Express + MongoDB
├── ml_service/        # Python FastAPI + NLP engine
│   ├── app.py         # API endpoints
│   ├── parser.py      # Resume parsing pipeline
│   ├── embeddings.py  # Sentence-transformers + FAISS
│   ├── scorer.py      # Weighted scoring algorithm
│   ├── explainer.py   # Explainability engine
│   └── skill_db.py    # Skill taxonomy database
├── docker-compose.yml # Orchestrate all services
└── static/            # Legacy single-page UI (still works)
```

---

## Quick Start (Docker)

```bash
cp .env.example .env
docker-compose up --build
```

| Service      | URL                          |
|--------------|------------------------------|
| Frontend     | http://localhost:80           |
| Backend API  | http://localhost:3001/api     |
| ML Service   | http://localhost:8001/docs    |
| MongoDB      | mongodb://localhost:27017     |

---

## Local Dev (without Docker)

### 1 — ML Service (Python)
```powershell
cd ml_service
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### 2 — Backend (Node.js)
```powershell
cd backend
cp .env.example .env        # edit values
npm install
npm run dev
```

### 3 — Frontend (React)
```powershell
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

---

## ML Pipeline

### Scoring Formula
```
Score = 0.50 × Semantic Similarity
      + 0.25 × Skill Match
      + 0.15 × Experience Match
      + 0.10 × Education Match
```
Weights are fully adjustable per request.

### Explainability Output
Every ranked resume returns:
- ✅ Matched skills
- ❌ Missing skills
- 📈 Experience gap
- 🎯 Fit category (Excellent / Strong / Good / Partial / Weak)
- 📝 AI-generated summary paragraph

### Vector Database (FAISS)
Pre-parse and index large resume batches via `POST /parse`.
Then rank on demand with `POST /rank/stored` (no re-embedding).

---

## Backend API

| Method | Endpoint                    | Auth | Description                          |
|--------|-----------------------------|------|--------------------------------------|
| POST   | /api/auth/register          | —    | Create account                       |
| POST   | /api/auth/login             | —    | Get JWT token                        |
| GET    | /api/auth/me                | JWT  | Current user                         |
| GET    | /api/resumes                | JWT  | List uploaded resumes                |
| POST   | /api/resumes/upload         | JWT  | Upload + parse a resume PDF          |
| DELETE | /api/resumes/:id            | JWT  | Delete resume                        |
| POST   | /api/rank/upload            | JWT  | Upload PDFs + JD → ranked results    |
| POST   | /api/rank/stored            | JWT  | Rank FAISS-indexed resumes vs JD     |
| GET    | /api/rank/history           | JWT  | Past ranking sessions                |
| GET    | /api/rank/history/:id       | JWT  | Full detail of a session             |

---

## Legacy API (original single-service)

```
POST /api/rank
  jd      — job description text
  resumes — up to 4 PDF files
```
Still available via `uvicorn app:app --reload` from the root.
