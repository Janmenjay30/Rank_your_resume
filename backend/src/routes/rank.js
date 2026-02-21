import { Router } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import FormData from "form-data";
import fetch from "node-fetch";
import { protect } from "../middleware/auth.js";
import RankResult from "../models/RankResult.js";

const router = Router();
const ML_URL = process.env.ML_SERVICE_URL || "http://localhost:8001";

// Temp storage for files attached to rank requests
const TMP_DIR = path.resolve("tmp_rank");
fs.mkdirSync(TMP_DIR, { recursive: true });

const tmpUpload = multer({
  dest: TMP_DIR,
  limits: { fileSize: 10 * 1024 * 1024, files: 20 },
  fileFilter: (_req, file, cb) => {
    if (file.mimetype === "application/pdf") cb(null, true);
    else cb(new Error("Only PDF files are allowed."));
  },
});

/**
 * POST /api/rank/upload
 * Upload PDFs + JD directly → get ranked results immediately.
 * Body (multipart):
 *   jd        {string}  - job description
 *   resumes   {files}   - up to 20 PDF files
 *   weights   {string}  - optional JSON of scoring weights
 */
router.post("/upload", protect, tmpUpload.array("resumes", 20), async (req, res, next) => {
  const files = req.files || [];
  const { jd, weights } = req.body;

  if (!jd) {
    files.forEach((f) => fs.unlink(f.path, () => {}));
    return res.status(400).json({ error: "jd (job description) is required." });
  }
  if (files.length === 0) {
    return res.status(400).json({ error: "At least one resume file is required." });
  }

  try {
    const form = new FormData();
    form.append("jd", jd);
    if (weights) form.append("weights", weights);
    for (const file of files) {
      form.append("resumes", fs.createReadStream(file.path), file.originalname);
    }

    const mlRes = await fetch(`${ML_URL}/rank`, { method: "POST", body: form });
    if (!mlRes.ok) {
      const err = await mlRes.text();
      throw Object.assign(new Error(err), { status: mlRes.status });
    }

    const data = await mlRes.json();

    // Persist result to MongoDB
    // Strip 'resume' field from ML response (it's a filename string, not an ObjectId)
    const cleanRankings = (data.rankings || []).map(({ resume: _r, ...rest }) => rest);
    const saved = await RankResult.create({
      owner: req.user.id,
      jobDescription: jd,
      rankings: cleanRankings,
      weights: weights ? JSON.parse(weights) : undefined,
    });

    res.json({ resultId: saved._id, ...data });
  } catch (err) {
    next(err);
  } finally {
    files.forEach((f) => fs.unlink(f.path, () => {}));
  }
});

/**
 * POST /api/rank/stored
 * Rank previously parsed & indexed resumes using FAISS.
 * Body (JSON):
 *   jd     {string} - job description
 *   top_k  {number} - how many results (default 20)
 */
router.post("/stored", protect, async (req, res, next) => {
  const { jd, top_k = 20 } = req.body;
  if (!jd) return res.status(400).json({ error: "jd is required." });

  try {
    const form = new FormData();
    form.append("jd", jd);
    form.append("top_k", String(top_k));

    const mlRes = await fetch(`${ML_URL}/rank/stored`, { method: "POST", body: form });
    if (!mlRes.ok) throw new Error(await mlRes.text());

    const data = await mlRes.json();

    const cleanRankings = (data.rankings || []).map(({ resume: _r, ...rest }) => rest);
    const saved = await RankResult.create({
      owner: req.user.id,
      jobDescription: jd,
      rankings: cleanRankings,
    });

    res.json({ resultId: saved._id, ...data });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/rank/history
 * Return past ranking sessions for the current user.
 */
router.get("/history", protect, async (req, res, next) => {
  try {
    const results = await RankResult.find({ owner: req.user.id })
      .select("jobDescription rankings.rank rankings.filename rankings.total_score rankings.fit_category createdAt")
      .sort({ createdAt: -1 })
      .limit(50);
    res.json(results);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/rank/history/:id
 * Full detail of a past ranking session.
 */
router.get("/history/:id", protect, async (req, res, next) => {
  try {
    const result = await RankResult.findOne({ _id: req.params.id, owner: req.user.id });
    if (!result) return res.status(404).json({ error: "Not found." });
    res.json(result);
  } catch (err) {
    next(err);
  }
});

export default router;
