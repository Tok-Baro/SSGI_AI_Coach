/**
 * API 클라이언트 싱글톤.
 * 모든 백엔드 요청을 관리하며, JWT 토큰을 자동 주입합니다.
 */

import type {
  AuthResponse,
  User,
  VerifyBusinessResponse,
  KakaoLocalSearchResult,
  CompleteOnboardingResponse,
  DashboardData,
  DailyAction,
  SubsidyMatchesResponse,
  ApplyDraftResponse,
  Coupon,
  CreateCouponRequest,
  VoiceQueryResponse,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
    requireAuth = true
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (requireAuth && this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
      throw new Error("인증이 만료되었습니다.");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "요청에 실패했습니다.");
    }

    return response.json();
  }

  // ===== 인증 =====
  async kakaoCallback(code: string): Promise<AuthResponse> {
    return this.request<AuthResponse>(
      `/auth/kakao/callback?code=${encodeURIComponent(code)}`,
      { method: "POST" },
      false
    );
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  async registerFcmToken(fcmToken: string): Promise<void> {
    await this.request(`/auth/fcm-token?fcm_token=${encodeURIComponent(fcmToken)}`, {
      method: "POST",
    });
  }

  // ===== 온보딩 =====
  async verifyBusiness(businessNumber: string): Promise<VerifyBusinessResponse> {
    return this.request("/onboarding/verify-business", {
      method: "POST",
      body: JSON.stringify({ business_number: businessNumber }),
    });
  }

  async searchBusiness(query: string): Promise<KakaoLocalSearchResult[]> {
    return this.request(`/onboarding/search-business?query=${encodeURIComponent(query)}`);
  }

  async completeOnboarding(data: {
    business_number: string;
    business_name: string;
    business_type: string;
    address: string;
    dong_name: string;
    gu_name: string;
    lat: number;
    lng: number;
  }): Promise<CompleteOnboardingResponse> {
    return this.request("/onboarding/complete", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // ===== 대시보드 =====
  async getDashboard(): Promise<DashboardData> {
    return this.request("/dashboard");
  }

  // ===== 일일 액션 =====
  async getTodayAction(): Promise<DailyAction> {
    return this.request("/actions/today");
  }

  async getActionHistory(days = 30): Promise<DailyAction[]> {
    return this.request(`/actions/history?days=${days}`);
  }

  async completeAction(actionId: string): Promise<{ success: boolean; message: string }> {
    return this.request(`/actions/${actionId}/complete`, { method: "POST" });
  }

  // ===== 지원사업 =====
  async getSubsidyMatches(): Promise<SubsidyMatchesResponse> {
    return this.request("/subsidies/matches");
  }

  async generateApplyDraft(
    subsidyId: string,
    additionalInfo?: string
  ): Promise<ApplyDraftResponse> {
    return this.request("/subsidies/apply-draft", {
      method: "POST",
      body: JSON.stringify({
        subsidy_id: subsidyId,
        additional_info: additionalInfo,
      }),
    });
  }

  // ===== 쿠폰 =====
  async createCoupon(data: CreateCouponRequest): Promise<Coupon> {
    return this.request("/coupons/create", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listCoupons(): Promise<Coupon[]> {
    return this.request("/coupons");
  }

  async getCoupon(couponId: string): Promise<Coupon> {
    return this.request(`/coupons/${couponId}`, {}, false);
  }

  async scanCoupon(couponId: string): Promise<{ success: boolean; scan_count: number }> {
    return this.request(`/coupons/${couponId}/scan`, { method: "POST" }, false);
  }

  // ===== 음성 =====
  async voiceQuery(text: string): Promise<VoiceQueryResponse> {
    return this.request("/voice/query", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }
}

export const api = new ApiClient();
