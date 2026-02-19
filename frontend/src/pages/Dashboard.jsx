import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { rankUpload, getHistory } from "../api/index.js";
import ResultsTable from "../components/ResultsTable.jsx";

export default function Dashboard() {
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [jd, setJd] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);

  // Scoring weights
  const [weights, setWeights] = useState({
    semantic: 0.5,
    skill: 0.25,
    experience: 0.15,
    education: 0.1,
  });
  const [showWeights, setShowWeights] = useState(false);

  useEffect(() => {
    getHistory()
      .then((r) => setHistory(r.data))
      .catch(() => {});
  }, []);

  const handleFiles = (e) => {
    const selected = Array.from(e.target.files || []);
    setFiles(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    );
    setFiles(dropped);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResults(null);

    if (!jd.trim()) return setError("Paste a job description.");
    if (files.length === 0) return setError("Upload at least 1 resume PDF.");
    if (files.length > 20) return setError("Max 20 resumes per request.");

    const fd = new FormData();
    fd.append("jd", jd);
    fd.append("weights", JSON.stringify(weights));
    files.forEach((f) => fd.append("resumes", f, f.name));

    setLoading(true);
    try {
      const { data } = await rankUpload(fd);
      setResults(data);
      // Refresh history
      getHistory()
        .then((r) => setHistory(r.data))
        .catch(() => {});
    } catch (err) {
      setError(err.response?.data?.error || err.message || "Ranking failed.");
    } finally {
      setLoading(false);
    }
  };

  const totalW = Object.values(weights).reduce((a, b) => a + b, 0);
  const weightsValid = Math.abs(totalW - 1) < 0.01;

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Resume Ranking Dashboard</h1>
        <p className="text-white/50 text-sm mt-1">
          Upload resumes + paste a job description to get AI-powered rankings.
        </p>
      </div>

      {/* Form card */}
      <section className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-5">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* JD */}
          <label className="block space-y-2">
            <span className="font-semibold text-sm">Job Description</span>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              rows={10}
              placeholder="Paste the full job description here…"
              className="w-full bg-white/5 border border-white/15 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y"
            />
          </label>

          {/* File drop zone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-white/20 hover:border-purple-400 rounded-xl p-8 text-center cursor-pointer transition"
          >
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              multiple
              onChange={handleFiles}
              className="hidden"
            />
            {files.length === 0 ? (
              <>
                <p className="text-white/60 text-sm">
                  Drag &amp; drop PDF resumes here, or click to select
                </p>
                <p className="text-white/30 text-xs mt-1">Up to 20 files</p>
              </>
            ) : (
              <div className="space-y-1">
                <p className="text-green-400 text-sm font-medium">
                  {files.length} file{files.length > 1 ? "s" : ""} selected
                </p>
                <ul className="text-white/50 text-xs space-y-0.5">
                  {files.map((f, i) => (
                    <li key={i}>{f.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Weights (collapsible) */}
          <div>
            <button
              type="button"
              onClick={() => setShowWeights((s) => !s)}
              className="text-sm text-purple-400 hover:underline"
            >
              {showWeights ? "▲ Hide" : "▼ Adjust"} scoring weights
            </button>

            {showWeights && (
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Object.entries(weights).map(([key, val]) => (
                  <label key={key} className="block space-y-1">
                    <span className="text-xs text-white/60 capitalize">{key}</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.05"
                      value={val}
                      onChange={(e) =>
                        setWeights((w) => ({
                          ...w,
                          [key]: parseFloat(e.target.value) || 0,
                        }))
                      }
                      className="w-full bg-white/5 border border-white/15 rounded-lg px-2 py-1.5 text-sm text-center"
                    />
                  </label>
                ))}
                <div className="col-span-full">
                  <span
                    className={`text-xs ${weightsValid ? "text-green-400" : "text-red-400"}`}
                  >
                    Sum: {totalW.toFixed(2)} {weightsValid ? "✓" : "(must equal 1.00)"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-xl text-sm font-semibold transition"
            >
              {loading ? "Ranking…" : "Rank Resumes"}
            </button>
            <button
              type="button"
              onClick={() => {
                setJd("");
                setFiles([]);
                setResults(null);
                setError("");
              }}
              className="px-6 py-2.5 border border-white/15 hover:bg-white/5 rounded-xl text-sm transition"
            >
              Clear
            </button>
          </div>
        </form>
      </section>

      {/* Results */}
      {results && (
        <section className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg">
              Results
              <span className="ml-2 text-sm text-white/40 font-normal">
                {results.count} resume{results.count !== 1 ? "s" : ""} ranked
              </span>
            </h2>
            {results.resultId && (
              <button
                onClick={() => navigate(`/results/${results.resultId}`)}
                className="text-sm text-purple-400 hover:underline"
              >
                Full detail →
              </button>
            )}
          </div>
          <ResultsTable rankings={results.rankings} onRowClick={(id) => navigate(`/results/${id}`)} />
        </section>
      )}

      {/* History */}
      {history.length > 0 && (
        <section className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-3">
          <h2 className="font-semibold text-lg">Past Sessions</h2>
          <div className="space-y-2">
            {history.map((h) => (
              <button
                key={h._id}
                onClick={() => navigate(`/results/${h._id}`)}
                className="w-full text-left bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl px-4 py-3 transition"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate max-w-[60%]">
                    {h.jobDescription?.slice(0, 80)}…
                  </p>
                  <span className="text-xs text-white/40">
                    {new Date(h.createdAt).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-white/40 mt-0.5">
                  {h.rankings?.length} resume{h.rankings?.length !== 1 ? "s" : ""}
                </p>
              </button>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
