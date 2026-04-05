"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api } from "@/lib/api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (code: string) => Promise<void>;
  checkAuth: () => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>()(persist((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (code: string) => {
    try {
      const response = await api.kakaoCallback(code);
      api.setToken(response.access_token);
      set({ user: response.user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      console.error("Login failed:", error);
      set({ user: null, isAuthenticated: false, isLoading: false });
      throw error;
    }
  },

  checkAuth: async () => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      const user = await api.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      api.clearToken();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: () => {
    api.clearToken();
    set({ user: null, isAuthenticated: false, isLoading: false });
  },
}), {
  name: "auth-storage",
  storage: createJSONStorage(() => localStorage),
  partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
}));
