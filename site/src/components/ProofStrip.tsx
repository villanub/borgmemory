export function ProofStrip() {
  return (
    <div className="proof">
      <div className="cell">
        <span className="caption">TASK SUCCESS — ENGINEERING-TASK BENCH</span>
        <span className="num">
          10<span className="unit">/ 10</span>
        </span>
        <span className="label">
          Borg-compiled context completes every task. No-memory baseline: 0/10.
        </span>
      </div>
      <div className="cell">
        <span className="caption">RETRIEVAL PRECISION</span>
        <span className="num">
          91.3<span className="unit">%</span>
        </span>
        <span className="label">
          +12.7 pts over top-10 vector RAG. Measured against labeled ground-truth.
        </span>
      </div>
      <div className="cell">
        <span className="caption">STALE-FACT RATE</span>
        <span className="num">
          −78<span className="unit">%</span>
        </span>
        <span className="label">
          Temporal supersession keeps contradicted decisions out of compiled context.
        </span>
      </div>
    </div>
  );
}
