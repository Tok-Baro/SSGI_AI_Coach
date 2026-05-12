"""심사위원 체험용 데모 계정 시드 (전부 가공 데이터 — 실존 인물·실제 사업자번호 없음).

- 데모 사장님: 관악구 신림동 입시 수학학원 (kakao_id 음수 sentinel)
- 최근 30일치 일일 액션 + 위험도 추이 + 일부 완료
- 쿠폰 3건 + 스캔 수
- 같은 업종(학원) 더미 또래 10명 — k≥10 또래 비교가 화면에 뜨도록

사용법:
  cd backend
  python -m scripts.seed_demo

멱등: 데모 사장님이 이미 25일치 이상 액션을 가지고 있으면 스킵.
Dockerfile CMD 에서 자동 실행되도록 연결되어 있음 (실패해도 앱 기동엔 영향 없음).
"""
import asyncio
import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, delete

from app.database import async_session_factory, init_db
from app.models.user import User
from app.models.daily_action import DailyAction
from app.models.coupon import CouponTemplate

# ── 데모 계정 식별자 (실제 카카오 ID 와 절대 안 겹치는 음수 sentinel) ──
DEMO_KAKAO_ID = -10001
PEER_KAKAO_IDS = list(range(-10011, -10001))  # -10011 .. -10002 (10명)

DEMO_PROFILE = dict(
    kakao_id=DEMO_KAKAO_ID,
    nickname="데모 사장님",
    business_name="또랑수학학원",
    business_type="학원",
    business_category="학원",
    industry_slug="academy.exam",
    address="서울특별시 관악구 신림동",
    dong_name="신림동",
    gu_name="관악구",
    plan_tier="free",
    onboarding_completed=True,
)

# 일일 액션 템플릿 — 입시 수학학원 맥락 (action_type, title, description, cta_type)
ACTION_TEMPLATES = [
    ("subsidy", "소상공인 컨설팅 사업, 신청 마감 임박",
     "경영·마케팅 1:1 방문 컨설팅 최대 5회 무료. 우리 학원 자격 조건 충족 — 신청 페이지로 가서 1분이면 끝나요.",
     "apply_subsidy"),
    ("competitor", "신림동에 신규 영어학원 1곳 개원 — 학부모 이탈 주의",
     "같은 상권에 새 학원이 열렸어요. 이번 주에 재원생 학부모께 '○○월 성적 향상 사례' 카톡 한 번 보내 단골을 단단히 잡으세요.",
     "view_detail"),
    ("event", "관악구 청소년 진로 박람회 — 이번 주말 개최",
     "근처에서 학부모·학생이 모이는 행사예요. 입구 배너 + 무료 진단 테스트 쿠폰 한 장이면 신규 상담이 들어옵니다.",
     "create_coupon"),
    ("coupon", "신학기 전 등록 유도 — 형제 동시 등록 쿠폰 발행",
     "지금이 다음 학기 등록을 미리 받을 타이밍이에요. '형제·자매 동시 등록 시 1개월 무료' 쿠폰을 카톡으로 한 번에 뿌리세요.",
     "create_coupon"),
    ("population", "신림동 저녁 7~9시 유동인구, 지난주 대비 12% 증가",
     "학원가 피크 시간대 사람이 늘었어요. 이 시간에 맞춰 등록 상담 안내 전단·플레이스 글을 올리면 노출이 큽니다.",
     "view_detail"),
    ("subsidy", "스마트상점 디지털화 지원 — 학원도 대상",
     "출결·결제 시스템, 온라인 홍보 제작비를 지원해요. 우리 업종(교육)도 신청 가능 — 자격 확인부터 해보세요.",
     "apply_subsidy"),
    ("competitor", "재원생 이탈 신호: 최근 14일 신규 문의 둔화",
     "문의가 평소보다 줄었어요. 네이버 플레이스 후기 요청 + 합격·성적 향상 사례 콘텐츠를 한 가지 올려보세요.",
     "view_detail"),
]

COUPONS = [
    dict(title="신규생 등록비 50% 할인", discount_type="percent", discount_value=50,
         description="처음 등록하는 학생 대상 · 진단 테스트 포함", scan_count=14, download_count=31),
    dict(title="형제·자매 동시 등록 시 1개월 무료", discount_type="free_item", discount_value=None,
         description="둘째부터 1개월 수강료 면제", scan_count=7, download_count=19),
    dict(title="친구 추천 시 교재비 지원", discount_type="fixed", discount_value=30000,
         description="추천한 재원생·새로 등록한 학생 모두 교재비 3만원 지원", scan_count=3, download_count=8),
]


async def _count_demo_actions(db, demo_id) -> int:
    return (await db.execute(
        select(func.count(DailyAction.id)).where(DailyAction.user_id == demo_id)
    )).scalar() or 0


