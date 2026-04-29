"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import STTButton from "@/components/common/STTButton";
import type { DashboardData, RiskFactor } from "@/types";

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
      // cta_type에 따라 해당 기능 페이지로 이동
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
        {/* 손실 프레이밍 메시지 */}
        <div className="bg-red-50 border border-red-100 rounded-xl p-4">
          <p className="text-red-600 font-semibold text-sm">{data.loss_message}</p>
          {data.social_proof && (
            <p className="text-red-400 text-xs mt-1">{data.social_proof}</p>
          )}
        </div>

        {/* 복합 위험도 */}
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">경영 위험도</span>
            <div className="flex items-center gap-2">
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
                {Math.round(data.risk_score * 100)}점
              </span>
            </div>
          </div>

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

          {/* 요인 분석 토글 */}
          <button
            onClick={() => setShowFactors(!showFactors)}
            className="mt-3 text-xs text-gray-400 hover:text-gray-600 w-full text-center"
          >
            {showFactors ? "요인 분석 접기" : "요인 분석 보기"}
          </button>

          {/* 요인 분석 상세 */}
          {showFactors && data.risk_factors && (
            <div className="mt-3 space-y-2.5">
              {data.risk_factors.map((factor: RiskFactor) => (
                <FactorBar key={factor.name} factor={factor} />
              ))}
            </div>
          )}
        </div>

        {/* 오늘의 액션 */}
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
              <p className="text-center text-sm text-green-600 font-medium">완료됨</p>
            )}
          </div>
        )}

        {/* 지원사업 매칭 */}
        {data.subsidy_matches.length > 0 && (
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
          </div>
        ) : (
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
            <h3 className="font-semibold text-gray-400 mb-1">유동인구 트렌드</h3>
            <p className="text-xs text-gray-400">서울 외 지역은 유동인구 데이터를 제공하지 않습니다</p>
          </div>
        )}

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
          <h3 className="font-semibold text-gray-900 mb-2">쿠폰 성과</h3>
          <div className="flex gap-4">
            <div>
              <p className="text-2xl font-bold text-gray-900">{data.coupon_stats.total_created}</p>
              <p className="text-xs text-gray-500">발행</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">{data.coupon_stats.total_scanned}</p>
              <p className="text-xs text-gray-500">스캔</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">{Math.round(data.action_completion_rate * 100)}%</p>
              <p className="text-xs text-gray-500">액션 완료율</p>
            </div>
          </div>
        </div>
      </div>

      {/* STT 음성 질의 버튼 */}
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

function NavItem({ label, active, onClick }: { label: string; active?: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`text-xs font-medium py-1 ${active ? "text-yellow-600" : "text-gray-400"}`}
    >
      {label}
    </button>
  );
}
