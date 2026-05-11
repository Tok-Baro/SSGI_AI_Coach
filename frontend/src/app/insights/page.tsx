"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

interface CompetitionData {
  sales_data: any;
  competition_data: any;
  population_data: any;
  sales_detail: {
    day_of_week: Record<string, number>;
    time_zone: Record<string, number>;
    gender: Record<string, number>;
    age_group: Record<string, number>;
    age_group_count?: Record<string, number>;
    weekday_vs_weekend: Record<string, number>;
    sample_count: number;
    data_scope?: "exact" | "dong_all_industry" | "seoul_industry";
    scope_note?: string;
  } | null;
  floating_population: {
    total: number;
    gender: Record<string, number>;
    age_group: Record<string, number>;
    time_zone: Record<string, number>;
    day_of_week: Record<string, number>;
  } | null;
  change_index: {
    dominant_status: string;
    status_distribution: Record<string, number>;
    change_index_code: string;
    avg_monthly_sales: number;
    sample_count: number;
  } | null;
  facilities: Record<string, number> | null;
  workplace_population: {
    total: number;
    gender: Record<string, number>;
    age_group: Record<string, number>;
  } | null;
  benchmark: {
    local_avg_ticket: number;
    seoul_avg_ticket: number;
    ticket_diff_pct: number;
    local_weekend_ratio: number;
    seoul_weekend_ratio: number;
    local_female_ratio: number;
    seoul_female_ratio: number;
    business_type: string;
  } | null;
  radius_summary: Record<string, number> | null;
  location_analysis: {
    work_resident_ratio?: { ratio: number; workplace: number; resident: number; profile: string };
    diversity_index?: { hhi: number; interpretation: string; total_businesses: number; dominant_category: string; dominant_share: number };
    anchor_score?: { score: number; grade: string; facilities: Record<string, number> };
    traffic_efficiency?: { sales_per_visitor: number; interpretation: string };
    time_concentration?: { peak_time: string; peak_share: number; interpretation: string };
    seoul_positioning?: { sales_diff_pct: number; position: string };
    lifecycle?: { stage: string; strategy: string };
  } | null;
  weather: {
    temperature: string;
    sky: string;
    precipitation: string;
    rain_probability: string;
    humidity?: string;
    insights: string[];
  } | null;
  nearby_competitors: { name: string; address: string; category: string; phone: string }[];
  business_name: string;
  business_type: string;
  location: string;
}

interface MarketingStrategy {
  title: string;
  description: string;
  evidence?: string;
  priority: "high" | "medium" | "low";
  category: string;
  expected_effect: string;
  budget?: string;
  timeline?: string;
}

interface UpliftOption {
  name: string;
  add_price_won: number;
  expected_attach_rate_pct: number;
  expected_avg_uplift_won: number;
  how: string;
  ease: "easy" | "medium" | "hard";
}

interface RevenueUpliftPlan {
  current_avg_ticket: number;
  target_avg_ticket: number;
  gap_per_order: number;
  monthly_orders_estimate: number;
  monthly_uplift_potential_won: number;
  rationale: string;
  uplift_options: UpliftOption[];
}

interface ReadyCopies {
  sms_to_regulars: string;
  store_pop: string;
  sns_caption: string;
  delivery_intro: string;
}

interface BudgetScenario {
  budget_label: string;
  budget_won: number;
  headline: string;
  actions: string[];
  expected_uplift_won: number;
  expected_orders: number;
}

interface ChannelScore {
  channel: string;
  label: string;
  fit_score: number;
  expected_roi_pct: number;
  rationale: string;
  first_step: string;
}

interface CopyVariant {
  tone_label: string;
  tone_desc: string;
  sms_to_regulars: string;
  store_pop: string;
  sns_caption: string;
  delivery_intro: string;
}

interface CopyVariants {
  trust?: CopyVariant;
  friendly?: CopyVariant;
  urgent?: CopyVariant;
}

interface MarketingData {
  strategy: {
    summary: string;
    strategies: MarketingStrategy[];
    weekly_plan: string;
    quick_win?: string;
    revenue_uplift_plan?: RevenueUpliftPlan;
    ready_to_use_copies?: ReadyCopies;
    budget_scenarios?: BudgetScenario[];
    channel_priority?: ChannelScore[];
    copy_variants?: CopyVariants;
  };
}