async def seed_demo() -> None:
    await init_db()
    today = date.today()
    rnd = random.Random(42)  # 재현 가능

    async with async_session_factory() as db:
        # ── 데모 사장님 ──
        demo = (await db.execute(
            select(User).where(User.kakao_id == DEMO_KAKAO_ID)
        )).scalar_one_or_none()

        if demo is not None and await _count_demo_actions(db, demo.id) >= 25:
            print("데모 계정이 이미 시드되어 있음 — 스킵")
            return

        if demo is None:
            demo = User(**DEMO_PROFILE)
            db.add(demo)
            await db.flush()
        else:
            for k, v in DEMO_PROFILE.items():
                setattr(demo, k, v)
        # 개점 3년차 (학년도 시작월), 가입 30일 전
        demo.business_start_date = date(today.year - 3, 3, 2)
        demo.created_at = datetime.utcnow() - timedelta(days=30)
        await db.flush()

        # 기존 데모 액션·쿠폰 정리 후 재생성
        await db.execute(delete(DailyAction).where(DailyAction.user_id == demo.id))
        await db.execute(delete(CouponTemplate).where(CouponTemplate.user_id == demo.id))

        # ── 30일치 일일 액션 (위험도: 0.56 → 0.42 로 완만히 개선되는 스토리) ──
        n = 30
        for i in range(n):
            d = today - timedelta(days=(n - 1 - i))
            base = 0.56 - (0.14 * i / (n - 1))
            risk = round(min(0.85, max(0.20, base + rnd.uniform(-0.04, 0.04))), 3)
            tpl = ACTION_TEMPLATES[i % len(ACTION_TEMPLATES)]
            is_today = (d == today)
            completed = (not is_today) and (rnd.random() < 0.62)
            db.add(DailyAction(
                user_id=demo.id,
                date=d,
                action_type=tpl[0],
                title=tpl[1],
                description=tpl[2],
                risk_score=risk,
                data_source="서울 상권분석서비스 · 우리마을가게",
                cta_type=tpl[3],
                is_completed=completed,
                completed_at=(datetime.utcnow() - timedelta(days=(n - 1 - i)) + timedelta(hours=10)) if completed else None,
                created_at=datetime.utcnow() - timedelta(days=(n - 1 - i)),
            ))

        # ── 쿠폰 3건 ──
        for c in COUPONS:
            db.add(CouponTemplate(
                user_id=demo.id,
                title=c["title"],
                discount_type=c["discount_type"],
                discount_value=c["discount_value"],
                description=c["description"],
                valid_days=14,
                valid_from=today - timedelta(days=10),
                valid_until=today + timedelta(days=20),
                qr_data=f"demo-coupon-{rnd.randint(100000, 999999)}",
                qr_image_base64=None,
                download_count=c["download_count"],
                scan_count=c["scan_count"],
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=rnd.randint(3, 12)),
            ))

        # ── 더미 또래 10명 (학원, 최근 14일 위험도 보유 → k≥10 비교 활성화) ──
        peer_gus = ["관악구", "강남구", "노원구", "양천구", "동작구", "마포구", "성북구", "서대문구", "광진구", "은평구"]
        for idx, kid in enumerate(PEER_KAKAO_IDS):
            peer = (await db.execute(
                select(User).where(User.kakao_id == kid)
            )).scalar_one_or_none()
            if peer is None:
                peer = User(
                    kakao_id=kid,
                    nickname=f"동종업종 사장님{idx + 1}",
                    business_name=f"○○학원 {idx + 1}호",
                    business_type="학원",
                    business_category="학원",
                    industry_slug="academy",
                    dong_name=None,
                    gu_name=peer_gus[idx % len(peer_gus)],
                    plan_tier="free",
                    onboarding_completed=True,
                    business_start_date=date(today.year - rnd.randint(1, 6), rnd.randint(1, 12), 5),
                    created_at=datetime.utcnow() - timedelta(days=rnd.randint(20, 90)),
                )
                db.add(peer)
                await db.flush()
            # 또래 액션 정리 후 최근 14일 중 4~6일치 위험도 생성 (날짜 중복 없이 — UniqueConstraint)
            await db.execute(delete(DailyAction).where(DailyAction.user_id == peer.id))
            peer_level = rnd.uniform(0.40, 0.72)
            day_offsets = rnd.sample(range(14), rnd.randint(4, 6))
            for off in day_offsets:
                db.add(DailyAction(
                    user_id=peer.id,
                    date=today - timedelta(days=off),
                    action_type="population",
                    title="(또래 표본) 일일 진단",
                    description="또래 비교용 합성 데이터",
                    risk_score=round(min(0.9, max(0.2, peer_level + rnd.uniform(-0.05, 0.05))), 3),
                    is_completed=rnd.random() < 0.5,
                    created_at=datetime.utcnow() - timedelta(days=off),
                ))

        await db.commit()

    print(f"데모 시드 완료 — 사장님 1명(또랑수학학원·신림동) + 30일 액션 + 쿠폰 {len(COUPONS)}건 + 또래 {len(PEER_KAKAO_IDS)}명")


if __name__ == "__main__":
    asyncio.run(seed_demo())
