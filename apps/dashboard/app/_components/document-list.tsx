import { listRecentDocuments } from "@/lib/queries";

type Props = {
  corpusVersion: string;
};

export async function DocumentList({ corpusVersion }: Props) {
  const documents = await listRecentDocuments(corpusVersion, 25);

  if (documents.length === 0) {
    return (
      <p className="rounded-sm border border-dashed border-border-secondary bg-surface-card p-6 text-sm text-text-secondary">
        No documents ingested yet. Run{" "}
        <code className="rounded bg-code-bg px-1 py-0.5 font-mono text-xs">
          uv run signals ingest wayback --url &lt;url&gt;
        </code>{" "}
        from <code className="font-mono text-xs">dev/tell/</code> to
        populate the corpus.
      </p>
    );
  }

  return (
    <ul className="flex flex-col">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="flex flex-col gap-1 border-b border-border-primary py-4 last:border-b-0"
        >
          <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
            <h3 className="text-base font-medium leading-snug text-text-primary">
              {doc.title ?? "(no title)"}
            </h3>
            <span className="shrink-0 text-xs uppercase tracking-wide text-text-muted">
              {doc.sourceKind}
            </span>
          </div>
          <p className="truncate text-xs font-mono text-text-muted">
            {doc.sourceDomain}
          </p>
          <p className="text-xs text-text-muted">
            fetched {formatDate(doc.fetchedAt)}
            {doc.publishedAt
              ? ` · published ${formatDate(doc.publishedAt)}`
              : null}
          </p>
        </li>
      ))}
    </ul>
  );
}

function formatDate(d: Date): string {
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
