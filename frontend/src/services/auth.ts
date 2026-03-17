import axios, { AxiosError } from "axios";
import Cookies from "js-cookie";
import { apiClient } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "GLOBAL_ADMIN" | "RH" | "LEADER";
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

const extractErrorMessage = (error: unknown): string => {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (detail) return detail;
    const errors = error.response?.data;
    if (typeof errors === "object") {
      const firstKey = Object.keys(errors)[0];
      if (firstKey) {
        const val = errors[firstKey];
        return Array.isArray(val) ? val[0] : String(val);
      }
    }
    if (error.response?.status === 429) {
      return "Too many login attempts. Please wait and try again.";
    }
  }
  return "An unexpected error occurred.";
};

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    try {
      const response = await axios.post<LoginResponse>(`${API_URL}/api/auth/login/`, {
        email,
        password,
      });

      const { access, refresh, user } = response.data;

      // Store tokens
      Cookies.set("access_token", access, { expires: 1 / 96, sameSite: "strict" }); // 15min
      Cookies.set("refresh_token", refresh, { expires: 7, sameSite: "strict" });

      // Cache user in localStorage
      if (typeof window !== "undefined") {
        sessionStorage.setItem("user", JSON.stringify(user));
      }

      return response.data;
    } catch (error) {
      throw new Error(extractErrorMessage(error));
    }
  },

  async logout(): Promise<void> {
    const refreshToken = Cookies.get("refresh_token");
    try {
      if (refreshToken) {
        await apiClient.post("/api/auth/logout/", { refresh: refreshToken });
      }
    } finally {
      Cookies.remove("access_token");
      Cookies.remove("refresh_token");
      if (typeof window !== "undefined") {
        sessionStorage.removeItem("user");
      }
    }
  },

  async requestPasswordReset(email: string): Promise<void> {
    try {
      await axios.post(`${API_URL}/api/auth/password/reset/`, { email });
    } catch (error) {
      throw new Error(extractErrorMessage(error));
    }
  },

  async confirmPasswordReset(
    token: string,
    new_password: string,
    new_password_confirm: string
  ): Promise<void> {
    try {
      await axios.post(`${API_URL}/api/auth/password/reset/confirm/`, {
        token,
        new_password,
        new_password_confirm,
      });
    } catch (error) {
      throw new Error(extractErrorMessage(error));
    }
  },

  getStoredUser(): User | null {
    if (typeof window === "undefined") return null;
    const stored = sessionStorage.getItem("user");
    if (!stored) return null;
    try {
      return JSON.parse(stored) as User;
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!Cookies.get("access_token") || !!Cookies.get("refresh_token");
  },
};
