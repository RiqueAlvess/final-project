"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Users,
  UserPlus,
  Pencil,
  Trash2,
  ShieldAlert,
  ShieldCheck,
  Settings2,
  X,
  Check,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/services/api";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

interface LeaderPermission {
  id: number;
  unidade: number;
  unidade_name: string;
  setor: number | null;
  setor_name: string | null;
}

interface UserItem {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "GLOBAL_ADMIN" | "RH" | "LEADER";
  is_active: boolean;
  is_locked: boolean;
  date_joined: string;
  last_login: string | null;
  leader_permissions: LeaderPermission[];
}

interface Unidade {
  id: number;
  name: string;
  setores: { id: number; name: string; unidade: number; created_at: string }[];
}

type ModalMode = "create" | "edit" | "permissions" | null;

const ROLE_COLORS: Record<string, string> = {
  GLOBAL_ADMIN: "bg-red-100 text-red-700 border-red-200",
  RH: "bg-blue-100 text-blue-700 border-blue-200",
  LEADER: "bg-green-100 text-green-700 border-green-200",
};

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const { toast } = useToast();

  const [users, setUsers] = useState<UserItem[]>([]);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Modal state
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    role: "RH" as "RH" | "LEADER",
    password: "",
    password_confirm: "",
  });
  const [formError, setFormError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Permissions state
  const [permRows, setPermRows] = useState<{ unidade: number; setor: number | null }[]>([]);

  const fetchUsers = useCallback(() => {
    return apiClient.get<{ results?: UserItem[] } | UserItem[]>("/api/users/").then((res) => {
      const data = res.data;
      if (Array.isArray(data)) setUsers(data);
      else if (data && "results" in data && Array.isArray(data.results)) setUsers(data.results);
    });
  }, []);

  const fetchUnidades = useCallback(() => {
    return apiClient
      .get<{ results?: Unidade[] } | Unidade[]>("/api/organizational/unidades/")
      .then((res) => {
        const data = res.data;
        if (Array.isArray(data)) setUnidades(data);
        else if (data && "results" in data && Array.isArray(data.results)) setUnidades(data.results);
      })
      .catch(() => setUnidades([]));
  }, []);

  useEffect(() => {
    Promise.all([fetchUsers(), fetchUnidades()]).finally(() => setIsLoading(false));
  }, [fetchUsers, fetchUnidades]);

  // ── Open modals ────────────────────────────────────────────────────────────

  function openCreate() {
    setFormData({ email: "", first_name: "", last_name: "", role: "RH", password: "", password_confirm: "" });
    setFormError("");
    setSelectedUser(null);
    setModalMode("create");
  }

  function openEdit(u: UserItem) {
    setFormData({ email: u.email, first_name: u.first_name, last_name: u.last_name, role: u.role === "GLOBAL_ADMIN" ? "RH" : u.role, password: "", password_confirm: "" });
    setFormError("");
    setSelectedUser(u);
    setModalMode("edit");
  }

  function openPermissions(u: UserItem) {
    setSelectedUser(u);
    setPermRows(
      u.leader_permissions.map((p) => ({ unidade: p.unidade, setor: p.setor }))
    );
    setModalMode("permissions");
  }

  function closeModal() {
    setModalMode(null);
    setSelectedUser(null);
    setFormError("");
  }

  // ── Create user ────────────────────────────────────────────────────────────

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");

    if (formData.password !== formData.password_confirm) {
      setFormError("Passwords do not match.");
      return;
    }

    setIsSaving(true);
    try {
      await apiClient.post("/api/users/", formData);
      toast({ title: "User created successfully." });
      closeModal();
      fetchUsers();
    } catch (err: unknown) {
      const msg = extractError(err);
      setFormError(msg);
    } finally {
      setIsSaving(false);
    }
  }

  // ── Edit user ──────────────────────────────────────────────────────────────

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUser) return;
    setFormError("");
    setIsSaving(true);
    try {
      await apiClient.patch(`/api/users/${selectedUser.id}/`, {
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
      });
      toast({ title: "User updated successfully." });
      closeModal();
      fetchUsers();
    } catch (err: unknown) {
      setFormError(extractError(err));
    } finally {
      setIsSaving(false);
    }
  }

  // ── Delete user ────────────────────────────────────────────────────────────

  async function handleDelete(u: UserItem) {
    if (!confirm(`Deactivate ${u.full_name}?`)) return;
    try {
      await apiClient.delete(`/api/users/${u.id}/`);
      toast({ title: "User deactivated." });
      fetchUsers();
    } catch {
      toast({ title: "Failed to deactivate user.", variant: "destructive" });
    }
  }

  // ── Toggle lock ────────────────────────────────────────────────────────────

  async function handleToggleLock(u: UserItem) {
    const action = u.is_locked ? "unlock" : "lock";
    try {
      await apiClient.post(`/api/users/${u.id}/${action}/`);
      toast({ title: `User ${action}ed.` });
      fetchUsers();
    } catch {
      toast({ title: `Failed to ${action} user.`, variant: "destructive" });
    }
  }

  // ── Save permissions ───────────────────────────────────────────────────────

  async function handleSavePermissions(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUser) return;
    setIsSaving(true);
    try {
      await apiClient.put(`/api/organizational/permissions/${selectedUser.id}/`, {
        permissions: permRows,
      });
      toast({ title: "Permissions saved." });
      closeModal();
      fetchUsers();
    } catch (err: unknown) {
      toast({ title: extractError(err), variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  function extractError(err: unknown): string {
    if (err && typeof err === "object" && "response" in err) {
      const resp = (err as { response?: { data?: unknown } }).response;
      if (resp?.data) {
        if (typeof resp.data === "string") return resp.data;
        if (typeof resp.data === "object") {
          const d = resp.data as Record<string, unknown>;
          if (d.detail) return String(d.detail);
          const first = Object.values(d)[0];
          return Array.isArray(first) ? String(first[0]) : String(first);
        }
      }
    }
    return "An unexpected error occurred.";
  }

  const setoresForUnidade = (unidadeId: number) =>
    unidades.find((u) => u.id === unidadeId)?.setores ?? [];

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-48" />
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-600" />
            User Management
          </h1>
          <p className="text-slate-500 text-sm mt-1">{users.length} user(s) in this workspace</p>
        </div>
        {(currentUser?.role === "RH" || currentUser?.role === "GLOBAL_ADMIN") && (
          <Button
            onClick={openCreate}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            <UserPlus className="w-4 h-4" />
            New User
          </Button>
        )}
      </div>

      {/* Table */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-slate-800 text-base">Users</CardTitle>
          <CardDescription>Manage users, roles, and leader access permissions.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Email</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Role</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-800">{u.full_name}</td>
                    <td className="px-4 py-3 text-slate-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className={ROLE_COLORS[u.role] ?? ""}>
                        {u.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      {u.is_locked ? (
                        <Badge variant="outline" className="bg-red-50 text-red-600 border-red-200">
                          Locked
                        </Badge>
                      ) : u.is_active ? (
                        <Badge variant="outline" className="bg-green-50 text-green-600 border-green-200">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-slate-100 text-slate-500">
                          Inactive
                        </Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {u.role === "LEADER" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Configure permissions"
                            onClick={() => openPermissions(u)}
                          >
                            <Settings2 className="w-4 h-4 text-purple-500" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Edit user"
                          onClick={() => openEdit(u)}
                        >
                          <Pencil className="w-4 h-4 text-slate-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          title={u.is_locked ? "Unlock account" : "Lock account"}
                          onClick={() => handleToggleLock(u)}
                        >
                          {u.is_locked ? (
                            <ShieldCheck className="w-4 h-4 text-green-500" />
                          ) : (
                            <ShieldAlert className="w-4 h-4 text-amber-500" />
                          )}
                        </Button>
                        {currentUser?.id !== u.id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Deactivate user"
                            onClick={() => handleDelete(u)}
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                      No users found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ── Create / Edit Modal ─────────────────────────────────────────────── */}
      {(modalMode === "create" || modalMode === "edit") && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-800">
                {modalMode === "create" ? "Create User" : "Edit User"}
              </h2>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={modalMode === "create" ? handleCreate : handleEdit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="first_name">First Name</Label>
                  <Input
                    id="first_name"
                    value={formData.first_name}
                    onChange={(e) => setFormData((d) => ({ ...d, first_name: e.target.value }))}
                    required
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="last_name">Last Name</Label>
                  <Input
                    id="last_name"
                    value={formData.last_name}
                    onChange={(e) => setFormData((d) => ({ ...d, last_name: e.target.value }))}
                    required
                    className="mt-1"
                  />
                </div>
              </div>

              {modalMode === "create" && (
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData((d) => ({ ...d, email: e.target.value }))}
                    required
                    className="mt-1"
                  />
                </div>
              )}

              <div>
                <Label htmlFor="role">Role</Label>
                <select
                  id="role"
                  value={formData.role}
                  onChange={(e) =>
                    setFormData((d) => ({ ...d, role: e.target.value as "RH" | "LEADER" }))
                  }
                  className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="RH">RH</option>
                  <option value="LEADER">Leader</option>
                </select>
              </div>

              {modalMode === "create" && (
                <>
                  <div>
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData((d) => ({ ...d, password: e.target.value }))}
                      required
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password_confirm">Confirm Password</Label>
                    <Input
                      id="password_confirm"
                      type="password"
                      value={formData.password_confirm}
                      onChange={(e) =>
                        setFormData((d) => ({ ...d, password_confirm: e.target.value }))
                      }
                      required
                      className="mt-1"
                    />
                  </div>
                </>
              )}

              {formError && (
                <p className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  {formError}
                </p>
              )}

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {isSaving ? "Saving…" : modalMode === "create" ? "Create" : "Save"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Permissions Modal ───────────────────────────────────────────────── */}
      {modalMode === "permissions" && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">
                  Leader Permissions
                </h2>
                <p className="text-sm text-slate-500">{selectedUser.full_name}</p>
              </div>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSavePermissions} className="space-y-4">
              <p className="text-sm text-slate-600">
                Configure which Unidades and Setores this leader can access. Leave Setor empty to
                grant access to all Setores within the Unidade.
              </p>

              {permRows.map((row, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-slate-50 rounded-lg p-3">
                  <div className="flex-1">
                    <Label className="text-xs text-slate-500">Unidade</Label>
                    <select
                      value={row.unidade}
                      onChange={(e) => {
                        const newRows = [...permRows];
                        newRows[idx] = { unidade: Number(e.target.value), setor: null };
                        setPermRows(newRows);
                      }}
                      className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value={0} disabled>
                        Select Unidade
                      </option>
                      {unidades.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex-1">
                    <Label className="text-xs text-slate-500">Setor (optional)</Label>
                    <select
                      value={row.setor ?? ""}
                      onChange={(e) => {
                        const newRows = [...permRows];
                        newRows[idx] = {
                          ...newRows[idx],
                          setor: e.target.value ? Number(e.target.value) : null,
                        };
                        setPermRows(newRows);
                      }}
                      disabled={!row.unidade}
                      className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                    >
                      <option value="">All Setores</option>
                      {setoresForUnidade(row.unidade).map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={() => setPermRows((rows) => rows.filter((_, i) => i !== idx))}
                    className="mt-4 text-red-400 hover:text-red-600 shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full border-dashed"
                onClick={() =>
                  setPermRows((rows) => [...rows, { unidade: unidades[0]?.id ?? 0, setor: null }])
                }
              >
                + Add Permission
              </Button>

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={closeModal} className="flex-1">
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white gap-2"
                >
                  {isSaving ? (
                    "Saving…"
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      Save Permissions
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
