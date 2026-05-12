import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 경영코치 - 소상공인 경영 지원",
  description: "사장님이 모르고 놓치는 돈, AI가 찾아줍니다.",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#0F2A3F",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          as="style"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className="font-sans bg-white text-gray-900 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
