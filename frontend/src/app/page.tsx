"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

// OAuth state 파라미터 발급 (CSRF 방어, RFC 6749 §10.12)
function buildKakaoUrl(): string {
  if (typeof window === "undefined") return "#";
  // crypto.randomUUID 폴리필 fallback (구형 브라우저 대응)
  const rand =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
  sessionStorage.setItem("oauth_state", rand);
  const params = new URLSearchParams({
    client_id: process.env.NEXT_PUBLIC_KAKAO_REST_API_KEY || "",
    redirect_uri:
      process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI ||
      "http://localhost:3000/auth/kakao/callback",
    response_type: "code",
    scope: "profile_nickname,profile_image,account_email",
    state: rand,
  });
  return `https://kauth.kakao.com/oauth/authorize?${params.toString()}`;
}

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user, checkAuth } = useAuth();
  const [kakaoUrl, setKakaoUrl] = useState("#");

  useEffect(() => {
    checkAuth();
    setKakaoUrl(buildKakaoUrl());
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (user.onboarding_completed) {
        router.push("/dashboard");
      } else {
        router.push("/onboarding");
      }
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-6 py-12">
      {/* 헤더 */}
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          AI 경영코치
        </h1>
        <p className="text-lg text-gray-600">
          사장님이 모르고 놓치는 돈, AI가 찾아줍니다.
        </p>
      </div>

      {/* 가치 제안 카드 */}
      <div className="w-full max-w-sm space-y-4 mb-12">
        <ValueCard
          title="지원금 자동 매칭"
          description="연 400~700만원 지원사업, 자격 자동 판별"
          highlight="놓치면 내년까지 없어요"
        />
        <ValueCard
          title="유동인구 기반 이벤트"
          description="QR 쿠폰 1탭 생성 + 카카오톡 발송"
          highlight="이벤트 없이 지나가고 있어요"
        />
        <ValueCard
          title="경쟁 가게 모니터링"
          description="같은 동네 개폐업 알림 + AI 대응 전략"
          highlight="옆 가게는 이미 시작했어요"
        />
      </div>

      {/* 카카오 로그인 버튼 */}
      <a
        href={kakaoUrl}
        className="w-full max-w-sm flex items-center justify-center gap-2 bg-[#FEE500] text-[#191919] font-semibold py-4 rounded-xl hover:bg-[#FDD835] transition-colors"
      >
        <KakaoIcon />
        카카오로 15초 만에 시작하기
      </a>

      <p className="mt-4 text-xs text-gray-400">
        카카오 로그인 + 상호명 입력 = 15초
      </p>
    </main>
  );
}

function ValueCard({
  title,
  description,
  highlight,
}: {
  title: string;
  description: string;
  highlight: string;
}) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-2">{description}</p>
      <p className="text-sm font-medium text-red-500">{highlight}</p>
    </div>
  );
}

function KakaoIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path
        d="M10 3C5.58 3 2 5.79 2 9.25c0 2.18 1.45 4.1 3.63 5.2l-.93 3.45c-.08.3.26.54.52.37l4.12-2.72c.22.02.44.03.66.03 4.42 0 8-2.79 8-6.25S14.42 3 10 3z"
        fill="#191919"
      />
    </svg>
  );
}
