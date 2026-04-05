"""손실 프레이밍 메시지 템플릿 라이브러리."""
from typing import Optional


# ===== 지원사업 카테고리 =====
def subsidy_deadline_urgent(subsidy_name: str, days_left: int, amount: int) -> str:
    return f"사장님, {subsidy_name} 마감 D-{days_left}입니다. {amount}만원, 안 하면 내년까지 없어요."


def subsidy_deadline_week(subsidy_name: str, social_proof: str) -> str:
    return f"사장님, {subsidy_name} 마감이 일주일 남았습니다. {social_proof}"


def subsidy_new_match(amount: int) -> str:
    return f"사장님 업종에 딱 맞는 지원금 {amount}만원을 놓치고 있습니다."


def subsidy_multiple_match(count: int, total_amount: int) -> str:
    return f"사장님, 지금 신청 가능한 지원금 {count}건, 최대 {total_amount}만원을 놓치고 있습니다."


# ===== 유동인구 카테고리 =====
def population_surge(dong_name: str, change: float) -> str:
    return f"오늘 {dong_name} 유동인구 {change}%↑ 예상인데 이벤트 없으면 놓쳐요."


def population_weekend_surge(change: float) -> str:
    return f"주말 유동인구 {change}%↑ 예상. 이벤트 없이 지나가면 기회 손실입니다."


def population_decline(change: float) -> str:
    return f"유동인구가 {abs(change)}% 줄었습니다. 쿠폰 이벤트로 고객을 붙잡으세요."


# ===== 매출 카테고리 =====
def sales_decline(change: float) -> str:
    return f"사장님 업종 매출이 전분기 대비 {abs(change)}% 감소했습니다. 대응이 필요합니다."


def competitor_event(count: int) -> str:
    return f"같은 동네 {count}곳이 이벤트 중인데, 사장님만 안 하고 계세요."


def weekly_no_event() -> str:
    return "이번 주 이벤트 없이 지나가고 있어요. 매출 기회를 놓치고 있습니다."


# ===== 문화행사 카테고리 =====
def nearby_event(event_name: str, days_left: int) -> str:
    return f"{event_name} D-{days_left}. 옆 가게가 이벤트 시작했는데, 사장님은요?"


def ongoing_event(event_name: str) -> str:
    return f"{event_name} 진행 중! 이벤트 연계 쿠폰으로 유입을 잡으세요."


# ===== 리텐션 (FOMO) =====
def retention_week1(coupon_count: int) -> str:
    return f"이번 주 쿠폰 만든 가게 {coupon_count}곳. 사장님은 아직 안 만드셨어요."


def retention_week2(amount: int) -> str:
    return f"옆 가게가 지원금 {amount}만원 받았대요. 사장님은 아직 미신청입니다."


def retention_monthly(hours: int) -> str:
    return f"이번 달 절약한 시간: {hours}시간. AI 경영코치가 대신 찾아드리고 있어요."


# ===== 메인 손실 메시지 생성 =====
def generate_loss_message(total_amount: int) -> str:
    """대시보드 메인 손실 프레이밍 메시지."""
    if total_amount > 0:
        return f"사장님, 연 {total_amount}만원을 놓치고 있습니다."
    return "사장님, 오늘의 기회를 확인하세요."
