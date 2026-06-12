import { getCorpusStats } from "@/lib/queries";
import { corpusTeardownEntries } from "@/lib/teardown-content";
import { TeardownPanel } from "./teardown-panel";

type Props = {
  corpusVersion: string;
  teardown?: boolean;
};

export async function CorpusSummary({ corpusVersion, teardown = false }: Props) {
  const stats = await getCorpusStats(corpusVersion);

  return (
    <section className={`flex flex-col gap-4 ${teardown ? "rounded-sm border-l-2 border-accent bg-surface-teardown p-4" : ""}`}>
      {teardown && (
        <p className="text-[10px] uppercase tracking-[0.15em] text-accent">
          <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-accent align-middle" />
          teardown
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-6">
        <Stat label="Documents" value={stats.totalDocuments.toLocaleString()} />
        <Stat label="Sources" value={stats.sourcesCount.toLocaleString()} />
        <Stat
          label="Latest title"
          value={
            stats.latestDocumentTitle
              ? truncate(stats.latestDocumentTitle, 40)
              : "— none yet —"
          }
          small
        />
      </div>

      {teardown && (
        <TeardownPanel
          entries={corpusTeardownEntries({ corpusVersion })}
        />
      )}
    </section>
  );
}

function Stat({
  label,
  value,
  small = false,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="flex flex-col justify-between rounded-sm border border-border-primary bg-surface-stat p-5">
      <p className="text-xs uppercase tracking-[0.18em] text-text-muted">
        {label}
      </p>
      <p
        className={
          small
            ? "mt-3 text-sm font-medium leading-snug text-text-primary"
            : "mt-3 text-4xl font-medium text-text-primary"
        }
      >
        {value}
      </p>
    </div>
  );
}

function truncate(s: string, n: number): string {
  return s.length <= n ? s : s.slice(0, n - 1) + "…";
}
