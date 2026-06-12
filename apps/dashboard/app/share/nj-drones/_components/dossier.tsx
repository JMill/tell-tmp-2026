type Props = {
  recipient: string;
  context: string;
  date: string;
};

export function Dossier({ recipient, context, date }: Props) {
  return (
    <aside className="mb-12 flex flex-col gap-1 border-y border-border-primary py-4 font-sans text-[0.7rem] uppercase tracking-[0.22em] text-text-muted">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span>Unlisted</span>
        <span aria-hidden>·</span>
        <span>For {recipient}</span>
        <span aria-hidden>·</span>
        <span>{context}</span>
        <span aria-hidden>·</span>
        <span>{date}</span>
      </div>
    </aside>
  );
}
