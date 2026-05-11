"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

function SuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"approving" | "success" | "error">("approving");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<{ item_name: string; total_amount: number; expired_at: string | null } | null>(null);

  useEffect(() => {
    const pgToken = searchParams.get("pg_token");
    const tid = sessionStorage.getItem("kakao_pay_tid");
    const orderId = sessionStorage.getItem("kakao_pay_order");

    if (!pgToken || !tid || !orderId) {
      setStatus("error");
      setError("결제 정보가 없어요. 다시 시도해 주세요.");
      return;
    }

    api.approveKakaoPayment({ tid, partner_order_id: orderId, pg_token: pgToken })
      .then((res) => {
        setStatus("success");
        setInfo({ item_name: res.item_name, total_amount: res.total_amount, expired_at: res.expired_at });
        sessionStorage.removeItem("kakao_pay_tid");
        sessionStorage.removeItem("kakao_pay_order");
      })
      .catch((err: any) => {
        setStatus("error");
        setError(err?.message || "결제 승인이 막혔어요. 잠시 후 다시 시도해 주세요.");
      });
  }, [searchParams]);

  if (status === "approving") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-200 border-t-warn-500 mb-4" />
        <p className="text-base font-semibold text-gray-900">결제 승인 중이에요</p>
        <p className="text-xs text-gray-500 mt-1">잠시만 기다려 주세요</p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-loss-50 flex items-center justify-center text-3xl">⚠</div>
        <p className="text-base font-bold text-gray-900 mb-1">결제가 완료되지 못했어요</p>
        <p className="text-sm text-loss-600 mb-6 text-center">{error}</p>
        <button
          onClick={() => router.push("/upgrade")}
          className="press-effect px-6 py-3 bg-warn-500 text-gray-900 font-bold rounded-xl"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
      <div className="w-20 h-20 rounded-full bg-success-50 flex items-center justify-center text-4xl mb-6">
        ✓
      </div>
      <h1 className="text-2xl font-extrabold text-gray-900 mb-2">결제 완료</h1>
      <p className="text-sm text-gray-600 mb-1">{info?.item_name}</p>
      <p className="text-xl font-bold text-warn-600 tabular-nums mb-6">
        {info?.total_amount.toLocaleString()}원
      </p>
      {info?.expired_at && (
        <p className="text-sm text-gray-700 mb-8">
          {new Date(info.expired_at).toLocaleDateString("ko-KR")}까지 Pro 이용 가능
        </p>
      )}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6 max-w-sm text-center">
        <p className="text-xs text-amber-800">
          테스트 결제입니다. 실제 청구되지 않았어요.
        </p>
      </div>
      <button
        onClick={() => router.push("/dashboard")}
        className="press-effect w-full max-w-sm py-3 bg-warn-500 text-gray-900 font-bold rounded-xl"
      >
        Pro로 대시보드 가기
      </button>
    </main>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
