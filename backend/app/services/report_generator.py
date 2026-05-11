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
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie

from app.utils.industry import industry_report_weights, classify_industry

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
    ("코치 활용도", 0.10),
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
    # 집중분석(deep-report) JSON — 있으면 PDF 뒷부분에 추가 섹션 렌더링
    deep_report: Optional[dict] = None


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
    """AI 코치 액션 활용도 — 외부 마케팅 활동과 별개의 앱 내 지표."""
    score = int(rate * 100)
    if score >= 80:
        note = f"앱 액션 {score}% 완료 — 활발히 사용 중"
    elif score >= 50:
        note = f"앱 액션 {score}% 완료 — 꾸준히 사용 중"
    elif score >= 30:
        note = f"앱 액션 {score}% 완료 — 더 활용해 보세요"
    else:
        note = f"앱 액션 {score}% 완료 — AI 코치 활용도 낮음 (외부 마케팅과 별개)"
    return CategoryScore("코치 활용도", 0.10, max(score, 15), note)


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
    from app.utils.korean_number import korean_d_day  # 지연 import (순환 방지)

    quick: list[str] = []
    medium: list[str] = []
    strategic: list[str] = []

    score_map = {s.name: s for s in scores}

    if completion_rate < 0.5:
        quick.append("오늘의 액션을 지금 끝내 보세요. 미실행이 쌓이면 위험도가 더 올라가요.")
    if matches and score_map["보조금 활용"].score < 70:
        first = matches[0]
        days = first.get("days_until_deadline")
        amount = first.get("max_amount", 0) or 0
        deadline_text = korean_d_day(days)
        quick.append(
            f"'{first.get('title', '매칭 지원사업')}' (최대 {amount}만원, {deadline_text}) 신청 페이지부터 들여다보세요."
        )
    if coupon_created == 0:
        quick.append("QR 쿠폰 1개만 만들어서 매장에 붙여 보세요. 신규 손님 유입을 그날부터 추적할 수 있어요.")
    if not quick:
        quick.append("매장 SNS에 쿠폰 사진 1장만 올려 보세요. 5분이면 끝나요.")

    if score_map["유동인구 활용"].score < 65:
        medium.append("손님 몰리는 시간대에 맞춰 시간 한정 쿠폰을 1주 단위로 돌려 보세요. (인사이트 리포트 참고)")
    if score_map["경쟁 포지셔닝"].score < 60:
        medium.append("옆 가게가 못 가진 우리만의 포인트 1개를 메뉴나 서비스에 박아 보세요 (예: '50대 단골 추천 1위').")
    if len(matches) >= 2:
        medium.append("매칭된 보조금 2건 이상이면 4주 안에 순차 신청해 보세요. 사업계획서 초안은 AI가 도와드려요.")
    if not medium:
        medium.append("월간 매출 패턴을 인사이트 리포트로 살펴보고, 약한 요일에 프로모션을 몰아 보세요.")

    if score_map["매출 트렌드"].score < 60:
        strategic.append("3개월 단위 매출 회복 플랜을 세워 보세요. 신메뉴·배달 채널·리뷰 관리 자동화부터.")
    if score_map["위험도 추세"].score < 55:
        strategic.append("분기마다 한 번씩 경영 컨설팅을 받아 보세요. 서울신용보증재단 무료 컨설팅이 있어요.")
    strategic.append("쿠폰 스캔 데이터가 쌓이면 단골 패턴 분석 → 멤버십·재방문 유도까지 한 번에 가능해요.")

    return quick[:5], medium[:5], strategic[:5]


