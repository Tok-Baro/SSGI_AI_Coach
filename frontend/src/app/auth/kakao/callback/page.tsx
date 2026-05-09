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
      <div className="flex flex-col items-center justify-center min-h-screen px-6">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="px-6 py-2 bg-gray-100 rounded-lg text-gray-700 hover:bg-gray-200"
        >
          다시 시도하기
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mx-auto mb-4" />
        <p className="text-gray-500">로그인 중...</p>
      </div>
    </div>
  );
}

export default function KakaoCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
        </div>
      }
    >
      <KakaoCallbackContent />
    </Suspense>
  );
}
