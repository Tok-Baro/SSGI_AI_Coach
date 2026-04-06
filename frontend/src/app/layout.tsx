import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI 경영코치 - 소상공인 경영 지원",
  description: "사장님이 모르고 놓치는 돈, AI가 찾아줍니다.",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#FEE500",
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
      <body className={`${inter.className} bg-white min-h-screen`}>{children}</body>
    </html>
  );
}
