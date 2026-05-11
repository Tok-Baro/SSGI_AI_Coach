"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { requestFCMToken } from "@/lib/firebase";
import { normalizeBusinessType } from "@/lib/businessType";
import type { KakaoLocalSearchResult, IndustryPackInfo } from "@/types";

// 카카오 카테고리/업종명을 업종 지식팩 keywords 와 매칭해 기본 선택값을 고른다 (백엔드 분류 규칙 미러).
function guessIndustrySlug(rawType: string, businessType: string, packs: IndustryPackInfo[]): string {
  const texts = [rawType, businessType].filter(Boolean).map((t) => t.toLowerCase());
  if (texts.length === 0) return "";
  for (const p of [...packs].sort((a, b) => a.priority - b.priority)) {
    for (const kw of p.keywords || []) {
      if (texts.some((t) => t.includes(kw.toLowerCase()))) return p.id;
    }
  }
  return "";
}

type Step = "business_number" | "business_search" | "confirm" | "loading" | "done";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth, refreshUser } = useAuth();
  const [step, setStep] = useState<Step>("business_number");
  const [businessNumber, setBusinessNumber] = useState("");
  const [businessStatus, setBusinessStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KakaoLocalSearchResult[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<KakaoLocalSearchResult | null>(null);
  const [verificationToken, setVerificationToken] = useState("");
  const [businessStartDate, setBusinessStartDate] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ subsidy_count: number; message: string } | null>(null);
  const [industries, setIndustries] = useState<IndustryPackInfo[]>([]);
  const [industrySlug, setIndustrySlug] = useState(""); // "" = 자동 감지

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    api.getIndustries().then(setIndustries).catch(() => {});
  }, []);

  // 가게를 고르면 카테고리에서 기본 업종을 추정해 선택값 채움 (사용자가 바꿀 수 있음)
  useEffect(() => {
    if (!selectedBusiness || industries.length === 0) return;
    const cats = selectedBusiness.category_name.split(" > ");
    const rawType = cats.length >= 2 ? cats[1] : cats[0];
    setIndustrySlug(guessIndustrySlug(rawType, normalizeBusinessType(rawType), industries));
  }, [selectedBusiness, industries]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
    if (!isLoading && isAuthenticated && user?.onboarding_completed) {
      router.push("/dashboard");
    }
  }, [isLoading, isAuthenticated, user, router]);

  // Step 1: 사업자번호 검증
  const handleVerifyBusiness = async () => {
    if (businessNumber.length !== 10) {
      setError("사업자번호 10자리를 입력해주세요.");
      return;
    }
    setError("");
    try {
      const res = await api.verifyBusiness(businessNumber);
      if (res.is_valid && res.verification_token) {
        setBusinessStatus(res.business_status);
        setVerificationToken(res.verification_token);
        setStep("business_search");
      } else {
        // 사장님 친화 — raw status 노출 안 함 (human-tone 룰)
        const statusCopy: Record<string, string> = {
          "폐업자": "폐업으로 등록된 사업자번호예요. 다른 번호로 다시 시도해 주세요.",
          "휴업자": "휴업 상태예요. 사업자 재개 후 다시 시도해 주세요.",
        };
        setError(statusCopy[res.business_status] ?? "이 번호는 지금 이용이 어려워요. 사업자번호를 다시 확인해 주세요.");
      }
    } catch (err: any) {
      setError(err.message || "잠시 통신이 불안정해요. 한 번 더 눌러 주세요.");
    }
  };

  // Step 2: 상호명 검색
  const handleSearch = useCallback(async () => {
    if (searchQuery.length < 1) return;
    try {
      const results = await api.searchBusiness(searchQuery);
      setSearchResults(results);
    } catch {
      setSearchResults([]);
    }
  }, [searchQuery]);

  useEffect(() => {
    const timer = setTimeout(handleSearch, 500);
    return () => clearTimeout(timer);
  }, [searchQuery, handleSearch]);

  const handleSelectBusiness = (biz: KakaoLocalSearchResult) => {
    setSelectedBusiness(biz);
    setStep("confirm");
  };

  // Step 3: 온보딩 완료
  const handleComplete = async () => {
    if (!selectedBusiness) return;
    setStep("loading");
    setError("");

    // 카테고리에서 업종 추출 + canonical taxonomy 정규화
    // 예: "음식점 > 한식 > 백반" → "한식" → normalize → "음식점"
    const categories = selectedBusiness.category_name.split(" > ");
    const rawType = categories.length >= 2 ? categories[1] : categories[0];
    const businessType = normalizeBusinessType(rawType);

    // 주소에서 동명, 구명 추출 (지번주소 + 도로명주소 모두 탐색)
    const allAddressParts = [
      ...selectedBusiness.address_name.split(" "),
      ...(selectedBusiness.road_address_name || "").split(" "),
    ];
    const guName = allAddressParts.find((p) => /^[가-힣]+구$/.test(p)) || "";
    // "동" 또는 "가"로 끝나는 행정동 (삼선동2가, 역삼1동 등)
    const dongName = allAddressParts.find((p) => /^[가-힣]{2,}[0-9]*동[0-9]*$/.test(p))
      || allAddressParts.find((p) => /^[가-힣]{2,}[0-9]*가$/.test(p))
      || "";

    try {
      const res = await api.completeOnboarding({
        business_number: businessNumber,
        verification_token: verificationToken,
        business_name: selectedBusiness.place_name,
        business_type: businessType,
        industry_slug: industrySlug || undefined,
        address: selectedBusiness.road_address_name || selectedBusiness.address_name,
        dong_name: dongName,
        gu_name: guName,
        lat: parseFloat(selectedBusiness.y),
        lng: parseFloat(selectedBusiness.x),
        business_start_date: businessStartDate || undefined,
      });
      setResult({ subsidy_count: res.subsidy_count, message: res.message });
      setStep("done");

      // 유저 정보 갱신 (onboarding_completed=true 반영)
      await refreshUser();

      // FCM 푸시 알림 등록 (비동기, 실패 무시)
      requestFCMToken().then((token) => {
        if (token) api.registerFcmToken(token).catch(() => {});
      }).catch(() => {});
    } catch (err: any) {
      setError(err.message || "정보 등록이 잠시 막혔어요. 한 번 더 눌러 주세요.");
      setStep("confirm");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  // 단계 진행률 (P1-6: stepper 표시)
  const stepIdx =
    step === "business_number" ? 1
    : step === "business_search" ? 2
    : 3;
  const stepLabel =
    step === "business_number" ? "사업자등록번호 확인"
    : step === "business_search" ? "가게 검색"
    : "사업장 정보 확인";

  return (
    <main className="min-h-screen bg-white">
      <div className="max-w-md mx-auto px-5 pt-12 pb-8">
        <h1 className="text-display-sm text-gray-900 mb-2">
          사장님 가게부터 알려주세요
        </h1>
        <p className="text-base text-gray-600 mb-8">15초만 쓰시면 끝나요</p>

        {/* Stepper */}
        {step !== "loading" && step !== "done" && (
          <div className="mb-10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold text-gray-900 tabular-nums">
                <span className="text-warn-600">{stepIdx}</span>
                <span className="text-gray-400"> / 3</span>
              </span>
              <span className="text-sm font-medium text-gray-600">{stepLabel}</span>
            </div>
            <div className="flex gap-1.5">
              {[1, 2, 3].map((n) => (
                <div
                  key={n}
                  className={`flex-1 h-1 rounded-full transition-colors ${
                    n <= stepIdx ? "bg-warn-500" : "bg-gray-200"
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Step 1: 사업자번호 */}
        {step === "business_number" && (
          <div>
            <label className="block text-base font-bold text-gray-900 mb-2">
              사업자등록번호
            </label>
            <p className="text-sm text-gray-500 mb-4">
              하이픈 없이 10자리 숫자만 입력해 주세요
            </p>
            <input
              type="text"
              inputMode="numeric"
              maxLength={10}
              value={businessNumber}
              onChange={(e) => setBusinessNumber(e.target.value.replace(/\D/g, ""))}
              placeholder="0000000000"
              className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-xl text-gray-900 tabular-nums tracking-wide focus:outline-none focus:ring-2 focus:ring-warn-500 focus:bg-white border-2 border-transparent focus:border-warn-500"
            />
            {error && (
              <p className="mt-3 text-sm font-medium text-loss-500">{error}</p>
            )}
            <button
              onClick={handleVerifyBusiness}
              disabled={businessNumber.length !== 10}
              className="press-effect w-full mt-6 py-[18px] bg-warn-500 text-gray-900 font-bold text-base rounded-2xl shadow-btn disabled:opacity-40 disabled:cursor-not-allowed hover:bg-warn-600"
            >
              다음
            </button>
          </div>
        )}

        {/* Step 2: 상호명 검색 */}
        {step === "business_search" && (
          <div>
            <div className="flex items-center gap-2 mb-6 px-3 py-2 bg-success-50 rounded-xl">
              <span className="text-success-600 font-bold">✓</span>
              <span className="text-sm font-semibold text-success-700">
                {businessStatus} 확인 완료
              </span>
            </div>
            <label className="block text-base font-bold text-gray-900 mb-2">
              가게 이름이 어떻게 되세요?
            </label>
            <p className="text-sm text-gray-500 mb-4">
              상호명만 적으시면 카카오맵에서 가게를 찾아드려요
            </p>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="예: 삼각김밥 카페, 떡볶이"
              className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-base text-gray-900 focus:outline-none focus:ring-2 focus:ring-warn-500 focus:bg-white border-2 border-transparent focus:border-warn-500"
            />
            <div className="mt-4 space-y-2">
              {searchResults.map((biz) => (
                <button
                  key={`${biz.place_name}-${biz.x}-${biz.y}`}
                  onClick={() => handleSelectBusiness(biz)}
                  className="press-effect w-full text-left p-4 bg-gray-50 rounded-2xl hover:bg-warn-50 transition-colors"
                >
                  <p className="font-bold text-gray-900 text-base mb-0.5">{biz.place_name}</p>
                  <p className="text-sm text-gray-600">
                    {biz.road_address_name || biz.address_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">{biz.category_name}</p>
                </button>
              ))}
              {searchQuery && searchResults.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-8">
                  검색되는 가게가 없어요. 이름을 다르게 적어 주세요
                </p>
              )}
            </div>
          </div>
        )}

        {/* Step 3: 확인 */}
        {step === "confirm" && selectedBusiness && (
          <div>
            <p className="text-base font-bold text-gray-900 mb-2">
              이 가게가 맞나요?
            </p>
            <p className="text-sm text-gray-500 mb-5">
              아니면 아래 &lsquo;다시 검색하기&rsquo;로 골라보세요
            </p>

            <div className="bg-warn-50 p-5 rounded-2xl mb-4">
              <p className="font-bold text-gray-900 text-lg mb-1">
                {selectedBusiness.place_name}
              </p>
              <p className="text-sm text-gray-700 mb-1">
                {selectedBusiness.road_address_name || selectedBusiness.address_name}
              </p>
              <p className="text-sm text-gray-500">{selectedBusiness.category_name}</p>
            </div>

            {/* 업종 선택 (지식팩 매핑 — 진단/마케팅 조언이 업종별로 달라짐) */}
            {industries.length > 0 && (
              <div className="bg-gray-50 rounded-2xl p-5 mb-6">
                <label className="block">
                  <span className="text-base font-bold text-gray-900">우리 가게 업종</span>
                  <p className="text-sm text-gray-500 mt-1 mb-3">
                    맞으면 그대로 두세요. 업종에 맞춰 진단·마케팅 조언이 달라져요.
                  </p>
                  <select
                    value={industrySlug}
                    onChange={(e) => setIndustrySlug(e.target.value)}
                    className="w-full px-4 py-3 bg-white rounded-xl text-base text-gray-900 focus:outline-none focus:ring-2 focus:ring-warn-500 border-2 border-transparent focus:border-warn-500"
                  >
                    <option value="">자동 감지 (가게 카테고리로)</option>
                    {industries
                      .filter((p) => p.group === null)
                      .sort((a, b) => a.priority - b.priority)
                      .flatMap((parent) => [
                        <option key={parent.id} value={parent.id}>
                          {parent.name}
                        </option>,
                        ...industries
                          .filter((p) => p.group === parent.id)
                          .sort((a, b) => a.priority - b.priority)
                          .map((child) => (
                            <option key={child.id} value={child.id}>
                              {"  ↳ "}
                              {child.name}
                            </option>
                          )),
                      ])}
                  </select>
                </label>
              </div>
            )}

            {/* 개점일 입력 (선택) */}
            <div className="bg-gray-50 rounded-2xl p-5 mb-6">
              <label className="block">
                <span className="text-base font-bold text-gray-900">
                  가게 처음 연 날
                  <span className="ml-2 text-xs font-medium text-gray-400">선택</span>
                </span>
                <p className="text-sm text-gray-500 mt-1 mb-3">
                  적어주시면 폐업 위험 분석이 더 정확해져요
                </p>
                <input
                  type="date"
                  value={businessStartDate}
                  max={new Date().toISOString().slice(0, 10)}
                  onChange={(e) => setBusinessStartDate(e.target.value)}
                  className="w-full px-4 py-3 bg-white rounded-xl text-base text-gray-900 focus:outline-none focus:ring-2 focus:ring-warn-500 border-2 border-transparent focus:border-warn-500"
                />
              </label>
            </div>

            {error && (
              <p className="mb-3 text-sm font-medium text-loss-500">{error}</p>
            )}
            <button
              onClick={handleComplete}
              className="press-effect w-full py-[18px] bg-warn-500 text-gray-900 font-bold text-base rounded-2xl shadow-btn hover:bg-warn-600"
            >
              이 가게가 맞아요
            </button>
            <button
              onClick={() => setStep("business_search")}
              className="w-full mt-2 py-4 text-sm font-medium text-gray-500 hover:text-gray-700"
            >
              다시 검색하기
            </button>
          </div>
        )}

        {/* Loading */}
        {step === "loading" && (
          <div className="text-center pt-16">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-gray-200 border-t-warn-500 mx-auto mb-6" />
            <p className="text-base font-semibold text-gray-900 mb-1">
              우리 가게에 맞는 지원사업을 찾고 있어요
            </p>
            <p className="text-sm text-gray-500">서울시 데이터 살펴보는 중...</p>
          </div>
        )}

        {/* Done */}
        {step === "done" && result && (
          <div className="text-center pt-12">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-success-100 flex items-center justify-center">
              <span className="text-success-600 text-3xl font-bold">✓</span>
            </div>
            <h2 className="text-display-sm text-gray-900 mb-3 text-balance">
              {result.message}
            </h2>
            {result.subsidy_count > 0 && (
              <p className="text-base font-semibold text-loss-500 mb-8">
                지금 확인하지 않으면 놓칠 수 있어요
              </p>
            )}
            <button
              onClick={() => router.push("/dashboard")}
              className="press-effect w-full py-[18px] bg-warn-500 text-gray-900 font-bold text-base rounded-2xl shadow-btn hover:bg-warn-600"
            >
              대시보드로 이동
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