def _build_executive_summary(
    business_name: str,
    overall_score: int,
    scores: list[CategoryScore],
    total_amount: int,
) -> str:
    from app.utils.korean_number import korean_won

    grade = _grade_for(overall_score)
    weakest = min(scores, key=lambda s: s.score)
    parts = [f"{business_name}의 종합 마케팅 점수는 {overall_score}점({grade})이에요."]
    if weakest.score < 60:
        parts.append(f"지금 가장 급한 곳은 '{weakest.name}' ({weakest.score}점)이에요.")
    if total_amount > 0:
        # total_amount는 만원 단위 → 원 단위로 변환 후 한국식 표기
        parts.append(f"매칭된 지원사업 {korean_won(total_amount * 10_000)} 중 신청 안 한 게 있어요.")
    parts.append("아래 Quick Wins부터 1주 안에 시작해 보세요.")
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
    deep_report: Optional[dict] = None,
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
    # 업종별 가중치 재배분 (편의점은 유동인구 ↑, 미용은 보조금 ↑, 치킨은 매출/경쟁 ↑)
    industry_weights = industry_report_weights(business_type)
    for s in scores:
        if s.name in industry_weights:
            s.weight = industry_weights[s.name]
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
        deep_report=deep_report,
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
                        fontSize=22, textColor=PRIMARY, spaceAfter=4, spaceBefore=0)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontName=font,
                        fontSize=14, textColor=PRIMARY, spaceAfter=4, spaceBefore=8)
    body = ParagraphStyle("body", parent=base["BodyText"], fontName=font,
                          fontSize=10.5, textColor=BODY, leading=15, spaceAfter=4)
    meta = ParagraphStyle("meta", parent=base["BodyText"], fontName=font,
                          fontSize=9, textColor=SECONDARY, leading=12, spaceAfter=2)
    # 점수 hero — leading 명시로 라벨과 겹침 방지
    score_color = _color_for(report.overall_score)
    score_big = ParagraphStyle("score_big", parent=base["Heading1"], fontName=font,
                               fontSize=72, textColor=score_color,
                               alignment=1, leading=80, spaceAfter=0, spaceBefore=0)
    score_label = ParagraphStyle("score_label", parent=base["BodyText"], fontName=font,
                                  fontSize=11, textColor=SECONDARY, alignment=1, leading=14, spaceAfter=0)
    metric_value = ParagraphStyle("metric_value", parent=base["BodyText"], fontName=font,
                                   fontSize=18, textColor=PRIMARY, alignment=1, leading=22, spaceAfter=2)
    metric_label = ParagraphStyle("metric_label", parent=base["BodyText"], fontName=font,
                                   fontSize=8.5, textColor=SECONDARY, alignment=1, leading=11)

    story = []

    # ===== 1페이지: 표지 (점수 카드 + AI 진단 + 핵심 지표 + 인덱스) =====
    story.append(Paragraph("우리 가게 진단서", h1))
    story.append(Paragraph(
        f"{report.business_name} · {report.business_type} · {report.location}",
        meta,
    ))
    story.append(Paragraph(f"발행일: {report.report_date}", meta))
    story.append(Spacer(1, 14))

    # 점수 카드 (Table로 score + label을 셀 단위 분리 → 겹침 0)
    grade = _grade_for(report.overall_score)
    score_card = Table(
        [
            [Paragraph(f"<para align='center'>{report.overall_score}</para>", score_big)],
            [Paragraph(f"<para align='center'>종합 점수 · 등급 {grade}</para>", score_label)],
        ],
        colWidths=[174 * mm],
    )
    score_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 1), LIGHT_BG),
        ("BOX", (0, 0), (0, 1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (0, 0), 14),
        ("BOTTOMPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 14),
    ]))
    story.append(score_card)
    story.append(Spacer(1, 14))

    # AI 종합 진단 (있으면 우선, 없으면 generic)
    ai_summary_text = ""
    if report.deep_report and isinstance(report.deep_report, dict):
        es_cover = report.deep_report.get("executive_summary")
        if isinstance(es_cover, dict):
            ai_summary_text = es_cover.get("current") or es_cover.get("summary") or ""
        elif isinstance(es_cover, str):
            ai_summary_text = es_cover
    ai_summary_text = _strip_evidence_tags(ai_summary_text)

    story.append(Paragraph("AI 종합 진단", h2))
    if ai_summary_text and ai_summary_text.strip():
        story.append(Paragraph(ai_summary_text, body))
        story.append(Spacer(1, 2))
        story.append(Paragraph(report.executive_summary, meta))
    else:
        story.append(Paragraph(report.executive_summary, body))
    story.append(Spacer(1, 14))

    # 핵심 지표 미리보기 (3카드 가로 배치)
    weakest = min(report.categories, key=lambda s: s.score)
    strongest = max(report.categories, key=lambda s: s.score)

    def _metric_inner(value: str, label1: str, label2: str) -> Table:
        inner = Table(
            [
                [Paragraph(f"<para align='center'>{value}</para>", metric_value)],
                [Paragraph(f"<para align='center'>{label1}</para>", metric_label)],
                [Paragraph(f"<para align='center'>{label2}</para>", metric_label)],
            ],
            colWidths=[55 * mm],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return inner

    metric_cards = Table(
        [[
            _metric_inner(f"{strongest.score}점", strongest.name, "가장 잘 하고 있어요"),
            _metric_inner(f"{weakest.score}점", weakest.name, "지금 가장 급해요"),
            _metric_inner(f"{report.overall_score}점", f"종합 등급 {grade}", "6개 영역 평균"),
        ]],
        colWidths=[58 * mm, 58 * mm, 58 * mm],
    )
    metric_cards.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(metric_cards)
    story.append(Spacer(1, 12))

    # 이 리포트가 담은 것
    story.append(Paragraph("이 리포트가 담은 것", h2))
    toc_items = [
        "1. 카테고리별 평가 (6개 영역 점수 + 분포 차트)",
        "2. 주요 진단 (Critical/High/Medium 6건)",
        "3. 액션 플랜 (Quick / Medium-Term / Strategic)",
    ]
    if report.deep_report and isinstance(report.deep_report, dict):
        toc_items.extend([
            "4. AI 집중 진단 (시급한 신호 + 추천 한 수)",
            "5. 강점·약점·기회·위협 + 전략 도출",
            "6. 단골·시간·경쟁·트렌드 + 시각 차트",
            "7. AI 추천 액션 우선순위 + 이번 달 KPI",
        ])
    for t in toc_items:
        story.append(Paragraph(t, body))
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
    story.append(Spacer(1, 8))

    # 막대 그래프 (Table 기반 시각화)
    story.append(Paragraph("점수 분포", h2))
    bar_rows = []
    for s in report.categories:
        filled = max(0, min(20, int(s.score / 5)))
        bar = "■" * filled + "□" * (20 - filled)
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
    story.append(Spacer(1, 14))

    # ===== Findings — 점수 분포 바로 아래 이어서 =====
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
    story.append(Spacer(1, 14))

    # ===== 액션 플랜 — Findings 바로 아래 이어서 =====
    story.append(Paragraph("액션 플랜", h2))

    def _action_block(title: str, sub: str, items: list[str], color):
        story.append(Spacer(1, 4))
        title_style = ParagraphStyle(
            f"act_{title}", parent=h2, fontSize=12, textColor=color, spaceAfter=1, spaceBefore=4,
        )
        story.append(Paragraph(f"{title} · {sub}", title_style))
        for idx, item in enumerate(items, start=1):
            story.append(Paragraph(f"{idx}. {item}", body))

    _action_block("Quick Wins", "1주 안에 실행", report.quick_wins, SUCCESS)
    _action_block("Medium-Term", "1~3개월 실행", report.medium_term, ACCENT)
    _action_block("Strategic", "3~6개월 전략", report.strategic, HIGHLIGHT)

    # ===== 집중분석 섹션 (deep_report 있을 때만) =====
    if report.deep_report and isinstance(report.deep_report, dict):
        dr = report.deep_report

        def _dget(obj, key, default=None):
            """obj가 dict가 아닐 때도 안전하게 key 접근."""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default

        story.append(Spacer(1, 16))
        story.append(Paragraph("집중 진단", h1))
        story.append(Paragraph(
            "AI가 서울시 빅데이터·상권·경쟁사 데이터를 종합해 우리 가게에 맞춘 깊이 있는 진단입니다.",
            meta,
        ))
        story.append(Spacer(1, 8))

        # 표지에 이미 AI 종합 진단을 넣었으면 여기서는 risk/recommendation만
        es = _dget(dr, "executive_summary")
        if isinstance(es, dict):
            es_risk = _safe(es.get("risk"))
            es_reco = _safe(es.get("recommendation"))
        else:
            es_risk = ""
            es_reco = ""
        if es_reco:
            reco_style = ParagraphStyle(
                "reco_style", parent=body, fontSize=11, leading=16,
                textColor=ACCENT, spaceAfter=10,
            )
            story.append(Paragraph(f"<b>→ 추천 한 수</b> · {es_reco}", reco_style))

        # 가장 시급한 위험 — 손실 프레이밍 hero
        risk_alert = _safe(_dget(dr, "risk_alert")) or es_risk
        if risk_alert:
            story.append(Paragraph("지금 가장 시급한 신호", h2))
            risk_para_style = ParagraphStyle(
                "risk_para", parent=body, textColor=DANGER, fontSize=12, leading=18,
                spaceAfter=12,
            )
            story.append(Paragraph(risk_alert, risk_para_style))

        # 우리 가게 자리 분석
        loc = _safe(_dget(dr, "location_analysis"))
        if loc:
            story.append(Paragraph("우리 가게 자리 분석", h2))
            story.append(Paragraph(loc, body))

        # 강점·약점·기회·위협 (SWOT)
        swot = _dget(dr, "swot") or {}
        if isinstance(swot, dict) and swot:
            story.append(Paragraph("강점·약점 한눈에", h2))
            swot_rows = [["항목", "내용"]]
            for label, key in [("강점", "strengths"), ("약점", "weaknesses"),
                                ("기회", "opportunities"), ("위협", "threats")]:
                items = swot.get(key) or []
                if isinstance(items, list) and items:
                    text = "\n".join(f"· {_safe(i)}" for i in items[:5])
                    swot_rows.append([label, text])
            if len(swot_rows) > 1:
                swot_tbl = Table(swot_rows, colWidths=[24 * mm, 134 * mm])
                swot_tbl.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(swot_tbl)

        # TOWS 전략
        tows = _dget(dr, "tows_matrix") or {}
        tows_keys = [
            ("강점으로 기회 잡기 (SO)", "so_strategy"),
            ("강점으로 위협 막기 (ST)", "st_strategy"),
            ("기회로 약점 보완 (WO)", "wo_strategy"),
            ("약점·위협 함께 줄이기 (WT)", "wt_strategy"),
        ]
        if isinstance(tows, dict) and any(_dget(tows, k) for _, k in tows_keys):
            story.append(Paragraph("전략 도출", h2))
            for label, key in tows_keys:
                v = _safe(_dget(tows, key))
                if v:
                    story.append(Paragraph(f"<b>{label}</b> · {v}", body))

        # 데이터 요약 추출 (차트용)
        data_summary = _dget(dr, "data_summary") if _dget(dr, "data_summary") is not None else _dget(report.deep_report, "data_summary")
        if not isinstance(data_summary, dict):
            data_summary = {}
        sales_detail = _dget(data_summary, "sales") or {}
        if not isinstance(sales_detail, dict):
            sales_detail = {}

        # 핵심 고객층 + 성별/연령 차트
        ci = _safe(_dget(dr, "customer_insight"))
        if ci:
            customer_block = [Paragraph("우리 가게 단골은 어떤 분일까요?", h2),
                              Paragraph(ci, body)]
            # 성별 도넛 + 연령 막대 차트 (가능한 경우)
            gender = _dget(sales_detail, "gender") or {}
            age = _dget(sales_detail, "age_group") or {}
            charts_row = []
            if isinstance(gender, dict) and (gender.get("남성_비중") or gender.get("여성_비중")):
                m_pct = gender.get("남성_비중") or 0
                f_pct = gender.get("여성_비중") or 0
                if m_pct + f_pct > 0:
                    # 정규화
                    total = m_pct + f_pct
                    m_norm = round(m_pct / total * 100, 1)
                    f_norm = round(100 - m_norm, 1)
                    charts_row.append(_donut_chart([("남성", m_norm), ("여성", f_norm)]))
            if isinstance(age, dict) and age:
                age_items = sorted(
                    [(k, v) for k, v in age.items() if isinstance(v, (int, float))],
                    key=lambda x: ["10대", "20대", "30대", "40대", "50대", "60대+", "60대이상"].index(x[0]) if x[0] in ["10대", "20대", "30대", "40대", "50대", "60대+", "60대이상"] else 99,
                )[:6]
                if age_items:
                    charts_row.append(_bar_chart(age_items, width=170, height=80))
            if charts_row:
                customer_block.append(Spacer(1, 4))
                if len(charts_row) == 2:
                    customer_block.append(Table([[charts_row[0], charts_row[1]]], colWidths=[80 * mm, 90 * mm]))
                else:
                    customer_block.append(charts_row[0])
            story.append(KeepTogether(customer_block))

        # 시간 전략 + 시간대별 매출 막대
        ts = _safe(_dget(dr, "time_strategy"))
        if ts:
            time_block = [Paragraph("언제 손님이 가장 많을까요?", h2),
                          Paragraph(ts, body)]
            # 데이터 출처 라벨 (사장님 가게 ≠ 상권 평균임을 명시)
            scope_label = _dget(sales_detail, "scope_note") or _dget(sales_detail, "note") or ""
            if scope_label:
                time_block.append(Paragraph(f"※ 차트 출처: {scope_label} (사장님 가게 매출 아님)", meta))
            tz = _dget(sales_detail, "time_zone") or {}
            if isinstance(tz, dict) and tz:
                order = ["00~06", "06~11", "11~14", "14~17", "17~21", "21~24"]
                tz_items = [(k, tz.get(k, 0)) for k in order if k in tz]
                if not tz_items:
                    tz_items = [(k, v) for k, v in tz.items() if isinstance(v, (int, float))][:6]
                if tz_items:
                    time_block.append(Spacer(1, 4))
                    time_block.append(_bar_chart(tz_items, width=170, height=70, bar_color=ACCENT))
            # 요일별 매출
            wd = _dget(sales_detail, "weekday") or _dget(sales_detail, "day_of_week") or {}
            if isinstance(wd, dict) and wd:
                order = ["월", "화", "수", "목", "금", "토", "일"]
                wd_items = [(k, wd.get(k, 0)) for k in order if k in wd]
                if not wd_items:
                    wd_items = [(k, v) for k, v in wd.items() if isinstance(v, (int, float))][:7]
                if wd_items:
                    time_block.append(Spacer(1, 4))
                    time_block.append(_bar_chart(wd_items, width=170, height=70, bar_color=HIGHLIGHT))
            story.append(KeepTogether(time_block))

        # 경쟁 분석
        ca = _safe(_dget(dr, "competition_analysis"))
        if ca:
            story.append(KeepTogether([
                Paragraph("옆 가게와 비교하면", h2),
                Paragraph(ca, body),
            ]))

        # 업종 트렌드
        ta = _safe(_dget(dr, "trend_analysis"))
        if ta:
            story.append(KeepTogether([
                Paragraph("업종 흐름은 어떻게 가고 있을까요?", h2),
                Paragraph(ta, body),
            ]))

        # 액션 우선순위 (impact-effort) — Paragraph로 wrapping 보장
        actions = _dget(dr, "action_items") or []
        if isinstance(actions, list) and actions:
            story.append(Paragraph("AI 추천 액션 우선순위", h2))
            act_rows = [[
                Paragraph("<b>우선순위</b>", body),
                Paragraph("<b>액션</b>", body),
                Paragraph("<b>기대 효과</b>", body),
                Paragraph("<b>기간</b>", body),
            ]]
            for a in actions[:8]:
                if not isinstance(a, dict):
                    continue
                priority = _safe(a.get("priority", "")).upper()
                act_rows.append([
                    Paragraph(priority, body),
                    Paragraph(_safe(a.get("action", "")), body),
                    Paragraph(_safe(a.get("expected_impact", "")), body),
                    Paragraph(_safe(a.get("timeline", "")), body),
                ])
            if len(act_rows) > 1:
                # colWidths 재배분 — 액션 60mm, 효과 60mm 충분히
                act_tbl = Table(
                    act_rows,
                    colWidths=[18 * mm, 60 * mm, 60 * mm, 36 * mm],
                    repeatRows=1,
                )
                act_tbl.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(act_tbl)

        # 이번 달 KPI 목표 — monthly_goal이 string으로 올 수도 있음
        goal_raw = _dget(dr, "monthly_goal")
        goal = goal_raw if isinstance(goal_raw, dict) else {}
        # GPT가 string으로 던졌으면 summary로 취급
        goal_summary = _dget(goal, "summary") or (goal_raw if isinstance(goal_raw, str) else "")
        kpis = _dget(goal, "kpis") or []
        if not isinstance(kpis, list):
            kpis = []
        if goal_summary or kpis:
            story.append(Paragraph("이번 달 목표", h2))
            if goal_summary:
                story.append(Paragraph(_safe(goal_summary), body))
            if kpis:
                from app.utils.korean_number import korean_won as _kwon, korean_count as _kcount
                kpi_rows = [["지표", "현재", "목표", "이유"]]
                for k in kpis[:5]:
                    if not isinstance(k, dict):
                        continue
                    unit = str(k.get("unit", "")).strip()
                    cur_v = k.get("current_value")
                    tgt_v = k.get("target_value")
                    # 단위에 따라 한국식 수치 변환
                    def _fmt(v):
                        if v is None or v == "":
                            return "—"
                        try:
                            n = float(v)
                        except (TypeError, ValueError):
                            return str(v)
                        if unit == "원":
                            return _kwon(n)
                        if unit in ("명", "건", "개"):
                            return _kcount(n, unit=unit)
                        if unit == "%":
                            return f"{round(n, 1)}%"
                        return f"{int(n):,}{unit}" if unit else f"{int(n):,}"
                    kpi_rows.append([
                        Paragraph(_safe(k.get("name", "")), body),
                        Paragraph(_fmt(cur_v), body),
                        Paragraph(_fmt(tgt_v), body),
                        Paragraph(_safe(k.get("rationale", ""))[:80], body),
                    ])
            if kpis and len(kpi_rows) > 1:
                kpi_tbl = Table(kpi_rows, colWidths=[28 * mm, 32 * mm, 32 * mm, 66 * mm])
                kpi_tbl.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, 0), font),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (2, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(kpi_tbl)

    # 마지막: 각주
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "이 리포트는 서울시 빅데이터와 사장님 활동 데이터를 합쳐 자동으로 만든 자료예요. "
        "수치는 발행 시점 기준이고, 마지막 결정은 사장님 몫이에요.",
        meta,
    ))

    doc.build(story)
    return buf.getvalue()


