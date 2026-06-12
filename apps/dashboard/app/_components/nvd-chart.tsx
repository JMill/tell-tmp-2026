import { getNvdSeries } from "@/lib/queries";
import { nvdTeardownEntries } from "@/lib/teardown-content";
import { ChartLegend } from "./chart-legend";
import { TeardownPanel } from "./teardown-panel";

type Props = {
  topic: string;
  corpusVersion: string;
  teardown?: boolean;
  /** ISO date (YYYY-MM-DD) lower bound on windowEnd. Inclusive. */
  fromDate?: string;
  /** ISO date (YYYY-MM-DD) upper bound on windowEnd. Inclusive. */
  toDate?: string;
  /** If provided, render only these narrative slugs (still ordered by NARRATIVE_ORDER). */
  narrativeSlugs?: string[];
};

// Narratives that are worth rendering (non-zero document matches in the corpus).
// Sorted by expected visual interest for the CMU demo.
const NARRATIVE_ORDER = [
  "iranian-mothership",
  "drones-legit",
  "mass-hysteria",
  "test-flights",
  "uap",
  "loose-nuke",
];

const NARRATIVE_LABELS: Record<string, string> = {
  "iranian-mothership": "Iranian Mothership",
  "drones-legit": "Legitimate Drones",
  "mass-hysteria": "Mass Hysteria",
  "test-flights": "FAA-Approved Flights",
  "uap": "Genuine UAP",
  "loose-nuke": "Loose Nuke",
};

const NARRATIVE_COLORS: Record<string, string> = {
  "iranian-mothership": "var(--accent)",
  "drones-legit": "var(--chart-green)",
  "mass-hysteria": "var(--chart-gray)",
  "test-flights": "var(--chart-tan)",
  "uap": "var(--accent-muted)",
  "loose-nuke": "var(--chart-mauve)",
};

/**
 * Narrative Velocity Divergence chart.
 *
 * Renders NVD as a multi-line time series — one line per narrative — where
 * the y-axis is the NVD ratio (narrative spread / (evidence + 1)). A ratio
 * above 1.0 means the narrative is spreading faster than corroborating
 * evidence is appearing. The Iranian Mothership narrative peaks at 2.0 on
 * Dec 11, 2024, the day Van Drew made his public statement.
 *
 * Hand-drawn SVG, no chart library, same approach as the IVI and hypothesis
 * charts.
 */
function parseIsoDate(iso: string, endOfDay: boolean): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return null;
  return endOfDay
    ? Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 23, 59, 59, 999)
    : Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 0, 0, 0, 0);
}

