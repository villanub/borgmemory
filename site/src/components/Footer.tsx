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
      </div>
    </footer>
  );
}
