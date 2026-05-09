"""업종 taxonomy 정규화.

카카오 로컬 카테고리(`category_name`)의 두 번째 토큰("한식", "치킨", "분식" 등)을
시드 보조금의 canonical taxonomy("음식점", "카페", "소매업", "미용실" 등)로 매핑.

Round 2 검증 결과: 카카오 raw 저장 시 한식/치킨/분식/호프 페르소나 ~140명이
시드 보조금과 매칭 0건 (모든 시드가 "음식점"으로 등록).

ADR: backend·frontend 동시 정의 필요. 변경 시 양쪽 함께 수정.
대응 frontend 위치: src/lib/businessType.ts
"""

# canonical 10종 (시드 boundary와 일치)
TAXONOMY_MAP: dict[str, str] = {
    # 음식점 계열
    "한식": "음식점",
    "양식": "음식점",
    "일식": "음식점",
    "중식": "음식점",
    "치킨": "음식점",
    "분식": "음식점",
    "고기": "음식점",
    "패스트푸드": "음식점",
    "백반": "음식점",
    "찌개": "음식점",
    "해산물": "음식점",
    "도시락": "음식점",
    # 카페 계열
    "카페": "카페",
    "디저트": "카페",
    "베이커리": "카페",
    "커피": "카페",
    "커피전문점": "카페",
    "제과": "카페",
    # 소매업 계열
    "편의점": "소매업",
    "마트": "소매업",
    "슈퍼": "소매업",
    "전자상거래": "소매업",
    "문구": "소매업",
    "화장품": "소매업",
    # 의류
    "의류": "의류",
    "신발": "의류",
    "가방": "의류",
    # 미용실 계열
    "미용실": "미용실",
    "미용": "미용실",
    "네일": "미용실",
    "헤어": "미용실",
    # 호프·주점은 음식점 (시드에 호프 카테고리 없음)
    "호프": "음식점",
    "주점": "음식점",
    "술집": "음식점",
    # 학원·교육
    "학원": "학원",
    "교습": "학원",
    "보습": "학원",
    "교육": "교육",
    # 기타
    "세탁": "세탁소",
    "공방": "공방",
    "갤러리": "갤러리",
    "서점": "서점",
    "숙박": "숙박",
    "제조": "제조업",
    "수공예": "수공예",
}


def normalize_business_type(raw: str | None) -> str:
    """카카오 raw category → canonical taxonomy.

    - 매핑이 있으면 canonical 반환
    - 매핑이 없으면 입력 그대로 반환 (정규화 실패 fallback)
    - None/빈 문자열은 빈 문자열 반환
    """
    if not raw:
        return ""
    raw = raw.strip()
    if raw in TAXONOMY_MAP:
        return TAXONOMY_MAP[raw]
    # 부분 일치 (예: "커피전문점" → "커피전문점" 그대로 → "커피"로 fallback)
    for key, canonical in TAXONOMY_MAP.items():
        if key in raw:
            return canonical
    return raw  # 매핑 없으면 raw 보존 (Subsidy.target_business_types.any로 fallback 매칭 시도)
