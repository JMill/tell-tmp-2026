import type { ReactNode } from "react";
import { MotionReveal } from "@/app/_components/motion-reveal";

type Props = {
  caption?: ReactNode;
  children: ReactNode;
  reveal?: boolean;
};

export function FigureBlock({ caption, children, reveal = true }: Props) {
  const body = (
    <figure className="my-10 flex flex-col gap-3">
      <div className="font-sans">{children}</div>
      {caption && <figcaption className="font-sans">{caption}</figcaption>}
    </figure>
  );
  return reveal ? <MotionReveal>{body}</MotionReveal> : body;
}
