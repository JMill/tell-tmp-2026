"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

/**
 * Teardown mode toggle.
 *
 * Inspired by End Effector teardowns: flips the dashboard from a clean
 * editorial presentation into an annotated engineering view that reveals
 * the formulas, assumptions, model choices, and data lineage behind
 * every visualization.
 *
 * Uses URL search params (?teardown=true) so teardown state is shareable,
 * bookmarkable, and compatible with Server Components.
 */
export function TeardownToggle({ active }: { active: boolean }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const toggle = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    if (active) {
      params.delete("teardown");
    } else {
      params.set("teardown", "true");
    }
    const qs = params.toString();
    router.push(qs ? `?${qs}` : "/", { scroll: false });
  }, [active, router, searchParams]);

  return (
    <button
      onClick={toggle}
      className="group flex items-center gap-2 rounded-sm border px-3 py-2.5 text-xs uppercase tracking-[0.15em] transition-colors sm:py-1.5"
      style={{
        borderColor: active ? "var(--accent)" : "var(--border-primary)",
        backgroundColor: active ? "var(--surface-teardown)" : "transparent",
        color: active ? "var(--accent)" : "var(--text-muted)",
      }}
    >
      <span
        className="inline-block h-2 w-2 rounded-full transition-colors"
        style={{ backgroundColor: active ? "var(--accent)" : "var(--border-secondary)" }}
      />
      {active ? "Teardown on" : "Teardown"}
    </button>
  );
}
