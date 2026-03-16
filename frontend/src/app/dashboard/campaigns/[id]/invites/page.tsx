"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  RefreshCw,
  Send,
  CheckCircle2,
  Clock,
  XCircle,
  Users,
  ChevronLeft,
  ChevronRight,
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
import campaignsApi, { Campaign, SurveyInvite } from "@/services/campaigns";

const SEND_STATUS_CONFIG: Record<
  string,
  { label: string; color: string; icon: React.ReactNode }
> = {
  PENDING: {
    label: "Pendente",
    color: "bg-slate-100 text-slate-600 border-slate-200",
    icon: <Clock className="w-3 h-3" />,
  },
  SENT: {
    label: "Enviado",
    color: "bg-blue-100 text-blue-700 border-blue-200",
    icon: <Send className="w-3 h-3" />,
  },
  FAILED: {
    label: "Falhou",
    color: "bg-red-100 text-red-700 border-red-200",
    icon: <XCircle className="w-3 h-3" />,
  },
};

const RESPONSE_STATUS_CONFIG: Record<
  string,
  { label: string; color: string }
> = {
  PENDING: { label: "Aguardando", color: "bg-amber-100 text-amber-700 border-amber-200" },
  ANSWERED: { label: "Respondido", color: "bg-green-100 text-green-700 border-green-200" },
};

