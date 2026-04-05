"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { Coupon, CreateCouponRequest } from "@/types";

export default function CouponsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, checkAuth } = useAuth();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateCouponRequest>({
    title: "",
    discount_type: "percent",
    discount_value: 10,
    description: "",
    valid_days: 7,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.push("/"); return; }
    if (isAuthenticated) {
      api.listCoupons().then(setCoupons).finally(() => setLoading(false));
    }
  }, [isLoading, isAuthenticated, router]);

  const handleCreate = async () => {
    if (!form.title) return;
    setCreating(true);
    try {
      const coupon = await api.createCoupon(form);
      setCoupons([coupon, ...coupons]);
      setShowCreate(false);
      setForm({ title: "", discount_type: "percent", discount_value: 10, description: "", valid_days: 7 });
    } catch {}
    setCreating(false);
  };

  if (isLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400" />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <header className="bg-white px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.back()} className="text-gray-500">&larr;</button>
          <h1 className="text-lg font-bold text-gray-900">QR 쿠폰</h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-1.5 bg-yellow-400 text-gray-900 text-sm font-semibold rounded-lg"
        >
          + 새 쿠폰
        </button>
      </header>

      <div className="px-6 py-4 space-y-3">
        {coupons.map((c) => (
          <div key={c.id} className="bg-white rounded-xl p-4 border border-gray-100">
            <div className="flex gap-4">
              {c.qr_image_base64 && (
                <img src={c.qr_image_base64} alt="QR" className="w-20 h-20 rounded-lg" />
              )}
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{c.title}</h3>
                <p className="text-xs text-gray-500 mt-1">
                  {c.discount_type === "percent" && `${c.discount_value}% 할인`}
                  {c.discount_type === "fixed" && `${c.discount_value}원 할인`}
                  {c.discount_type === "bogo" && "1+1"}
                  {c.discount_type === "free_item" && "무료 증정"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {c.valid_from} ~ {c.valid_until}
                </p>
                <div className="flex gap-3 mt-2 text-xs">
                  <span className="text-gray-500">다운 {c.download_count}</span>
                  <span className="text-yellow-600 font-medium">스캔 {c.scan_count}</span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {coupons.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">아직 쿠폰이 없어요</p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-6 py-2 bg-yellow-400 text-gray-900 font-semibold rounded-xl"
            >
              첫 쿠폰 만들기
            </button>
          </div>
        )}
      </div>

      {/* 쿠폰 생성 모달 */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end">
          <div className="bg-white w-full rounded-t-2xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg text-gray-900">쿠폰 만들기</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 text-xl">&times;</button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">쿠폰명</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="예: 아메리카노 1+1"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">할인 유형</label>
                <select
                  value={form.discount_type}
                  onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl"
                >
                  <option value="percent">% 할인</option>
                  <option value="fixed">원 할인</option>
                  <option value="bogo">1+1</option>
                  <option value="free_item">무료 증정</option>
                </select>
              </div>

              {(form.discount_type === "percent" || form.discount_type === "fixed") && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {form.discount_type === "percent" ? "할인율 (%)" : "할인 금액 (원)"}
                  </label>
                  <input
                    type="number"
                    value={form.discount_value || ""}
                    onChange={(e) => setForm({ ...form, discount_value: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">유효기간 (일)</label>
                <input
                  type="number"
                  value={form.valid_days || 7}
                  onChange={(e) => setForm({ ...form, valid_days: parseInt(e.target.value) || 7 })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl"
                />
              </div>

              <button
                onClick={handleCreate}
                disabled={!form.title || creating}
                className="w-full py-3 bg-yellow-400 text-gray-900 font-semibold rounded-xl disabled:opacity-50"
              >
                {creating ? "생성 중..." : "QR 쿠폰 만들기"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
