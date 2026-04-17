"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/features", label: "Features" },
  { href: "/architecture", label: "Architecture" },
  { href: "/science", label: "Science" },
  { href: "/integrations", label: "Integrations" },
  { href: "/docs", label: "API Docs" },
  { href: "/benchmarks", label: "Benchmarks" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3 group">
          <span className="text-2xl font-bold text-[var(--accent-green)] glow-green-text group-hover:brightness-125 transition-all">
            ⬡
          </span>
          <span className="text-lg font-bold text-[var(--text-primary)]">
            Borg
          </span>
        </Link>

        <div className="flex items-center gap-8">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "text-[var(--accent-green)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <a
            href="https://github.com/villanub/borgmemory"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--accent-green)]/30 bg-[var(--accent-green)]/10 px-3 py-1 text-xs font-medium text-[var(--accent-green)] transition-all hover:bg-[var(--accent-green)]/20"
          >
            Open Source ↗
          </a>
        </div>
      </div>
    </nav>
  );
}
