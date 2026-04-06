"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api } from "@/lib/api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasChecked: boolean;
  login: (code: string) => Promise<void>;
  checkAuth: () => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>()(persist((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  _hasChecked: false,

  login: async (code: string) => {
    try {
      const response = await api.kakaoCallback(code);
      // access + refresh 토큰 모두 저장
      if (response.refresh_token) {
        api.setTokens(response.access_token, response.refresh_token);
      } else {
        api.setToken(response.access_token);
      }
      set({ user: response.user, isAuthenticated: true, isLoading: false, _hasChecked: true });
    } catch (error) {
      console.error("Login failed:", error);
      set({ user: null, isAuthenticated: false, isLoading: false, _hasChecked: true });
      throw error;
    }
  },

  checkAuth: async () => {
    // 이미 확인했으면 중복 호출 방지
    if (get()._hasChecked) {
      set({ isLoading: false });
      return;
    }
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false, _hasChecked: true });
        return;
      }
      const user = await api.getMe();
      set({ user, isAuthenticated: true, isLoading: false, _hasChecked: true });
    } catch {
      api.clearToken();
      set({ user: null, isAuthenticated: false, isLoading: false, _hasChecked: true });
    }
  },

  logout: () => {
    api.clearToken();
    set({ user: null, isAuthenticated: false, isLoading: false, _hasChecked: false });
  },
}), {
  name: "auth-storage",
  storage: createJSONStorage(() => localStorage),
  // isAuthenticated를 persist하지 않음 - 항상 서버에서 검증
  partialize: (state) => ({ user: state.user }),
}));
