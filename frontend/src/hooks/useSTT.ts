"use client";

import { useState, useCallback, useRef } from "react";

interface UseSTTReturn {
  isListening: boolean;
  transcript: string;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  isSupported: boolean;
}

export function useSTT(): UseSTTReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const isSupported =
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError("이 브라우저는 음성 인식을 지원하지 않습니다. Chrome을 사용해주세요.");
      return;
    }

    setError(null);
    setTranscript("");

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
    };

    recognition.onerror = (event: any) => {
      setIsListening(false);
      switch (event.error) {
        case "no-speech":
          setError("음성이 감지되지 않았습니다. 다시 시도해주세요.");
          break;
        case "not-allowed":
          setError("마이크 권한이 필요합니다. 브라우저 설정에서 허용해주세요.");
          break;
        case "network":
          setError("네트워크 오류가 발생했습니다.");
          break;
        default:
          setError("음성 인식 오류가 발생했습니다.");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
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
    error,
    startListening,
    stopListening,
    isSupported,
  };
}
