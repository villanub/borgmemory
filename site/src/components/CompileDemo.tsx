"use client";

import { useEffect, useState, Fragment } from "react";

type TraceStep = { label: React.ReactNode; meta: string; dur: number };

const TRACE: TraceStep[] = [
  {
    label: (
      <>
        Classify intent <b>· debug</b>
      </>
    ),
    meta: "0.92 / 0.31",
    dur: 900,
  },
  {
    label: (
      <>
        Retrieve across <b>3 strategies</b>
      </>
    ),
    meta: "graph · episodes · facts",
    dur: 1100,
  },
  {
    label: (
      <>
        Score <b>14 candidates</b>, select <b>6</b>
      </>
    ),
    meta: "relevance · recency · stability · prov.",
    dur: 1100,
  },
  {
    label: (
      <>
        Compile XML for <b>claude</b>
      </>
    ),
    meta: "1,840 tokens",
    dur: 700,
  },
  { label: <>Audit log + access tracking</>, meta: "12 ms", dur: 500 },
];

const OUTPUT_LINES: { tokens: { t: string; c?: string }[] }[] = [
  {
    tokens: [
      { t: "<" },
      { t: "borg", c: "tag" },
      { t: " " },
      { t: "model", c: "attr" },
      { t: '="' },
      { t: "claude", c: "val" },
      { t: '" ' },
      { t: "ns", c: "attr" },
      { t: '="' },
      { t: "product-engineering", c: "val" },
      { t: '" ' },
      { t: "task", c: "attr" },
      { t: '="' },
      { t: "debug", c: "val" },
      { t: '">' },
    ],
  },
  { tokens: [{ t: "  <" }, { t: "knowledge", c: "tag" }, { t: ">" }] },
  {
    tokens: [
      { t: "    <" },
      { t: "fact", c: "tag" },
      { t: " " },
      { t: "status", c: "attr" },
      { t: '="' },
      { t: "observed", c: "val" },
      { t: '" ' },
      { t: "salience", c: "attr" },
      { t: '="' },
      { t: "0.94", c: "val" },
      { t: '">Webhook gateway verifies HMAC before enqueue.</' },
      { t: "fact", c: "tag" },
      { t: ">" },
    ],
  },
  {
    tokens: [
      { t: "    <" },
      { t: "fact", c: "tag" },
      { t: " " },
      { t: "status", c: "attr" },
      { t: '="' },
      { t: "observed", c: "val" },
      { t: '" ' },
      { t: "salience", c: "attr" },
      { t: '="' },
      { t: "0.88", c: "val" },
      { t: '">Background jobs retry with exp. backoff.</' },
      { t: "fact", c: "tag" },
      { t: ">" },
    ],
  },
  { tokens: [{ t: "  </" }, { t: "knowledge", c: "tag" }, { t: ">" }] },
  { tokens: [{ t: "  <" }, { t: "episodes", c: "tag" }, { t: ">" }] },
  {
    tokens: [
      { t: "    <" },
      { t: "episode", c: "tag" },
      { t: " " },
      { t: "source", c: "attr" },
      { t: '="' },
      { t: "claude-code", c: "val" },
      { t: '" ' },
      { t: "date", c: "attr" },
      { t: '="' },
      { t: "2026-03-01", c: "val" },
      { t: '">Fixed duplicate webhook delivery during replay.</' },
      { t: "episode", c: "tag" },
      { t: ">" },
    ],
  },
  {
    tokens: [
      { t: "    <" },
      { t: "episode", c: "tag" },
      { t: " " },
      { t: "source", c: "attr" },
      { t: '="' },
      { t: "claude-code", c: "val" },
      { t: '" ' },
      { t: "date", c: "attr" },
      { t: '="' },
      { t: "2026-02-14", c: "val" },
      { t: '">Resolved OAuth scope mismatch in staging.</' },
      { t: "episode", c: "tag" },
      { t: ">" },
    ],
  },
  { tokens: [{ t: "  </" }, { t: "episodes", c: "tag" }, { t: ">" }] },
  { tokens: [{ t: "  <" }, { t: "patterns", c: "tag" }, { t: ">" }] },
  {
    tokens: [
      { t: "    <" },
      { t: "procedure", c: "tag" },
      { t: " " },
      { t: "confidence", c: "attr" },
      { t: '="' },
      { t: "0.92", c: "val" },
      { t: '">Debug auth: verify scopes, inspect token aud + iss.</' },
      { t: "procedure", c: "tag" },
      { t: ">" },
    ],
  },
  { tokens: [{ t: "  </" }, { t: "patterns", c: "tag" }, { t: ">" }] },
  { tokens: [{ t: "</" }, { t: "borg", c: "tag" }, { t: ">" }] },
];

const TARGET_QUERY = "debug webhook delivery timeout";

export function CompileDemo() {
  const [step, setStep] = useState(-1);
  const [running, setRunning] = useState(false);
  const [query, setQuery] = useState("");
  const [showOut, setShowOut] = useState(false);

  const run = () => {
    if (running) return;
    setRunning(true);
    setShowOut(false);
    setStep(-1);
    setQuery("");

    let i = 0;
    const type = () => {
      if (i <= TARGET_QUERY.length) {
        setQuery(TARGET_QUERY.slice(0, i));
        i++;
        window.setTimeout(type, 35);
      } else {
        advance(0);
      }
    };
    const advance = (k: number) => {
      if (k >= TRACE.length) {
        setShowOut(true);
        setRunning(false);
        return;
      }
      setStep(k);
      window.setTimeout(() => advance(k + 1), TRACE[k].dur);
    };
    type();
  };

  useEffect(() => {
    const t = window.setTimeout(run, 600);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="compile">
      <div className="left">
        <span className="qlabel">Query from claude-code · ns: product-engineering</span>
        <div className="qbox">
          {query}
          {running && query.length < TARGET_QUERY.length ? <span className="caret" /> : null}
        </div>
        <div className="chips">
          <span className={"chip " + (step >= 0 ? "live" : "")}>task: debug</span>
          <span className={"chip " + (step >= 1 ? "live" : "")}>graph_neighborhood</span>
          <span className={"chip " + (step >= 1 ? "live" : "")}>episode_recall</span>
          <span className={"chip " + (step >= 1 ? "live" : "")}>fact_lookup</span>
        </div>
        <div style={{ marginTop: "auto", display: "flex", gap: 10 }}>
          <button
            className="btn primary"
            onClick={run}
            disabled={running}
            type="button"
          >
            {running ? "compiling…" : "Replay"}
          </button>
          <a className="btn" href="#mcp">
            See the 3 MCP tools
          </a>
        </div>
      </div>

      <div className="right">
        {TRACE.map((t, i) => (
          <div
            key={i}
            className={"trace-row " + (step === i ? "active" : step > i ? "done" : "")}
          >
            <span className="dot" />
            <div>
              <div className="label">{t.label}</div>
              <div className="bar">
                <span />
              </div>
            </div>
            <span className="meta">{t.meta}</span>
          </div>
        ))}
        {showOut && (
          <pre className="output-pre">
            {OUTPUT_LINES.map((line, li) => (
              <Fragment key={li}>
                {line.tokens.map((tok, ti) =>
                  tok.c ? (
                    <span key={ti} className={tok.c}>
                      {tok.t}
                    </span>
                  ) : (
                    <Fragment key={ti}>{tok.t}</Fragment>
                  ),
                )}
                {"\n"}
              </Fragment>
            ))}
          </pre>
        )}
      </div>
    </div>
  );
}
