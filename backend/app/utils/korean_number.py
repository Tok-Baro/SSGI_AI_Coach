"""한국식 수치 자연 표기 헬퍼 (백엔드).

PDF 정적 텍스트와 시스템 프롬프트 예시에 사용. AI 생성 텍스트는 프롬프트 룰로 처리.
"""
from __future__ import annotations


def korean_won(won: int | float) -> str:
    """원 단위를 한국식 만/억 표기로.

    예:
      1234       → "1,234원"
      58000      → "5만 8천원"
      5800000    → "580만원"
      58000000   → "5,800만원"
      125400000  → "1억 2,540만원"
      902628924  → "9억 263만원"
    """
    if won is None:
        return "0원"
    try:
        won = float(won)
    except (TypeError, ValueError):
        return "0원"
    abs_v = abs(won)
    sign = "-" if won < 0 else ""

    if abs_v >= 100_000_000:
        eok = int(abs_v // 100_000_000)
        remain_man = int((abs_v % 100_000_000) // 10_000)
        if remain_man == 0:
            return f"{sign}{eok}억원"
        return f"{sign}{eok}억 {remain_man:,}만원"
    if abs_v >= 10_000:
        man = int(abs_v // 10_000)
        remain_cheon = int((abs_v % 10_000) // 1_000)
        if remain_cheon == 0:
            return f"{sign}{man:,}만원"
        if man < 10:
            return f"{sign}{man}만 {remain_cheon}천원"
        return f"{sign}{man:,}만원"
    return f"{sign}{int(abs_v):,}원"


def korean_count(n: int | float, unit: str = "명") -> str:
    """큰 숫자를 한국 단위(만/억)로 짧게."""
    if n is None:
        return f"0{unit}"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return f"0{unit}"
    abs_v = abs(n)
    if abs_v < 10_000:
        return f"{int(n):,}{unit}"
    if abs_v < 100_000_000:
        return f"{round(abs_v / 10_000):,}만{unit}"
    eok = int(abs_v // 100_000_000)
    man = round((abs_v % 100_000_000) / 10_000)
    if man == 0:
        return f"{eok}억{unit}"
    return f"{eok}억 {man:,}만{unit}"


def korean_change(pct: float, up: str = "늘었어요", down: str = "줄었어요") -> str:
    """변화율을 사람 말투로."""
    if pct is None:
        return "변화 없음"
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return "변화 없음"
    abs_v = abs(pct)
    if abs_v < 0.5:
        return "거의 그대로예요"
    if abs_v >= 50:
        return f"{round(abs_v)}% {'급증했어요' if pct > 0 else '급감했어요'}"
    if abs_v < 2:
        return f"{abs_v:.1f}% {up if pct > 0 else down}"
    return f"{round(abs_v)}% {up if pct > 0 else down}"


def korean_d_day(days: int | None) -> str:
    """D-day 자연 표기."""
    if days is None:
        return "마감일 미정"
    try:
        days = int(days)
    except (TypeError, ValueError):
        return "마감일 미정"
    if days <= 0:
        return "오늘 마감"
    if days == 1:
        return "내일까지"
    if days <= 3:
        return f"{days}일 안에 마감"
    if days <= 7:
        return "이번 주 안에"
    if days <= 14:
        return "2주 안에"
    if days <= 30:
        return "한 달 안에"
    return f"{days}일 남음"
