"""주간 마케팅 PDF 리포트 생성 서비스.

zubair-trabzada/ai-marketing-claude의 6-카테고리 가중 점수 + 3-tier 액션 패턴을
우리 도메인(소상공인)에 맞춰 이식.
"""
import io
import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

logger = logging.getLogger(__name__)

# zubair 색상 팔레트
PRIMARY = colors.HexColor("#1B2A4A")
ACCENT = colors.HexColor("#2D5BFF")
HIGHLIGHT = colors.HexColor("#FF6B35")
SUCCESS = colors.HexColor("#00C853")
WARNING = colors.HexColor("#FFB300")
DANGER = colors.HexColor("#FF1744")
LIGHT_BG = colors.HexColor("#F5F7FA")
BODY = colors.HexColor("#2C3E50")
SECONDARY = colors.HexColor("#7F8C9B")
BORDER = colors.HexColor("#E0E6ED")

# 6-카테고리 가중치 (소상공인 도메인 매핑)
CATEGORIES = [
    ("매출 트렌드", 0.25),
    ("보조금 활용", 0.20),
    ("유동인구 활용", 0.20),
    ("경쟁 포지셔닝", 0.15),
    ("액션 실행률", 0.10),
    ("위험도 추세", 0.10),
]

_KOREAN_FONT: Optional[str] = None


