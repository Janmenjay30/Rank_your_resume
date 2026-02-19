import mongoose from "mongoose";

export async function connectDB() {
  const uri = process.env.MONGO_URI || "mongodb://localhost:27017/resumechecker";
  try {
    await mongoose.connect(uri);
    console.log("MongoDB connected:", uri.replace(/\/\/.*@/, "//***@"));
  } catch (err) {
    console.error("MongoDB connection error:", err.message);
    process.exit(1);
  }
}
