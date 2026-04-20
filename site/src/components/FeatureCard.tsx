// Legacy export kept to avoid breaking any lingering imports in older pages.
// The new design uses the `.features`/`.feat` editorial list inline, not this component.
import type { ReactNode } from "react";

export function FeatureCard({ title, children }: { title: ReactNode; children: ReactNode }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  );
}
