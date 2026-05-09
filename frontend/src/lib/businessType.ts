/**
 * 업종 taxonomy 정규화 (frontend).
 *
 * 카카오 로컬 `category_name`의 두 번째 토큰을 시드 보조금의 canonical
 * taxonomy로 매핑. 백엔드 `app/utils/business_type.py`와 동일한 매핑.
 *
 * 변경 시 backend 동시 수정 필수.
 */

// canonical 10종 (시드 boundary와 일치)
export const TAXONOMY_MAP: Record<string, string> = {
  // 음식점 계열
  "한식": "음식점", "양식": "음식점", "일식": "음식점", "중식": "음식점",
  "치킨": "음식점", "분식": "음식점", "고기": "음식점", "패스트푸드": "음식점",
  "백반": "음식점", "찌개": "음식점", "해산물": "음식점", "도시락": "음식점",
  // 카페 계열
  "카페": "카페", "디저트": "카페", "베이커리": "카페",
  "커피": "카페", "커피전문점": "카페", "제과": "카페",
  // 소매업
  "편의점": "소매업", "마트": "소매업", "슈퍼": "소매업",
  "전자상거래": "소매업", "문구": "소매업", "화장품": "소매업",
  // 의류
  "의류": "의류", "신발": "의류", "가방": "의류",
  // 미용실
  "미용실": "미용실", "미용": "미용실", "네일": "미용실", "헤어": "미용실",
  // 호프·주점은 음식점
  "호프": "음식점", "주점": "음식점", "술집": "음식점",
  // 학원·교육
  "학원": "학원", "교습": "학원", "보습": "학원", "교육": "교육",
  // 기타
  "세탁": "세탁소", "공방": "공방", "갤러리": "갤러리",
  "서점": "서점", "숙박": "숙박", "제조": "제조업", "수공예": "수공예",
};

/**
 * 카카오 raw category 토큰 → canonical taxonomy.
 * 매핑 없으면 입력 그대로 (Subsidy.target_business_types.any fallback).
 */
export function normalizeBusinessType(raw: string | null | undefined): string {
  if (!raw) return "";
  const trimmed = raw.trim();
  if (trimmed in TAXONOMY_MAP) return TAXONOMY_MAP[trimmed];
  for (const [key, canonical] of Object.entries(TAXONOMY_MAP)) {
    if (trimmed.includes(key)) return canonical;
  }
  return trimmed;
}
