/**
 * Server-only database queries for the dashboard.
 *
 * Imported by Server Components. Never imported in Client Components.
 */
import "server-only";
import { and, asc, desc, eq, sql } from "drizzle-orm";

import { db, tables } from "@tells-fyi/db";

export type CorpusStats = {
  totalDocuments: number;
  sourcesCount: number;
  latestDocumentTitle: string | null;
};

export async function getCorpusStats(corpusVersion: string): Promise<CorpusStats> {
  const [countRow] = await db
    .select({ total: sql<number>`count(*)::int` })
    .from(tables.documents)
    .where(eq(tables.documents.corpusVersion, corpusVersion));

  const [sourceCountRow] = await db
    .select({ total: sql<number>`count(distinct ${tables.documents.sourceId})::int` })
    .from(tables.documents)
    .where(eq(tables.documents.corpusVersion, corpusVersion));

  const [latest] = await db
    .select({ title: tables.documents.title })
    .from(tables.documents)
    .where(eq(tables.documents.corpusVersion, corpusVersion))
    .orderBy(desc(tables.documents.fetchedAt))
    .limit(1);

  return {
    totalDocuments: countRow?.total ?? 0,
    sourcesCount: sourceCountRow?.total ?? 0,
    latestDocumentTitle: latest?.title ?? null,
  };
}

export type DocumentRow = {
  id: string;
  title: string | null;
  url: string;
  sourceDomain: string;
  sourceKind: string;
  fetchedAt: Date;
  publishedAt: Date | null;
};

export async function listRecentDocuments(
  corpusVersion: string,
  limit = 25,
): Promise<DocumentRow[]> {
  const rows = await db
    .select({
      id: tables.documents.id,
      title: tables.documents.title,
      url: tables.documents.url,
      sourceDomain: tables.sources.domain,
      sourceKind: tables.sources.kind,
      fetchedAt: tables.documents.fetchedAt,
      publishedAt: tables.documents.publishedAt,
    })
    .from(tables.documents)
    .innerJoin(tables.sources, eq(tables.sources.id, tables.documents.sourceId))
    .where(eq(tables.documents.corpusVersion, corpusVersion))
    .orderBy(desc(tables.documents.fetchedAt))
    .limit(limit);

  return rows;
}

export type IviPoint = {
  windowEnd: Date;
  discourseCount: number;
  authoritativeCount: number;
  value: number;
};

/**
 * Load the IVI time series for a topic at a given window width, sorted
 * chronologically. Used by the dashboard to render the IVI chart.
 */
export async function getIviSeries(
  topic: string,
  windowDays = 7,
): Promise<IviPoint[]> {
  const rows = await db
    .select({
      windowEnd: tables.signalIvi.windowEnd,
      discourseCount: tables.signalIvi.discourseCount,
      authoritativeCount: tables.signalIvi.authoritativeCount,
      value: tables.signalIvi.value,
    })
    .from(tables.signalIvi)
    .where(
      and(
        eq(tables.signalIvi.topic, topic),
        eq(tables.signalIvi.windowDays, windowDays),
      ),
    )
    .orderBy(asc(tables.signalIvi.windowEnd));

  return rows;
}

export type HypothesisDistributionPoint = {
  day: Date;
  documentCount: number;
  distribution: Record<string, number>;
  entropy: number;
  modalHypothesis: string;
  modalProbability: number;
};

/**
 * Load the per-day H1-H5 distributions for a topic, sorted chronologically.
 * Used by the dashboard to render the hypothesis-evolution chart.
 */
export async function getHypothesisDistributionSeries(
  topic: string,
  corpusVersion: string,
  promptVersion = "h15-v1",
  model = "claude-haiku-4-5-20251001",
): Promise<HypothesisDistributionPoint[]> {
  const rows = await db
    .select({
      day: tables.hypothesisDistributions.day,
      documentCount: tables.hypothesisDistributions.documentCount,
      distribution: tables.hypothesisDistributions.distribution,
      entropy: tables.hypothesisDistributions.entropy,
      modalHypothesis: tables.hypothesisDistributions.modalHypothesis,
      modalProbability: tables.hypothesisDistributions.modalProbability,
    })
    .from(tables.hypothesisDistributions)
    .where(
      and(
        eq(tables.hypothesisDistributions.topic, topic),
        eq(tables.hypothesisDistributions.corpusVersion, corpusVersion),
        eq(tables.hypothesisDistributions.promptVersion, promptVersion),
        eq(tables.hypothesisDistributions.model, model),
      ),
    )
    .orderBy(asc(tables.hypothesisDistributions.day));

  return rows;
}

// ---------------------------------------------------------------------------
// NVD queries
// ---------------------------------------------------------------------------

export type NvdPoint = {
  narrativeSlug: string;
  windowEnd: Date;
  narrativeVelocity: number;
  evidenceVelocity: number;
  nvdValue: number;
};

export async function getNvdSeries(
  topic: string,
  corpusVersion: string,
  windowDays = 3,
): Promise<NvdPoint[]> {
  const rows = await db
    .select({
      narrativeSlug: tables.signalNvd.narrativeSlug,
      windowEnd: tables.signalNvd.windowEnd,
      narrativeVelocity: tables.signalNvd.narrativeVelocity,
      evidenceVelocity: tables.signalNvd.evidenceVelocity,
      nvdValue: tables.signalNvd.nvdValue,
    })
    .from(tables.signalNvd)
    .where(
      and(
        eq(tables.signalNvd.topic, topic),
        eq(tables.signalNvd.corpusVersion, corpusVersion),
        eq(tables.signalNvd.windowDays, windowDays),
      ),
    )
    .orderBy(
      asc(tables.signalNvd.narrativeSlug),
      asc(tables.signalNvd.windowEnd),
    );

  return rows;
}

// ---------------------------------------------------------------------------
// Source Independence Graph queries
// ---------------------------------------------------------------------------

export type IndependenceRow = {
  narrativeSlug: string;
  narrativeLabel: string;
  originLabel: string;
  totalDocuments: number;
  uniqueDomains: number;
  independentSources: number;
  amplifierSources: number;
  independenceScore: number;
  amplificationRatio: number;
};

export async function getIndependenceRows(
  topic: string,
  corpusVersion: string,
): Promise<IndependenceRow[]> {
  const rows = await db
    .select({
      narrativeSlug: tables.signalIndependence.narrativeSlug,
      narrativeLabel: tables.signalIndependence.narrativeLabel,
      originLabel: tables.signalIndependence.originLabel,
      totalDocuments: tables.signalIndependence.totalDocuments,
      uniqueDomains: tables.signalIndependence.uniqueDomains,
      independentSources: tables.signalIndependence.independentSources,
      amplifierSources: tables.signalIndependence.amplifierSources,
      independenceScore: tables.signalIndependence.independenceScore,
      amplificationRatio: tables.signalIndependence.amplificationRatio,
    })
    .from(tables.signalIndependence)
    .where(
      and(
        eq(tables.signalIndependence.topic, topic),
        eq(tables.signalIndependence.corpusVersion, corpusVersion),
      ),
    )
    .orderBy(asc(tables.signalIndependence.independenceScore));

  return rows;
}
