// ===== 사용자 =====
export interface User {
  id: string;
  kakao_id: number;
  email: string | null;
  nickname: string;
  profile_image_url: string | null;
  business_number: string | null;
  business_name: string | null;
  business_type: string | null;
  address: string | null;
  dong_name: string | null;
  gu_name: string | null;
  plan_tier: "free" | "pro";
  onboarding_completed: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ===== 온보딩 =====
export interface VerifyBusinessResponse {
  is_valid: boolean;
  business_status: string;
  business_name: string | null;
  tax_type: string | null;
  verification_token: string | null;
}

export interface KakaoLocalSearchResult {
  place_name: string;
  address_name: string;
  road_address_name: string | null;
  category_name: string;
  x: string; // lng
  y: string; // lat
  phone: string | null;
}

export interface CompleteOnboardingResponse {
  success: boolean;
  message: string;
  subsidy_count: number;
  risk_score: number;
}

// ===== 일일 액션 =====
export interface DailyAction {
  id: string;
  date: string;
  action_type: "subsidy" | "event" | "coupon" | "competitor" | "population";
  title: string;
  description: string;
  risk_score: number;
  data_source: string | null;
  cta_type: string | null;
  cta_payload: Record<string, any> | null;
  is_completed: boolean;
  completed_at: string | null;
}

// ===== 지원사업 =====
export interface Subsidy {
  id: string;
  title: string;
  organization: string;
  deadline: string | null;
  max_amount: number | null;
  eligibility_summary: string | null;
  description: string;
  application_url: string | null;
  relevance_score: number | null;
  days_until_deadline: number | null;
  social_proof_message: string | null;
}

export interface SubsidyMatchesResponse {
  matches: Subsidy[];
  total_potential_amount: number;
  loss_message: string;
}

export interface ApplyDraftResponse {
  draft_text: string;
  subsidy_title: string;
  estimated_time_saved: string;
}

// ===== 쿠폰 =====
export interface Coupon {
  id: string;
  title: string;
  discount_type: "percent" | "fixed" | "bogo" | "free_item";
  discount_value: number | null;
  description: string | null;
  valid_from: string | null;
  valid_until: string | null;
  qr_data: string;
  qr_image_base64: string;
  download_count: number;
  scan_count: number;
  is_active: boolean;
}

export interface CreateCouponRequest {
  title: string;
  discount_type: string;
  discount_value?: number;
  description?: string;
  valid_days?: number;
}

// ===== 위험도 분석 =====
export interface RiskFactor {
  name: string;
  label: string;
  score: number;
  weight: number;
  description: string;
  data_available: boolean;
}

export interface RiskTrendPoint {
  date: string;
  score: number;
}

// ===== 대시보드 =====
export interface DashboardData {
  user: {
    nickname: string;
    business_name: string;
    plan_tier: string;
  };
  risk_score: number;
  risk_factors: RiskFactor[];
  risk_trend: RiskTrendPoint[];
  trend_direction: "improving" | "stable" | "worsening";
  today_action: DailyAction | null;
  subsidy_matches: Subsidy[];
  total_potential_amount: number;
  loss_message: string;
  upcoming_events: any[];
  population_trend: {
    today: number;
    yesterday: number;
    change_percent: number;
  } | null;
  social_proof: string | null;
  coupon_stats: {
    total_created: number;
    total_scanned: number;
  };
  action_completion_rate: number;
}

// ===== 음성 =====
export interface VoiceQueryResponse {
  answer: string;
  intent: string;
  suggestions: string[];
}
