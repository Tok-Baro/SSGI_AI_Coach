"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import STTButton from "@/components/common/STTButton";
import { koreanWon, koreanChange, koreanDDay } from "@/lib/koreanNumber";
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

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
        <p className="text-base font-semibold text-loss-500 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="press-effect px-6 py-3 bg-gray-100 rounded-2xl font-semibold text-gray-900"
        >
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
    red: { text: "text-loss-500", bg: "bg-loss-500", light: "bg-loss-50" },
    yellow: { text: "text-warn-600", bg: "bg-warn-500", light: "bg-warn-50" },
    green: { text: "text-success-600", bg: "bg-success-500", light: "bg-success-50" },
  };
  const colors = riskColorMap[riskColor];
  const trendLabel = { improving: "개선 중", stable: "유지", worsening: "악화 중" };
  const riskScore100 = Math.round(data.risk_score * 100);
  const riskGrade =
    data.risk_score > 0.7 ? "위험"
    : data.risk_score > 0.5 ? "경고"
    : data.risk_score > 0.3 ? "주의"
    : "안전";

  return (
    <main className="min-h-screen bg-gray-50 pb-24">
      {/* 헤더 */}
      <header className="bg-white px-5 py-4 sticky top-0 z-10">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">
              안녕하세요, {data.user.nickname}님
            </p>
            <h1 className="text-lg font-bold text-gray-900 mt-0.5">
              {data.user.business_name}
            </h1>
          </div>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="press-effect text-sm font-medium text-gray-500 px-4 py-2 bg-gray-100 rounded-xl hover:bg-gray-200"
          >
            로그아웃
          </button>
        </div>
      </header>

      <div className="max-w-md mx-auto px-5 py-5 space-y-3">
        {/* 잠재 지원금 — Hero */}
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
        <div className="bg-white rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-gray-700">우리 가게 위험도</p>
                <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">AI 추정</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                서울시 공식 데이터 · 점수가 높을수록 위험해요
              </p>
            </div>
            <div className="text-right">
              <p className={`text-display-sm tabular-nums ${colors.text}`}>
                {riskGrade}
              </p>
              <p className="text-xs text-gray-500 tabular-nums mt-0.5">
                {riskScore100} / 100
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <DeltaBadge value={data.deltas?.risk_score_delta ?? null} suffix="" inversed scale={100} />
            {data.trend_direction && (
              <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${
                data.trend_direction === "worsening" ? "bg-loss-50 text-loss-600" :
                data.trend_direction === "improving" ? "bg-success-50 text-success-700" :
                "bg-gray-100 text-gray-500"
              }`}>
                {trendLabel[data.trend_direction] || "유지"}
              </span>
            )}
          </div>

          {/* Peer percentile (k≥10일 때만) */}
          {data.peer_percentile !== null && data.peer_percentile !== undefined ? (
            <p className="text-sm text-gray-600 mb-3">
              같은 업종 안에서 <span className="font-bold text-gray-900">상위 {data.peer_percentile}%</span>
              <span className="text-gray-400 ml-1">· {data.peer_sample}명과 비교 (최근 14일 평균)</span>
            </p>
          ) : (
            <p className="text-xs text-gray-400 mb-3">
              같은 업종 사장님 10명이 모이면 비교를 시작해요
            </p>
          )}

          {/* 프로그레스 바 */}
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${colors.bg}`}
              style={{ width: `${data.risk_score * 100}%` }}
            />
          </div>

          {/* 위험도 추이 미니 차트 */}
          {data.risk_trend && data.risk_trend.length > 1 && (
            <div className="mt-4 flex items-end gap-1 h-12">
              {data.risk_trend.slice(-14).map((point, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t-md transition-all ${
                    point.score > 0.5 ? "bg-loss-500/60" : point.score > 0.3 ? "bg-warn-500/60" : "bg-success-500/60"
                  }`}
                  style={{ height: `${Math.max(point.score * 100, 8)}%` }}
                  title={`${point.date}: ${Math.round(point.score * 100)}점`}
                />
              ))}
            </div>
          )}

          <button
            onClick={() => setShowFactors(!showFactors)}
            className="mt-4 text-sm font-medium text-gray-500 hover:text-gray-700 w-full text-center"
          >
            {showFactors ? "요인 분석 접기 ▲" : "요인 분석 보기 ▼"}
          </button>

          {showFactors && data.risk_factors && (
            <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
              {data.risk_factors.map((factor: RiskFactor) => (
                <FactorBar key={factor.name} factor={factor} />
              ))}
            </div>
          )}
        </div>

        {/* 폐업 위험 진단 (Survival Matrix) */}
        <SurvivalMatrixCard />

        {/* 오늘의 액션 — 검정 CTA (1차 액션 명확, Hero 노랑과 분리) */}
        {!data.today_action && (
          <div className="bg-gray-50 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-1 text-xs font-bold bg-gray-900 text-white rounded-lg">
                오늘의 액션
              </span>
              <span className="text-xs text-gray-500">매일 아침 7시</span>
            </div>
            <p className="text-base font-bold text-gray-900 mb-1">
              사장님 첫 액션, 곧 도착해요
            </p>
            <p className="text-sm text-gray-600">
              우리 동네 상권을 분석한 다음, 매일 한 가지만 알려드려요
            </p>
          </div>
        )}
        {data.today_action && (
          <div className="bg-white rounded-2xl p-5 shadow-card">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-1 text-xs font-bold bg-gray-900 text-white rounded-lg">
                오늘의 액션
              </span>
              <span className="text-xs text-gray-400">{data.today_action.action_type}</span>
            </div>
            <h3 className="font-bold text-gray-900 text-lg mb-2 text-balance">
              {data.today_action.title}
            </h3>
            <p className="text-sm text-gray-600 leading-relaxed mb-4">
              {data.today_action.description}
            </p>
            {!data.today_action.is_completed ? (
              <button
                onClick={handleCompleteAction}
                className="press-effect w-full py-[14px] bg-gray-900 text-white font-bold rounded-xl shadow-btn hover:bg-gray-800"
              >
                {data.today_action.cta_type === "apply_subsidy" ? "지원사업 확인하기" :
                 data.today_action.cta_type === "create_coupon" ? "쿠폰 만들기" :
                 "실행하기"}
              </button>
            ) : (
              <>
                <div className="flex items-center justify-center gap-2 py-3 bg-success-50 rounded-xl">
                  <span className="text-success-600 font-bold">✓</span>
                  <p className="text-sm font-bold text-success-700">완료됨</p>
                </div>
                {data.next_action_preview && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs font-semibold text-gray-400 mb-1">
                      다음 후보
                    </p>
                    <p className="text-base font-bold text-gray-900">
                      {data.next_action_preview.title}
                    </p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {data.next_action_preview.subtitle}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* 지원사업 매칭 */}
        {data.subsidy_matches.length === 0 ? (
          <div className="bg-white rounded-2xl p-5 shadow-card">
            <h3 className="font-bold text-gray-900 mb-1">우리 가게 지원사업</h3>
            <p className="text-sm text-gray-600 mb-1">
              지금은 딱 맞는 게 없어요
            </p>
            <p className="text-xs text-gray-400 mb-3">
              새 공고가 올라오면 자동으로 알려드릴게요
            </p>
            <button
              onClick={() => router.push("/subsidies")}
              className="press-effect w-full py-3 bg-gray-100 text-gray-900 font-semibold rounded-xl text-sm hover:bg-gray-200"
            >
              그래도 전체 지원사업 보기 →
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900 text-base">
                매칭 지원사업
              </h3>
              <span className="text-sm font-bold text-loss-500 tabular-nums">
                {data.subsidy_matches.length}건
              </span>
            </div>
            <div className="space-y-2">
              {data.subsidy_matches.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    api.logSubsidySignal(s.id, "click").catch(() => {});
                    router.push("/subsidies");
                  }}
                  className="press-effect w-full p-4 bg-gray-50 rounded-2xl text-left hover:bg-gray-100"
                >
                  <div className="flex justify-between items-start gap-3">
                    <p className="font-bold text-sm text-gray-900 flex-1 min-w-0">
                      {s.title}
                    </p>
                    {s.max_amount && (
                      <span className="text-base font-extrabold text-loss-500 whitespace-nowrap tabular-nums">
                        최대 {s.max_amount}만원
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1.5">{s.organization}</p>
                  {s.days_until_deadline !== null && s.days_until_deadline !== undefined && (
                    <p className="text-xs font-semibold text-loss-500 mt-1.5">
                      {koreanDDay(s.days_until_deadline)}
                    </p>
                  )}
                  {s.match_reasons && s.match_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {s.match_reasons.map((r, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-0.5 bg-warn-50 text-warn-900 rounded-md font-semibold"
                        >
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
              className="press-effect w-full mt-4 py-3 text-sm font-semibold text-warn-600 hover:text-warn-700 bg-warn-50 rounded-xl"
            >
              전체 지원사업 보기
            </button>
          </div>
        )}

        {/* 유동인구 트렌드 */}
        {data.population_trend ? (
          <div className="bg-white rounded-2xl p-5 shadow-card">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              어제 대비 우리 동네 유동인구
            </h3>
            <div className="flex items-baseline gap-2">
              <span className={`text-display-sm tabular-nums ${
                data.population_trend.change_percent > 0 ? "text-success-600" : "text-loss-500"
              }`}>
                {data.population_trend.change_percent > 0 ? "+" : ""}
                {data.population_trend.change_percent}%
              </span>
            </div>
            <p className="text-sm font-semibold text-gray-700 mt-1">
              어제보다 {koreanChange(data.population_trend.change_percent, { up: "더 다녀요", down: "줄었어요" })}
            </p>
            <p className="text-xs text-gray-400 mt-2">
              서울시 생활인구 자료 · 우리 행정동 기준
            </p>
          </div>
        ) : (
          <div className="bg-gray-100 rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-gray-500 mb-1">
              유동인구 트렌드
            </h3>
            <p className="text-xs text-gray-400">
              서울 외 지역은 아직 데이터가 없어요
            </p>
          </div>
        )}

        {/* 이번주 문화행사 */}
        <UpcomingEventsCard events={data.upcoming_events || []} />

        {/* 주간 마케팅 리포트 PDF */}
        <div className="rounded-2xl p-5 bg-gradient-to-br from-gray-900 to-gray-800 text-white shadow-card">
          <p className="text-xs font-semibold text-warn-500 mb-2 uppercase tracking-wider">
            Premium
          </p>
          <h3 className="text-lg font-bold mb-1">이번 주 우리 가게 진단서</h3>
          <p className="text-sm text-gray-300 leading-relaxed mb-4">
            여섯 가지 항목 점수와 진단, 1주·1~3개월·3~6개월 액션 플랜까지 한 장에
          </p>
          {reportError && (
            <p className="text-sm font-medium text-loss-500 mb-3">{reportError}</p>
          )}
          <button
            onClick={handleDownloadReport}
            disabled={reportLoading}
            className="press-effect w-full py-3 bg-white text-gray-900 font-bold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {reportLoading ? "리포트 만드는 중..." : "PDF로 받기"}
          </button>
        </div>

        {/* 쿠폰 통계 */}
        <div className="bg-white rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 text-base">쿠폰 성과</h3>
            <DeltaBadge value={data.deltas?.coupon_scan_delta_pct ?? null} suffix="%" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-display-sm tabular-nums text-gray-900">
                {data.coupon_stats.total_created}
              </p>
              <p className="text-xs text-gray-500 mt-1">발행</p>
            </div>
            <div>
              <p className="text-display-sm tabular-nums text-warn-600">
                {data.coupon_stats.total_scanned}
              </p>
              <p className="text-xs text-gray-500 mt-1">스캔 누적</p>
            </div>
            <div>
              <p className="text-display-sm tabular-nums text-success-600">
                {Math.round(data.action_completion_rate * 100)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">액션 완료율</p>
            </div>
          </div>
        </div>
      </div>

      <STTButton />

      {/* 하단 네비게이션 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-5 py-2 safe-bottom">
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

function FactorBar({ factor }: { factor: RiskFactor }) {
  if (!factor.data_available) {
    return (
      <div className="opacity-50">
        <div className="flex justify-between text-sm mb-1.5">
          <span className="text-gray-400">{factor.label}</span>
          <span className="text-gray-400">데이터 없음</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full" />
      </div>
    );
  }

  const barColor = factor.score > 0.6 ? "bg-loss-500" : factor.score > 0.3 ? "bg-warn-500" : "bg-success-500";

  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-semibold text-gray-700">{factor.label}</span>
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
      <div className="bg-white rounded-2xl p-5 shadow-card">
        <p className="text-sm font-semibold text-gray-700 mb-2">받을 수 있는 지원금</p>
        <p className="text-base text-gray-900">
          지금은 딱 맞는 게 없어요
        </p>
        <p className="text-sm text-gray-400 mt-1">
          새 공고가 뜨면 자동으로 매칭해 드릴게요
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl p-6 bg-gradient-to-br from-warn-500 via-warn-500 to-warn-600 shadow-card overflow-hidden relative">
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-bold text-gray-900">
            받을 수 있는 지원금
          </p>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold px-2.5 py-1 bg-gray-900/10 text-gray-900 rounded-lg">
              매칭 {matchCount}건
            </span>
            <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">최대 합계 추정</span>
          </div>
        </div>
        {/* Hero 숫자: 정밀 콤마 표기 (시각 강조) */}
        <div className="flex items-baseline gap-1 mb-1">
          <span className="text-display-lg tabular-nums text-gray-900">
            {totalAmountWon.toLocaleString()}
          </span>
          <span className="text-xl font-bold text-gray-900">원</span>
        </div>
        {/* 보조 표기: 한국식 만/억 (사람 말투) */}
        <p className="text-base font-semibold text-gray-900/80 mb-3">
          한 달이면 받을 수 있는 {koreanWon(totalAmountWon)} 정도예요
        </p>
        <p className="text-sm text-gray-800 leading-relaxed">
          매칭된 지원사업 최대 금액을 다 더한 값이에요
          {imminentCount > 0 && (
            <span className="block mt-1 font-bold text-loss-700">
              ⚠ 2주 안에 마감되는 사업 {imminentCount}건
            </span>
          )}
        </p>
        {socialProof && (
          <div className="mt-4 pt-4 border-t border-gray-900/10">
            <p className="text-sm text-gray-800">{socialProof}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function UpcomingEventsCard({ events }: { events: UpcomingEvent[] }) {
  if (!events || events.length === 0) return null;
  return (
    <div className="bg-white rounded-2xl p-5 shadow-card">
      <h3 className="font-bold text-gray-900 mb-1">이번 주 우리 동네 이벤트</h3>
      <p className="text-xs text-gray-400 mb-3">
        서울시 문화행사 정보 (자치구 단위)
      </p>
      <div className="space-y-2">
        {events.slice(0, 3).map((e, i) => (
          <a
            key={i}
            href={e.url || "#"}
            target="_blank"
            rel="noreferrer"
            className="press-effect block p-3 bg-gray-50 hover:bg-gray-100 rounded-xl"
          >
            <div className="flex items-baseline justify-between gap-2">
              <p className="font-semibold text-sm text-gray-900 truncate">
                {e.title}
              </p>
              {e.start_date && (
                <span className="text-xs text-gray-500 whitespace-nowrap tabular-nums">
                  {e.start_date.slice(0, 10)}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5 truncate">
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
  const color = isGood ? "bg-success-50 text-success-700" : "bg-loss-50 text-loss-600";
  const arrow = isUp ? "▲" : "▼";
  const formatted = scale === 1 ? display.toFixed(1) : Math.round(display).toString();
  return (
    <span className={`text-xs px-2 py-1 rounded-lg font-bold ${color} tabular-nums`}>
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
      <div className="bg-white rounded-2xl p-5 shadow-card">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-200 border-t-warn-500" />
          <span className="text-sm text-gray-500">우리 가게 진단 보는 중...</span>
        </div>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="bg-gray-100 rounded-2xl p-5">
        <p className="text-sm text-gray-500">진단 결과를 불러오지 못했어요</p>
      </div>
    );
  }

  const levelStyle = {
    safe: { gradient: "from-success-500 to-success-600", chip: "bg-white/20" },
    watch: { gradient: "from-gray-700 to-gray-800", chip: "bg-white/20" },
    warning: { gradient: "from-warn-500 to-loss-500", chip: "bg-white/20" },
    critical: { gradient: "from-loss-500 to-loss-700", chip: "bg-white/20" },
  }[data.risk_level];

  const sevColor = (s: string) =>
    s === "high" ? "bg-loss-500" : s === "medium" ? "bg-warn-500" : "bg-gray-300";

  const pos = data.your_position;
  const showPositionBar =
    pos.operating_months !== null && pos.closed_avg_months > 0;
  const positionPct = pos.operating_percentile !== null ? Math.min(130, pos.operating_percentile) : 0;

  return (
    <div className="bg-white rounded-2xl shadow-card overflow-hidden">
      <div className={`bg-gradient-to-br ${levelStyle.gradient} px-5 py-5`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-white/90 uppercase tracking-wider">
              우리 가게 폐업 위험도
            </span>
            <span className="text-[10px] px-1.5 py-0.5 bg-white/30 text-white rounded font-medium">AI 추정</span>
          </div>
          <span className={`text-xs px-2.5 py-1 ${levelStyle.chip} text-white rounded-lg font-bold`}>
            {data.risk_label}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-display-lg tabular-nums text-white">
            {data.survival_score}
          </span>
          <span className="text-base font-semibold text-white/80">/ 100</span>
        </div>
        <p className="text-xs text-white/80 mt-1">
          비슷하게 폐업한 가게와 패턴 일치율 {data.pattern_similarity_pct}%
        </p>
      </div>

      <div className="p-5 space-y-4">
        <p className="text-base font-bold text-gray-900 text-balance">
          {data.headline}
        </p>

        {showPositionBar && (
          <div>
            <div className="flex justify-between text-xs text-gray-500 mb-1.5">
              <span>우리 가게 {pos.operating_months}개월</span>
              <span>폐업 평균 {pos.closed_avg_months}개월</span>
            </div>
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div className="absolute top-0 bottom-0 bg-loss-100" style={{ left: "53%", right: "0%" }} />
              <div
                className={`absolute top-0 bottom-0 w-1 ${
                  positionPct >= 70 ? "bg-loss-500" : "bg-success-500"
                }`}
                style={{ left: `${(positionPct / 130) * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1.5">
              폐업 평균의 {pos.operating_percentile} 지점에 있어요 · 빨간 구간이 위험권이에요
            </p>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-2.5">
            <p className="text-sm font-bold text-gray-700">감지된 위험 신호</p>
            <p className="text-xs text-gray-500">
              <span className={`font-bold tabular-nums ${data.triggered_count >= 3 ? "text-loss-600" : "text-gray-700"}`}>
                {data.triggered_count}
              </span>
              <span className="text-gray-400"> / 전체 {data.total_signals}개</span>
            </p>
          </div>
          <div className="space-y-2">
            {data.risk_signals.map((s, i) => (
              <div key={i} className="flex items-start gap-2.5 text-sm">
                <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${
                  s.triggered ? sevColor(s.severity) : "bg-gray-200"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className={`font-semibold ${s.triggered ? "text-gray-900" : "text-gray-400"}`}>
                      {s.name}
                    </span>
                    <span className={`text-xs tabular-nums ${s.triggered ? "text-gray-600" : "text-gray-300"}`}>
                      {s.current}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={`rounded-xl p-4 ${
          data.risk_level === "critical" || data.risk_level === "warning"
            ? "bg-loss-50"
            : "bg-success-50"
        }`}>
          <p className={`text-xs font-bold uppercase tracking-wider mb-1.5 ${
            data.risk_level === "critical" || data.risk_level === "warning"
              ? "text-loss-600" : "text-success-700"
          }`}>
            오늘 사장님이 할 단 한 가지
          </p>
          <p className="text-base font-bold text-gray-900 text-balance">
            {data.survival_action}
          </p>
        </div>
      </div>
    </div>
  );
}

function NavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="press-effect flex flex-col items-center gap-0.5 px-3 py-2"
    >
      <span className={`text-base ${active ? "" : "grayscale opacity-50"}`}>
        {icon}
      </span>
      <span className={`text-xs font-bold ${active ? "text-gray-900" : "text-gray-400"}`}>
        {label}
      </span>
    </button>
  );
}
