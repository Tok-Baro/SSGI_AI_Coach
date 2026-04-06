"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6">
      <h2 className="text-xl font-bold text-gray-900 mb-2">문제가 발생했습니다</h2>
      <p className="text-sm text-gray-500 mb-6">
        {error.message || "일시적인 오류가 발생했습니다. 다시 시도해주세요."}
      </p>
      <button
        onClick={reset}
        className="px-6 py-3 bg-yellow-400 text-gray-900 font-semibold rounded-xl hover:bg-yellow-500 transition-colors"
      >
        다시 시도
      </button>
    </div>
  );
}
