"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  Play,
  Square,
  Trash2,
  BarChart3,
  Users,
  Send,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import campaignsApi, { Campaign } from "@/services/campaigns";

const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Rascunho",
  ACTIVE: "Ativa",
  CLOSED: "Encerrada",
};

const STATUS_COLORS: Record<string, string> = {
  DRAFT: "bg-slate-100 text-slate-700 border-slate-200",
  ACTIVE: "bg-green-100 text-green-700 border-green-200",
  CLOSED: "bg-red-100 text-red-700 border-red-200",
};

export default function CampaignsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });

  const load = useCallback(async () => {
    try {
      const res = await campaignsApi.list();
      setCampaigns(res.data.results);
    } catch {
      toast({ title: "Erro ao carregar campanhas", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await campaignsApi.create(form);
      setForm({ name: "", description: "" });
      setShowCreate(false);
      toast({ title: "Campanha criada com sucesso!" });
      load();
    } catch {
      toast({ title: "Erro ao criar campanha", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  };

  const handleActivate = async (id: number) => {
    try {
      await campaignsApi.activate(id);
      toast({ title: "Campanha ativada!" });
      load();
    } catch {
      toast({ title: "Erro ao ativar campanha", variant: "destructive" });
    }
  };

  const handleClose = async (id: number) => {
    if (!confirm("Encerrar esta campanha? Esta ação não pode ser desfeita.")) return;
    try {
      await campaignsApi.close(id);
      toast({ title: "Campanha encerrada." });
      load();
    } catch {
      toast({ title: "Erro ao encerrar campanha", variant: "destructive" });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Excluir esta campanha permanentemente?")) return;
    try {
      await campaignsApi.delete(id);
      toast({ title: "Campanha excluída." });
      load();
    } catch {
      toast({ title: "Erro ao excluir campanha", variant: "destructive" });
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Campanhas</h1>
          <p className="text-slate-500 text-sm mt-1">
            Gerencie ciclos de pesquisa organizacional
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
          <Button
            size="sm"
            className="bg-purple-600 hover:bg-purple-700"
            onClick={() => setShowCreate(!showCreate)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Campanha
          </Button>
        </div>
      </div>

      {/* Create form */}
      {showCreate && (
        <Card className="border-purple-200 bg-purple-50/30">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Nova Campanha</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">
                Nome *
              </label>
              <input
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Ex: Pesquisa HSE-IT Q1 2025"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">
                Descrição
              </label>
              <textarea
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                rows={2}
                placeholder="Descreva o objetivo desta campanha..."
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowCreate(false)}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                className="bg-purple-600 hover:bg-purple-700"
                onClick={handleCreate}
                disabled={creating || !form.name.trim()}
              >
                {creating ? "Criando..." : "Criar Campanha"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Campaign list */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="font-medium">Nenhuma campanha encontrada</p>
          <p className="text-sm mt-1">Crie sua primeira campanha para começar.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {campaigns.map((c) => (
            <Card key={c.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-snug">{c.name}</CardTitle>
                  <Badge
                    variant="outline"
                    className={`text-xs shrink-0 ${STATUS_COLORS[c.status]}`}
                  >
                    {STATUS_LABELS[c.status]}
                  </Badge>
                </div>
                {c.description && (
                  <CardDescription className="text-xs line-clamp-2">
                    {c.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Stats */}
                <div className="flex gap-4 text-sm text-slate-600">
                  <span className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    {c.total_invites} convidados
                  </span>
                  <span className="flex items-center gap-1">
                    <Send className="w-3.5 h-3.5 text-slate-400" />
                    {c.total_answered} respondidos
                  </span>
                </div>

                {/* Adhesion bar */}
                {c.total_invites > 0 && (
                  <div>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>Taxa de adesão</span>
                      <span>
                        {Math.round((c.total_answered / c.total_invites) * 100)}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full">
                      <div
                        className="h-full bg-purple-500 rounded-full"
                        style={{
                          width: `${Math.round(
                            (c.total_answered / c.total_invites) * 100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-400">
                  Criada em {new Date(c.created_at).toLocaleDateString("pt-BR")}
                </p>

                {/* Actions */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {c.status === "DRAFT" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs h-7 text-green-600 border-green-200 hover:bg-green-50"
                      onClick={() => handleActivate(c.id)}
                    >
                      <Play className="w-3 h-3 mr-1" />
                      Ativar
                    </Button>
                  )}
                  {c.status === "ACTIVE" && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        onClick={() =>
                          router.push(`/dashboard/campaigns/${c.id}/invites`)
                        }
                      >
                        <Send className="w-3 h-3 mr-1" />
                        Envios
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7"
                        onClick={() =>
                          router.push(`/dashboard/campaigns/${c.id}/dashboard`)
                        }
                      >
                        <BarChart3 className="w-3 h-3 mr-1" />
                        Dashboard
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 text-red-600 border-red-200 hover:bg-red-50"
                        onClick={() => handleClose(c.id)}
                      >
                        <Square className="w-3 h-3 mr-1" />
                        Encerrar
                      </Button>
                    </>
                  )}
                  {c.status === "CLOSED" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs h-7"
                      onClick={() =>
                        router.push(`/dashboard/campaigns/${c.id}/dashboard`)
                      }
                    >
                      <BarChart3 className="w-3 h-3 mr-1" />
                      Dashboard
                    </Button>
                  )}
                  {c.status === "DRAFT" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs h-7 text-red-600 border-red-200 hover:bg-red-50"
                      onClick={() => handleDelete(c.id)}
                    >
                      <Trash2 className="w-3 h-3 mr-1" />
                      Excluir
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
