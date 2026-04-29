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

interface MarketingData {
  strategy: {
    summary: string;
    strategies: MarketingStrategy[];
    weekly_plan: string;
    quick_win?: string;
    revenue_uplift_plan?: RevenueUpliftPlan;
    ready_to_use_copies?: ReadyCopies;
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
  const [deepReport, setDeepReport] = useState<any>(null);
  const [deepLoading, setDeepLoading] = useState(false);
  const [tab, setTab] = useState<"competition" | "marketing" | "deep">("competition");

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
    try {
      const result = await api.getMarketingStrategy(refresh);
      setMarketing(result);
    } catch {} finally { setMarketingLoading(false); }
  };

  const loadDeepReport = async (refresh = false) => {
    if (!refresh && (deepReport || deepLoading)) return;
    setDeepLoading(true);
    try {
      const result = await api.getDeepReport(refresh);
      setDeepReport(result);
    } catch {} finally { setDeepLoading(false); }
  };

  useEffect(() => {
    if (tab === "marketing" && !marketing) loadMarketing();
    if (tab === "deep" && !deepReport) loadDeepReport();
  }, [tab]);

  if (isLoading || compLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  const priorityColor: Record<string, string> = { high: "bg-red-100 text-red-700", medium: "bg-yellow-100 text-yellow-700", low: "bg-green-100 text-green-700" };
  const priorityLabel: Record<string, string> = { high: "긴급", medium: "중요", low: "참고" };

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <header className="bg-white px-6 py-4 border-b border-gray-100">
        <h1 className="text-lg font-bold text-gray-900">경영 인사이트</h1>
        <p className="text-sm text-gray-500">{comp?.business_name} · {comp?.location}</p>
      </header>

      <div className="flex bg-white border-b border-gray-100">
        <button onClick={() => setTab("competition")}
          className={`flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors ${tab === "competition" ? "border-yellow-400 text-yellow-600" : "border-transparent text-gray-400"}`}>
          경쟁 분석
        </button>
        <button onClick={() => setTab("marketing")}
          className={`flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors ${tab === "marketing" ? "border-yellow-400 text-yellow-600" : "border-transparent text-gray-400"}`}>
          마케팅
        </button>
        <button onClick={() => setTab("deep")}
          className={`flex-1 py-3 text-sm font-medium text-center border-b-2 transition-colors ${tab === "deep" ? "border-yellow-400 text-yellow-600" : "border-transparent text-gray-400"}`}>
          집중분석
        </button>
      </div>

      <div className="px-6 py-4 space-y-4">
        {tab === "competition" && comp && (
          <>
            {/* 경쟁 현황 요약 */}
            {comp.competition_data ? (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-1">경쟁 현황</h3>
                <p className="text-xs text-gray-400 mb-3">{comp.competition_data.area_name}</p>
                <div className="grid grid-cols-3 gap-3">
                  <StatCard label="평균 점포 수" value={`${comp.competition_data.total_stores}개`} />
                  <StatCard label="개업률" value={`${comp.competition_data.opening_rate}%`} color={comp.competition_data.opening_rate > 5 ? "red" : "green"} />
                  <StatCard label="폐업률" value={`${comp.competition_data.closing_rate}%`} color={comp.competition_data.closing_rate > 5 ? "red" : "yellow"} />
                </div>
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600">
                    {comp.competition_data.net_change > 0
                      ? `순증가 ${comp.competition_data.net_change}%p — 경쟁이 심화되고 있습니다. 차별화가 필요합니다.`
                      : comp.competition_data.net_change < 0
                        ? `순감소 ${Math.abs(comp.competition_data.net_change)}%p — 시장이 축소 중입니다. 고객 유지에 집중하세요.`
                        : "개폐업 균형 상태입니다."}
                  </p>
                </div>
              </div>
            ) : (
              <GrayCard title="경쟁 현황" message="서울 외 지역은 개폐업 데이터를 제공하지 않습니다" />
            )}

            {/* 서울 평균 대비 벤치마킹 */}
            {comp.benchmark && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">서울 평균 대비 분석</h3>
                <p className="text-xs text-gray-400 mb-3">{comp.benchmark.business_type} 기준</p>
                <div className="space-y-3">
                  <BenchmarkRow
                    label="평균 객단가"
                    local={comp.benchmark.local_avg_ticket}
                    seoul={comp.benchmark.seoul_avg_ticket}
                    diff={comp.benchmark.ticket_diff_pct}
                    format="money"
                  />
                  <BenchmarkRow
                    label="주말 매출 비중"
                    local={comp.benchmark.local_weekend_ratio}
                    seoul={comp.benchmark.seoul_weekend_ratio}
                    diff={comp.benchmark.local_weekend_ratio - comp.benchmark.seoul_weekend_ratio}
                    format="pct"
                  />
                  <BenchmarkRow
                    label="여성 고객 비중"
                    local={comp.benchmark.local_female_ratio}
                    seoul={comp.benchmark.seoul_female_ratio}
                    diff={comp.benchmark.local_female_ratio - comp.benchmark.seoul_female_ratio}
                    format="pct"
                  />
                </div>
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
                <p className="mt-2 text-xs text-red-500 font-medium">
                  반경 500m 내 총 {Object.values(comp.radius_summary).reduce((a: number, b: any) => a + b, 0)}개 업체와 경쟁 중
                </p>
              </div>
            )}

            {/* 요일별 매출 */}
            {comp.sales_detail?.day_of_week && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">요일별 매출 패턴</h3>
                <BarChart data={comp.sales_detail.day_of_week} unit="%" />
                <p className="mt-2 text-xs text-gray-400">
                  {comp.sales_detail.sample_count}개 상권 평균 · {comp.location}
                </p>
              </div>
            )}

            {/* 시간대별 매출 */}
            {comp.sales_detail?.time_zone && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">시간대별 매출 패턴</h3>
                <BarChart data={comp.sales_detail.time_zone} unit="%" />
                <PeakInsight data={comp.sales_detail.time_zone} type="시간대" />
              </div>
            )}

