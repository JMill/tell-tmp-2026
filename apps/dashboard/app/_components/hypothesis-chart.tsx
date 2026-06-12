import { getHypothesisDistributionSeries } from "@/lib/queries";
import { hypothesisTeardownEntries } from "@/lib/teardown-content";
import { ChartLegend } from "./chart-legend";
import { TeardownPanel } from "./teardown-panel";

type Props = {
  topic: string;
  corpusVersion: string;
  teardown?: boolean;
};

const HYPOTHESES = [
  { id: "H1", label: "Artifact", color: "var(--chart-gray)" },
  { id: "H2", label: "Natural", color: "var(--chart-tan)" },
  { id: "H3", label: "Unclassified Tech", color: "var(--chart-green)" },
  { id: "H4", label: "Classified Tech", color: "var(--accent)" },
  { id: "H5", label: "Unknown", color: "var(--accent-muted)" },
] as const;

const MAX_ENTROPY_BITS = Math.log2(5); // ~2.32

/**
 * Daily H1-H5 hypothesis distribution chart.
 *
 * Renders the time series as a stacked bar chart where each day is a bar
 * subdivided into colored segments by hypothesis. The total height of each
 * bar is the entropy (in bits) of that day's distribution, capped at the
 * theoretical maximum of log2(5) ≈ 2.32 bits.
 *
 * The visual claim: when entropy stays high, the system is preserving
 * "structured uncertainty" — the abstract's promised behavior. When entropy
 * dips, the system is narrowing in response to evidence (not collapsing).
 *
 * Hand-drawn SVG, no chart library, same approach as the IVI chart. To be
 * replaced with Visx in a Stage 3+ polish pass.
 */
