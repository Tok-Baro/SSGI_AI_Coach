"use client";

import { useRouter } from "next/navigation";

export default function FailPage() {
  const router = useRouter();
  return (
    <main className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
      <div className="w-16 h-16 rounded-full bg-loss-50 flex items-center justify-center text-3xl mb-4">
        ✕
      </div>
      <h1 className="text-base font-bold text-gray-900 mb-1">결제가 실패했어요</h1>
      <p className="text-sm text-gray-600 mb-6">잠시 후 다시 시도해 주세요</p>
      <button
        onClick={() => router.push("/upgrade")}
        className="press-effect px-6 py-3 bg-warn-500 text-gray-900 font-bold rounded-xl"
      >
        다시 시도
      </button>
    </main>
  );
}
