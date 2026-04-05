"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { DashboardData } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

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
      api.getDashboard().then(setData).finally(() => setLoading(false));
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  if (!data) return null;

  const handleCompleteAction = async () => {
    if (!data.today_action) return;
    try {
      await api.completeAction(data.today_action.id);
      setData({
        ...data,
        today_action: { ...data.today_action, is_completed: true },
      });
    } catch {}
  };

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      {/* 헤더 */}
      <header className="bg-white px-6 py-4 border-b border-gray-100">
        <p className="text-sm text-gray-500">안녕하세요, {data.user.nickname}님</p>
        <h1 className="text-lg font-bold text-gray-900">{data.user.business_name}</h1>
      </header>

      <div className="px-6 py-4 space-y-4">
        {/* 손실 프레이밍 메시지 */}
        <div className="bg-red-50 border border-red-100 rounded-xl p-4">
          <p className="text-red-600 font-semibold text-sm">{data.loss_message}</p>
          {data.social_proof && (
            <p className="text-red-400 text-xs mt-1">{data.social_proof}</p>
          )}
        </div>

        {/* 위험 점수 */}
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">경영 위험도</span>
            <span className={`text-lg font-bold ${
              data.risk_score > 0.5 ? "text-red-500" : data.risk_score > 0.3 ? "text-yellow-500" : "text-green-500"
            }`}>
              {Math.round(data.risk_score * 100)}점
            </span>
          </div>
          <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                data.risk_score > 0.5 ? "bg-red-500" : data.risk_score > 0.3 ? "bg-yellow-400" : "bg-green-500"
              }`}
              style={{ width: `${data.risk_score * 100}%` }}
            />
          </div>
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
                실행하기
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
              {data.subsidy_matches.map((s, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
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
                </div>
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
        {data.population_trend && (
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
        )}

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

      {/* 하단 네비게이션 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-6 py-3">
        <div className="flex justify-around max-w-sm mx-auto">
          <NavItem label="홈" active onClick={() => {}} />
          <NavItem label="지원사업" onClick={() => router.push("/subsidies")} />
          <NavItem label="쿠폰" onClick={() => router.push("/coupons")} />
          <NavItem label="설정" onClick={() => {}} />
        </div>
      </nav>
    </main>
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
