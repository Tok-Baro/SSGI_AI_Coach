"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { KakaoLocalSearchResult } from "@/types";

type Step = "business_number" | "business_search" | "confirm" | "loading" | "done";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth } = useAuth();
  const [step, setStep] = useState<Step>("business_number");
  const [businessNumber, setBusinessNumber] = useState("");
  const [businessStatus, setBusinessStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KakaoLocalSearchResult[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<KakaoLocalSearchResult | null>(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ subsidy_count: number; message: string } | null>(null);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

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
      if (res.is_valid) {
        setBusinessStatus(res.business_status);
        setStep("business_search");
      } else {
        setError(`사업자 상태: ${res.business_status}. 계속사업자만 이용 가능합니다.`);
      }
    } catch (err: any) {
      setError(err.message || "검증에 실패했습니다.");
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

    // 카테고리에서 업종 추출 (예: "음식점 > 카페 > 커피전문점" → "카페")
    const categories = selectedBusiness.category_name.split(" > ");
    const businessType = categories.length >= 2 ? categories[1] : categories[0];

    // 주소에서 동명, 구명 추출 (서울시 행정구역 기준)
    const fullAddress = selectedBusiness.address_name;
    const addressParts = fullAddress.split(" ");
    // "구"로 끝나는 것 중 실제 행정구 찾기 (예: "강남구", "종로구")
    const guName = addressParts.find((p) => /^[가-힣]+구$/.test(p)) || "";
    // "동"으로 끝나면서 숫자동(역삼1동)도 포함, 최소 2글자
    const dongName = addressParts.find((p) => /^[가-힣0-9]{2,}동$/.test(p)) || "";

    try {
      const res = await api.completeOnboarding({
        business_number: businessNumber,
        business_name: selectedBusiness.place_name,
        business_type: businessType,
        address: selectedBusiness.road_address_name || selectedBusiness.address_name,
        dong_name: dongName,
        gu_name: guName,
        lat: parseFloat(selectedBusiness.y),
        lng: parseFloat(selectedBusiness.x),
      });
      setResult({ subsidy_count: res.subsidy_count, message: res.message });
      setStep("done");
    } catch (err: any) {
      setError(err.message || "온보딩에 실패했습니다.");
      setStep("confirm");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  return (
    <main className="flex flex-col items-center min-h-screen px-6 py-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">사업장 등록</h1>
      <p className="text-sm text-gray-500 mb-8">15초면 끝나요</p>

      {/* Step 1: 사업자번호 */}
      {step === "business_number" && (
        <div className="w-full max-w-sm">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            사업자등록번호
          </label>
          <input
            type="text"
            maxLength={10}
            value={businessNumber}
            onChange={(e) => setBusinessNumber(e.target.value.replace(/\D/g, ""))}
            placeholder="10자리 숫자 입력"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-400 focus:border-transparent text-lg"
          />
          {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
          <button
            onClick={handleVerifyBusiness}
            disabled={businessNumber.length !== 10}
            className="w-full mt-4 py-3 bg-yellow-400 text-gray-900 font-semibold rounded-xl disabled:opacity-50 hover:bg-yellow-500 transition-colors"
          >
            확인
          </button>
        </div>
      )}

      {/* Step 2: 상호명 검색 */}
      {step === "business_search" && (
        <div className="w-full max-w-sm">
          <p className="text-sm text-green-600 mb-4">
            {businessStatus} 확인 완료
          </p>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            상호명 검색
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="가게 이름을 검색하세요"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
          />
          <div className="mt-3 space-y-2">
            {searchResults.map((biz, i) => (
              <button
                key={i}
                onClick={() => handleSelectBusiness(biz)}
                className="w-full text-left p-3 bg-gray-50 rounded-xl hover:bg-yellow-50 border border-gray-100 transition-colors"
              >
                <p className="font-medium text-gray-900">{biz.place_name}</p>
                <p className="text-xs text-gray-500">{biz.road_address_name || biz.address_name}</p>
                <p className="text-xs text-gray-400">{biz.category_name}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: 확인 */}
      {step === "confirm" && selectedBusiness && (
        <div className="w-full max-w-sm">
          <div className="bg-yellow-50 p-4 rounded-xl mb-4">
            <p className="font-semibold text-gray-900">{selectedBusiness.place_name}</p>
            <p className="text-sm text-gray-600">{selectedBusiness.road_address_name || selectedBusiness.address_name}</p>
            <p className="text-sm text-gray-500">{selectedBusiness.category_name}</p>
          </div>
          {error && <p className="mb-2 text-sm text-red-500">{error}</p>}
          <button
            onClick={handleComplete}
            className="w-full py-3 bg-yellow-400 text-gray-900 font-semibold rounded-xl hover:bg-yellow-500 transition-colors"
          >
            이 가게가 맞아요
          </button>
          <button
            onClick={() => setStep("business_search")}
            className="w-full mt-2 py-3 text-gray-500 hover:text-gray-700"
          >
            다시 검색
          </button>
        </div>
      )}

      {/* Loading */}
      {step === "loading" && (
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-yellow-400 mx-auto mb-4" />
          <p className="text-gray-500">사장님에게 맞는 지원사업을 찾고 있어요...</p>
          <p className="text-xs text-gray-400 mt-2">서울시 데이터 분석 중</p>
        </div>
      )}

      {/* Done */}
      {step === "done" && result && (
        <div className="w-full max-w-sm text-center">
          <div className="text-4xl mb-4">
            {result.subsidy_count > 0 ? "!" : ""}
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{result.message}</h2>
          {result.subsidy_count > 0 && (
            <p className="text-red-500 font-medium mb-6">
              지금 확인하지 않으면 놓칠 수 있어요
            </p>
          )}
          <button
            onClick={() => router.push("/dashboard")}
            className="w-full py-3 bg-yellow-400 text-gray-900 font-semibold rounded-xl hover:bg-yellow-500 transition-colors"
          >
            대시보드로 이동
          </button>
        </div>
      )}
    </main>
  );
}
