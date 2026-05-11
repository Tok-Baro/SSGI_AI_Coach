"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import type { IndustryPackInfo, MyIndustryPack } from "@/types";

/** 내 가게 정보 — 온보딩 후에도 업종을 다시 고를 수 있는 개인 페이지. */
export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, checkAuth, refreshUser } = useAuth();
  const [industries, setIndustries] = useState<IndustryPackInfo[]>([]);
  const [myPack, setMyPack] = useState<MyIndustryPack | null>(null);
  const [industrySlug, setIndustrySlug] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/");
    if (!isLoading && isAuthenticated && user && !user.onboarding_completed) router.push("/onboarding");
  }, [isLoading, isAuthenticated, user, router]);

  const loadMyPack = () => {
    api
      .getMyIndustryPack()
      .then((p) => {
        setMyPack(p);
        setIndustrySlug(p.is_unknown ? "" : p.id);
      })
      .catch(() => {});
  };

  useEffect(() => {
    api.getIndustries().then(setIndustries).catch(() => {});
    loadMyPack();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setErr("");
    setMsg("");
    try {
      const res = await api.updateProfile({ industry_slug: industrySlug || undefined });
      setMsg(`업종이 "${res.industry_name ?? "미등록"}"(으)로 저장됐어요.`);
      await refreshUser();
      loadMyPack();
    } catch (e: any) {
      setErr(e?.message || "저장이 잠시 막혔어요. 다시 시도해 주세요.");
    } finally {
      setSaving(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-warn-500" />
      </div>
    );
  }

  const reviewed = myPack?.reviewed_date ? myPack.reviewed_date.replace(/-/g, ".") : null;

  return (
    <main className="min-h-screen bg-gray-50 pb-24">
      <header className="sticky top-0 z-10 bg-white px-5 py-5">
        <div className="mx-auto flex max-w-md items-center gap-3">
          <button onClick={() => router.back()} aria-label="뒤로" className="press-effect text-2xl text-gray-400">
            ‹
          </button>
          <h1 className="text-display-sm text-gray-900">내 가게 정보</h1>
        </div>
      </header>

      <div className="mx-auto max-w-md space-y-4 px-5 py-5">
        <div className="rounded-2xl border border-gray-100 bg-white p-5">
          <p className="mb-1 text-sm text-gray-500">상호</p>
          <p className="mb-3 text-base font-bold text-gray-900">{user.business_name || "—"}</p>
          {user.address ? (
            <>
              <p className="mb-1 text-sm text-gray-500">주소</p>
              <p className="mb-3 text-sm text-gray-700">{user.address}</p>
            </>
          ) : null}
          <p className="mb-1 text-sm text-gray-500">현재 업종</p>
          <p className="text-base font-bold text-gray-900">
            {myPack ? (myPack.is_unknown ? "미등록" : myPack.name) : "…"}
            {myPack && !myPack.is_unknown ? (
              <span className="ml-1 text-xs font-normal text-gray-400">
                플레이북 v{myPack.version}
                {reviewed ? ` · 검수 ${reviewed}` : ""}
              </span>
            ) : null}
          </p>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-5">
          <label className="block">
            <span className="text-base font-bold text-gray-900">업종 바꾸기</span>
            <p className="mb-3 mt-1 text-sm text-gray-500">
              업종에 맞춰 진단·마케팅 조언이 달라져요. (예: 학원 → 입시·교과 / 코딩·로봇 / 미술 / 체육 / 어학)
            </p>
            {industries.length === 0 ? (
              <p className="text-sm text-gray-400">불러오는 중…</p>
            ) : (
              <select
                value={industrySlug}
                onChange={(e) => setIndustrySlug(e.target.value)}
                className="w-full rounded-xl border-2 border-transparent bg-gray-50 px-4 py-3 text-base text-gray-900 focus:border-warn-500 focus:outline-none focus:ring-2 focus:ring-warn-500"
              >
                <option value="">자동 감지 (가게 카테고리로)</option>
                {industries
                  .filter((p) => p.group === null)
                  .sort((a, b) => a.priority - b.priority)
                  .flatMap((parent) => [
                    <option key={parent.id} value={parent.id}>
                      {parent.name}
                    </option>,
                    ...industries
                      .filter((p) => p.group === parent.id)
                      .sort((a, b) => a.priority - b.priority)
                      .map((child) => (
                        <option key={child.id} value={child.id}>
                          {"  ↳ "}
                          {child.name}
                        </option>
                      )),
                  ])}
              </select>
            )}
          </label>
          {err ? <p className="mt-3 text-sm font-medium text-loss-500">{err}</p> : null}
          {msg ? <p className="mt-3 text-sm font-medium text-green-700">{msg}</p> : null}
          <button
            onClick={handleSave}
            disabled={saving}
            className="press-effect mt-4 w-full rounded-xl bg-warn-500 py-3 text-base font-bold text-gray-900 disabled:opacity-60"
          >
            {saving ? "저장 중…" : "저장"}
          </button>
        </div>
      </div>
    </main>
  );
}
