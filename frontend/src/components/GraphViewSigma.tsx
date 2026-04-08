"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { api, type GraphEdge, type GraphNode, type GraphResponse, type KgNodeDetails } from "@/lib/api";
import { hexToRgbaBytes, loadCircleNodeProgram, loadDashedEdgeProgram } from "@/lib/sigmaPrograms";

import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";

type EdgeType = "domain_case" | "case_similar" | "cluster_case" | string;
type SigmaConstructor = new (graph: Graph, container: HTMLElement, settings: SigmaSettings) => SigmaLike;

interface SigmaLike {
  refresh?: () => void;
  resize?: () => void;
  kill?: () => void;
  setSetting?: (key: string, value: unknown) => void;
  getCamera?: () => {
    getState?: () => { ratio?: number };
    on?: (event: string, callback: () => void) => void;
  };
  getMouseCaptor?: () => {
    on?: (event: string, callback: (event: MouseCaptorEvent) => void) => void;
  };
  on: (event: string, callback: (event?: SigmaNodeEvent) => void) => void;
}

interface SigmaSettings {
  renderEdgeLabels?: boolean;
  labelRenderedSizeThreshold?: number;
  defaultLabelColor?: string;
  defaultNodeType?: string;
  zIndex?: boolean;
  allowInvalidContainer?: boolean;
  edgeProgramClasses?: Record<string, unknown>;
  nodeProgramClasses?: Record<string, unknown>;
  nodeHoverProgramClasses?: Record<string, unknown>;
  nodeHoverRenderer?: (ctx: CanvasRenderingContext2D, data: SigmaNodeRenderData, settings: LabelRendererSettings) => void;
}

interface SigmaNodeRenderData {
  key?: string;
  id?: string;
  label?: string;
  size?: number;
  x: number;
  y: number;
  nodeType?: string;
  color?: string;
  originalColor?: string;
  borderWidth?: number;
  glow?: number;
  [key: string]: unknown;
}

interface LabelRendererSettings {
  labelFont?: string;
  labelSize?: number;
  [key: string]: unknown;
}

interface SigmaNodeAttributes {
  color?: string;
  originalColor?: string;
  size?: number;
  zIndex?: number;
  hidden?: boolean;
  glow?: number;
  borderWidth?: number;
  [key: string]: unknown;
}

interface SigmaEdgeAttributes {
  color?: string;
  originalColor?: string;
  size?: number;
  zIndex?: number;
  hidden?: boolean;
  type?: string;
  edgeType?: string;
  colorRGBA?: [number, number, number, number] | number[];
  strength?: number;
  [key: string]: unknown;
}

interface MouseCaptorEvent {
  x?: number;
  y?: number;
}

interface SigmaNodeEvent {
  node?: string;
}

interface WorkerLayoutLike {
  start?: () => void;
  stop?: () => void;
  kill?: () => void;
}

interface GraphCurveModule {
  default?: unknown;
  EdgeCurveProgram?: unknown;
  EdgeCurve?: unknown;
  createEdgeCurveProgram?: () => unknown;
}

interface GraphEdgeWithEvidence extends GraphEdge {
  strength?: number;
  confidence?: number;
}

const THEME = {
  background: "#f8fafc",
  edgeDomain: "rgba(100, 116, 139, 0.20)",
  edgeSimilar: "rgba(249, 115, 22, 0.58)",
  edgeCluster: "rgba(56, 189, 248, 0.22)",
  edgeFocus: "rgba(99, 102, 241, 0.76)",
  nodeCase: {
    color: "#6b7280",
  },
  nodeDomain: {
    color: "#3b82f6",
  },
  nodeCluster: {
    color: "#14b8a6",
  },
};

const DOMAIN_COLORS: Record<string, string> = {
  TECH: "#2563eb",
  FIN: "#16a34a",
  CAR: "#f59e0b",
  HEALTH: "#dc2626",
  EDU: "#7c3aed",
  LEGAL: "#0891b2",
  BUSINESS: "#ea580c",
  LIFE: "#db2777",
  TEC: "#2563eb",
  MGT: "#0ea5e9",
  REL: "#a855f7",
  HEA: "#dc2626",
  LIF: "#db2777",
};

function pickNodeColor(n: GraphNode): string {
  if (n.type === "domain") {
    const main = (n.domain || n.label || "").split("-")[0];
    return DOMAIN_COLORS[main] || THEME.nodeDomain.color;
  }
  if (n.type === "cluster") return THEME.nodeCluster.color;
  return THEME.nodeCase.color;
}

function withAlpha(hex: string, alpha: number): [number, number, number, number] {
  return hexToRgbaBytes(hex, alpha);
}

function rgbaCssToBytes(rgba: string): [number, number, number, number] {
  const m = rgba
    .replace(/\s+/g, "")
    .match(/^rgba\((\d+),(\d+),(\d+),(\d*\.?\d+)\)$/i);
  if (!m) return [156, 163, 175, 160];
  const r = Math.max(0, Math.min(255, Number(m[1])));
  const g = Math.max(0, Math.min(255, Number(m[2])));
  const b = Math.max(0, Math.min(255, Number(m[3])));
  const a = Math.max(0, Math.min(1, Number(m[4])));
  return [r, g, b, Math.round(a * 255)];
}

function edgeColor(edgeType: EdgeType): string {
  if (edgeType === "case_similar") return THEME.edgeSimilar;
  if (edgeType === "cluster_case") return THEME.edgeCluster;
  return THEME.edgeDomain;
}

function hash01(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 1000) / 1000;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

