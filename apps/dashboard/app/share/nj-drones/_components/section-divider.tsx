type Props = {
  label?: string;
};

export function SectionDivider({ label = "§" }: Props) {
  return (
    <div className="essay-divider" role="separator" aria-orientation="horizontal">
      <span>{label}</span>
    </div>
  );
}
