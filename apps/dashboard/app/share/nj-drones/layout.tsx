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
  title: "The Forty-Seven-Day Vacuum",
  description:
    "What the New Jersey drones case looks like inside a weak-signal pipeline. An unlisted draft.",
  robots: { index: false, follow: false, nocache: true },
};

export default function ShareLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className={`${serif.variable} essay-root min-h-full bg-surface-primary py-16 sm:py-24`}>
      <article className="essay-prose">{children}</article>
    </div>
  );
}
