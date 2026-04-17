export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg-primary)] py-12">
      <div className="mx-auto max-w-6xl px-6 text-center">
        <p className="text-sm text-[var(--text-muted)]">
          Project Borg — PostgreSQL-native memory compiler for AI workflows.
        </p>
        <p className="mt-2 text-xs text-[var(--text-muted)]">
          Built with PostgreSQL, pgvector, FastAPI, and Python.
        </p>
        <p className="mx-auto mt-6 max-w-3xl text-xs text-[var(--text-muted)] opacity-70">
          Independent open-source project. Not affiliated with, endorsed by, or
          connected to any company, brand, franchise, or intellectual property
          referenced by the project name or any term used here — including (but
          not limited to) Paramount Global, CBS Studios, the Star Trek
          franchise, Anthropic, OpenAI, Microsoft, or GitHub. All product
          names, trademarks, and registered trademarks are property of their
          respective owners.
        </p>
      </div>
    </footer>
  );
}
