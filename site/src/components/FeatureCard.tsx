import { ReactNode } from "react";

interface FeatureCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  detail?: string;
}

export function FeatureCard({ icon, title, description, detail }: FeatureCardProps) {
  return (
    <div className="group rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-6 transition-all hover:border-[var(--accent-green)]/30 hover:bg-[var(--bg-card-hover)]">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--accent-green)]/10 text-[var(--accent-green)] text-xl">
        {icon}
      </div>
      <h3 className="mb-2 text-lg font-semibold text-[var(--text-primary)]">
        {title}
      </h3>
      <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
        {description}
      </p>
      {detail && (
        <p className="mt-3 text-xs leading-relaxed text-[var(--text-muted)]">
          {detail}
        </p>
      )}
    </div>
  );
}
