const ITEMS = [
  "borg_think · classify → retrieve → rank → compile",
  "postgres-native · pgvector · recursive CTE",
  "24 canonical predicates",
  "3-pass entity resolution",
  "apache 2.0",
  "claude code · codex · copilot · kiro",
  "valid_from / valid_until supersession",
  "single-user · localhost · auth on roadmap",
  "15 tables · 1 function",
  "78% fewer stale facts vs RAG",
];

export function Ticker() {
  const doubled = [...ITEMS, ...ITEMS];
  return (
    <div className="ticker">
      <div className="track">
        {doubled.map((s, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 12 }}>
            <span className="dot">◆</span>
            <span>{s}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
