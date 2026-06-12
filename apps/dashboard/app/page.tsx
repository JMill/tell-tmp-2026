import { Suspense } from "react";

import { CorpusSummary } from "./_components/corpus-summary";
import { DocumentList } from "./_components/document-list";
import { HypothesisChart } from "./_components/hypothesis-chart";
import { IndependenceGraphSection } from "./_components/independence-graph-section";
import { IndependenceTable } from "./_components/independence-table";
import { IviChart } from "./_components/ivi-chart";
import { NvdChart } from "./_components/nvd-chart";
import { SensemakingAnnotations } from "./_components/sensemaking-annotations";
import { TeardownToggle } from "./_components/teardown-toggle";

export const dynamic = "force-dynamic";

const DEFAULT_CORPUS = "nj-drones-2026-04-08";
const DEFAULT_TOPIC = "nj-drones";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ teardown?: string }>;
}) {
  const params = await searchParams;
  const teardown = params.teardown === "true";

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 font-sans sm:gap-12 sm:px-8 sm:py-16">
      <header className="flex flex-col gap-2 border-b border-border-primary pb-6 sm:pb-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <p className="text-xs uppercase tracking-[0.2em] text-text-muted">
            OSINT Weak Signal Detection · Stage 2
          </p>
          <TeardownToggle active={teardown} />
        </div>
        <h1 className="text-2xl font-medium leading-tight text-text-primary sm:text-4xl">
          Sensemaking under uncertainty
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-text-secondary">
          A human-machine pipeline for policy-relevant weak signal detection in
          ambiguous information environments. This is the retrospective working
          view against the New Jersey aerial phenomena corpus: a frozen
          analysis build, not a live feed. Each chart measures one failure
          mode of an information environment under uncertainty.
        </p>
        <nav className="flex flex-wrap gap-x-5 gap-y-1 pt-1 text-sm">
          <a
            href="/brief"
            className="text-accent underline decoration-accent/40 underline-offset-4 hover:decoration-accent"
          >
            Start with the one-page research brief
          </a>
          <a
            href="/tmp26"
            className="text-accent underline decoration-accent/40 underline-offset-4 hover:decoration-accent"
          >
            CMU TMP 2026 talk slides
          </a>
        </nav>
      </header>

      <SensemakingAnnotations teardown={teardown} />

      <Suspense fallback={<CorpusSummarySkeleton />}>
        <CorpusSummary corpusVersion={DEFAULT_CORPUS} teardown={teardown} />
      </Suspense>

      <Suspense fallback={<IviSkeleton />}>
        <IviChart topic={DEFAULT_TOPIC} teardown={teardown} />
      </Suspense>

      <Suspense fallback={<IviSkeleton />}>
        <HypothesisChart topic={DEFAULT_TOPIC} corpusVersion={DEFAULT_CORPUS} teardown={teardown} />
      </Suspense>

      <Suspense fallback={<IviSkeleton />}>
        <NvdChart topic={DEFAULT_TOPIC} corpusVersion={DEFAULT_CORPUS} teardown={teardown} />
      </Suspense>

      <Suspense fallback={<IviSkeleton />}>
        <IndependenceTable topic={DEFAULT_TOPIC} corpusVersion={DEFAULT_CORPUS} teardown={teardown} />
      </Suspense>

      <Suspense fallback={<IviSkeleton />}>
        <IndependenceGraphSection topic={DEFAULT_TOPIC} corpusVersion={DEFAULT_CORPUS} />
      </Suspense>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
          <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
            Recent Documents
          </h2>
          <span className="text-xs text-text-muted">corpus: {DEFAULT_CORPUS}</span>
        </div>
        <Suspense fallback={<DocumentListSkeleton />}>
          <DocumentList corpusVersion={DEFAULT_CORPUS} />
        </Suspense>
      </section>

      <footer className="flex flex-col gap-1 border-t border-border-primary pt-6 text-xs leading-relaxed text-text-muted">
        <p>
          Jonathan Miller · Doctor of Engineering praxis, Penn State College of
          Engineering. Presented at the CMU Technology, Management, and Policy
          Graduate Consortium, June 15, 2026.
        </p>
        <p>
          Cite as: Miller, TELL pipeline, Penn State D.Eng. praxis, 2026.
          Method definitions and headline findings are on the{" "}
          <a
            href="/brief"
            className="text-accent underline decoration-accent/40 underline-offset-4 hover:decoration-accent"
          >
            research brief
          </a>
          .
        </p>
      </footer>
    </main>
  );
}

function CorpusSummarySkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-6">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="flex h-28 animate-pulse flex-col justify-between rounded-sm border border-border-primary bg-surface-stat p-5"
        >
          <div className="h-3 w-24 rounded bg-skeleton" />
          <div className="h-8 w-16 rounded bg-skeleton" />
        </div>
      ))}
    </div>
  );
}

function DocumentListSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="flex animate-pulse flex-col gap-2 border-b border-border-primary pb-3"
        >
          <div className="h-4 w-3/4 rounded bg-skeleton" />
          <div className="h-3 w-1/2 rounded bg-skeleton" />
        </div>
      ))}
    </div>
  );
}

function IviSkeleton() {
  return (
    <div className="flex h-64 animate-pulse flex-col gap-3 rounded-sm border border-border-primary bg-surface-card p-6">
      <div className="h-3 w-40 rounded bg-skeleton" />
      <div className="flex-1 rounded bg-skeleton opacity-40" />
    </div>
  );
}
