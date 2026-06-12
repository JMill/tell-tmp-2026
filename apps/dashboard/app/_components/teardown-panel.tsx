/**
 * Teardown annotation panel.
 *
 * Renders engineering annotations alongside dashboard visualizations
 * when teardown mode is active. Styled as editorial margin notes: left
 * accent border, muted background, monospace for formulas.
 *
 * Content is defined in lib/teardown-content.ts (single source of truth).
 * Components import their entries from that module and pass them here.
 */

import type { TeardownEntry } from "@/lib/teardown-content";

type Props = {
  entries: TeardownEntry[];
};

export function TeardownPanel({ entries }: Props) {
  return (
    <div className="border-l-2 border-accent bg-surface-teardown px-4 py-3">
      <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-accent">
        Teardown
      </p>
      <dl className="flex flex-col gap-1.5">
        {entries.map((entry) => (
          <div key={entry.label} className="flex flex-col gap-0.5">
            <dt className="text-[10px] font-medium uppercase tracking-[0.1em] text-text-muted">
              {entry.label}
            </dt>
            <dd className="font-mono text-[11px] leading-snug text-text-secondary">
              {entry.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
