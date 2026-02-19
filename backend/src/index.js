import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import rateLimit from "express-rate-limit";
import { connectDB } from "./config/db.js";
import authRoutes from "./routes/auth.js";
import resumeRoutes from "./routes/resumes.js";
import rankRoutes from "./routes/rank.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// ── Middleware ───────────────────────────────
app.use(cors({ origin: process.env.FRONTEND_URL || "http://localhost:5173" }));
app.use(express.json());
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 200,
    message: { error: "Too many requests, please try again later." },
  })
);

// ── Routes ───────────────────────────────────
app.use("/api/auth", authRoutes);
app.use("/api/resumes", resumeRoutes);
app.use("/api/rank", rankRoutes);

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", service: "backend", ts: new Date().toISOString() });
});

// ── 404 + Error handlers ─────────────────────
app.use((_req, res) => res.status(404).json({ error: "Not found" }));

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || "Internal server error" });
});

// ── Start ─────────────────────────────────────
connectDB().then(() => {
  app.listen(PORT, () =>
    console.log(`Backend running on http://localhost:${PORT}`)
  );
});
