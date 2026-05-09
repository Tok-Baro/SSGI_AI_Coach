import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // 시니어 가독성: 기본 text-xs를 12px → 14px로 상향 (50-60+ 사장 타깃)
      // QA Round 2 P0-I: text-xs/text-[8-11px] occurrence 192건 일괄 보강
      fontSize: {
        xs: ["14px", { lineHeight: "20px" }],
        sm: ["15px", { lineHeight: "22px" }],
        // base/lg/xl 등은 기본값 유지
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
