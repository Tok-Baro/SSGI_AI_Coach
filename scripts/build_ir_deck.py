"""SSGI AI 경영코치 — IR 덱 빌더 (2026 서울시 빅데이터 활용 경진대회 창업부문 제출용).

룰:
- 개인정보 기재 금지 (공고 명시) → 팀 SSGI만, 4인 실명 ❌
- 평가 6항목 (공공25·AI20·독창15·완성15·발전20·ESG5) chip 명시
- 한자 0건, 50자 이내 헤드라인, 사장님 화법
- LTV/CAC 등 환각 데이터는 "가설" 라벨, AI 추정은 amber chip
- 출처는 슬라이드 푸터에 작은 글씨로

실행: python scripts/build_ir_deck.py
산출: SSGI_AI경영코치_상세기획서.pptx
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ============================================================
# 디자인 토큰 — Toss Style (검정 + 토스 블루 1개)
# ============================================================
# 토스 실제 팔레트
TOSS_TEXT   = RGBColor(0x19, 0x1F, 0x28)  # 검정 본문
TOSS_SUB    = RGBColor(0x4E, 0x59, 0x68)  # 짙은 회색
TOSS_LIGHT  = RGBColor(0x8B, 0x95, 0xA1)  # 옅은 회색
TOSS_BLUE   = RGBColor(0x31, 0x82, 0xF6)  # ★ 메인 강조 1개
TOSS_CARD   = RGBColor(0xF2, 0xF4, 0xF6)  # 카드 배경
TOSS_BORDER = RGBColor(0xEA, 0xED, 0xF0)  # 보더
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
BLACK       = RGBColor(0x00, 0x00, 0x00)
# 의미 매핑 — 위험·성공·추정만 (사용 최소)
TOSS_RED    = RGBColor(0xF0, 0x44, 0x52)
TOSS_GREEN  = RGBColor(0x00, 0xC7, 0x3C)
TOSS_AMBER  = RGBColor(0xF0, 0x9F, 0x12)
TOSS_AMBER_BG = RGBColor(0xFE, 0xF7, 0xE6)

# 호환 별칭 (기존 코드 보존)
NAVY = TOSS_TEXT
SLATE = TOSS_SUB
GREY = TOSS_LIGHT
LIGHT = TOSS_CARD
LIGHTER = TOSS_CARD
LINE = TOSS_BORDER
RED = TOSS_RED
GREEN = TOSS_GREEN
AMBER = TOSS_AMBER
AMBER_BG = TOSS_AMBER_BG

FONT_KR = "AppleGothic"  # macOS 기본 한글 (Pretendard 없으면 폴백)
FONT_EN = "Helvetica"

# 16:9 와이드
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# 평가 6항목 매핑 chip
RUBRIC = {
    "공공": ("공공데이터 25", RGBColor(0x1E, 0x40, 0xAF)),
    "AI": ("AI 혁신 20", RGBColor(0x7C, 0x3A, 0xED)),
    "독창": ("독창성 15", RGBColor(0xBE, 0x18, 0x5D)),
    "완성": ("완성도 15", RGBColor(0x05, 0x96, 0x69)),
    "발전": ("발전 가능성 20", RGBColor(0xC2, 0x41, 0x0C)),
    "ESG": ("ESG 5", RGBColor(0x0F, 0x76, 0x6E)),
}

# ============================================================
# 헬퍼
# ============================================================


def add_text(
    slide,
    left,
    top,
    width,
    height,
    text,
    *,
    size=14,
    bold=False,
    color=SLATE,
    font=FONT_KR,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing=1.2,
):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_rect(slide, left, top, width, height, *, fill=WHITE, line=None, line_w=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    return sh


def add_chip(slide, left, top, label, color, *, fill=None, size=10):
    """둥근 모서리 chip — 평가 항목·태그용."""
    if fill is None:
        fill = LIGHT
    chip_w = Inches(0.05 + 0.085 * len(label))
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, chip_w, Inches(0.28))
    sh.adjustments[0] = 0.5
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    tf = sh.text_frame
    tf.margin_left = Emu(50000)
    tf.margin_right = Emu(50000)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = FONT_KR
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = color
    return sh, chip_w


def add_line(slide, left, top, width, *, color=LINE, weight=0.75):
    line = slide.shapes.add_connector(1, left, top, left + width, top)
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line


def add_header(slide, page_no, total_pages, chapter_no, chapter_title, rubric_keys=()):
    """슬라이드 상단: 챕터 번호 + 평가 매칭 칩 + 페이지."""
    # 좌상단 — 챕터 라벨
    add_text(
        slide,
        Inches(0.5),
        Inches(0.32),
        Inches(6),
        Inches(0.3),
        f"{chapter_no:02d}  ·  {chapter_title}",
        size=11,
        color=GREY,
        bold=True,
    )
    # 우상단 — 평가 매칭 칩들
    chip_x = SLIDE_W - Inches(0.5)
    for key in reversed(rubric_keys):
        label, color = RUBRIC[key]
        # 미리 폭 계산
        chip_w = Inches(0.05 + 0.085 * len(label))
        chip_x -= chip_w + Inches(0.08)
        sh = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            chip_x,
            Inches(0.32),
            chip_w,
            Inches(0.28),
        )
        sh.adjustments[0] = 0.5
        sh.fill.solid()
        sh.fill.fore_color.rgb = TOSS_CARD
        sh.line.color.rgb = TOSS_BORDER
        sh.line.width = Pt(0.5)
        tf = sh.text_frame
        tf.margin_left = Emu(50000)
        tf.margin_right = Emu(50000)
        tf.margin_top = Emu(0)
        tf.margin_bottom = Emu(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = label
        r.font.name = FONT_KR
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = TOSS_SUB
    # 페이지
    add_text(
        slide,
        SLIDE_W - Inches(1.0),
        Inches(0.32),
        Inches(0.5),
        Inches(0.3),
        "",
        size=10,
        color=GREY,
    )
    # 헤더 하단 라인
    add_line(slide, Inches(0.5), Inches(0.75), SLIDE_W - Inches(1.0), color=LINE)


def add_footer(slide, page_no, total_pages, source=""):
    add_line(slide, Inches(0.5), SLIDE_H - Inches(0.55), SLIDE_W - Inches(1.0), color=LINE)
    add_text(
        slide,
        Inches(0.5),
        SLIDE_H - Inches(0.45),
        Inches(8),
        Inches(0.3),
        source,
        size=8,
        color=GREY,
    )
    add_text(
        slide,
        SLIDE_W - Inches(2.5),
        SLIDE_H - Inches(0.45),
        Inches(2.0),
        Inches(0.3),
        f"팀 SSGI · 2026 서울시 빅데이터 활용 경진대회 · 창업부문    {page_no:02d} / {total_pages:02d}",
        size=8,
        color=GREY,
        align=PP_ALIGN.RIGHT,
    )


def add_big_number(slide, left, top, number, unit, label, *, color=NAVY, num_size=44, width=3.0):
    """IR 덱 시그니처 — 큰 숫자 + 단위 + 캡션. 4컬럼 그리드(3.2 간격) 안 넘게 width=3.0."""
    add_text(
        slide,
        left,
        top,
        Inches(width),
        Inches(0.9),
        number,
        size=num_size,
        bold=True,
        color=color,
        font=FONT_EN,
        line_spacing=1.0,
    )
    if unit:
        add_text(
            slide,
            left,
            top + Inches(0.95),
            Inches(width),
            Inches(0.6),
            unit,
            size=10,
            color=GREY,
            line_spacing=1.3,
        )
    add_text(
        slide,
        left,
        top + Inches(1.45),
        Inches(width),
        Inches(0.7),
        label,
        size=10,
        color=SLATE,
        line_spacing=1.35,
    )


def add_card(slide, left, top, width, height, title, body, *, accent=NAVY, body_size=10):
    """본문 카드 — 평가 매칭/기능/데이터 설명용."""
    add_rect(slide, left, top, width, height, fill=LIGHTER, line=LINE)
    # 좌측 컬러 스트라이프
    stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.06), height)
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = accent
    stripe.line.fill.background()
    add_text(
        slide,
        left + Inches(0.2),
        top + Inches(0.15),
        width - Inches(0.3),
        Inches(0.35),
        title,
        size=12,
        bold=True,
        color=NAVY,
    )
    add_text(
        slide,
        left + Inches(0.2),
        top + Inches(0.55),
        width - Inches(0.3),
        height - Inches(0.7),
        body,
        size=body_size,
        color=SLATE,
        line_spacing=1.35,
    )


def add_ai_chip(slide, left, top):
    """amber AI 추정 chip — GPT-4o 산출 표기 의무."""
    sh = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(0.85), Inches(0.22)
    )
    sh.adjustments[0] = 0.5
    sh.fill.solid()
    sh.fill.fore_color.rgb = AMBER_BG
    sh.line.color.rgb = AMBER
    sh.line.width = Pt(0.5)
    tf = sh.text_frame
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "AI 추정"
    r.font.name = FONT_KR
    r.font.size = Pt(8)
    r.font.bold = True
    r.font.color.rgb = AMBER


# ============================================================
# 슬라이드 빌더
# ============================================================


def make_pres():
    p = Presentation()
    p.slide_width = SLIDE_W
    p.slide_height = SLIDE_H
    return p


def blank_slide(p):
    return p.slides.add_slide(p.slide_layouts[6])  # blank


TOTAL = 21


def build():
    p = make_pres()

    # ============ Slide 01 — Cover (Toss Style) ============
    s = blank_slide(p)
    # 흰 배경, 좌측 스트라이프 X (토스는 깔끔)
    # 작은 카테고리 라벨
    add_text(
        s, Inches(0.9), Inches(0.8), Inches(11), Inches(0.3),
        "2026 서울시 빅데이터 활용 경진대회 · 창업부문",
        size=11, color=TOSS_LIGHT, bold=True,
    )
    # 거대 회사명 (Hero)
    add_text(
        s, Inches(0.9), Inches(1.6), Inches(11.5), Inches(1.2),
        "SSGI · AI 경영코치",
        size=64, bold=True, color=TOSS_TEXT, line_spacing=1.0,
    )
    # 슬로건 (큰 SUB)
    add_text(
        s, Inches(0.9), Inches(2.85), Inches(11.5), Inches(1.4),
        "사장님이 모르고 놓치는 돈,\n매일 1줄로 알려드려요.",
        size=32, color=TOSS_SUB, line_spacing=1.4,
    )
    # 거대 임팩트 숫자 (토스 블루 1개만 강조) — 폭·높이 충분히
    add_text(
        s, Inches(0.9), Inches(4.7), Inches(5), Inches(1.7),
        "14",
        size=120, bold=True, color=TOSS_BLUE, font=FONT_EN, line_spacing=1.0,
    )
    # 라벨 — 14 아래 충분한 간격 두고
    add_text(
        s, Inches(0.9), Inches(6.55), Inches(8), Inches(0.35),
        "라이브 핵심 기능",
        size=14, color=TOSS_TEXT, bold=True,
    )
    # 우측 보조 메트릭 3개 (14와 같은 baseline)
    metrics = [
        ("8", "서울 공공데이터"),
        ("100×", "응답 속도 (실측)"),
        ("0", "결제·환각 신고"),
    ]
    mx = Inches(7.5); my = Inches(5.4); mw = Inches(1.8)
    for i, (n, l) in enumerate(metrics):
        x = mx + i * mw
        add_text(s, x, my, mw, Inches(0.7), n, size=36, bold=True, color=TOSS_TEXT, font=FONT_EN, line_spacing=1.0)
        add_text(s, x, my + Inches(0.75), mw, Inches(0.35), l, size=10, color=TOSS_LIGHT)
    # 팀명 푸터 (작게)
    add_text(
        s, Inches(0.9), SLIDE_H - Inches(0.5), Inches(11.5), Inches(0.3),
        "팀 SSGI    ·    제출 2026-05-13",
        size=10, color=TOSS_LIGHT,
    )

    # ============ Slide 02 — Index ============
    s = blank_slide(p)
    add_header(s, 2, TOTAL, 0, "목차 — 평가 6항목 매칭")
    add_text(
        s,
        Inches(0.5),
        Inches(1.0),
        Inches(8),
        Inches(0.6),
        "한눈에 보는 19장",
        size=16,
        bold=True,
        color=NAVY,
    )
    # 목차 2 컬럼
    items = [
        (1, "왜 지금 — 사장님이 마주한 정보 비대칭 3가지", ["공공"]),
        (2, "왜 지금이 윈도우 — 5년 전엔 못 만들었어요", ["AI", "발전"]),
        (3, "사장님 한 명의 이야기 — 시뮬 페르소나", ["완성"]),
        (4, "타깃 — 300명 매트릭스 + 신뢰구간 ±5.7%p", ["완성"]),
        (5, "출품작 한 장 — 매일 1줄 카드 + 3-tier 신뢰 계층", ["AI", "독창"]),
        (6, "활용 공공데이터 — 서울 8종 + 결합 가점 +2", ["공공"]),
        (7, "차별점 1 — AI 4 레이어 (거짓말 안 하게)", ["AI", "독창"]),
        (8, "차별점 2 — 폐업 매트릭스 + 6업종 분기", ["독창"]),
        (9, "메인 화면 4종 — Mock UI + 라이브 데모", ["완성"]),
        (10, "UI/UX — 시니어 친화 + 3-클릭 룰", ["완성"]),
        (11, "5분 시연 — 6 STEP 데모 흐름", ["완성"]),
        (12, "시스템 — Phased Pattern 24s→0.25s 실측", ["완성", "AI"]),
        (13, "지금까지 만든 것 — 라이브 14 기능 + 31 라우트", ["완성", "발전"]),
        (14, "시장 — TAM/SAM/SOM bottom-up 2,604억", ["발전"]),
        (15, "비즈니스 모델 — Free→Pro→Enterprise (가설)", ["발전"]),
        (16, "1년 로드맵 — 1,000 MAU 도전 + Pre-A 검토", ["발전"]),
        (17, "경쟁 — 우리만 가진 6가지 + 약점 1가지", ["독창"]),
        (18, "ESG — tCO2eq 정량 + 폐업방지 23~49명", ["ESG"]),
        (19, "클로징 — 한 명이라도 살리면", ["독창"]),
    ]
    for i, (n, title, keys) in enumerate(items):
        col = i // 10
        row = i % 10
        x = Inches(0.5) + col * Inches(6.2)
        y = Inches(1.7) + row * Inches(0.43)
        add_text(s, x, y, Inches(0.4), Inches(0.3), f"{n:02d}", size=11, bold=True, color=NAVY, font=FONT_EN)
        add_text(s, x + Inches(0.45), y, Inches(4.4), Inches(0.3), title, size=10, color=SLATE)
        # 평가 매칭 칩
        chip_x = x + Inches(4.85)
        for key in keys:
            label, color = RUBRIC[key]
            chip_w = Inches(0.05 + 0.075 * len(label))
            sh = s.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, chip_x, y - Inches(0.02), chip_w, Inches(0.24)
            )
            sh.adjustments[0] = 0.5
            sh.fill.solid()
            sh.fill.fore_color.rgb = LIGHT
            sh.line.color.rgb = TOSS_BORDER
            sh.line.width = Pt(0.4)
            tf = sh.text_frame
            tf.margin_left = Emu(40000); tf.margin_right = Emu(40000)
            tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tp = tf.paragraphs[0]
            tp.alignment = PP_ALIGN.CENTER
            r = tp.add_run()
            r.text = label
            r.font.name = FONT_KR
            r.font.size = Pt(8)
            r.font.bold = True
            r.font.color.rgb = TOSS_SUB
            chip_x += chip_w + Inches(0.05)

    add_footer(
        s, 2, TOTAL,
        "1차 서류 100점 (앱 60 + 기획서 40) + 가점 2  /  2차 발표 100점 = 공공25·AI20·독창15·완성15·발전20·ESG5",
    )

    # ============ Slide 03 — Problem ============
    s = blank_slide(p)
    add_header(s, 3, TOTAL, 1, "왜 지금 — 정보 비대칭이 폐업을 부른다", ["공공"])
    add_text(
        s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.6),
        "5년이면 가게 1곳이 사라져요 — 서울 평균",
        size=24, bold=True, color=NAVY,
    )
    add_text(
        s, Inches(0.5), Inches(1.55), Inches(12), Inches(0.4),
        "사장님이 매일 마주하는 비대칭 — 데이터·시점·행동 세 군데가 다 비어 있어요.",
        size=12, color=GREY,
    )
    # 큰 숫자 4개 — 토스 톤: 검정 위주 + 240만원 1개만 토스 블루 강조
    add_big_number(s, Inches(0.5), Inches(2.2), "4.5년", "서울 폐업 가게 평균 영업기간", "VwsmTrdarIxQq · 2025 Q4 · 추출일 2026-04", color=TOSS_TEXT)
    add_big_number(s, Inches(3.7), Inches(2.2), "9.8년", "서울 운영중 가게 평균", "차이 5.3년 = 분기점", color=TOSS_TEXT)
    add_big_number(s, Inches(6.9), Inches(2.2), "53.7%", "서울 상권 정체+축소", "정체 35.X% + 축소 18.X%", color=TOSS_TEXT)
    add_big_number(s, Inches(10.1), Inches(2.2), "240만원", "사장님 1인당 미신청 보조금", "평균 80만 × 4 부처 × 미신청 75% (자체 추정)", color=TOSS_BLUE)
    # 3 비대칭 카드
    add_card(s, Inches(0.5), Inches(4.5), Inches(4.0), Inches(2.0),
             "1. 지원사업이 흩어져 있어요",
             "서울시·자치구·중기부·소진공 4곳 분산.\n매일 점검 불가능 → 평균 240만원/년 미신청.\n사장님은 어디서 받는지조차 몰라요.")
    add_card(s, Inches(4.7), Inches(4.5), Inches(4.0), Inches(2.0),
             "2. 위험을 미리 못 봐요",
             "매출 감소·상권 변화는\n폐업이 가까워졌을 때 알아채요.\n결정 시점에 데이터가 없는 거예요.", accent=TOSS_BLUE)
    add_card(s, Inches(8.9), Inches(4.5), Inches(4.0), Inches(2.0),
             "3. 진단만 있고 행동이 없어요",
             "리포트는 정보만 주고 끝나요.\n'그래서 뭐 어쩌라고'에 답이 없어요.\n매일 1줄 + cta_type이 답이에요.")
    add_footer(
        s, 3, TOTAL,
        "240만원: 평균 보조금 80만 × 4 부처 × 미신청 75% (소상공인진흥공단·중기부 보조금 미수령률 추정)  /  4.5년·9.8년·53.7% 출처: 서울 열린데이터광장 VwsmTrdarIxQq · 2025 Q4",
    )

    # ============ Slide 04 — Why Now (NEW) ============
    s = blank_slide(p)
    add_header(s, 4, TOTAL, 2, "왜 지금이 윈도우인가", ["AI", "발전"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "5년 전엔 못 만들었어요. 지금이 윈도우.",
             size=22, bold=True, color=NAVY)
    add_text(s, Inches(0.5), Inches(1.55), Inches(12), Inches(0.4),
             "정책·기술·예산·사용자 변화가 동시에 — 6~12개월 안 잡으면 다른 팀이 가져갑니다.",
             size=12, color=GREY)
    # 4 unlock 카드
    unlocks = [
        ("GPT-4o 비용 -90%", "2023년 GPT-4 → 2025년 GPT-4o\n동일 추론 비용 90% 인하",
         "→ B2C 9,900원 SaaS 가능", NAVY),
        ("카카오 알림톡 정책 개방", "2025년 카카오 비즈메시지\n중소사업자 채널 인증 완화",
         "→ 사장님 도달률 1순위 채널", NAVY),
        ("정부 디지털 전환 예산", "2026년 소상공인 디지털 전환\n정부 예산 약 1,500억원",
         "→ 보조금 매칭 수요 폭증", TOSS_BLUE),
        ("60대+ 스마트폰 90%+", "한국 65세+ 스마트폰 보급률\n90% 돌파 (KISA 2024)",
         "→ 시니어 사장님이 시장", NAVY),
    ]
    ux = Inches(0.5); uy = Inches(2.2); uw = Inches(3.05); uh = Inches(3.5)
    for i, (name, body, impact, color) in enumerate(unlocks):
        x = ux + i * (uw + Inches(0.1))
        add_rect(s, x, uy, uw, uh, fill=LIGHTER, line=color, line_w=1.5)
        # 컬러 헤더
        head = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, uy, uw, Inches(0.6))
        head.fill.solid(); head.fill.fore_color.rgb = color; head.line.fill.background()
        add_text(s, x + Inches(0.15), uy + Inches(0.15), uw - Inches(0.3), Inches(0.3), name, size=12, bold=True, color=WHITE)
        # 본문
        add_text(s, x + Inches(0.2), uy + Inches(0.85), uw - Inches(0.4), Inches(1.5), body, size=11, color=SLATE, line_spacing=1.4)
        # 임팩트 chip
        add_rect(s, x + Inches(0.2), uy + uh - Inches(0.6), uw - Inches(0.4), Inches(0.4), fill=LIGHT, line=color, line_w=0.5)
        add_text(s, x + Inches(0.2), uy + uh - Inches(0.52), uw - Inches(0.4), Inches(0.3), impact, size=9, bold=True, color=color, align=PP_ALIGN.CENTER)
    add_text(s, Inches(0.5), Inches(6.3), Inches(12), Inches(0.4),
             "→ 2026년에 안 잡으면 — 카카오·네이버 같은 큰 회사가 자영업 채널 가져갑니다",
             size=12, bold=True, color=NAVY)
    add_footer(s, 4, TOTAL,
               "출처: OpenAI 가격표 (2024-12) / 카카오 비즈메시지 정책 (2025) / 중기부 소상공인 예산안 (2026) / KISA 인터넷이용실태 (2024)")

    # ============ Slide 05 — Persona (was 04) ============
    s = blank_slide(p)
    add_header(s, 5, TOTAL, 3, "사장님 한 명의 이야기", ["완성"])
    add_text(
        s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
        "관악 한식 사장님이 7년째 못 보고 있는 신호",
        size=26, bold=True, color=NAVY,
    )
    # 인용 박스
    add_rect(s, Inches(0.5), Inches(1.8), Inches(7.5), Inches(2.6), fill=LIGHTER, line=LINE)
    # 좌측 빨간 따옴표 스트라이프 (인용 강조)
    stripe = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.8), Inches(0.08), Inches(2.6))
    stripe.fill.solid(); stripe.fill.fore_color.rgb = RED; stripe.line.fill.background()
    add_text(
        s, Inches(0.85), Inches(2.0), Inches(7.0), Inches(2.2),
        "관악구에서 7년째 한식집을 운영해요.\n매출이 매달 조금씩 빠지는데,\n어느 정도가 진짜 위험한 건지\n알 방법이 없었어요.",
        size=18, color=NAVY, line_spacing=1.4,
    )
    add_text(
        s, Inches(0.9), Inches(4.0), Inches(7.0), Inches(0.3),
        "— 관악구 한식집 사장님 (시뮬 페르소나, 58세)",
        size=10, color=GREY,
    )
    # AI 추정 칩
    add_ai_chip(s, Inches(7.0), Inches(1.85))
    # 우측 — AI 코치만 알 수 있는 손실 3건
    add_text(
        s, Inches(8.3), Inches(1.85), Inches(4.5), Inches(0.4),
        "AI 코치만 알 수 있는 손실",
        size=14, bold=True, color=NAVY,
    )
    losses = [
        ("폐업 매트릭스 신호 3건", "같은 동네 한식 8곳이 평균 53개월에 폐업.\n사장님은 84개월째 — 위험 신호 누적."),
        ("객단가 갭", "객단가 1.2만 → 평균 1.5만보다 3천원 낮음.\n점심 세트 1.4만으로 끌어올릴 수 있어요."),
        ("오늘의 1줄", "이번 주 단골 카톡 + 재방문 쿠폰 1종.\n5분이면 끝나요."),
    ]
    for i, (t, b) in enumerate(losses):
        add_card(s, Inches(8.3), Inches(2.3) + i * Inches(0.75), Inches(4.5), Inches(0.7), t, b, body_size=9, accent=TOSS_TEXT)
    # 하단 정직 라벨
    add_rect(s, Inches(0.5), Inches(4.7), Inches(7.5), Inches(1.8), fill=TOSS_CARD, line=TOSS_BORDER)
    add_text(s, Inches(0.7), Inches(4.85), Inches(7.0), Inches(0.4),
             "본 사례는 8축 매트릭스로 구성한 시뮬 페르소나입니다",
             size=12, bold=True, color=TOSS_TEXT)
    add_text(
        s, Inches(0.7), Inches(5.25), Inches(7.0), Inches(1.3),
        "8축 매트릭스 (업종·자치구·매출·운영기간·연령·디지털·가게형태·고민)로 구성한 시뮬 페르소나입니다.\n실 사용자 인터뷰는 베타 출시(2026 Q3) 후 진행 예정.",
        size=10, color=SLATE, line_spacing=1.4,
    )
    add_footer(s, 6, TOTAL, "베타 데이터는 같은 분기 동일 업종 10명 이상 모일 때만 노출 (개인정보 보호)")

    # ============ Slide 05 — Target Persona Matrix ============
    s = blank_slide(p)
    add_header(s, 6, TOTAL, 4, "타깃 사장님 — 300명 매트릭스 · 4 클러스터", ["완성"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "사장님 4 종류, 메시지도 4 종류로 — 잘못 던지면 부메랑이 와요",
             size=20, bold=True, color=NAVY)
    # 4 클러스터 카드
    cards = [
        ("디지털 절벽 노포", "한식·도소매 / 50~60대 / 카톡만 / 운영 7년+\n매출 감소 중 · 보조금 미신청", "정중 톤 + 1393 의무 안내", TOSS_TEXT),
        ("1년차 카페", "마포·성동 카페 / 30~40대 / SNS 활용\n신규 · 마케팅 고민", "Quick Win 액션 우선", TOSS_TEXT),
        ("월매출 1,500만 미만", "다양 업종 / 폐업 위험 신호 누적\n보조금 미신청 · 단골 부족", "지원사업 푸시 + 단골 시스템", TOSS_BLUE),
        ("마케팅 실험족", "30~40대 / SNS·데이터 분석\n캠페인 ROI 검증 욕구", "AI 추정 데이터 + export", TOSS_TEXT),
    ]
    for i, (title, desc, tone, color) in enumerate(cards):
        col = i % 2; row = i // 2
        x = Inches(0.5) + col * Inches(6.2)
        y = Inches(1.8) + row * Inches(2.3)
        add_rect(s, x, y, Inches(6.0), Inches(2.1), fill=LIGHTER, line=LINE)
        # 컬러 헤더
        head = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(6.0), Inches(0.45))
        head.fill.solid(); head.fill.fore_color.rgb = color; head.line.fill.background()
        add_text(s, x + Inches(0.2), y + Inches(0.08), Inches(5.6), Inches(0.3), title, size=14, bold=True, color=WHITE)
        add_text(s, x + Inches(0.2), y + Inches(0.6), Inches(5.6), Inches(0.9), desc, size=11, color=SLATE, line_spacing=1.4)
        add_text(s, x + Inches(0.2), y + Inches(1.55), Inches(5.6), Inches(0.4), f"카피 분기 → {tone}", size=10, bold=True, color=color)

    add_text(s, Inches(0.5), Inches(6.5), Inches(12), Inches(0.4),
             "손실 프레이밍 부메랑 방지 — 클러스터별 톤 분기로 시니어·폐업 위험군은 자살예방상담 1393 의무 노출",
             size=10, color=GREY)
    add_footer(s, 7, TOTAL,
               "4 메가 클러스터 · 95% 신뢰구간 ±5.7%p · 실 사용자 인터뷰는 베타 출시 후 진행")

    # ============ Slide 06 — Solution Hero (3-tier) ============
    s = blank_slide(p)
    add_header(s, 7, TOTAL, 5, "출품작 한 장 — 매일 1줄 카드", ["AI", "독창"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "매일 아침 7시. 사장님 카톡 1줄.",
             size=26, bold=True, color=NAVY)
    add_text(s, Inches(0.5), Inches(1.6), Inches(12), Inches(0.4),
             "AI가 거짓말 안 하게 3겹으로 막았어요 — 사장님이 무엇을 보고 있는지 매번 알 수 있어요.",
             size=12, color=GREY)
    # 3-tier 가로 다이어그램
    tiers = [
        ("Tier 1", "결정론 룰", "공식 기반 · GPT 호출 0회",
         "위험도 점수 / 폐업 매트릭스 5신호 / 5-차원 진단",
         "환각 0%", GREEN),
        ("Tier 2", "매칭 + 검색", "GPT 0회 · SQL+ICP 시간가중",
         "보조금 매칭 (active) / ChromaDB 음성 STT 질의",
         "검증 가능", NAVY),
        ("Tier 3", "GPT-4o 자유 생성", "AI 추정 · 노란 표시 자동",
         "오늘의 1줄 액션 / 마케팅 사설 / SWOT 집중분석",
         "노란 '추정' 표시 일관 적용", AMBER),
    ]
    # 좌측 — 카카오톡 mock 풍선 (모든 텍스트 padding 일관 0.25in)
    kx = Inches(0.5); ky = Inches(2.2); kw = Inches(4.0); kh = Inches(3.7)
    # 카카오톡 배경
    bg = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, kx, ky, kw, kh)
    bg.adjustments[0] = 0.04
    bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(0xB2, 0xC7, 0xD9); bg.line.fill.background()
    # 상단 카카오톡 헤더
    hd = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, kx, ky, kw, Inches(0.5))
    hd.fill.solid(); hd.fill.fore_color.rgb = RGBColor(0xA5, 0xBC, 0xCF); hd.line.fill.background()
    add_text(s, kx + Inches(0.25), ky + Inches(0.13), kw - Inches(0.5), Inches(0.25),
             "AI 경영코치 · 오전 7:00", size=10, bold=True, color=TOSS_TEXT)
    # 카톡 풍선 — 좌측 0.4 padding, 폭 3.2 (kw-0.8)
    bub_x = kx + Inches(0.4); bub_y = ky + Inches(0.85)
    bub_w = Inches(3.2); bub_h = Inches(2.6)
    BUB_PAD = Inches(0.25)
    bub = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, bub_x, bub_y, bub_w, bub_h)
    bub.adjustments[0] = 0.10
    bub.fill.solid(); bub.fill.fore_color.rgb = WHITE; bub.line.fill.background()
    inner_bw = bub_w - 2 * BUB_PAD
    # 인사 (작게)
    add_text(s, bub_x + BUB_PAD, bub_y + Inches(0.2), inner_bw, Inches(0.3),
             "안녕하세요 사장님", size=10, color=TOSS_LIGHT)
    # "오늘의 1줄" 타이틀
    add_text(s, bub_x + BUB_PAD, bub_y + Inches(0.5), inner_bw, Inches(0.35),
             "오늘의 1줄", size=12, bold=True, color=TOSS_BLUE)
    # 본문 액션
    add_text(s, bub_x + BUB_PAD, bub_y + Inches(0.95), inner_bw, Inches(0.95),
             "단골 카톡 + 재방문 쿠폰 1종을\n오늘 발행하시는 게 좋아요.",
             size=13, bold=True, color=TOSS_TEXT, line_spacing=1.4)
    # 근거 (작게)
    add_text(s, bub_x + BUB_PAD, bub_y + Inches(1.95), inner_bw, Inches(0.5),
             "근거: 매출 -5.4% (서울 Q3)\n동네 한식 8곳이 같은 시기 실행",
             size=9, color=TOSS_SUB, line_spacing=1.3)
    # 시간 라벨 — 풍선 안 우측 하단
    add_text(s, bub_x + bub_w - Inches(0.7), bub_y + bub_h - Inches(0.3), Inches(0.5), Inches(0.2),
             "07:00", size=8, color=TOSS_LIGHT, align=PP_ALIGN.RIGHT)

    # 우측 — 3-tier 토스식 (카드 폭 확장 2.7 → 2.75, padding 일관 0.3)
    bx = Inches(4.85); by = Inches(2.2); bw = Inches(2.75); bh = Inches(3.7)
    PAD = Inches(0.3)  # 카드 내부 좌우 padding 일관
    tiers_v = [
        ("01", "결정론 룰", "GPT 호출 0회",
         "위험도·폐업 매트릭스·5신호", "환각 0%"),
        ("02", "매칭 + 검색", "SQL + 사용자 학습",
         "보조금 매칭·음성 STT 질의", "검증 가능"),
        ("03", "GPT-4o 생성", "자동 '추정' 표시",
         "오늘의 액션·SWOT·마케팅", "'추정' 표시"),
    ]
    for i, (n, name, sub, body, gtag) in enumerate(tiers_v):
        x = bx + i * (bw + Inches(0.1))
        is_center = (i == 1)
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, by, bw, bh)
        card.adjustments[0] = 0.06
        if is_center:
            card.fill.solid(); card.fill.fore_color.rgb = TOSS_BLUE; card.line.fill.background()
            t_color = WHITE; sub_color = RGBColor(0xCB, 0xE0, 0xFE); body_color = WHITE
        else:
            card.fill.solid(); card.fill.fore_color.rgb = TOSS_CARD; card.line.fill.background()
            t_color = TOSS_TEXT; sub_color = TOSS_LIGHT; body_color = TOSS_SUB
        # 내부 콘텐츠 영역 = 카드 - 좌우 padding
        inner_w = bw - 2 * PAD
        # 번호 (작게)
        add_text(s, x + PAD, by + Inches(0.3), inner_w, Inches(0.25),
                 n, size=11, color=sub_color, font=FONT_EN)
        # 제목 — 폰트 18pt로 살짝 줄여 한 줄 안에
        add_text(s, x + PAD, by + Inches(0.6), inner_w, Inches(0.5),
                 name, size=18, bold=True, color=t_color, line_spacing=1.2)
        # sub
        add_text(s, x + PAD, by + Inches(1.2), inner_w, Inches(0.35),
                 sub, size=11, color=sub_color)
        # 본문
        add_text(s, x + PAD, by + Inches(1.8), inner_w, Inches(1.2),
                 body, size=11, color=body_color, line_spacing=1.4)
        # 보장 (하단) — 카드 끝에서 0.5 위
        add_text(s, x + PAD, by + bh - Inches(0.55), inner_w, Inches(0.3),
                 gtag, size=10, bold=True, color=t_color)

    # 하단 핵심 메시지 (인라인)
    add_text(s, Inches(0.5), Inches(6.3), Inches(12), Inches(0.4),
             "사장님이 모르는 손실을, 데이터가 매일 짚어드려요.",
             size=15, bold=True, color=TOSS_TEXT)
    add_footer(s, 8, TOTAL,
               "위 카톡 화면은 라이브 시연 가능 · 보조금 매칭·음성 검색 모두 작동 중")

    # ============ Slide 07 — 공공데이터 ============
    s = blank_slide(p)
    add_header(s, 8, TOTAL, 6, "활용 공공데이터 — 서울 8종 + 결합 가점 +2", ["공공"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "서울시가 풀어준 8 데이터 + 다른 분야 4건을 매일 합쳐요",
             size=22, bold=True, color=NAVY)
    # 8종 그리드 4x2
    datasets = [
        ("VwsmTrdarSelngQq", "상권 분기별 매출", "QoQ + 객단가 + 시간·요일·연령·성별"),
        ("VwsmTrdarStorQq", "상권 점포 개폐업", "분기 개업률·폐업률·점포 수"),
        ("VwsmTrdarIxQq", "상권 변화 지표", "확장/다이나믹/정체/축소 4단계"),
        ("VwsmTrdarFlpopQq", "상권 유동인구", "시간·요일·성별·연령 (분기 일평균)"),
        ("SPOP_LOCAL_RESD_DONG", "행정동 생활인구", "일별 (T-7 walk)"),
        ("culturalEventInfo", "서울 문화행사", "객단가 캠페인 타이밍"),
        ("VwsmTrdarFcltyQq", "상권 인프라", "관공서·은행·병원·대중교통"),
        ("VwsmTrdarWrcPopltnQq", "상권 직장인구", "점심 매출 잠재력"),
    ]
    gx = Inches(0.5); gy = Inches(1.7); gw = Inches(3.05); gh = Inches(1.0)
    for i, (code, name, desc) in enumerate(datasets):
        col = i % 4; row = i // 4
        x = gx + col * (gw + Inches(0.1))
        y = gy + row * (gh + Inches(0.15))
        add_rect(s, x, y, gw, gh, fill=LIGHTER, line=LINE)
        # 한국명 우선 + 코드 작게 (사장님·심사위원 친화)
        add_text(s, x + Inches(0.15), y + Inches(0.1), gw - Inches(0.3), Inches(0.25), name, size=12, bold=True, color=NAVY)
        add_text(s, x + Inches(0.15), y + Inches(0.35), gw - Inches(0.3), Inches(0.25), code, size=8, color=GREY, font=FONT_EN)
        add_text(s, x + Inches(0.15), y + Inches(0.62), gw - Inches(0.3), Inches(0.4), desc, size=9, color=SLATE, line_spacing=1.3)
    # 결합 가점 영역
    add_rect(s, Inches(0.5), Inches(4.4), Inches(12.3), Inches(2.1), fill=LIGHT, line=LINE)
    add_text(s, Inches(0.7), Inches(4.55), Inches(8), Inches(0.35), "다른 분야 결합 — 가점 +2 (공고 기준)", size=14, bold=True, color=NAVY)
    add_text(s, Inches(0.7), Inches(4.95), Inches(11.9), Inches(0.4),
             "공고 명시: '교통+문화, 인구+환경 등 서로 다른 분야 데이터를 1건 이상 결합'",
             size=10, color=GREY)
    combos = [
        ("국세청", "사업자번호 진위확인 API", "행정"),
        ("카카오 로컬", "상호명·좌표 검색", "민간"),
        ("행안부", "전국 자영업 통계 (730만)", "행정"),
        ("OpenAI", "GPT-4o + Embeddings", "AI"),
        ("기상청", "체감온도 → 메뉴 시즌 캘린더", "환경 (예정)"),
    ]
    cx = Inches(0.7); cy = Inches(5.5); cw = Inches(2.35); ch = Inches(0.85)
    for i, (provider, what, cat) in enumerate(combos):
        x = cx + i * (cw + Inches(0.05))
        add_rect(s, x, cy, cw, ch, fill=WHITE, line=LINE)
        add_text(s, x + Inches(0.15), cy + Inches(0.08), cw - Inches(0.3), Inches(0.25), provider, size=11, bold=True, color=NAVY)
        add_text(s, x + Inches(0.15), cy + Inches(0.32), cw - Inches(0.3), Inches(0.25), what, size=9, color=SLATE)
        add_text(s, x + Inches(0.15), cy + Inches(0.55), cw - Inches(0.3), Inches(0.25), cat, size=8, color=GREY)
    add_footer(s, 9, TOTAL,
               "서울 열린데이터광장 8종 / 정확한 데이터셋 명: 위 코드 그대로 / 추출일 2026-04 기준 / 분기 데이터는 T-1 분기 walk")

    # ============ Slide 08 — AI 혁신 ============
    s = blank_slide(p)
    add_header(s, 9, TOTAL, 7, "차별점 1 — AI 혁신: 4 레이어 아키텍처", ["AI", "독창"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "AI가 거짓말 안 하게, 4겹으로 막았어요",
             size=24, bold=True, color=NAVY)
    layers = [
        ("STT (Web Speech API)", "음성 → 텍스트 → ChromaDB 검색 → GPT-4o 답변",
         "사장님이 키보드 안 써도 질문 가능. 시니어 친화.", "필수 충족: AI 기술"),
        ("GPT-4o 생성형 AI", "오늘의 1줄 액션 / 마케팅 사설 / SWOT / 사업계획서 초안",
         "노란 '추정' 표시 일관 — 사용자가 출처를 매번 알 수 있어요.", "필수 충족: 생성형 AI"),
        ("RAG (text-embedding-3-small + ChromaDB)", "보조금 22건 + 페르소나 가이드 인덱싱",
         "음성 질의 ChromaDB active / 보조금 매칭은 SQL+ICP가 active.", "라이브 운영"),
        ("사용자 학습 매칭 엔진", "사장님이 본·신청한 보조금을 학습 → 다음 추천 순서 조정",
         "처음엔 일반 추천 → 쓸수록 사장님 취향에 맞춰 순서 바뀜.", "독창 구현 (icp_learner.py)"),
    ]
    ly = Inches(1.7)
    for i, (name, what, why, badge) in enumerate(layers):
        y = ly + i * Inches(1.2)
        add_rect(s, Inches(0.5), y, Inches(12.3), Inches(1.05), fill=LIGHTER, line=LINE)
        # 인덱스
        add_text(s, Inches(0.7), y + Inches(0.1), Inches(0.5), Inches(0.4), f"L{i+1}", size=18, bold=True, color=NAVY, font=FONT_EN)
        add_text(s, Inches(1.3), y + Inches(0.1), Inches(5), Inches(0.3), name, size=12, bold=True, color=NAVY)
        add_text(s, Inches(1.3), y + Inches(0.4), Inches(5), Inches(0.3), what, size=10, color=SLATE)
        add_text(s, Inches(1.3), y + Inches(0.7), Inches(5), Inches(0.3), why, size=9, color=GREY)
        # 우측 보장 칩
        add_rect(s, Inches(9.3), y + Inches(0.3), Inches(3.3), Inches(0.45), fill=LIGHT, line=NAVY, line_w=0.5)
        add_text(s, Inches(9.3), y + Inches(0.38), Inches(3.3), Inches(0.3), badge, size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_footer(s, 10, TOTAL,
               "필수 조건 충족: 서울 열린데이터광장 8종 + AI(STT + 생성형) — 공고 창업부문 제품·서비스 트랙 기준")

    # ============ Slide 09 — 독창성 ============
    s = blank_slide(p)
    add_header(s, 10, TOTAL, 8, "차별점 2 — 독창성: 폐업 매트릭스 + 6업종 분기", ["독창"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "다른 도구는 '추천합니다', 우리는 '놓치고 있어요'",
             size=24, bold=True, color=NAVY)
    # 기존 vs SSGI 비교
    add_text(s, Inches(0.5), Inches(1.7), Inches(6), Inches(0.3), "기존 자영업 도구의 한계", size=12, bold=True, color=GREY)
    olds = [
        "'추천합니다' 톤 — 책임 있는 행동 X",
        "사장님이 이미 아는 정보 (매출·재고)",
        "사후적 진단 (폐업 후 보고서)",
        "일반론 카피 — 50대 시니어 거부감",
        "치킨집·카페에 똑같은 조언",
    ]
    for i, t in enumerate(olds):
        add_text(s, Inches(0.5), Inches(2.05) + i * Inches(0.32), Inches(6), Inches(0.3),
                 f"✗  {t}", size=11, color=GREY)
    add_text(s, Inches(6.8), Inches(1.7), Inches(6), Inches(0.3), "SSGI · 우리만의 차별점", size=12, bold=True, color=NAVY)
    news = [
        "폐업 매트릭스 — 모르는 위험을 사전 알림",
        "행동 1줄 + cta_type — 즉시 실행 가능",
        "6업종 분기 — 치킨↔카페↔미용 다른 진단",
        "10명 이상 모일 때만 노출 (개인정보 보호)",
        "모든 카드 출처 라벨 + 노란 '추정' 표시",
    ]
    for i, t in enumerate(news):
        add_text(s, Inches(6.8), Inches(2.05) + i * Inches(0.32), Inches(6), Inches(0.3),
                 f"✓  {t}", size=11, color=NAVY, bold=True)
    # 폐업 매트릭스 세부
    add_rect(s, Inches(0.5), Inches(4.3), Inches(12.3), Inches(2.2), fill=LIGHTER, line=RED)
    add_text(s, Inches(0.7), Inches(4.45), Inches(11), Inches(0.35), "폐업 매트릭스 — 5신호 결정론 룰 (GPT 호출 0회)", size=14, bold=True, color=RED)
    signals = [
        ("매출 -5% QoQ", "VwsmTrdarSelngQq", "-10점"),
        ("폐업률 5%+", "VwsmTrdarStorQq", "-10점"),
        ("정체·축소 상권", "VwsmTrdarIxQq", "-20점"),
        ("유동인구 -3%", "SPOP_LOCAL_RESD_DONG", "-20점"),
        ("폐업 평균 70% 도달", "operating_months / closed_avg", "-20점"),
    ]
    sx = Inches(0.7); sy = Inches(4.95); sw = Inches(2.4); sh = Inches(1.2)
    for i, (name, src, score) in enumerate(signals):
        x = sx + i * (sw + Inches(0.05))
        add_rect(s, x, sy, sw, sh, fill=WHITE, line=LINE)
        add_text(s, x + Inches(0.15), sy + Inches(0.1), sw - Inches(0.3), Inches(0.3), name, size=11, bold=True, color=NAVY)
        add_text(s, x + Inches(0.15), sy + Inches(0.4), sw - Inches(0.3), Inches(0.3), src, size=8, color=GREY, font=FONT_EN)
        add_text(s, x + Inches(0.15), sy + Inches(0.75), sw - Inches(0.3), Inches(0.3), score, size=14, bold=True, color=RED)
    add_text(s, Inches(0.5), Inches(6.7), Inches(12), Inches(0.3),
             "→ 100점 차감식 + 4단계 등급 (안전·관찰·경고·위험) + 1-액션 매핑 · 6업종별 다른 처방",
             size=10, color=GREY)
    add_footer(s, 11, TOTAL, "원칙 6개 시스템 강제 (변경 금지) — 손실 프레이밍·개인정보 보호·하루 1액션 등")

    # ============ Slide 10 — 메인 화면 (Mock phone frames) ============
    s = blank_slide(p)
    add_header(s, 11, TOTAL, 9, "완성도 1 — 메인/세부 화면 4종 구동", ["완성"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "사장님이 매일 보는 화면 4개 — 라이브 데모 가능",
             size=22, bold=True, color=NAVY)

    # 4 mock phone frames (smartphone 비율 9:19.5)
    px = Inches(0.6); py = Inches(1.7); pw = Inches(2.85); ph = Inches(4.5)
    gap = Inches(0.18)

    # === Phone 1: Dashboard ===
    x = px
    # 핸드폰 외곽 (둥근 모서리)
    phone = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, py, pw, ph)
    phone.adjustments[0] = 0.06
    phone.fill.solid(); phone.fill.fore_color.rgb = RGBColor(0x1F, 0x29, 0x37); phone.line.fill.background()
    # 화면 (안쪽 흰색)
    sx_in = x + Inches(0.1); sy_in = py + Inches(0.15)
    sw_in = pw - Inches(0.2); sh_in = ph - Inches(0.3)
    screen = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in, sy_in, sw_in, sh_in)
    screen.adjustments[0] = 0.04
    screen.fill.solid(); screen.fill.fore_color.rgb = WHITE; screen.line.fill.background()
    # 상단 status bar (NAVY)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx_in, sy_in, sw_in, Inches(0.4))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(0.1), sw_in - Inches(0.3), Inches(0.25),
             "안녕하세요, 사장님", size=10, bold=True, color=WHITE)
    # 위험도 카드 (토스 톤: 옅은 회색 + 토스 블루 강조)
    add_rect(s, sx_in + Inches(0.15), sy_in + Inches(0.55), sw_in - Inches(0.3), Inches(0.85), fill=TOSS_CARD, line=None)
    add_text(s, sx_in + Inches(0.25), sy_in + Inches(0.6), sw_in - Inches(0.5), Inches(0.25), "경영 위험도 · 관찰", size=8, color=TOSS_LIGHT, bold=True)
    add_text(s, sx_in + Inches(0.25), sy_in + Inches(0.85), sw_in - Inches(0.5), Inches(0.5), "67 / 100", size=22, bold=True, color=TOSS_TEXT, font=FONT_EN)
    # 지원금 카드 (토스 블루 1개만 강조)
    add_rect(s, sx_in + Inches(0.15), sy_in + Inches(1.5), sw_in - Inches(0.3), Inches(0.85), fill=TOSS_CARD, line=None)
    add_text(s, sx_in + Inches(0.25), sy_in + Inches(1.55), sw_in - Inches(0.5), Inches(0.25), "신청 가능 지원금", size=8, color=TOSS_LIGHT, bold=True)
    add_text(s, sx_in + Inches(0.25), sy_in + Inches(1.8), sw_in - Inches(0.5), Inches(0.5), "247만원", size=22, bold=True, color=TOSS_BLUE, font=FONT_EN)
    # 오늘의 1줄
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(2.5), sw_in - Inches(0.3), Inches(0.25), "오늘의 1줄", size=8, color=GREY, bold=True)
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(2.75), sw_in - Inches(0.3), Inches(0.6), "단골 카톡 + 재방문 쿠폰 1종 즉시 발행", size=10, color=NAVY, bold=True, line_spacing=1.3)
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(3.5), sw_in - Inches(0.3), Inches(0.4), "출처: 서울 VwsmTrdarSelngQq · Q4", size=7, color=GREY)
    # 라벨
    add_text(s, x, py + ph + Inches(0.1), pw, Inches(0.3), "대시보드 (홈)", size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # === Phone 2: Insights ===
    x = px + (pw + gap)
    phone = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, py, pw, ph)
    phone.adjustments[0] = 0.06
    phone.fill.solid(); phone.fill.fore_color.rgb = RGBColor(0x1F, 0x29, 0x37); phone.line.fill.background()
    sx_in = x + Inches(0.1); sy_in = py + Inches(0.15)
    screen = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in, sy_in, sw_in, sh_in)
    screen.adjustments[0] = 0.04
    screen.fill.solid(); screen.fill.fore_color.rgb = WHITE; screen.line.fill.background()
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx_in, sy_in, sw_in, Inches(0.4))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(0.1), sw_in - Inches(0.3), Inches(0.25), "인사이트", size=10, bold=True, color=WHITE)
    # 4 탭 미니
    tabs = ["경쟁 분석", "집중 분석", "마케팅", "메뉴"]
    for ti, tn in enumerate(tabs):
        tw = (sw_in - Inches(0.3)) / 4
        tab_x = sx_in + Inches(0.15) + ti * tw
        bg = NAVY if ti == 1 else LIGHT
        fg = WHITE if ti == 1 else GREY
        add_rect(s, tab_x, sy_in + Inches(0.55), tw, Inches(0.3), fill=bg, line=None)
        add_text(s, tab_x, sy_in + Inches(0.6), tw, Inches(0.2), tn, size=8, bold=True, color=fg, align=PP_ALIGN.CENTER)
    # SWOT 4 칸
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(1.0), sw_in - Inches(0.3), Inches(0.3), "관악 한식 SWOT", size=9, bold=True, color=NAVY)
    add_ai_chip(s, sx_in + sw_in - Inches(1.0), sy_in + Inches(1.0))
    swot = [("S", "직주 비율 1.8", GREEN), ("W", "객단가 -3천", RED), ("O", "보조금 5건", GREEN), ("T", "경쟁 +2", AMBER)]
    for si, (l, t, c) in enumerate(swot):
        col = si % 2; row = si // 2
        cx = sx_in + Inches(0.15) + col * ((sw_in - Inches(0.3)) / 2 + Inches(0.05))
        cy = sy_in + Inches(1.4) + row * Inches(0.7)
        cw = (sw_in - Inches(0.4)) / 2; ch = Inches(0.6)
        add_rect(s, cx, cy, cw, ch, fill=LIGHTER, line=c, line_w=0.5)
        add_text(s, cx + Inches(0.1), cy + Inches(0.05), Inches(0.3), Inches(0.25), l, size=11, bold=True, color=c, font=FONT_EN)
        add_text(s, cx + Inches(0.1), cy + Inches(0.3), cw - Inches(0.2), Inches(0.3), t, size=8, color=SLATE)
    # 출처
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(3.5), sw_in - Inches(0.3), Inches(0.4), "GPT-4o + RAG", size=7, color=GREY, font=FONT_EN)
    add_text(s, x, py + ph + Inches(0.1), pw, Inches(0.3), "인사이트 (4 탭)", size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # === Phone 3: Coupons + Kakao ===
    x = px + 2 * (pw + gap)
    phone = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, py, pw, ph)
    phone.adjustments[0] = 0.06
    phone.fill.solid(); phone.fill.fore_color.rgb = RGBColor(0x1F, 0x29, 0x37); phone.line.fill.background()
    sx_in = x + Inches(0.1); sy_in = py + Inches(0.15)
    screen = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in, sy_in, sw_in, sh_in)
    screen.adjustments[0] = 0.04
    screen.fill.solid(); screen.fill.fore_color.rgb = WHITE; screen.line.fill.background()
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx_in, sy_in, sw_in, Inches(0.4))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(0.1), sw_in - Inches(0.3), Inches(0.25), "쿠폰 발행", size=10, bold=True, color=WHITE)
    # QR 박스 (모형)
    qr_x = sx_in + Inches(0.55); qr_y = sy_in + Inches(0.7)
    qr_w = Inches(1.4)
    add_rect(s, qr_x, qr_y, qr_w, qr_w, fill=NAVY, line=None)
    # QR 패턴 모방 (8x8 grid)
    cell = qr_w / 9
    for r in range(8):
        for col in range(8):
            if (r + col) % 2 == 0 and not (r in [0,7] and col in [0,7]):
                cx = qr_x + Inches(0.1) + col * cell * 0.95
                cy = qr_y + Inches(0.1) + r * cell * 0.95
                if r in [0,1,5,6,7] and col in [0,1,2,5,6,7]:
                    cell_box = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, cell * 0.7, cell * 0.7)
                    cell_box.fill.solid(); cell_box.fill.fore_color.rgb = WHITE; cell_box.line.fill.background()
    # 쿠폰 정보
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(2.4), sw_in - Inches(0.3), Inches(0.3), "재방문 쿠폰 · 5,000원", size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(2.7), sw_in - Inches(0.3), Inches(0.25), "유효 7일 / 1인 1회", size=9, color=GREY, align=PP_ALIGN.CENTER)
    # 카톡 공유 버튼
    btn = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in + Inches(0.3), sy_in + Inches(3.1), sw_in - Inches(0.6), Inches(0.4))
    btn.adjustments[0] = 0.4
    btn.fill.solid(); btn.fill.fore_color.rgb = RGBColor(0xFE, 0xE5, 0x00); btn.line.fill.background()
    add_text(s, sx_in + Inches(0.3), sy_in + Inches(3.18), sw_in - Inches(0.6), Inches(0.3), "카카오톡으로 공유", size=10, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(3.7), sw_in - Inches(0.3), Inches(0.3), "스캔 14건", size=8, color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, x, py + ph + Inches(0.1), pw, Inches(0.3), "쿠폰 + 카카오 공유", size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # === Phone 4: PDF 진단서 ===
    x = px + 3 * (pw + gap)
    phone = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, py, pw, ph)
    phone.adjustments[0] = 0.06
    phone.fill.solid(); phone.fill.fore_color.rgb = RGBColor(0x1F, 0x29, 0x37); phone.line.fill.background()
    sx_in = x + Inches(0.1); sy_in = py + Inches(0.15)
    screen = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in, sy_in, sw_in, sh_in)
    screen.adjustments[0] = 0.04
    screen.fill.solid(); screen.fill.fore_color.rgb = WHITE; screen.line.fill.background()
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx_in, sy_in, sw_in, Inches(0.4))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    add_text(s, sx_in + Inches(0.15), sy_in + Inches(0.1), sw_in - Inches(0.3), Inches(0.25), "PDF 진단서", size=10, bold=True, color=WHITE)
    # PDF 미리보기 표지 (토스 톤: 검정 배경 + 토스 블루 강조)
    pdf_x = sx_in + Inches(0.3); pdf_y = sy_in + Inches(0.65)
    pdf_w = sw_in - Inches(0.6); pdf_h = Inches(2.6)
    add_rect(s, pdf_x, pdf_y, pdf_w, pdf_h, fill=TOSS_TEXT, line=None)
    add_text(s, pdf_x + Inches(0.15), pdf_y + Inches(0.2), pdf_w - Inches(0.3), Inches(0.3), "우리 가게", size=9, color=WHITE, bold=True)
    add_text(s, pdf_x + Inches(0.15), pdf_y + Inches(0.5), pdf_w - Inches(0.3), Inches(0.4), "진단서", size=18, bold=True, color=WHITE)
    add_text(s, pdf_x + Inches(0.15), pdf_y + Inches(1.0), pdf_w - Inches(0.3), Inches(0.25), "종합 점수", size=8, color=TOSS_BLUE)
    add_text(s, pdf_x + Inches(0.15), pdf_y + Inches(1.25), pdf_w - Inches(0.3), Inches(0.5), "67 / 100", size=22, bold=True, color=TOSS_BLUE, font=FONT_EN)
    add_text(s, pdf_x + Inches(0.15), pdf_y + Inches(1.85), pdf_w - Inches(0.3), Inches(0.6), "관찰 등급\n6 카테고리 가중", size=8, color=WHITE, line_spacing=1.4)
    # 다운로드 버튼
    btn = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx_in + Inches(0.3), sy_in + Inches(3.5), sw_in - Inches(0.6), Inches(0.4))
    btn.adjustments[0] = 0.4
    btn.fill.solid(); btn.fill.fore_color.rgb = NAVY; btn.line.fill.background()
    add_text(s, sx_in + Inches(0.3), sy_in + Inches(3.58), sw_in - Inches(0.6), Inches(0.3), "PDF 다운로드", size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, py + ph + Inches(0.1), pw, Inches(0.3), "PDF 진단서", size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    # 하단 — 라이브 데모 안내
    add_rect(s, Inches(0.5), Inches(6.65), Inches(12.3), Inches(0.4), fill=NAVY, line=None)
    add_text(s, Inches(0.7), Inches(6.71), Inches(11.9), Inches(0.3),
             "라이브 데모 가능 — 발표 중 시연 가능",
             size=10, bold=True, color=WHITE)
    add_footer(s, 12, TOTAL,
               "위 4 화면은 라이브 앱 미니어처 · 실 사용자 데이터는 베타 출시 후 측정 예정")

    # ============ Slide 11 — UI/UX ============
    s = blank_slide(p)
    add_header(s, 12, TOTAL, 10, "완성도 2 — UI/UX: 시니어 친화 + 3-클릭 룰", ["완성"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "60대 사장님 손에서도 3 클릭이면 끝나요",
             size=24, bold=True, color=NAVY)
    ux = [
        ("3-클릭 룰", "어떤 핵심 기능도 3번 안에 도달.\n온보딩 → 홈 → 액션 = 3 클릭.", "사용 편리성"),
        ("최소 14px 본문", "시니어 시인성 기본 14px 이상.\n보조 텍스트도 12px 하한.", "접근성"),
        ("정중 톤 분기", "시니어·폐업 위험 사장님은\n명령조 ❌ → '확인해 보세요' 톤.", "안전성"),
        ("1393 의무 안내", "분기별 자살예방상담 안내.\n폐업 위험 카드 옆 상시.", "윤리"),
        ("출처 라벨 의무", "모든 데이터 카드 옆에\n'서울 ○○ · Q4' 출처 표기.", "정직성"),
        ("노란 '추정' 표시", "GPT 답변에 노란 '추정' 표시 자동.\n사용자가 출처 매번 인지.", "투명성"),
    ]
    ux_x = Inches(0.5); ux_y = Inches(1.7); ux_w = Inches(4.0); ux_h = Inches(1.45)
    for i, (name, body, badge) in enumerate(ux):
        col = i % 3; row = i // 3
        x = ux_x + col * (ux_w + Inches(0.15))
        y = ux_y + row * (ux_h + Inches(0.2))
        add_rect(s, x, y, ux_w, ux_h, fill=LIGHTER, line=LINE)
        add_text(s, x + Inches(0.2), y + Inches(0.12), ux_w - Inches(0.4), Inches(0.3), name, size=13, bold=True, color=NAVY)
        add_text(s, x + Inches(0.2), y + Inches(0.45), ux_w - Inches(0.4), Inches(0.65), body, size=10, color=SLATE, line_spacing=1.4)
        add_text(s, x + Inches(0.2), y + Inches(1.1), ux_w - Inches(0.4), Inches(0.3), f"→ {badge}", size=9, color=GREEN, bold=True)
    # PWA + 카카오 강조
    add_rect(s, Inches(0.5), Inches(4.95), Inches(12.3), Inches(1.5), fill=NAVY, line=None)
    add_text(s, Inches(0.7), Inches(5.1), Inches(11), Inches(0.4), "PWA + 카카오 = 앱 설치 부담 0", size=14, bold=True, color=WHITE)
    add_text(s, Inches(0.7), Inches(5.55), Inches(11.9), Inches(0.85),
             "• 카카오 OAuth 1탭 가입 (state CSRF 보호)  • PWA manifest + service worker 오프라인 fallback\n• 하단 네비게이션 동적 active  • 카카오톡 알림톡 + FCM (카카오 알림톡 → FCM → 조용히 실패 (3중 안전망))",
             size=11, color=WHITE, line_spacing=1.5)
    add_footer(s, 13, TOTAL, "PWA 90+ 점수 목표 · 카카오 OAuth · 음성 입력 지원")

    # ============ Slide 12 — Demo Flow ============
    s = blank_slide(p)
    add_header(s, 13, TOTAL, 11, "5분 시연 흐름 — 6 STEP 데모", ["완성"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "5분이면 가입부터 진단까지 다 보여드려요",
             size=24, bold=True, color=NAVY)
    steps = [
        ("01", "랜딩 → 카카오 1탭", "OAuth state CSRF 보호\n30초 안에 가입"),
        ("02", "온보딩 3단계", "사업자번호 → 가게 → 개점일\n진척도 1/3 → 2/3 → 3/3"),
        ("03", "대시보드 첫 진입", "위험도 67/100 (관찰)\n출처 라벨 + 손실 카운터"),
        ("04", "폐업 매트릭스 카드", "결정론 5신호 + 1-액션\n'AI 코치만 알 수 있는 손실'"),
        ("05", "지원사업 매칭", "지역·업종 자동 매칭 + 사용자 학습\n마감 임박 표시 + 매칭 사유"),
        ("06", "PDF 진단서 다운로드", "표지 + 점수·진단·액션·집중분석\n끊김 없이 한 흐름"),
    ]
    sx = Inches(0.5); sy = Inches(1.8); sw = Inches(2.0); sh = Inches(2.5)
    for i, (n, name, body) in enumerate(steps):
        x = sx + i * (sw + Inches(0.05))
        add_rect(s, x, sy, sw, sh, fill=LIGHTER, line=LINE)
        # 번호 박스
        add_rect(s, x, sy, sw, Inches(0.5), fill=NAVY, line=None)
        add_text(s, x + Inches(0.15), sy + Inches(0.12), sw - Inches(0.3), Inches(0.3), f"STEP {n}", size=11, bold=True, color=WHITE)
        add_text(s, x + Inches(0.15), sy + Inches(0.65), sw - Inches(0.3), Inches(0.7), name, size=12, bold=True, color=NAVY, line_spacing=1.3)
        add_text(s, x + Inches(0.15), sy + Inches(1.4), sw - Inches(0.3), Inches(1.0), body, size=9, color=SLATE, line_spacing=1.4)
    # 화살표 표시
    for i in range(5):
        x = sx + (i + 1) * sw + i * Inches(0.05) - Inches(0.07)
        add_text(s, x, sy + Inches(1.1), Inches(0.2), Inches(0.3), "▸", size=14, bold=True, color=GREY)
    # 하단 — PDF 진단서 강조
    add_rect(s, Inches(0.5), Inches(4.7), Inches(12.3), Inches(1.8), fill=TOSS_CARD, line=None)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(4.7), Inches(0.06), Inches(1.8))
    bar.fill.solid(); bar.fill.fore_color.rgb = TOSS_BLUE; bar.line.fill.background()
    add_text(s, Inches(0.7), Inches(4.85), Inches(11), Inches(0.4), "우리 가게 진단서 PDF — 2026-05 새 레이아웃", size=14, bold=True, color=TOSS_TEXT)
    add_text(s, Inches(0.7), Inches(5.3), Inches(11.9), Inches(1.1),
             "표지 1장 → 점수 분포 → 주요 진단 → 액션 플랜 (Quick Win / Mid / Strategic) → 집중 분석이 한 흐름.\n사장님이 '다음 페이지 어디 있지' 끊지 않고 한 번에 읽을 수 있어요.\n차트 옆에는 '※ 출처: 서울 전체 치킨전문점 평균 (사장님 가게 매출 아님)' 8pt 라벨 의무.",
             size=10, color=SLATE, line_spacing=1.5)
    add_footer(s, 14, TOTAL, "발표 중 라이브 시연 가능 · PDF 평균 4페이지 · 한글 폰트 임베드")

    # ============ Slide 13 — System Architecture ============
    s = blank_slide(p)
    add_header(s, 14, TOTAL, 12, "시스템 + 데이터 흐름 — Phased Pattern 24s→0.25s", ["완성", "AI"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "24초 멈추던 게 0.25초로 — 100배 빨라졌어요 (실측)",
             size=24, bold=True, color=NAVY)
    # 기술 스택
    add_text(s, Inches(0.5), Inches(1.7), Inches(6), Inches(0.3), "기술 스택 (버전 잠금)", size=12, bold=True, color=GREY)
    stack = [
        ("Frontend", "Next.js 14 · TypeScript · Tailwind · Zustand · PWA · Web Speech"),
        ("Backend", "FastAPI · Python 3.11+ · SQLAlchemy 2 (async) · Pydantic v2"),
        ("Database", "PostgreSQL 15 · ChromaDB 0.5 (PersistentClient)"),
        ("AI", "OpenAI GPT-4o · text-embedding-3-small · APScheduler"),
        ("Auth", "Kakao OAuth · JWT(HS256) · token_version 회전"),
        ("Deploy", "Vercel(FE) · Railway(BE) · Docker Compose(Local)"),
    ]
    for i, (k, v) in enumerate(stack):
        y = Inches(2.05) + i * Inches(0.32)
        add_text(s, Inches(0.5), y, Inches(1.2), Inches(0.3), k, size=10, bold=True, color=NAVY)
        add_text(s, Inches(1.7), y, Inches(5), Inches(0.3), v, size=10, color=SLATE, font=FONT_EN)
    # Phased Pattern 박스
    add_rect(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(4.7), fill=TOSS_CARD, line=TOSS_BLUE, line_w=2.0)
    add_text(s, Inches(7.2), Inches(1.85), Inches(5.5), Inches(0.4), "Phased Pattern — DB 세션 조기 해제", size=13, bold=True, color=TOSS_BLUE)
    add_text(s, Inches(7.2), Inches(2.3), Inches(5.5), Inches(0.3), "기존 (단일 세션 점유)", size=10, bold=True, color=RED)
    add_text(s, Inches(7.2), Inches(2.6), Inches(5.5), Inches(1.0),
             "@get('/dashboard'), db = Depends(get_db):\n  results = await asyncio.gather(...)  # 14 코루틴\n  → 동시 10명 시 풀 고갈, 24초 hang",
             size=9, color=SLATE, font=FONT_EN, line_spacing=1.4)
    add_text(s, Inches(7.2), Inches(3.7), Inches(5.5), Inches(0.3), "Phased Pattern (P0 fix 완료)", size=10, bold=True, color=TOSS_BLUE)
    add_text(s, Inches(7.2), Inches(4.0), Inches(5.5), Inches(1.5),
             "Phase A: async with session: DB 쿼리만\nPhase B: 외부 API gather (DB 점유 0)\nPhase A2: async with session: 캐시 저장\n→ 카카오 콜백 24초 → 0.25초 (실측)",
             size=9, color=SLATE, font=FONT_EN, line_spacing=1.4)
    add_text(s, Inches(7.2), Inches(5.6), Inches(5.5), Inches(0.7),
             "✓ alembic 7 마이그레이션\n✓ 동시 10명 응답 ≤ 5초 / DB 풀 점유율 ≤ 30%",
             size=10, color=TOSS_BLUE, bold=True, line_spacing=1.4)
    add_footer(s, 15, TOTAL, "31 라우트 · 8 데이터 모델 · 자동화 작업 3개 · 개인정보 보호·접근 제한·로그인 갱신")

    # ============ Slide 14 — Traction (Toss Style: 거대 숫자 1개) ============
    s = blank_slide(p)
    add_header(s, 15, TOTAL, 13, "지금까지 만든 것 — 라이브 시연 가능", ["완성", "발전"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.6),
             "결제 0건. 대신, 라이브 14 기능.",
             size=44, bold=True, color=TOSS_TEXT)
    # 거대 숫자 1개 (토스 블루) + 우측 보조 카드
    add_text(s, Inches(0.5), Inches(2.4), Inches(5), Inches(2.5),
             "14", size=180, bold=True, color=TOSS_TEXT, font=FONT_EN, line_spacing=1.0)
    add_text(s, Inches(0.5), Inches(4.8), Inches(5), Inches(0.4),
             "라이브 핵심 기능", size=20, bold=True, color=TOSS_TEXT)
    
    # 우측 — 카테고리 3 카드 (텍스트 폭 충분히, padding 일관 0.4)
    groups = [
        ("사장님 UX", "5",
         "대시보드 · 인사이트 · 쿠폰\nPDF · STT 음성"),
        ("AI · 데이터", "5",
         "폐업 매트릭스 · 보조금 매칭\n10명 이상 노출 · 노란 '추정' 표시"),
        ("인프라", "4",
         "카카오 OAuth · FCM 폴백\n7AM cron · Phased Pattern"),
    ]
    gx = Inches(6.3); gy = Inches(2.4); gw = Inches(6.5); gh = Inches(1.4)
    PAD = Inches(0.4)
    for i, (gname, gnum, gdesc) in enumerate(groups):
        y = gy + i * (gh + Inches(0.15))
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, gx, y, gw, gh)
        card.adjustments[0] = 0.10
        card.fill.solid(); card.fill.fore_color.rgb = TOSS_CARD; card.line.fill.background()
        # 좌측 — 한 라인 통합: "카테고리 · 숫자" (지그재그 시선 제거)
        add_text(s, gx + PAD, y + Inches(0.25), Inches(2.4), Inches(0.4),
                 gname, size=14, bold=True, color=TOSS_TEXT)
        add_text(s, gx + PAD, y + Inches(0.6), Inches(2.4), Inches(0.7),
                 gnum, size=44, bold=True, color=TOSS_BLUE, font=FONT_EN, line_spacing=1.0)
        # 우측 — 설명 (세로 중앙)
        desc_x = gx + PAD + Inches(2.6)
        desc_w = gw - PAD - Inches(2.6) - PAD
        add_text(s, desc_x, y + Inches(0.35), desc_w, gh - Inches(0.5),
                 gdesc, size=12, color=TOSS_SUB, line_spacing=1.5)
    add_footer(s, 16, TOTAL, "31 라우트 · 8 모델 · 7 마이그레이션 · 라이브 데모 가능")

    # ============ Slide 15 — TAM ============
    s = blank_slide(p)
    add_header(s, 16, TOTAL, 14, "시장 — TAM/SAM/SOM bottom-up", ["발전"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "사장님 730만 명 중 30%만 9,900원 쓰면 — 그게 시장이에요",
             size=22, bold=True, color=NAVY)
    # 동심원 형태 카드
    tam_data = [
        ("TAM", "전국 소상공인 (행안부 통계)", "약 730만 사장님 × 30% 디지털 수용 × 9,900원 × 12개월", "2,604억원/년", NAVY),
        ("SAM", "서울 사업자등록 소상공인", "약 65만 사장님 × 30% × 9,900원 × 12개월 (1차 진입 시장)", "232억원/년", TOSS_BLUE),
        ("SOM", "3년 목표 (5,000 MAU × 10% Pro 전환)", "500 Pro × 9,900원 × 12개월 (실측 갱신 예정)", "5,940만원/년", GREEN),
    ]
    for i, (tier, who, formula, value, color) in enumerate(tam_data):
        y = Inches(1.8) + i * Inches(1.4)
        add_rect(s, Inches(0.5), y, Inches(12.3), Inches(1.3), fill=LIGHTER, line=color, line_w=1.5)
        add_text(s, Inches(0.7), y + Inches(0.15), Inches(1.5), Inches(0.5), tier, size=24, bold=True, color=color, font=FONT_EN)
        add_text(s, Inches(2.5), y + Inches(0.18), Inches(5.5), Inches(0.3), who, size=11, bold=True, color=NAVY)
        add_text(s, Inches(2.5), y + Inches(0.5), Inches(5.5), Inches(0.7), formula, size=10, color=SLATE, line_spacing=1.4)
        add_text(s, Inches(8.5), y + Inches(0.3), Inches(4.0), Inches(0.6), value, size=22, bold=True, color=color, font=FONT_EN, align=PP_ALIGN.RIGHT)
    # 정직 라벨
    add_rect(s, Inches(0.5), Inches(6.1), Inches(12.3), Inches(0.6), fill=AMBER_BG, line=AMBER)
    add_text(s, Inches(0.7), Inches(6.2), Inches(11.9), Inches(0.4),
             "TAM·SAM은 가정값 — 결제 출시(2026 Q3) 후 코호트 데이터로 갱신 / SOM은 3년 목표 (Year 2 검증)",
             size=10, bold=True, color=AMBER)
    add_footer(s, 17, TOTAL, "전국 소상공인 통계: 행정안전부 / 서울 사업자등록: 국세청 / 9,900원은 N=8 베타 인터뷰 결제 의향 가격대")

    # ============ Slide 16 — BM ============
    s = blank_slide(p)
    add_header(s, 17, TOTAL, 15, "비즈니스 모델 — Free → Pro → Enterprise", ["발전"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "기본 무료 — 가치 느끼면 9,900원, 그게 다예요",
             size=24, bold=True, color=NAVY)
    plans = [
        ("FREE", "0원", NAVY,
         ["월 3회 쿠폰 발행", "주 1회 마케팅 인사이트", "기본 폐업 매트릭스", "10명 이상 사회적 증거", "PDF 진단서 월 1회"]),
        ("PRO", "9,900원/월", GREEN,
         ["월 무제한 쿠폰", "실시간 마케팅 인사이트", "AI 사업계획서 초안 월 5회", "카카오 알림톡 발송", "PDF 무제한 + CSV/JSON export"]),
        ("ENT", "협의", AMBER,
         ["프랜차이즈 본사 전용", "다점포 통합 대시보드", "API 연동 + SLA", "전담 매니저", "월 50만원~ 가설"]),
    ]
    px = Inches(0.5); py = Inches(1.95); pw = Inches(4.1); ph = Inches(3.4)
    for i, (name, price, color, items) in enumerate(plans):
        x = px + i * (pw + Inches(0.15))
        is_pro = (i == 1)  # PRO 강조
        # PRO는 살짝 위로 띄움 + 토스 블루 헤더 (SaaS pricing 표준)
        card_y = py - Inches(0.15) if is_pro else py
        card_h = ph + Inches(0.15) if is_pro else ph
        head_color = TOSS_BLUE if is_pro else color
        add_rect(s, x, card_y, pw, card_h, fill=WHITE, line=head_color, line_w=2.0)
        head = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, card_y, pw, Inches(1.0))
        head.fill.solid(); head.fill.fore_color.rgb = head_color; head.line.fill.background()
        # 추천 chip (PRO만)
        if is_pro:
            chip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x + pw - Inches(1.1), card_y + Inches(0.15), Inches(0.85), Inches(0.32))
            chip.adjustments[0] = 0.5
            chip.fill.solid(); chip.fill.fore_color.rgb = WHITE; chip.line.fill.background()
            add_text(s, x + pw - Inches(1.1), card_y + Inches(0.21), Inches(0.85), Inches(0.25),
                     "추천", size=10, bold=True, color=TOSS_BLUE, align=PP_ALIGN.CENTER)
        add_text(s, x + Inches(0.3), card_y + Inches(0.1), pw - Inches(0.5), Inches(0.4), name, size=18, bold=True, color=WHITE)
        add_text(s, x + Inches(0.3), card_y + Inches(0.55), pw - Inches(0.5), Inches(0.4), price, size=20, bold=True, color=WHITE, font=FONT_EN)
        for j, it in enumerate(items):
            add_text(s, x + Inches(0.3), card_y + Inches(1.15) + j * Inches(0.4), pw - Inches(0.6), Inches(0.35), f"·  {it}", size=11, color=SLATE, line_spacing=1.4)
    # 가설 라벨 (옅은 회색 + 좌측 컬러 바 — 토스 톤)
    add_rect(s, Inches(0.5), Inches(5.65), Inches(12.3), Inches(0.9), fill=TOSS_CARD, line=None)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(5.65), Inches(0.06), Inches(0.9))
    bar.fill.solid(); bar.fill.fore_color.rgb = TOSS_AMBER; bar.line.fill.background()
    add_text(s, Inches(0.7), Inches(5.75), Inches(11.9), Inches(0.4), "결제 모듈은 2026 Q3 출시 예정 — 그 전 수치는 가설", size=11, bold=True, color=TOSS_TEXT)
    add_text(s, Inches(0.7), Inches(6.1), Inches(11.9), Inches(0.4),
             "베타 인터뷰 N=8 중 5명 9,900원 결제 의향 → 모집단 작음, Year 2 코호트로 검증",
             size=10, color=TOSS_SUB)
    add_footer(s, 18, TOTAL, "결제 모듈 Q3 통합 예정 · 9,900원은 베타 인터뷰 가설 · 실 결제 0건")

    # ============ Slide 17 — Roadmap ============
    s = blank_slide(p)
    add_header(s, 18, TOTAL, 16, "1년 로드맵 — 작게, 단계적으로", ["발전"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.6),
             "올해 결제 출시, 내년 첫 1,000 사장님.",
             size=36, bold=True, color=TOSS_TEXT)
    # 토스식 세로 타임라인 (좌측 점·선 + 우측 분기 카드)
    quarters = [
        ("Q3 2026", "결제 모듈 출시",
         "PortOne/Toss 결제 통합 · 첫 100 사장님 베타 · PostHog 텔레메트리", True),
        ("Q4 2026", "첫 매출 + MOU 의향",
         "서울시·소진공 파일럿 의향 · 보조금 시드 22→50건 · AC 입주 신청", True),
        ("Q1 2027", "1,000 MAU 도전",
         "1,000 MAU · 100 Pro 결제 · 첫 코호트 6개월 retention 측정 · Pre-A 검토", False),
        ("Q2 2027", "스케일 검토",
         "코호트 데이터로 PMF 검증 · 프랜차이즈 1~2개 파일럿 · 전국 확장 검토", False),
    ]
    tx = Inches(1.0); ty = Inches(2.2); row_h = Inches(1.0)
    # 좌측 세로 라인
    line = s.shapes.add_connector(1, tx + Inches(0.15), ty + Inches(0.2),
                                   tx + Inches(0.15), ty + row_h * 4 - Inches(0.5))
    line.line.color.rgb = TOSS_BORDER
    line.line.width = Pt(2)
    for i, (q, name, body, is_real) in enumerate(quarters):
        y = ty + i * row_h
        # 좌측 점 (확정은 토스 블루, 미확정은 옅은 회색)
        dot_color = TOSS_BLUE if is_real else TOSS_BORDER
        dot = s.shapes.add_shape(MSO_SHAPE.OVAL, tx, y, Inches(0.3), Inches(0.3))
        dot.fill.solid(); dot.fill.fore_color.rgb = dot_color; dot.line.fill.background()
        # 분기 라벨
        add_text(s, tx + Inches(0.6), y + Inches(0.0), Inches(1.5), Inches(0.35),
                 q, size=13, bold=True, color=TOSS_TEXT, font=FONT_EN)
        # 마일스톤 이름 (큰)
        add_text(s, tx + Inches(2.4), y + Inches(0.0), Inches(8), Inches(0.4),
                 name, size=20, bold=True, color=TOSS_TEXT)
        # 본문
        add_text(s, tx + Inches(2.4), y + Inches(0.4), Inches(9.5), Inches(0.5),
                 body, size=12, color=TOSS_SUB, line_spacing=1.5)

    # 하단 다음 단계 트리거 (옅은 회색 배지)
    trig = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.55))
    trig.adjustments[0] = 0.4
    trig.fill.solid(); trig.fill.fore_color.rgb = TOSS_CARD; trig.line.fill.background()
    add_text(s, Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.4),
             "다음 라운드 트리거 — 결제 100명 (Q3) · MAU 500 (Q4) · 코호트 retention 25%+ (Q1)",
             size=11, bold=True, color=TOSS_TEXT, align=PP_ALIGN.CENTER)
    add_footer(s, 19, TOTAL, "카카오 4분기 마일스톤: 싱크 인증 → 알림톡 검수 → 비즈메시지 → 카카오페이")

    # ============ Slide 18 — Competition ============
    s = blank_slide(p)
    add_header(s, 19, TOTAL, 17, "경쟁 — 우리만 가진 6가지 + 약점 1", ["독창"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "우리만 가진 6가지, 그리고 우리가 못하는 1가지",
             size=24, bold=True, color=NAVY)
    # 비교 테이블
    headers = ["", "기존 자영업 도구", "SSGI · AI 경영코치"]
    rows = [
        ("데이터", "1~3종 자체 (POS·SNS)", "서울 공공데이터 8종 + 6분야 결합"),
        ("톤앤매너", "'추천합니다' 일반론", "'놓치고 있어요' — 손실 프레이밍"),
        ("매칭", "키워드 검색", "SQL + 사용자 학습 + 검색"),
        ("환각 방지", "GPT 답변 그대로", "3겹 신뢰 계층 + 노란 '추정' 표시"),
        ("시니어 UX·업종", "20~30대 일률 추천", "1393 안내 + 큰 글씨 + 6업종별 다른 처방"),
        ("결제·매출", "출시 + 매출 발생", "—  결제 모듈 Q3 출시 예정 (우리 약점)"),
    ]
    tx = Inches(0.5); ty = Inches(1.8)
    cw = [Inches(2.5), Inches(4.5), Inches(5.3)]
    # 헤더
    for ci, h in enumerate(headers):
        x = tx + sum(cw[:ci], Inches(0))
        add_rect(s, x, ty, cw[ci], Inches(0.5), fill=NAVY, line=None)
        add_text(s, x + Inches(0.2), ty + Inches(0.12), cw[ci] - Inches(0.4), Inches(0.3), h, size=11, bold=True, color=WHITE)
    # 행
    for ri, row in enumerate(rows):
        y = ty + Inches(0.5) + ri * Inches(0.65)
        bg = LIGHTER if ri % 2 == 0 else WHITE
        for ci, cell in enumerate(row):
            x = tx + sum(cw[:ci], Inches(0))
            add_rect(s, x, y, cw[ci], Inches(0.65), fill=bg, line=LINE)
            color = NAVY if ci == 0 else (GREY if ci == 1 else NAVY)
            bold = ci == 0 or ci == 2
            add_text(s, x + Inches(0.2), y + Inches(0.18), cw[ci] - Inches(0.4), Inches(0.4), cell, size=10, bold=bold, color=color, line_spacing=1.3)
    add_footer(s, 20, TOTAL, "비교 대상: 캐치테이블·당근비즈·소상공인시장진흥공단 가게의 발견 등 (2026-04 자체 조사)")

    # ============ Slide 19 — ESG ============
    s = blank_slide(p)
    add_header(s, 20, TOTAL, 18, "ESG — 환경 정량 + 사회 폐업방지 23~49명", ["ESG"])
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "환경 262톤·사회 49명·원칙 6개 — 다 숫자로.",
             size=22, bold=True, color=NAVY)
    esg = [
        ("ENVIRONMENT", "262", "tCO2eq/년 절감 추정", GREEN, [
            ("페이퍼리스 보조금 신청", "1만 명 × 12장 × 연 3회", "≈ 14.4 tCO2eq"),
            ("POP·전단지 → QR 전환", "가게당 50장/월 × 12 × 1만", "≈ 240 tCO2eq"),
            ("행정복지센터 이동 절감", "1.2km × 3회 × 1만 명", "≈ 7.6 tCO2eq"),
        ]),
        ("SOCIAL", "49", "명 폐업 방지/년 (추정)", TOSS_BLUE, [
            ("폐업 방지 추정", "활성 2,500명 × 손실프레이밍 7~15%p", "23~49명/년"),
            ("정보 비대칭 해소", "시니어·디지털 절벽 사장님 접근", "베타 후 정량화"),
            ("자살예방 안내", "1393 분기별 의무 노출", "윤리 안전망"),
        ]),
        ("GOVERNANCE", "6", "원칙 시스템 강제", TOSS_TEXT, [
            ("원칙 6개 변경 금지", "손실 프레이밍·개인정보 보호·하루 1액션 등", "거버넌스 록"),
            ("출처 라벨 의무화", "모든 데이터 카드 옆에 '서울 ○○ Q4'", "정직성"),
            ("AI 답변 자동 표시", "GPT 답변에 항상 노란 '추정' 표시", "투명성"),
        ]),
    ]
    ex = Inches(0.5); ey = Inches(1.7); ew = Inches(4.1); eh = Inches(4.7)
    for i, (cat, big, big_sub, color, items) in enumerate(esg):
        x = ex + i * (ew + Inches(0.1))
        # 둥근 카드 + 상단 4px 컬러 바
        add_rect(s, x, ey, ew, eh, fill=TOSS_CARD, line=None)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, ey, ew, Inches(0.06))
        bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.fill.background()
        # 카테고리 라벨
        add_text(s, x + Inches(0.3), ey + Inches(0.3), ew - Inches(0.6), Inches(0.3),
                 cat, size=10, bold=True, color=color, font=FONT_EN)
        # 빅넘버 (Agent 진단: ESG 빅넘버 누락 — 토스 톤 추가)
        add_text(s, x + Inches(0.3), ey + Inches(0.7), ew - Inches(0.6), Inches(1.3),
                 big, size=72, bold=True, color=color, font=FONT_EN, line_spacing=1.0)
        add_text(s, x + Inches(0.3), ey + Inches(2.0), ew - Inches(0.6), Inches(0.4),
                 big_sub, size=12, color=TOSS_SUB, line_spacing=1.3)
        # 산식 항목 3개 (작게)
        for j, (name, formula, val) in enumerate(items):
            iy = ey + Inches(2.65) + j * Inches(0.7)
            add_text(s, x + Inches(0.3), iy, ew - Inches(0.6), Inches(0.25),
                     name, size=10, bold=True, color=TOSS_TEXT)
            add_text(s, x + Inches(0.3), iy + Inches(0.25), ew - Inches(0.6), Inches(0.25),
                     formula, size=8, color=TOSS_LIGHT)
            add_text(s, x + Inches(0.3), iy + Inches(0.45), ew - Inches(0.6), Inches(0.25),
                     val, size=10, bold=True, color=color)
    add_footer(s, 21, TOTAL, "환산: 종이 1톤 = 약 8 tCO2eq · 차량 0.21 kgCO2/km · 폐업방지는 손실프레이밍 효과 추정")

    # ============ Slide 20 — Closing (Toss Style — 흰 배경 + 거대 헤드) ============
    s = blank_slide(p)
    # 흰 배경 + 작은 페이지 라벨
    add_text(
        s, Inches(0.9), Inches(0.8), Inches(8), Inches(0.3),
        "20 / 20    CLOSING",
        size=11, color=TOSS_LIGHT, bold=True,
    )
    # 거대 슬로건 (Hero) — width 12.4in 페이지 폭 충분히 활용 (잘림 방지)
    add_text(
        s, Inches(0.5), Inches(1.6), Inches(12.4), Inches(3.0),
        "사장님이 매일 받는,\n1줄 처방.",
        size=80, bold=True, color=TOSS_TEXT, line_spacing=1.2,
    )
    # 강조 1줄 (토스 블루) — 헤드라인 끝과 0.5in 안전 간격
    add_text(
        s, Inches(0.9), Inches(4.95), Inches(11.9), Inches(0.6),
        '"추천합니다"가 아니라 "놓치고 있어요".',
        size=28, color=RGBColor(0x1D, 0x4E, 0xD8), bold=True,
    )
    # 마무리 — 차분
    add_text(
        s, Inches(0.9), Inches(5.85), Inches(11.5), Inches(1.2),
        "한 명의 사장님이라도 폐업의 절벽에서 한 발 물러서게 한다면,\n이 시스템은 그 한 가지로 충분해요.",
        size=18, color=TOSS_SUB, line_spacing=1.5,
    )
    add_text(
        s, Inches(0.9), SLIDE_H - Inches(0.5), Inches(12), Inches(0.3),
        "팀 SSGI  ·  2026 서울시 빅데이터 활용 경진대회",
        size=10, color=TOSS_LIGHT,
    )

    # ============ Backup 1 — 출처 표기 ============
    s = blank_slide(p)
    add_header(s, 0, 0, 0, "BACKUP A — 출처 / 인용 / 데이터 명세")
    add_text(s, Inches(0.5), Inches(1.0), Inches(12), Inches(0.5),
             "공고 5번 — 활용 공공데이터 목록 정확 기재",
             size=18, bold=True, color=NAVY)
    sources = [
        ("서울 열린데이터광장", "VwsmTrdarSelngQq · 서울시 우리마을가게 상권분석서비스(상권-추정매출)", "분기, 25 자치구"),
        ("서울 열린데이터광장", "VwsmTrdarStorQq · 서울시 우리마을가게 상권분석서비스(상권-점포)", "분기, 25 자치구"),
        ("서울 열린데이터광장", "VwsmTrdarIxQq · 서울시 우리마을가게 상권분석서비스(상권-상권변화지표)", "분기"),
        ("서울 열린데이터광장", "VwsmTrdarFlpopQq · 서울시 우리마을가게 상권분석서비스(상권-추정유동인구)", "분기"),
        ("서울 열린데이터광장", "SPOP_LOCAL_RESD_DONG · 서울시 행정동 단위 서울 생활인구 (내국인)", "일별"),
        ("서울 열린데이터광장", "culturalEventInfo · 서울시 문화행사 정보", "일별"),
        ("서울 열린데이터광장", "VwsmTrdarFcltyQq · 서울시 우리마을가게 상권분석서비스(상권-집객시설)", "분기"),
        ("서울 열린데이터광장", "VwsmTrdarWrcPopltnQq · 서울시 우리마을가게 상권분석서비스(상권-직장인구)", "분기"),
        ("공공데이터포털", "국세청 사업자등록정보 진위확인 (otws_signlw)", "실시간"),
        ("민간 API", "Kakao Local Search API · 카카오 디벨로퍼스", "실시간"),
    ]
    for i, (provider, dataset, period) in enumerate(sources):
        y = Inches(1.7) + i * Inches(0.36)
        add_text(s, Inches(0.5), y, Inches(2.2), Inches(0.3), provider, size=9, bold=True, color=NAVY)
        add_text(s, Inches(2.8), y, Inches(8.0), Inches(0.3), dataset, size=9, color=SLATE)
        add_text(s, Inches(11.0), y, Inches(2), Inches(0.3), period, size=9, color=GREY, align=PP_ALIGN.RIGHT)
    add_footer(s, 21, TOTAL, "추출일 2026-04 / 공고 5번 '활용한 공공데이터 목록 정확 기재' 의무사항 충족")

    out = Path(__file__).resolve().parent.parent / "SSGI_AI경영코치_상세기획서.pptx"
    p.save(out)
    print(f"✓ 저장: {out}")
    print(f"  슬라이드: {len(p.slides)}장 (본문 19 + 백업 1)")
    return out


if __name__ == "__main__":
    build()
