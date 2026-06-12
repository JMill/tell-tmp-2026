"use client";

import {
  ReactFlow,
  type Node,
  type Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

type NarrativeData = {
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

type Props = {
  rows: NarrativeData[];
};

/**
 * React Flow graph visualization for the Source Independence Graph.
 *
 * For echo-chamber narratives (independence score <= 2), renders a radial
 * layout: the origin source at center, amplifier domains radiating outward.
 * For independent narratives, renders a cluster of peer nodes.
 *
 * This is the visual complement to the independence-table.tsx. The table
 * shows the numbers; the graph shows the topology.
 */
export function IndependenceGraph({ rows }: Props) {
  const echoNarratives = rows.filter(
    (r) => r.independenceScore <= 2 && r.amplificationRatio >= 2 && r.totalDocuments > 0,
  );

  if (echoNarratives.length === 0) {
    return (
      <p className="text-xs text-text-muted">
        No echo-chamber narratives to visualize.
      </p>
    );
  }

  const nodes: Node[] = [];
  const edges: Edge[] = [];

  let yOffset = 0;

  for (const narrative of echoNarratives) {
    const centerX = 200;
    const centerY = yOffset + 120;
    const radius = 140;
    const ampCount = narrative.amplifierSources;

    // Origin node (center)
    const originId = `${narrative.narrativeSlug}-origin`;
    nodes.push({
      id: originId,
      position: { x: centerX, y: centerY },
      data: {
        label: narrative.originLabel || "Origin",
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        background: "var(--accent)",
        color: "#fff",
        border: "2px solid var(--accent-border-dark)",
        borderRadius: "4px",
        padding: "8px 12px",
        fontSize: "11px",
        fontWeight: 600,
        width: "auto",
        textAlign: "center" as const,
      },
    });

    // Narrative label node (above center)
    nodes.push({
      id: `${narrative.narrativeSlug}-label`,
      position: { x: centerX - 20, y: yOffset },
      data: {
        label: `${narrative.narrativeLabel} · score ${narrative.independenceScore} · ${narrative.amplificationRatio.toFixed(1)}× amplification`,
      },
      selectable: false,
      draggable: false,
      style: {
        background: "transparent",
        border: "none",
        fontSize: "10px",
        color: "var(--text-muted)",
        textTransform: "uppercase" as const,
        letterSpacing: "0.1em",
        width: 280,
        textAlign: "center" as const,
      },
    });

    // Amplifier nodes (radial)
    for (let i = 0; i < ampCount; i++) {
      const angle = (2 * Math.PI * i) / ampCount - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      const ampId = `${narrative.narrativeSlug}-amp-${i}`;

      nodes.push({
        id: ampId,
        position: { x, y },
        data: { label: `Outlet ${i + 1}` },
        sourcePosition: Position.Left,
        targetPosition: Position.Right,
        style: {
          background: "var(--surface-teardown)",
          color: "var(--text-secondary)",
          border: "1px solid var(--border-primary)",
          borderRadius: "4px",
          padding: "6px 10px",
          fontSize: "10px",
          width: "auto",
        },
      });

      edges.push({
        id: `${originId}-${ampId}`,
        source: originId,
        target: ampId,
        animated: true,
        style: { stroke: "var(--accent)", strokeWidth: 1.5, opacity: 0.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "var(--accent)",
          width: 12,
          height: 12,
        },
      });
    }

    yOffset += radius * 2 + 100;
  }

  return (
    <div
      className="-mx-4 border-y border-border-primary bg-surface-card sm:mx-0 sm:rounded-sm sm:border-x"
      style={{ height: Math.max(yOffset, 300) }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        minZoom={0.3}
        maxZoom={1.5}
      />
    </div>
  );
}
