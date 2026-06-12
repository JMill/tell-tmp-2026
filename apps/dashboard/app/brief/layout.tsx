import type { Metadata } from "next";
import { Source_Serif_4 } from "next/font/google";

const serif = Source_Serif_4({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "TELL · Sensemaking Quality, Not Prediction",
  description:
    "Three measures for detecting narrative capture in real time. A research overview of the TELL pipeline.",
};

export default function BriefLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div
      className={`${serif.variable} brief-root min-h-full bg-surface-primary py-10 sm:py-14 print:py-0`}
    >
      <article className="brief-prose">{children}</article>
    </div>
  );
}
