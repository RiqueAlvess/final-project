"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  LayoutList,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

interface CSVImportRecord {
  id: number;
  file_name: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  errors: { row: number; data: Record<string, string>; error: string }[] | string[];
  imported_by_email: string | null;
  created_at: string;
}

interface Registro {
  id: number;
  email: string;
  unidade: number;
  unidade_name: string;
  setor: number;
  setor_name: string;
  created_at: string;
}

const STATUS_CONFIG = {
  PENDING: { label: "Pending", color: "bg-slate-100 text-slate-600 border-slate-200", Icon: Clock },
  PROCESSING: { label: "Processing", color: "bg-blue-100 text-blue-600 border-blue-200", Icon: RefreshCw },
  COMPLETED: { label: "Completed", color: "bg-green-100 text-green-700 border-green-200", Icon: CheckCircle2 },
  FAILED: { label: "Failed", color: "bg-red-100 text-red-700 border-red-200", Icon: XCircle },
};

export default function CSVImportPage() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [imports, setImports] = useState<CSVImportRecord[]>([]);
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [isLoadingImports, setIsLoadingImports] = useState(true);
  const [isLoadingRegistros, setIsLoadingRegistros] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [expandedImport, setExpandedImport] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"imports" | "records">("imports");

  // Filters for records
  const [filterUnidade, setFilterUnidade] = useState("");
  const [filterSetor, setFilterSetor] = useState("");
  const [filterEmail, setFilterEmail] = useState("");

  const fetchImports = useCallback(() => {
    setIsLoadingImports(true);
    return apiClient
      .get<{ results?: CSVImportRecord[] } | CSVImportRecord[]>("/api/organizational/csv-imports/")
      .then((res) => {
        const data = res.data;
        if (Array.isArray(data)) setImports(data);
        else if (data && "results" in data && Array.isArray(data.results)) setImports(data.results);
      })
      .finally(() => setIsLoadingImports(false));
  }, []);

  const fetchRegistros = useCallback(() => {
    setIsLoadingRegistros(true);
    const params = new URLSearchParams();
    if (filterUnidade) params.set("unidade", filterUnidade);
    if (filterSetor) params.set("setor", filterSetor);
    return apiClient
      .get<{ results?: Registro[] } | Registro[]>(`/api/organizational/registros/?${params}`)
      .then((res) => {
        const data = res.data;
        if (Array.isArray(data)) setRegistros(data);
        else if (data && "results" in data && Array.isArray(data.results)) setRegistros(data.results);
      })
      .finally(() => setIsLoadingRegistros(false));
  }, [filterUnidade, filterSetor]);

  useEffect(() => {
    fetchImports();
  }, [fetchImports]);

  useEffect(() => {
    fetchRegistros();
  }, [fetchRegistros]);

  // ── Upload handler ─────────────────────────────────────────────────────────

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
      toast({ title: "Only CSV files are accepted.", variant: "destructive" });
      return;
    }

    setIsUploading(true);
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await apiClient.post<CSVImportRecord>("/api/organizational/csv-imports/upload/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const record = res.data;
      if (record.status === "COMPLETED") {
        toast({
          title: `Import completed: ${record.successful_rows} rows imported.`,
        });
      } else {
        toast({
          title: `Import failed: ${record.errors[0] ?? "Unknown error"}`,
          variant: "destructive",
        });
      }

      await fetchImports();
      await fetchRegistros();
      setActiveTab("imports");
    } catch (err: unknown) {
      const msg = extractError(err);
      toast({ title: msg, variant: "destructive" });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function extractError(err: unknown): string {
    if (err && typeof err === "object" && "response" in err) {
      const resp = (err as { response?: { data?: unknown } }).response;
      if (resp?.data) {
        if (typeof resp.data === "string") return resp.data;
        if (typeof resp.data === "object") {
          const d = resp.data as Record<string, unknown>;
          if (d.detail) return String(d.detail);
        }
      }
    }
    return "Upload failed. Please try again.";
  }

  const filteredRegistros = registros.filter((r) => {
    if (filterEmail && !r.email.toLowerCase().includes(filterEmail.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FileSpreadsheet className="w-6 h-6 text-purple-600" />
            CSV Import
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Import organizational hierarchy records via CSV
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchImports();
              fetchRegistros();
            }}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            <Upload className="w-4 h-4" />
            {isUploading ? "Uploading…" : "Upload CSV"}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      {/* CSV format hint */}
      <Card className="border-slate-200 bg-slate-50">
        <CardContent className="p-4">
          <p className="text-sm font-medium text-slate-700 mb-1">Expected CSV format:</p>
          <pre className="text-xs text-slate-600 font-mono bg-white border border-slate-200 rounded px-3 py-2 inline-block">
            EMAIL,UNIDADE,SETOR{"\n"}
            john@company.com,Unit 1,Sector A{"\n"}
            jane@company.com,Unit 1,Sector B
          </pre>
          <p className="text-xs text-slate-400 mt-2">
            Columns are case-insensitive. Existing records will be updated.
          </p>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("imports")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "imports"
              ? "bg-white border border-b-white border-slate-200 text-purple-700 -mb-px"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Import History ({imports.length})
        </button>
        <button
          onClick={() => setActiveTab("records")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "records"
              ? "bg-white border border-b-white border-slate-200 text-purple-700 -mb-px"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <span className="flex items-center gap-1">
            <LayoutList className="w-4 h-4" />
            Records ({registros.length})
          </span>
        </button>
      </div>

      {/* ── Import History Tab ──────────────────────────────────────────────── */}
      {activeTab === "imports" && (
        <div className="space-y-3">
          {isLoadingImports ? (
            <div className="animate-pulse space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-slate-200 rounded-lg" />
              ))}
            </div>
          ) : imports.length === 0 ? (
            <Card className="border-slate-200">
              <CardContent className="p-8 text-center text-slate-400">
                No imports yet. Upload a CSV file to get started.
              </CardContent>
            </Card>
          ) : (
            imports.map((imp) => {
              const cfg = STATUS_CONFIG[imp.status];
              const StatusIcon = cfg.Icon;
              const isExpanded = expandedImport === imp.id;

              return (
                <Card key={imp.id} className="border-slate-200">
                  <CardContent className="p-4">
                    <div
                      className="flex items-center gap-3 cursor-pointer"
                      onClick={() =>
                        setExpandedImport(isExpanded ? null : imp.id)
                      }
                    >
                      <StatusIcon
                        className={`w-5 h-5 shrink-0 ${
                          imp.status === "COMPLETED"
                            ? "text-green-500"
                            : imp.status === "FAILED"
                            ? "text-red-500"
                            : imp.status === "PROCESSING"
                            ? "text-blue-500 animate-spin"
                            : "text-slate-400"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">
                          {imp.file_name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {new Date(imp.created_at).toLocaleString()} ·{" "}
                          {imp.imported_by_email ?? "—"}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <Badge variant="outline" className={cfg.color}>
                          {cfg.label}
                        </Badge>
                        <div className="text-xs text-slate-500 text-right hidden sm:block">
                          <p>
                            <span className="text-green-600 font-medium">{imp.successful_rows}</span>/
                            {imp.total_rows} rows
                          </p>
                          {imp.failed_rows > 0 && (
                            <p className="text-red-500">{imp.failed_rows} failed</p>
                          )}
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {/* Expanded error list */}
                    {isExpanded && imp.errors.length > 0 && (
                      <div className="mt-3 border-t border-slate-100 pt-3">
                        <p className="text-xs font-medium text-red-600 mb-2">
                          Errors ({imp.errors.length})
                        </p>
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                          {imp.errors.map((err, idx) => (
                            <div
                              key={idx}
                              className="text-xs bg-red-50 border border-red-100 rounded px-2 py-1 text-red-700"
                            >
                              {typeof err === "string"
                                ? err
                                : `Row ${err.row}: ${err.error}`}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {isExpanded && imp.errors.length === 0 && imp.status === "COMPLETED" && (
                      <div className="mt-3 border-t border-slate-100 pt-3">
                        <p className="text-xs text-green-600">
                          All {imp.successful_rows} rows imported successfully.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      )}

      {/* ── Records Tab ────────────────────────────────────────────────────── */}
      {activeTab === "records" && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex gap-3 flex-wrap">
            <input
              type="text"
              placeholder="Filter by email…"
              value={filterEmail}
              onChange={(e) => setFilterEmail(e.target.value)}
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-base text-slate-800">Imported Records</CardTitle>
              <CardDescription>
                {filteredRegistros.length} record(s) · Organizational hierarchy data
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {isLoadingRegistros ? (
                <div className="animate-pulse p-4 space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-8 bg-slate-200 rounded" />
                  ))}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <th className="text-left px-4 py-3 font-medium text-slate-600">Email</th>
                        <th className="text-left px-4 py-3 font-medium text-slate-600">Unidade</th>
                        <th className="text-left px-4 py-3 font-medium text-slate-600">Setor</th>
                        <th className="text-left px-4 py-3 font-medium text-slate-600">Imported At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRegistros.map((r) => (
                        <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="px-4 py-2.5 text-slate-800">{r.email}</td>
                          <td className="px-4 py-2.5">
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                              {r.unidade_name}
                            </Badge>
                          </td>
                          <td className="px-4 py-2.5">
                            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                              {r.setor_name}
                            </Badge>
                          </td>
                          <td className="px-4 py-2.5 text-slate-500 text-xs">
                            {new Date(r.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                      {filteredRegistros.length === 0 && (
                        <tr>
                          <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                            No records found. Import a CSV file to get started.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
