/**
 * API 클라이언트 싱글톤.
 * 모든 백엔드 요청을 관리하며, JWT 토큰을 자동 주입합니다.
 * - access token 만료 시 refresh token으로 자동 갱신
 * - 기본 요청 30초 timeout, GPT 생성 호출은 60~90초로 개별 지정
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
const REQUEST_TIMEOUT_MS = 30_000;

class ApiClient {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private _refreshing: Promise<boolean> | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.token = accessToken;
    this.refreshToken = refreshToken;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
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
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  private async _tryRefresh(): Promise<boolean> {
    if (!this.refreshToken) return false;
    try {
      const res = await fetch(`${API_URL}/auth/refresh?refresh_token=${encodeURIComponent(this.refreshToken)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
    requireAuth = true
  ): Promise<T> {
    if (requireAuth && !this.token) {
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
      throw new Error("인증이 필요합니다.");
    }

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
      signal: options.signal || AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    if (response.status === 401 && requireAuth) {
      // refresh token으로 재시도 (중복 방지)
      if (!this._refreshing) {
        this._refreshing = this._tryRefresh().finally(() => {
          this._refreshing = null;
        });
      }
      const refreshed = await this._refreshing;
      if (refreshed) {
        // 새 토큰으로 재요청
        headers["Authorization"] = `Bearer ${this.token}`;
        const retry = await fetch(`${API_URL}${path}`, {
          ...options,
          headers,
          signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        });
        if (retry.ok) return retry.json();
      }
      // refresh도 실패
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
      throw new Error("인증이 만료되었습니다.");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const detail = error.detail;
      const message = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(", ")
          : "요청에 실패했습니다.";
      throw new Error(message);
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
    verification_token: string;
    business_name: string;
    business_type: string;
    address: string;
    dong_name: string;
    gu_name: string;
    lat: number;
    lng: number;
    business_start_date?: string;
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
      signal: AbortSignal.timeout(60_000), // GPT 생성은 60초 타임아웃
    });
  }

  async logSubsidySignal(
    subsidyId: string,
    signalType: "view" | "click" | "draft" | "apply" = "click",
  ): Promise<{ ok: boolean; signal_type: string }> {
    return this.request(
      `/subsidies/${subsidyId}/signal?signal_type=${signalType}`,
      { method: "POST" }
    );
  }

  async getIcpProfile(): Promise<{
    has_signals: boolean;
    signal_count: number;
    weighted_signal_total: number;
    preferred_organizations: { name: string; score: number }[];
    amount_range: { median: number; min: number; max: number } | null;
    top_keywords: { word: string; score: number }[];
  }> {
    return this.request("/subsidies/icp-profile");
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

  // ===== 인사이트 =====
  async getCompetitionAnalysis(): Promise<any> {
    return this.request("/insights/competition");
  }

  async getMarketingStrategy(refresh = false): Promise<any> {
    // GPT-4o + max_tokens=4000 (가장 무거움) → 90초 여유
    return this.request(
      `/insights/marketing${refresh ? "?refresh=true" : ""}`,
      { signal: AbortSignal.timeout(90_000) },
      true,
    );
  }

  async getDeepReport(refresh = false): Promise<any> {
    return this.request(`/insights/deep-report${refresh ? "?refresh=true" : ""}`, {
      signal: AbortSignal.timeout(90_000),
    });
  }

  async getMenuStrategy(refresh = false): Promise<any> {
    return this.request(`/insights/menu-strategy${refresh ? "?refresh=true" : ""}`, {
      signal: AbortSignal.timeout(60_000),
    }, true);
  }

  async getSurvivalScore(refresh = false): Promise<any> {
    return this.request(`/insights/survival-score${refresh ? "?refresh=true" : ""}`, {
      signal: AbortSignal.timeout(45_000),
    });
  }

  // ===== 주간 리포트 =====
  async downloadWeeklyReport(): Promise<Blob> {
    if (!this.token) {
      throw new Error("인증이 필요합니다.");
    }
    const res = await fetch(`${API_URL}/reports/weekly`, {
      method: "GET",
      headers: { Authorization: `Bearer ${this.token}` },
      signal: AbortSignal.timeout(60_000),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "리포트 생성에 실패했습니다.");
    }
    return res.blob();
  }

  // ===== 음성 =====
  async voiceQuery(text: string): Promise<VoiceQueryResponse> {
    return this.request("/voice/query", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  // ===== 결제 (카카오페이) =====
  async readyKakaoPayment(): Promise<{
    tid: string;
    next_redirect_pc_url: string;
    next_redirect_mobile_url: string;
    partner_order_id: string;
  }> {
    return this.request("/payments/kakao/ready", { method: "POST" });
  }

  async approveKakaoPayment(body: {
    tid: string;
    partner_order_id: string;
    pg_token: string;
  }): Promise<{
    status: string;
    item_name: string;
    total_amount: number;
    approved_at: string;
    expired_at: string | null;
  }> {
    return this.request("/payments/kakao/approve", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async getSubscriptionStatus(): Promise<{
    is_pro: boolean;
    status: string;
    started_at: string | null;
    expired_at: string | null;
  }> {
    return this.request("/payments/subscription");
  }
}

export const api = new ApiClient();
