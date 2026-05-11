"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MyIndustryPack } from "@/types";

/**
 * 진단/리포트 화면 출처칩.
 * "이 진단은 [업종명] 플레이북 v_n · 검수 YYYY.MM.DD 기준 · 출처 N건" — 클릭 시 출처 목록 펼침.
 * 업종 미등록(unknown)이거나 조회 실패 시 아무것도 렌더하지 않음 (조용히 사라짐).
 */
export default function IndustryPackChip() {
  const [pack, setPack] = useState<MyIndustryPack | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api.getMyIndustryPack().then(setPack).catch(() => {});
  }, []);

  if (!pack || pack.is_unknown) return null;

  const reviewed = pack.reviewed_date ? pack.reviewed_date.replace(/-/g, ".") : null;

  return (
    <div className="rounded-xl border border-gray-100 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="press-effect flex w-full items-center justify-between gap-2 px-3 py-2 text-left"
      >
        <span className="text-xs leading-relaxed text-gray-500">
          이 진단은 <b className="text-gray-700">{pack.name} 플레이북 v{pack.version}</b>
          {reviewed ? <> · 검수 {reviewed}</> : null} 기준 · 출처 {pack.source_count}건
        </span>
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden
          className={`h-3.5 w-3.5 shrink-0 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>
      {open ? (
        <div className="border-t border-gray-100 px-3 py-2">
          {pack.sources.length === 0 ? (
            <p className="text-xs text-gray-400">등록된 출처가 없어요.</p>
          ) : (
            <ul className="space-y-1">
              {pack.sources.map((s, i) => (
                <li key={i} className="text-xs leading-relaxed text-gray-500">
                  •{" "}
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                      {s.label}
                    </a>
                  ) : (
                    s.label
                  )}
                  {s.year ? ` (${s.year})` : ""}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-2 text-[11px] leading-relaxed text-gray-400">
            업종 평균·벤치마크 기반 추정값이 포함돼요. 사장님 가게 실제 수치와 다를 수 있어요.
          </p>
        </div>
      ) : null}
    </div>
  );
}
