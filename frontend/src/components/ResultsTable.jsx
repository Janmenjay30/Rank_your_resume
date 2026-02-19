const FIT_COLORS = {
  "Excellent Match": "text-emerald-400 bg-emerald-400/10",
  "Strong Match": "text-green-400 bg-green-400/10",
  "Good Match": "text-yellow-400 bg-yellow-400/10",
  "Partial Match": "text-orange-400 bg-orange-400/10",
  "Weak Match": "text-red-400 bg-red-400/10",
};

export default function ResultsTable({ rankings, onRowClick }) {
  if (!rankings || rankings.length === 0) {
    return (
      <div className="text-center text-white/30 text-sm py-8">No results yet.</div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-white/10">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-white/40 text-xs uppercase tracking-wide">
            <th className="text-left px-4 py-3 w-10">#</th>
            <th className="text-left px-4 py-3">Resume</th>
            <th className="text-left px-4 py-3 hidden sm:table-cell">Candidate</th>
            <th className="text-right px-4 py-3">Score</th>
            <th className="text-center px-4 py-3 hidden md:table-cell">Fit</th>
            <th className="text-right px-4 py-3 hidden lg:table-cell">Skills</th>
            <th className="text-right px-4 py-3 hidden lg:table-cell">Semantic</th>
          </tr>
        </thead>
        <tbody>
          {rankings.map((r, i) => (
            <tr
              key={i}
              onClick={() => onRowClick?.(r._id)}
              className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition"
            >
              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                    r.rank === 1
                      ? "bg-yellow-500 text-black"
                      : r.rank === 2
                      ? "bg-gray-300 text-black"
                      : r.rank === 3
                      ? "bg-amber-600 text-black"
                      : "bg-white/10 text-white/50"
                  }`}
                >
                  {r.rank}
                </span>
              </td>
              <td className="px-4 py-3 font-medium truncate max-w-[160px]">{r.filename}</td>
              <td className="px-4 py-3 text-white/60 hidden sm:table-cell truncate max-w-[140px]">
                {r.candidate_name || "—"}
              </td>
              <td className="px-4 py-3 text-right font-bold text-purple-300">
                {(r.total_score * 100).toFixed(1)}%
              </td>
              <td className="px-4 py-3 text-center hidden md:table-cell">
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    FIT_COLORS[r.fit_category] || "text-white/40 bg-white/5"
                  }`}
                >
                  {r.fit_category || "—"}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-white/50 hidden lg:table-cell">
                {r.skill_match_pct != null ? `${r.skill_match_pct.toFixed(0)}%` : "—"}
              </td>
              <td className="px-4 py-3 text-right text-white/50 hidden lg:table-cell">
                {r.score_breakdown?.semantic != null
                  ? `${(r.score_breakdown.semantic * 100).toFixed(1)}%`
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
