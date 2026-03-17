"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authService, User } from "@/services/auth";
import { apiClient } from "@/services/api";

export function useAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = authService.getStoredUser();
    if (stored) {
      setUser(stored);
      // Refresh from API in background
      apiClient
        .get<User>("/api/users/me/")
        .then((res) => {
          setUser(res.data);
          sessionStorage.setItem("user", JSON.stringify(res.data));
        })
        .catch(() => {
          // If fetch fails, the token may be expired - interceptor handles redirect
        })
        .finally(() => setIsLoading(false));
    } else if (!authService.isAuthenticated()) {
      setIsLoading(false);
      router.replace("/auth/login");
    } else {
      apiClient
        .get<User>("/api/users/me/")
        .then((res) => {
          setUser(res.data);
          sessionStorage.setItem("user", JSON.stringify(res.data));
        })
        .finally(() => setIsLoading(false));
    }
  }, [router]);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    router.push("/auth/login");
  }, [router]);

  return { user, isLoading, logout };
}
