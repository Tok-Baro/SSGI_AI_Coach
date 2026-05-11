/**
 * 한국식 수치 자연 표기 헬퍼.
 *
 * 원칙:
 * - Hero 숫자(큰 글씨, 시각 강조)는 정밀 유지 ("5,800,000원" / "67/100").
 * - **설명 문장 안 숫자**는 사람 말투로 부드럽게 (이 헬퍼들 사용).
 * - 천 단위 콤마는 항상 유지, "만/억" 단위는 자연스럽게.
 */

/**
 * 원 단위를 한국식 만/억 표기로.
 *   1,234       → "1,234원"
 *   58_000      → "5만 8천원"            (만 단위)
 *   5_800_000   → "580만원"
 *   58_000_000  → "5,800만원"
 *   125_400_000 → "1억 2,540만원"
 *   902_628_924 → "9억 263만원"          (만 단위 반올림)
 */
export function koreanWon(won: number): string {
  if (!Number.isFinite(won)) return "0원";
  const abs = Math.abs(won);
  const sign = won < 0 ? "-" : "";

  if (abs >= 100_000_000) {
    const eok = Math.floor(abs / 100_000_000);
    const remainMan = Math.floor((abs % 100_000_000) / 10_000);
    if (remainMan === 0) return `${sign}${eok}억원`;
    return `${sign}${eok}억 ${remainMan.toLocaleString()}만원`;
  }
  if (abs >= 10_000) {
    const man = Math.floor(abs / 10_000);
    const remainCheon = Math.floor((abs % 10_000) / 1_000);
    if (remainCheon === 0) return `${sign}${man.toLocaleString()}만원`;
    // 1만~9만 사이는 "X만 Y천원" 친근하게
    if (man < 10) return `${sign}${man}만 ${remainCheon}천원`;
    return `${sign}${man.toLocaleString()}만원`;
  }
  return `${sign}${abs.toLocaleString()}원`;
}

/**
 * 큰 숫자를 한국 단위(만/억)로 짧게.
 *   1247    → "1,247"
 *   12_470  → "1만 2천"
 *   1_247_000 → "약 125만"
 *   124_700_000 → "약 1억 2,470만"
 */
export function koreanCount(n: number, unit = "명"): string {
  if (!Number.isFinite(n)) return `0${unit}`;
  const abs = Math.abs(n);
  if (abs < 10_000) return `${n.toLocaleString()}${unit}`;
  if (abs < 100_000_000) {
    return `${Math.round(abs / 10_000).toLocaleString()}만${unit}`;
  }
  const eok = Math.floor(abs / 100_000_000);
  const man = Math.round((abs % 100_000_000) / 10_000);
  if (man === 0) return `${eok}억${unit}`;
  return `${eok}억 ${man.toLocaleString()}만${unit}`;
}

/**
 * 변화율을 사람 말투로.
 *   0.3   → "거의 그대로예요"
 *   8.3   → "8% 정도 늘었어요"
 *   -8.3  → "8% 정도 줄었어요"
 *   55    → "55% 급증했어요"
 */
export function koreanChange(pct: number, opts?: { up?: string; down?: string }): string {
  if (!Number.isFinite(pct)) return "변화 없음";
  const abs = Math.abs(pct);
  const up = opts?.up || "늘었어요";
  const down = opts?.down || "줄었어요";
  if (abs < 0.5) return "거의 그대로예요";
  if (abs >= 50) return `${Math.round(abs)}% ${pct > 0 ? "급증했어요" : "급감했어요"}`;
  if (abs < 2) return `${abs.toFixed(1)}% ${pct > 0 ? up : down}`;
  return `${Math.round(abs)}% ${pct > 0 ? up : down}`;
}

/**
 * D-day 자연 표기.
 *   0~음수 → "오늘 마감"
 *   1     → "내일까지"
 *   2~3   → "N일 안에 마감"
 *   4~7   → "이번 주 안에"
 *   8~14  → "2주 안에"
 *   15~30 → "한 달 안에"
 *   30+   → "N일 남음"
 */
export function koreanDDay(days: number | null | undefined): string {
  if (days == null || !Number.isFinite(days)) return "마감일 미정";
  if (days <= 0) return "오늘 마감";
  if (days === 1) return "내일까지";
  if (days <= 3) return `${days}일 안에 마감`;
  if (days <= 7) return "이번 주 안에";
  if (days <= 14) return "2주 안에";
  if (days <= 30) return "한 달 안에";
  return `${days}일 남음`;
}

/**
 * 짧은 D-day (배지/칩용).
 *   0~음수 → "오늘 마감"
 *   1~30  → "D-N"
 *   30+   → "한 달 이상"
 */
export function dDayShort(days: number | null | undefined): string {
  if (days == null || !Number.isFinite(days)) return "—";
  if (days <= 0) return "오늘 마감";
  if (days > 30) return "한 달 이상";
  return `D-${days}`;
}

/**
 * 점수(0~100) → "67점 (B등급)" 식.
 */
export function koreanScore(score: number, total = 100): string {
  if (!Number.isFinite(score)) return "—";
  return `${Math.round(score)}점 / ${total}점`;
}
