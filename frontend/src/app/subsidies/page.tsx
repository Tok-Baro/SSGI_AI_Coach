"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { SubsidyMatchesResponse, ApplyDraftResponse } from "@/types";

export default function SubsidiesPage() {
  const router = useRouter();
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

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <header className="bg-white px-6 py-4 border-b border-gray-100 flex items-center gap-3">
        <button onClick={() => router.back()} className="text-gray-500">&larr;</button>
        <h1 className="text-lg font-bold text-gray-900">지원사업 매칭</h1>
      </header>

      <div className="px-6 py-4">
        {data && (
          <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-4">
            <p className="text-red-600 font-semibold text-sm">{data.loss_message}</p>
          </div>
        )}

        <div className="space-y-3">
          {data?.matches.map((s) => (
            <div key={s.id} className="bg-white rounded-xl p-4 border border-gray-100">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900 text-sm flex-1">{s.title}</h3>
                {s.max_amount && (
                  <span className="text-sm font-bold text-red-500 ml-2">{s.max_amount}만원</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mb-1">{s.organization}</p>
              {s.eligibility_summary && (
                <p className="text-xs text-gray-600 mb-2">{s.eligibility_summary}</p>
              )}
              <div className="flex items-center gap-2 mb-3">
                {s.days_until_deadline !== null && s.days_until_deadline !== undefined && (
                  <span className="text-xs px-2 py-0.5 bg-red-100 text-red-600 rounded-full font-medium">
                    마감 D-{s.days_until_deadline}
                  </span>
                )}
                {s.social_proof_message && (
                  <span className="text-xs text-gray-400">{s.social_proof_message}</span>
                )}
              </div>
              <div className="flex gap-2">
                {s.application_url && (
                  <a
                    href={s.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => api.logSubsidySignal(s.id, "apply").catch(() => {})}
                    className="flex-1 py-2 text-center text-sm bg-yellow-400 text-gray-900 font-semibold rounded-lg hover:bg-yellow-500"
                  >
                    신청 페이지
                  </a>
                )}
                <button
                  onClick={() => handleGenerateDraft(s.id)}
                  className="flex-1 py-2 text-center text-sm bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200"
                >
                  사업계획서 초안
                </button>
              </div>
            </div>
          ))}
        </div>

        {data?.matches.length === 0 && (
          <p className="text-center text-gray-400 py-12">매칭되는 지원사업이 없습니다.</p>
        )}
      </div>

      {/* 사업계획서 초안 모달 */}
      {(draft || draftLoading) && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end">
          <div className="bg-white w-full max-h-[80vh] rounded-t-2xl p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg text-gray-900">
                {draft ? draft.subsidy_title : "생성 중..."}
              </h2>
              <button onClick={() => { setDraft(null); setDraftLoading(false); setDraftError(null); }} className="text-gray-400 hover:text-gray-600 text-xl">
                &times;
              </button>
            </div>
            {draftError && (
              <p className="text-red-500 text-sm mb-3">{draftError}</p>
            )}
            {draftLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-400" />
                <span className="text-gray-500">GPT-4o가 사업계획서를 작성하고 있어요...</span>
              </div>
            ) : draft ? (
              <div>
                <p className="text-xs text-green-600 mb-3">절약 시간: {draft.estimated_time_saved}</p>
                <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-700">
                  {draft.draft_text}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </main>
  );
}
