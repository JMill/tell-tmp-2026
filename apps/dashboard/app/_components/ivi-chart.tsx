import { getIviSeries } from "@/lib/queries";
import { iviTeardownEntries } from "@/lib/teardown-content";
import { ChartLegend } from "./chart-legend";
import { TeardownPanel } from "./teardown-panel";

type Props = {
  topic: string;
  windowDays?: number;
  teardown?: boolean;
  /** ISO date (YYYY-MM-DD) lower bound on windowEnd. Inclusive. */
  fromDate?: string;
  /** ISO date (YYYY-MM-DD) upper bound on windowEnd. Inclusive. */
  toDate?: string;
};

/**
 * Information Vacuum Index time-series chart.
 *
 * Hand-drawn SVG so the dashboard has no chart-library dependency yet.
 * Will be replaced with Visx (or equivalent) in a later polish pass when
 * the design tokens are locked. For Phase B the point is that the signal
 * is rendered, not that it's stylized.
 *
 * The chart shows IVI value as vertical bars, colored to highlight the
 * December 2024 vacuum window. Peak IVI values and their corresponding
 * narrative events are annotated inline underneath.
 */
function parseIsoDate(iso: string, endOfDay: boolean): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return null;
  return endOfDay
    ? Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 23, 59, 59, 999)
    : Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 0, 0, 0, 0);
}

