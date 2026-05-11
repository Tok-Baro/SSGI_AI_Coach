"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { Coupon, CreateCouponRequest } from "@/types";

export default function CouponsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateCouponRequest>({
    title: "",
    discount_type: "percent",
    discount_value: 10,
    description: "",
    valid_days: 7,
  });
  const [creating, setCreating] = useState(false);
  const [zoomQR, setZoomQR] = useState<Coupon | null>(null);

  // 카카오톡 공유 — Web Share API + 카카오 SDK 폴백
  const shareToKakao = async (coupon: Coupon) => {
    const shareUrl = typeof window !== "undefined" ? window.location.origin + `/coupons/${coupon.id}` : "";
    const text = `[${coupon.title}] ${
      coupon.discount_type === "percent" ? `${coupon.discount_value}% 할인` :
      coupon.discount_type === "fixed" ? `${(coupon.discount_value ?? 0).toLocaleString()}원 할인` :
      coupon.discount_type === "bogo" ? "1+1" : "무료 증정"
    } · ${coupon.valid_until}까지`;
    try {
      // 1순위: Web Share API (모바일)
      if (navigator.share) {
        await navigator.share({ title: coupon.title, text, url: shareUrl });
        return;
      }
      // 폴백: 클립보드 복사
      await navigator.clipboard.writeText(`${text}\n${shareUrl}`);
      alert("쿠폰 정보를 복사했어요. 카카오톡에 붙여넣으세요.");
    } catch {
      // 사용자 취소 OK
    }
  };

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.push("/"); return; }
    if (isAuthenticated) {
      api.listCoupons()
        .then(setCoupons)
        .catch((err) => setError(err.message || "쿠폰 목록을 불러오지 못했습니다."))
        .finally(() => setLoading(false));
    }
  }, [isLoading, isAuthenticated, router]);

  const handleCreate = async () => {
    if (!form.title) return;
    setCreating(true);
    setCreateError(null);
    try {
      const coupon = await api.createCoupon(form);
      setCoupons([coupon, ...coupons]);
      setShowCreate(false);
      setForm({ title: "", discount_type: "percent", discount_value: 10, description: "", valid_days: 7 });
    } catch (err: any) {
      setCreateError(err.message || "쿠폰 생성에 실패했습니다.");
    }
    setCreating(false);
  };

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-6 bg-white">
        <p className="text-base font-semibold text-loss-500 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="press-effect px-6 py-3 bg-gray-100 rounded-2xl font-semibold text-gray-900"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 pb-24">
      <header className="bg-white px-5 py-5 sticky top-0 z-10">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="press-effect w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-lg"
              aria-label="뒤로"
            >
              ←
            </button>
            <h1 className="text-display-sm text-gray-900">QR 쿠폰</h1>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="press-effect px-4 py-2.5 bg-warn-500 text-gray-900 text-sm font-bold rounded-xl shadow-btn"
          >
            + 새 쿠폰
          </button>
        </div>
      </header>

      <div className="max-w-md mx-auto px-5 py-5 space-y-3">
        {coupons.map((c) => (
          <div key={c.id} className="bg-white rounded-2xl p-5 shadow-card">
            <div className="flex gap-4">
              {c.qr_image_base64 && (
                <button
                  onClick={() => setZoomQR(c)}
                  aria-label="QR 코드 확대 보기"
                  className="press-effect w-24 h-24 rounded-xl bg-gray-50 overflow-hidden flex-shrink-0"
                >
                  <img src={c.qr_image_base64} alt="QR" className="w-full h-full" />
                </button>
              )}
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-gray-900 text-base mb-1 truncate">
                  {c.title}
                </h3>
                <p className="text-xl font-extrabold text-warn-600 tabular-nums mb-1">
                  {c.discount_type === "percent" && `${c.discount_value}% 할인`}
                  {c.discount_type === "fixed" && `${(c.discount_value ?? 0).toLocaleString()}원 할인`}
                  {c.discount_type === "bogo" && "1+1"}
                  {c.discount_type === "free_item" && "무료 증정"}
                </p>
                <p className="text-xs text-gray-400 tabular-nums">
                  {c.valid_from} ~ {c.valid_until}
                </p>
                <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100">
                  <div>
                    <p className="text-xs text-gray-500">다운로드</p>
                    <p className="text-base font-bold text-gray-900 tabular-nums mt-0.5">
                      {c.download_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">스캔</p>
                    <p className="text-base font-bold text-warn-600 tabular-nums mt-0.5">
                      {c.scan_count}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            {/* 카카오 공유 + QR 확대 액션 row */}
            <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
              <button
                onClick={() => shareToKakao(c)}
                className="press-effect flex-1 py-2.5 bg-warn-500 text-gray-900 font-bold text-sm rounded-xl"
              >
                카카오톡으로 공유
              </button>
              <button
                onClick={() => setZoomQR(c)}
                className="press-effect flex-shrink-0 px-4 py-2.5 bg-gray-100 text-gray-700 font-medium text-sm rounded-xl"
              >
                QR 보기
              </button>
            </div>
          </div>
        ))}

        {coupons.length === 0 && (
          <div className="bg-white rounded-2xl p-10 text-center shadow-card">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-warn-50 flex items-center justify-center text-3xl">
              🎟
            </div>
            <p className="text-base font-bold text-gray-900 mb-1">
              아직 만든 쿠폰이 없어요
            </p>
            <p className="text-sm text-gray-500 mb-6">
              첫 쿠폰을 뿌려서 우리 가게 단골을 만들어 보세요
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="press-effect w-full py-[14px] bg-warn-500 text-gray-900 font-bold rounded-xl shadow-btn"
            >
              첫 쿠폰 만들기
            </button>
          </div>
        )}
      </div>

      {/* 쿠폰 생성 모달 */}
      {showCreate && (
        <div className="fixed inset-0 bg-gray-900/40 z-50 flex items-end backdrop-blur-sm">
          <div className="bg-white w-full max-w-md mx-auto rounded-t-3xl p-6 pb-8 max-h-[90vh] overflow-y-auto">
            <div className="w-12 h-1 bg-gray-200 rounded-full mx-auto mb-5" />
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-display-sm text-gray-900">쿠폰 만들기</h2>
              <button
                onClick={() => setShowCreate(false)}
                className="press-effect w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 text-lg"
                aria-label="닫기"
              >
                ✕
              </button>
            </div>

            <div className="space-y-5">
              {createError && (
                <div className="bg-loss-50 rounded-xl p-3">
                  <p className="text-loss-500 text-sm font-medium">{createError}</p>
                </div>
              )}
              <div>
                <label className="block text-base font-bold text-gray-900 mb-2">
                  쿠폰명
                </label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="예: 아메리카노 1+1"
                  className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-base focus:outline-none focus:ring-2 focus:ring-warn-500 focus:bg-white border-2 border-transparent focus:border-warn-500"
                />
              </div>

              <div>
                <label className="block text-base font-bold text-gray-900 mb-2">
                  할인 유형
                </label>
                <select
                  value={form.discount_type}
                  onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
                  className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-base focus:outline-none focus:ring-2 focus:ring-warn-500 border-2 border-transparent focus:border-warn-500"
                >
                  <option value="percent">% 할인</option>
                  <option value="fixed">원 할인</option>
                  <option value="bogo">1+1</option>
                  <option value="free_item">무료 증정</option>
                </select>
              </div>

              {(form.discount_type === "percent" || form.discount_type === "fixed") && (
                <div>
                  <label className="block text-base font-bold text-gray-900 mb-2">
                    {form.discount_type === "percent" ? "할인율 (%)" : "할인 금액 (원)"}
                  </label>
                  <input
                    type="number"
                    inputMode="numeric"
                    value={form.discount_value || ""}
                    onChange={(e) => setForm({ ...form, discount_value: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-base tabular-nums focus:outline-none focus:ring-2 focus:ring-warn-500 focus:bg-white border-2 border-transparent focus:border-warn-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-base font-bold text-gray-900 mb-2">
                  유효기간 (일)
                </label>
                <input
                  type="number"
                  inputMode="numeric"
                  value={form.valid_days || 7}
                  onChange={(e) => setForm({ ...form, valid_days: parseInt(e.target.value) || 7 })}
                  className="w-full px-4 py-4 bg-gray-50 rounded-2xl text-base tabular-nums focus:outline-none focus:ring-2 focus:ring-warn-500 focus:bg-white border-2 border-transparent focus:border-warn-500"
                />
              </div>

              <button
                onClick={handleCreate}
                disabled={!form.title || creating}
                className="press-effect w-full py-[18px] bg-warn-500 text-gray-900 font-bold text-base rounded-2xl shadow-btn disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {creating ? "만드는 중..." : "QR 쿠폰 만들기"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 하단 네비게이션 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-5 py-2">
        <div className="flex justify-around max-w-md mx-auto">
          <NavItem icon="🏠" label="홈" active={pathname === "/dashboard"} onClick={() => router.push("/dashboard")} />
          <NavItem icon="💰" label="지원사업" active={pathname === "/subsidies"} onClick={() => router.push("/subsidies")} />
          <NavItem icon="📊" label="인사이트" active={pathname === "/insights"} onClick={() => router.push("/insights")} />
          <NavItem icon="🎟" label="쿠폰" active={pathname === "/coupons"} onClick={() => router.push("/coupons")} />
        </div>
      </nav>

      {/* QR 확대 모달 */}
      {zoomQR && (
        <div
          onClick={() => setZoomQR(null)}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-6"
          aria-modal="true"
          role="dialog"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-2xl p-6 max-w-sm w-full"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-gray-900">{zoomQR.title}</h2>
              <button
                onClick={() => setZoomQR(null)}
                aria-label="닫기"
                className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-gray-700"
              >
                ✕
              </button>
            </div>
            {zoomQR.qr_image_base64 && (
              <img
                src={zoomQR.qr_image_base64}
                alt="QR 코드 확대"
                className="w-full aspect-square rounded-xl bg-gray-50"
              />
            )}
            <p className="text-xs text-gray-500 text-center mt-3">
              사장님 손님이 카메라로 찍어서 사용해요
            </p>
            <button
              onClick={() => shareToKakao(zoomQR)}
              className="press-effect w-full py-3 mt-4 bg-warn-500 text-gray-900 font-bold text-sm rounded-xl"
            >
              카카오톡으로 공유
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function NavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="press-effect flex flex-col items-center gap-0.5 px-3 py-2"
    >
      <span className={`text-base ${active ? "" : "grayscale opacity-50"}`}>{icon}</span>
      <span className={`text-xs font-bold ${active ? "text-gray-900" : "text-gray-400"}`}>
        {label}
      </span>
    </button>
  );
}
