import mongoose from "mongoose";

const rankItemSchema = new mongoose.Schema({
  resume: { type: mongoose.Schema.Types.ObjectId, ref: "Resume" },
  filename: String,
  candidate_name: String,
  rank: Number,
  total_score: Number,
  fit_category: String,
  fit_description: String,
  summary: String,
  score_breakdown: {
    semantic: Number,
    skill: Number,
    experience: Number,
    education: Number,
    total: Number,
  },
  matched_skills: [String],
  missing_skills: [String],
  skill_match_pct: Number,
  experience_status: String,
  experience_gap: Number,
  education: [String],
  recommendations: [String],
});

const rankResultSchema = new mongoose.Schema(
  {
    owner: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    jobDescription: { type: String, required: true },
    rankings: [rankItemSchema],
    weights: {
      semantic: { type: Number, default: 0.5 },
      skill: { type: Number, default: 0.25 },
      experience: { type: Number, default: 0.15 },
      education: { type: Number, default: 0.1 },
    },
  },
  { timestamps: true }
);

export default mongoose.model("RankResult", rankResultSchema);
