"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";

// OAuth state 파라미터 발급 (CSRF 방어, RFC 6749 §10.12)
function buildKakaoUrl(): string {
  if (typeof window === "undefined") return "#";
  const rand =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2) + Date.now().toString(36);
  const clientId = process.env.NEXT_PUBLIC_KAKAO_REST_API_KEY;
  if (!clientId) return "#"; // silent fail 방지 — 호출 측에서 disabled 처리
  sessionStorage.setItem("oauth_state", rand);
  const params = new URLSearchParams({
    client_id: clientId,
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
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => {
    checkAuth();
    setKakaoUrl(buildKakaoUrl());
  }, [checkAuth]);

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    try {
      const r = await api.demoLogin();
      api.setTokens(r.access_token, r.refresh_token);
      useAuth.setState({
        user: r.user,
        isAuthenticated: true,
        isLoading: false,
        _hasChecked: true,
      });
      router.push("/dashboard");
    } catch {
      setDemoLoading(false);
      alert("데모 진입에 실패했어요. 잠시 후 다시 시도해 주세요.");
    }
  };

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
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-white flex flex-col">
      <div className="flex-1 flex flex-col px-5 pt-16 pb-8 max-w-md mx-auto w-full">
        {/* 헤더 */}
        <div className="mb-12">
          <p className="text-base font-medium text-warn-600 mb-3">
            AI 경영코치
          </p>
          <h1 className="text-display text-gray-900 text-balance">
            사장님이 모르고
            <br />
            놓치는 돈,
            <br />
            <span className="text-loss-500">AI가 찾아드려요.</span>
          </h1>
          <p className="mt-5 text-base text-gray-600 leading-relaxed">
            지원금부터 단골 만들기까지,
            <br />
            매일 아침 7시, 우리 가게에 맞는 액션 1개를 알려드려요.
          </p>
        </div>

        {/* 가치 제안 카드 */}
        <div className="space-y-3 mb-10">
          <ValueCard
            icon="💰"
            title="지원금 자동 매칭"
            description="우리 가게에 맞는 사업만 골라서, 자격까지 알아서 확인"
            highlight="신청 안 하면 내년까지 없어요"
          />
          <ValueCard
            icon="📍"
            title="유동인구 보고 이벤트 추천"
            description="손님 몰리는 시간대에 맞춰 QR 쿠폰을 카톡으로 한 번에"
            highlight="이대로 지나가면 그냥 끝이에요"
          />
          <ValueCard
            icon="👀"
            title="옆 가게 동향 알림"
            description="같은 동네에 새 가게가 열리면 바로 알림 + 대응 전략"
            highlight="옆 가게는 이미 시작했어요"
          />
        </div>

        <div className="flex-1" />

        {/* 카카오 로그인 버튼 — client_id 누락 시 disabled (silent fail 방지) */}
        {kakaoUrl === "#" ? (
          <button
            disabled
            aria-label="카카오 로그인 준비 중"
            className="w-full flex items-center justify-center gap-2 bg-gray-200 text-gray-500 font-bold text-base py-[18px] rounded-2xl cursor-not-allowed"
          >
            <KakaoIcon />
            잠시 후 다시 시도해 주세요
          </button>
        ) : (
          <a
            href={kakaoUrl}
            aria-label="카카오 계정으로 15초 만에 시작하기"
            className="press-effect w-full flex items-center justify-center gap-2 bg-warn-500 text-gray-900 font-bold text-base py-[18px] rounded-2xl shadow-btn hover:bg-warn-600"
          >
            <KakaoIcon />
            카카오로 15초 만에 시작하기
          </a>
        )}
        <p className="mt-3 text-center text-xs text-gray-400">
          가입 = 카카오 로그인 + 상호명 입력 (15초 소요)
        </p>

        {/* 심사위원 체험 — 로그인 없이 데모 계정으로 둘러보기 */}
        <button
          onClick={handleDemoLogin}
          disabled={demoLoading}
          className="press-effect mt-4 w-full py-3 rounded-2xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          {demoLoading ? "데모 준비 중…" : "심사위원 체험하기 — 로그인 없이 둘러보기"}
        </button>
        <p className="mt-2 text-center text-[11px] text-gray-300">
          가공 데이터(관악구 신림동 학원 예시)로 모든 화면을 미리 볼 수 있어요
        </p>
      </div>
    </main>
  );
}

function ValueCard({
  icon,
  title,
  description,
  highlight,
}: {
  icon: string;
  title: string;
  description: string;
  highlight: string;
}) {
  return (
    <div className="bg-gray-50 rounded-2xl p-5">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-white flex items-center justify-center text-xl">
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 text-base mb-1">{title}</h3>
          <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
          <p className="mt-2 text-sm font-semibold text-loss-500">
            {highlight}
          </p>
        </div>
      </div>
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
