import { getIndependenceRows } from "@/lib/queries";
import { independenceTeardownEntries } from "@/lib/teardown-content";
import { TeardownPanel } from "./teardown-panel";

type Props = {
  topic: string;
  corpusVersion: string;
  teardown?: boolean;
};

/**
 * Source Independence Graph table.
 *
 * Renders the per-narrative independence scores as an annotated table.
 * A narrative with independence_score == 1 and a high amplification_ratio
 * is a canonical echo chamber: many outlets, one root.
 *
 * The Iranian Mothership narrative is the expected standout: 6 documents,
 * 6 domains, 0 independent sources, 1 origin (Van Drew), amplification 6×.
 *
 * The React Flow graph visualization is deferred to Phase E. For the CMU
 * demo the table is sufficient to demonstrate the claim.
 */
export async function IndependenceTable({ topic, corpusVersion, teardown = false }: Props) {
  const rows = await getIndependenceRows(topic, corpusVersion);
  const active = rows.filter((r) => r.totalDocuments > 0);

  if (active.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-border-secondary bg-surface-card p-6 text-sm text-text-secondary">
        No source independence data for topic{" "}
        <code className="font-mono text-xs">{topic}</code>. Run{" "}
        <code className="rounded bg-code-bg px-1 py-0.5 font-mono text-xs">
          uv run signals compute independence --corpus {corpusVersion} --topic {topic}
        </code>{" "}
        to populate.
      </div>
    );
  }

  const maxAmplification = Math.max(...active.map((r) => r.amplificationRatio), 1);
  const topRow = active.find((r) => r.amplificationRatio === maxAmplification);

  return (
    <div className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
            Source Independence Graph
            {teardown && (
              <span className="ml-2 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-accent">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                teardown
              </span>
            )}
          </h2>
          <p className="text-sm text-text-secondary">
            {topic} · per-narrative · distinguishing corroboration from echo amplification
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs uppercase tracking-[0.18em] text-text-muted">
            Max amplification
          </p>
          <p className="text-3xl font-medium text-text-primary">{maxAmplification.toFixed(1)}×</p>
          <p className="text-xs text-text-muted">{topRow?.narrativeLabel ?? "—"} narrative</p>
        </div>
      </div>

      {/* Mobile: stacked cards */}
      <div className="flex flex-col gap-3 sm:hidden">
        {active.map((r) => {
          const isEchoChamber = r.independenceScore <= 2 && r.amplificationRatio >= 3;
          const barPct =
            maxAmplification > 0 ? (r.amplificationRatio / maxAmplification) * 100 : 0;
          return (
            <div
              key={r.narrativeSlug}
              className={`flex flex-col gap-2 rounded-sm border border-border-primary p-3 ${
                isEchoChamber ? "bg-surface-teardown" : "bg-surface-card"
              }`}
            >
              <div className="flex items-baseline gap-2">
                <span className="text-xs font-medium text-text-primary">{r.narrativeLabel}</span>
                {isEchoChamber && (
                  <span className="rounded bg-accent px-1 py-0.5 text-[10px] font-medium text-white">
                    echo
                  </span>
                )}
              </div>
              <p className="text-[10px] text-text-muted">origin: {r.originLabel}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
                <span className="text-text-secondary">
                  <span className="text-text-muted">Docs</span>{" "}
                  <span className="tabular-nums font-medium text-text-primary">{r.totalDocuments}</span>
                </span>
                <span className="text-text-secondary">
                  <span className="text-text-muted">Domains</span>{" "}
                  <span className="tabular-nums font-medium text-text-primary">{r.uniqueDomains}</span>
                </span>
                <span className="text-text-secondary">
                  <span className="text-text-muted">Independent</span>{" "}
                  <span className="tabular-nums font-medium text-text-primary">{r.independentSources}</span>
                </span>
                <span className="text-text-secondary">
                  <span className="text-text-muted">Score</span>{" "}
                  <span className="tabular-nums font-medium text-text-primary">{r.independenceScore.toFixed(0)}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-border-primary">
                  <div
                    className="h-1.5 rounded-full"
                    style={{
                      width: `${barPct}%`,
                      backgroundColor: isEchoChamber ? "var(--accent)" : "var(--chart-gray)",
                      opacity: 0.7,
                    }}
                  />
                </div>
                <span className="text-[11px] tabular-nums text-text-secondary">
                  {r.amplificationRatio.toFixed(1)}×
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Desktop: full table */}
      <div className="hidden overflow-x-auto border-y border-border-primary bg-surface-card sm:block sm:rounded-sm sm:border-x">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border-primary">
              <th className="px-4 py-2 text-left font-medium uppercase tracking-[0.15em] text-text-muted">
                Narrative
              </th>
              <th className="px-4 py-2 text-right font-medium uppercase tracking-[0.15em] text-text-muted">
                Docs
              </th>
              <th className="px-4 py-2 text-right font-medium uppercase tracking-[0.15em] text-text-muted">
                Domains
              </th>
              <th className="px-4 py-2 text-right font-medium uppercase tracking-[0.15em] text-text-muted">
                Independent
              </th>
              <th className="px-4 py-2 text-right font-medium uppercase tracking-[0.15em] text-text-muted">
                Score
              </th>
              <th className="px-4 py-2 text-left font-medium uppercase tracking-[0.15em] text-text-muted">
                Amplification
              </th>
            </tr>
          </thead>
          <tbody>
            {active.map((r) => {
              const isEchoChamber = r.independenceScore <= 2 && r.amplificationRatio >= 3;
              const barWidth =
                maxAmplification > 0 ? (r.amplificationRatio / maxAmplification) * 100 : 0;
              return (
                <tr
                  key={r.narrativeSlug}
                  className={`border-b border-border-primary last:border-0 ${
                    isEchoChamber ? "bg-surface-teardown" : ""
                  }`}
                >
                  <td className="px-4 py-2.5">
                    <span className="font-medium text-text-primary">{r.narrativeLabel}</span>
                    {isEchoChamber && (
                      <span className="ml-2 rounded bg-accent px-1 py-0.5 text-[10px] font-medium text-white">
                        echo
                      </span>
                    )}
                    <br />
                    <span className="text-text-muted">origin: {r.originLabel}</span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-secondary">
                    {r.totalDocuments}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-secondary">
                    {r.uniqueDomains}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-secondary">
                    {r.independentSources}
                  </td>
                  <td className="px-4 py-2.5 text-right font-medium tabular-nums text-text-primary">
                    {r.independenceScore.toFixed(0)}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-32 rounded-full bg-border-primary">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${barWidth}%`,
                            backgroundColor: isEchoChamber ? "var(--accent)" : "var(--chart-gray)",
                            opacity: 0.7,
                          }}
                        />
                      </div>
                      <span className="tabular-nums text-text-secondary">
                        {r.amplificationRatio.toFixed(1)}×
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs leading-relaxed text-text-secondary">
        Independence score = number of independent source domains + 1 (the originating source).
        Amplification ratio = total documents / independence score. A score of 1 with high
        amplification means a single originating claim repeated across many outlets with no
        independent corroboration, the structural signature of echo amplification. The Iranian
        Mothership narrative (score 1, 6x) is the clearest example: Rep. Van Drew&apos;s Fox News
        statement was repeated by 6 domains, none providing independent evidence of Iranian
        involvement. See{" "}
        <code className="font-mono text-xs">docs/methods/independence.md</code> for the full
        method documentation.
      </p>

      {teardown && (
        <TeardownPanel entries={independenceTeardownEntries} />
      )}
    </div>
  );
}