def _safe(val: object) -> str:
    """집중분석 필드 값(문자열 또는 dict)을 PDF용 안전한 문자열로 변환."""
    if val is None:
        return ""
    if isinstance(val, dict):
        # 다양한 dict 형태(executive_summary 등)에서 핵심 텍스트 추출
        for k in ("text", "value", "summary", "current"):
            if k in val and isinstance(val[k], str):
                return _strip_evidence_tags(val[k])
        text = " · ".join(f"{k}: {v}" for k, v in val.items() if isinstance(v, (str, int, float)))[:300]
        return _strip_evidence_tags(text)
    if isinstance(val, list):
        return _strip_evidence_tags(" / ".join(str(x) for x in val[:5]))
    return _strip_evidence_tags(str(val))


def _strip_evidence_tags(text: str) -> str:
    """AI 텍스트에서 [근거: ...] 같은 내부 태그 제거.

    GPT가 user-facing 텍스트에 가끔 흘리는 `[근거: 데이터X]` 형태를 후처리로 정리.
    """
    if not text:
        return ""
    import re
    # [근거: ...] 또는 [근거:...] 또는 (근거: ...) 패턴 제거
    cleaned = re.sub(r"\s*[\[\(]\s*근거\s*[:：][^\]\)]*[\]\)]\s*", " ", text)
    # 잔여 공백 정리
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # 끝에 남은 콤마/마침표 정리
    cleaned = re.sub(r"[,，]\s*([.!?])", r"\1", cleaned)
    return cleaned


