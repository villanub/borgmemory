"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/features", label: "Features" },
  { href: "/architecture", label: "Architecture" },
  { href: "/science", label: "Science" },
  { href: "/integrations", label: "Integrations" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/docs", label: "Docs" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="topnav">
      <div className="wrap inner">
        <Link href="/" className="mark">
          <span style={{ color: "var(--ink)", fontWeight: 600, letterSpacing: "-0.01em" }}>
            Borg
          </span>
          <span className="kicker" style={{ marginLeft: 8 }}>
            v2.1
          </span>
        </Link>

        <div className="links">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "active" : ""}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="right">
          <a
            className="pill"
            href="https://github.com/villanub/borgmemory"
            target="_blank"
            rel="noopener noreferrer"
          >
            <span className="dot" />
            github · open source
          </a>
          <Link className="btn primary" href="/#install">
            Install
          </Link>
        </div>
      </div>
    </nav>
  );
}
