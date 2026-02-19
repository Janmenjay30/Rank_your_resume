import { Router } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { v4 as uuidv4 } from "uuid";
import FormData from "form-data";
import fetch from "node-fetch";
import { protect } from "../middleware/auth.js";
import Resume from "../models/Resume.js";

const router = Router();
const ML_URL = process.env.ML_SERVICE_URL || "http://localhost:8001";

// ── Multer setup ─────────────────────────────
const UPLOAD_DIR = path.resolve("uploads");
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${uuidv4()}${ext}`);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: (_req, file, cb) => {
    if (file.mimetype === "application/pdf") cb(null, true);
    else cb(new Error("Only PDF files are allowed."));
  },
});

// ── Routes ───────────────────────────────────

// GET /api/resumes — list all resumes for current user
router.get("/", protect, async (req, res, next) => {
  try {
    const resumes = await Resume.find({ owner: req.user.id })
      .select("-filePath")
      .sort({ createdAt: -1 });
    res.json(resumes);
  } catch (err) {
    next(err);
  }
});

// POST /api/resumes/upload — upload + parse a single resume
router.post("/upload", protect, upload.single("resume"), async (req, res, next) => {
  if (!req.file)
    return res.status(400).json({ error: "No file uploaded." });

  const resumeId = uuidv4();

  try {
    // Forward to ML service for parsing + embedding storage
    const form = new FormData();
    form.append("resume", fs.createReadStream(req.file.path), req.file.originalname);
    form.append("resume_id", resumeId);

    let parsed = null;
    try {
      const mlRes = await fetch(`${ML_URL}/parse`, { method: "POST", body: form });
      if (mlRes.ok) parsed = await mlRes.json();
    } catch {
      // ML service unavailable — store file metadata only
    }

    const doc = await Resume.create({
      owner: req.user.id,
      filename: req.file.filename,
      originalName: req.file.originalname,
      filePath: req.file.path,
      fileSize: req.file.size,
      mlResumeId: resumeId,
      parsed: parsed
        ? {
            name: parsed.name,
            email: parsed.email,
            phone: parsed.phone,
            skills: parsed.skills,
            experience_years: parsed.experience_years,
            education: parsed.education,
            certifications: parsed.certifications,
            projects: parsed.projects,
          }
        : undefined,
      embeddingStored: !!parsed?.embedding_stored,
    });

    res.status(201).json({ id: doc._id, mlResumeId: resumeId, parsed: doc.parsed });
  } catch (err) {
    // Clean up uploaded file on error
    fs.unlink(req.file.path, () => {});
    next(err);
  }
});

// DELETE /api/resumes/:id
router.delete("/:id", protect, async (req, res, next) => {
  try {
    const doc = await Resume.findOne({ _id: req.params.id, owner: req.user.id });
    if (!doc) return res.status(404).json({ error: "Resume not found." });

    // Remove file
    fs.unlink(doc.filePath, () => {});

    // Remove from FAISS
    if (doc.mlResumeId) {
      try {
        await fetch(`${ML_URL}/store/${doc.mlResumeId}`, { method: "DELETE" });
      } catch {}
    }

    await doc.deleteOne();
    res.json({ deleted: doc._id });
  } catch (err) {
    next(err);
  }
});

export default router;
