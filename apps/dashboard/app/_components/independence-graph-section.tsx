import { getIndependenceRows } from "@/lib/queries";
import { IndependenceGraph } from "./independence-graph";

type Props = {
  topic: string;
  corpusVersion: string;
};

/**
 * Server Component wrapper for the Source Independence Graph visualization.
 *
 * Fetches independence data on the server, then passes it to the React Flow
 * client component. This pattern keeps the database query server-side while
 * enabling the interactive graph on the client.
 */
export async function IndependenceGraphSection({ topic, corpusVersion }: Props) {
  const rows = await getIndependenceRows(topic, corpusVersion);
  const active = rows.filter((r) => r.totalDocuments > 0);

  if (active.length === 0) return null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-xs uppercase tracking-[0.2em] text-text-muted">
          Echo Chamber Topology
        </h2>
        <p className="text-sm text-text-secondary">
          Radial graph of narratives with independence score ≤ 2.
          Origin source at center, amplifying outlets radiating outward.
        </p>
      </div>
      <IndependenceGraph rows={active} />
      <p className="text-xs leading-relaxed text-text-secondary">
        Each arrow represents a single originating claim amplified across
        outlets without independent corroboration. The Iranian Mothership
        narrative is the clearest case: Rep. Van Drew&apos;s Fox News statement
        was echoed by six domains, none providing independent evidence of
        Iranian involvement. See{" "}
        <code className="font-mono text-xs">docs/methods/independence.md</code>{" "}
        for the full method documentation.
      </p>
    </div>
  );
}
