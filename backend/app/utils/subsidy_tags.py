"""지원사업 카테고리 태그 — 업종 지식팩의 subsidy_tags 와 같은 분류 체계.

공고 제목/설명 텍스트에서 카테고리를 추론한다(시드 적재·외부 인제스트 공통).
업종팩(app/knowledge)의 subsidy_tags 와 교집합이 크면 RAG 매칭에서 점수를 부스트.

태그 분류 (소진공/중기부/서울시 사업 유형 기준):
  policy_loan / credit_guarantee / consulting / digital / store_renovation /
  education / restart_exit / employment / marketing / rnd / rent_utility /
  commercial_district / voucher / tax_relief
"""
from __future__ import annotations

SUBSIDY_CATEGORY_TAGS: tuple[str, ...] = (
    "policy_loan",        # 정책자금(저금리 융자)
    "credit_guarantee",   # 신용보증
    "consulting",         # 컨설팅·경영개선
    "digital",            # 디지털 전환(스마트상점·온라인 판로·키오스크·POS)
    "store_renovation",   # 점포환경개선(간판·인테리어·설비)
    "education",          # 교육·역량강화
    "restart_exit",       # 재기·폐업지원
    "employment",         # 고용·인건비
    "marketing",          # 마케팅·홍보·판로
    "rnd",                # R&D·소공인 제조혁신
    "rent_utility",       # 임대료·공공요금·에너지
    "commercial_district",# 지역상권·전통시장·로컬·관광특구·사회적경제
    "voucher",            # 바우처·통합지원
    "tax_relief",         # 세제·부담완화
)

_TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "policy_loan": ("정책자금", "경영안정자금", "특별자금", "특화자금", "긴급 경영자금", "운전자금", "시설자금", "융자", "저금리"),
    "credit_guarantee": ("신용보증", "특례보증", "보증재단", "보증"),
    "consulting": ("컨설팅", "경영진단", "자영업클리닉"),
    "digital": ("디지털", "스마트 상점", "스마트상점", "온라인 판로", "온라인판로", "e커머스", "이커머스", "키오스크", "pos", "비대면"),
    "store_renovation": ("점포환경", "점포 환경", "환경 개선", "환경개선", "간판", "인테리어", "설비 지원", "시설 개선", "노후 시설"),
    "education": ("역량강화", "교육", "사관학교", "아카데미", "직무교육", "창업교육"),
    "restart_exit": ("재기", "폐업", "재창업", "재도전", "사업정리", "전직"),
    "employment": ("고용", "인건비", "일자리", "두루누리", "사회보험"),
    "marketing": ("마케팅", "홍보", "판로", "라이브커머스", "라이브 커머스", "홍보비", "판촉"),
    "rnd": ("기술개발", "r&d", "rnd", "소공인", "스마트제조", "생산성 향상"),
    "rent_utility": ("임차료", "임대료", "에너지 절감", "에너지절감", "공공요금", "전기요금", "가스요금"),
    "commercial_district": ("전통시장", "상권 활성화", "상권활성화", "로컬크리에이터", "로컬 크리에이터", "골목상권", "관광특구", "사회적경제", "소셜벤처", "소셜 벤처", "전통 시장"),
    "voucher": ("바우처",),
    "tax_relief": ("세액공제", "세제", "감면"),
}


def infer_subsidy_category_tags(text: str | None) -> list[str]:
    """공고 제목+설명 텍스트에서 카테고리 태그 추론 (소문자 부분일치). 없으면 빈 리스트."""
    if not text:
        return []
    low = text.lower()
    return [tag for tag, kws in _TAG_KEYWORDS.items() if any(kw in low for kw in kws)]
