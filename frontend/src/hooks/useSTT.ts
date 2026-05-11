"use client";

import { useState, useCallback, useRef } from "react";

interface UseSTTReturn {
  isListening: boolean;
  transcript: string;
  transcriptRef: { current: string };
  error: string | null;
  startListening: (onFinal?: (text: string) => void) => void;
  stopListening: () => void;
  isSupported: boolean;
}

export function useSTT(): UseSTTReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const transcriptRef = useRef<string>("");
  const onFinalRef = useRef<((text: string) => void) | null>(null);
  const firedRef = useRef(false);

  const isSupported =
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  const startListening = useCallback((onFinal?: (text: string) => void) => {
    if (!isSupported) {
      setError("이 브라우저는 음성 인식을 지원하지 않아요. Chrome이나 Edge에서 써 주세요.");
      return;
    }

    setError(null);
    setTranscript("");
    transcriptRef.current = "";
    onFinalRef.current = onFinal ?? null;
    firedRef.current = false;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = "ko-KR";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const results = event.results;
      const text = results[results.length - 1][0].transcript;
      setTranscript(text);
      transcriptRef.current = text;
    };

    recognition.onerror = (event: any) => {
      setIsListening(false);
      switch (event.error) {
        case "no-speech":
          setError("말소리가 안 들렸어요. 버튼 누르고 또박또박 말해 주세요.");
          break;
        case "not-allowed":
        case "service-not-allowed":
          setError("마이크 권한이 막혀 있어요. 주소창 왼쪽 자물쇠 → 마이크 → 허용으로 바꿔 주세요.");
          break;
        case "audio-capture":
          setError("마이크를 못 찾았어요. 마이크가 연결됐는지 확인해 주세요.");
          break;
        case "network":
          setError("네트워크가 불안정해요. 다시 시도해 주세요.");
          break;
        case "aborted":
          break;
        default:
          setError("음성 인식이 잘 안 됐어요. 다시 시도해 주세요.");
      }
    };

    // continuous=false면 말이 끝나면 자동으로 onend가 불림 — 그 시점에 바로 AI로 전달.
    // 사용자가 버튼을 한 번 더 누르면 stopListening()도 결국 onend를 트리거하므로 경로는 동일.
    recognition.onend = () => {
      setIsListening(false);
      const finalText = transcriptRef.current.trim();
      if (finalText && !firedRef.current && onFinalRef.current) {
        firedRef.current = true;
        onFinalRef.current(finalText);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isSupported]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  }, []);

  return {
    isListening,
    transcript,
    transcriptRef,
    error,
    startListening,
    stopListening,
    isSupported,
  };
}