export async function NvdChart({
  topic,
  corpusVersion,
  teardown = false,
  fromDate,
  toDate,
  narrativeSlugs,
}: Props) {
  const fullSeries = await getNvdSeries(topic, corpusVersion, 3);

  const fromMs = fromDate ? parseIsoDate(fromDate, false) : null;
  const toMs = toDate ? parseIsoDate(toDate, true) : null;
  const slugFilter = narrativeSlugs ? new Set(narrativeSlugs) : null;
  const series = fullSeries.filter((p) => {
    if (slugFilter && !slugFilter.has(p.narrativeSlug)) return false;
    if (fromMs !== null || toMs !== null) {
      const t = new Date(p.windowEnd).getTime();
      if (fromMs !== null && t < fromMs) return false;
      if (toMs !== null && t > toMs) return false;
    }
    return true;
  });

  // Build active slugs from data, then apply preferred ordering.
  // This ensures narratives not in NARRATIVE_ORDER still render.
  const dataSlugs = new Set(
    series.filter((p) => p.nvdValue > 0).map((p) => p.narrativeSlug),
  );
  const orderedActive = NARRATIVE_ORDER.filter((s) => dataSlugs.has(s));
  const unordered = [...dataSlugs].filter((s) => !NARRATIVE_ORDER.includes(s)).sort();
  const activeSlugs = [...orderedActive, ...unordered];

  if (activeSlugs.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-border-secondary bg-surface-card p-6 text-sm text-text-secondary">
        No NVD data for topic{" "}
        <code className="font-mono text-xs">{topic}</code>. Run{" "}
        <code className="rounded bg-code-bg px-1 py-0.5 font-mono text-xs">
          uv run signals compute nvd --corpus {corpusVersion} --topic {topic}
        </code>{" "}
        to populate.
      </div>
    );
  }

  // Build per-narrative point maps
  type PointMap = Map<string, number>; // window_end ISO → nvd_value
  const byNarrative: Record<string, PointMap> = {};
  for (const slug of activeSlugs) {
    byNarrative[slug] = new Map();
  }
  const allDates = new Set<string>();
  for (const p of series) {
    if (!activeSlugs.includes(p.narrativeSlug)) continue;
    const key = new Date(p.windowEnd).toISOString().slice(0, 10);
    byNarrative[p.narrativeSlug].set(key, p.nvdValue);
    allDates.add(key);
  }
  const sortedDates = Array.from(allDates).sort();

  const maxNvd = Math.max(
    2.5,
    ...series
      .filter((p) => activeSlugs.includes(p.narrativeSlug))
      .map((p) => p.nvdValue),
  );

  const width = 1000;
  const height = 300;
  const marginTop = 30;
  const marginBottom = 55;
  const marginLeft = 55;
  const marginRight = 20;
  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;

  const xScale = (i: number) =>
    marginLeft + (i / Math.max(1, sortedDates.length - 1)) * plotWidth;
  const yScale = (v: number) =>
    marginTop + plotHeight * (1 - v / maxNvd);

  // Highlight the Dec 11-13 window (Iranian Mothership spike)
  const highlightStart = sortedDates.findIndex((d) => d >= "2024-12-11");
  const highlightEnd = sortedDates.findIndex((d) => d > "2024-12-13");
  const hxStart = highlightStart >= 0 ? xScale(highlightStart) : null;
  const hxEnd =
    highlightEnd > 0
      ? xScale(highlightEnd - 1)
      : highlightStart >= 0
        ? xScale(sortedDates.length - 1)
        : null;

  const labelStride = Math.max(1, Math.floor(sortedDates.length / 20));

  // Derive peak annotation from series data rather than hard-coding corpus-specific values.
  const activePoints = series.filter((p) => activeSlugs.includes(p.narrativeSlug));
  const peakPoint = activePoints.reduce(
    (best, p) => (p.nvdValue > best.nvdValue ? p : best),
    activePoints[0],
  );
  const peakNarrative = NARRATIVE_LABELS[peakPoint.narrativeSlug] ?? peakPoint.narrativeSlug;
  const peakValue = peakPoint.nvdValue;
  const peakDate = new Date(peakPoint.windowEnd).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
            Narrative Velocity Divergence
            {teardown && (
              <span className="ml-2 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-accent">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                teardown
              </span>
            )}
          </h2>
          <p className="text-sm text-text-secondary">
            {topic} · 3-day rolling window · NVD {">"} 1.0 means narrative outpacing evidence
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs uppercase tracking-[0.18em] text-text-muted">
            {peakNarrative} peak
          </p>
          <p className="text-3xl font-medium text-text-primary">{peakValue.toFixed(2)}</p>
          <p className="text-xs text-text-muted">{peakDate}</p>
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="-mx-4 h-auto w-[calc(100%+2rem)] border-y border-border-primary bg-surface-card sm:mx-0 sm:w-full sm:rounded-sm sm:border-x"
        role="img"
        aria-label={`Narrative Velocity Divergence for ${topic}`}
      >
        {/* Dec 11-13 highlight band */}
        {hxStart !== null && hxEnd !== null && (
          <rect
            x={hxStart}
            y={marginTop}
            width={hxEnd - hxStart + 2}
            height={plotHeight}
            fill="var(--accent)"
            opacity={0.08}
          />
        )}

        {/* Gridlines */}
        {[0.5, 1.0, 1.5, 2.0].map((v) => {
          const y = yScale(v);
          return (
            <g key={v}>
              <line
                x1={marginLeft}
                y1={y}
                x2={width - marginRight}
                y2={y}
                stroke="var(--border-primary)"
                strokeDasharray={v === 1.0 ? "none" : "2 4"}
                strokeWidth={v === 1.0 ? 1.5 : 1}
              />
              <text
                x={marginLeft - 6}
                y={y}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="10"
                fill={v === 1.0 ? "var(--text-muted)" : "var(--grid-muted)"}
              >
                {v.toFixed(1)}
              </text>
            </g>
          );
        })}
        <text x={marginLeft - 6} y={marginTop - 10} textAnchor="end" fontSize="9" fill="var(--text-muted)">
          NVD
        </text>

        {/* Lines per narrative */}
        {activeSlugs.map((slug) => {
          const color = NARRATIVE_COLORS[slug] ?? "var(--chart-gray)";
          const pts = sortedDates.map((d, i) => {
            const v = byNarrative[slug].get(d) ?? 0;
            return `${xScale(i)},${yScale(v)}`;
          });
          return (
            <polyline
              key={slug}
              points={pts.join(" ")}
              fill="none"
              stroke={color}
              strokeWidth={slug === "iranian-mothership" ? 2 : 1.5}
              opacity={slug === "iranian-mothership" ? 1 : 0.7}
            />
          );
        })}

        {/* X-axis labels */}
        {sortedDates.map((d, i) => {
          if (i % labelStride !== 0 && i !== sortedDates.length - 1) return null;
          const label = new Date(d).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            timeZone: "UTC",
          });
          return (
            <text
              key={d}
              x={xScale(i)}
              y={height - 36}
              textAnchor="middle"
              fontSize="9"
              fill="var(--text-muted)"
            >
              {label}
            </text>
          );
        })}

        {/* Legend (hidden on mobile; HTML ChartLegend below handles small screens).
            Slot pitch is derived from plotWidth so the last item never overflows
            the viewBox regardless of how many narratives are active. */}
        <g transform={`translate(${marginLeft}, ${height - 18})`} className="hidden sm:block">
          {(() => {
            const slot = Math.floor(plotWidth / Math.max(1, activeSlugs.length));
            return activeSlugs.map((slug, idx) => (
              <g key={slug} transform={`translate(${idx * slot}, 0)`}>
                <line
                  x1="0"
                  y1="5"
                  x2="12"
                  y2="5"
                  stroke={NARRATIVE_COLORS[slug] ?? "var(--chart-gray)"}
                  strokeWidth={slug === "iranian-mothership" ? 2 : 1.5}
                />
                <text x="16" y="9" fontSize="9" fill="var(--text-secondary)">
                  {NARRATIVE_LABELS[slug] ?? slug}
                </text>
              </g>
            ));
          })()}
        </g>
      </svg>

      <ChartLegend
        items={activeSlugs.map((slug) => ({
          color: NARRATIVE_COLORS[slug] ?? "var(--chart-gray)",
          label: NARRATIVE_LABELS[slug] ?? slug,
          line: true,
        }))}
      />

      <p className="text-xs leading-relaxed text-text-secondary">
        The Iranian Mothership narrative (red line) reaches NVD{" "}
        <span className="font-medium text-text-primary">2.00</span> on December 11,
        2024, the day Rep. Van Drew made his public statement on Fox News. Six
        documents reference the narrative; three documents score on H4 (Classified
        Tech, the narrative&apos;s supporting hypothesis), but none provide
        independent corroboration. The narrative spread at twice the rate of
        supporting evidence. The Pentagon denied the claim the same day; NVD
        returns to baseline within 48 hours as the denial propagates. See{" "}
        <code className="font-mono text-xs">docs/methods/nvd.md</code> for the
        full method documentation.
      </p>

      {teardown && (
        <TeardownPanel
          entries={nvdTeardownEntries({
            peakNarrative,
            peakValue,
            peakDate,
            peakNarrativeVelocity: peakPoint.narrativeVelocity,
            peakEvidenceVelocity: peakPoint.evidenceVelocity,
          })}
        />
      )}
    </div>
  );
}