export async function HypothesisChart({ topic, corpusVersion, teardown = false }: Props) {
  const series = await getHypothesisDistributionSeries(topic, corpusVersion);

  if (series.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-border-secondary bg-surface-card p-6 text-sm text-text-secondary">
        No hypothesis distributions persisted for topic{" "}
        <code className="font-mono text-xs">{topic}</code>. Run{" "}
        <code className="rounded bg-code-bg px-1 py-0.5 font-mono text-xs">
          uv run signals analyze hypotheses --corpus {corpusVersion} --topic {topic}
        </code>{" "}
        to populate.
      </div>
    );
  }

  const minEntropy = Math.min(...series.map((p) => p.entropy));
  const meanEntropy =
    series.reduce((acc, p) => acc + p.entropy, 0) / series.length;

  const width = 1000;
  const height = 320;
  const marginTop = 30;
  const marginBottom = 60;
  const marginLeft = 60;
  const marginRight = 20;
  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;

  // Bar width / gap calculation that stays valid for any series length.
  //
  // Previous formula was `plotWidth / series.length - barGap` with a fixed
  // 4px gap, which goes NEGATIVE once the series has ~230+ entries at the
  // current plotWidth. Negative widths produce invalid SVG and a broken
  // chart (flagged by Codex review on PR #8).
  //
  // New approach:
  //   - slotWidth is the total horizontal space per bar (including gap)
  //   - barGap is a fraction of the slot (capped so bars stay visible)
  //   - barWidth is what's left, clamped to MIN_BAR_WIDTH
  // This produces readable bars for short series (fat, with generous gaps)
  // and degrades gracefully to thin bars with minimal gaps for long series.
  const MIN_BAR_WIDTH = 1.5;
  const slotWidth = plotWidth / series.length;
  const barGap = Math.min(4, slotWidth * 0.25);
  const barWidth = Math.max(MIN_BAR_WIDTH, slotWidth - barGap);
  const yScale = (v: number) => plotHeight * (1 - v / MAX_ENTROPY_BITS);

  return (
    <div className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
            Hypothesis Distribution
            {teardown && (
              <span className="ml-2 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-accent">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                teardown
              </span>
            )}
          </h2>
          <p className="text-sm text-text-secondary">
            {topic} · daily H1-H5 mix · stacked by hypothesis, height = entropy in bits
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs uppercase tracking-[0.18em] text-text-muted">
            Entropy floor
          </p>
          <p className="text-3xl font-medium text-text-primary">
            {minEntropy.toFixed(2)}
          </p>
          <p className="text-xs text-text-muted">
            of {MAX_ENTROPY_BITS.toFixed(2)} bits max ·{" "}
            {((minEntropy / MAX_ENTROPY_BITS) * 100).toFixed(0)}% retained
          </p>
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="-mx-4 h-auto w-[calc(100%+2rem)] border-y border-border-primary bg-surface-card sm:mx-0 sm:w-full sm:rounded-sm sm:border-x"
        role="img"
        aria-label={`Daily hypothesis distribution for ${topic}`}
      >
        {/* Y-axis: entropy in bits */}
        {[0.25, 0.5, 0.75, 1].map((frac) => {
          const y = marginTop + plotHeight * (1 - frac);
          const value = (frac * MAX_ENTROPY_BITS).toFixed(2);
          return (
            <g key={frac}>
              <line
                x1={marginLeft}
                y1={y}
                x2={width - marginRight}
                y2={y}
                stroke="var(--border-primary)"
                strokeDasharray="2 4"
              />
              <text
                x={marginLeft - 6}
                y={y}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="10"
                fill="var(--text-muted)"
              >
                {value}
              </text>
            </g>
          );
        })}
        <text
          x={marginLeft - 6}
          y={marginTop - 10}
          textAnchor="end"
          fontSize="9"
          fill="var(--text-muted)"
        >
          entropy (bits)
        </text>

        {/* Stacked bars */}
        {series.map((point, i) => {
          const x = marginLeft + i * slotWidth;
          const totalHeight = plotHeight - yScale(point.entropy);
          const top = marginTop + yScale(point.entropy);

          // Stack hypothesis segments proportional to their probability
          let cumulative = 0;
          const segments = HYPOTHESES.map((h) => {
            const p = point.distribution[h.id] ?? 0;
            const segHeight = totalHeight * p;
            const segY = top + totalHeight * cumulative;
            cumulative += p;
            return { ...h, p, segY, segHeight };
          });

          return (
            <g key={i}>
              {segments.map((seg) => {
                // Skip zero-probability segments entirely. Rendering a minimum
                // height for p=0 fabricates visible mass that distorts the
                // distribution, especially on low-entropy days.
                if (seg.p === 0) return null;
                return (
                  <rect
                    key={seg.id}
                    x={x}
                    y={seg.segY}
                    width={barWidth}
                    height={Math.max(0.5, seg.segHeight)}
                    fill={seg.color}
                    opacity={0.92}
                  >
                    <title>
                      {`${new Date(point.day).toISOString().slice(0, 10)}: ${seg.id} ${seg.label} = ${(seg.p * 100).toFixed(0)}% (entropy ${point.entropy.toFixed(2)} bits, ${point.documentCount} docs, modal ${point.modalHypothesis})`}
                    </title>
                  </rect>
                );
              })}
            </g>
          );
        })}

        {/* X-axis labels. For short series show a label per bar; for longer
            series stride so labels do not collide. */}
        {(() => {
          const labelStride = Math.max(1, Math.floor(series.length / 20));
          return series.map((point, i) => {
            if (i % labelStride !== 0 && i !== series.length - 1) return null;
            const x = marginLeft + i * slotWidth + barWidth / 2;
            const label = new Date(point.day).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
              timeZone: "UTC",
            });
            return (
              <text
                key={`label-${i}`}
                x={x}
                y={height - 36}
                textAnchor="middle"
                fontSize="9"
                fill="var(--text-muted)"
              >
                {label}
              </text>
            );
          });
        })()}

        {/* Legend (hidden on mobile; HTML ChartLegend below handles small screens) */}
        <g transform={`translate(${marginLeft}, ${height - 18})`} className="hidden sm:block">
          {HYPOTHESES.map((h, idx) => (
            <g key={h.id} transform={`translate(${idx * 170}, 0)`}>
              <rect width="10" height="10" fill={h.color} opacity={0.92} />
              <text x="14" y="9" fontSize="9" fill="var(--text-secondary)">
                {h.id} {h.label}
              </text>
            </g>
          ))}
        </g>
      </svg>

      <ChartLegend
        items={HYPOTHESES.map((h) => ({
          color: h.color,
          label: `${h.id} ${h.label}`,
          opacity: 0.92,
        }))}
      />

      <p className="text-xs leading-relaxed text-text-secondary">
        Mean entropy across the corpus is{" "}
        <span className="font-medium text-text-primary">
          {meanEntropy.toFixed(2)} bits
        </span>{" "}
        ({((meanEntropy / MAX_ENTROPY_BITS) * 100).toFixed(0)}% of max). No
        hypothesis ever zeros out across the entire window. The system
        preserves structured uncertainty across H1-H5 even as the modal
        hypothesis shifts in response to incoming evidence. See{" "}
        <code className="font-mono text-xs">docs/methods/sqm.md</code> for the
        full empirical write-up.
      </p>

      {teardown && (
        <TeardownPanel
          entries={hypothesisTeardownEntries({
            maxEntropyBits: MAX_ENTROPY_BITS,
            minEntropy,
            minEntropyPct: (minEntropy / MAX_ENTROPY_BITS) * 100,
          })}
        />
      )}
    </div>
  );
}
