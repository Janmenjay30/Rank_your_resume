import mongoose from "mongoose";

const resumeSchema = new mongoose.Schema(
  {
    owner: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true },
    filename: { type: String, required: true },
    originalName: { type: String, required: true },
    filePath: { type: String, required: true },
    fileSize: { type: Number },
    mlResumeId: { type: String },        // ID used in FAISS vector store
    parsed: {
      name: String,
      email: String,
      phone: String,
      skills: [String],
      experience_years: Number,
      education: [String],
      certifications: [String],
      projects: [String],
    },
    embeddingStored: { type: Boolean, default: false },
  },
  { timestamps: true }
);

export default mongoose.model("Resume", resumeSchema);
