import Link from "next/link";

export function Footer() {
  const cols: { h: string; links: { label: string; href: string; external?: boolean }[] }[] = [
    {
      h: "Borg",
      links: [
        { label: "Features", href: "/features" },
        { label: "Architecture", href: "/architecture" },
        { label: "Science", href: "/science" },
        { label: "Benchmarks", href: "/benchmarks" },
        { label: "Docs", href: "/docs" },
      ],
    },
    {
      h: "Build",
      links: [
        { label: "GitHub", href: "https://github.com/villanub/borgmemory", external: true },
        { label: "Issues", href: "https://github.com/villanub/borgmemory/issues", external: true },
        {
          label: "Apache 2.0",
          href: "https://github.com/villanub/borgmemory/blob/main/LICENSE",
          external: true,
        },
      ],
    },
    {
      h: "Integrations",
      links: [
        { label: "Claude Code", href: "/integrations" },
        { label: "Codex CLI", href: "/integrations" },
        { label: "Copilot", href: "/integrations" },
        { label: "Kiro", href: "/integrations" },
      ],
    },
  ];

  return (
    <footer className="site">
      <div className="wrap inner">
        <div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 600,
              letterSpacing: "-0.01em",
              color: "var(--ink)",
              marginBottom: 12,
            }}
          >
            Borg
          </div>
          <p
            style={{
              color: "var(--ink-3)",
              maxWidth: 320,
              lineHeight: 1.55,
              margin: 0,
            }}
          >
            A memory stronghold for your AI coding agent. Open source,
            PostgreSQL-native, Apache 2.0.
          </p>
        </div>

        {cols.map((c) => (
          <div key={c.h}>
            <h5>{c.h}</h5>
            {c.links.map((l) =>
              l.external ? (
                <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer">
                  {l.label}
                </a>
              ) : (
                <Link key={l.label} href={l.href}>
                  {l.label}
                </Link>
              ),
            )}
          </div>
        ))}
      </div>

      <div className="wrap legal">
        <span>© 2026 Borg contributors · Apache 2.0</span>
        <span className="mono">built with postgres, not by it</span>
      </div>

      <div
        className="wrap"
        style={{
          marginTop: 18,
          fontSize: 11,
          color: "var(--ink-3)",
          opacity: 0.7,
          lineHeight: 1.6,
          maxWidth: 960,
        }}
      >
        Independent open-source project. All trademarks and product names are
        the property of their respective owners.
      </div>
    </footer>
  );
}