function strengthToRgba(strength: number, alpha = 0.65): [number, number, number, number] {
  const s = clamp(strength, 0, 1);
  const a = Math.round(clamp(alpha, 0, 1) * 255);
  const b1: [number, number, number] = [59, 130, 246];
  const y1: [number, number, number] = [234, 179, 8];
  const r1: [number, number, number] = [244, 63, 94];

  if (s <= 0.5) {
    const t = s / 0.5;
    return [
      Math.round(lerp(b1[0], y1[0], t)),
      Math.round(lerp(b1[1], y1[1], t)),
      Math.round(lerp(b1[2], y1[2], t)),
      a,
    ];
  }
  const t = (s - 0.5) / 0.5;
  return [
    Math.round(lerp(y1[0], r1[0], t)),
    Math.round(lerp(y1[1], r1[1], t)),
    Math.round(lerp(y1[2], r1[2], t)),
    a,
  ];
}

function clamp01(v: unknown): number {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function compactLabel(text: string, max = 16): string {
  const t = (text || "").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max)}...`;
}

function GraphCanvas({
  graph,
  selectedId,
  setSelectedId,
  hoveredId,
  setHoveredId,
  showAllEdges,
  showLabels,
  showTypeChips,
  focusRedEdges,
  similarEdgeColorMode,
  allEdgesColorMode,
  onNodeClick,
}: {
  graph: GraphResponse;
  selectedId: string;
  setSelectedId: (id: string) => void;
  hoveredId: string;
  setHoveredId: (id: string) => void;
  showAllEdges: boolean;
  showLabels: boolean;
  showTypeChips: boolean;
  focusRedEdges: boolean;
  similarEdgeColorMode: "fixed" | "gradient";
  allEdgesColorMode: "default" | "confidence_gradient";
  onNodeClick?: (node: GraphNode) => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sigmaRef = useRef<SigmaLike | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const fa2WorkerRef = useRef<WorkerLayoutLike | null>(null);
  const stateRef = useRef<{
    selectedId: string;
    hoveredId: string;
    showAllEdges: boolean;
    showLabels: boolean;
    showTypeChips: boolean;
    focusRedEdges: boolean;
    similarEdgeColorMode: "fixed" | "gradient";
    allEdgesColorMode: "default" | "confidence_gradient";
  }>({
    selectedId: "",
    hoveredId: "",
    showAllEdges: false,
    showLabels: true,
    showTypeChips: true,
    focusRedEdges: true,
    similarEdgeColorMode: "fixed",
    allEdgesColorMode: "default",
  });
  const neighborRef = useRef<Set<string>>(new Set());
  const dragRef = useRef<{ down: boolean; moved: boolean; x: number; y: number }>({
    down: false,
    moved: false,
    x: 0,
    y: 0,
  });

  useEffect(() => {
    stateRef.current = {
      selectedId,
      hoveredId,
      showAllEdges,
      showLabels,
      showTypeChips,
      focusRedEdges,
      similarEdgeColorMode,
      allEdgesColorMode,
    };
    const g = graphRef.current;
    const focus = selectedId || hoveredId;
    const neighbor = new Set<string>();
    if (g && focus && g.hasNode(focus)) {
      neighbor.add(focus);
      g.forEachNeighbor(focus, (n: string) => neighbor.add(n));
    }
    neighborRef.current = neighbor;
    try {
      sigmaRef.current?.refresh?.();
    } catch {}
    try {
      const renderer = sigmaRef.current;
      const ratio = renderer?.getCamera?.()?.getState?.()?.ratio;
      const r = typeof ratio === "number" ? ratio : 1;
      const thr = stateRef.current.showLabels ? (r > 1.35 ? 999 : r > 1.15 ? 20 : 12) : 999;
      renderer?.setSetting?.("labelRenderedSizeThreshold", thr);
      renderer?.refresh?.();
    } catch {}
  }, [selectedId, hoveredId, showAllEdges, showLabels, showTypeChips, focusRedEdges, similarEdgeColorMode, allEdgesColorMode]);

  // Keep Sigma in sync with layout changes (e.g., Node Details drawer opens)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let disposed = false;
    let ro: ResizeObserver | null = null;

    const apply = () => {
      if (disposed) return;
      const r = sigmaRef.current;
      if (!r) return;
      try {
        // Some Sigma builds expose resize()
        r.resize?.();
      } catch {}
      try {
        r.refresh?.();
      } catch {}
    };

    try {
      ro = new ResizeObserver(() => apply());
      ro.observe(container);
    } catch {
      // ignore
    }

    // Initial best-effort
    setTimeout(apply, 0);

    return () => {
      disposed = true;
      try {
        ro?.disconnect?.();
      } catch {}
      ro = null;
    };
  }, []);

  // Extra refresh after selecting a node (prevents occasional blank frame)
  useEffect(() => {
    const r = sigmaRef.current;
    if (!r) return;
    const t = setTimeout(() => {
      try {
        r.refresh?.();
      } catch {}
    }, 0);
    return () => clearTimeout(t);
  }, [selectedId]);

  // init & load
  useEffect(() => {
    let disposed = false;
    let ro: ResizeObserver | null = null;
    let started = false;
    (async () => {
      const container = containerRef.current;
      if (!container) return;

      const ensureSize = async (): Promise<boolean> => {
        if (disposed) return false;
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (w > 0 && h > 0) return true;
        return await new Promise<boolean>((resolve) => {
          let done = false;
          const finish = (ok: boolean) => {
            if (done) return;
            done = true;
            try {
              ro?.disconnect?.();
            } catch {}
            ro = null;
            resolve(ok);
          };

          try {
            ro = new ResizeObserver(() => {
              if (disposed) return finish(false);
              if (container.clientWidth > 0 && container.clientHeight > 0) finish(true);
            });
            ro.observe(container);
          } catch {
            // ResizeObserver might be unavailable in some environments
          }

          setTimeout(() => {
            if (disposed) return finish(false);
            finish(container.clientWidth > 0 && container.clientHeight > 0);
          }, 250);
        });
      };

      const ok = await ensureSize();
      if (!ok || disposed) return;
      if (started) return;
      started = true;

      const mod = (await import("sigma")) as unknown as { default?: SigmaConstructor };
      const Sigma = mod.default as SigmaConstructor;
      const CircleNodeProgram = await loadCircleNodeProgram();
      const DashedEdgeProgram = await loadDashedEdgeProgram();

      let CurveEdgeProgram: unknown = null;
      try {
        const cmod = (await import("@sigma/edge-curve")) as GraphCurveModule;
        const factory = cmod.createEdgeCurveProgram;
        if (typeof factory === "function") {
          CurveEdgeProgram = factory();
        } else {
          CurveEdgeProgram = cmod.default || cmod.EdgeCurveProgram || cmod.EdgeCurve || null;
        }
      } catch {}

      const enableCurves = Boolean(CurveEdgeProgram);

      const g = new Graph();

      for (const n of graph.nodes) {
        if (g.hasNode(n.id)) continue;
        const baseColor = pickNodeColor(n);
        const size = n.type === "domain" ? 8.5 : n.type === "cluster" ? 7.2 : 4.6;
        const fill = n.type === "domain" ? withAlpha(baseColor, 0.16) : withAlpha(baseColor, 1.0);
        const border = withAlpha(baseColor, 1.0);
        g.addNode(n.id, {
          label: compactLabel(n.label || n.id),
          fullLabel: n.label,
          x: Math.random() * 10 - 5,
          y: Math.random() * 10 - 5,
          size,
          color: baseColor,
          originalColor: baseColor,
          fillColorRGBA: fill,
          borderColorRGBA: border,
          borderWidth: n.type === "domain" ? 2.2 : 1.4,
          glow: 0.0,
          nodeType: n.type,
        });
      }

      // Progressive edges insertion to keep main thread responsive on large graphs
      const edgesAll = graph.edges.slice();
      const batchSize = g.order > 800 ? 400 : g.order > 300 ? 700 : 1200;
      let idx = 0;
      const applyDegreeSizing = () => {
        try {
          g.forEachNode((nodeId: string) => {
            const deg = g.degree(nodeId);
            const nodeType = String(g.getNodeAttribute(nodeId, "nodeType") || "");
            const base = nodeType === "domain" ? 8.5 : nodeType === "cluster" ? 7.2 : 4.6;
            const boost = Math.min(3.2, Math.log2(deg + 1) * 0.9);
            const nextSize = Math.max(base, base + boost);
            g.setNodeAttribute(nodeId, "size", Number(nextSize.toFixed(2)));
            if (deg >= 8) {
              g.setNodeAttribute(nodeId, "borderWidth", Math.max(2.2, Number(g.getNodeAttribute(nodeId, "borderWidth") || 1.4)));
            }
          });
        } catch {
          // ignore sizing failures
        }
      };
      const addEdgeBatch = () => {
        if (disposed) return;
        const end = Math.min(edgesAll.length, idx + batchSize);
        for (; idx < end; idx++) {
          const e = edgesAll[idx];
          if (g.hasEdge(e.id)) continue;
          if (!g.hasNode(e.source) || !g.hasNode(e.target)) continue;
          const src = e.source;
          const tgt = e.target;
          const et = (e.type || e.edge_type || "domain_case") as EdgeType;
          const edgeWithMetrics = e as GraphEdge & { weight?: number; score?: number };
          const strength = clamp01(edgeWithMetrics.weight ?? edgeWithMetrics.score ?? 0.5);
          const c = edgeColor(et);
          const isSimilar = et === "case_similar";
          const colorRGBA = isSimilar ? withAlpha("#ea580c", 0.62) : rgbaCssToBytes(c);

          const baseW = et === "case_similar" ? 1.2 : 1.0;
          const w = strength !== undefined ? baseW + strength * 4.2 : 1.8;

          const key = e.id || `${src}->${tgt}`;

          // Graphology (non-multi) does not allow parallel edges between same node pair.
          // Merge by keeping the strongest visual attributes.
          let existingEdgeKey: string | null = null;
          try {
            if (g.hasEdge(src, tgt)) existingEdgeKey = g.edge(src, tgt) ?? null;
          } catch {}
          if (!existingEdgeKey) {
            try {
              if (g.hasEdge(tgt, src)) existingEdgeKey = g.edge(tgt, src) ?? null;
            } catch {}
          }

          if (existingEdgeKey) {
            try {
              const prevSize = Number(g.getEdgeAttribute(existingEdgeKey, "size") || 0);
              if (w > prevSize) {
                g.setEdgeAttribute(existingEdgeKey, "size", w);
                g.setEdgeAttribute(existingEdgeKey, "color", c);
                g.setEdgeAttribute(existingEdgeKey, "edgeType", et);
                g.setEdgeAttribute(existingEdgeKey, "type", isSimilar ? "dashed" : undefined);
                g.setEdgeAttribute(existingEdgeKey, "colorRGBA", colorRGBA);
                g.setEdgeAttribute(existingEdgeKey, "thickness", w);
              }
            } catch {}
            continue;
          }

          if (g.hasEdge(key)) continue;
          try {
            g.addEdgeWithKey(key, src, tgt, {
              label: ("label" in e ? (e as GraphEdge & { label?: string }).label : undefined),
              color: c,
              size: isSimilar ? w : Math.max(0.6, w * 0.85),
              edgeType: et,
              type: isSimilar ? "dashed" : enableCurves ? "curve" : undefined,
              curvature: enableCurves && !isSimilar ? (hash01(key) - 0.5) * 0.7 : 0,
              colorRGBA,
              thickness: w,
              originalColor: c,
              strength,
            });
          } catch {
            // best-effort: ignore insertion errors
          }
        }
        sigmaRef.current?.refresh?.();
        if (idx < edgesAll.length) {
          setTimeout(addEdgeBatch, 0);
        } else {
          applyDegreeSizing();
          sigmaRef.current?.refresh?.();
        }
      };

      if (disposed) return;
      graphRef.current = g;

      const edgeProgramClasses: Record<string, unknown> = {
        dashed: DashedEdgeProgram,
      };
      if (enableCurves) edgeProgramClasses.curve = CurveEdgeProgram;
      const nodeProgramClasses: Record<string, unknown> = {
        circle: CircleNodeProgram,
      };

      const renderer = new Sigma(g, container, {
        renderEdgeLabels: false,
        labelRenderedSizeThreshold: 0,
        defaultNodeType: "circle",
        defaultLabelColor: "rgba(15,23,42,0.82)",
        zIndex: true,
        allowInvalidContainer: true,
        edgeProgramClasses,
        nodeProgramClasses,
        nodeHoverRenderer: (ctx: CanvasRenderingContext2D, data: SigmaNodeRenderData, settings: LabelRendererSettings) => {
          void settings;
          const focus = stateRef.current.selectedId || stateRef.current.hoveredId;
          const isFocus = focus && data && data.key === focus;
          const size = data.size || 4;
          const x = data.x;
          const y = data.y;

          ctx.save();
          ctx.beginPath();
          ctx.arc(x, y, size + 2.5, 0, Math.PI * 2);
          ctx.strokeStyle = isFocus ? "rgba(37,99,235,0.55)" : "rgba(15,23,42,0.18)";
          ctx.lineWidth = isFocus ? 2.2 : 1.2;
          ctx.stroke();

          if (isFocus) {
            ctx.beginPath();
            ctx.arc(x, y, size + 6.5, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(37,99,235,0.18)";
            ctx.lineWidth = 6;
            ctx.stroke();
          }
          ctx.restore();
        },
      });
      sigmaRef.current = renderer;

      try {
        renderer.setSetting?.("defaultNodeType", "circle");
        renderer.setSetting?.("nodeProgramClasses", nodeProgramClasses);
        renderer.setSetting?.("nodeHoverProgramClasses", nodeProgramClasses);
      } catch {}

      // LOD + focus: reducers (avoid mutating graph in response to hover/click)
      try {
        const nEdges = edgesAll.length;
        const shouldHideEdgesByDefault = nEdges > 2500;
        if (typeof renderer?.setSetting === "function") {
          renderer.setSetting("nodeReducer", (node: string, attrs: SigmaNodeAttributes) => {
            try {
              const { selectedId: sel, hoveredId: hov } = stateRef.current;
              const focus = sel || hov;
              if (!focus) return { ...attrs, hidden: false };

              // Keep focused node very visible.
              if (node === focus) {
                return {
                  ...attrs,
                  hidden: false,
                  color: attrs.originalColor || attrs.color,
                  size: Math.max((attrs.size || 4) * 1.35, 6),
                  zIndex: 2,
                  glow: 1.0,
                  borderWidth: Math.max(Number(attrs.borderWidth || 1.4), 2.8),
                };
              }

              const on = neighborRef.current.has(node);
              if (on)
                return {
                  ...attrs,
                  hidden: false,
                  zIndex: 1,
                  glow: 0.0,
                };

              // Dim non-neighbors but keep them visible (avoid "empty canvas" perception).
              return {
                ...attrs,
                hidden: false,
                color: "rgba(156, 163, 175, 0.55)",
                size: Math.max(2.8, (attrs.size || 4) * 0.9),
                zIndex: 0,
                glow: 0.0,
              };
            } catch {
              return attrs;
            }
          });

          renderer.setSetting("edgeReducer", (edge: string, attrs: SigmaEdgeAttributes) => {
            try {
              const { selectedId: sel, hoveredId: hov, showAllEdges: showAll, focusRedEdges: focusRed, similarEdgeColorMode: simMode } =
                stateRef.current;
              const allMode = stateRef.current.allEdgesColorMode;
              const ratio = renderer.getCamera?.()?.getState?.()?.ratio;
              const zoomedOut = typeof ratio === "number" ? ratio > 1.2 : false;

              const focus = sel || hov;
              const s = g.source(edge);
              const t = g.target(edge);

              const et = attrs.edgeType || attrs.type || "";
              const isSimilar = et === "case_similar" || attrs.type === "dashed";
              const base = attrs.originalColor || attrs.color || edgeColor(et);
              const strength = typeof attrs.strength === "number" ? clamp01(attrs.strength) : 0.5;
              const gradRgba = strengthToRgba(strength, 0.20);
              const gradCss = `rgba(${gradRgba[0]}, ${gradRgba[1]}, ${gradRgba[2]}, ${gradRgba[3] / 255})`;

              // If focusing a node, only keep incident edges visible.
              if (focus) {
                const on = s === focus || t === focus;
                if (on) {
                  if (isSimilar) {
                    return {
                      ...attrs,
                      hidden: false,
                      color: "rgba(234, 88, 12, 0.72)",
                      colorRGBA: simMode === "gradient" ? strengthToRgba(strength, 0.72) : attrs.colorRGBA,
                      size: Math.max(Number(attrs.size || 1), 1.4),
                      zIndex: 2,
                    };
                  }
                  return {
                    ...attrs,
                    hidden: false,
                    color: focusRed ? THEME.edgeFocus : allMode === "confidence_gradient" ? gradCss : base,
                    size: Math.max(Number(attrs.size || 1), 1.6),
                    zIndex: 2,
                  };
                }
                return {
                  ...attrs,
                  hidden: false,
                  color: "rgba(148, 163, 184, 0.08)",
                  size: Math.max(0.5, Number(attrs.size || 0.8) * 0.7),
                  zIndex: 0,
                };
              }

              // Otherwise, apply LOD edge hiding to reduce overdraw.
              if (!showAll && shouldHideEdgesByDefault && zoomedOut) {
                return { ...attrs, hidden: true };
              }

              if (isSimilar) {
                return {
                  ...attrs,
                  hidden: false,
                  color: "rgba(234, 88, 12, 0.55)",
                  colorRGBA: simMode === "gradient" ? strengthToRgba(strength, 0.62) : attrs.colorRGBA,
                  size: Math.max(0.8, Number(attrs.size || 1)),
                  zIndex: 1,
                };
              }

              return {
                ...attrs,
                hidden: false,
                color: allMode === "confidence_gradient" ? gradCss : base,
                size: Math.max(0.6, Number(attrs.size || 0.8)),
                zIndex: 0,
              };
            } catch {
              return attrs;
            }
          });
        }
      } catch {}

      // LOD: update label threshold on camera changes
      try {
        const applyLabelLOD = () => {
          const thr = stateRef.current.showLabels || stateRef.current.showTypeChips ? 0 : 999;
          renderer.setSetting?.("labelRenderedSizeThreshold", thr);
          renderer.refresh?.();
        };
        renderer.getCamera?.()?.on?.("updated", applyLabelLOD);
        applyLabelLOD();
      } catch {}

      // Start ForceAtlas2 in a WebWorker to avoid blocking UI
      try {
        const wmod = (await import("graphology-layout-forceatlas2/worker")) as unknown as { default?: new (graph: Graph, options: { settings: Record<string, number | boolean>; iterationsPerRender: number }) => WorkerLayoutLike };
        const FA2Layout = wmod.default;
        if (!FA2Layout) throw new Error("ForceAtlas2 worker unavailable");
        const nNodes = g.order;
        const layoutSettings = {
          gravity: 0.8,
          scalingRatio: 6,
          strongGravityMode: true,
          slowDown: 2,
        };
        const iterationsPerRender = nNodes > 1200 ? 1 : nNodes > 600 ? 2 : 3;
        const layout = new FA2Layout(g, { settings: layoutSettings, iterationsPerRender });
        fa2WorkerRef.current = layout;
        layout.start?.();

        // Do not keep layout running forever (it causes nodes to drift on interaction).
        // Warm up briefly, then stop for stable UX.
        setTimeout(() => {
          try {
            layout.stop?.();
            layout.kill?.();
            if (fa2WorkerRef.current === layout) fa2WorkerRef.current = null;
            sigmaRef.current?.refresh?.();
          } catch {}
        }, nNodes > 1200 ? 2200 : nNodes > 600 ? 1800 : 1400);
      } catch {
        // fallback to small synchronous iterations for environments without worker bundling
        try {
          const nNodes = g.order;
          const iterations = nNodes > 1200 ? 25 : nNodes > 600 ? 35 : nNodes > 300 ? 55 : 90;
          forceAtlas2.assign(g, { iterations, settings: { gravity: 0.8, scalingRatio: 6, strongGravityMode: true, slowDown: 2 } });
          renderer.refresh?.();
        } catch {}
      }

      // Insert edges after renderer is ready
      addEdgeBatch();

      // A2: custom label renderer (label + small type tag)
      try {
        if (typeof renderer?.setSetting === "function") {
          renderer.setSetting("labelRenderer", (ctx: CanvasRenderingContext2D, data: SigmaNodeRenderData, settings: LabelRendererSettings) => {
            if (!data?.label) return;

            if (!stateRef.current.showLabels && !stateRef.current.showTypeChips) return;

            const ratio = renderer.getCamera?.()?.getState?.()?.ratio;
            const r = typeof ratio === "number" ? ratio : 1;

            const nt = data.nodeType ? String(data.nodeType) : "";
            const isDomain = nt === "domain";
            const isCluster = nt === "cluster";
            const isCase = nt === "case";

            const focus = stateRef.current.selectedId || stateRef.current.hoveredId;
            const isFocus = Boolean(focus && data && (data.key === focus || data.id === focus));

            const typeText = isDomain ? "领域" : isCluster ? "簇" : isCase ? "案例" : nt ? nt : "";

            const showTypeChip =
              Boolean(typeText) &&
              stateRef.current.showTypeChips &&
              (isFocus || (r <= 1.25 && (isDomain || isCluster)) || (r <= 1.05 && (isDomain || isCluster || isCase)));

            const showMainLabel =
              r <= 1.35 &&
              stateRef.current.showLabels &&
              (r <= 1.05 ? true : r <= 1.15 ? isDomain || isCluster : isDomain);

            if (!showTypeChip && !showMainLabel) return;

            const font = settings?.labelFont || "PingFang SC, Microsoft YaHei UI, sans-serif";
            const size = Math.max(11, Math.floor((settings?.labelSize || 12) * (isDomain ? 1.05 : 1.0)));
            const x = data.x;
            const y = data.y;

            const text = String(data.label);
            const padX = 6;
            const padY = 3;
            const radius = 6;

            ctx.save();
            ctx.font = `500 ${size}px ${font}`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            const w = ctx.measureText(text).width;
            const boxW = w + padX * 2;
            const boxH = size + padY * 2;
            const dy = (data.size || 4) + 10;
            const bx = x - boxW / 2;
            const by = y + dy;

            const rr = (xx: number, yy: number, ww: number, hh: number, rr: number) => {
              const r2 = Math.min(rr, ww / 2, hh / 2);
              ctx.beginPath();
              ctx.moveTo(xx + r2, yy);
              ctx.arcTo(xx + ww, yy, xx + ww, yy + hh, r2);
              ctx.arcTo(xx + ww, yy + hh, xx, yy + hh, r2);
              ctx.arcTo(xx, yy + hh, xx, yy, r2);
              ctx.arcTo(xx, yy, xx + ww, yy, r2);
              ctx.closePath();
            };

            if (showMainLabel) {
              rr(bx, by, boxW, boxH, radius);
              ctx.fillStyle = "rgba(255,255,255,0.86)";
              ctx.fill();
              ctx.strokeStyle = isDomain ? "rgba(37,99,235,0.18)" : "rgba(15,23,42,0.10)";
              ctx.lineWidth = 1;
              ctx.stroke();

              ctx.fillStyle = isDomain ? "rgba(15,23,42,0.86)" : "rgba(15,23,42,0.78)";
              ctx.fillText(text, x, by + boxH / 2);
            }

            if (showTypeChip) {
              const chipSize = Math.max(10, Math.floor(size * 0.78));
              ctx.font = `600 ${chipSize}px ${font}`;
              const tw = ctx.measureText(typeText).width;
              const cw = tw + 10;
              const ch = chipSize + 6;
              const cy = y - (data.size || 4) - 10 - ch;
              const cx = x - cw / 2;

              rr(cx, cy, cw, ch, 7);
              ctx.fillStyle = isDomain
                ? "rgba(37,99,235,0.10)"
                : isCluster
                  ? "rgba(16,185,129,0.10)"
                  : "rgba(148,163,184,0.14)";
              ctx.fill();
              ctx.strokeStyle = "rgba(15,23,42,0.10)";
              ctx.lineWidth = 1;
              ctx.stroke();

              ctx.fillStyle = "rgba(15,23,42,0.70)";
              ctx.fillText(typeText, x, cy + ch / 2 + 0.5);
            }

            ctx.restore();
          });
        }
      } catch {}

      renderer.on("clickNode", (evt?: SigmaNodeEvent) => {
        const id = evt?.node;
        if (typeof id === "string") {
          if (!dragRef.current.moved) {
            setSelectedId(id);
            // 触发节点点击回调
            if (onNodeClick) {
              const node = graph.nodes.find(n => n.id === id);
              if (node) {
                onNodeClick(node);
              }
            }
          }
        }
      });
      renderer.on("enterNode", (evt?: SigmaNodeEvent) => {
        const id = evt?.node;
        if (typeof id === "string") setHoveredId(id);
      });
      renderer.on("leaveNode", () => setHoveredId(""));
      renderer.on("clickStage", () => setSelectedId(""));

      // Discriminate drag vs click (prevents accidental selection while panning)
      try {
        const mc = renderer.getMouseCaptor?.();
        if (mc?.on) {
          mc.on("mousedown", (e: MouseCaptorEvent) => {
            dragRef.current.down = true;
            dragRef.current.moved = false;
            dragRef.current.x = e?.x ?? 0;
            dragRef.current.y = e?.y ?? 0;
          });
          mc.on("mousemove", (e: MouseCaptorEvent) => {
            if (!dragRef.current.down) return;
            const dx = (e?.x ?? 0) - dragRef.current.x;
            const dy = (e?.y ?? 0) - dragRef.current.y;
            if (dx * dx + dy * dy > 9) dragRef.current.moved = true;
          });
          mc.on("mouseup", () => {
            dragRef.current.down = false;
            // keep moved state until next mousedown
          });
        }
      } catch {}
    })();

    return () => {
      disposed = true;
      try {
        ro?.disconnect?.();
      } catch {}
      ro = null;
      try {
        fa2WorkerRef.current?.stop?.();
      } catch {}
      try {
        fa2WorkerRef.current?.kill?.();
      } catch {}
      fa2WorkerRef.current = null;
      try {
        sigmaRef.current?.kill?.();
      } catch {}
      sigmaRef.current = null;
      graphRef.current = null;
    };
  }, [graph.edges, graph.nodes, setHoveredId, setSelectedId, onNodeClick]);

  // Pause layout while a node is selected to avoid "node flying away" effect
  useEffect(() => {
    // layout is killed after warm-up; keep this effect as a no-op for stability
    return;
  }, [selectedId]);

  // center camera when selection changes
  useEffect(() => {
    // Disable auto camera movement to avoid coordinate/offset issues.
    return;
  }, [selectedId]);

  return <div ref={containerRef} className="h-full w-full rounded-[18px]" />;
}

export default function GraphViewSigma({
  graph,
  isKg,
  onExpandSeed,
  onNodeClick,
}: {
  graph: GraphResponse;
  isKg?: boolean;
  onExpandSeed?: (entityId: string) => void;
  onNodeClick?: (node: GraphNode) => void;
}) {
  const router = useRouter();
  const [selectedId, setSelectedId] = useState<string>("");
  const [hoveredId, setHoveredId] = useState<string>("");
  const [showAllEdges, setShowAllEdges] = useState<boolean>(false);
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [showTypeChips, setShowTypeChips] = useState<boolean>(true);
  const [focusRedEdges, setFocusRedEdges] = useState<boolean>(true);
  const [similarEdgeColorMode, setSimilarEdgeColorMode] = useState<"fixed" | "gradient">("fixed");
  const [allEdgesColorMode, setAllEdgesColorMode] = useState<"default" | "confidence_gradient">("default");

  useEffect(() => {
    setSelectedId("");
    setHoveredId("");
  }, [isKg, graph]);

  const [caseDetails, setCaseDetails] = useState<null | {
    decision_node?: string | null;
    lesson_core?: string | null;
  }>(null);
  const [caseDetailsLoading, setCaseDetailsLoading] = useState<boolean>(false);

  const [kgDetails, setKgDetails] = useState<KgNodeDetails | null>(null);
  const nodesById = useMemo(() => new Map(graph.nodes.map((n) => [n.id, n] as const)), [graph.nodes]);
  const selectedNode = useMemo(() => nodesById.get(selectedId), [nodesById, selectedId]);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (isKg || !selectedNode || selectedNode.type !== "case") {
        setCaseDetails(null);
        return;
      }
      const cid = (selectedNode.case_id || "").trim();
      if (!cid) {
        setCaseDetails(null);
        return;
      }
      setCaseDetailsLoading(true);
      try {
        const c = await api.case(cid);
        if (!alive) return;
        setCaseDetails({
          decision_node: c.decision_node,
          lesson_core: c.lesson_core,
        });
      } catch {
        if (!alive) return;
        setCaseDetails(null);
      } finally {
        if (!alive) return;
        setCaseDetailsLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [isKg, selectedNode]);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!isKg || !selectedId) {
        setKgDetails(null);
        return;
      }
      try {
        const d = await api.kgNode(selectedId);
        if (!alive) return;
        setKgDetails(d);
      } catch {
        if (!alive) return;
        setKgDetails(null);
      }
    })();
    return () => {
      alive = false;
    };
  }, [isKg, selectedId]);

  const connected = useMemo(() => {
    if (!selectedId) return { edges: [] as GraphEdge[], nodes: [] as GraphNode[] };
    const edges = graph.edges.filter((e) => e.source === selectedId || e.target === selectedId);
    const nodeIds = new Set<string>();
    for (const e of edges) {
      if (e.source !== selectedId) nodeIds.add(e.source);
      if (e.target !== selectedId) nodeIds.add(e.target);
    }
    const nodes = Array.from(nodeIds)
      .map((id) => nodesById.get(id))
      .filter((v): v is GraphNode => !!v);
    return { edges, nodes };
  }, [graph.edges, nodesById, selectedId]);

  const attributeEntries = useMemo(() => {
    const attrs = isKg ? kgDetails?.attributes : selectedNode?.attributes;
    if (!attrs || typeof attrs !== "object") return [] as Array<[string, unknown]>;
    return Object.entries(attrs as Record<string, unknown>)
      .filter(([k]) => k !== "id" && k !== "type" && k !== "label")
      .slice(0, 80);
  }, [isKg, kgDetails, selectedNode]);

  const evidenceItems = useMemo(() => {
    const edges = connected.edges as GraphEdgeWithEvidence[];
    const out: Array<{
      edgeId: string;
      relationType: string;
      confidence?: number;
      case_id: string;
      quote: string;
    }> = [];
    for (const e of edges) {
      const ev = e?.evidence;
      if (!Array.isArray(ev)) continue;
      for (const item of ev) {
        if (!item?.quote) continue;
        out.push({
          edgeId: String(e.id || ""),
          relationType: String(e.edge_type || e.type || "related_to"),
          confidence:
            typeof e.strength === "number"
              ? e.strength
              : typeof e.confidence === "number"
                ? e.confidence
                : undefined,
          case_id: String(item.case_id || ""),
          quote: String(item.quote || ""),
        });
      }
    }
    return out.slice(0, 50);
  }, [connected.edges]);

  return (
    <div className="relative h-full min-h-[650px] overflow-hidden bg-[var(--bg-secondary)]">
      <div
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          background:
            "radial-gradient(1200px 560px at 20% -5%, rgba(99,102,241,0.08), transparent 60%), radial-gradient(900px 500px at 95% 105%, rgba(20,184,166,0.06), transparent 55%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 z-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(15, 23, 42, 0.055) 1px, transparent 0)",
          backgroundSize: "20px 20px",
          backgroundPosition: "0 0",
        }}
      />

      <div className="absolute inset-0 z-10">
        <GraphCanvas
          graph={graph}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
          hoveredId={hoveredId}
          setHoveredId={setHoveredId}
          showAllEdges={showAllEdges}
          showLabels={showLabels}
          showTypeChips={showTypeChips}
          focusRedEdges={focusRedEdges}
          similarEdgeColorMode={similarEdgeColorMode}
          allEdgesColorMode={allEdgesColorMode}
          onNodeClick={onNodeClick}
        />
      </div>

      <div className="absolute bottom-3 left-3 z-20 flex max-w-[calc(100vw-32px)] flex-wrap items-center gap-2 rounded-lg border border-[color:var(--border-subtle)] bg-white/85 px-2.5 py-1.5 text-[10px] text-[var(--text-muted)] shadow-sm backdrop-blur-sm">
        <span>拖拽平移，滚轮缩放</span>
        <span className="mx-1 text-[rgba(0,0,0,0.18)]">|</span>
        <button
          type="button"
          onClick={() => setShowAllEdges((v) => !v)}
          className={showAllEdges ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="大图建议关闭，避免渲染卡顿"
        >
          {showAllEdges ? "全部边: 开" : "全部边: 关"}
        </button>

        <span className="mx-1 text-[rgba(0,0,0,0.18)]">|</span>

        <button
          type="button"
          onClick={() => setShowLabels((v) => !v)}
          className={showLabels ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="显示/隐藏节点名称"
        >
          {showLabels ? "标签: 开" : "标签: 关"}
        </button>

        <button
          type="button"
          onClick={() => setShowTypeChips((v) => !v)}
          className={showTypeChips ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="显示/隐藏节点类型小标签"
        >
          {showTypeChips ? "类型: 开" : "类型: 关"}
        </button>

        <button
          type="button"
          onClick={() => setFocusRedEdges((v) => !v)}
          className={focusRedEdges ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="focus 时是否使用红色高亮边"
        >
          {focusRedEdges ? "聚焦高亮: 开" : "聚焦高亮: 关"}
        </button>

        <button
          type="button"
          onClick={() => setSimilarEdgeColorMode((v) => (v === "fixed" ? "gradient" : "fixed"))}
          className={similarEdgeColorMode === "gradient" ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="相似边配色：固定橙色 / 按相关度渐变"
        >
          {similarEdgeColorMode === "gradient" ? "相似边: 渐变" : "相似边: 固定色"}
        </button>

        <button
          type="button"
          onClick={() => setAllEdgesColorMode((v) => (v === "default" ? "confidence_gradient" : "default"))}
          className={allEdgesColorMode === "confidence_gradient" ? "text-[var(--accent-primary)]" : "hover:text-[var(--text-primary)]"}
          title="全边配色：默认灰 / 按相关度渐变（较克制）"
        >
          {allEdgesColorMode === "confidence_gradient" ? "全边: 置信渐变" : "全边: 默认"}
        </button>
      </div>

      {/* Node Details 抽屉浮层 */}
      {selectedNode && (
        <div className="absolute right-3 top-16 z-30 w-[390px] overflow-hidden rounded-2xl border border-[color:var(--border-subtle)] bg-white/96 shadow-xl backdrop-blur">
          <div className="flex items-center justify-between border-b border-[color:var(--border-subtle)] bg-[rgba(248,250,252,0.9)] px-3 py-2.5">
            <div className="text-xs font-medium text-[var(--text-primary)]">节点详情</div>
            <button
              type="button"
              onClick={() => setSelectedId("")}
              className="rounded border border-[color:var(--border-subtle)] bg-white px-2 py-0.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              关闭
            </button>
          </div>

          <div className="max-h-[calc(100vh-260px)] overflow-y-auto p-3">
            <div className="rounded-xl border border-[color:var(--border-subtle)] bg-[#f8fafc] p-3">
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-[var(--text-primary)]">{selectedNode.label}</div>
                    <div className="mt-0.5 font-mono text-[10px] text-[var(--text-muted)] break-all">{selectedNode.id}</div>
                  </div>
                  <span
                    className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                    style={{
                      background:
                        selectedNode.type === "domain"
                          ? "rgba(59, 130, 246, 0.10)"
                          : selectedNode.type === "cluster"
                            ? "rgba(16, 185, 129, 0.10)"
                            : "rgba(107, 114, 128, 0.10)",
                      color:
                        selectedNode.type === "domain" ? "rgb(37, 99, 235)" : selectedNode.type === "cluster" ? "rgb(5, 150, 105)" : "rgb(75, 85, 99)",
                    }}
                  >
                    {selectedNode.type}
                  </span>
                </div>

                {isKg && onExpandSeed && (
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      onClick={() => onExpandSeed(selectedNode.id)}
                      className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-2 py-1 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    >
                      展开邻域
                    </button>
                    <button
                      type="button"
                      onClick={() => navigator.clipboard?.writeText(selectedNode.id)}
                      className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-2 py-1 text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                    >
                      复制ID
                    </button>
                  </div>
                )}

                {selectedNode.domain && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-0.5">领域</div>
                    <div className="text-xs text-[var(--text-secondary)]">{selectedNode.domain}</div>
                  </div>
                )}

                {selectedNode.decision_node && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-0.5">决策节点</div>
                    <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{selectedNode.decision_node}</div>
                  </div>
                )}

                {selectedNode.lesson_core && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-0.5">经验教训</div>
                    <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{selectedNode.lesson_core}</div>
                  </div>
                )}

                {!isKg && selectedNode.type === "case" && caseDetailsLoading && (
                  <div className="mt-2 text-[10px] text-[var(--text-muted)]">Loading details...</div>
                )}

                {!isKg && selectedNode.type === "case" && caseDetails?.decision_node && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-0.5">决策节点</div>
                    <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{caseDetails.decision_node}</div>
                  </div>
                )}

                {!isKg && selectedNode.type === "case" && caseDetails?.lesson_core && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-0.5">经验教训</div>
                    <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{caseDetails.lesson_core}</div>
                  </div>
                )}

                {attributeEntries.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-[color:var(--border-subtle)]">
                    <div className="text-[10px] text-[var(--text-muted)] mb-1">扩展属性</div>
                    <div className="space-y-1">
                      {attributeEntries.map(([k, v]) => (
                        <div key={k} className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-2 py-1">
                          <div className="text-[10px] text-[var(--text-muted)]">{k}</div>
                          <div className="mt-0.5 text-xs text-[var(--text-secondary)] break-words">
                            {typeof v === "string" ? v : JSON.stringify(v)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-2 text-center">
                  <div className="text-lg font-semibold text-[var(--accent-primary)]">{connected.edges.length}</div>
                  <div className="text-[10px] text-[var(--text-muted)]">关联边</div>
                </div>
                <div className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-2 text-center">
                  <div className="text-lg font-semibold text-[var(--accent-primary)]">{connected.nodes.length}</div>
                  <div className="text-[10px] text-[var(--text-muted)]">相邻节点</div>
                </div>
              </div>

              <div>
                <div className="mb-1 text-[10px] font-medium text-[var(--text-primary)]">相邻节点列表</div>
                <div className="space-y-1">
                  {connected.nodes.slice(0, 50).map((n) => (
                    <button
                      key={n.id}
                      onClick={() => setSelectedId(n.id)}
                      className="flex w-full items-center justify-between gap-2 rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-2 py-1.5 text-left hover:opacity-90"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-xs text-[var(--text-primary)]">{n.label}</div>
                        <div className="text-[9px] text-[var(--text-muted)] font-mono">{n.id}</div>
                      </div>
                      <span className="text-[10px] text-[var(--text-muted)]">{n.type}</span>
                    </button>
                  ))}
                  {connected.nodes.length === 0 && <div className="text-center py-6 text-xs text-[var(--text-muted)]">暂无相邻节点</div>}
                </div>
              </div>

              {evidenceItems.length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] font-medium text-[var(--text-primary)]">证据摘录</div>
                  <div className="space-y-2">
                    {evidenceItems.map((ev, idx) => (
                      <div
                        key={`${ev.edgeId}_${idx}`}
                        className="rounded border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-[10px] font-medium text-[var(--text-primary)] truncate">
                            {ev.relationType}
                          </div>
                          <div className="text-[10px] text-[var(--text-muted)]">
                            {typeof ev.confidence === "number" ? `conf: ${Math.round(ev.confidence * 100)}%` : ""}
                          </div>
                        </div>
                        <div className="mt-1 text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{ev.quote}</div>
                        <button
                          type="button"
                          onClick={async () => {
                            const cid = ev.case_id;
                            if (!cid) return;
                            try {
                              await api.case(cid);
                              router.push(`/cases/${encodeURIComponent(cid)}`);
                            } catch {
                              try {
                                await navigator.clipboard?.writeText(cid);
                              } catch {}
                              router.push(`/cases?q=${encodeURIComponent(cid)}`);
                            }
                          }}
                          className="mt-1 text-left text-[10px] text-[var(--accent-primary)] hover:opacity-90 font-mono"
                        >
                          case: {ev.case_id}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </div>
        </div>
      )}
    </div>
  );
}