def _register_korean_font() -> str:
    """한글 폰트 등록. TTF 우선, 실패 시 CID 폴백."""
    global _KOREAN_FONT
    if _KOREAN_FONT:
        return _KOREAN_FONT

    candidates = [
        os.environ.get("KOREAN_FONT_PATH"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    ]
    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        try:
            if path.endswith(".ttc"):
                pdfmetrics.registerFont(TTFont("KoreanFont", path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont("KoreanFont", path))
            _KOREAN_FONT = "KoreanFont"
            logger.info(f"Registered Korean font: {path}")
            return _KOREAN_FONT
        except Exception as e:
            logger.warning(f"Korean font registration failed for {path}: {e}")

    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    _KOREAN_FONT = "HYSMyeongJo-Medium"
    logger.info("Using fallback CID font: HYSMyeongJo-Medium")
    return _KOREAN_FONT


@dataclass
class CategoryScore:
    name: str
    weight: float
    score: int
    note: str


@dataclass
class Finding:
    severity: str
    text: str


@dataclass
class ReportData:
    business_name: str
    business_type: str
    location: str
    report_date: str
    overall_score: int
    executive_summary: str
    categories: list[CategoryScore]
    findings: list[Finding]
    quick_wins: list[str]
    medium_term: list[str]
    strategic: list[str]


# ===== 카테고리 점수 산출 =====

def _score_sales_trend(sales_data: Optional[dict]) -> CategoryScore:
    if not sales_data:
        return CategoryScore("매출 트렌드", 0.25, 50, "데이터 미제공 (서울 외 지역 가능성)")
    change = sales_data.get("quarterly_change_percent", 0) or 0
    if change >= 10:
        return CategoryScore("매출 트렌드", 0.25, 90, f"전분기 대비 +{change:.1f}% — 강한 성장")
    if change >= 0:
        return CategoryScore("매출 트렌드", 0.25, 72, f"전분기 대비 +{change:.1f}% — 안정적")
    if change >= -5:
        return CategoryScore("매출 트렌드", 0.25, 55, f"전분기 대비 {change:.1f}% — 약한 감소")
    if change >= -10:
        return CategoryScore("매출 트렌드", 0.25, 40, f"전분기 대비 {change:.1f}% — 주의 필요")
    return CategoryScore("매출 트렌드", 0.25, 22, f"전분기 대비 {change:.1f}% — 위기 단계")


def _score_subsidy(matches: list, total_amount: int) -> CategoryScore:
    count = len(matches) if matches else 0
    if count == 0:
        return CategoryScore("보조금 활용", 0.20, 35, "매칭 지원사업 0건 — 기회 손실")
    if count >= 5 or total_amount >= 5000:
        return CategoryScore(
            "보조금 활용", 0.20, 85,
            f"{count}건 매칭, 최대 {total_amount}만원 — 적극 활용 가능",
        )
    if count >= 3 or total_amount >= 2000:
        return CategoryScore(
            "보조금 활용", 0.20, 70,
            f"{count}건 매칭, 최대 {total_amount}만원 — 양호",
        )
    return CategoryScore(
        "보조금 활용", 0.20, 55,
        f"{count}건 매칭, 최대 {total_amount}만원 — 추가 발굴 필요",
    )


def _score_population(
    population_data: Optional[dict],
    coupon_created: int,
    coupon_scanned: int,
) -> CategoryScore:
    if not population_data:
        return CategoryScore("유동인구 활용", 0.20, 50, "유동인구 데이터 미제공")
    change = population_data.get("change_percent", 0) or 0
    base = 60 + min(max(change * 2, -20), 20)
    utilization = (coupon_scanned / coupon_created * 30) if coupon_created > 0 else 0
    score = int(min(base + utilization, 95))
    note = f"전일 대비 {change:+.1f}%, 쿠폰 활용 {coupon_scanned}/{coupon_created}건"
    return CategoryScore("유동인구 활용", 0.20, score, note)


def _score_competition(competition_data: Optional[dict]) -> CategoryScore:
    if not competition_data:
        return CategoryScore("경쟁 포지셔닝", 0.15, 50, "경쟁 데이터 미제공")
    opening = competition_data.get("opening_rate", 0) or 0
    closing = competition_data.get("closing_rate", 0) or 0
    total = competition_data.get("total_stores", 0) or 0
    if closing > opening + 2:
        return CategoryScore(
            "경쟁 포지셔닝", 0.15, 35,
            f"{total}개 점포, 폐업률 {closing}% > 개업률 {opening}% — 상권 축소",
        )
    if opening > closing + 2:
        return CategoryScore(
            "경쟁 포지셔닝", 0.15, 70,
            f"{total}개 점포, 개업률 {opening}% > 폐업률 {closing}% — 상권 확장",
        )
    return CategoryScore(
        "경쟁 포지셔닝", 0.15, 60,
        f"{total}개 점포, 개업률 {opening}% / 폐업률 {closing}% — 안정",
    )


def _score_action_completion(rate: float) -> CategoryScore:
    score = int(rate * 100)
    if score >= 80:
        note = f"{score}% 완료 — 우수"
    elif score >= 50:
        note = f"{score}% 완료 — 양호"
    elif score >= 30:
        note = f"{score}% 완료 — 더 실행 필요"
    else:
        note = f"{score}% 완료 — 액션 미실행 다수"
    return CategoryScore("액션 실행률", 0.10, max(score, 15), note)


def _score_risk_trend(trend_direction: Optional[str], current_risk: float) -> CategoryScore:
    inverse = max(0, int((1 - current_risk) * 100))
    if trend_direction == "improving":
        return CategoryScore(
            "위험도 추세", 0.10, min(inverse + 15, 95),
            f"개선 추세, 현재 위험도 {int(current_risk * 100)}점",
        )
    if trend_direction == "worsening":
        return CategoryScore(
            "위험도 추세", 0.10, max(inverse - 20, 15),
            f"악화 추세, 현재 위험도 {int(current_risk * 100)}점",
        )
    return CategoryScore(
        "위험도 추세", 0.10, inverse,
        f"유지 중, 현재 위험도 {int(current_risk * 100)}점",
    )


# ===== Findings + 액션 플랜 =====

def _build_findings(scores: list[CategoryScore]) -> list[Finding]:
    findings: list[Finding] = []
    for s in scores:
        if s.score < 40:
            findings.append(Finding("Critical", f"{s.name}: {s.note}"))
        elif s.score < 60:
            findings.append(Finding("High", f"{s.name}: {s.note}"))
        elif s.score < 75:
            findings.append(Finding("Medium", f"{s.name}: {s.note}"))
    if not findings:
        findings.append(Finding("Low", "모든 영역에서 양호한 성과를 보이고 있습니다."))
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    findings.sort(key=lambda f: severity_order.get(f.severity, 9))
    return findings


def _build_actions(
    scores: list[CategoryScore],
    matches: list,
    completion_rate: float,
    coupon_created: int,
) -> tuple[list[str], list[str], list[str]]:
    quick: list[str] = []
    medium: list[str] = []
    strategic: list[str] = []

    score_map = {s.name: s for s in scores}

    if completion_rate < 0.5:
        quick.append("오늘의 액션을 지금 완료하세요. 누적된 미실행 액션이 위험도를 높이고 있습니다.")
    if matches and score_map["보조금 활용"].score < 70:
        first = matches[0]
        days = first.get("days_until_deadline")
        amount = first.get("max_amount", 0) or 0
        deadline_text = f"D-{days}" if days is not None else "마감일 확인"
        quick.append(
            f"'{first.get('title', '매칭 지원사업')}' ({amount}만원, {deadline_text}) 지금 신청 페이지를 확인하세요."
        )
    if coupon_created == 0:
        quick.append("QR 쿠폰을 1개 만드세요. 지금 매장에 비치하는 것만으로 신규 유입 추적이 시작됩니다.")
    if not quick:
        quick.append("오늘 매장 SNS에 쿠폰 사진 1장 업로드 — 5분 작업으로 노출 시작.")

    if score_map["유동인구 활용"].score < 65:
        medium.append("피크 시간대(인사이트 리포트 참조)에 맞춘 시간 한정 쿠폰을 1주일 단위로 운영하세요.")
    if score_map["경쟁 포지셔닝"].score < 60:
        medium.append("주변 경쟁점 대비 차별화 포인트 1개를 메뉴/서비스에 명시하세요 (예: '50대 단골 추천 1위').")
    if len(matches) >= 2:
        medium.append("매칭된 보조금 2건 이상을 4주 안에 순차 신청 — 사업계획서 초안은 AI에 요청 가능합니다.")
    if not medium:
        medium.append("월간 매출 패턴을 인사이트 리포트로 분석해 약한 요일에 프로모션을 집중하세요.")

    if score_map["매출 트렌드"].score < 60:
        strategic.append("3개월 단위 매출 회복 플랜 — 신메뉴/배달 채널 추가/리뷰 관리 시스템화 검토.")
    if score_map["위험도 추세"].score < 55:
        strategic.append("분기별 경영 컨설팅 (서울신용보증재단 무료 컨설팅 활용) 정기화.")
    strategic.append("쿠폰 스캔 데이터를 누적해 단골 고객 패턴 분석 → 멤버십/재방문 유도 시스템 구축.")

    return quick[:5], medium[:5], strategic[:5]


def _build_executive_summary(
    business_name: str,
    overall_score: int,
    scores: list[CategoryScore],
    total_amount: int,
) -> str:
    grade = _grade_for(overall_score)
    weakest = min(scores, key=lambda s: s.score)
    parts = [f"{business_name}의 종합 마케팅 점수는 {overall_score}점({grade})입니다."]
    if weakest.score < 60:
        parts.append(f"가장 시급한 영역은 '{weakest.name}'({weakest.score}점)입니다.")
    if total_amount > 0:
        parts.append(f"매칭된 지원사업 총액 {total_amount}만원 중 미신청분이 발견되었습니다.")
    parts.append("아래 Quick Wins부터 1주 내 실행을 권장합니다.")
    return " ".join(parts)


# ===== 점수 → 등급/색 =====

def _grade_for(score: int) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def _color_for(score: int):
    if score >= 80: return SUCCESS
    if score >= 60: return ACCENT
    if score >= 40: return WARNING
    return DANGER


def _severity_color(severity: str):
    return {
        "Critical": DANGER,
        "High": HIGHLIGHT,
        "Medium": WARNING,
        "Low": ACCENT,
    }.get(severity, SECONDARY)


# ===== 공개 API: 데이터 조립 + PDF 생성 =====

def assemble_report_data(
    business_name: str,
    business_type: str,
    location: str,
    sales_data: Optional[dict],
    population_data: Optional[dict],
    competition_data: Optional[dict],
    subsidy_matches: list,
    total_potential_amount: int,
    coupon_created: int,
    coupon_scanned: int,
    action_completion_rate: float,
    risk_score: float,
    trend_direction: Optional[str],
) -> ReportData:
    """대시보드/인사이트 데이터를 ReportData로 조립."""
    scores = [
        _score_sales_trend(sales_data),
        _score_subsidy(subsidy_matches, total_potential_amount),
        _score_population(population_data, coupon_created, coupon_scanned),
        _score_competition(competition_data),
        _score_action_completion(action_completion_rate),
        _score_risk_trend(trend_direction, risk_score),
    ]
    overall = int(sum(s.score * s.weight for s in scores))
    quick, medium, strategic = _build_actions(
        scores, subsidy_matches or [], action_completion_rate, coupon_created
    )
    return ReportData(
        business_name=business_name or "사장님",
        business_type=business_type or "미등록",
        location=location or "미등록",
        report_date=date.today().strftime("%Y년 %m월 %d일"),
        overall_score=overall,
        executive_summary=_build_executive_summary(
            business_name, overall, scores, total_potential_amount
        ),
        categories=scores,
        findings=_build_findings(scores),
        quick_wins=quick,
        medium_term=medium,
        strategic=strategic,
    )


def generate_pdf(report: ReportData) -> bytes:
    """ReportData를 PDF 바이트로 렌더링."""
    font = _register_korean_font()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"{report.business_name} 주간 마케팅 리포트",
    )

    base = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=base["Heading1"], fontName=font,
                        fontSize=24, textColor=PRIMARY, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontName=font,
                        fontSize=16, textColor=PRIMARY, spaceAfter=6, spaceBefore=12)
    body = ParagraphStyle("body", parent=base["BodyText"], fontName=font,
                          fontSize=10.5, textColor=BODY, leading=15)
    meta = ParagraphStyle("meta", parent=base["BodyText"], fontName=font,
                          fontSize=9, textColor=SECONDARY, leading=13)
    score_big = ParagraphStyle("score_big", parent=base["Heading1"], fontName=font,
                               fontSize=64, textColor=_color_for(report.overall_score),
                               alignment=1, spaceAfter=4)

    story = []

    # ===== 1페이지: 표지 =====
    story.append(Paragraph("주간 마케팅 인사이트 리포트", h1))
    story.append(Paragraph(
        f"{report.business_name} · {report.business_type} · {report.location}",
        meta,
    ))
    story.append(Paragraph(f"발행일: {report.report_date}", meta))
    story.append(Spacer(1, 24))

    story.append(Paragraph(f"{report.overall_score}", score_big))
    story.append(Paragraph(
        f"<para align='center'>종합 점수 · 등급 {_grade_for(report.overall_score)}</para>",
        meta,
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(report.executive_summary, body))
    story.append(PageBreak())

    # ===== 2페이지: 카테고리 점수 =====
    story.append(Paragraph("카테고리별 평가", h2))
    rows = [["카테고리", "점수", "가중치", "상태"]]
    for s in report.categories:
        rows.append([
            s.name,
            str(s.score),
            f"{int(s.weight * 100)}%",
            s.note,
        ])
    tbl = Table(rows, colWidths=[32 * mm, 18 * mm, 18 * mm, 90 * mm])
    style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    for i, s in enumerate(report.categories, start=1):
        style.add("TEXTCOLOR", (1, i), (1, i), _color_for(s.score))
        style.add("FONTSIZE", (1, i), (1, i), 11)
    tbl.setStyle(style)
    story.append(tbl)
    story.append(Spacer(1, 12))

    # 막대 그래프 (Table 기반 시각화)
    story.append(Paragraph("점수 분포", h2))
    bar_rows = []
    for s in report.categories:
        filled = int(s.score / 5)
        bar = "█" * filled + "░" * (20 - filled)
        bar_rows.append([s.name, bar, f"{s.score}점"])
    bar_tbl = Table(bar_rows, colWidths=[32 * mm, 100 * mm, 22 * mm])
    bar_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTSIZE", (1, 0), (1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ])
    for i, s in enumerate(report.categories):
        bar_style.add("TEXTCOLOR", (1, i), (2, i), _color_for(s.score))
    bar_tbl.setStyle(bar_style)
    story.append(bar_tbl)
    story.append(PageBreak())

    # ===== 3페이지: Findings =====
    story.append(Paragraph("주요 진단", h2))
    finding_rows = [["심각도", "내용"]]
    for f in report.findings:
        finding_rows.append([f.severity, f.text])
    fnd_tbl = Table(finding_rows, colWidths=[24 * mm, 134 * mm])
    fnd_style = TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])
    for i, f in enumerate(report.findings, start=1):
        fnd_style.add("BACKGROUND", (0, i), (0, i), _severity_color(f.severity))
        fnd_style.add("TEXTCOLOR", (0, i), (0, i), colors.white)
    fnd_tbl.setStyle(fnd_style)
    story.append(fnd_tbl)
    story.append(PageBreak())

    # ===== 4페이지: 액션 플랜 =====
    story.append(Paragraph("액션 플랜", h2))

    def _action_block(title: str, sub: str, items: list[str], color):
        story.append(Spacer(1, 6))
        title_style = ParagraphStyle(
            f"act_{title}", parent=h2, fontSize=13, textColor=color, spaceAfter=2,
        )
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(sub, meta))
        for idx, item in enumerate(items, start=1):
            story.append(Paragraph(f"{idx}. {item}", body))

    _action_block("Quick Wins", "1주 안에 실행", report.quick_wins, SUCCESS)
    _action_block("Medium-Term", "1~3개월 실행", report.medium_term, ACCENT)
    _action_block("Strategic", "3~6개월 전략", report.strategic, HIGHLIGHT)

    # 마지막: 각주
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "본 리포트는 서울시 빅데이터 + 사장님 활동 데이터로 자동 생성되었습니다. "
        "수치는 보고서 발행 시점 기준이며, 실제 의사결정은 사장님의 판단을 따라야 합니다.",
        meta,
    ))

    doc.build(story)
    return buf.getvalue()
