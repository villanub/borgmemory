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
        <div className="mt-4 flex justify-center gap-6 text-xs text-[var(--text-muted)]">
          <a
            href="https://github.com/villanub/borgmemory"
            className="hover:text-[var(--text-primary)] transition-colors"
          >
            GitHub
          </a>
          <a
            href="https://github.com/villanub/borgmemory/issues"
            className="hover:text-[var(--text-primary)] transition-colors"
          >
            Issues
          </a>
          <a
            href="https://github.com/villanub/borgmemory/blob/main/LICENSE"
            className="hover:text-[var(--text-primary)] transition-colors"
          >
            Apache 2.0
          </a>
        </div>
        <p className="mx-auto mt-6 max-w-2xl text-xs text-[var(--text-muted)] opacity-70">
          Independent open-source project. All trademarks and product names
          are the property of their respective owners.
        </p>
      </div>
    </footer>
  );
}
