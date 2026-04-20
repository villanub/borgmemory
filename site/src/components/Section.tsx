import type { ReactNode } from "react";

export function Section({
  id,
  num,
  title,
  sub,
  children,
  style,
}: {
  id?: string;
  num?: string;
  title: ReactNode;
  sub?: ReactNode;
  children?: ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <section className="block" id={id} style={style}>
      <div className="wrap">
        <div className="section-head">
          <div>
            {num && <div className="num">{num}</div>}
            <h2>{title}</h2>
          </div>
          {sub && <p className="sub">{sub}</p>}
        </div>
        {children}
      </div>
    </section>
  );
}

export function PageHero({
  num,
  title,
  lede,
  meta,
}: {
  num: string;
  title: ReactNode;
  lede?: ReactNode;
  meta?: { label: string; value: string }[];
}) {
  return (
    <header className="page-hero">
      <div className="wrap">
        <div className="num">{num}</div>
        <h1>{title}</h1>
        {lede && <p className="lede">{lede}</p>}
        {meta && (
          <div className="meta">
            {meta.map((m, i) => (
              <span key={i}>
                {m.label} · <b>{m.value}</b>
              </span>
            ))}
          </div>
        )}
      </div>
    </header>
  );
}

export function Crosslinks({
  left,
  right,
}: {
  left: { kicker: string; href: string; title: ReactNode; body: string };
  right: { kicker: string; href: string; title: ReactNode; body: string };
}) {
  return (
    <div className="wrap" style={{ padding: "60px 28px" }}>
      <div className="crosslinks">
        {[left, right].map((c, i) => (
          <a key={i} className="crosslink" href={c.href}>
            <span className="kicker">{c.kicker}</span>
            <h4>{c.title}</h4>
            <p>{c.body}</p>
            <span className="arrow">OPEN ↗</span>
          </a>
        ))}
      </div>
    </div>
  );
}
