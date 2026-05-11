"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

const PRO_FEATURES = [
  "월 무제한 쿠폰 발행",
  "실시간 마케팅 인사이트 (4 탭 전부)",
  "AI 사업계획서 초안 월 5회",
  "카카오 알림톡 발송",
  "PDF 진단서 무제한 + CSV/JSON 내보내기",
];

const FREE_FEATURES = [
  "월 3회 쿠폰 발행",
  "주 1회 마케팅 인사이트",
  "기본 폐업 매트릭스",
  "10명 이상 모일 때 사회적 증거",
  "PDF 진단서 월 1회",
];

export default function UpgradePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPro, setIsPro] = useState(false);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.push("/"); return; }
    if (isAuthenticated) {
      api.getSubscriptionStatus()
        .then((s) => { setIsPro(s.is_pro); setExpiresAt(s.expired_at); })
        .catch(() => {});
    }
  }, [isLoading, isAuthenticated, router]);

  const handlePay = async () => {
    setPaying(true);
    setError(null);
    try {
      const ready = await api.readyKakaoPayment();
      // 결제 정보 sessionStorage 저장 (success 페이지에서 사용)
      sessionStorage.setItem("kakao_pay_tid", ready.tid);
      sessionStorage.setItem("kakao_pay_order", ready.partner_order_id);
      // 모바일/PC 분기
      const isMobile = /iPhone|Android|iPad|Mobile/i.test(navigator.userAgent);
      window.location.href = isMobile ? ready.next_redirect_mobile_url : ready.next_redirect_pc_url;
    } catch (err: any) {
      setError(err?.message || "결제 준비가 잠시 막혔어요. 다시 시도해 주세요.");
      setPaying(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 pb-12">
      {/* 헤더 */}
      <header className="bg-white px-5 py-5 sticky top-0 z-10 border-b border-gray-100">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <button
            onClick={() => router.back()}
            aria-label="뒤로"
            className="press-effect w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-lg"
          >
            ←
          </button>
          <h1 className="text-display-sm text-gray-900">SSGI Pro</h1>
        </div>
      </header>

      <div className="max-w-md mx-auto px-5 pt-6 space-y-4">
        {/* 테스트 결제 안내 (정직 라벨) */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">
              테스트 결제
            </span>
            <span className="text-xs text-amber-700 font-semibold">실제 정산 없음</span>
          </div>
          <p className="text-xs text-amber-900 leading-relaxed">
            지금은 카카오페이 테스트 환경이에요. 실제 결제·청구되지 않아요.<br />
            정식 출시는 사업자 가맹 후 (2026 Q3 예정).
          </p>
        </div>

        {/* 활성 구독 — 이미 Pro인 경우 */}
        {isPro && (
          <div className="bg-white rounded-2xl shadow-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold px-2.5 py-1 bg-gray-900 text-white rounded-lg">PRO</span>
              <span className="text-sm text-gray-700 font-semibold">사용 중</span>
            </div>
            {expiresAt && (
              <p className="text-sm text-gray-600">
                {new Date(expiresAt).toLocaleDateString("ko-KR")}까지 이용 가능해요
              </p>
            )}
          </div>
        )}

        {/* Hero */}
        <div className="bg-white rounded-2xl shadow-card p-6">
          <p className="text-xs text-gray-500 mb-1">월 9,900원</p>
          <h2 className="text-2xl font-extrabold text-gray-900 mb-1">
            놓치는 돈, <span className="text-warn-600">하루 330원</span>으로 잡기
          </h2>
          <p className="text-sm text-gray-600 mb-5">
            보조금 5건 평균 240만원 미신청 → Pro 1년 12만원으로 회수
          </p>

          {/* PRO 혜택 */}
          <div className="space-y-2.5 mb-6">
            {PRO_FEATURES.map((f, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className="text-warn-600 text-sm font-bold mt-0.5">✓</span>
                <span className="text-sm text-gray-800">{f}</span>
              </div>
            ))}
          </div>

          {/* 결제 버튼 */}
          {!isPro && (
            <button
              onClick={handlePay}
              disabled={paying}
              className="press-effect w-full flex items-center justify-center gap-2 py-[14px] bg-warn-500 text-gray-900 font-bold rounded-xl shadow-btn hover:bg-warn-600 disabled:opacity-50"
            >
              {paying ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-900 border-t-transparent" />
                  결제 준비 중...
                </>
              ) : (
                "카카오페이로 결제 (테스트)"
              )}
            </button>
          )}
          {error && <p className="mt-3 text-xs text-loss-600">{error}</p>}
          <p className="mt-3 text-xs text-gray-400 text-center">
            결제 시 카카오페이 화면으로 이동해요
          </p>
        </div>

        {/* Free vs Pro 비교 */}
        <div className="bg-white rounded-2xl shadow-card p-5">
          <h3 className="text-base font-bold text-gray-900 mb-4">Free vs Pro</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-bold text-gray-500 uppercase mb-2">Free · 0원</p>
              <ul className="space-y-1.5">
                {FREE_FEATURES.map((f, i) => (
                  <li key={i} className="text-xs text-gray-700">· {f}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-bold text-warn-600 uppercase mb-2">Pro · 9,900원</p>
              <ul className="space-y-1.5">
                {PRO_FEATURES.map((f, i) => (
                  <li key={i} className="text-xs text-gray-900 font-medium">· {f}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* 정직 안내 */}
        <p className="text-center text-xs text-gray-400 pt-2">
          현재 결제는 모두 테스트입니다. 실제 결제 출시는 2026 Q3 예정.
        </p>
      </div>
    </main>
  );
}