export default function InsightsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuth();
  const [comp, setComp] = useState<CompetitionData | null>(null);
  const [marketing, setMarketing] = useState<MarketingData | null>(null);
  const [compLoading, setCompLoading] = useState(true);
  const [marketingLoading, setMarketingLoading] = useState(false);
  const [marketingError, setMarketingError] = useState<string | null>(null);
  const [deepReport, setDeepReport] = useState<any>(null);
  const [deepLoading, setDeepLoading] = useState(false);
  const [deepError, setDeepError] = useState<string | null>(null);
  const [deepDetailOpen, setDeepDetailOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [tab, setTab] = useState<"competition" | "deep" | "marketing" | "menu">("competition");
  const [isPro, setIsPro] = useState(false);

  // 구독 상태 1회 로드
  useEffect(() => {
    if (isAuthenticated) {
      api.getSubscriptionStatus()
        .then((s) => setIsPro(s.is_pro))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    setPdfError(null);
    try {
      const blob = await api.downloadWeeklyReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `우리가게-진단서-${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : "PDF 만들기에 실패했어요. 잠시 뒤 다시 시도해 보세요.");
    } finally {
      setPdfLoading(false);
    }
  };

  // URL ?tab= 진입 시 초기 탭 동기화 (음성 라우팅 등)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const t = new URLSearchParams(window.location.search).get("tab");
    if (t === "deep" || t === "marketing" || t === "competition" || t === "menu") setTab(t);
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.push("/"); return; }
    if (!isLoading && isAuthenticated && user && !user.onboarding_completed) { router.push("/onboarding"); return; }
    if (isAuthenticated && user?.onboarding_completed) {
      api.getCompetitionAnalysis()
        .then(setComp)
        .catch(() => {})
        .finally(() => setCompLoading(false));
    }
  }, [isLoading, isAuthenticated, user, router]);

  const loadMarketing = async (refresh = false) => {
    if (!refresh && (marketing || marketingLoading)) return;
    setMarketingLoading(true);
    setMarketingError(null);
    try {
      const result = await api.getMarketingStrategy(refresh);
      setMarketing(result);
    } catch (e) {
      setMarketingError(e instanceof Error ? e.message : "마케팅 전략 로드 실패");
    } finally {
      setMarketingLoading(false);
    }
  };

  const loadDeepReport = async (refresh = false) => {
    if (!refresh && (deepReport || deepLoading)) return;
    setDeepLoading(true);
    setDeepError(null);
    try {
      const result = await api.getDeepReport(refresh);
      setDeepReport(result);
    } catch (e) {
      setDeepError(e instanceof Error ? e.message : "집중분석 리포트 로드 실패");
    } finally {
      setDeepLoading(false);
    }
  };

  useEffect(() => {
    if (tab === "marketing" && !marketing && !marketingLoading) loadMarketing();
    if (tab === "deep" && !deepReport && !deepLoading) loadDeepReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, marketing, deepReport]);

  if (isLoading || compLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  const priorityColor: Record<string, string> = { high: "bg-loss-100 text-loss-700", medium: "bg-warn-100 text-warn-900", low: "bg-success-100 text-success-700" };
  const priorityLabel: Record<string, string> = { high: "긴급", medium: "중요", low: "참고" };

  return (
    <main className="min-h-screen bg-gray-50 pb-24">
      <header className="bg-white px-5 py-5 sticky top-0 z-10">
        <div className="max-w-md mx-auto">
          <h1 className="text-display-sm text-gray-900">우리 가게 인사이트</h1>
          <p className="text-sm text-gray-500 mt-1">{comp?.business_name} · {comp?.location}</p>
        </div>
      </header>

      <div className="bg-white sticky top-[90px] z-10 border-b border-gray-100">
        <div className="max-w-md mx-auto flex">
          <button onClick={() => setTab("competition")} aria-current={tab === "competition" ? "page" : undefined}
            className={`flex-1 py-3.5 text-xs font-bold text-center border-b-2 transition-all ${tab === "competition" ? "border-gray-900 text-gray-900" : "border-transparent text-gray-400"}`}>
            경쟁
          </button>
          <button onClick={() => setTab("deep")} aria-current={tab === "deep" ? "page" : undefined}
            className={`flex-1 py-3.5 text-xs font-bold text-center border-b-2 transition-all ${tab === "deep" ? "border-gray-900 text-gray-900" : "border-transparent text-gray-400"}`}>
            집중분석
          </button>
          <button onClick={() => setTab("marketing")} aria-current={tab === "marketing" ? "page" : undefined}
            className={`flex-1 py-3.5 text-xs font-bold text-center border-b-2 transition-all ${tab === "marketing" ? "border-gray-900 text-gray-900" : "border-transparent text-gray-400"}`}>
            마케팅
          </button>
          <button onClick={() => setTab("menu")} aria-current={tab === "menu" ? "page" : undefined}
            className={`flex-1 py-3.5 text-xs font-bold text-center border-b-2 transition-all ${tab === "menu" ? "border-gray-900 text-gray-900" : "border-transparent text-gray-400"}`}>
            메뉴
          </button>
        </div>
      </div>

      <div className="max-w-md mx-auto px-5 py-5 space-y-3">
        {tab === "competition" && comp && (
          <>
            {/* 데이터 안내 — 페이지 최상단 한 번 */}
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-blue-900 mb-1">📊 어떤 데이터를 보여드리는지</p>
              <ul className="text-xs text-blue-800 space-y-0.5 leading-relaxed">
                <li>• <b>매출·점포 수·개폐업률</b>: <b>분기마다</b> 한 번 (서울시 상권분석)</li>
                <li>• <b>유동인구</b>: <b>매일</b> 갱신 (서울시 생활인구)</li>
                <li>• <b>객단가</b>: 분기 매출 ÷ 거래 건수 (한 명당 평균)</li>
                <li>• <b>매출 비중 %</b>: 분기 매출 전체를 100%로 봤을 때 비율</li>
              </ul>
            </div>

            {/* 경쟁 현황 요약 */}
            {comp.competition_data ? (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">경쟁 현황</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 단위</span>
                </div>
                <p className="text-xs text-gray-400 mb-3">
                  {comp.competition_data.area_name} · 출처: 서울시 VwsmTrdarStorQq
                </p>
                <div className="grid grid-cols-3 gap-3">
                  <StatCard label="상권 평균 점포 수" value={`${comp.competition_data.total_stores}개`} />
                  <StatCard label="분기 개업률" value={`${comp.competition_data.opening_rate}%`} color={comp.competition_data.opening_rate > 5 ? "red" : "green"} />
                  <StatCard label="분기 폐업률" value={`${comp.competition_data.closing_rate}%`} color={comp.competition_data.closing_rate > 5 ? "red" : "yellow"} />
                </div>
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600">
                    {comp.competition_data.net_change > 0
                      ? `이번 분기 ${comp.competition_data.net_change}%p 늘었어요 (개업이 폐업보다 많음) — 경쟁이 더 치열해지는 중. 차별화가 필요해요.`
                      : comp.competition_data.net_change < 0
                        ? `이번 분기 ${Math.abs(comp.competition_data.net_change)}%p 줄었어요 (폐업이 개업보다 많음) — 시장이 축소 중. 단골 잡는 데 집중하세요.`
                        : "이번 분기는 개업과 폐업이 비슷해요."}
                  </p>
                </div>
              </div>
            ) : (
              <GrayCard title="경쟁 현황" message="서울 외 지역은 아직 개폐업 데이터가 없어요" />
            )}

            {/* 서울 평균 대비 벤치마킹 */}
            {comp.benchmark && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">서울 평균 대비 분석</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 단위</span>
                </div>
                <p className="text-xs text-gray-400 mb-3">
                  {comp.benchmark.business_type} 기준 · 우리 동네 vs 서울 전체 평균 비교
                </p>
                <div className="space-y-3">
                  <BenchmarkRow
                    label="1건당 평균 객단가 (분기)"
                    local={comp.benchmark.local_avg_ticket}
                    seoul={comp.benchmark.seoul_avg_ticket}
                    diff={comp.benchmark.ticket_diff_pct}
                    format="money"
                  />
                  <BenchmarkRow
                    label="주말 매출 비중 (분기)"
                    local={comp.benchmark.local_weekend_ratio}
                    seoul={comp.benchmark.seoul_weekend_ratio}
                    diff={comp.benchmark.local_weekend_ratio - comp.benchmark.seoul_weekend_ratio}
                    format="pct"
                  />
                  <BenchmarkRow
                    label="여성 고객 매출 비중 (분기)"
                    local={comp.benchmark.local_female_ratio}
                    seoul={comp.benchmark.seoul_female_ratio}
                    diff={comp.benchmark.local_female_ratio - comp.benchmark.seoul_female_ratio}
                    format="pct"
                  />
                </div>
                <p className="text-[10px] text-gray-400 mt-3 italic">
                  ※ 객단가 = 분기 총매출 ÷ 거래건수. 1번 결제할 때 평균 얼마인지를 의미합니다.
                </p>
              </div>
            )}

            {/* 반경 500m 업종 분포 */}
            {comp.radius_summary && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">반경 500m 업종 분포</h3>
                <div className="grid grid-cols-4 gap-2">
                  {Object.entries(comp.radius_summary)
                    .sort(([, a]: [string, any], [, b]: [string, any]) => b - a)
                    .map(([name, count]: [string, any]) => (
                      <div key={name} className="bg-gray-50 rounded-lg p-2 text-center">
                        <p className="text-lg font-bold text-gray-900">{count}</p>
                        <p className="text-[10px] text-gray-500">{name}</p>
                      </div>
                    ))}
                </div>
                <p className="mt-2 text-xs text-loss-500 font-medium">
                  반경 500m 내 총 {Object.values(comp.radius_summary).reduce((a: number, b: any) => a + b, 0)}개 업체와 경쟁 중
                </p>
              </div>
            )}

            {/* 요일별 매출 */}
            {comp.sales_detail?.day_of_week && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">요일별 매출 패턴</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 매출 비중</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  분기 동안 발생한 매출을 요일별로 나눈 비율 (월~일 합계 = 100%)
                </p>
                {comp.sales_detail.data_scope && comp.sales_detail.data_scope !== "exact" && (
                  <div className="mb-2 px-2 py-1.5 bg-warn-50 border border-warn-200 rounded text-xs text-warn-900">
                    ⚠️ {comp.sales_detail.scope_note || "사장님 업종 데이터가 부족해 다른 범위로 대체됐어요"}.
                    사장님 가게 실제 패턴과 다를 수 있어요.
                  </div>
                )}
                <BarChart data={comp.sales_detail.day_of_week} unit="%" />
                <p className="mt-2 text-xs text-gray-400">
                  ※ {comp.sales_detail.sample_count}개 상권 분기 평균 · {comp.sales_detail.scope_note || comp.location} · 사장님 가게 매출 아님
                </p>
              </div>
            )}

            {/* 시간대별 매출 */}
            {comp.sales_detail?.time_zone && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">시간대별 매출 패턴</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 매출 비중</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  하루 6개 시간대 중 어디서 매출이 가장 많이 발생하는지 비율 (분기 합계 = 100%)
                </p>
                <BarChart data={comp.sales_detail.time_zone} unit="%" />
                <PeakInsight data={comp.sales_detail.time_zone} type="시간대" />
              </div>
            )}

            {/* 고객 분석 */}
            {comp.sales_detail && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">고객 분석</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 매출 비중</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  분기 동안 매장에서 발생한 매출을 성별·연령·주중주말로 나눈 비율
                </p>

                {/* 성별 비교 */}
                <GenderCompare gender={comp.sales_detail.gender} />

                {/* 주중 vs 주말 */}
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">주중 vs 주말 매출 비중 (분기)</p>
                  <WeekdayCompare data={comp.sales_detail.weekday_vs_weekend} />
                </div>

                {/* 연령대별 매출 */}
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">연령대별 매출 비중 (분기, 합계 100%)</p>
                  <BarChart data={comp.sales_detail.age_group} unit="%" />
                  <PeakInsight data={comp.sales_detail.age_group} type="연령대" />
                </div>

                {/* 연령대별 건수 */}
                {comp.sales_detail.age_group_count && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">연령대별 이용 건수 비중 (분기, 합계 100%)</p>
                    <BarChart data={comp.sales_detail.age_group_count} unit="%" />
                    <PeakInsight data={comp.sales_detail.age_group_count} type="연령대" />
                  </div>
                )}
              </div>
            )}

            {/* 상권변화지표 (서울시 공식 알고리즘) */}
            {comp.change_index && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900">상권변화 판정</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-400">서울시 공식</span>
                </div>
                <div className="flex items-center gap-3 mb-2">
                  <span className={`text-xl font-bold ${
                    comp.change_index.dominant_status === "상권확장" ? "text-success-600" :
                    comp.change_index.dominant_status === "다이나믹" ? "text-blue-600" :
                    comp.change_index.dominant_status === "정체" ? "text-warn-600" : "text-loss-500"
                  }`}>
                    {comp.change_index.dominant_status}
                  </span>
                  <span className="text-xs text-gray-400">{comp.change_index.sample_count}개 상권</span>
                </div>
                <p className="text-xs text-gray-600 mb-3 leading-relaxed">
                  {comp.change_index.dominant_status === "상권확장"
                    ? "새로 들어오기 좋은 성장 상권이에요. 영업기간이 짧고 시장이 커지는 중."
                    : comp.change_index.dominant_status === "다이나믹"
                      ? "들고남이 잦은 역동적인 상권이에요. 도시재생·개발지로 기회와 위험이 같이 와요."
                      : comp.change_index.dominant_status === "정체"
                        ? "이미 포화된 정체 상권이에요. 들어가려면 차별화가 필수예요."
                        : "기존 가게들이 강한 축소 상권이에요. 신규 진입 실패율이 높아 조심하세요."}
                </p>
                {comp.change_index.status_distribution && (
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(comp.change_index.status_distribution).map(([status, count]: [string, any]) => (
                      <span key={status} className={`text-xs px-2 py-1 rounded-full ${
                        status === "상권확장" ? "bg-success-100 text-success-700" :
                        status === "다이나믹" ? "bg-blue-100 text-blue-700" :
                        status === "정체" ? "bg-warn-100 text-warn-900" :
                        "bg-loss-100 text-loss-700"
                      }`}>
                        {status} {count}곳
                      </span>
                    ))}
                  </div>
                )}
                {comp.change_index.avg_monthly_sales > 0 && (
                  <p className="text-xs text-gray-400 mt-2">
                    상권 1곳당 월평균 매출 (분기 평균): {comp.change_index.avg_monthly_sales.toLocaleString()}만원
                  </p>
                )}
                <p className="text-[10px] text-gray-400 mt-2 italic">
                  ※ 출처: 서울시 VwsmTrdarIxQq · 분기 1회 갱신
                </p>
              </div>
            )}

            {/* 집객시설 */}
            {comp.facilities && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-1">주변 집객시설</h3>
                <p className="text-xs text-gray-500 mb-3">
                  같은 상권 내 평균 시설 수 (관공서·은행·병원·대중교통 등)
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(comp.facilities)
                    .filter(([k, v]: [string, any]) => k !== "sample_count" && v > 0)
                    .map(([name, count]: [string, any]) => (
                      <div key={name} className="bg-gray-50 rounded-lg p-2 text-center">
                        <p className="text-sm font-bold text-gray-900">{count}</p>
                        <p className="text-[10px] text-gray-500">{name}</p>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* 직장인구 */}
            {comp.workplace_population && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">직장인구</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 평균</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">상권 내 출근하는 직장인 평균 인원 (점심 매출 잠재력 지표)</p>
                <p className="text-2xl font-bold text-gray-900 mb-2">{comp.workplace_population.total?.toLocaleString()}명</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-blue-500">남성</p>
                    <p className="text-sm font-bold text-blue-700">{comp.workplace_population.gender?.["남성"]?.toLocaleString()}</p>
                  </div>
                  <div className="bg-pink-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-pink-500">여성</p>
                    <p className="text-sm font-bold text-pink-700">{comp.workplace_population.gender?.["여성"]?.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 상권 유동인구 */}
            {comp.floating_population && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <div className="flex items-baseline justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">상권 유동인구</h3>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">분기 일평균</span>
                </div>
                <p className="text-xs text-gray-500 mb-3">분기 동안 상권을 지나간 평균 인원 (하루 기준)</p>
                <p className="text-2xl font-bold text-gray-900 mb-3">{comp.floating_population.total?.toLocaleString()}명</p>
                {comp.floating_population.time_zone && (
                  <>
                    <p className="text-xs text-gray-500 mb-2">시간대별 유동인구 (분기 일평균)</p>
                    <BarChart data={comp.floating_population.time_zone} unit="명" />
                    <PeakInsight data={comp.floating_population.time_zone} type="시간대" />
                  </>
                )}
              </div>
            )}

            {/* 날씨 */}
            {comp.weather && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">오늘 날씨</h3>
                <div className="flex items-center gap-4 mb-2">
                  <span className="text-2xl font-bold text-gray-900">{comp.weather.temperature}</span>
                  <span className="text-sm text-gray-500">{comp.weather.sky}</span>
                  <span className="text-sm text-blue-500">강수 {comp.weather.rain_probability}</span>
                </div>
                {comp.weather.insights?.map((ins: string, i: number) => (
                  <p key={i} className="text-xs text-warn-900 bg-warn-50 rounded-lg p-2 mt-1">{ins}</p>
                ))}
              </div>
            )}

            {/* 주변 경쟁가게 */}
            {comp.nearby_competitors && comp.nearby_competitors.length > 0 && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">
                  주변 경쟁가게 ({comp.nearby_competitors.length}곳)
                </h3>
                <div className="space-y-2">
                  {comp.nearby_competitors.map((c, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-sm text-gray-900">{c.name}</p>
                      <p className="text-xs text-gray-500">{c.address}</p>
                      <p className="text-xs text-gray-400">{c.category}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-xs text-loss-500 font-medium">
                  주변 {comp.nearby_competitors.length}곳과 경쟁 중이에요. 우리만의 차별점이 필요해요.
                </p>
              </div>
            )}

            {/* 유동인구 */}
            {comp.population_data ? (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">유동인구</h3>
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-bold ${comp.population_data.change_percent > 0 ? "text-success-600" : "text-loss-500"}`}>
                    {comp.population_data.change_percent > 0 ? "+" : ""}{comp.population_data.change_percent}%
                  </span>
                  <span className="text-sm text-gray-500">전일 대비</span>
                </div>
              </div>
            ) : (
              <GrayCard title="유동인구" message="서울 외 지역은 아직 유동인구 데이터가 없어요" />
            )}
          </>
        )}

        {tab === "marketing" && (
          <>
            {marketingLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-warn-500 mb-4" />
                <p className="text-sm text-gray-500">AI가 우리 가게 마케팅 전략을 만들고 있어요...</p>
                <p className="text-xs text-gray-400 mt-1">사장님 가게 자료로 분석 중 · 30초까지 걸려요</p>
              </div>
            ) : marketingError ? (
              <div className="bg-loss-50 border border-loss-100 rounded-xl p-6 text-center">
                <p className="text-sm text-loss-600 font-semibold mb-2">마케팅 전략을 불러오지 못했습니다</p>
                <p className="text-xs text-loss-500 mb-3">{marketingError}</p>
                <button onClick={() => loadMarketing(true)}
                  className="px-4 py-2 bg-warn-500 text-gray-900 text-sm font-semibold rounded-lg">
                  다시 시도
                </button>
              </div>
            ) : marketing ? (
              <>
                {/* 데이터 단위 안내 — 마케팅 탭 최상단 */}
                <div className="bg-blue-50 border border-blue-100 rounded-xl p-3">
                  <p className="text-xs font-semibold text-blue-900 mb-1">📊 이 페이지의 수치 안내</p>
                  <ul className="text-xs text-blue-800 space-y-0.5 leading-relaxed">
                    <li>• <b>예상 추가 매출/주문</b>: <b>월 단위</b> 추정 (AI 산출, 공식 미적용)</li>
                    <li>• <b>객단가</b>: 분기 총매출 ÷ 거래건수 (1건당 평균)</li>
                    <li>• <b>매출 갭</b>: 우리 가게 vs 서울 평균 (분기 단위)</li>
                    <li>• <b>fit_score, ROI%</b>: AI 추정치 — 실제 캠페인 결과로 검증 필요</li>
                  </ul>
                </div>
                <div className="bg-warn-50 border border-warn-100 rounded-xl p-4">
                  <p className="text-xs text-warn-900 font-medium mb-1">📰 마케팅 진단 한 줄</p>
                  <p className="text-sm font-semibold text-warn-900">{marketing.strategy.summary}</p>
                </div>
                {marketing.strategy.quick_win && (
                  <div className="bg-success-50 border border-success-100 rounded-xl p-4">
                    <p className="text-xs text-success-600 font-medium mb-1">⚡ 오늘 당장 (30분 내) 할 수 있는 것</p>
                    <p className="text-sm text-success-700 font-semibold">{marketing.strategy.quick_win}</p>
                  </div>
                )}

                {marketing.strategy.budget_scenarios && marketing.strategy.budget_scenarios.length > 0 && (
                  <BudgetScenariosCard scenarios={marketing.strategy.budget_scenarios} />
                )}

                {marketing.strategy.channel_priority && marketing.strategy.channel_priority.length > 0 && (
                  <ChannelPriorityCard channels={marketing.strategy.channel_priority} />
                )}

                {marketing.strategy.revenue_uplift_plan && (
                  <UpliftCard plan={marketing.strategy.revenue_uplift_plan} />
                )}

                {marketing.strategy.copy_variants ? (
                  <CopyVariantsCard variants={marketing.strategy.copy_variants} />
                ) : marketing.strategy.ready_to_use_copies ? (
                  <CopiesCard copies={marketing.strategy.ready_to_use_copies} />
                ) : null}
                <div className="space-y-3">
                  {marketing.strategy.strategies?.map((s, i) => (
                    <div key={i} className="bg-white rounded-xl p-4 border border-gray-100">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${priorityColor[s.priority] || "bg-gray-100 text-gray-600"}`}>
                          {priorityLabel[s.priority] || s.priority}
                        </span>
                        <span className="text-xs text-gray-400">{s.category}</span>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">{s.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{s.description}</p>
                      {s.evidence && (
                        <div className="flex items-start gap-1.5 mb-2 p-2 bg-blue-50 rounded-md">
                          <span className="text-[10px] font-bold text-blue-600 mt-0.5 shrink-0">근거</span>
                          <span className="text-xs text-blue-700 leading-relaxed">{s.evidence}</span>
                        </div>
                      )}
                      <p className="text-xs text-success-600 font-medium">{s.expected_effect}</p>
                      {(s.budget || s.timeline) && (
                        <div className="flex gap-3 mt-1">
                          {s.budget && <span className="text-xs text-gray-400">비용: {s.budget}</span>}
                          {s.timeline && <span className="text-xs text-gray-400">기간: {s.timeline}</span>}
                        </div>
                      )}
                      {(s.category === "offline" || s.category === "event") && (
                        <button onClick={() => router.push("/coupons")}
                          className="mt-3 w-full py-2 bg-warn-500 text-gray-900 text-sm font-semibold rounded-lg hover:bg-warn-600 transition-colors">
                          쿠폰으로 실행하기
                        </button>
                      )}
                      {s.category === "subsidy" && (
                        <button onClick={() => router.push("/subsidies")}
                          className="mt-3 w-full py-2 bg-warn-500 text-gray-900 text-sm font-semibold rounded-lg hover:bg-warn-600 transition-colors">
                          지원사업 확인하기
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                {marketing.strategy.weekly_plan && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">이번 주 실행 계획</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{marketing.strategy.weekly_plan}</p>
                  </div>
                )}
                <button onClick={() => { setMarketing(null); loadMarketing(true); }}
                  className="w-full py-2 text-sm text-gray-400 hover:text-gray-600">
                  전략 다시 분석하기
                </button>
              </>
            ) : (
              <p className="text-center text-gray-400 py-8">마케팅 전략을 불러오지 못했습니다</p>
            )}
          </>
        )}

        {tab === "menu" && (
          <>
            <div className="bg-white rounded-xl border border-gray-100 p-4 mb-3">
              <div className="flex items-center justify-between gap-2 mb-1">
                <h2 className="text-base font-bold text-gray-900">메뉴 전략</h2>
                {!isPro && (
                  <span className="text-[10px] px-2 py-0.5 bg-warn-100 text-warn-800 rounded font-bold uppercase">
                    Pro 전용
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500">사장님 가게에 맞는 메뉴 갭·시즌·차별화 — AI 분석</p>
            </div>
            {!isPro && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 mb-3 text-center">
                <p className="text-sm font-bold text-amber-900 mb-1">메뉴 전략은 Pro 전용이에요</p>
                <p className="text-xs text-amber-800 mb-4">월 9,900원으로 갭 분석·시즌 캘린더·차별화 메뉴 받기</p>
                <button
                  onClick={() => router.push("/upgrade")}
                  className="press-effect px-6 py-2.5 bg-warn-500 text-gray-900 font-bold text-sm rounded-xl"
                >
                  Pro 보러가기 →
                </button>
              </div>
            )}
            {isPro && <MenuStrategyCard />}
          </>
        )}

        {tab === "deep" && (
          <>
            {deepLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-warn-500 mb-4" />
                <p className="text-sm text-gray-500">AI가 우리 가게 진단서를 쓰고 있어요...</p>
                <p className="text-xs text-gray-400 mt-1">서울시 빅데이터 + 상권 분석 + 경쟁사 데이터 종합 중 · 최대 60초 소요</p>
              </div>
            ) : deepError ? (
              <div className="bg-loss-50 border border-loss-100 rounded-xl p-6 text-center">
                <p className="text-sm text-loss-600 font-semibold mb-2">집중분석 리포트를 불러오지 못했습니다</p>
                <p className="text-xs text-loss-500 mb-3">{deepError}</p>
                <button onClick={() => loadDeepReport(true)}
                  className="px-4 py-2 bg-warn-500 text-gray-900 text-sm font-semibold rounded-lg">
                  다시 시도
                </button>
              </div>
            ) : deepReport ? (
              <>
                {/* HERO 1 — 종합 진단 (그라디언트 배경) — string/dict 양쪽 다 처리 */}
                {(() => {
                  const es = deepReport.report.executive_summary;
                  const isDict = es && typeof es === "object";
                  const currentText = isDict ? safeText(es.current) : safeText(es);
                  const recoText = isDict ? safeText(es.recommendation) : "";
                  const riskText = isDict ? safeText(es.risk) : "";
                  return (
                    <div className="rounded-2xl p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white shadow-card">
                      <p className="text-xs font-bold text-warn-500 uppercase tracking-wider mb-3">
                        AI 종합 진단
                      </p>
                      <h2 className="text-xl font-bold leading-snug text-balance mb-3">
                        {firstSentence(currentText, 130) || "사장님 가게 자료를 살펴보고 있어요."}
                      </h2>
                      {currentText.length > 130 && (
                        <p className="text-sm text-gray-300 leading-relaxed mb-3">
                          {currentText}
                        </p>
                      )}
                      {riskText && (
                        <div className="mt-3 pt-3 border-t border-white/15">
                          <p className="text-xs text-loss-500 font-bold mb-1">⚠ 핵심 위험</p>
                          <p className="text-sm text-gray-200 leading-relaxed">
                            {firstSentence(riskText, 110)}
                          </p>
                        </div>
                      )}
                      {recoText && (
                        <div className="mt-3 pt-3 border-t border-white/15">
                          <p className="text-xs text-warn-500 font-bold mb-1">→ 추천 한 수</p>
                          <p className="text-sm text-gray-200 leading-relaxed">
                            {firstSentence(recoText, 110)}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* HERO 2 — 강점·약점 한 줄씩 */}
                {deepReport.report.swot && (
                  (deepReport.report.swot.strengths?.length || deepReport.report.swot.weaknesses?.length) && (
                    <div className="bg-white rounded-2xl p-5 shadow-card">
                      <p className="text-xs font-semibold text-gray-500 mb-3">우리 가게 핵심 강점·약점</p>
                      <div className="space-y-3">
                        {deepReport.report.swot.strengths?.[0] && (
                          <div className="flex gap-3">
                            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-success-50 flex items-center justify-center text-success-600 font-bold">
                              ✓
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-bold text-success-700 mb-0.5">강점</p>
                              <p className="text-sm font-semibold text-gray-900 leading-relaxed">
                                {firstSentence(safeText(deepReport.report.swot.strengths[0]), 90)}
                              </p>
                            </div>
                          </div>
                        )}
                        {deepReport.report.swot.weaknesses?.[0] && (
                          <div className="flex gap-3">
                            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-loss-50 flex items-center justify-center text-loss-600 font-bold">
                              !
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-bold text-loss-600 mb-0.5">약점</p>
                              <p className="text-sm font-semibold text-gray-900 leading-relaxed">
                                {firstSentence(safeText(deepReport.report.swot.weaknesses[0]), 90)}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                )}

                {/* HERO 3 — 우리 가게 자리 (포지셔닝/입지) */}
                {(deepReport.report.positioning_map?.interpretation || deepReport.report.location_analysis) && (
                  <div className="bg-white rounded-2xl p-5 shadow-card">
                    <p className="text-xs font-semibold text-gray-500 mb-2">우리 가게 자리</p>
                    <p className="text-base font-bold text-gray-900 leading-relaxed text-balance">
                      {firstSentence(
                        safeText(deepReport.report.positioning_map?.interpretation)
                          || safeText(deepReport.report.location_analysis),
                        110
                      )}
                    </p>
                  </div>
                )}

                {/* HERO 4 — 가장 시급한 위험 */}
                {deepReport.report.risk_alert && (
                  <div className="bg-loss-50 rounded-2xl p-5 shadow-card">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-loss-600 text-base">⚠</span>
                      <p className="text-xs font-bold text-loss-600 uppercase tracking-wider">
                        지금 가장 시급한 신호
                      </p>
                    </div>
                    <p className="text-base font-bold text-gray-900 leading-relaxed text-balance">
                      {safeText(deepReport.report.risk_alert)}
                    </p>
                  </div>
                )}

                {/* HERO 5 — 이번 주 1가지 액션 */}
                {deepReport.report.action_items?.[0] && (
                  <div className="bg-white rounded-2xl p-5 shadow-card border-l-4 border-warn-500">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="px-2.5 py-1 text-xs font-bold bg-warn-500 text-gray-900 rounded-lg">
                        이번 주 1가지
                      </span>
                      {deepReport.report.action_items[0].timeline && (
                        <span className="text-xs text-gray-500">
                          {safeText(deepReport.report.action_items[0].timeline)}
                        </span>
                      )}
                    </div>
                    <p className="text-base font-bold text-gray-900 mb-2 text-balance leading-snug">
                      {safeText(deepReport.report.action_items[0].action)}
                    </p>
                    {deepReport.report.action_items[0].expected_impact && (
                      <p className="text-sm text-gray-600 leading-relaxed">
                        예상 효과 · {safeText(deepReport.report.action_items[0].expected_impact)}
                      </p>
                    )}
                  </div>
                )}

                {/* HERO 6 — 우리 가게 단골은 누구? (요약) */}
                {deepReport.report.customer_insight && (
                  <div className="bg-white rounded-2xl p-5 shadow-card">
                    <p className="text-xs font-semibold text-gray-500 mb-2">우리 가게 단골은 어떤 분일까요?</p>
                    <p className="text-base font-bold text-gray-900 leading-relaxed text-balance">
                      {firstSentence(safeText(deepReport.report.customer_insight), 110)}
                    </p>
                  </div>
                )}

                {/* PDF 받기 CTA — Free 월 1회 한도 / Pro 무제한 */}
                <div className="rounded-2xl p-5 bg-gradient-to-br from-gray-900 to-gray-800 text-white shadow-card">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-warn-500 uppercase tracking-wider">
                      Premium Report
                    </p>
                    {!isPro && (
                      <span className="text-[10px] px-2 py-0.5 bg-white/15 text-white rounded font-bold">
                        Free · 월 1회
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-bold mb-1">자세한 진단서 한 장으로 받기</h3>
                  <p className="text-sm text-gray-300 leading-relaxed mb-4">
                    SWOT·경쟁·고객층·시간 전략·12가지 액션까지 PDF 한 장에 담아 드릴게요.
                  </p>
                  {pdfError && (
                    <p className="text-sm font-medium text-loss-500 mb-3">{pdfError}</p>
                  )}
                  <button
                    onClick={handleDownloadPdf}
                    disabled={pdfLoading}
                    className="press-effect w-full py-3 bg-white text-gray-900 font-bold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {pdfLoading ? "리포트 만드는 중..." : "PDF로 받기"}
                  </button>
                  {!isPro && (
                    <button
                      onClick={() => router.push("/upgrade")}
                      className="press-effect w-full mt-2 py-2 text-xs text-white/70 hover:text-white"
                    >
                      Pro로 무제한 받기 →
                    </button>
                  )}
                </div>

                {/* 지난 진단 대비 변화 — Hero 옆에 작게 */}
                {deepReport.previous && (
                  <PreviousDiffCard
                    previous={deepReport.previous}
                    currentRisk={safeText(deepReport.report.risk_alert)}
                  />
                )}

                {/* 더 자세히 보기 토글 */}
                <button
                  onClick={() => setDeepDetailOpen(!deepDetailOpen)}
                  className="press-effect w-full py-4 bg-white rounded-2xl shadow-card flex items-center justify-center gap-2 font-semibold text-gray-700"
                >
                  {deepDetailOpen ? "자세한 분석 접기 ▲" : "더 자세한 분석 보기 ▼"}
                </button>

                {deepDetailOpen && (
                  <>
                    {/* 경영 진단 요약 (3-section: 현황/위험/권고) */}
                    <ExecutiveSummaryCard summary={deepReport.report.executive_summary} />

                    {/* 상권 입지 분석 */}
                    {deepReport.report.location_analysis && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-2">우리 가게 자리 분석</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{safeText(deepReport.report.location_analysis)}</p>
                      </div>
                    )}

                    {/* SWOT */}
                    {deepReport.report.swot && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-3">강점·약점 한눈에</h3>
                        <div className="grid grid-cols-2 gap-2">
                          <SwotCard title="강점" items={deepReport.report.swot.strengths} color="green" />
                          <SwotCard title="약점" items={deepReport.report.swot.weaknesses} color="red" />
                          <SwotCard title="기회" items={deepReport.report.swot.opportunities} color="blue" />
                          <SwotCard title="위협" items={deepReport.report.swot.threats} color="yellow" />
                        </div>
                      </div>
                    )}

                    {deepReport.report.tows_matrix && (
                      <TowsMatrixCard tows={deepReport.report.tows_matrix} />
                    )}

                    {deepReport.report.positioning_map && (
                      <PositioningMapCard map={deepReport.report.positioning_map} />
                    )}

                    {deepReport.report.customer_insight && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-2">우리 가게 단골은 어떤 분일까요?</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{safeText(deepReport.report.customer_insight)}</p>
                      </div>
                    )}

                    {deepReport.report.time_strategy && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-2">언제 손님이 가장 많을까요?</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{safeText(deepReport.report.time_strategy)}</p>
                      </div>
                    )}

                    {deepReport.report.competition_analysis && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-2">옆 가게와 비교하면</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{safeText(deepReport.report.competition_analysis)}</p>
                      </div>
                    )}

                    {deepReport.report.trend_analysis && (
                      <div className="bg-white rounded-2xl p-5 shadow-card">
                        <h3 className="font-bold text-gray-900 mb-2">업종 흐름은 어떻게 가고 있을까요?</h3>
                        <p className="text-sm text-gray-700 leading-relaxed">{safeText(deepReport.report.trend_analysis)}</p>
                      </div>
                    )}

                    {deepReport.report.action_items?.length > 0 && (
                      <ActionImpactMatrix items={deepReport.report.action_items} />
                    )}

                    {deepReport.report.monthly_goal && (
                      <MonthlyGoalCard goal={deepReport.report.monthly_goal} />
                    )}

                    {/* 데이터 안내 — 펼치기 안에 */}
                    <div className="bg-blue-50 rounded-2xl p-4">
                      <p className="text-xs font-semibold text-blue-900 mb-1">📊 이 리포트가 본 자료</p>
                      <ul className="text-xs text-blue-800 space-y-0.5 leading-relaxed">
                        <li>• <b>매출·객단가·점포 수</b>: 분기마다 한 번 (서울시 상권분석)</li>
                        <li>• <b>유동인구</b>: 분기 하루 평균 (서울시 생활인구)</li>
                        <li>• <b>강점·약점·전략 권고</b>: AI 분석 (위 자료 위에서 작성)</li>
                        <li>• <b>포지셔닝 좌표·목표 수치</b>: AI 추정값 — 실데이터로 다시 점검 필요</li>
                        <li>• <b>액션 점수</b>: AI 추정 1~10점</li>
                      </ul>
                    </div>
                  </>
                )}

                <button onClick={() => { setDeepReport(null); setDeepDetailOpen(false); loadDeepReport(true); }}
                  className="w-full py-3 text-sm text-gray-400 hover:text-gray-600">
                  리포트 새로 만들기
                </button>
              </>
            ) : (
              <p className="text-center text-gray-400 py-8">리포트를 불러오지 못했어요</p>
            )}
          </>
        )}

      </div>

      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-5 py-2">
        <div className="flex justify-around max-w-md mx-auto">
          <NavItem icon="🏠" label="홈" active={pathname === "/dashboard"} onClick={() => router.push("/dashboard")} />
          <NavItem icon="💰" label="지원사업" active={pathname === "/subsidies"} onClick={() => router.push("/subsidies")} />
          <NavItem icon="📊" label="인사이트" active={pathname === "/insights"} onClick={() => router.push("/insights")} />
          <NavItem icon="🎟" label="쿠폰" active={pathname === "/coupons"} onClick={() => router.push("/coupons")} />
        </div>
      </nav>
    </main>
  );
}

// === 컴포넌트들 ===

// GPT가 문자열 대신 객체를 반환할 수 있으므로 안전하게 렌더링
function safeText(val: any): string {
  if (val === null || val === undefined) return "";
  if (typeof val === "string") return val;
  if (typeof val === "number") return String(val);
  if (typeof val === "object") {
    return Object.entries(val).map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`).join(" / ");
  }
  return String(val);
}

/**
 * 한국어 첫 문장 추출 — 200자 단락 → hero용 한 줄 요약.
 * "다.", "요.", "?", "!" 등 종결 마커로 자르고, 못 찾으면 max 글자에서 ellipsis.
 */
function firstSentence(text: string, max = 100): string {
  if (!text) return "";
  const cleaned = text.trim();
  const markers = ["다. ", "요. ", "죠. ", "에요. ", "예요. ", "다.\n", "요.\n", ". ", "! ", "? "];
  let best = -1;
  for (const m of markers) {
    const i = cleaned.indexOf(m);
    if (i > 8 && (best === -1 || i < best)) best = i + m.length - 1;
  }
  if (best === -1) {
    return cleaned.length > max ? cleaned.slice(0, max).trim() + "…" : cleaned;
  }
  const out = cleaned.slice(0, best + 1).trim();
  return out.length > max ? out.slice(0, max) + "…" : out;
}

const DAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"];
const TIME_ORDER = ["00~06", "06~11", "11~14", "14~17", "17~21", "21~24"];
const AGE_ORDER = ["10대", "20대", "30대", "40대", "50대", "60대+"];

function BarChart({ data, unit }: { data: Record<string, number>; unit?: string }) {
  // 키 순서 보장
  const keys = Object.keys(data);
  let orderedKeys = keys;
  if (keys.includes("월")) orderedKeys = DAY_ORDER.filter(k => k in data);
  else if (keys.includes("00~06")) orderedKeys = TIME_ORDER.filter(k => k in data);
  else if (keys.includes("10대")) orderedKeys = AGE_ORDER.filter(k => k in data);

  const entries = orderedKeys.map(k => [k, data[k]] as [string, number]);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  const formatNum = (n: number) => {
    if (unit === "%") return `${n}%`;
    if (n >= 100000000) return `${(n / 100000000).toFixed(1)}억`;
    if (n >= 10000) return `${(n / 10000).toFixed(0)}만`;
    return n.toLocaleString();
  };
  return (
    <div className="space-y-2">
      {entries.map(([label, value]) => (
        <div key={label} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-12 text-right shrink-0">{label}</span>
          <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-warn-500 rounded-full transition-all duration-500"
              style={{ width: `${(value / max) * 100}%` }}
            />
          </div>
          <span className="text-xs text-gray-600 w-14 text-right shrink-0">{formatNum(value)}</span>
        </div>
      ))}
    </div>
  );
}


function PeakInsight({ data, type }: { data: Record<string, number>; type: string }) {
  const peak = Object.entries(data).sort((a, b) => b[1] - a[1])[0];
  if (!peak) return null;
  return (
    <p className="mt-2 text-xs text-loss-500 font-medium">
      {type} 중 {peak[0]}에 매출이 가장 높습니다. 이 시간대 마케팅에 집중하세요.
    </p>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  const colorMap: Record<string, string> = { red: "text-loss-500", yellow: "text-warn-600", green: "text-success-600" };
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className={`text-lg font-bold ${colorMap[color || ""] || "text-gray-900"}`}>{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function GenderCompare({ gender }: { gender: Record<string, number> }) {
  // 서울 API 원본값 — '미상/기타' 제외라 합이 100% 미만일 수 있음
  const mRaw = gender["남성_비중"] || gender["남성_매출"] || 0;
  const fRaw = gender["여성_비중"] || gender["여성_매출"] || 0;
  const mCountRaw = gender["남성_건수비중"] || gender["남성_건수"] || 0;
  const fCountRaw = gender["여성_건수비중"] || gender["여성_건수"] || 0;
  // 남녀만 비교 → 합 100% 되도록 정규화
  const totalSales = mRaw + fRaw || 1;
  const mPct = Math.round((mRaw / totalSales) * 1000) / 10;
  const fPct = Math.round(1000 - mPct * 10) / 10;
  const totalCount = mCountRaw + fCountRaw || 1;
  const mCountPct = Math.round((mCountRaw / totalCount) * 1000) / 10;
  const fCountPct = Math.round(1000 - mCountPct * 10) / 10;

  return (
    <div>
      <p className="text-xs text-gray-500 mb-2">성별 매출 비교 (남녀 합계 100% 기준)</p>
      <div className="flex h-8 rounded-full overflow-hidden mb-2">
        <div className="bg-blue-400 flex items-center justify-center text-xs font-medium text-white tabular-nums" style={{ width: `${mPct}%` }}>
          {mPct > 15 && `남 ${mPct}%`}
        </div>
        <div className="bg-pink-400 flex items-center justify-center text-xs font-medium text-white tabular-nums" style={{ width: `${fPct}%` }}>
          {fPct > 15 && `여 ${fPct}%`}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xs text-blue-500 mb-1">남성</p>
          <p className="text-sm font-bold text-blue-700 tabular-nums">매출 {mPct}%</p>
          <p className="text-xs text-blue-400 tabular-nums">건수 {mCountPct}%</p>
        </div>
        <div className="bg-pink-50 rounded-lg p-3 text-center">
          <p className="text-xs text-pink-500 mb-1">여성</p>
          <p className="text-sm font-bold text-pink-700 tabular-nums">매출 {fPct}%</p>
          <p className="text-xs text-pink-400 tabular-nums">건수 {fCountPct}%</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        {mPct > fPct
          ? `남성 고객 매출이 ${(mPct - fPct).toFixed(1)}%p 더 많아요. 여성 손님을 잡으면 매출이 더 늘어요.`
          : `여성 고객 매출이 ${(fPct - mPct).toFixed(1)}%p 더 많아요. 여성 손님 만족도를 잘 지켜보세요.`}
      </p>
      {Math.round(mRaw + fRaw) < 99 && (
        <p className="mt-1 text-[11px] text-gray-400">
          서울 API 원본 비중 합 {(mRaw + fRaw).toFixed(1)}% (미상·기타 제외) — 남녀 비교용으로 정규화함
        </p>
      )}
    </div>
  );
}

function WeekdayCompare({ data }: { data: Record<string, number> }) {
  const weekday = data["주중"] || 0;
  const weekend = data["주말"] || 0;

  return (
    <div className="flex gap-3">
      <div className="flex-1 bg-gray-50 rounded-lg p-3 text-center">
        <p className="text-xs text-gray-500">주중 (월~금)</p>
        <p className="text-lg font-bold text-gray-900">{weekday}%</p>
      </div>
      <div className="flex-1 bg-warn-50 rounded-lg p-3 text-center">
        <p className="text-xs text-warn-600">주말 (토~일)</p>
        <p className="text-lg font-bold text-warn-900">{weekend}%</p>
      </div>
    </div>
  );
}

function BenchmarkRow({ label, local, seoul, diff, format }: {
  label: string; local: number; seoul: number; diff: number; format: "money" | "pct";
}) {
  const fmt = (n: number) => {
    if (format === "pct") return `${n.toFixed(1)}%`;
    if (n >= 100000000) return `${(n / 100000000).toFixed(1)}억`;
    if (n >= 10000) return `${(n / 10000).toFixed(0)}만`;
    return n.toLocaleString();
  };
  const isPositive = diff > 0;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{label}</span>
        <span className={`font-medium ${isPositive ? "text-success-600" : "text-loss-500"}`}>
          {isPositive ? "+" : ""}{format === "pct" ? `${diff.toFixed(1)}%p` : `${diff.toFixed(1)}%`}
        </span>
      </div>
      <div className="flex gap-2 text-xs">
        <div className="flex-1 bg-warn-50 rounded p-1.5 text-center">
          <p className="text-[10px] text-gray-400">우리 지역</p>
          <p className="font-bold text-gray-900">{fmt(local)}</p>
        </div>
        <div className="flex-1 bg-gray-50 rounded p-1.5 text-center">
          <p className="text-[10px] text-gray-400">서울 평균</p>
          <p className="font-bold text-gray-500">{fmt(seoul)}</p>
        </div>
      </div>
    </div>
  );
}

function SwotCard({ title, items, color }: { title: string; items: string[]; color: string }) {
  const colorMap: Record<string, string> = {
    green: "bg-success-50 border-success-100", red: "bg-loss-50 border-loss-100",
    blue: "bg-blue-50 border-blue-200", yellow: "bg-warn-50 border-warn-100",
  };
  const textMap: Record<string, string> = {
    green: "text-success-700", red: "text-loss-700", blue: "text-blue-700", yellow: "text-warn-900",
  };
  return (
    <div className={`rounded-lg p-3 border ${colorMap[color] || "bg-gray-50 border-gray-200"}`}>
      <p className={`text-xs font-semibold mb-1.5 ${textMap[color] || "text-gray-700"}`}>{title}</p>
      <ul className="space-y-1">
        {(items || []).map((item, i) => (
          <li key={i} className="text-xs text-gray-600">· {item}</li>
        ))}
      </ul>
    </div>
  );
}

function GrayCard({ title, message }: { title: string; message: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <h3 className="font-semibold text-gray-400 mb-1">{title}</h3>
      <p className="text-xs text-gray-400">{message}</p>
    </div>
  );
}

function UpliftCard({ plan }: { plan: RevenueUpliftPlan }) {
  const won = (n: number) => n.toLocaleString() + "원";
  const easeBadge = { easy: "쉬움", medium: "보통", hard: "어려움" } as const;
  const easeColor = {
    easy: "bg-success-100 text-success-700",
    medium: "bg-warn-100 text-warn-900",
    hard: "bg-loss-50 text-loss-700",
  } as const;
  const pct = plan.target_avg_ticket > 0
    ? Math.min(100, Math.round((plan.current_avg_ticket / plan.target_avg_ticket) * 100))
    : 0;

  // 옵션 선택 → 30일 누적 매출 증분 미니 차트
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selected = plan.uplift_options[selectedIdx];
  const dailyOrders = plan.monthly_orders_estimate / 30;
  const dailyUplift = selected ? selected.expected_avg_uplift_won * dailyOrders : 0;
  const days = Array.from({ length: 30 }, (_, i) => i + 1);
  const points = days.map((d) => Math.round(dailyUplift * d));
  const peakUplift = points[points.length - 1] || 0;

  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">객단가 끌어올리기</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>

      {/* 게이지 */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>현재 {won(plan.current_avg_ticket)}</span>
          <span>목표 {won(plan.target_avg_ticket)}</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-warn-500 to-orange-400 rounded-full transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-loss-500 font-medium mt-1.5">
          1건당 {won(plan.gap_per_order)} 부족 · 월 {plan.monthly_orders_estimate.toLocaleString()}건 기준 잠재력 +{won(plan.monthly_uplift_potential_won)}/월
        </p>
      </div>

      <p className="text-xs text-gray-600 mb-3 bg-gray-50 rounded-lg p-2">{plan.rationale}</p>

      {/* 추천 옵션 3종 (선택 시 30일 차트 갱신) */}
      <p className="text-xs text-gray-500 font-medium mb-2">추천 옵션 (탭하면 30일 시뮬)</p>
      <div className="space-y-2">
        {plan.uplift_options.map((opt, i) => (
          <button
            key={i}
            onClick={() => setSelectedIdx(i)}
            className={`w-full text-left border rounded-lg p-3 transition-colors ${
              i === selectedIdx ? "border-warn-500 bg-warn-50" : "border-gray-100 hover:border-gray-200"
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-1">
              <p className="font-semibold text-gray-900 text-sm flex-1">{opt.name}</p>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${easeColor[opt.ease] || "bg-gray-100 text-gray-700"}`}>
                {easeBadge[opt.ease] || opt.ease}
              </span>
            </div>
            <div className="flex gap-3 text-xs text-gray-500 mb-2">
              <span>+{won(opt.add_price_won)}</span>
              <span>부착률 {opt.expected_attach_rate_pct}%</span>
              <span className="text-success-600 font-semibold">평균 +{won(opt.expected_avg_uplift_won)}</span>
            </div>
            <p className="text-xs text-gray-600">{opt.how}</p>
          </button>
        ))}
      </div>

      {/* 30일 누적 매출 증분 미니 차트 */}
      {selected && peakUplift > 0 && (
        <div className="mt-4 p-3 bg-gradient-to-br from-success-50 to-emerald-50 border border-success-100 rounded-lg">
          <div className="flex items-baseline justify-between mb-2">
            <p className="text-[11px] text-success-700 font-medium">
              &ldquo;{selected.name}&rdquo; 적용 시 30일 예상 누적
            </p>
            <p className="text-base font-extrabold text-success-700 tabular-nums">+{won(peakUplift)}</p>
          </div>
          <svg viewBox="0 0 300 60" className="w-full h-12">
            <polyline
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              points={points
                .map((v, i) => `${(i / 29) * 300},${60 - (v / peakUplift) * 55}`)
                .join(" ")}
            />
            <polygon
              fill="#10b98120"
              points={`0,60 ${points
                .map((v, i) => `${(i / 29) * 300},${60 - (v / peakUplift) * 55}`)
                .join(" ")} 300,60`}
            />
          </svg>
          <p className="text-[10px] text-success-600/80 mt-1">
            일 {Math.round(dailyOrders)}건 × {selected.expected_attach_rate_pct}% × {won(selected.add_price_won)} 가정
          </p>
        </div>
      )}
    </div>
  );
}

function BudgetScenariosCard({ scenarios }: { scenarios: BudgetScenario[] }) {
  const won = (n: number) => n.toLocaleString() + "원";
  const colorMap = ["bg-gray-50 border-gray-200", "bg-warn-50 border-warn-100", "bg-warn-50 border-warn-200"];
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">예산별 시나리오</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      <p className="text-xs text-gray-500 mb-1">현재 가용 예산에 맞춰 골라 실행하세요</p>
      <p className="text-[10px] text-amber-700 bg-amber-50 px-2 py-1 rounded mb-3">
        ⓘ 예상 추가 매출은 <span className="font-semibold">AI 추정치 (공식 미적용)</span>입니다. 실제 캠페인 결과로 검증하세요.
      </p>
      <div className="space-y-2">
        {scenarios.map((s, i) => (
          <div key={i} className={`rounded-lg p-3 border ${colorMap[i] || "bg-gray-50 border-gray-200"}`}>
            <div className="flex items-baseline justify-between mb-1">
              <p className="font-bold text-sm text-gray-900">{s.budget_label}</p>
              <p className="text-xs font-semibold text-success-600 tabular-nums">
                +{won(s.expected_uplift_won)}/월
              </p>
            </div>
            <p className="text-sm text-gray-800 font-medium mb-2">{s.headline}</p>
            <ul className="space-y-1 mb-2">
              {(s.actions || []).map((a, j) => (
                <li key={j} className="text-xs text-gray-600 flex gap-1.5">
                  <span className="text-gray-400 shrink-0">·</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
            <p className="text-[10px] text-gray-500">예상 추가 주문 ≈ {s.expected_orders}건/월</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChannelPriorityCard({ channels }: { channels: ChannelScore[] }) {
  const sorted = [...channels].sort((a, b) => b.fit_score - a.fit_score);
  const maxScore = Math.max(...sorted.map((c) => c.fit_score), 1);
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">채널 우선순위</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      <p className="text-[10px] text-amber-700 bg-amber-50 px-2 py-1 rounded mb-3">
        ⓘ 적합도·ROI는 <span className="font-semibold">AI 추정치 (공식 미적용)</span>. 의사결정 시 실데이터 검증 필요.
      </p>
      <div className="space-y-3">
        {sorted.map((c, i) => {
          const barPct = (c.fit_score / maxScore) * 100;
          const isTop = i === 0;
          return (
            <div key={i}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${isTop ? "text-warn-600" : "text-gray-400"}`}>
                    #{i + 1}
                  </span>
                  <span className="text-sm font-semibold text-gray-900">{c.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">적합 {c.fit_score}</span>
                  <span className={`text-xs font-semibold tabular-nums ${
                    c.expected_roi_pct >= 100 ? "text-success-600" : "text-loss-500"
                  }`}>
                    ROI {c.expected_roi_pct}%
                  </span>
                </div>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-1.5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isTop ? "bg-warn-500" : "bg-gray-300"
                  }`}
                  style={{ width: `${barPct}%` }}
                />
              </div>
              <p className="text-[11px] text-gray-500 leading-relaxed">{c.rationale}</p>
              <p className="text-[11px] text-blue-600 mt-0.5">→ {c.first_step}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CopyVariantsCard({ variants }: { variants: CopyVariants }) {
  const tones = (["trust", "friendly", "urgent"] as const).filter((t) => variants[t]);
  const [active, setActive] = useState<typeof tones[number]>(tones[0] || "trust");
  const current = variants[active];
  if (!current) return null;
  const labelMap = { trust: "신뢰형", friendly: "친근형", urgent: "긴급형" };
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">바로 쓰는 카피 4종</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>

      {/* 톤 탭 */}
      <div className="flex gap-1 mb-2 p-1 bg-gray-100 rounded-lg">
        {tones.map((t) => (
          <button
            key={t}
            onClick={() => setActive(t)}
            className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${
              active === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
            }`}
          >
            {labelMap[t]}
          </button>
        ))}
      </div>
      <p className="text-[11px] text-gray-500 mb-3">{current.tone_desc}</p>

      <div className="space-y-2">
        {current.sms_to_regulars && <CopyRow label="단골 SMS (140자)" text={current.sms_to_regulars} />}
        {current.store_pop && <CopyRow label="매장 POP (50자)" text={current.store_pop} />}
        {current.sns_caption && <CopyRow label="SNS 캡션 + 해시태그" text={current.sns_caption} />}
        {current.delivery_intro && <CopyRow label="배달앱 가게 소개 한 줄" text={current.delivery_intro} />}
      </div>
    </div>
  );
}

function CopyRow({ label, text }: { label: string; text: string }) {
  const [copied, setCopied] = useState(false);
  const handle = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {}
  };
  return (
    <div className="border border-gray-100 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <button
          onClick={handle}
          className={`text-xs px-2 py-0.5 rounded font-medium transition-colors ${
            copied ? "bg-success-100 text-success-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          {copied ? "복사됨" : "복사"}
        </button>
      </div>
      <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{text}</p>
    </div>
  );
}

function CopiesCard({ copies }: { copies: ReadyCopies }) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">바로 쓰는 카피 4종</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      <div className="space-y-2">
        {copies.sms_to_regulars && <CopyRow label="단골 SMS (140자)" text={copies.sms_to_regulars} />}
        {copies.store_pop && <CopyRow label="매장 POP (50자)" text={copies.store_pop} />}
        {copies.sns_caption && <CopyRow label="SNS 캡션 + 해시태그" text={copies.sns_caption} />}
        {copies.delivery_intro && <CopyRow label="배달앱 가게 소개 한 줄" text={copies.delivery_intro} />}
      </div>
    </div>
  );
}

function ExecutiveSummaryCard({ summary }: { summary: any }) {
  // 신구조: {current, risk, recommendation} | 구구조: string
  const isStructured = summary && typeof summary === "object" && (summary.current || summary.risk || summary.recommendation);
  if (!isStructured) {
    return (
      <div className="bg-loss-50 border border-loss-100 rounded-xl p-4">
        <h3 className="font-semibold text-loss-700 text-sm mb-1">경영 진단 요약</h3>
        <p className="text-sm text-loss-600">{safeText(summary)}</p>
      </div>
    );
  }
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-4 py-2.5">
        <p className="text-[10px] text-white/70 font-bold uppercase tracking-wider">전문가 진단 리포트</p>
      </div>
      <div className="p-4 space-y-3">
        {summary.current && (
          <div className="border-l-2 border-blue-400 pl-3">
            <p className="text-[10px] text-blue-600 font-bold uppercase tracking-wide mb-1">현황</p>
            <p className="text-sm text-gray-700 leading-relaxed">{safeText(summary.current)}</p>
          </div>
        )}
        {summary.risk && (
          <div className="border-l-2 border-loss-500 pl-3">
            <p className="text-[10px] text-loss-600 font-bold uppercase tracking-wide mb-1">핵심 위험</p>
            <p className="text-sm text-gray-700 leading-relaxed">{safeText(summary.risk)}</p>
          </div>
        )}
        {summary.recommendation && (
          <div className="border-l-2 border-success-500 pl-3">
            <p className="text-[10px] text-success-600 font-bold uppercase tracking-wide mb-1">권고</p>
            <p className="text-sm text-gray-700 leading-relaxed">{safeText(summary.recommendation)}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function PreviousDiffCard({ previous, currentRisk }: { previous: any; currentRisk: string }) {
  if (!previous || (!previous.summary && !previous.risk_alert)) return null;
  const dateStr = previous.generated_at
    ? new Date(previous.generated_at).toISOString().slice(0, 10)
    : "이전";
  const riskChanged = previous.risk_alert && currentRisk && previous.risk_alert !== currentRisk;
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[10px] text-blue-700 font-bold uppercase tracking-wider">지난 진단 대비</span>
        <span className="text-[10px] text-blue-500">{dateStr}</span>
      </div>
      {previous.summary && (
        <div className="text-xs text-gray-700 leading-relaxed mb-2 line-clamp-3">
          이전: {previous.summary}
        </div>
      )}
      {riskChanged && (
        <div className="text-xs text-blue-700 bg-white rounded-md p-2 border border-blue-100">
          <span className="font-semibold">위험 변동: </span>
          기존 위험과 다른 새로운 위험이 식별됐습니다.
        </div>
      )}
    </div>
  );
}

function TowsMatrixCard({ tows }: { tows: any }) {
  if (!tows) return null;
  const cells = [
    { key: "so_strategy", label: "SO · 강점×기회 (공격)", color: "bg-success-50 border-success-100 text-success-700" },
    { key: "st_strategy", label: "ST · 강점×위협 (방어)", color: "bg-blue-50 border-blue-200 text-blue-900" },
    { key: "wo_strategy", label: "WO · 약점×기회 (보완)", color: "bg-warn-50 border-warn-100 text-warn-900" },
    { key: "wt_strategy", label: "WT · 약점×위협 (회피)", color: "bg-loss-50 border-loss-100 text-loss-700" },
  ];
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">TOWS 전략 도출</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {cells.map((c) => (
          <div key={c.key} className={`rounded-lg p-3 border ${c.color}`}>
            <p className="text-[10px] font-bold mb-1.5 opacity-80">{c.label}</p>
            <p className="text-xs leading-relaxed">{safeText(tows[c.key]) || "—"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function PositioningMapCard({ map }: { map: any }) {
  if (!map || !map.us) return null;
  const us = map.us;
  const competitors = (map.competitors || []) as { x: number; y: number; label: string }[];
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">포지셔닝 맵</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      <div className="relative">
        <svg viewBox="0 0 240 240" className="w-full bg-gray-50 rounded-lg">
          {/* 4분면 */}
          <line x1="120" y1="10" x2="120" y2="230" stroke="#cbd5e1" strokeWidth="1" />
          <line x1="10" y1="120" x2="230" y2="120" stroke="#cbd5e1" strokeWidth="1" />
          {/* 축 라벨 */}
          <text x="120" y="240" textAnchor="middle" className="text-[8px] fill-gray-500">{map.x_label || "X"}</text>
          <text x="6" y="120" transform="rotate(-90 6 120)" textAnchor="middle" className="text-[8px] fill-gray-500">{map.y_label || "Y"}</text>
          {/* 경쟁사 */}
          {competitors.map((c, i) => {
            const cx = 10 + (c.x / 100) * 220;
            const cy = 230 - (c.y / 100) * 220;
            return (
              <g key={i}>
                <circle cx={cx} cy={cy} r="5" fill="#9ca3af" />
                <text x={cx + 7} y={cy + 3} className="text-[8px] fill-gray-600">{c.label}</text>
              </g>
            );
          })}
          {/* 우리 가게 */}
          {(() => {
            const cx = 10 + (us.x / 100) * 220;
            const cy = 230 - (us.y / 100) * 220;
            return (
              <g>
                <circle cx={cx} cy={cy} r="9" fill="#facc15" stroke="#ca8a04" strokeWidth="2" />
                <text x={cx + 11} y={cy + 3} className="text-[9px] font-bold fill-warn-900">{us.label || "우리"}</text>
              </g>
            );
          })()}
        </svg>
      </div>
      {map.interpretation && (
        <p className="text-xs text-gray-600 mt-2 bg-gray-50 rounded-md p-2 leading-relaxed">
          {safeText(map.interpretation)}
        </p>
      )}
    </div>
  );
}

function ActionImpactMatrix({ items }: { items: any[] }) {
  // 점수 없는 아이템은 priority로 폴백
  const scored = items.map((it) => {
    const impact = typeof it.impact_score === "number" ? it.impact_score
      : it.priority === "high" ? 8 : it.priority === "medium" ? 5 : 3;
    const effort = typeof it.effort_score === "number" ? it.effort_score : 5;
    return { ...it, _impact: impact, _effort: effort };
  });

  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">실행 항목</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
      </div>
      {/* 2x2 매트릭스 */}
      <div className="relative bg-gradient-to-br from-success-50 via-white to-loss-50 rounded-lg p-2 mb-4 border border-gray-100">
        <svg viewBox="0 0 240 200" className="w-full">
          <line x1="120" y1="10" x2="120" y2="190" stroke="#e5e7eb" strokeWidth="1" />
          <line x1="10" y1="100" x2="230" y2="100" stroke="#e5e7eb" strokeWidth="1" />
          {/* 분면 라벨 */}
          <text x="170" y="20" textAnchor="middle" className="text-[8px] fill-success-600 font-bold">⭐ 즉시 실행</text>
          <text x="70" y="20" textAnchor="middle" className="text-[8px] fill-blue-600 font-bold">대형 프로젝트</text>
          <text x="170" y="195" textAnchor="middle" className="text-[8px] fill-warn-600 font-bold">자투리 시간</text>
          <text x="70" y="195" textAnchor="middle" className="text-[8px] fill-gray-500 font-bold">고려 안 함</text>
          {/* 축 */}
          <text x="6" y="100" transform="rotate(-90 6 100)" textAnchor="middle" className="text-[8px] fill-gray-500">임팩트 →</text>
          <text x="120" y="200" textAnchor="middle" className="text-[8px] fill-gray-500">← 실행 쉬움  /  어려움 →</text>
          {/* 데이터 점 — effort 낮을수록 오른쪽 (= 쉬움) */}
          {scored.map((it, i) => {
            const cx = 10 + ((10 - it._effort) / 10) * 220;
            const cy = 190 - (it._impact / 10) * 180;
            const color = it.priority === "high" ? "#ef4444" : it.priority === "medium" ? "#eab308" : "#22c55e";
            return (
              <g key={i}>
                <circle cx={cx} cy={cy} r="6" fill={color} fillOpacity="0.7" stroke="white" strokeWidth="1.5" />
                <text x={cx} y={cy + 3} textAnchor="middle" className="text-[8px] fill-white font-bold">{i + 1}</text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* 리스트 */}
      <div className="space-y-2">
        {scored.map((item, i) => (
          <div key={i} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="shrink-0 w-6 h-6 rounded-full bg-gray-700 text-white text-xs font-bold flex items-center justify-center">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  item.priority === "high" ? "bg-loss-100 text-loss-700" :
                  item.priority === "medium" ? "bg-warn-100 text-warn-900" :
                  "bg-success-100 text-success-700"
                }`}>
                  {item.priority === "high" ? "긴급" : item.priority === "medium" ? "중요" : "참고"}
                </span>
                <span className="text-[10px] text-gray-400">임팩트 {item._impact}/10</span>
                <span className="text-[10px] text-gray-400">난이도 {item._effort}/10</span>
              </div>
              <p className="text-sm text-gray-900 font-medium">{item.action}</p>
              <p className="text-xs text-success-600 mt-0.5">{item.expected_impact}</p>
              {(item.timeline || item.cost) && (
                <div className="flex gap-3 mt-1">
                  {item.timeline && <p className="text-xs text-gray-400">기간 {item.timeline}</p>}
                  {item.cost && <p className="text-xs text-gray-400">비용 {item.cost}</p>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MonthlyGoalCard({ goal }: { goal: any }) {
  // 신구조: {summary, kpis: [{name, target_value, current_value, unit, rationale}]}
  const kpis = goal && Array.isArray(goal.kpis) ? goal.kpis : null;
  if (!kpis) {
    // legacy fallback
    return (
      <div className="bg-warn-50 border border-warn-100 rounded-xl p-4">
        <h3 className="font-semibold text-warn-900 mb-1">이번 달 목표</h3>
        {typeof goal === "string" ? (
          <p className="text-sm text-warn-900">{goal}</p>
        ) : (
          <ul className="space-y-1">
            {Object.entries(goal || {}).map(([k, v]: [string, any]) => (
              <li key={k} className="text-sm text-warn-900">· {k}: {typeof v === "string" ? v : JSON.stringify(v)}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }
  const fmt = (n: number, u: string) => {
    if (u === "원") {
      if (n >= 100000000) return `${(n / 100000000).toFixed(1)}억`;
      if (n >= 10000) return `${(n / 10000).toFixed(0)}만`;
    }
    return n.toLocaleString();
  };
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className="bg-gradient-to-r from-warn-500 to-orange-400 px-4 py-2.5">
        <p className="text-[10px] text-white/90 font-bold uppercase tracking-wider">이번 달 목표</p>
        {goal.summary && <p className="text-sm text-white font-semibold mt-0.5">{goal.summary}</p>}
      </div>
      <div className="p-4 space-y-3">
        {kpis.map((k: any, i: number) => {
          const target = Number(k.target_value) || 0;
          const current = Number(k.current_value) || 0;
          const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0;
          return (
            <div key={i}>
              <div className="flex items-baseline justify-between mb-1">
                <p className="text-sm font-semibold text-gray-900">{k.name}</p>
                <p className="text-xs text-gray-500 tabular-nums">
                  <span className="font-bold text-gray-900">{fmt(current, k.unit)}</span>
                  <span className="text-gray-400"> / {fmt(target, k.unit)}{k.unit}</span>
                </p>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    pct >= 80 ? "bg-success-500" : pct >= 50 ? "bg-warn-500" : "bg-loss-500"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <div className="flex items-center justify-between mt-1">
                <p className="text-[10px] text-gray-500">{k.rationale}</p>
                <p className="text-[10px] font-bold text-gray-600">{pct}%</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface MenuMissingCategory {
  category: string;
  competitor_coverage_pct: number;
  fit_score: number;
  rationale: string;
  expected_avg_ticket_change_pct: number;
  implementation_cost: "low" | "medium" | "high";
}
interface MenuSeasonalWeek {
  week_label: string;
  theme: string;
  menu_idea: string;
  rationale: string;
  channel_action: string;
}
interface MenuDifferentiationPick {
  menu_name: string;
  why_us: string;
  why_not_competitors: string;
  first_step: string;
}
interface MenuStrategyData {
  strategy: {
    summary: string;
    gap_analysis: { headline: string; missing_categories: MenuMissingCategory[] };
    seasonal_calendar: MenuSeasonalWeek[];
    differentiation_pick: MenuDifferentiationPick | null;
  };
  generated_at: string;
}

function MenuStrategyCard() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<MenuStrategyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMenuStrategy(refresh);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "메뉴 전략 로드 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    if (!open && !data && !loading) load();
    setOpen(!open);
  };

  const costLabel = { low: "낮음", medium: "보통", high: "높음" };
  const costColor = {
    low: "bg-success-100 text-success-700",
    medium: "bg-warn-100 text-warn-900",
    high: "bg-loss-100 text-loss-700",
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <button
        onClick={handleOpen}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">메뉴 전략</h3>
          <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">
            갭 + 시즌 + 차별화
          </span>
        </div>
        <span className="text-gray-400 text-sm">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 border-t border-gray-100 pt-4">
          {loading && (
            <div className="flex flex-col items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-warn-500 mb-3" />
              <p className="text-xs text-gray-500">주변 경쟁 가게와 핵심 고객층을 살펴보는 중...</p>
            </div>
          )}
          {error && (
            <div className="text-center py-4">
              <p className="text-sm text-loss-500 mb-2">{error}</p>
              <button onClick={() => load(true)} className="text-xs text-gray-500 underline">
                다시 시도
              </button>
            </div>
          )}
          {data && data.strategy && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="bg-amber-50 border border-amber-100 rounded-lg p-3">
                <p className="text-sm font-semibold text-amber-800">{data.strategy.summary}</p>
              </div>

              {/* Gap Analysis */}
              {data.strategy.gap_analysis?.missing_categories?.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <p className="text-xs font-bold text-gray-700 uppercase tracking-wider">갭 분석</p>
                    <p className="text-[11px] text-gray-500">{data.strategy.gap_analysis.headline}</p>
                  </div>
                  <div className="space-y-2">
                    {data.strategy.gap_analysis.missing_categories.map((m, i) => (
                      <div key={i} className="border border-gray-100 rounded-lg p-3">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <p className="font-semibold text-sm text-gray-900 flex-1">{m.category}</p>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${costColor[m.implementation_cost] || "bg-gray-100"}`}>
                            도입비용 {costLabel[m.implementation_cost] || m.implementation_cost}
                          </span>
                        </div>
                        <div className="flex gap-3 text-[11px] text-gray-500 mb-2 tabular-nums">
                          <span>주변 보유 {m.competitor_coverage_pct}%</span>
                          <span>적합도 {m.fit_score}/100</span>
                          <span className={m.expected_avg_ticket_change_pct >= 0 ? "text-success-600 font-semibold" : "text-loss-500 font-semibold"}>
                            객단가 {m.expected_avg_ticket_change_pct >= 0 ? "+" : ""}{m.expected_avg_ticket_change_pct}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 leading-relaxed">{m.rationale}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Seasonal Calendar */}
              {data.strategy.seasonal_calendar?.length > 0 && (
                <div>
                  <p className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">시즌 캘린더 (4주)</p>
                  <div className="space-y-2">
                    {data.strategy.seasonal_calendar.map((w, i) => (
                      <div key={i} className="border-l-2 border-warn-400 bg-warn-50/50 pl-3 py-2">
                        <div className="flex items-baseline justify-between mb-1">
                          <p className="text-xs font-bold text-warn-900">{w.week_label}</p>
                          <p className="text-[10px] text-gray-500">{w.theme}</p>
                        </div>
                        <p className="text-sm text-gray-900 font-medium">{w.menu_idea}</p>
                        <p className="text-[11px] text-gray-600 mt-0.5">{w.rationale}</p>
                        <p className="text-[11px] text-blue-600 mt-1">→ {w.channel_action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Differentiation Pick */}
              {data.strategy.differentiation_pick && (
                <div className="bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200 rounded-lg p-3">
                  <p className="text-[10px] font-bold text-amber-700 uppercase tracking-wider mb-1">차별화 한 수</p>
                  <p className="text-base font-extrabold text-amber-900 mb-2">{data.strategy.differentiation_pick.menu_name}</p>
                  <div className="space-y-1.5 text-xs">
                    <p><span className="text-gray-500">우리 가게 적합 이유: </span><span className="text-gray-800">{data.strategy.differentiation_pick.why_us}</span></p>
                    <p><span className="text-gray-500">경쟁사가 못 하는 이유: </span><span className="text-gray-800">{data.strategy.differentiation_pick.why_not_competitors}</span></p>
                  </div>
                  <div className="mt-2 pt-2 border-t border-amber-200">
                    <p className="text-xs text-amber-700"><span className="font-semibold">오늘 시작: </span>{data.strategy.differentiation_pick.first_step}</p>
                  </div>
                </div>
              )}

              <button onClick={() => load(true)} className="w-full py-2 text-xs text-gray-400 hover:text-gray-600">
                메뉴 전략 다시 분석하기
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: { icon: string; label: string; active?: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="press-effect flex flex-col items-center gap-0.5 px-3 py-2"
    >
      <span className={`text-base ${active ? "" : "grayscale opacity-50"}`}>{icon}</span>
      <span className={`text-xs font-bold ${active ? "text-gray-900" : "text-gray-400"}`}>
        {label}
      </span>
    </button>
  );
}
