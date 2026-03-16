"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Building2,
  TrendingUp,
  ShieldAlert,
  UserCheck,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/services/api";
import { useAuth } from "@/hooks/use-auth";

interface DashboardStats {
  users: {
    total: number;
    rh: number;
    leaders: number;
    locked: number;
  };
  tenant: {
    name: string;
    schema: string;
  };
}

interface StatCardProps {
  title: string;
  value: number | string;
  description: string;
  icon: React.ReactNode;
  trend?: { value: number; positive: boolean };
  color: string;
}

function StatCard({ title, value, description, icon, trend, color }: StatCardProps) {
  return (
    <Card className="border-slate-200 hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl ${color}`}>{icon}</div>
          {trend && (
            <div
              className={`flex items-center gap-1 text-xs font-medium ${
                trend.positive ? "text-green-600" : "text-red-600"
              }`}
            >
              {trend.positive ? (
                <ArrowUpRight className="w-3 h-3" />
              ) : (
                <ArrowDownRight className="w-3 h-3" />
              )}
              {trend.value}%
            </div>
          )}
        </div>
        <div>
          <p className="text-3xl font-bold text-slate-800 mb-1">{value}</p>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="text-xs text-slate-400 mt-1">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get<DashboardStats>("/api/dashboard/stats/")
      .then((res) => setStats(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            {greeting()}, {user?.first_name}!
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            {stats?.tenant.name
              ? `You are accessing ${stats.tenant.name}`
              : "Loading workspace..."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="border-purple-200 bg-purple-50 text-purple-700 font-medium"
          >
            <Activity className="w-3 h-3 mr-1" />
            {user?.role}
          </Badge>
        </div>
      </div>

      {/* Stats grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="border-slate-200">
              <CardContent className="p-6">
                <div className="animate-pulse space-y-3">
                  <div className="w-12 h-12 bg-slate-200 rounded-xl" />
                  <div className="h-8 bg-slate-200 rounded w-16" />
                  <div className="h-4 bg-slate-200 rounded w-24" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Users"
            value={stats?.users.total ?? 0}
            description="Active users in this tenant"
            icon={<Users className="w-5 h-5 text-blue-600" />}
            color="bg-blue-50"
            trend={{ value: 12, positive: true }}
          />
          <StatCard
            title="RH Users"
            value={stats?.users.rh ?? 0}
            description="Human Resources team"
            icon={<UserCheck className="w-5 h-5 text-green-600" />}
            color="bg-green-50"
          />
          <StatCard
            title="Leaders"
            value={stats?.users.leaders ?? 0}
            description="Management & team leads"
            icon={<TrendingUp className="w-5 h-5 text-purple-600" />}
            color="bg-purple-50"
          />
          <StatCard
            title="Locked Accounts"
            value={stats?.users.locked ?? 0}
            description="Requires admin attention"
            icon={<ShieldAlert className="w-5 h-5 text-red-600" />}
            color="bg-red-50"
            trend={
              stats?.users.locked
                ? { value: stats.users.locked, positive: false }
                : undefined
            }
          />
        </div>
      )}

      {/* Tenant information card */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-800">
              <Building2 className="w-5 h-5 text-purple-600" />
              Workspace Information
            </CardTitle>
            <CardDescription>Details about your current tenant</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-500">Company</span>
              <span className="text-sm font-medium text-slate-800">
                {stats?.tenant.name ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-500">Schema</span>
              <code className="text-xs bg-slate-100 px-2 py-1 rounded font-mono text-slate-700">
                {stats?.tenant.schema ?? "—"}
              </code>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-500">Your Role</span>
              <Badge
                variant="outline"
                className="border-purple-200 bg-purple-50 text-purple-700"
              >
                {user?.role}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-800">
              <Activity className="w-5 h-5 text-green-600" />
              System Status
            </CardTitle>
            <CardDescription>Platform health overview</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-500">API</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600 font-medium">Operational</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-500">Database</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600 font-medium">Connected</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-500">Background Jobs</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-green-600 font-medium">Running</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
