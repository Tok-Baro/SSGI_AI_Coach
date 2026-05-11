"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useSTT } from "@/hooks/useSTT";
import { api } from "@/lib/api";
import type { VoiceQueryResponse } from "@/types";

export default function STTButton() {
  const router = useRouter();
  const pathname = usePathname();
  const { isListening, transcript, transcriptRef, error, startListening, stopListening, isSupported } = useSTT();
  const [response, setResponse] = useState<VoiceQueryResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  if (!isSupported) return null;

  const callVoiceQuery = async (text: string) => {
    setIsProcessing(true);
    setApiError(null);
    try {
      const res = await api.voiceQuery(text);
      setResponse(res);
      // 라우팅 의도가 있고 현재 경로와 다르면 자동 이동
      if (res.route) {
        const target = res.route.split("?")[0];
        if (target !== pathname) {
          router.push(res.route);
          // 도착 후 답변을 짧게 보여주기 위해 패널은 유지
        }
      }
    } catch (e) {
      setResponse(null);
      const msg = e instanceof Error ? e.message : "AI 응답을 받지 못했습니다.";
      setApiError(msg.includes("인증") ? "세션이 만료되어 로그인 화면으로 이동합니다." : msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggle = async () => {
    if (isListening) {
      stopListening();
      const finalText = transcriptRef.current;
      if (finalText) {
        setShowPanel(true);
        await callVoiceQuery(finalText);
      }
    } else {
      setResponse(null);
      setApiError(null);
      setShowPanel(true);
      startListening();
    }
  };

  const handleSuggestion = (text: string) => callVoiceQuery(text);

  return (
    <>
      {/* 플로팅 마이크 버튼 */}
      <button
        onClick={handleToggle}
        aria-label={isListening ? "음성 인식 중지" : "음성 질문하기"}
        className={`press-effect fixed bottom-24 right-5 w-16 h-16 rounded-full flex items-center justify-center transition-all z-50 ${
          isListening
            ? "bg-loss-500 animate-pulse text-white shadow-card-hover"
            : "bg-gray-900 hover:bg-gray-800 text-white shadow-card-hover"
        }`}
      >
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      </button>

      {/* 응답 패널 */}
      {showPanel && (
        <div className="fixed bottom-44 right-5 left-5 max-w-md mx-auto bg-white rounded-2xl shadow-card-hover p-5 z-50">
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              {isListening && (
                <span className="w-2 h-2 rounded-full bg-loss-500 animate-pulse" />
              )}
              <span className="text-sm font-bold text-gray-900">
                {isListening ? "듣고 있어요" : "AI 경영코치"}
              </span>
            </div>
            <button
              onClick={() => setShowPanel(false)}
              className="press-effect w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-500"
              aria-label="닫기"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* 실시간 트랜스크립트 */}
          {transcript && (
            <p className="text-sm text-gray-700 bg-gray-50 rounded-xl p-3 mb-3 leading-relaxed">
              &ldquo;{transcript}&rdquo;
            </p>
          )}

          {/* 로딩 */}
          {isProcessing && (
            <div className="flex items-center gap-2 text-sm text-gray-600 py-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-200 border-t-warn-500" />
              <span className="font-semibold">답을 찾고 있어요...</span>
            </div>
          )}

          {/* 에러 */}
          {error && (
            <div className="bg-loss-50 rounded-xl p-3 mt-2">
              <p className="text-sm text-loss-500 font-medium">{error}</p>
            </div>
          )}
          {apiError && !isProcessing && (
            <div className="bg-loss-50 rounded-xl p-3 mt-2">
              <p className="text-sm text-loss-500 font-medium">{apiError}</p>
            </div>
          )}

          {/* AI 응답 */}
          {response && !isProcessing && (
            <div>
              <p className="text-base text-gray-900 mb-3 leading-relaxed">
                {response.answer}
              </p>
              <div className="flex flex-wrap gap-2">
                {response.suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSuggestion(s)}
                    className="press-effect text-xs px-3 py-2 bg-gray-100 text-gray-900 font-bold rounded-full hover:bg-gray-200"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
