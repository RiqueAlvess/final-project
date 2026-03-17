"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  Users,
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  Activity,
  Filter,
  X,
} from "lucide-react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import campaignsApi, {
  DashboardData,
  DashboardFilters,
  DashboardFilterParams,
} from "@/services/campaigns";

// ── Risk level colours ────────────────────────────────────────────────────────
const RISK_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  ACEITAVEL: { label: "Aceitável", color: "#22c55e", bg: "bg-green-100 text-green-700" },
  MODERADO: { label: "Moderado", color: "#f59e0b", bg: "bg-amber-100 text-amber-700" },
  IMPORTANTE: { label: "Importante", color: "#f97316", bg: "bg-orange-100 text-orange-700" },
  CRITICO: { label: "Crítico", color: "#ef4444", bg: "bg-red-100 text-red-700" },
};

const GENDER_LABELS: Record<string, string> = {
  M: "Masculino",
  F: "Feminino",
  O: "Outro",
  P: "Prefiro não dizer",
};

const AGE_LABELS: Record<string, string> = {
  UP_TO_25: "≤25",
  "26_35": "26-35",
  "36_45": "36-45",
  "46_55": "46-55",
  ABOVE_55: ">55",
  PREF: "N/D",
};

const CHART_COLORS = ["#8b5cf6", "#3b82f6", "#ec4899", "#f59e0b", "#22c55e", "#f97316"];

