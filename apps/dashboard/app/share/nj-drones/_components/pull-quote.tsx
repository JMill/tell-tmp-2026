import { MotionReveal } from "@/app/_components/motion-reveal";

type Props = {
  attribution?: string;
  children: React.ReactNode;
  reveal?: boolean;
};

export function PullQuote({ attribution, children, reveal = true }: Props) {
  const body = (
    <aside className="essay-pullquote" role="note">
      <p>{children}</p>
      {attribution ? <cite>{attribution}</cite> : null}
    </aside>
  );
  return reveal ? <MotionReveal>{body}</MotionReveal> : body;
}
