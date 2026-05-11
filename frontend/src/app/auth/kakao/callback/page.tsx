"use client";

import { Suspense } from "react";
import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

function KakaoCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  // 카카오 OAuth code는 일회용 — StrictMode/리렌더로 useEffect 2회 실행 시 중복 사용 방지
  const handledRef = useRef(false);

  useEffect(() => {
    if (handledRef.current) return;
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    if (!code) {
      setError("카카오 인증 코드가 없습니다.");
      return;
    }
    // OAuth state CSRF 검증 (RFC 6749 §10.12)
    const expected = sessionStorage.getItem("oauth_state");
    sessionStorage.removeItem("oauth_state");
    if (expected && (!state || state !== expected)) {
      setError("보안 검증에 실패했습니다. 처음부터 다시 시도해주세요.");
      return;
    }
    handledRef.current = true;

    login(code)
      .then(() => {
        router.push("/");
      })
      .catch((err) => {
        setError(err.message || "로그인에 실패했습니다.");
        // 실패 시에는 다시 시도 가능하도록 가드 해제
        handledRef.current = false;
      });
  }, [searchParams, login, router]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
        <div className="w-14 h-14 mb-4 rounded-full bg-loss-50 flex items-center justify-center text-2xl">
          ⚠
        </div>
        <p className="text-base font-bold text-gray-900 mb-2 text-center">로그인에 실패했어요</p>
        <p className="text-sm text-loss-500 mb-6 text-center">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="press-effect px-6 py-3 bg-warn-500 text-gray-900 font-bold rounded-2xl shadow-btn"
        >
          다시 시도하기
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-200 border-t-warn-500 mx-auto mb-4" />
        <p className="text-base font-semibold text-gray-700">로그인하고 있어요</p>
        <p className="text-xs text-gray-400 mt-1">2초만 기다려 주세요</p>
      </div>
    </div>
  );
}

export default function KakaoCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen bg-white">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-200 border-t-warn-500" />
        </div>
      }
    >
      <KakaoCallbackContent />
    </Suspense>
  );
}
