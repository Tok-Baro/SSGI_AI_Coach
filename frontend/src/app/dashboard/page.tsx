"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import STTButton from "@/components/common/STTButton";
import type { DashboardData, RiskFactor, UpcomingEvent } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, checkAuth, logout } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFactors, setShowFactors] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
      return;
    }
    if (!isLoading && isAuthenticated && user && !user.onboarding_completed) {
      router.push("/onboarding");
      return;
    }
    if (isAuthenticated && user?.onboarding_completed) {
      api.getDashboard()
        .then(setData)
        .catch((err) => setError(err.message || "데이터를 불러오지 못했습니다."))
        .finally(() => setLoading(false));
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={() => window.location.reload()} className="px-6 py-2 bg-gray-100 rounded-lg">
          다시 시도
        </button>
      </div>
    );
  }

  if (!data) return null;

  const handleDownloadReport = async () => {
    setReportLoading(true);
    setReportError(null);
    try {
      const blob = await api.downloadWeeklyReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `weekly-report-${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "리포트 생성 실패");
    } finally {
      setReportLoading(false);
    }
  };

  const handleCompleteAction = async () => {
    if (!data.today_action) return;
    try {
      await api.completeAction(data.today_action.id);
      setData({
        ...data,
        today_action: { ...data.today_action, is_completed: true },
      });
      const cta = data.today_action.cta_type;
      if (cta === "apply_subsidy") {
        router.push("/subsidies");
      } else if (cta === "create_coupon") {
        router.push("/coupons");
      }
    } catch (err) {
      console.error("Action completion failed:", err);
    }
  };

  const riskColor = data.risk_score > 0.5 ? "red" : data.risk_score > 0.3 ? "yellow" : "green";
  const riskColorMap = {
    red: { text: "text-red-500", bg: "bg-red-500", light: "bg-red-50" },
    yellow: { text: "text-yellow-500", bg: "bg-yellow-400", light: "bg-yellow-50" },
    green: { text: "text-green-500", bg: "bg-green-500", light: "bg-green-50" },
  };
  const colors = riskColorMap[riskColor];
  const trendLabel = { improving: "개선 중", stable: "유지", worsening: "악화 중" };
  // 위험도 4단계 등급 (점수 의미를 시니어도 직관적으로)
  const riskScore100 = Math.round(data.risk_score * 100);
  const riskGrade =
    data.risk_score > 0.7 ? "위험"
    : data.risk_score > 0.5 ? "경고"
    : data.risk_score > 0.3 ? "주의"
    : "안전";

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      {/* 헤더 */}
      <header className="bg-white px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">안녕하세요, {data.user.nickname}님</p>
          <h1 className="text-lg font-bold text-gray-900">{data.user.business_name}</h1>
        </div>
        <button
          onClick={() => { logout(); router.push("/"); }}
          className="text-xs text-gray-400 hover:text-red-500 px-3 py-1.5 border border-gray-200 rounded-lg"
        >
          로그아웃
        </button>
      </header>

      <div className="px-6 py-4 space-y-4">
        {/* 잠재 지원금 (정직: 매칭 합계, 가짜 ticker 없음) */}
        <PotentialSubsidyBadge
          totalAmountWon={(data.total_potential_amount || 0) * 10_000}
          matchCount={data.subsidy_matches?.length || 0}
          imminentCount={
            data.subsidy_matches?.filter(
              (s) => s.days_until_deadline !== null && s.days_until_deadline !== undefined && s.days_until_deadline <= 14,
            ).length || 0
          }
          socialProof={data.social_proof}
        />

        {/* 복합 위험도 */}
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">경영 위험도</span>
            <div className="flex items-center gap-2">
              <DeltaBadge value={data.deltas?.risk_score_delta ?? null} suffix="" inversed scale={100} />
              {data.trend_direction && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  data.trend_direction === "worsening" ? "bg-red-50 text-red-500" :
                  data.trend_direction === "improving" ? "bg-green-50 text-green-500" :
                  "bg-gray-50 text-gray-400"
                }`}>
                  {trendLabel[data.trend_direction] || "유지"}
                </span>
              )}
              <span className={`text-xl font-bold ${colors.text}`}>
                {riskGrade}
                <span className="ml-1 text-base font-medium text-gray-500">
                  ({riskScore100}/100)
                </span>
              </span>
            </div>
          </div>
          <p className="text-[11px] text-gray-400 mb-2">
            출처: 서울 열린데이터 (상권매출·유동인구·상권변화) · 점수가 높을수록 위험
          </p>

          {/* Peer percentile (k≥10일 때만) */}
          {data.peer_percentile !== null && data.peer_percentile !== undefined ? (
            <p className="text-xs text-gray-500 mb-2">
              동종업계 <span className="font-semibold text-gray-700">상위 {data.peer_percentile}%</span>
              <span className="text-gray-400"> · {data.peer_sample}명 비교 (14일 평균)</span>
            </p>
          ) : (
            <p className="text-[11px] text-gray-400 mb-2">
              동종업계 비교 — 같은 업종 사용자 10명 누적 시 활성화 (k-anonymity)
            </p>
          )}

          {/* 프로그레스 바 */}
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${colors.bg}`}
              style={{ width: `${data.risk_score * 100}%` }}
            />
          </div>

          {/* 위험도 추이 미니 차트 */}
          {data.risk_trend && data.risk_trend.length > 1 && (
            <div className="mt-3 flex items-end gap-1 h-10">
              {data.risk_trend.slice(-14).map((point, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t transition-all ${
                    point.score > 0.5 ? "bg-red-300" : point.score > 0.3 ? "bg-yellow-300" : "bg-green-300"
                  }`}
                  style={{ height: `${Math.max(point.score * 100, 8)}%` }}
                  title={`${point.date}: ${Math.round(point.score * 100)}점`}
                />
              ))}
            </div>
          )}

          <button
            onClick={() => setShowFactors(!showFactors)}
            className="mt-3 text-xs text-gray-400 hover:text-gray-600 w-full text-center"
          >
            {showFactors ? "요인 분석 접기" : "요인 분석 보기"}
          </button>

          {showFactors && data.risk_factors && (
            <div className="mt-3 space-y-2.5">
              {data.risk_factors.map((factor: RiskFactor) => (
                <FactorBar key={factor.name} factor={factor} />
              ))}
            </div>
          )}
        </div>

        {/* 폐업 위험 진단 (Survival Matrix) */}
        <SurvivalMatrixCard />

        {/* 오늘의 액션 */}
        {!data.today_action && (
          <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">
                오늘의 액션
              </span>
              <span className="text-[10px] text-yellow-600">매일 오전 7시 자동 생성</span>
            </div>
            <p className="text-sm text-yellow-800 font-medium mt-2">
              사장님의 첫 액션이 곧 도착합니다
            </p>
            <p className="text-[11px] text-yellow-700/80 mt-1">
              상권 데이터 분석 후 매일 1개의 액션을 추천합니다
            </p>
          </div>
        )}
        {data.today_action && (
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">
                오늘의 액션
              </span>
              <span className="text-xs text-gray-400">{data.today_action.action_type}</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{data.today_action.title}</h3>
            <p className="text-sm text-gray-600 mb-3">{data.today_action.description}</p>
            {!data.today_action.is_completed ? (
              <button
                onClick={handleCompleteAction}
                className="w-full py-2.5 bg-yellow-400 text-gray-900 font-semibold rounded-lg hover:bg-yellow-500 transition-colors"
              >
                {data.today_action.cta_type === "apply_subsidy" ? "지원사업 확인하기" :
                 data.today_action.cta_type === "create_coupon" ? "쿠폰 만들기" :
                 "실행하기"}
              </button>
            ) : (
              <>
                <p className="text-center text-sm text-green-600 font-medium">완료됨</p>
                {data.next_action_preview && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wide mb-1">다음 후보</p>
                    <p className="text-sm font-semibold text-gray-800">{data.next_action_preview.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{data.next_action_preview.subtitle}</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 지원사업 매칭 */}
        {data.subsidy_matches.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <h3 className="font-semibold text-gray-700 mb-1">매칭 지원사업</h3>
            <p className="text-sm text-gray-500 mb-1">현재 매칭되는 지원사업이 없습니다</p>
            <p className="text-[11px] text-gray-400">
              지역 · 업종 조건에 맞는 사업이 등록되면 자동 표시됩니다
            </p>
            <button
              onClick={() => router.push("/subsidies")}
              className="mt-2 text-xs text-yellow-600 font-medium"
            >
              전체 지원사업 둘러보기 →
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-3">
              매칭 지원사업 ({data.subsidy_matches.length}건)
            </h3>
            <div className="space-y-3">
              {data.subsidy_matches.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    api.logSubsidySignal(s.id, "click").catch(() => {});
                    router.push("/subsidies");
                  }}
                  className="w-full p-3 bg-gray-50 rounded-lg text-left hover:bg-gray-100 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <p className="font-medium text-sm text-gray-900">{s.title}</p>
                    {s.max_amount && (
                      <span className="text-sm font-bold text-red-500 whitespace-nowrap ml-2">
                        {s.max_amount}만원
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{s.organization}</p>
                  {s.days_until_deadline !== null && s.days_until_deadline !== undefined && (
                    <p className="text-xs text-red-500 mt-1 font-medium">
                      마감 D-{s.days_until_deadline}
                    </p>
                  )}
                  {s.match_reasons && s.match_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {s.match_reasons.map((r, i) => (
                        <span key={i} className="text-[10px] px-1.5 py-0.5 bg-yellow-50 text-yellow-700 rounded font-medium">
                          ✓ {r}
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
            <button
              onClick={() => router.push("/subsidies")}
              className="w-full mt-3 py-2 text-sm text-yellow-600 font-medium hover:text-yellow-700"
            >
              전체 지원사업 보기
            </button>
          </div>
        )}

        {/* 유동인구 트렌드 */}
        {data.population_trend ? (
          <div className="bg-white rounded-xl p-4 border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-2">유동인구 트렌드</h3>
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-bold ${
                data.population_trend.change_percent > 0 ? "text-green-600" : "text-red-500"
              }`}>
                {data.population_trend.change_percent > 0 ? "+" : ""}
                {data.population_trend.change_percent}%
              </span>
              <span className="text-sm text-gray-500">전일 대비</span>
            </div>
            <p className="text-[10px] text-gray-400 mt-1">서울시 생활인구 (행정동 단위 합산)</p>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <h3 className="font-semibold text-gray-400 mb-1">유동인구 트렌드</h3>
            <p className="text-xs text-gray-400">서울 외 지역은 데이터를 제공하지 않습니다</p>
          </div>
        )}

        {/* 이번주 문화행사 (real Seoul API) */}
        <UpcomingEventsCard events={data.upcoming_events || []} />

        {/* 주간 마케팅 리포트 PDF */}
        <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-4 border border-indigo-100">
          <h3 className="font-semibold text-gray-900 mb-1">주간 마케팅 인사이트 리포트</h3>
          <p className="text-xs text-gray-600 mb-3">
            6개 카테고리 점수, 주요 진단, 1주/1~3개월/3~6개월 액션 플랜이 담긴 PDF
          </p>
          {reportError && (
            <p className="text-xs text-red-500 mb-2">{reportError}</p>
          )}
          <button
            onClick={handleDownloadReport}
            disabled={reportLoading}
            className="w-full py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {reportLoading ? "리포트 생성 중..." : "PDF 다운로드"}
          </button>
        </div>

        {/* 쿠폰 통계 */}
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">쿠폰 성과</h3>
            <DeltaBadge value={data.deltas?.coupon_scan_delta_pct ?? null} suffix="%" />
          </div>
          <div className="flex gap-4">
            <div>
              <p className="text-2xl font-bold text-gray-900">{data.coupon_stats.total_created}</p>
              <p className="text-xs text-gray-500">발행</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{data.coupon_stats.total_scanned}</p>
              <p className="text-xs text-gray-500">스캔 (누적)</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">{Math.round(data.action_completion_rate * 100)}%</p>
              <p className="text-xs text-gray-500">액션 완료율 (30일)</p>
            </div>
          </div>
        </div>
      </div>

      <STTButton />

      {/* 하단 네비게이션 */}
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

function FactorBar({ factor }: { factor: RiskFactor }) {
  if (!factor.data_available) {
    return (
      <div className="opacity-50">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-400">{factor.label}</span>
          <span className="text-gray-400">데이터 없음</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full" />
      </div>
    );
  }

  const barColor = factor.score > 0.6 ? "bg-red-400" : factor.score > 0.3 ? "bg-yellow-400" : "bg-green-400";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600">{factor.label}</span>
        <span className="text-gray-500">{factor.description}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${factor.score * 100}%` }}
        />
      </div>
    </div>
  );
}

/**
 * 잠재 지원금 카드 — 정직 버전.
 * - 매칭된 지원사업 max_amount 합계 (실제값)
 * - 가짜 실시간 ticker 애니메이션 제거
 * - "추정 ÷ 365일" 같은 단순 환산 라벨 제거
 */
function PotentialSubsidyBadge({
  totalAmountWon,
  matchCount,
  imminentCount,
  socialProof,
}: {
  totalAmountWon: number;
  matchCount: number;
  imminentCount: number;
  socialProof: string | null;
}) {
  if (totalAmountWon <= 0 || matchCount === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">
          매칭 지원금
        </p>
        <p className="text-sm text-gray-600">
          현재 사장님 업종/지역에 매칭된 지원사업이 없습니다
        </p>
        <p className="text-[11px] text-gray-400 mt-1">
          신규 공고 등록 시 자동 매칭됩니다
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-amber-700 font-bold uppercase tracking-wider">
          신청 가능 지원금
        </span>
        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">
          매칭 {matchCount}건
        </span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-extrabold text-amber-700 tabular-nums">
          {totalAmountWon.toLocaleString()}
        </span>
        <span className="text-base font-semibold text-amber-600">원</span>
      </div>
      <p className="text-[11px] text-amber-700/80 mt-1.5 leading-relaxed">
        매칭된 지원사업 최대금액 합계
        {imminentCount > 0 && (
          <span className="ml-1 text-red-600 font-semibold">· D-14 임박 {imminentCount}건</span>
        )}
      </p>
      {socialProof && (
        <div className="mt-3 pt-3 border-t border-amber-100">
          <p className="text-xs text-amber-700/90">{socialProof}</p>
        </div>
      )}
    </div>
  );
}

function UpcomingEventsCard({ events }: { events: UpcomingEvent[] }) {
  if (!events || events.length === 0) return null;
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <h3 className="font-semibold text-gray-900 mb-2">이번 주 우리 동네 이벤트</h3>
      <p className="text-[10px] text-gray-400 mb-3">서울시 문화행사 정보 (자치구 단위)</p>
      <div className="space-y-2">
        {events.slice(0, 3).map((e, i) => (
          <a
            key={i}
            href={e.url || "#"}
            target="_blank"
            rel="noreferrer"
            className="block p-2.5 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <div className="flex items-baseline justify-between gap-2">
              <p className="font-medium text-sm text-gray-900 truncate">{e.title}</p>
              {e.start_date && (
                <span className="text-[10px] text-gray-500 whitespace-nowrap tabular-nums">
                  {e.start_date.slice(0, 10)}
                </span>
              )}
            </div>
            <p className="text-[11px] text-gray-500 mt-0.5 truncate">
              {[e.category, e.place].filter(Boolean).join(" · ")}
            </p>
          </a>
        ))}
      </div>
    </div>
  );
}

function DeltaBadge({
  value,
  suffix = "%",
  inversed = false,
  scale = 1,
}: {
  value: number | null;
  suffix?: string;
  inversed?: boolean;
  scale?: number;
}) {
  if (value === null || value === undefined) return null;
  const display = Math.abs(value * scale);
  if (display < 0.05) return null;
  const isUp = value > 0;
  const isGood = inversed ? !isUp : isUp;
  const color = isGood ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700";
  const arrow = isUp ? "▲" : "▼";
  const formatted = scale === 1 ? display.toFixed(1) : Math.round(display).toString();
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${color} tabular-nums`}>
      {arrow} {formatted}{suffix}
    </span>
  );
}

interface SurvivalSignal {
  name: string;
  current: string;
  threshold: string;
  severity: "high" | "medium" | "low";
  triggered: boolean;
}
interface SurvivalScoreData {
  survival_score: number;
  risk_level: "safe" | "watch" | "warning" | "critical";
  risk_label: string;
  headline: string;
  your_position: {
    operating_months: number | null;
    closed_avg_months: number;
    survival_avg_months: number;
    operating_percentile: number | null;
  };
  risk_signals: SurvivalSignal[];
  triggered_count: number;
  total_signals: number;
  pattern_similarity_pct: number;
  survival_action: string;
}

function SurvivalMatrixCard() {
  const [data, setData] = useState<SurvivalScoreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getSurvivalScore()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "로드 실패"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-4 border border-gray-100">
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400" />
          <span className="text-xs text-gray-500">생존 매트릭스 분석 중...</span>
        </div>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
        <p className="text-xs text-gray-500">생존 진단 데이터를 불러오지 못했습니다</p>
      </div>
    );
  }

  const levelStyle = {
    safe: { bg: "from-green-500 to-emerald-600", text: "text-green-600", chip: "bg-green-100 text-green-700" },
    watch: { bg: "from-blue-500 to-indigo-600", text: "text-blue-600", chip: "bg-blue-100 text-blue-700" },
    warning: { bg: "from-orange-500 to-red-500", text: "text-orange-600", chip: "bg-orange-100 text-orange-700" },
    critical: { bg: "from-red-600 to-red-800", text: "text-red-600", chip: "bg-red-100 text-red-700" },
  }[data.risk_level];

  const sevColor = (s: string) =>
    s === "high" ? "bg-red-500" : s === "medium" ? "bg-yellow-500" : "bg-gray-300";

  const pos = data.your_position;
  const showPositionBar =
    pos.operating_months !== null && pos.closed_avg_months > 0;
  const positionPct = pos.operating_percentile !== null ? Math.min(130, pos.operating_percentile) : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className={`bg-gradient-to-r ${levelStyle.bg} px-4 py-3`}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-white/90 font-bold uppercase tracking-wider">
            생존 매트릭스
          </span>
          <span className={`text-[10px] px-2 py-0.5 bg-white/20 text-white rounded-full font-bold`}>
            {data.risk_label}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white tabular-nums">{data.survival_score}</span>
          <span className="text-sm text-white/80">/ 100</span>
          <span className="text-xs text-white/70 ml-auto">
            폐업 패턴 유사도 {data.pattern_similarity_pct}%
          </span>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <p className="text-sm text-gray-800 font-semibold">{data.headline}</p>

        {showPositionBar && (
          <div>
            <div className="flex justify-between text-[11px] text-gray-500 mb-1">
              <span>우리 가게 {pos.operating_months}개월</span>
              <span>폐업 평균 {pos.closed_avg_months}개월</span>
            </div>
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div className="absolute top-0 bottom-0 bg-red-100" style={{ left: "53%", right: "0%" }} />
              <div
                className={`absolute top-0 bottom-0 w-1 ${
                  positionPct >= 70 ? "bg-red-500" : "bg-green-500"
                }`}
                style={{ left: `${(positionPct / 130) * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-gray-400 mt-1">
              폐업 평균의 {pos.operating_percentile}% 지점 · 빨간 영역 = 위험 구간
            </p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-bold text-gray-700 uppercase tracking-wider">위험 신호</p>
            <p className="text-[11px] text-gray-500">
              <span className={`font-bold ${data.triggered_count >= 3 ? "text-red-600" : "text-gray-700"}`}>
                {data.triggered_count}
              </span>
              <span className="text-gray-400"> / {data.total_signals}개 발생</span>
            </p>
          </div>
          <div className="space-y-1.5">
            {data.risk_signals.map((s, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                  s.triggered ? sevColor(s.severity) : "bg-gray-200"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className={`font-medium ${s.triggered ? "text-gray-900" : "text-gray-400"}`}>
                      {s.name}
                    </span>
                    <span className={`text-[10px] tabular-nums ${s.triggered ? "text-gray-600" : "text-gray-300"}`}>
                      {s.current}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={`rounded-lg p-3 border ${
          data.risk_level === "critical" || data.risk_level === "warning"
            ? "bg-red-50 border-red-200"
            : "bg-blue-50 border-blue-200"
        }`}>
          <p className={`text-[10px] font-bold uppercase tracking-wider mb-1 ${
            data.risk_level === "critical" || data.risk_level === "warning"
              ? "text-red-600" : "text-blue-600"
          }`}>
            지금 해야 할 단 1가지
          </p>
          <p className="text-sm font-semibold text-gray-900">{data.survival_action}</p>
        </div>
      </div>
    </div>
  );
}

function NavItem({ label, active, onClick }: { label: string; active?: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex flex-col items-center gap-1">
      <span className={`text-xs font-medium ${active ? "text-yellow-600" : "text-gray-400"}`}>
        {label}
      </span>
      {active && <div className="w-1 h-1 rounded-full bg-yellow-500" />}
    </button>
  );
}
