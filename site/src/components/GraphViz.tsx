"use client";

import { useEffect, useState } from "react";

const W = 920;
const H = 460;

type Node = { id: string; label: string; type: "ent" | "ep"; x: number; y: number };

const NODES: Node[] = [
  { id: "WG", label: "Webhook Gateway", type: "ent", x: 160, y: 120 },
  { id: "OA", label: "OAuth Scope", type: "ent", x: 760, y: 130 },
  { id: "HM", label: "HMAC Pattern", type: "ent", x: 140, y: 340 },
  { id: "BJ", label: "Background Jobs", type: "ent", x: 470, y: 360 },
  { id: "PG", label: "Postgres", type: "ent", x: 620, y: 260 },
  { id: "EP", label: "ep · 2026-03-01 · claude-code", type: "ep", x: 400, y: 100 },
];

const EDGES: { from: string; to: string; pred: string }[] = [
  { from: "EP", to: "WG", pred: "mentions" },
  { from: "EP", to: "BJ", pred: "mentions" },
  { from: "WG", to: "HM", pred: "uses_pattern" },
  { from: "WG", to: "BJ", pred: "depends_on" },
  { from: "BJ", to: "PG", pred: "persists_to" },
  { from: "WG", to: "OA", pred: "validates" },
];

export function GraphViz() {
  const [t, setT] = useState(0);

  useEffect(() => {
    let raf: number;
    const loop = () => {
      setT((x) => x + 1);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  const pos = Object.fromEntries(NODES.map((n) => [n.id, n]));

  return (
    <div className="graph-wrap">
      <div className="gridbg" />
      <div className="caption">LIVE GRAPH NEIGHBORHOOD · ns=product-engineering</div>
      <svg viewBox={`0 0 ${W} ${H}`}>
        {EDGES.map((e, i) => {
          const a = pos[e.from];
          const b = pos[e.to];
          if (!a || !b) return null;
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          const phase = ((t + i * 28) % 240) / 240;
          const live = phase < 0.5;
          return (
            <g key={i}>
              <line
                className={"link " + (live ? "live" : "")}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
              />
              {live && (
                <circle
                  cx={a.x + (b.x - a.x) * phase * 2}
                  cy={a.y + (b.y - a.y) * phase * 2}
                  r="3"
                  fill="var(--accent)"
                />
              )}
              <text x={mx} y={my - 6} textAnchor="middle" className="pred">
                {e.pred}
              </text>
            </g>
          );
        })}
        {NODES.map((n) => (
          <g key={n.id} transform={`translate(${n.x} ${n.y})`}>
            {n.type === "ep" ? (
              <>
                <rect className="node-ep" x={-120} y={-16} width={240} height={32} rx={6} />
                <text className="ntext" y={5} textAnchor="middle">
                  {n.label}
                </text>
              </>
            ) : (
              <>
                <rect
                  className={"node-ent " + (n.id === "WG" ? "hl" : "")}
                  x={-76}
                  y={-16}
                  width={152}
                  height={32}
                  rx={6}
                />
                <text
                  className={"ntext " + (n.id === "WG" ? "hl" : "")}
                  y={5}
                  textAnchor="middle"
                >
                  {n.label}
                </text>
              </>
            )}
          </g>
        ))}
      </svg>
      <div className="legend">
        <span>
          <i className="ent" /> entity
        </span>
        <span>
          <i className="fact" /> fact (typed predicate)
        </span>
        <span>
          <i className="ep" /> episode
        </span>
      </div>
    </div>
  );
}