export default function InvitesPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const campaignId = Number(params.id);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [invites, setInvites] = useState<SurveyInvite[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [sending, setSending] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 20;

  const loadInvites = useCallback(
    async (p = page) => {
      try {
        const res = await campaignsApi.listInvites(campaignId, p);
        setInvites(res.data.results);
        setTotal(res.data.count);
      } catch {
        toast({ title: "Erro ao carregar convites", variant: "destructive" });
      }
    },
    [campaignId, page, toast]
  );

  const loadCampaign = useCallback(async () => {
    try {
      const res = await campaignsApi.list();
      const found = res.data.results.find((c) => c.id === campaignId);
      if (found) setCampaign(found);
    } catch {
      /* ignore */
    }
  }, [campaignId]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadCampaign(), loadInvites(1)]);
      setLoading(false);
    };
    init();
  }, [loadCampaign, loadInvites]);

  const handleImport = async () => {
    setImporting(true);
    try {
      const res = await campaignsApi.importInvites(campaignId);
      toast({
        title: `${res.data.created} novos convites importados`,
        description: `Total: ${res.data.total} convites`,
      });
      loadInvites(1);
      loadCampaign();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Erro ao importar convites";
      toast({ title: msg, variant: "destructive" });
    } finally {
      setImporting(false);
    }
  };

  const handleSendSelected = async () => {
    if (selected.size === 0) return;
    setSending(true);
    try {
      const res = await campaignsApi.sendInvites(campaignId, Array.from(selected));
      toast({ title: `${res.data.enqueued} e-mails enfileirados para envio!` });
      setSelected(new Set());
      setTimeout(() => loadInvites(), 2000);
    } catch {
      toast({ title: "Erro ao enviar convites", variant: "destructive" });
    } finally {
      setSending(false);
    }
  };

  const handleSendAll = async () => {
    const pendingIds = invites
      .filter(
        (i) =>
          i.send_status !== "SENT" &&
          i.response_status === "PENDING"
      )
      .map((i) => i.id);

    if (pendingIds.length === 0) {
      toast({ title: "Nenhum convite pendente para enviar." });
      return;
    }

    setSending(true);
    try {
      const res = await campaignsApi.sendInvites(campaignId, pendingIds);
      toast({ title: `${res.data.enqueued} e-mails enfileirados!` });
      setTimeout(() => loadInvites(), 2000);
    } catch {
      toast({ title: "Erro ao enviar convites", variant: "destructive" });
    } finally {
      setSending(false);
    }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === invites.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(invites.map((i) => i.id)));
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const goPage = (p: number) => {
    setPage(p);
    loadInvites(p);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
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
          <h1 className="text-xl font-bold text-slate-900">
            {campaign?.name ?? "Campanha"}
          </h1>
          <p className="text-slate-500 text-xs">Gerenciamento de envios</p>
        </div>
      </div>

      {/* Stats bar */}
      {campaign && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Total convidados", value: campaign.total_invites },
            { label: "Respondidos", value: campaign.total_answered },
            {
              label: "Taxa de adesão",
              value:
                campaign.total_invites > 0
                  ? `${Math.round(
                      (campaign.total_answered / campaign.total_invites) * 100
                    )}%`
                  : "0%",
            },
            {
              label: "Pendentes",
              value: campaign.total_invites - campaign.total_answered,
            },
          ].map((stat) => (
            <Card key={stat.label} className="text-center p-4">
              <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Actions */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base">Convites de Pesquisa</CardTitle>
              <CardDescription className="text-xs">
                {total} registro(s) • {selected.size} selecionado(s)
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadInvites()}
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" />
                Atualizar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleImport}
                disabled={importing}
              >
                <Download className="w-3.5 h-3.5 mr-1" />
                {importing ? "Importando..." : "Importar Registros CSV"}
              </Button>
              {selected.size > 0 && (
                <Button
                  size="sm"
                  className="bg-purple-600 hover:bg-purple-700"
                  onClick={handleSendSelected}
                  disabled={sending}
                >
                  <Send className="w-3.5 h-3.5 mr-1" />
                  Enviar Selecionados ({selected.size})
                </Button>
              )}
              <Button
                size="sm"
                className="bg-blue-600 hover:bg-blue-700"
                onClick={handleSendAll}
                disabled={sending}
              >
                <Send className="w-3.5 h-3.5 mr-1" />
                {sending ? "Enviando..." : "Enviar Todos Pendentes"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 mx-auto animate-spin mb-2" />
              Carregando...
            </div>
          ) : invites.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium text-slate-600">Nenhum convite encontrado</p>
              <p className="text-sm mt-1">
                Clique em &quot;Importar Registros CSV&quot; para gerar os convites.
              </p>
            </div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-y border-slate-200">
                  <tr>
                    <th className="w-10 px-4 py-3">
                      <input
                        type="checkbox"
                        checked={
                          selected.size === invites.length && invites.length > 0
                        }
                        onChange={toggleSelectAll}
                        className="rounded border-slate-300"
                      />
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Hash do Email
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Status Envio
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Status Resposta
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Enviado em
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {invites.map((invite) => {
                    const sendCfg = SEND_STATUS_CONFIG[invite.send_status];
                    const respCfg = RESPONSE_STATUS_CONFIG[invite.response_status];
                    const isAnswered = invite.response_status === "ANSWERED";
                    return (
                      <tr
                        key={invite.id}
                        className={`hover:bg-slate-50 transition-colors ${
                          isAnswered ? "opacity-60" : ""
                        }`}
                      >
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            disabled={isAnswered}
                            checked={selected.has(invite.id)}
                            onChange={() => toggleSelect(invite.id)}
                            className="rounded border-slate-300"
                          />
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-500">
                          {invite.email_hash.slice(0, 16)}…
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            variant="outline"
                            className={`text-xs gap-1 ${sendCfg.color}`}
                          >
                            {sendCfg.icon}
                            {sendCfg.label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                            variant="outline"
                            className={`text-xs ${respCfg.color}`}
                          >
                            {isAnswered && (
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                            )}
                            {respCfg.label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-slate-500 text-xs">
                          {invite.sent_at
                            ? new Date(invite.sent_at).toLocaleString("pt-BR")
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
                  <p className="text-xs text-slate-500">
                    Página {page} de {totalPages} ({total} registros)
                  </p>
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 1}
                      onClick={() => goPage(page - 1)}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === totalPages}
                      onClick={() => goPage(page + 1)}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
