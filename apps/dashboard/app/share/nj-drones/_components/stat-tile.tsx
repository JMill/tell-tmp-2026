type Props = {
  value: string;
  unit?: string;
  label: string;
  context?: string;
};

export function StatTile({ value, unit, label, context }: Props) {
  return (
    <figure className="my-10 flex flex-col items-start gap-2 border-l-2 border-accent pl-5">
      <figcaption className="text-[0.7rem] uppercase tracking-[0.2em] text-text-muted">
        {label}
      </figcaption>
      <div className="flex items-baseline gap-2">
        <span className="font-serif text-5xl font-semibold leading-none text-text-primary tabular-nums">
          {value}
        </span>
        {unit && (
          <span className="text-sm uppercase tracking-[0.18em] text-text-muted">
            {unit}
          </span>
        )}
      </div>
      {context && <p className="text-sm text-text-secondary">{context}</p>}
    </figure>
  );
}
