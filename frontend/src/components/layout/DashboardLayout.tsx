"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Building2,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Bell,
  Search,
  Shield,
  FileSpreadsheet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    roles: ["GLOBAL_ADMIN", "RH", "LEADER"],
  },
  {
    label: "Users",
    href: "/dashboard/users",
    icon: Users,
    roles: ["GLOBAL_ADMIN", "RH"],
  },
  {
    label: "Organization",
    href: "/dashboard/organization",
    icon: Building2,
    roles: ["GLOBAL_ADMIN", "RH"],
  },
  {
    label: "CSV Import",
    href: "/dashboard/csv-import",
    icon: FileSpreadsheet,
    roles: ["GLOBAL_ADMIN", "RH"],
  },
  {
    label: "Admin",
    href: "/admin",
    icon: Shield,
    roles: ["GLOBAL_ADMIN"],
    external: true,
  },
  {
    label: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
    roles: ["GLOBAL_ADMIN", "RH"],
  },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const userInitials = user
    ? `${user.first_name[0] ?? ""}${user.last_name[0] ?? ""}`.toUpperCase()
    : "U";

  const filteredNavItems = navItems.filter(
    (item) => !user?.role || item.roles.includes(user.role)
  );

  const roleBadgeColor: Record<string, string> = {
    GLOBAL_ADMIN: "bg-red-100 text-red-700 border-red-200",
    RH: "bg-blue-100 text-blue-700 border-blue-200",
    LEADER: "bg-green-100 text-green-700 border-green-200",
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-12 h-12 bg-purple-200 rounded-xl" />
          <div className="w-32 h-4 bg-slate-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full w-64 bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:z-auto",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-white font-semibold text-sm leading-none">SaaS Platform</p>
              <p className="text-slate-400 text-xs mt-0.5">Enterprise</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <p className="text-slate-500 text-xs uppercase tracking-wider font-medium px-3 mb-2">
            Navigation
          </p>
          {filteredNavItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return item.external ? (
              <a
                key={item.href}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  "text-slate-400 hover:text-white hover:bg-slate-700/60"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {item.label}
              </a>
            ) : (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-purple-600/20 text-purple-300 border border-purple-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-700/60"
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {item.label}
                {isActive && <div className="ml-auto w-1.5 h-1.5 bg-purple-400 rounded-full" />}
              </Link>
            );
          })}
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3 px-2 py-2">
            <Avatar className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600">
              <AvatarFallback className="text-white text-xs font-bold bg-transparent">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-slate-400 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 justify-start gap-2"
            onClick={logout}
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="bg-white border-b border-slate-200 px-4 lg:px-6 py-3 flex items-center gap-4 sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-slate-500 hover:text-slate-700"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search (decorative) */}
          <div className="flex-1 max-w-md hidden md:flex items-center gap-2 bg-slate-100 rounded-lg px-3 py-2">
            <Search className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400 text-sm">Search...</span>
          </div>

          <div className="ml-auto flex items-center gap-3">
            {/* Role badge */}
            {user?.role && (
              <Badge
                variant="outline"
                className={cn("text-xs font-medium", roleBadgeColor[user.role])}
              >
                {user.role}
              </Badge>
            )}

            {/* Notifications */}
            <Button variant="ghost" size="sm" className="relative text-slate-500">
              <Bell className="w-4 h-4" />
            </Button>

            {/* User menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 text-sm text-slate-700 hover:text-slate-900 focus:outline-none">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-gradient-to-br from-purple-500 to-blue-600 text-white text-xs font-bold">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:block font-medium">{user?.first_name}</span>
                  <ChevronDown className="w-3 h-3 hidden md:block text-slate-400" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-medium">{user?.full_name}</p>
                    <p className="text-xs text-slate-500 font-normal">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/dashboard/settings">
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-red-600 focus:text-red-600 focus:bg-red-50"
                  onClick={logout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
