"use client";

import { useRouter } from "next/navigation";

export default function CancelPage() {
  const router = useRouter();
  return (
    <main className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-3xl mb-4">
        ↺
      </div>
      <h1 className="text-base font-bold text-gray-900 mb-1">결제를 취소하셨어요</h1>
      <p className="text-sm text-gray-600 mb-6">언제든 다시 시도하실 수 있어요</p>
      <button
        onClick={() => router.push("/upgrade")}
        className="press-effect px-6 py-3 bg-warn-500 text-gray-900 font-bold rounded-xl"
      >
        다시 보기
      </button>
    </main>
  );
}