def _bar_chart(
    title_data: list[tuple[str, float]],
    width: float = 170,
    height: float = 70,
    bar_color=None,
    max_value: float | None = None,
) -> Drawing:
    """가벼운 막대 차트. ReportLab graphics 기반.

    title_data: [(라벨, 값), ...]
    """
    if bar_color is None:
        bar_color = ACCENT
    d = Drawing(width, height)
    if not title_data:
        return d
    labels = [t[0] for t in title_data]
    values = [t[1] for t in title_data]
    if max_value is None:
        max_value = max(values) if values else 1.0
        max_value = max_value * 1.1 if max_value > 0 else 1.0

    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 18
    chart.width = width - 40
    chart.height = height - 30
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = _KOREAN_FONT or "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value
    chart.valueAxis.labels.fontName = _KOREAN_FONT or "Helvetica"
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = bar_color
    chart.bars[0].strokeColor = None
    chart.barWidth = (width - 50) / max(len(values) * 2, 1)
    d.add(chart)
    return d


def _horizontal_bar_chart(
    title_data: list[tuple[str, float]],
    width: float = 170,
    height: float = 90,
    bar_color=None,
) -> Drawing:
    """가로 막대 차트 (라벨이 길 때 적합)."""
    if bar_color is None:
        bar_color = ACCENT
    d = Drawing(width, height)
    if not title_data:
        return d
    labels = [t[0] for t in title_data]
    values = [t[1] for t in title_data]
    max_v = max(values) * 1.1 if values and max(values) > 0 else 1.0

    chart = HorizontalBarChart()
    chart.x = 60
    chart.y = 10
    chart.width = width - 70
    chart.height = height - 20
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = _KOREAN_FONT or "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_v
    chart.valueAxis.labels.fontName = _KOREAN_FONT or "Helvetica"
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = bar_color
    chart.bars[0].strokeColor = None
    d.add(chart)
    return d


def _donut_chart(
    title_data: list[tuple[str, float]],
    width: float = 130,
    height: float = 90,
    color_palette: list | None = None,
) -> Drawing:
    """도넛(파이) 차트. 성별/연령 비중용."""
    if color_palette is None:
        color_palette = [ACCENT, HIGHLIGHT, SUCCESS, WARNING, SECONDARY, BODY]
    d = Drawing(width, height)
    if not title_data:
        return d

    pie = Pie()
    pie.x = 10
    pie.y = 5
    pie.width = 70
    pie.height = 70
    pie.data = [t[1] for t in title_data]
    pie.labels = [f"{t[0]} {round(t[1])}%" for t in title_data]
    pie.slices.strokeWidth = 0.5
    pie.slices.strokeColor = colors.white
    pie.simpleLabels = 1
    pie.sideLabels = 1
    for i, c in enumerate(color_palette[:len(title_data)]):
        pie.slices[i].fillColor = c
        pie.slices[i].fontName = _KOREAN_FONT or "Helvetica"
        pie.slices[i].fontSize = 8
    d.add(pie)
    return d
