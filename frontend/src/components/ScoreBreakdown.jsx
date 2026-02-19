function Bar({ label, value, color = "bg-purple-500" }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-white/60">
        <span className="capitalize">{label}</span>
        <span className="font-medium text-white/90">{pct}%</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`${color} h-full rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function Pill({ text, type }) {
  const styles = {
    matched: "bg-green-400/15 text-green-300 border-green-400/20",
    missing: "bg-red-400/15 text-red-300 border-red-400/20",
    neutral: "bg-white/5 text-white/50 border-white/10",
  };
  return (
    <span
      className={`inline-block text-xs px-2 py-0.5 rounded-full border ${
        styles[type] || styles.neutral
      } mr-1 mb-1`}
    >
      {text}
    </span>
  );
}

export default function ScoreBreakdown({ item }) {
  if (!item) return null;

  const sb = item.score_breakdown || {};

  return (
    <section className="bg-white/5 border border-white/10 rounded-2xl p-5 space-y-5 overflow-y-auto max-h-[700px]">
      {/* Header */}
      <div>
        <h2 className="font-semibold text-base truncate">
          {item.candidate_name || item.filename}
        </h2>
        <p className="text-xs text-white/40 mt-0.5">{item.filename}</p>
      </div>

      {/* Fit badge + total */}
      <div className="flex items-center gap-3">
        <span className="text-3xl font-bold text-purple-300">
          {((item.total_score ?? 0) * 100).toFixed(1)}%
        </span>
        <div>
          <p className="text-sm font-medium">{item.fit_category}</p>
          <p className="text-xs text-white/50">{item.fit_description}</p>
        </div>
      </div>

      {/* Score bars */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider">
          Score Breakdown
        </h3>
        <Bar label="Semantic Similarity" value={sb.semantic} color="bg-purple-500" />
        <Bar label="Skill Match" value={sb.skill} color="bg-blue-500" />
        <Bar label="Experience" value={sb.experience} color="bg-amber-500" />
        <Bar label="Education" value={sb.education} color="bg-teal-500" />
      </div>

      {/* AI Summary */}
      {item.summary && (
        <div className="bg-white/5 rounded-xl p-3">
          <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-1.5">
            AI Summary
          </h3>
          <p className="text-sm text-white/80 leading-relaxed">{item.summary}</p>
        </div>
      )}

      {/* Skills */}
      <div>
        <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
          Skill Match — {item.skill_match_pct?.toFixed(0)}%
        </h3>
        {(item.matched_skills?.length ?? 0) > 0 && (
          <div className="mb-2">
            <p className="text-xs text-white/40 mb-1">✅ Matched</p>
            {item.matched_skills.map((s) => (
              <Pill key={s} text={s} type="matched" />
            ))}
          </div>
        )}
        {(item.missing_skills?.length ?? 0) > 0 && (
          <div>
            <p className="text-xs text-white/40 mb-1">❌ Missing</p>
            {item.missing_skills.map((s) => (
              <Pill key={s} text={s} type="missing" />
            ))}
          </div>
        )}
      </div>

      {/* Experience */}
      <div className="bg-white/5 rounded-xl p-3">
        <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-1">
          Experience
        </h3>
        <p className="text-sm">
          📈 {item.experience_status || "—"}
        </p>
      </div>

      {/* Education */}
      {(item.education?.length ?? 0) > 0 && (
        <div className="bg-white/5 rounded-xl p-3">
          <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-1">
            Education
          </h3>
          {item.education.slice(0, 4).map((e, i) => (
            <p key={i} className="text-sm text-white/70">
              {e}
            </p>
          ))}
        </div>
      )}

      {/* Recommendations */}
      {(item.recommendations?.length ?? 0) > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-2">
            🎯 Recommendations
          </h3>
          <ul className="space-y-1.5">
            {item.recommendations.map((rec, i) => (
              <li
                key={i}
                className="text-sm text-white/70 bg-white/5 rounded-lg px-3 py-2"
              >
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
