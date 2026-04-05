"use client";

import { useState } from "react";
import { useSTT } from "@/hooks/useSTT";
import { api } from "@/lib/api";
import type { VoiceQueryResponse } from "@/types";

export default function STTButton() {
  const { isListening, transcript, error, startListening, stopListening, isSupported } = useSTT();
  const [response, setResponse] = useState<VoiceQueryResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPanel, setShowPanel] = useState(false);

  if (!isSupported) return null;

  const handleToggle = async () => {
    if (isListening) {
      stopListening();
      // 음성 인식 완료 후 API 호출
      if (transcript) {
        setIsProcessing(true);
        setShowPanel(true);
        try {
          const res = await api.voiceQuery(transcript);
          setResponse(res);
        } catch {
          setResponse(null);
        } finally {
          setIsProcessing(false);
        }
      }
    } else {
      setResponse(null);
      setShowPanel(true);
      startListening();
    }
  };

  const handleSuggestion = async (text: string) => {
    setIsProcessing(true);
    try {
      const res = await api.voiceQuery(text);
      setResponse(res);
    } catch {
      setResponse(null);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <>
      {/* 플로팅 마이크 버튼 */}
      <button
        onClick={handleToggle}
        className={`fixed bottom-24 right-6 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all z-50 ${
          isListening
            ? "bg-red-500 animate-pulse"
            : "bg-yellow-400 hover:bg-yellow-500"
        }`}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      </button>

      {/* 응답 패널 */}
      {showPanel && (
        <div className="fixed bottom-40 right-6 left-6 max-w-sm mx-auto bg-white rounded-2xl shadow-xl border border-gray-100 p-4 z-50">
          <div className="flex justify-between items-start mb-3">
            <span className="text-xs text-gray-400">
              {isListening ? "듣고 있어요..." : "AI 경영코치"}
            </span>
            <button onClick={() => setShowPanel(false)} className="text-gray-400 hover:text-gray-600">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* 실시간 트랜스크립트 */}
          {transcript && (
            <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-2 mb-3">
              &ldquo;{transcript}&rdquo;
            </p>
          )}

          {/* 로딩 */}
          {isProcessing && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400" />
              답변 생성 중...
            </div>
          )}

          {/* 에러 */}
          {error && <p className="text-sm text-red-500">{error}</p>}

          {/* AI 응답 */}
          {response && !isProcessing && (
            <div>
              <p className="text-sm text-gray-900 mb-3">{response.answer}</p>
              <div className="flex flex-wrap gap-2">
                {response.suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestion(s)}
                    className="text-xs px-3 py-1.5 bg-yellow-50 text-yellow-700 rounded-full hover:bg-yellow-100 transition-colors"
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
