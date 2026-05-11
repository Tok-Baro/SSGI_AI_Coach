"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
      <div className="w-16 h-16 mb-5 rounded-full bg-loss-50 flex items-center justify-center text-3xl">
        ⚠
      </div>
      <h2 className="text-display-sm text-gray-900 mb-2 text-center">
        문제가 발생했어요
      </h2>
      <p className="text-sm text-gray-500 mb-8 text-center leading-relaxed max-w-xs">
        {error.message || "잠깐 문제가 있었어요. 다시 한 번 눌러 보시겠어요?"}
      </p>
      <button
        onClick={reset}
        className="press-effect px-8 py-[14px] bg-warn-500 text-gray-900 font-bold rounded-2xl shadow-btn"
      >
        다시 시도
      </button>
    </div>
  );
}