export async function IviChart({
  topic,
  windowDays = 7,
  teardown = false,
  fromDate,
  toDate,
}: Props) {
  const fullSeries = await getIviSeries(topic, windowDays);

  const fromMs = fromDate ? parseIsoDate(fromDate, false) : null;
  const toMs = toDate ? parseIsoDate(toDate, true) : null;
  const series =
    fromMs !== null || toMs !== null
      ? fullSeries.filter((p) => {
          const t = p.windowEnd.getTime();
          if (fromMs !== null && t < fromMs) return false;
          if (toMs !== null && t > toMs) return false;
          return true;
        })
      : fullSeries;

  if (series.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-border-secondary bg-surface-card p-6 text-sm text-text-secondary">
        No IVI series persisted for topic{" "}
        <code className="font-mono text-xs">{topic}</code> at {windowDays}-day
        window. Run{" "}
        <code className="rounded bg-code-bg px-1 py-0.5 font-mono text-xs">
          uv run signals compute ivi --corpus ... --topic {topic}
        </code>{" "}
        to populate.
      </div>
    );
  }

  const maxValue = Math.max(...series.map((p) => p.value), 1);
  const peakPoint = series.reduce((a, b) => (a.value >= b.value ? a : b));

  const width = 1000;
  const height = 280;
  const marginTop = 20;
  // 60 keeps the SVG-internal legend and x-axis tick labels both inside the
  // viewBox. Earlier marginBottom=40 paired with `translate(.., height - 6)`
  // for the legend pushed the legend baseline to y=283 in a 280-tall viewBox,
  // so the bottom row of the legend rendered as half-height text.
  const marginBottom = 60;
  const marginLeft = 40;
  const marginRight = 20;
  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;

  const barWidth = plotWidth / series.length;
  const yScale = (v: number) => plotHeight - (v / maxValue) * plotHeight;

  // Highlight any bar whose window ends during the canonical Dec 11-25, 2024
  // vacuum period so it is immediately visible in the chart.
  //
  // Bug fix (Codex review on PR #7): the upper bound was previously
  // Date.UTC(2024, 11, 25, 23, 59, 59) which has milliseconds = 0, equal
  // to 2024-12-25T23:59:59.000Z. The persisted signal_ivi rows use
  // datetime.max.time() in Python which deserializes to
  // 2024-12-25T23:59:59.999Z, strictly greater than the upper bound, so
  // the Dec 25 bar was incorrectly classified as outside the vacuum window.
  // The fix is to compare on UTC calendar day, not on epoch milliseconds.
  const isVacuumWindow = (d: Date) => {
    const year = d.getUTCFullYear();
    const month = d.getUTCMonth(); // 0-indexed; 11 = December
    const day = d.getUTCDate();
    if (year !== 2024 || month !== 11) return false;
    return day >= 11 && day <= 25;
  };

  // Format window-end label for every 7th bar to avoid crowding.
  const labelStride = Math.max(1, Math.floor(series.length / 8));

  return (
    <div className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
            Information Vacuum Index
            {teardown && (
              <span className="ml-2 inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-accent">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
                teardown
              </span>
            )}
          </h2>
          <p className="text-sm text-text-secondary">
            {topic} · {windowDays}-day rolling window · {series.length} windows
          </p>
        </div>
        <div className="sm:text-right">
          <p className="text-xs uppercase tracking-[0.18em] text-text-muted">
            Peak
          </p>
          <p className="text-3xl font-medium text-text-primary">
            {peakPoint.value.toFixed(2)}
          </p>
          <p className="text-xs text-text-muted">
            {peakPoint.windowEnd.toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
              timeZone: "UTC",
            })}
          </p>
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="-mx-4 h-auto w-[calc(100%+2rem)] border-y border-border-primary bg-surface-card sm:mx-0 sm:w-full sm:rounded-sm sm:border-x"
        role="img"
        aria-label={`Information Vacuum Index time series for ${topic}`}
      >
        {/* Y-axis gridlines at 25%, 50%, 75%, 100% */}
        {[0.25, 0.5, 0.75, 1].map((frac) => {
          const y = marginTop + plotHeight - frac * plotHeight;
          const value = (frac * maxValue).toFixed(1);
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
                fontFamily="var(--font-geist-sans), sans-serif"
              >
                {value}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {series.map((point, i) => {
          const x = marginLeft + i * barWidth;
          const barHeight = plotHeight - yScale(point.value);
          const y = marginTop + yScale(point.value);
          const isVacuum = isVacuumWindow(new Date(point.windowEnd));
          const isPeak = point.value === peakPoint.value;
          return (
            <rect
              key={i}
              x={x + 1}
              y={y}
              width={Math.max(1, barWidth - 2)}
              height={Math.max(0.5, barHeight)}
              fill={isPeak ? "var(--accent)" : isVacuum ? "var(--accent-muted)" : "var(--chart-gray)"}
              opacity={isVacuum ? 1 : 0.55}
            >
              <title>
                {`${new Date(point.windowEnd).toISOString().slice(0, 10)}: ${point.value.toFixed(2)} (discourse=${point.discourseCount}, authoritative=${point.authoritativeCount})`}
              </title>
            </rect>
          );
        })}

        {/* X-axis labels. The final point is always rendered; the stride tick
            immediately before it is suppressed when the two would visually
            collide (e.g., "Apr 1" + "Apr 4" three bars apart). */}
        {series.map((point, i) => {
          const isLast = i === series.length - 1;
          const isStride = i % labelStride === 0;
          if (!isStride && !isLast) return null;
          const minGap = Math.max(4, Math.ceil(labelStride * 0.4));
          if (!isLast && series.length - 1 - i < minGap) return null;
          const x = marginLeft + i * barWidth + barWidth / 2;
          const label = new Date(point.windowEnd).toLocaleDateString(
            undefined,
            { month: "short", day: "numeric", timeZone: "UTC" },
          );
          return (
            <text
              key={`label-${i}`}
              x={x}
              y={height - 36}
              textAnchor="middle"
              fontSize="10"
              fill="var(--text-muted)"
              fontFamily="var(--font-geist-sans), sans-serif"
            >
              {label}
            </text>
          );
        })}

        {/* Legend (hidden on mobile; HTML ChartLegend below handles small screens) */}
        <g transform={`translate(${marginLeft}, ${height - 18})`} className="hidden sm:block">
          <rect width="10" height="10" fill="var(--accent)" />
          <text x="14" y="9" fontSize="9" fill="var(--text-secondary)">
            peak
          </text>
          <rect x="60" width="10" height="10" fill="var(--accent-muted)" />
          <text x="74" y="9" fontSize="9" fill="var(--text-secondary)">
            Dec 11-25 vacuum window
          </text>
          <rect x="250" width="10" height="10" fill="var(--chart-gray)" opacity="0.55" />
          <text x="264" y="9" fontSize="9" fill="var(--text-secondary)">
            outside window
          </text>
        </g>
      </svg>

      <ChartLegend
        items={[
          { color: "var(--accent)", label: "Peak" },
          { color: "var(--accent-muted)", label: "Dec 11-25 vacuum window" },
          { color: "var(--chart-gray)", label: "Outside window", opacity: 0.55 },
        ]}
      />

      <p className="text-xs leading-relaxed text-text-secondary">
        The peak falls in the December 11-25, 2024 window, the period
        corresponding to the Iranian Mothership narrative burst, the loose-nuke
        podcast, the Stewart Airport closure, and the FAA&apos;s 22-community TFR
        response. See{" "}
        <code className="font-mono text-xs">docs/methods/ivi.md</code> for the
        full empirical write-up and interpretation.
      </p>

      {teardown && (
        <TeardownPanel
          entries={iviTeardownEntries({
            windowDays,
            peakValue: peakPoint.value,
            peakDate: peakPoint.windowEnd.toISOString().slice(0, 10),
            peakDiscourse: peakPoint.discourseCount,
            peakAuthoritative: peakPoint.authoritativeCount,
          })}
        />
      )}
    </div>
  );
}
