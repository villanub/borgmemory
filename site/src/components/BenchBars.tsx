"use client";

import { useEffect, useRef, useState } from "react";

type Col = {
  k: string;
  name: string;
  sub: string;
  task: number;
  prec: number;
  stale: number;
  us: boolean;
};

const COLS: Col[] = [
  {
    k: "A",
    name: "No memory",
    sub: "Baseline — every session starts from zero.",
    task: 0,
    prec: 0.06,
    stale: 0,
    us: false,
  },
  {
    k: "B",
    name: "Top-10 vector RAG",
    sub: "Standard similarity search over conversation chunks.",
    task: 8,
    prec: 0.81,
    stale: 0.115,
    us: false,
  },
  {
    k: "C",
    name: "Borg · compiled",
    sub: "Full pipeline: classify, retrieve, rank on 4 dims, compile.",
    task: 10,
    prec: 0.913,
    stale: 0.025,
    us: true,
  },
];

export function BenchBars() {
  const [seen, setSeen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setSeen(true);
        });
      },
      { threshold: 0.2 },
    );
    io.observe(node);
    return () => io.disconnect();
  }, []);

  return (
    <div className="bench" ref={ref}>
      {COLS.map((c) => (
        <div key={c.k} className={"col " + (c.us ? "us" : "")}>
          <span className="label">Condition {c.k}</span>
          <h4>{c.name}</h4>
          <p
            style={{
              color: "var(--ink-2)",
              fontSize: 14,
              lineHeight: 1.55,
              margin: 0,
            }}
          >
            {c.sub}
          </p>

          <div className="metric">
            <span className="k">Task success</span>
            <span className="v">
              {c.task}
              <small>/ 10</small>
            </span>
            <div className="bar-wrap">
              <span style={{ width: seen ? `${c.task * 10}%` : 0 }} />
            </div>
          </div>

          <div className="metric">
            <span className="k">Retrieval precision</span>
            <span className="v">
              {(c.prec * 100).toFixed(1)}
              <small>%</small>
            </span>
            <div className="bar-wrap">
              <span style={{ width: seen ? `${c.prec * 100}%` : 0 }} />
            </div>
          </div>

          <div className="metric">
            <span className="k">Stale-fact rate</span>
            <span className="v">
              {(c.stale * 100).toFixed(1)}
              <small>%</small>
            </span>
            <div className="bar-wrap">
              <span
                style={{
                  width: seen ? `${Math.min(c.stale * 400, 100)}%` : 0,
                  background: c.us ? "var(--accent)" : "var(--danger)",
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