            {/* 고객 분석 */}
            {comp.sales_detail && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">고객 분석</h3>

                {/* 성별 비교 */}
                <GenderCompare gender={comp.sales_detail.gender} />

                {/* 주중 vs 주말 */}
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">주중 vs 주말</p>
                  <WeekdayCompare data={comp.sales_detail.weekday_vs_weekend} />
                </div>

                {/* 연령대별 매출 */}
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">연령대별 매출</p>
                  <BarChart data={comp.sales_detail.age_group} unit="%" />
                  <PeakInsight data={comp.sales_detail.age_group} type="연령대" />
                </div>

                {/* 연령대별 건수 */}
                {comp.sales_detail.age_group_count && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">연령대별 이용 건수</p>
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
                    comp.change_index.dominant_status === "상권확장" ? "text-green-600" :
                    comp.change_index.dominant_status === "다이나믹" ? "text-blue-600" :
                    comp.change_index.dominant_status === "정체" ? "text-yellow-600" : "text-red-500"
                  }`}>
                    {comp.change_index.dominant_status}
                  </span>
                  <span className="text-xs text-gray-400">{comp.change_index.sample_count}개 상권</span>
                </div>
                <p className="text-xs text-gray-600 mb-3 leading-relaxed">
                  {comp.change_index.dominant_status === "상권확장"
                    ? "신규 진입 기회가 있는 성장 상권입니다. 생존업체 영업기간이 짧고 시장이 성장 중입니다."
                    : comp.change_index.dominant_status === "다이나믹"
                      ? "높은 회전율의 역동적 상권입니다. 도시재생/신규 개발 지역으로 기회와 위험이 공존합니다."
                      : comp.change_index.dominant_status === "정체"
                        ? "시장이 포화된 정체 상권입니다. 생존/폐업 업체 모두 영업기간이 길어 신규 진입 시 차별화가 필수입니다."
                        : "기존 업체가 강세인 축소 상권입니다. 신규 진입 실패율이 높으므로 주의가 필요합니다."}
                </p>
                {comp.change_index.status_distribution && (
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(comp.change_index.status_distribution).map(([status, count]: [string, any]) => (
                      <span key={status} className={`text-xs px-2 py-1 rounded-full ${
                        status === "상권확장" ? "bg-green-100 text-green-700" :
                        status === "다이나믹" ? "bg-blue-100 text-blue-700" :
                        status === "정체" ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      }`}>
                        {status} {count}곳
                      </span>
                    ))}
                  </div>
                )}
                {comp.change_index.avg_monthly_sales > 0 && (
                  <p className="text-xs text-gray-400 mt-2">월평균 매출: {comp.change_index.avg_monthly_sales.toLocaleString()}만원</p>
                )}
              </div>
            )}

            {/* 집객시설 */}
            {comp.facilities && (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-3">주변 집객시설</h3>
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
                <h3 className="font-semibold text-gray-900 mb-2">직장인구</h3>
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
                <h3 className="font-semibold text-gray-900 mb-2">상권 유동인구</h3>
                <p className="text-2xl font-bold text-gray-900 mb-3">{comp.floating_population.total?.toLocaleString()}명</p>
                {comp.floating_population.time_zone && (
                  <>
                    <p className="text-xs text-gray-500 mb-2">시간대별 유동인구</p>
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
                  <p key={i} className="text-xs text-yellow-700 bg-yellow-50 rounded-lg p-2 mt-1">{ins}</p>
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
                <p className="mt-3 text-xs text-red-500 font-medium">
                  주변 {comp.nearby_competitors.length}곳과 경쟁 중입니다. 차별화 전략이 필요합니다.
                </p>
              </div>
            )}

            {/* 유동인구 */}
            {comp.population_data ? (
              <div className="bg-white rounded-xl p-4 border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">유동인구</h3>
                <div className="flex items-baseline gap-2">
                  <span className={`text-2xl font-bold ${comp.population_data.change_percent > 0 ? "text-green-600" : "text-red-500"}`}>
                    {comp.population_data.change_percent > 0 ? "+" : ""}{comp.population_data.change_percent}%
                  </span>
                  <span className="text-sm text-gray-500">전일 대비</span>
                </div>
              </div>
            ) : (
              <GrayCard title="유동인구" message="서울 외 지역은 유동인구 데이터를 제공하지 않습니다" />
            )}
          </>
        )}

        {tab === "marketing" && (
          <>
            {marketingLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-yellow-400 mb-4" />
                <p className="text-sm text-gray-500">AI가 마케팅 전략을 분석하고 있습니다...</p>
                <p className="text-xs text-gray-400 mt-1">사장님 데이터 기반 맞춤 분석 중</p>
              </div>
            ) : marketing ? (
              <>
                <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4">
                  <p className="text-sm font-semibold text-yellow-800">{marketing.strategy.summary}</p>
                </div>
                {marketing.strategy.quick_win && (
                  <div className="bg-green-50 border border-green-100 rounded-xl p-4">
                    <p className="text-xs text-green-600 font-medium mb-1">오늘 당장 할 수 있는 것</p>
                    <p className="text-sm text-green-800 font-semibold">{marketing.strategy.quick_win}</p>
                  </div>
                )}

                {marketing.strategy.revenue_uplift_plan && (
                  <UpliftCard plan={marketing.strategy.revenue_uplift_plan} />
                )}

                {marketing.strategy.ready_to_use_copies && (
                  <CopiesCard copies={marketing.strategy.ready_to_use_copies} />
                )}
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
                      <p className="text-xs text-green-600 font-medium">{s.expected_effect}</p>
                      {(s.budget || s.timeline) && (
                        <div className="flex gap-3 mt-1">
                          {s.budget && <span className="text-xs text-gray-400">비용: {s.budget}</span>}
                          {s.timeline && <span className="text-xs text-gray-400">기간: {s.timeline}</span>}
                        </div>
                      )}
                      {(s.category === "offline" || s.category === "event") && (
                        <button onClick={() => router.push("/coupons")}
                          className="mt-3 w-full py-2 bg-yellow-400 text-gray-900 text-sm font-semibold rounded-lg hover:bg-yellow-500 transition-colors">
                          쿠폰으로 실행하기
                        </button>
                      )}
                      {s.category === "subsidy" && (
                        <button onClick={() => router.push("/subsidies")}
                          className="mt-3 w-full py-2 bg-yellow-400 text-gray-900 text-sm font-semibold rounded-lg hover:bg-yellow-500 transition-colors">
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

        {tab === "deep" && (
          <>
            {deepLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-yellow-400 mb-4" />
                <p className="text-sm text-gray-500">AI가 종합 경영 진단을 수행하고 있습니다...</p>
                <p className="text-xs text-gray-400 mt-1">서울시 빅데이터 + 상권 분석 + 경쟁사 데이터 종합 중</p>
              </div>
            ) : deepReport ? (
              <>
                {/* 경영 현황 요약 */}
                <div className="bg-red-50 border border-red-100 rounded-xl p-4">
                  <h3 className="font-semibold text-red-700 text-sm mb-1">경영 진단 요약</h3>
                  <p className="text-sm text-red-600">{safeText(deepReport.report.executive_summary)}</p>
                </div>

                {/* 시급한 위험 */}
                {deepReport.report.risk_alert && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                    <p className="text-xs text-yellow-600 font-medium mb-1">시급한 위험</p>
                    <p className="text-sm text-yellow-800 font-semibold">{safeText(deepReport.report.risk_alert)}</p>
                  </div>
                )}

                {/* 상권 입지 분석 */}
                {deepReport.report.location_analysis && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">상권 입지 분석</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{safeText(deepReport.report.location_analysis)}</p>
                  </div>
                )}

                {/* SWOT 분석 */}
                {deepReport.report.swot && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-3">SWOT 분석</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <SwotCard title="강점 (S)" items={deepReport.report.swot.strengths} color="green" />
                      <SwotCard title="약점 (W)" items={deepReport.report.swot.weaknesses} color="red" />
                      <SwotCard title="기회 (O)" items={deepReport.report.swot.opportunities} color="blue" />
                      <SwotCard title="위협 (T)" items={deepReport.report.swot.threats} color="yellow" />
                    </div>
                  </div>
                )}

                {/* 핵심 고객층 분석 */}
                {deepReport.report.customer_insight && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">핵심 고객층 분석</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{safeText(deepReport.report.customer_insight)}</p>
                  </div>
                )}

                {/* 시간 전략 */}
                {deepReport.report.time_strategy && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">요일/시간대 최적화</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{safeText(deepReport.report.time_strategy)}</p>
                  </div>
                )}

                {/* 경쟁 분석 */}
                {deepReport.report.competition_analysis && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">경쟁 분석</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{safeText(deepReport.report.competition_analysis)}</p>
                  </div>
                )}

                {/* 업종 트렌드 */}
                {deepReport.report.trend_analysis && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-2">업종 트렌드</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">{safeText(deepReport.report.trend_analysis)}</p>
                  </div>
                )}

                {/* 실행 항목 */}
                {deepReport.report.action_items?.length > 0 && (
                  <div className="bg-white rounded-xl p-4 border border-gray-100">
                    <h3 className="font-semibold text-gray-900 mb-3">실행 항목</h3>
                    <div className="space-y-2">
                      {deepReport.report.action_items.map((item: any, i: number) => (
                        <div key={i} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
                          <span className={`shrink-0 px-2 py-0.5 text-xs font-medium rounded-full h-fit ${
                            item.priority === "high" ? "bg-red-100 text-red-700" :
                            item.priority === "medium" ? "bg-yellow-100 text-yellow-700" :
                            "bg-green-100 text-green-700"
                          }`}>
                            {item.priority === "high" ? "긴급" : item.priority === "medium" ? "중요" : "참고"}
                          </span>
                          <div>
                            <p className="text-sm text-gray-900 font-medium">{item.action}</p>
                            <p className="text-xs text-green-600 mt-0.5">{item.expected_impact}</p>
                            {item.timeline && <p className="text-xs text-gray-400 mt-0.5">{item.timeline}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 이번 달 목표 */}
                {deepReport.report.monthly_goal && (
                  <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4">
                    <h3 className="font-semibold text-yellow-800 mb-1">이번 달 목표</h3>
                    {typeof deepReport.report.monthly_goal === "string" ? (
                      <p className="text-sm text-yellow-700">{deepReport.report.monthly_goal}</p>
                    ) : (
                      <ul className="space-y-1">
                        {Object.entries(deepReport.report.monthly_goal).map(([k, v]: [string, any]) => (
                          <li key={k} className="text-sm text-yellow-700">· {k}: {typeof v === "string" ? v : JSON.stringify(v)}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                <button onClick={() => { setDeepReport(null); loadDeepReport(true); }}
                  className="w-full py-2 text-sm text-gray-400 hover:text-gray-600">
                  리포트 다시 생성하기
                </button>
              </>
            ) : (
              <p className="text-center text-gray-400 py-8">리포트를 불러오지 못했습니다</p>
            )}
          </>
        )}

      </div>

      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-6 py-3">
        <div className="flex justify-around max-w-sm mx-auto">
          <NavItem label="홈" active={pathname === "/dashboard"} onClick={() => router.push("/dashboard")} />
          <NavItem label="지원사업" active={pathname === "/subsidies"} onClick={() => router.push("/subsidies")} />
          <NavItem label="인사이트" active={pathname === "/insights"} onClick={() => router.push("/insights")} />
          <NavItem label="쿠폰" active={pathname === "/coupons"} onClick={() => router.push("/coupons")} />
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
              className="h-full bg-yellow-400 rounded-full transition-all duration-500"
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
    <p className="mt-2 text-xs text-red-500 font-medium">
      {type} 중 {peak[0]}에 매출이 가장 높습니다. 이 시간대 마케팅에 집중하세요.
    </p>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  const colorMap: Record<string, string> = { red: "text-red-500", yellow: "text-yellow-600", green: "text-green-600" };
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className={`text-lg font-bold ${colorMap[color || ""] || "text-gray-900"}`}>{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

function GenderCompare({ gender }: { gender: Record<string, number> }) {
  const mPct = gender["남성_비중"] || gender["남성_매출"] || 0;
  const fPct = gender["여성_비중"] || gender["여성_매출"] || 0;
  const mCountPct = gender["남성_건수비중"] || gender["남성_건수"] || 0;
  const fCountPct = gender["여성_건수비중"] || gender["여성_건수"] || 0;
  const total = mPct + fPct || 1;
  const mNorm = Math.round(mPct / total * 100);
  const fNorm = 100 - mNorm;

  return (
    <div>
      <p className="text-xs text-gray-500 mb-2">성별 매출 비교</p>
      <div className="flex h-8 rounded-full overflow-hidden mb-2">
        <div className="bg-blue-400 flex items-center justify-center text-xs font-medium text-white" style={{ width: `${mNorm}%` }}>
          {mNorm > 15 && `남 ${mPct}%`}
        </div>
        <div className="bg-pink-400 flex items-center justify-center text-xs font-medium text-white" style={{ width: `${fNorm}%` }}>
          {fNorm > 15 && `여 ${fPct}%`}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xs text-blue-500 mb-1">남성</p>
          <p className="text-sm font-bold text-blue-700">매출 {mPct}%</p>
          <p className="text-xs text-blue-400">건수 {mCountPct}%</p>
        </div>
        <div className="bg-pink-50 rounded-lg p-3 text-center">
          <p className="text-xs text-pink-500 mb-1">여성</p>
          <p className="text-sm font-bold text-pink-700">매출 {fPct}%</p>
          <p className="text-xs text-pink-400">건수 {fCountPct}%</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        {mPct > fPct
          ? `남성 고객 매출 비중이 ${(mPct - fPct).toFixed(1)}%p 높습니다. 여성 타겟 마케팅으로 매출을 늘릴 수 있습니다.`
          : `여성 고객 매출 비중이 ${(fPct - mPct).toFixed(1)}%p 높습니다. 여성 고객 만족도를 유지하세요.`}
      </p>
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
      <div className="flex-1 bg-yellow-50 rounded-lg p-3 text-center">
        <p className="text-xs text-yellow-600">주말 (토~일)</p>
        <p className="text-lg font-bold text-yellow-700">{weekend}%</p>
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
        <span className={`font-medium ${isPositive ? "text-green-600" : "text-red-500"}`}>
          {isPositive ? "+" : ""}{format === "pct" ? `${diff.toFixed(1)}%p` : `${diff.toFixed(1)}%`}
        </span>
      </div>
      <div className="flex gap-2 text-xs">
        <div className="flex-1 bg-yellow-50 rounded p-1.5 text-center">
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
    green: "bg-green-50 border-green-200", red: "bg-red-50 border-red-200",
    blue: "bg-blue-50 border-blue-200", yellow: "bg-yellow-50 border-yellow-200",
  };
  const textMap: Record<string, string> = {
    green: "text-green-700", red: "text-red-700", blue: "text-blue-700", yellow: "text-yellow-700",
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
    easy: "bg-green-100 text-green-700",
    medium: "bg-yellow-100 text-yellow-700",
    hard: "bg-orange-100 text-orange-700",
  } as const;
  const pct = plan.target_avg_ticket > 0
    ? Math.min(100, Math.round((plan.current_avg_ticket / plan.target_avg_ticket) * 100))
    : 0;

  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-gray-900">객단가 끌어올리기</h3>
        <span className="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded font-medium">시뮬레이션</span>
      </div>

      {/* 게이지 */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>현재 {won(plan.current_avg_ticket)}</span>
          <span>목표 {won(plan.target_avg_ticket)}</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-red-500 font-medium mt-1.5">
          1건당 {won(plan.gap_per_order)} 부족 · 월 {plan.monthly_orders_estimate.toLocaleString()}건 기준 잠재력 +{won(plan.monthly_uplift_potential_won)}/월
        </p>
      </div>

      <p className="text-xs text-gray-600 mb-3 bg-gray-50 rounded-lg p-2">{plan.rationale}</p>

      {/* 추천 옵션 3종 */}
      <p className="text-xs text-gray-500 font-medium mb-2">추천 옵션 (쉬운 순)</p>
      <div className="space-y-2">
        {plan.uplift_options.map((opt, i) => (
          <div key={i} className="border border-gray-100 rounded-lg p-3">
            <div className="flex items-start justify-between gap-2 mb-1">
              <p className="font-semibold text-gray-900 text-sm flex-1">{opt.name}</p>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${easeColor[opt.ease] || "bg-gray-100 text-gray-700"}`}>
                {easeBadge[opt.ease] || opt.ease}
              </span>
            </div>
            <div className="flex gap-3 text-xs text-gray-500 mb-2">
              <span>+{won(opt.add_price_won)}</span>
              <span>부착률 {opt.expected_attach_rate_pct}%</span>
              <span className="text-green-600 font-semibold">평균 +{won(opt.expected_avg_uplift_won)}</span>
            </div>
            <p className="text-xs text-gray-600">{opt.how}</p>
          </div>
        ))}
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
            copied ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
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
        <span className="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded font-medium">복붙 가능</span>
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

function NavItem({ label, active, onClick }: { label: string; active?: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className={`text-xs font-medium py-1 ${active ? "text-yellow-600" : "text-gray-400"}`}>
      {label}
    </button>
  );
}
