/**
 * HTML chart legend for mobile viewports.
 *
 * SVG-internal legends use 9px text in a 1000px viewBox, which renders
 * at ~3px on a 375px phone. This component provides a readable HTML
 * alternative that is visible below sm: breakpoint and hidden on larger
 * screens where the SVG legend is legible.
 */

type LegendItem = {
  color: string;
  label: string;
  /** Use a line swatch instead of a square (for line charts). */
  line?: boolean;
  opacity?: number;
};

type Props = {
  items: LegendItem[];
};

export function ChartLegend({ items }: Props) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 sm:hidden">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          {item.line ? (
            <span
              className="h-0.5 w-3 shrink-0 rounded-full"
              style={{ backgroundColor: item.color, opacity: item.opacity ?? 1 }}
            />
          ) : (
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-sm"
              style={{ backgroundColor: item.color, opacity: item.opacity ?? 1 }}
            />
          )}
          <span className="text-[11px] text-text-secondary">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
