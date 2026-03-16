"use client";

import type { MouseEvent } from "react";
import { useMemo, useState, useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";

import type { GraphEdge, GraphNode, GraphResponse } from "@/lib/api";
import { DOMAINS, getMainDomain } from "@/lib/domains";

type EdgeType = "domain_case" | "case_similar" | "same_domain" | "shared_tag";

interface EnhancedGraphEdge extends GraphEdge {
  edgeType?: EdgeType;
  similarity?: number;
}

interface GraphFilters {
  showDomainCase: boolean;
  showCaseSimilar: boolean;
  minSimilarity: number;
  clusterByDomain: boolean;
}

// MIROFISH 风格配色 - 浅色主题
const THEME = {
  background: "#fafafa",
  nodeDomain: {
    bg: "#e3f2fd",
    border: "#2196f3",
    text: "#1565c0",
  },
  nodeCase: {
    bg: "#ffffff",
    border: "#e0e0e0",
    text: "#424242",
  },
  edgeDomain: "#90caf9",
  edgeSimilar: "#ff7043",
  textMuted: "#757575",
  textPrimary: "#212121",
};

// 领域特定的颜色
const DOMAIN_COLORS: Record<string, string> = {
  "TECH": "#2196f3",
  "FIN": "#4caf50",
  "CAR": "#ff9800",
  "HEALTH": "#f44336",
  "EDU": "#9c27b0",
  "LEGAL": "#00bcd4",
  "BUSINESS": "#ff5722",
  "LIFE": "#e91e63",
};

function GraphViewInner({ graph }: { graph: GraphResponse }) {
  const [selectedId, setSelectedId] = useState<string>("");
  const [hoveredId, setHoveredId] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const { fitView, setCenter } = useReactFlow();
  
  // 图谱显示过滤器
  const [filters, setFilters] = useState<GraphFilters>({
    showDomainCase: true,
    showCaseSimilar: false, // 默认不显示相似边，提高性能
    minSimilarity: 0.5,
    clusterByDomain: true, // 默认使用聚类布局，更快
  });

  const canvas = useMemo(() => ({ w: 1000, h: 700 }), []);

  // 计算案例相似度并生成相似边 - 优化：限制计算量
  const enhancedEdges = useMemo((): EnhancedGraphEdge[] => {
    const edges: EnhancedGraphEdge[] = [];
    
    // 1. 原有的 domain -> case 边
    if (filters.showDomainCase) {
      for (const edge of graph.edges) {
        edges.push({ ...edge, edgeType: "domain_case" });
      }
    }
    
    // 2. case -> case 相似边（基于domain、title相似度）- 优化：只计算前100个case
    if (filters.showCaseSimilar) {
      const caseNodes = graph.nodes.filter(n => n.type === "case").slice(0, 100);
      for (let i = 0; i < caseNodes.length; i++) {
        for (let j = i + 1; j < caseNodes.length; j++) {
          const case1 = caseNodes[i];
          const case2 = caseNodes[j];
          
          let similarity = 0;
          
          // 相同domain增加相似度
          if (case1.domain === case2.domain) {
            similarity += 0.4;
          } else {
            const main1 = getMainDomain(case1.domain || "")?.code;
            const main2 = getMainDomain(case2.domain || "")?.code;
            if (main1 && main2 && main1 === main2) {
              similarity += 0.2;
            }
          }
          
          // title相似度
          const title1 = case1.label?.toLowerCase() || "";
          const title2 = case2.label?.toLowerCase() || "";
          const commonWords = title1.split(/\s+/).filter(w => 
            w.length > 1 && title2.includes(w)
          );
          similarity += commonWords.length * 0.1;
          similarity = Math.min(similarity, 1);
          
          if (similarity >= filters.minSimilarity) {
            edges.push({
              id: `similar:${case1.id}:${case2.id}`,
              source: case1.id,
              target: case2.id,
              edgeType: "case_similar",
              similarity,
            });
          }
        }
      }
    }
    
    return edges;
  }, [graph.nodes, graph.edges, filters.showDomainCase, filters.showCaseSimilar, filters.minSimilarity]);

  // 按domain聚类 - 计算节点位置 - 优化：使用更简单的布局算法
  const clusteredPositions = useMemo(() => {
    const positions = new Map<string, { x: number; y: number }>();
    const domainNodes = graph.nodes.filter(n => n.type === "domain");
    const caseNodes = graph.nodes.filter(n => n.type === "case");
    
    if (filters.clusterByDomain) {
      // 聚类布局：domain 分布在圆周上
      const centerX = canvas.w / 2;
      const centerY = canvas.h / 2;
      const domainRadius = Math.min(canvas.w, canvas.h) * 0.3;
      
      domainNodes.forEach((domain, index) => {
        const angle = (index / domainNodes.length) * 2 * Math.PI - Math.PI / 2;
        positions.set(domain.id, {
          x: centerX + domainRadius * Math.cos(angle),
          y: centerY + domainRadius * Math.sin(angle),
        });
      });
      
      // case 分布在对应 domain 周围
      const domainCaseMap = new Map<string, string[]>();
      for (const edge of graph.edges) {
        if (edge.source.startsWith("domain:")) {
          const cases = domainCaseMap.get(edge.source) || [];
          cases.push(edge.target);
          domainCaseMap.set(edge.source, cases);
        }
      }
      
      domainNodes.forEach((domain) => {
        const domainPos = positions.get(domain.id);
        if (!domainPos) return;
        
        const cases = domainCaseMap.get(domain.id) || [];
        const caseRadius = 100;
        
        cases.forEach((caseId, caseIndex) => {
          const angle = (caseIndex / Math.max(cases.length, 1)) * 2 * Math.PI - Math.PI / 2;
          positions.set(caseId, {
            x: domainPos.x + caseRadius * Math.cos(angle),
            y: domainPos.y + caseRadius * Math.sin(angle),
          });
        });
      });
    } else {
      // 简单布局：domain 在中心，case 围绕 - 使用确定性算法避免 Math.random
      domainNodes.forEach((domain, i) => {
        const angle = (i / Math.max(domainNodes.length, 1)) * 2 * Math.PI;
        positions.set(domain.id, {
          x: canvas.w / 2 + Math.cos(angle) * 150,
          y: canvas.h / 2 + Math.sin(angle) * 150,
        });
      });
      
      caseNodes.forEach((c, i) => {
        const angle = (i / Math.max(caseNodes.length, 1)) * 2 * Math.PI;
        positions.set(c.id, {
          x: canvas.w / 2 + Math.cos(angle) * 300,
          y: canvas.h / 2 + Math.sin(angle) * 300,
        });
      });
    }
    
    return positions;
  }, [graph.nodes, graph.edges, filters.clusterByDomain, canvas.w, canvas.h]);

  // 获取节点颜色
  const getNodeColor = useCallback((node: GraphNode) => {
    if (node.type === "domain") {
      const mainDomain = node.domain?.split("-")[0] || "";
      const color = DOMAIN_COLORS[mainDomain] || THEME.nodeDomain.border;
      return {
        bg: color + "20",
        border: color,
        text: color,
      };
    }
    return THEME.nodeCase;
  }, []);

  // 生成节点 - 使用预计算的位置
  const nodes = useMemo((): Node[] => {
    return graph.nodes.map((n) => {
      const isDomain = n.type === "domain";
      const domainInfo = isDomain ? DOMAINS.find(d => d.code === n.label) : null;
      const colors = getNodeColor(n);
      const pos = clusteredPositions.get(n.id) || { x: canvas.w / 2, y: canvas.h / 2 };
      
      return {
        id: n.id,
        type: "default",
        data: { 
          label: isDomain && domainInfo ? `${domainInfo.icon} ${n.label}` : n.label, 
          type: n.type,
          originalLabel: n.label,
          domain: n.domain,
        },
        position: pos,
        style: {
          borderRadius: isDomain ? 16 : 6,
          border: `1px solid ${colors.border}`,
          background: colors.bg,
          color: colors.text,
          padding: isDomain ? "8px 12px" : "6px 10px",
          minWidth: isDomain ? 120 : 140,
          maxWidth: 200,
          fontWeight: isDomain ? 600 : 400,
          fontSize: isDomain ? "12px" : "11px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        },
      } satisfies Node;
    });
  }, [graph.nodes, clusteredPositions, canvas.w, canvas.h, getNodeColor]);

  const edges = useMemo((): Edge[] => {
    const active = new Set<string>();
    const focus = selectedId || hoveredId;
    if (focus) {
      for (const e of enhancedEdges) {
        if (e.source === focus || e.target === focus) {
          active.add(e.id);
        }
      }
    }

    return enhancedEdges.map((e) => {
      const isActive = focus ? active.has(e.id) : true;
      const isSimilar = e.edgeType === "case_similar";
      
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        animated: isSimilar && isActive,
        style: {
          stroke: isSimilar ? THEME.edgeSimilar : THEME.edgeDomain,
          strokeWidth: isActive ? (isSimilar ? 2 : 1.5) : (isSimilar ? 1 : 1),
          opacity: isActive ? 0.8 : 0.3,
          strokeDasharray: isSimilar ? "3,3" : undefined,
        },
        label: isSimilar && e.similarity ? `${Math.round(e.similarity * 100)}%` : undefined,
        labelStyle: { fontSize: 9, fill: THEME.edgeSimilar },
        labelBgStyle: { fill: "#fff" },
        labelBgPadding: [2, 2],
        labelBgBorderRadius: 2,
      } satisfies Edge;
    });
  }, [enhancedEdges, hoveredId, selectedId]);

  // 节点点击处理
  const onNodeClick = useCallback(
    (_: MouseEvent, node: Node) => {
      setSelectedId(node.id);
      const nodePosition = nodes.find(n => n.id === node.id)?.position;
      if (nodePosition) {
        setCenter(nodePosition.x, nodePosition.y, { duration: 300, zoom: 1.2 });
      }
    },
    [nodes, setCenter]
  );

  const highlightedNodes = useMemo(() => {
    const focus = selectedId || hoveredId;
    if (!focus) return nodes;

    const neighbor = new Set<string>([focus]);
    for (const e of enhancedEdges) {
      if (e.source === focus) neighbor.add(e.target);
      if (e.target === focus) neighbor.add(e.source);
    }

    return nodes.map((n) => {
      const isOn = neighbor.has(n.id);
      const isSelected = n.id === selectedId;
      return {
        ...n,
        style: {
          ...(n.style || {}),
          opacity: isOn ? 1 : 0.25,
          filter: isOn ? "none" : "grayscale(80%)",
          boxShadow: isSelected ? `0 0 0 2px ${THEME.nodeDomain.border}` : "0 1px 3px rgba(0,0,0,0.1)",
        },
      } as Node;
    });
  }, [enhancedEdges, hoveredId, nodes, selectedId]);

  const selectedNode: GraphNode | undefined = useMemo(() => {
    return graph.nodes.find((n) => n.id === selectedId);
  }, [graph.nodes, selectedId]);

  const connectedEdges: EnhancedGraphEdge[] = useMemo(() => {
    if (!selectedId) return [];
    return enhancedEdges.filter((e) => e.source === selectedId || e.target === selectedId);
  }, [enhancedEdges, selectedId]);

  const connectedNodeIds = useMemo(() => {
    if (!selectedId) return [] as string[];
    const ids = new Set<string>();
    for (const e of connectedEdges) {
      if (e.source !== selectedId) ids.add(e.source);
      if (e.target !== selectedId) ids.add(e.target);
    }
    return Array.from(ids);
  }, [connectedEdges, selectedId]);

  const connectedNodes: GraphNode[] = useMemo(() => {
    const byId = new Map(graph.nodes.map((n) => [n.id, n] as const));
    return connectedNodeIds.map((id) => byId.get(id)).filter((v): v is GraphNode => !!v);
  }, [connectedNodeIds, graph.nodes]);

  // 统计信息
  const stats = useMemo(() => {
    const domainCaseCount = enhancedEdges.filter(e => e.edgeType === "domain_case").length;
    const similarCount = enhancedEdges.filter(e => e.edgeType === "case_similar").length;
    const domainCount = graph.nodes.filter(n => n.type === "domain").length;
    const caseCount = graph.nodes.filter(n => n.type === "case").length;
    return { domainCaseCount, similarCount, domainCount, caseCount };
  }, [enhancedEdges, graph.nodes]);

  // 过滤节点列表
  const filteredNodes = useMemo(() => {
    return graph.nodes.filter(n => {
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q);
    });
  }, [graph.nodes, search]);

  return (
    <div className="grid h-[calc(100vh-140px)] min-h-[600px] grid-cols-[1fr_320px] gap-3">
      {/* 主图谱区域 - MIROFISH 风格 */}
      <div className="relative overflow-hidden rounded-lg border border-gray-200 bg-white">
        {/* 顶部工具栏 */}
        <div className="absolute left-0 right-0 top-0 z-10 border-b border-gray-200 bg-white/95 px-3 py-2 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <div className="text-xs font-medium text-gray-700">知识图谱</div>
              
              {/* 过滤器控制 */}
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1 text-[10px] text-gray-600">
                  <input
                    type="checkbox"
                    checked={filters.showDomainCase}
                    onChange={(e) => setFilters(f => ({ ...f, showDomainCase: e.target.checked }))}
                    className="rounded"
                  />
                  <span>Domain关系</span>
                </label>
                <label className="flex items-center gap-1 text-[10px] text-gray-600">
                  <input
                    type="checkbox"
                    checked={filters.showCaseSimilar}
                    onChange={(e) => setFilters(f => ({ ...f, showCaseSimilar: e.target.checked }))}
                    className="rounded"
                  />
                  <span>相似关系</span>
                </label>
                <label className="flex items-center gap-1 text-[10px] text-gray-600">
                  <input
                    type="checkbox"
                    checked={filters.clusterByDomain}
                    onChange={(e) => setFilters(f => ({ ...f, clusterByDomain: e.target.checked }))}
                    className="rounded"
                  />
                  <span>聚类布局</span>
                </label>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* 相似度阈值 */}
              {filters.showCaseSimilar && (
                <div className="flex items-center gap-1">
                  <span className="text-[10px] text-gray-500">相似度:</span>
                  <input
                    type="range"
                    min="0.1"
                    max="0.9"
                    step="0.1"
                    value={filters.minSimilarity}
                    onChange={(e) => setFilters(f => ({ ...f, minSimilarity: parseFloat(e.target.value) }))}
                    className="w-16"
                  />
                  <span className="text-[10px] text-gray-500 w-6">{Math.round(filters.minSimilarity * 100)}%</span>
                </div>
              )}

              <button
                type="button"
                onClick={() => fitView({ padding: 0.1, duration: 300 })}
                className="h-6 rounded border border-gray-300 bg-white px-2 text-[10px] text-gray-600 hover:border-blue-400 hover:text-blue-600"
              >
                适应画布
              </button>
            </div>
          </div>
          
          {/* 图例 */}
          <div className="mt-1 flex items-center gap-3 text-[10px] text-gray-500">
            <div className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: THEME.nodeDomain.border }} />
              <span>Domain ({stats.domainCount})</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-gray-400" />
              <span>Case ({stats.caseCount})</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="inline-block h-0.5 w-4 bg-orange-400" />
              <span>相似边 ({stats.similarCount})</span>
            </div>
            <div className="ml-auto text-gray-400">总边数: {enhancedEdges.length}</div>
          </div>
        </div>

        {/* ReactFlow 图谱 */}
        <div className="h-full pt-16">
          <ReactFlow
            nodes={highlightedNodes}
            edges={edges}
            onNodeClick={onNodeClick}
            onNodeMouseEnter={(_, n) => setHoveredId(n.id)}
            onNodeMouseLeave={() => setHoveredId("")}
            fitView
            fitViewOptions={{ padding: 0.1 }}
            minZoom={0.1}
            maxZoom={2}
            defaultEdgeOptions={{ type: "bezier" }}
          >
            <Background color="#e0e0e0" gap={20} size={1} />
            <Controls className="!bg-white !border-gray-200" />
            <MiniMap 
              pannable 
              zoomable 
              position="bottom-right"
              className="!bg-white !border-gray-200"
              style={{ width: 120, height: 80, margin: 8 }}
              maskColor="rgba(0, 0, 0, 0.1)"
              nodeColor={(node) => {
                if (node.data?.type === 'domain') {
                  const mainDomain = node.data?.domain?.split("-")[0] || "";
                  return DOMAIN_COLORS[mainDomain] || THEME.nodeDomain.border;
                }
                return "#9e9e9e";
              }}
            />
          </ReactFlow>
        </div>
      </div>

      {/* 右侧详情面板 - MIROFISH 风格 */}
      <aside className="flex flex-col rounded-lg border border-gray-200 bg-white overflow-hidden">
        {/* 面板头部 */}
        <div className="border-b border-gray-200 px-3 py-2 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-xs font-medium text-gray-700">
              {selectedNode ? "节点详情" : "节点列表"}
            </div>
            {selectedNode && (
              <button
                type="button"
                onClick={() => setSelectedId("")}
                className="rounded border border-gray-300 bg-white px-2 py-0.5 text-[10px] text-gray-600 hover:text-gray-900"
              >
                返回
              </button>
            )}
          </div>
        </div>

        {/* 面板内容 */}
        <div className="flex-1 overflow-y-auto p-3">
          {!selectedNode ? (
            <div className="space-y-3">
              {/* 搜索框 */}
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="搜索节点..."
                  className="w-full rounded border border-gray-300 bg-white px-2 py-1.5 pl-7 text-xs text-gray-700 outline-none focus:border-blue-400"
                />
                <svg className="absolute left-2 top-2 h-3 w-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              
              {/* 节点列表 */}
              <div className="space-y-1">
                <div className="mb-1 text-[10px] text-gray-500">
                  共 {filteredNodes.length} 个节点
                </div>
                {filteredNodes.map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => {
                      setSelectedId(n.id);
                      const nodePos = nodes.find(node => node.id === n.id)?.position;
                      if (nodePos) {
                        setCenter(nodePos.x, nodePos.y, { duration: 300, zoom: 1.2 });
                      }
                    }}
                    className="flex w-full items-center gap-2 rounded border border-gray-200 bg-white px-2 py-1.5 text-left hover:bg-gray-50"
                  >
                    <span 
                      className="h-2 w-2 rounded-full flex-shrink-0"
                      style={{ 
                        background: n.type === "domain" 
                          ? (DOMAIN_COLORS[n.domain?.split("-")[0] || ""] || THEME.nodeDomain.border)
                          : "#9e9e9e"
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="truncate text-xs text-gray-700">{n.label}</div>
                      <div className="text-[9px] text-gray-400 font-mono">{n.id}</div>
                    </div>
                    {n.type === "domain" && (
                      <span className="text-[9px] px-1 py-0.5 rounded bg-blue-100 text-blue-600">
                        Domain
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* 节点基本信息 */}
              <div className="rounded border border-gray-200 bg-gray-50 p-3">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm font-semibold text-gray-800">{selectedNode.label}</div>
                    <div className="mt-0.5 font-mono text-[10px] text-gray-500">{selectedNode.id}</div>
                  </div>
                  <span 
                    className="px-1.5 py-0.5 rounded text-[10px] font-medium"
                    style={{ 
                      background: selectedNode.type === "domain" 
                        ? `${THEME.nodeDomain.border}20`
                        : "#f5f5f5",
                      color: selectedNode.type === "domain" 
                        ? THEME.nodeDomain.border
                        : "#616161"
                    }}
                  >
                    {selectedNode.type === "domain" ? "Domain" : "Case"}
                  </span>
                </div>
                
                {selectedNode.domain && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <div className="text-[10px] text-gray-500 mb-0.5">所属领域</div>
                    <div className="text-xs text-gray-700">{selectedNode.domain}</div>
                  </div>
                )}
              </div>

              {/* 关联边统计 */}
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded border border-gray-200 bg-white p-2 text-center">
                  <div className="text-lg font-semibold text-blue-600">{connectedEdges.length}</div>
                  <div className="text-[10px] text-gray-500">关联边</div>
                </div>
                <div className="rounded border border-gray-200 bg-white p-2 text-center">
                  <div className="text-lg font-semibold text-blue-600">{connectedNodes.length}</div>
                  <div className="text-[10px] text-gray-500">关联节点</div>
                </div>
              </div>

              {/* Domain归属关系 */}
              {connectedEdges.filter(e => e.edgeType === "domain_case").length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] font-medium text-gray-700">Domain 归属</div>
                  <div className="space-y-1">
                    {connectedEdges
                      .filter(e => e.edgeType === "domain_case")
                      .map(e => {
                        const relatedId = e.source === selectedId ? e.target : e.source;
                        const relatedNode = graph.nodes.find(n => n.id === relatedId);
                        return (
                          <div key={e.id} className="flex items-center gap-2 rounded border border-gray-200 bg-white px-2 py-1">
                            <span className="h-1.5 w-1.5 rounded-full" style={{ background: THEME.nodeDomain.border }} />
                            <span className="text-xs text-gray-700 flex-1 truncate">{relatedNode?.label || relatedId}</span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
              
              {/* 相似案例 */}
              {connectedEdges.filter(e => e.edgeType === "case_similar").length > 0 && (
                <div>
                  <div className="mb-1 text-[10px] font-medium text-gray-700">相似案例</div>
                  <div className="space-y-1">
                    {connectedEdges
                      .filter(e => e.edgeType === "case_similar")
                      .sort((a, b) => (b.similarity || 0) - (a.similarity || 0))
                      .map(e => {
                        const relatedId = e.source === selectedId ? e.target : e.source;
                        const relatedNode = graph.nodes.find(n => n.id === relatedId);
                        return (
                          <button
                            key={e.id}
                            onClick={() => setSelectedId(relatedId)}
                            className="flex w-full items-center gap-2 rounded border border-gray-200 bg-white px-2 py-1 hover:bg-gray-50"
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
                            <span className="text-xs text-gray-700 flex-1 truncate text-left">{relatedNode?.label || relatedId}</span>
                            <span className="text-[10px] font-medium text-orange-500">
                              {Math.round((e.similarity || 0) * 100)}%
                            </span>
                          </button>
                        );
                      })}
                  </div>
                </div>
              )}
              
              {connectedEdges.length === 0 && (
                <div className="text-center py-6 text-xs text-gray-400">
                  无关联边
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

// 包装组件，提供 ReactFlowProvider
export default function GraphView({ graph }: { graph: GraphResponse }) {
  return (
    <ReactFlowProvider>
      <GraphViewInner graph={graph} />
    </ReactFlowProvider>
  );
}
