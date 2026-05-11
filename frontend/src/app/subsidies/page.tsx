"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { koreanDDay } from "@/lib/koreanNumber";
import type { SubsidyMatchesResponse, ApplyDraftResponse } from "@/types";

export default function SubsidiesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [data, setData] = useState<SubsidyMatchesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<ApplyDraftResponse | null>(null);
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.push("/"); return; }
    if (isAuthenticated) {
      api.getSubsidyMatches()
        .then(setData)
        .catch((err) => setError(err.message || "데이터를 불러오지 못했습니다."))
        .finally(() => setLoading(false));
    }
  }, [isLoading, isAuthenticated, router]);

  const handleGenerateDraft = async (subsidyId: string) => {
    setDraftLoading(true);
    setDraft(null);
    setDraftError(null);
    try {
      const res = await api.generateApplyDraft(subsidyId);
      setDraft(res);
    } catch (err: any) {
      setDraftError(err.message || "사업계획서 생성에 실패했습니다.");
    }
    setDraftLoading(false);
  };

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

  return (
    <main className="min-h-screen bg-gray-50 pb-24">
      <header className="bg-white px-5 py-5 sticky top-0 z-10">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="press-effect w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-lg"
            aria-label="뒤로"
          >
            ←
          </button>
          <h1 className="text-display-sm text-gray-900">우리 가게 지원사업</h1>
        </div>
      </header>

      <div className="max-w-md mx-auto px-5 py-5">
        {data && data.loss_message && (
          <div className="bg-loss-50 rounded-2xl p-4 mb-4">
            <p className="text-loss-600 font-bold text-sm leading-relaxed">
              {data.loss_message}
            </p>
          </div>
        )}

        <div className="space-y-3">
          {data?.matches.map((s) => (
            <div key={s.id} className="bg-white rounded-2xl p-5 shadow-card">
              <div className="flex justify-between items-start gap-3 mb-2">
                <h3 className="font-bold text-gray-900 text-base flex-1 leading-snug">
                  {s.title}
                </h3>
                {s.max_amount && (
                  <span className="text-lg font-extrabold text-loss-500 whitespace-nowrap tabular-nums">
                    최대 {s.max_amount}만원
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 mb-2">{s.organization}</p>
              {s.eligibility_summary && (
                <p className="text-sm text-gray-700 leading-relaxed mb-3">
                  {s.eligibility_summary}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                {s.days_until_deadline !== null && s.days_until_deadline !== undefined && (
                  <span className="text-xs px-2.5 py-1 bg-loss-100 text-loss-700 rounded-lg font-bold">
                    {koreanDDay(s.days_until_deadline)}
                  </span>
                )}
                {s.social_proof_message && (
                  <span className="text-xs text-gray-400">{s.social_proof_message}</span>
                )}
              </div>
              {/* CTA 위계: 신청(1차, flex-1) vs 초안(보조, 좁게) */}
              <div className="flex gap-2">
                {s.application_url && (
                  <a
                    href={s.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => api.logSubsidySignal(s.id, "apply").catch(() => {})}
                    className="press-effect flex-1 py-3 text-center text-sm bg-warn-500 text-gray-900 font-bold rounded-xl shadow-btn"
                  >
                    신청하기 →
                  </a>
                )}
                <button
                  onClick={() => handleGenerateDraft(s.id)}
                  className="press-effect flex-shrink-0 px-4 py-3 text-center text-sm bg-white border border-gray-200 text-gray-700 font-medium rounded-xl"
                >
                  초안 받기
                </button>
              </div>
            </div>
          ))}
        </div>

        {data?.matches.length === 0 && (
          <div className="bg-white rounded-2xl p-10 text-center shadow-card">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center text-3xl">
              🔍
            </div>
            <p className="text-base font-bold text-gray-900 mb-2">
              지금은 딱 맞는 게 없네요
            </p>
            <p className="text-sm text-gray-500 leading-relaxed mb-6">
              사장님 업종·지역에 맞는 사업이 아직 없어요.
              <br />새 공고가 뜨면 카톡으로 바로 알려드릴게요.
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="press-effect w-full py-3 bg-gray-100 text-gray-900 font-bold rounded-xl"
            >
              대시보드로 돌아가기
            </button>
          </div>
        )}
      </div>

      {/* 사업계획서 초안 모달 */}
      {(draft || draftLoading) && (
        <div className="fixed inset-0 bg-gray-900/40 z-50 flex items-end backdrop-blur-sm">
          <div className="bg-white w-full max-w-md mx-auto max-h-[85vh] rounded-t-3xl p-6 overflow-y-auto">
            <div className="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-5" />
            <div className="flex justify-between items-start gap-3 mb-5">
              <h2 className="text-xl font-bold text-gray-900 flex-1 leading-snug">
                {draft ? draft.subsidy_title : "생성 중..."}
              </h2>
              <button
                onClick={() => {
                  setDraft(null);
                  setDraftLoading(false);
                  setDraftError(null);
                }}
                className="press-effect w-10 h-10 flex-shrink-0 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 text-lg"
                aria-label="닫기"
              >
                ✕
              </button>
            </div>
            {draftError && (
              <div className="bg-loss-50 rounded-xl p-3 mb-4">
                <p className="text-loss-500 text-sm font-medium">{draftError}</p>
              </div>
            )}
            {draftLoading ? (
              <div className="flex flex-col items-center gap-3 py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
                <span className="text-sm font-semibold text-gray-700">
                  사업계획서 초안을 쓰고 있어요
                </span>
                <span className="text-xs text-gray-400">10초만 기다려 주세요...</span>
              </div>
            ) : draft ? (
              <div>
                <div className="inline-block bg-success-50 px-3 py-1.5 rounded-lg mb-4">
                  <p className="text-xs font-bold text-success-700">
                    ⏱ 절약 시간 · {draft.estimated_time_saved}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-2xl p-5 whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
                  {draft.draft_text}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* 하단 네비게이션 */}
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
      <span className={`text-base ${active ? "" : "grayscale opacity-50"}`}>{icon}</span>
      <span className={`text-xs font-bold ${active ? "text-gray-900" : "text-gray-400"}`}>
        {label}
      </span>
    </button>
  );
}
