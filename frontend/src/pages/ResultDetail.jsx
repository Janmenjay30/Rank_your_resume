import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getHistoryItem } from "../api/index.js";
import ScoreBreakdown from "../components/ScoreBreakdown.jsx";

export default function ResultDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistoryItem(id)
      .then((r) => {
        setResult(r.data);
        if (r.data.rankings?.length) setSelected(r.data.rankings[0]);
      })
      .catch(() => setError("Could not load result."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center text-white/40">
        Loading…
      </div>
    );

  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center text-red-400">
        {error}
      </div>
    );

  return (
    <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-white/50 hover:text-white transition"
        >
          ← Back
        </button>
        <div>
          <h1 className="text-xl font-bold">Ranking Detail</h1>
          <p className="text-xs text-white/40 mt-0.5">
            {new Date(result.createdAt).toLocaleString()} · {result.rankings?.length} resumes
          </p>
        </div>
      </div>

      {/* Job Description preview */}
      <section className="bg-white/5 border border-white/10 rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-white/60 mb-2">Job Description</h2>
        <p className="text-sm text-white/80 whitespace-pre-wrap line-clamp-6">
          {result.jobDescription}
        </p>
      </section>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Rankings list */}
        <section className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-2">
          <h2 className="font-semibold mb-3">Ranked Resumes</h2>
          {result.rankings?.map((r) => (
            <button
              key={r.filename + r.rank}
              onClick={() => setSelected(r)}
              className={`w-full text-left rounded-xl px-4 py-3 border transition ${
                selected?.filename === r.filename && selected?.rank === r.rank
                  ? "border-purple-500 bg-purple-500/15"
                  : "border-white/10 hover:bg-white/5"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                      r.rank === 1
                        ? "bg-yellow-500 text-black"
                        : r.rank === 2
                        ? "bg-gray-300 text-black"
                        : r.rank === 3
                        ? "bg-amber-600 text-black"
                        : "bg-white/10 text-white/60"
                    }`}
                  >
                    {r.rank}
                  </span>
                  <div>
                    <p className="text-sm font-medium truncate max-w-[180px]">
                      {r.candidate_name || r.filename}
                    </p>
                    <p className="text-xs text-white/40">{r.filename}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-purple-300">
                    {(r.total_score * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-white/40">{r.fit_category}</p>
                </div>
              </div>
            </button>
          ))}
        </section>

        {/* Detail panel */}
        {selected && <ScoreBreakdown item={selected} />}
      </div>
    </main>
  );
}
