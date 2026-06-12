"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  delay?: number;
  amount?: number;
};

/**
 * Reveal a block with a single 500ms fade + lift the first time it enters
 * the viewport. Designed for editorial figures and pull quotes on the
 * share-route essays. Honours `prefers-reduced-motion` by short-circuiting
 * to a static render.
 */
export function MotionReveal({ children, delay = 0, amount = 0.2 }: Props) {
  const reduceMotion = useReducedMotion();

  if (reduceMotion) {
    return <>{children}</>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
