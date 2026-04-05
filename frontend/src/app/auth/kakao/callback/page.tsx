"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function KakaoCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("카카오 인증 코드가 없습니다.");
      return;
    }

    login(code)
      .then(() => {
        router.push("/");
      })
      .catch((err) => {
        setError(err.message || "로그인에 실패했습니다.");
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
