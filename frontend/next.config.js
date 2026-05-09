// next-pwa 기본 runtimeCaching에서 /api/* NetworkFirst를 NetworkOnly로 override.
// QA Round 2 P1-4: cross-user PII 노출 방지 (cache 키에 user/JWT 미포함).
const runtimeCaching = require("next-pwa/cache");
const customRuntimeCaching = runtimeCaching.map((entry) => {
  const url = entry.urlPattern;
  // /api/* 정확 매칭 (auth 제외 분기는 사용자 데이터 응답 다수)
  if (typeof entry.options?.cacheName === "string" && entry.options.cacheName === "apis") {
    return {
      urlPattern: url,
      handler: "NetworkOnly",
      method: "GET",
    };
  }
  return entry;
});

const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  // macOS Finder 부산물 (sw 2.js, sw 3.js 같은 중복) precache에서 제외
  buildExcludes: [/sw\s\d+\.js$/, /workbox-.*\.js\.map$/],
  runtimeCaching: customRuntimeCaching,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
