"""
보조금 시드 데이터 삽입 + ChromaDB 인덱싱 스크립트.

사용법:
  cd backend
  python -m scripts.seed_subsidies
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from sqlalchemy import select
from app.database import engine, async_session_factory as AsyncSessionLocal, init_db
from app.models.subsidy import Subsidy
from app.services.rag_service import RAGService
from app.utils.subsidy_tags import infer_subsidy_category_tags

# 서울시 소상공인 대상 실제/유사 보조금 시드 데이터 (15건)
SEED_SUBSIDIES = [
    {
        "title": "소상공인 경영안정자금",
        "organization": "서울시 경제정책과",
        "deadline": date(2026, 6, 30),
        "max_amount": 3000,
        "target_business_types": ["음식점", "카페", "소매업", "서비스업"],
        "target_regions": ["서울시 전체"],
        "eligibility_summary": "서울시 소재 소상공인, 매출 10억 이하",
        "description": "서울시 소상공인 경영안정자금은 코로나19 이후 매출 감소를 겪은 소상공인에게 최대 3,000만원의 경영안정자금을 지원합니다. 신청 자격은 서울시에 사업장을 둔 소상공인으로, 연매출 10억원 이하인 업체입니다. 자금은 운전자금 및 시설개선 용도로 활용할 수 있습니다.",
        "application_url": "https://seoulsbdc.or.kr",
        "source": "서울시 소상공인지원센터",
    },
    {
        "title": "청년 창업 지원금",
        "organization": "서울시 청년정책과",
        "deadline": date(2026, 5, 15),
        "max_amount": 5000,
        "target_business_types": ["전 업종"],
        "target_regions": ["서울시 전체"],
        "eligibility_summary": "만 19~39세 서울시 소재 창업 3년 이내",
        "description": "청년 창업자를 위한 지원금으로, 사업 운영에 필요한 임차료, 인테리어, 마케팅 비용 등을 최대 5,000만원까지 지원합니다. 창업 3년 이내 청년 사업자가 대상이며, 사업계획서 심사를 통해 선정됩니다.",
        "application_url": "https://youth.seoul.go.kr",
        "source": "서울시 청년정책",
    },
    {
        "title": "소상공인 디지털 전환 지원",
        "organization": "중소벤처기업부",
        "deadline": date(2026, 7, 31),
        "max_amount": 500,
        "target_business_types": ["음식점", "카페", "소매업", "미용실"],
        "target_regions": ["전국"],
        "eligibility_summary": "소상공인 확인서 보유 업체",
        "description": "소상공인의 디지털 전환을 위해 키오스크, POS, 배달앱 연동, 온라인 쇼핑몰 구축 등의 비용을 최대 500만원까지 지원합니다. 소상공인 확인서를 보유한 업체라면 누구나 신청 가능합니다.",
        "application_url": "https://www.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "강남구 소상공인 임차료 보조",
        "organization": "강남구청",
        "deadline": date(2026, 4, 30),
        "max_amount": 200,
        "target_business_types": ["음식점", "카페", "소매업"],
        "target_regions": ["강남구"],
        "eligibility_summary": "강남구 소재 소상공인, 임차료 월 300만원 이하",
        "description": "강남구 소재 소상공인의 임차료 부담 경감을 위해 월 최대 50만원, 최장 4개월간 임차료를 보조합니다. 대상은 강남구에 사업장을 둔 소상공인으로, 월 임차료가 300만원 이하인 업체입니다.",
        "application_url": "https://www.gangnam.go.kr",
        "source": "강남구 경제과",
    },
    {
        "title": "종로구 전통시장 활성화 지원",
        "organization": "종로구청",
        "deadline": date(2026, 5, 31),
        "max_amount": 300,
        "target_business_types": ["음식점", "소매업", "의류"],
        "target_regions": ["종로구"],
        "eligibility_summary": "종로구 전통시장 입점 소상공인",
        "description": "종로구 전통시장 활성화를 위해 시설 현대화, 마케팅, 공동 이벤트 등의 비용을 지원합니다. 종로구 소재 전통시장에 입점한 소상공인이 대상이며, 최대 300만원까지 지원받을 수 있습니다.",
        "application_url": "https://www.jongno.go.kr",
        "source": "종로구 경제과",
    },
    {
        "title": "마포구 로컬크리에이터 지원",
        "organization": "마포구청",
        "deadline": date(2026, 6, 15),
        "max_amount": 1000,
        "target_business_types": ["카페", "공방", "서점", "갤러리"],
        "target_regions": ["마포구"],
        "eligibility_summary": "마포구 소재 문화·창작 관련 소상공인",
        "description": "마포구의 로컬크리에이터를 위한 지원금으로, 공간 조성, 콘텐츠 제작, 커뮤니티 활동 등에 최대 1,000만원을 지원합니다. 카페, 공방, 서점, 갤러리 등 문화·창작 관련 업종이 대상입니다.",
        "application_url": "https://www.mapo.go.kr",
        "source": "마포구 문화체육과",
    },
    {
        "title": "소상공인 에너지 절감 설비 지원",
        "organization": "서울시 기후환경본부",
        "deadline": date(2026, 8, 31),
        "max_amount": 400,
        "target_business_types": ["음식점", "카페", "세탁소", "미용실"],
        "target_regions": ["서울시 전체"],
        "eligibility_summary": "서울시 소재 소상공인, 에너지 다소비 업종",
        "description": "에너지 고효율 설비(LED, 냉난방기, 단열 등) 교체 비용을 최대 400만원까지 지원합니다. 에너지 사용량이 많은 업종인 음식점, 카페, 세탁소, 미용실 등이 우선 대상입니다.",
        "application_url": "https://energysave.seoul.go.kr",
        "source": "서울시 기후환경본부",
    },
    {
        "title": "소상공인 스마트 상점 구축",
        "organization": "소상공인시장진흥공단",
        "deadline": date(2026, 5, 20),
        "max_amount": 1000,
        "target_business_types": ["소매업", "음식점", "카페"],
        "target_regions": ["전국"],
        "eligibility_summary": "소상공인 확인서 보유, ICT 활용 의지",
        "description": "오프라인 매장의 스마트화를 위해 키오스크, 디지털 사이니지, 스마트 주문 시스템 등 ICT 설비 도입 비용을 최대 1,000만원까지 지원합니다.",
        "application_url": "https://www.semas.or.kr/web/SUP/SMP_01.kmdc",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "서초구 소상공인 홍보비 지원",
        "organization": "서초구청",
        "deadline": date(2026, 4, 20),
        "max_amount": 150,
        "target_business_types": ["전 업종"],
        "target_regions": ["서초구"],
        "eligibility_summary": "서초구 소재 소상공인",
        "description": "서초구 소재 소상공인의 온오프라인 홍보 활동 비용을 최대 150만원까지 지원합니다. SNS 마케팅, 간판 제작, 전단지 인쇄 등이 포함됩니다.",
        "application_url": "https://www.seocho.go.kr",
        "source": "서초구 경제과",
    },
    {
        "title": "성동구 소셜벤처 육성 지원",
        "organization": "성동구청",
        "deadline": date(2026, 7, 15),
        "max_amount": 2000,
        "target_business_types": ["사회적기업", "카페", "교육", "서비스업"],
        "target_regions": ["성동구"],
        "eligibility_summary": "성동구 소재 사회적 가치 추구 소상공인",
        "description": "성동구의 소셜벤처 육성을 위해 사업 운영비, 공간 조성비, 멘토링 등을 지원합니다. 사회적 가치를 추구하는 소상공인이 대상이며 최대 2,000만원까지 지원됩니다.",
        "application_url": "https://www.sd.go.kr",
        "source": "성동구 경제진흥과",
    },
    {
        "title": "소상공인 재기 지원 특별자금",
        "organization": "신용보증재단",
        "deadline": None,
        "max_amount": 5000,
        "target_business_types": ["전 업종"],
        "target_regions": ["서울시 전체"],
        "eligibility_summary": "코로나 피해 소상공인, 연매출 3억 이하",
        "description": "코로나19로 인한 매출 감소 피해를 입은 소상공인에게 최대 5,000만원의 재기 지원 특별자금을 저금리로 대출합니다. 연매출 3억원 이하 소상공인이 대상이며, 상시 신청 가능합니다.",
        "application_url": "https://www.koreg.or.kr",
        "source": "서울신용보증재단",
    },
    {
        "title": "영등포구 여성 소상공인 창업 지원",
        "organization": "영등포구청",
        "deadline": date(2026, 6, 30),
        "max_amount": 800,
        "target_business_types": ["카페", "미용실", "유아", "교육"],
        "target_regions": ["영등포구"],
        "eligibility_summary": "영등포구 소재 여성 소상공인",
        "description": "영등포구 소재 여성 소상공인의 창업 및 사업 확장을 위해 최대 800만원의 사업비를 지원합니다. 창업 교육, 멘토링, 네트워킹 프로그램도 함께 제공됩니다.",
        "application_url": "https://www.ydp.go.kr",
        "source": "영등포구 여성가족과",
    },
    {
        "title": "소상공인 긴급 경영자금 보증",
        "organization": "서울시 소상공인지원센터",
        "deadline": date(2026, 12, 31),
        "max_amount": 7000,
        "target_business_types": ["전 업종"],
        "target_regions": ["서울시 전체"],
        "eligibility_summary": "서울시 소재 소상공인, 사업자등록증 보유",
        "description": "서울시 소상공인의 긴급 경영안정을 위해 최대 7,000만원의 보증 지원을 합니다. 보증비율 95%, 연 보증료율 0.8%로 저렴하게 이용 가능합니다.",
        "application_url": "https://seoulsbdc.or.kr",
        "source": "서울시 소상공인지원센터",
    },
    {
        "title": "중구 관광특구 소상공인 지원",
        "organization": "중구청",
        "deadline": date(2026, 5, 10),
        "max_amount": 500,
        "target_business_types": ["음식점", "카페", "기념품", "숙박"],
        "target_regions": ["중구"],
        "eligibility_summary": "중구 관광특구 소재 소상공인",
        "description": "명동, 남대문 등 관광특구에 위치한 소상공인을 위해 다국어 메뉴판, 외국인 응대 교육, 매장 환경 개선 등의 비용을 최대 500만원까지 지원합니다.",
        "application_url": "https://www.junggu.seoul.kr",
        "source": "중구 관광과",
    },
    {
        "title": "노원구 사회적경제 소상공인 지원",
        "organization": "노원구청",
        "deadline": date(2026, 6, 20),
        "max_amount": 600,
        "target_business_types": ["교육", "돌봄", "먹거리", "재활용"],
        "target_regions": ["노원구"],
        "eligibility_summary": "노원구 소재 사회적경제 관련 소상공인",
        "description": "노원구의 사회적경제 활성화를 위해 교육, 돌봄, 먹거리, 재활용 관련 소상공인에게 운영비, 마케팅비 등을 최대 600만원까지 지원합니다.",
        "application_url": "https://www.nowon.kr",
        "source": "노원구 사회적경제과",
    },
    # === 전국 대상 지원사업 (비서울 지역도 매칭) ===
    {
        "title": "소상공인 정책자금 (일반경영안정자금)",
        "organization": "중소벤처기업부",
        "deadline": date(2026, 12, 31),
        "max_amount": 7000,
        "target_business_types": ["전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "소상공인 확인서 보유, 업력 무관",
        "description": "소상공인의 경영안정을 위한 정책자금으로, 운전자금 및 시설자금을 최대 7,000만원까지 연 3.0~4.5% 금리로 지원합니다. 소상공인 확인서를 발급받은 모든 업체가 신청 가능합니다.",
        "application_url": "https://ols.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "소상공인 역량강화 교육",
        "organization": "소상공인시장진흥공단",
        "deadline": date(2026, 11, 30),
        "max_amount": 0,
        "target_business_types": ["전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "소상공인 및 예비 창업자",
        "description": "디지털 마케팅, 세무·회계, 고객관리, 메뉴개발 등 경영 역량강화 교육을 무료로 제공합니다. 온라인 과정도 있어 전국 어디서나 수강 가능합니다.",
        "application_url": "https://edu.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "소상공인 컨설팅 지원",
        "organization": "중소벤처기업부",
        "deadline": date(2026, 10, 31),
        "max_amount": 100,
        "target_business_types": ["전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "소상공인 확인서 보유 업체",
        "description": "경영, 마케팅, 세무, 법률, 기술 등 분야별 전문 컨설턴트가 1:1 방문 컨설팅을 최대 5회 무료 제공합니다. 소상공인시장진흥공단 지역센터에서 신청하세요.",
        "application_url": "https://www.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "소상공인 폐업 재기 지원",
        "organization": "중소벤처기업부",
        "deadline": None,
        "max_amount": 2000,
        "target_business_types": ["전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "폐업 후 재창업 또는 취업 희망 소상공인",
        "description": "폐업 소상공인의 재기를 위해 재기교육, 취업연계, 재창업자금(최대 2,000만원)을 지원합니다. 사업정리 컨설팅, 법률·세무 상담도 무료 제공됩니다.",
        "application_url": "https://www.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "소공인 특화자금",
        "organization": "중소벤처기업부",
        "deadline": date(2026, 9, 30),
        "max_amount": 5000,
        "target_business_types": ["제조업", "수공예", "전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "상시근로자 10인 미만 제조업",
        "description": "소공인(상시근로자 10인 미만 제조업)의 생산성 향상을 위해 설비자금 및 운전자금을 최대 5,000만원까지 저금리로 지원합니다.",
        "application_url": "https://ols.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
    {
        "title": "학원업 특화 경영개선 지원",
        "organization": "중소벤처기업부",
        "deadline": date(2026, 8, 31),
        "max_amount": 300,
        "target_business_types": ["학원", "교육", "전 업종"],
        "target_regions": ["전국"],
        "eligibility_summary": "학원법에 따른 등록 학원 운영 소상공인",
        "description": "학원업 소상공인의 온라인 교육 전환, 학사관리 시스템 구축, 홍보 마케팅 등을 최대 300만원까지 지원합니다. 대면·비대면 혼합 교육 환경 구축에 활용하세요.",
        "application_url": "https://www.semas.or.kr",
        "source": "소상공인시장진흥공단",
    },
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 기존 시드 데이터 확인
        result = await db.execute(select(Subsidy))
        existing = result.scalars().all()

        if existing:
            print(f"이미 {len(existing)}건의 보조금 데이터가 있습니다.")
            answer = input("초기화하고 다시 시드하시겠습니까? (y/N): ").strip().lower()
            if answer != "y":
                print("취소되었습니다.")
                return
            for s in existing:
                await db.delete(s)
            await db.commit()
            print("기존 데이터 삭제 완료.")

        # 시드 데이터 삽입
        subsidies = []
        for data in SEED_SUBSIDIES:
            # 카테고리 태그는 제목+설명에서 추론 (업종팩 매칭 부스트용)
            data["category_tags"] = infer_subsidy_category_tags(
                f"{data.get('title', '')} {data.get('description', '')}"
            ) or None
            subsidy = Subsidy(**data)
            db.add(subsidy)
            subsidies.append(subsidy)

        await db.commit()

        # ID 새로고침
        for s in subsidies:
            await db.refresh(s)

        print(f"\n{len(subsidies)}건의 보조금 시드 데이터 삽입 완료!")

        # ChromaDB 인덱싱
        print("\nChromaDB 인덱싱 시작...")
        rag = RAGService()
        indexed = 0

        for s in subsidies:
            text = f"{s.title}\n{s.organization}\n{s.description}\n{s.eligibility_summary or ''}"
            metadata = {
                "title": s.title,
                "organization": s.organization,
                "deadline": s.deadline.isoformat() if s.deadline else None,
                "max_amount": s.max_amount,
                "eligibility_summary": s.eligibility_summary or "",
                "application_url": s.application_url or "",
            }
            try:
                await rag.index_subsidy(str(s.id), text, metadata)
                s.embedding_id = str(s.id)
                indexed += 1
                print(f"  [{indexed}/{len(subsidies)}] {s.title}")
            except Exception as e:
                print(f"  [SKIP] {s.title}: {e}")

        await db.commit()
        print(f"\nChromaDB 인덱싱 완료: {indexed}/{len(subsidies)}건")
        print("\n총 잠재 지원금액:", sum(s.max_amount or 0 for s in subsidies), "만원")


if __name__ == "__main__":
    asyncio.run(seed())