// ── Metric card ───────────────────────────────────────────────────────────────
function MetricCard({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-slate-500 font-medium">{label}</p>
            <p className={`text-3xl font-bold mt-1 ${accent ?? "text-slate-900"}`}>
              {value}
            </p>
            {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
          </div>
          <div className="p-2 bg-slate-100 rounded-lg">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Filter panel ──────────────────────────────────────────────────────────────
function FilterPanel({
  filters,
  selectedUnidades,
  selectedSetores,
  onUnidadeToggle,
  onSetorToggle,
  onClear,
}: {
  filters: DashboardFilters;
  selectedUnidades: number[];
  selectedSetores: number[];
  onUnidadeToggle: (id: number) => void;
  onSetorToggle: (id: number) => void;
  onClear: () => void;
}) {
  // Setores available given the selected unidades (cascading)
  const visibleSetores =
    selectedUnidades.length > 0
      ? filters.setores.filter((s) => selectedUnidades.includes(s.unidade_id))
      : filters.setores;

  const hasFilters = selectedUnidades.length > 0 || selectedSetores.length > 0;

  return (
    <Card className="mb-4">
      <CardHeader className="pb-2 pt-4 px-5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            Filtros
            {hasFilters && (
              <Badge variant="secondary" className="text-xs ml-1">
                {selectedUnidades.length + selectedSetores.length} ativos
              </Badge>
            )}
          </CardTitle>
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={onClear} className="h-7 text-xs text-slate-500">
              <X className="w-3 h-3 mr-1" />
              Limpar
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-5 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Unidades */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2">Unidades</p>
            {filters.unidades.length === 0 ? (
              <p className="text-xs text-slate-400">Nenhuma unidade disponível</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {filters.unidades.map((u) => {
                  const active = selectedUnidades.includes(u.id);
                  return (
                    <button
                      key={u.id}
                      onClick={() => onUnidadeToggle(u.id)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                        active
                          ? "bg-violet-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {u.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Setores */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2">
              Setores
              {selectedUnidades.length > 0 && (
                <span className="text-slate-400 font-normal ml-1">(filtrado por unidade)</span>
              )}
            </p>
            {visibleSetores.length === 0 ? (
              <p className="text-xs text-slate-400">Nenhum setor disponível</p>
            ) : (
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                {visibleSetores.map((s) => {
                  const active = selectedSetores.includes(s.id);
                  return (
                    <button
                      key={s.id}
                      onClick={() => onSetorToggle(s.id)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                        active
                          ? "bg-blue-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {s.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────
export default function CampaignDashboard() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const campaignId = Number(params.id);

  const [data, setData] = useState<DashboardData | null>(null);
  const [availableFilters, setAvailableFilters] = useState<DashboardFilters | null>(null);
  const [selectedUnidades, setSelectedUnidades] = useState<number[]>([]);
  const [selectedSetores, setSelectedSetores] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtersLoading, setFiltersLoading] = useState(true);

  // Load available filter options once on mount
  useEffect(() => {
    campaignsApi
      .getDashboardFilters(campaignId)
      .then((res) => setAvailableFilters(res.data))
      .catch(() => {
        // Non-fatal – filters panel just won't render
      })
      .finally(() => setFiltersLoading(false));
  }, [campaignId]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const filterParams: DashboardFilterParams = {};
      if (selectedUnidades.length) filterParams.unidade_ids = selectedUnidades;
      if (selectedSetores.length) filterParams.setor_ids = selectedSetores;
      const res = await campaignsApi.getDashboard(campaignId, filterParams);
      setData(res.data);
    } catch {
      toast({ title: "Erro ao carregar dashboard", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [campaignId, toast, selectedUnidades, selectedSetores]);

  // Reload dashboard whenever filters change
  useEffect(() => {
    load();
  }, [load]);

  // ── Filter handlers ─────────────────────────────────────────────────────────
  const toggleUnidade = (id: number) => {
    setSelectedUnidades((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    // If toggling off a unidade, also remove its setores from selection
    if (selectedUnidades.includes(id) && availableFilters) {
      const setoresForUnidade = availableFilters.setores
        .filter((s) => s.unidade_id === id)
        .map((s) => s.id);
      setSelectedSetores((prev) => prev.filter((s) => !setoresForUnidade.includes(s)));
    }
  };

  const toggleSetor = (id: number) => {
    setSelectedSetores((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const clearFilters = () => {
    setSelectedUnidades([]);
    setSelectedSetores([]);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-8 w-8 bg-slate-200 rounded animate-pulse" />
          <div className="h-6 w-48 bg-slate-200 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-28 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-72 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { summary, campaign } = data;

  // ── Prepare radar data ──────────────────────────────────────────────────────
  const radarData = summary.dimension_scores.map((d) => ({
    dimension: d.dimension__name,
    score: Number(d.avg_score?.toFixed(2) ?? 0),
    risco: Number(d.avg_risk?.toFixed(2) ?? 0),
  }));

  // ── Risk donut ──────────────────────────────────────────────────────────────
  const donutData = Object.entries(summary.risk_distribution).map(([key, val]) => ({
    name: RISK_CONFIG[key]?.label ?? key,
    value: val,
    color: RISK_CONFIG[key]?.color ?? "#94a3b8",
  }));

  // ── Gender scores line ──────────────────────────────────────────────────────
  const genderDims = Array.from(
    new Set(data.gender_scores.map((g) => g.dimension__name))
  );
  const genderByDim: Record<string, Record<string, number>> = {};
  data.gender_scores.forEach((g) => {
    if (!genderByDim[g.dimension__name]) genderByDim[g.dimension__name] = {};
    genderByDim[g.dimension__name][g.gender] = Number(g.avg_score?.toFixed(2) ?? 0);
  });
  const genderLineData = genderDims.map((dim) => ({
    dim: dim.length > 12 ? dim.slice(0, 12) + "…" : dim,
    ...genderByDim[dim],
  }));
  const genderKeys = Array.from(
    new Set(data.gender_scores.map((g) => g.gender))
  );

  // ── Age range scores line ───────────────────────────────────────────────────
  const ageDims = Array.from(
    new Set(data.age_range_scores.map((a) => a.dimension__name))
  );
  const ageByDim: Record<string, Record<string, number>> = {};
  data.age_range_scores.forEach((a) => {
    if (!ageByDim[a.dimension__name]) ageByDim[a.dimension__name] = {};
    ageByDim[a.dimension__name][a.age_range] = Number(a.avg_score?.toFixed(2) ?? 0);
  });
  const ageLineData = ageDims.map((dim) => ({
    dim: dim.length > 12 ? dim.slice(0, 12) + "…" : dim,
    ...ageByDim[dim],
  }));
  const ageKeys = Array.from(
    new Set(data.age_range_scores.map((a) => a.age_range))
  );

  // ── Gender distribution (pie) ───────────────────────────────────────────────
  const genderPie = data.demographic_groups.by_gender.map((g, i) => ({
    name: GENDER_LABELS[g.gender] ?? g.gender,
    value: Number(g.avg_risk?.toFixed(2) ?? 0),
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/dashboard/campaigns")}
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Campanhas
          </Button>
          <div className="h-4 w-px bg-slate-300" />
          <div>
            <h1 className="text-xl font-bold text-slate-900">{campaign.name}</h1>
            <p className="text-xs text-slate-500">Dashboard Analítico</p>
          </div>
          <Badge
            variant="outline"
            className={
              campaign.status === "ACTIVE"
                ? "bg-green-100 text-green-700"
                : "bg-slate-100 text-slate-600"
            }
          >
            {campaign.status === "ACTIVE"
              ? "Ativa"
              : campaign.status === "CLOSED"
              ? "Encerrada"
              : "Rascunho"}
          </Badge>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="w-4 h-4 mr-1" />
          Atualizar
        </Button>
      </div>

      {/* Filter panel */}
      {!filtersLoading && availableFilters && (
        <FilterPanel
          filters={availableFilters}
          selectedUnidades={selectedUnidades}
          selectedSetores={selectedSetores}
          onUnidadeToggle={toggleUnidade}
          onSetorToggle={toggleSetor}
          onClear={clearFilters}
        />
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <MetricCard
          icon={<Users className="w-5 h-5 text-slate-500" />}
          label="Total Convidados"
          value={summary.total_invites}
        />
        <MetricCard
          icon={<CheckCircle2 className="w-5 h-5 text-green-500" />}
          label="Respondidos"
          value={summary.total_answered}
          accent="text-green-600"
        />
        <MetricCard
          icon={<TrendingUp className="w-5 h-5 text-blue-500" />}
          label="Taxa de Adesão"
          value={`${summary.adhesion_rate}%`}
          accent="text-blue-600"
        />
        <MetricCard
          icon={<Activity className="w-5 h-5 text-purple-500" />}
          label="IGRP"
          value={summary.igrp.toFixed(2)}
          sub="Índice Geral de Risco"
          accent="text-purple-600"
        />
        <MetricCard
          icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
          label="Risco Alto"
          value={`${summary.high_risk_pct}%`}
          sub="Importante + Crítico"
          accent="text-red-600"
        />
      </div>

      {/* Charts row 1: Radar + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Scores por Dimensão
            </CardTitle>
          </CardHeader>
          <CardContent>
            {radarData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
                Sem dados disponíveis
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 4]} tick={{ fontSize: 10 }} />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.3}
                  />
                  <Radar
                    name="Risco"
                    dataKey="risco"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.15}
                  />
                  <Legend />
                  <Tooltip formatter={(v: number) => v.toFixed(2)} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Donut – risk distribution */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Distribuição de Riscos
            </CardTitle>
          </CardHeader>
          <CardContent>
            {donutData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
                Sem dados disponíveis
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={donutData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {donutData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts row 2: Gender scores line + Age range scores line */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Gender line */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Scores por Gênero
            </CardTitle>
          </CardHeader>
          <CardContent>
            {genderLineData.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-slate-400 text-sm">
                Sem dados demográficos
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={genderLineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="dim" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 4]} tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend />
                  {genderKeys.map((g, i) => (
                    <Line
                      key={g}
                      type="monotone"
                      dataKey={g}
                      name={GENDER_LABELS[g] ?? g}
                      stroke={CHART_COLORS[i % CHART_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Age range line */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Scores por Faixa Etária
            </CardTitle>
          </CardHeader>
          <CardContent>
            {ageLineData.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-slate-400 text-sm">
                Sem dados demográficos
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={ageLineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="dim" tick={{ fontSize: 10 }} />
                  <YAxis domain={[0, 4]} tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend />
                  {ageKeys.map((a, i) => (
                    <Line
                      key={a}
                      type="monotone"
                      dataKey={a}
                      name={AGE_LABELS[a] ?? a}
                      stroke={CHART_COLORS[i % CHART_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts row 3: Gender pie + Critical sectors bar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Gender pie */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Risco Médio por Gênero
            </CardTitle>
          </CardHeader>
          <CardContent>
            {genderPie.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-slate-400 text-sm">
                Sem dados demográficos
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={genderPie}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value: v }) => `${name}: ${v}`}
                  >
                    {genderPie.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Critical sectors */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Setores Mais Críticos
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.critical_sectors.length === 0 ? (
              <div className="h-56 flex items-center justify-center text-slate-400 text-sm">
                Nenhum setor crítico
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={data.critical_sectors.map((s) => ({
                    setor: `Setor ${s.setor_id}`,
                    risco: Number(Number(s.avg_risk).toFixed(2)),
                    ocorrencias: s.high_risk_count,
                  }))}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 4]} tick={{ fontSize: 10 }} />
                  <YAxis
                    type="category"
                    dataKey="setor"
                    tick={{ fontSize: 10 }}
                    width={60}
                  />
                  <Tooltip />
                  <Bar dataKey="risco" name="Risco Médio" fill="#f97316" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Heatmap setor × dimensão */}
      {data.sector_heatmap.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Heatmap – Setor × Dimensão (Risco Médio)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              {(() => {
                const sectors = Array.from(
                  new Set(data.sector_heatmap.map((h) => h.setor_id))
                );
                const dims = Array.from(
                  new Set(data.sector_heatmap.map((h) => h.dimension__name))
                );
                const map: Record<string, Record<string, number>> = {};
                data.sector_heatmap.forEach((h) => {
                  const k = String(h.setor_id);
                  if (!map[k]) map[k] = {};
                  map[k][h.dimension__name] = Number(Number(h.avg_risk).toFixed(2));
                });

                const getRiskColor = (v: number) => {
                  if (v < 1) return "bg-green-200 text-green-800";
                  if (v < 2.5) return "bg-amber-200 text-amber-800";
                  if (v < 3.5) return "bg-orange-300 text-orange-900";
                  return "bg-red-400 text-white";
                };

                return (
                  <table className="text-xs w-full min-w-max">
                    <thead>
                      <tr>
                        <th className="px-3 py-2 text-left text-slate-500 font-medium">
                          Setor
                        </th>
                        {dims.map((d) => (
                          <th
                            key={d}
                            className="px-3 py-2 text-center text-slate-500 font-medium"
                          >
                            {d.length > 10 ? d.slice(0, 10) + "…" : d}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sectors.map((s) => (
                        <tr key={s}>
                          <td className="px-3 py-2 font-medium text-slate-700">
                            Setor {s}
                          </td>
                          {dims.map((d) => {
                            const v = map[String(s)]?.[d];
                            return (
                              <td key={d} className="px-3 py-2 text-center">
                                {v !== undefined ? (
                                  <span
                                    className={`inline-block px-2 py-0.5 rounded font-semibold ${getRiskColor(v)}`}
                                  >
                                    {v}
                                  </span>
                                ) : (
                                  <span className="text-slate-300">—</span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                );
              })()}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top demographic groups */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Grupos Críticos – Gênero
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.demographic_groups.by_gender.length === 0 ? (
              <p className="text-slate-400 text-sm text-center py-6">Sem dados</p>
            ) : (
              <div className="space-y-2">
                {data.demographic_groups.by_gender.map((g) => (
                  <div
                    key={g.gender}
                    className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                  >
                    <span className="text-sm text-slate-700">
                      {GENDER_LABELS[g.gender] ?? g.gender}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-100 rounded-full">
                        <div
                          className="h-full bg-purple-500 rounded-full"
                          style={{ width: `${(Number(g.avg_risk) / 4) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-700 w-8 text-right">
                        {Number(g.avg_risk).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Grupos Críticos – Faixa Etária
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.demographic_groups.by_age_range.length === 0 ? (
              <p className="text-slate-400 text-sm text-center py-6">Sem dados</p>
            ) : (
              <div className="space-y-2">
                {data.demographic_groups.by_age_range.map((a) => (
                  <div
                    key={a.age_range}
                    className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
                  >
                    <span className="text-sm text-slate-700">
                      {AGE_LABELS[a.age_range] ?? a.age_range}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-100 rounded-full">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${(Number(a.avg_risk) / 4) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-700 w-8 text-right">
                        {Number(a.avg_risk).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
