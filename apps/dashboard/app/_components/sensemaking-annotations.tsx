/**
 * Sensemaking Activities annotations.
 *
 * Maps each dashboard section to its Klein (2007) sensemaking activity
 * and Leveson (2012) STAMP concept. This component is the interactive
 * demonstration of Claim 5: "The architecture embeds sensemaking theory
 * and systems-theoretic accident modeling as design requirements."
 *
 * Rendered as a compact legend between the header and the charts. Each
 * card links a Klein activity to the pipeline component that instantiates
 * it, grounding the theoretical framework in the empirical dashboard.
 */

import { sensemakingTeardownEntries } from "@/lib/teardown-content";
import { TeardownPanel } from "./teardown-panel";

const activities: {
  klein: string;
  leveson: string;
  pipeline: string;
  chart: string;
}[] = [
  {
    klein: "Elaborating",
    leveson: "Process model",
    pipeline: "H1-H5 hypothesis scoring builds a progressively richer picture from each document",
    chart: "Hypothesis chart",
  },
  {
    klein: "Questioning",
    leveson: "Process model divergence",
    pipeline: "NVD detects when narratives outpace evidence; contradicting evidence lag measures response time",
    chart: "NVD chart",
  },
  {
    klein: "Connecting",
    leveson: "Sensor independence",
    pipeline: "Source Independence Graph traces attribution chains to distinguish corroboration from echo",
    chart: "Independence table + graph",
  },
  {
    klein: "Comparing",
    leveson: "Unsafe control action",
    pipeline: "Five hypotheses maintained simultaneously; entropy tracks capacity to compare alternatives",
    chart: "Hypothesis chart",
  },
  {
    klein: "Framing",
    leveson: "Control loop adequacy",
    pipeline: "Eight expert-curated narratives applied to corpus; IVI measures institutional response gap",
    chart: "IVI chart",
  },
  {
    klein: "Re-Framing",
    leveson: "Feedback loop closure",
    pipeline: "IVI drop signals vacuum closing; premature closure resistance ensures frames stay revisable",
    chart: "IVI chart",
  },
];

export function SensemakingAnnotations({ teardown = false }: { teardown?: boolean }) {
  return (
    <section className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      <div className="flex flex-col gap-1">
        <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
          Sensemaking Architecture
          {teardown && (
            <span className="ml-2 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-accent">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
              teardown
            </span>
          )}
        </h2>
        <p className="text-sm text-text-secondary">
          Each chart below instantiates a Klein (2007) sensemaking activity and
          a Leveson (2012) STAMP concept as a computational design requirement.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-3 min-[400px]:grid-cols-2 sm:grid-cols-3">
        {activities.map((a) => (
          <div
            key={a.klein}
            className="flex flex-col gap-1 rounded-sm border border-border-primary bg-surface-card p-3"
          >
            <div className="flex items-baseline gap-2">
              <span className="text-xs font-medium text-text-primary">
                {a.klein}
              </span>
              <span className="text-[10px] text-text-muted">
                {a.leveson}
              </span>
            </div>
            <p className="text-[10px] leading-snug text-text-secondary">
              {a.pipeline}
            </p>
            <p className="mt-auto text-[10px] text-text-muted">
              → {a.chart}
            </p>
          </div>
        ))}
      </div>

      {teardown && (
        <TeardownPanel entries={sensemakingTeardownEntries} />
      )}
    </section>
  );
}
