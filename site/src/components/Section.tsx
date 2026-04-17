interface SectionProps {
  id?: string;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function Section({ id, title, subtitle, children, className = "" }: SectionProps) {
  return (
    <section id={id} className={`py-20 ${className}`}>
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-[var(--text-primary)]">
            {title}
          </h2>
          {subtitle && (
            <p className="mt-3 max-w-2xl text-[var(--text-secondary)]">
              {subtitle}
            </p>
          )}
        </div>
        {children}
      </div>
    </section>
  );
}
