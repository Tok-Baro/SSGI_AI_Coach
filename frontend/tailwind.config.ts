import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Pretendard Variable",
          "Pretendard",
          "-apple-system",
          "BlinkMacSystemFont",
          "system-ui",
          "Roboto",
          "sans-serif",
        ],
      },
      // 시니어 가독성: 기본 text-xs를 12px → 14px로 상향 (50-60+ 사장 타깃)
      // QA Round 2 P0-I: text-xs/text-[8-11px] occurrence 192건 일괄 보강
      fontSize: {
        xs: ["14px", { lineHeight: "20px" }],
        sm: ["15px", { lineHeight: "22px" }],
        // base/lg/xl 등은 기본값 유지
        // Toss 풍 디스플레이 타이포 (큰 숫자 hero용)
        "display-sm": ["28px", { lineHeight: "36px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display": ["34px", { lineHeight: "42px", letterSpacing: "-0.025em", fontWeight: "700" }],
        "display-lg": ["42px", { lineHeight: "50px", letterSpacing: "-0.03em", fontWeight: "800" }],
      },
      colors: {
        // 토스풍 그레이스케일 (정보 위계용)
        gray: {
          50: "#F9FAFB",
          100: "#F2F4F6",
          200: "#E5E8EB",
          300: "#D1D6DB",
          400: "#B0B8C1",
          500: "#8B95A1",
          600: "#6B7684",
          700: "#4E5968",
          800: "#333D4B",
          900: "#191F28",
        },
        // 의미색 — 톤 다운된 토스 스타일 (3색 시스템 유지: 빨강/노랑/초록)
        loss: {
          50: "#FEF1F2",
          100: "#FEE2E4",
          500: "#F04452",
          600: "#E0202F",
          700: "#C81628",
        },
        warn: {
          // 노랑 = 카카오 + 액션
          50: "#FFFBEB",
          100: "#FEF3C7",
          400: "#FDD835",
          500: "#FEE500",
          600: "#F1B800",
          900: "#7C5E00",
        },
        success: {
          50: "#E6FAF4",
          100: "#C0F2DF",
          500: "#00C896",
          600: "#00A87E",
          700: "#008A66",
        },
      },
      borderRadius: {
        // 토스는 카드 16px, hero 20px 즐겨씀
        xl: "12px",
        "2xl": "16px",
        "3xl": "20px",
      },
      boxShadow: {
        // 토스풍 부드러운 그림자
        card: "0 1px 3px rgba(25, 31, 40, 0.04), 0 4px 12px rgba(25, 31, 40, 0.04)",
        "card-hover": "0 1px 3px rgba(25, 31, 40, 0.06), 0 8px 24px rgba(25, 31, 40, 0.08)",
        "btn": "0 1px 2px rgba(25, 31, 40, 0.04)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
