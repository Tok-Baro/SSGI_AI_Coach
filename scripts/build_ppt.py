"""SSGI AI 경영코치 상세기획서 PPT 생성기.

2026-05-09 5-패널 검토(PANEL-REVIEW-AGGREGATE.md) 정정 5+7건 반영.
2026-05-10 sme-coach 6업종 분기 + 치킨 매핑 fix + PDF 연속 흐름 추가 반영.
human-tone 스킬 적용 (한자 0개·해요체·사장님 호칭·손실 프레이밍).

구조: 본문 14장 + Q&A 백업 4장 = 18장.
실행: backend/.venv/bin/python scripts/build_ppt.py
출력: SSGI_AI_경영코치_상세기획서.pptx (덮어쓰기)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from lxml import etree


def _set_run_font(run, name: str):
    """python-pptx의 font.name은 latin만 설정.
    한글 글리프가 다른 폰트로 떨어지지 않도록 ea(EastAsian) + cs(complexScript)도 같이 명시."""
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        existing = rPr.find(qn(f"a:{tag}"))
        if existing is not None:
            rPr.remove(existing)
        el = etree.SubElement(rPr, qn(f"a:{tag}"))
        el.set("typeface", name)

# ===== 디자인 시스템 =====
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# 색
NAVY = RGBColor(0x1E, 0x3A, 0x8A)       # 권위/안전
LOSS = RGBColor(0xDC, 0x26, 0x26)       # 손실 빨강
AMBER = RGBColor(0xD9, 0x77, 0x06)      # AI 추정
INK = RGBColor(0x1F, 0x29, 0x37)        # 본문
GRAY = RGBColor(0x6B, 0x72, 0x80)       # 메타
LIGHT = RGBColor(0xF3, 0xF4, 0xF6)      # 카드 배경
SUCCESS = RGBColor(0x05, 0x96, 0x69)    # 성공
BORDER = RGBColor(0xE5, 0xE7, 0xEB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# 평가 채점표 매칭 컬러 칩
CHIP_COLORS = {
    "공공25": RGBColor(0x1E, 0x3A, 0x8A),
    "AI20": RGBColor(0x7C, 0x3A, 0xED),
    "독창15": RGBColor(0xDC, 0x26, 0x26),
    "완성15": RGBColor(0x05, 0x96, 0x69),
    "발전20": RGBColor(0xD9, 0x77, 0x06),
    "ESG5": RGBColor(0x06, 0xB6, 0xD4),
}

FONT = "Pretendard Variable"  # 사용자 ~/Library/Fonts/ 설치 확인됨
FONT_FALLBACK = "Apple SD Gothic Neo"

TOTAL_PAGES = 14   # 본문 14장 (백업은 별도 P. 표기)


def _set_text(tf, text: str, *, size: int = 12, bold: bool = False,
              color=INK, align=PP_ALIGN.LEFT, font=FONT):
    """TextFrame에 텍스트 + 스타일 적용."""
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    _set_run_font(run, font)  # latin + ea + cs 모두 같은 폰트로


def _add_text(slide, x, y, w, h, text: str, *, size=12, bold=False,
              color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """슬라이드에 텍스트 박스 추가."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    _set_text(tf, text, size=size, bold=bold, color=color, align=align)
    return tb


def _add_multiline(slide, x, y, w, h, lines: list[tuple[str, dict]],
                   anchor=MSO_ANCHOR.TOP):
    """여러 줄 — 각 줄 (text, style_dict). style_dict: size/bold/color/align."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, (text, style) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = style.get("align", PP_ALIGN.LEFT)
        run = p.add_run()
        run.text = text
        run.font.size = Pt(style.get("size", 12))
        run.font.bold = style.get("bold", False)
        run.font.color.rgb = style.get("color", INK)
        _set_run_font(run, style.get("font", FONT))
        if "space_after" in style:
            p.space_after = Pt(style["space_after"])
    return tb


def _add_card(slide, x, y, w, h, *, fill=LIGHT, border=BORDER, line_w=0.5):
    """둥근 카드(배경 + 얇은 테두리)."""
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    rect.adjustments[0] = 0.04
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill
    rect.line.color.rgb = border
    rect.line.width = Pt(line_w)
    rect.shadow.inherit = False
    return rect


def _add_chip(slide, x, y, label: str, color=NAVY, *, fg=WHITE, w=Inches(0.55)):
    """평가 매칭 컬러 칩."""
    h = Inches(0.22)
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    rect.adjustments[0] = 0.5
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    rect.line.fill.background()
    rect.shadow.inherit = False
    tf = rect.text_frame
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.word_wrap = False
    _set_text(tf, label, size=8, bold=True, color=fg, align=PP_ALIGN.CENTER)
    return rect


def _add_amber_chip(slide, x, y, label: str = "AI 추정"):
    """GPT 산출물 amber 일관 라벨."""
    return _add_chip(slide, x, y, label, color=AMBER, fg=WHITE, w=Inches(0.7))


def _header(slide, page_num: int, *, total=TOTAL_PAGES, suffix=""):
    """모든 슬라이드 상단 공통 헤더 + 페이지 번호."""
    _add_text(slide, Inches(0.6), Inches(0.3), Inches(10), Inches(0.3),
              "SSGI AI 경영코치 · 2026 서울 빅데이터 활용 경진대회 · 창업부문",
              size=9, color=GRAY)
    label = f"P. {page_num:02d} / {total}"
    if suffix:
        label = f"{suffix} · " + label
    _add_text(slide, Inches(11.2), Inches(0.3), Inches(1.6), Inches(0.3),
              label, size=9, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    # 헤더 하단 얇은 라인
    line = slide.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                       Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER
    line.line.width = Pt(0.5)


def _section_title(slide, num: str, title: str, subtitle: str = ""):
    """섹션 번호 + 큰 제목 + 부제."""
    _add_text(slide, Inches(0.6), Inches(0.85), Inches(2.0), Inches(0.45),
              num, size=11, bold=True, color=LOSS)
    _add_text(slide, Inches(0.6), Inches(1.15), Inches(12), Inches(0.6),
              title, size=26, bold=True, color=INK)
    if subtitle:
        _add_text(slide, Inches(0.6), Inches(1.78), Inches(12), Inches(0.4),
                  subtitle, size=12, color=GRAY)


def _footer_source(slide, text: str, y=Inches(7.05)):
    """하단 출처 라벨 (모든 차트/카드 의무)."""
    _add_text(slide, Inches(0.6), y, Inches(12.2), Inches(0.3),
              text, size=8, color=GRAY)


# ===== 슬라이드 빌더 =====

def build_cover(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    # 배경 strip
    strip = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, Inches(2.4))
    strip.fill.solid()
    strip.fill.fore_color.rgb = NAVY
    strip.line.fill.background()
    strip.shadow.inherit = False

    _add_text(s, Inches(0.8), Inches(0.7), Inches(11), Inches(0.4),
              "2026 서울특별시 빅데이터 활용 경진대회 · 창업부문",
              size=12, color=WHITE)
    _add_text(s, Inches(0.8), Inches(1.15), Inches(11), Inches(0.6),
              "SSGI AI 경영코치", size=36, bold=True, color=WHITE)
    _add_text(s, Inches(0.8), Inches(1.78), Inches(11), Inches(0.5),
              "사장님이 모르고 놓치는 돈, 데이터가 매일 한 줄로 알려드려요.",
              size=14, color=WHITE)

    # 본문 강조 3개 카드
    pills = [
        ("서울 공공데이터 8종+", "상권·인구·문화·기상"),
        ("3-tier 신뢰 계층", "결정론 + SQL+ICP + GPT-4o"),
        ("'추천' 대신 '놓치고 있어요'", "행동경제학 손실 프레이밍"),
    ]
    cw = Inches(3.9); gap = Inches(0.25)
    for i, (h, sub) in enumerate(pills):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(3.0), cw, Inches(1.4),
                  fill=WHITE, border=BORDER, line_w=1)
        _add_text(s, x + Inches(0.25), Inches(3.2), cw - Inches(0.5), Inches(0.5),
                  h, size=14, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.25), Inches(3.7), cw - Inches(0.5), Inches(0.5),
                  sub, size=11, color=GRAY)

    # 핵심 한 줄
    _add_card(s, Inches(0.6), Inches(4.95), Inches(12.1), Inches(1.2),
              fill=LIGHT, border=BORDER)
    _add_text(s, Inches(0.9), Inches(5.15), Inches(11.5), Inches(0.5),
              "한 명의 사장님이라도 폐업의 절벽에서 한 발 물러서게 한다면,",
              size=14, color=INK)
    _add_text(s, Inches(0.9), Inches(5.55), Inches(11.5), Inches(0.5),
              "이 시스템은 그 한 가지로 충분해요.",
              size=15, bold=True, color=LOSS)

    _add_text(s, Inches(0.6), Inches(6.7), Inches(8), Inches(0.3),
              "팀 SSGI · 정수현 · 구혁모 · 나은민 · 이준수",
              size=10, color=GRAY)
    _add_text(s, Inches(0.6), Inches(7.0), Inches(8), Inches(0.3),
              f"제출 {date.today().strftime('%Y년 %m월 %d일')} · 본문 14장 + 백업 4장",
              size=9, color=GRAY)


def build_toc(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    # 목차는 본문 번호 대상이 아니므로 페이지 번호 미표기
    _add_text(s, Inches(0.6), Inches(0.3), Inches(10), Inches(0.3),
              "SSGI AI 경영코치 · 2026 서울 빅데이터 활용 경진대회 · 창업부문",
              size=9, color=GRAY)
    _add_text(s, Inches(11.2), Inches(0.3), Inches(1.6), Inches(0.3),
              "TABLE OF CONTENTS", size=9, bold=True, color=NAVY,
              align=PP_ALIGN.RIGHT)
    line = s.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                   Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER
    line.line.width = Pt(0.5)
    _section_title(s, "00 · 목차", "한눈에 보는 14장",
                   "옆 색칠 칩은 평가 채점표 매칭 영역이에요")

    items = [
        ("01", "왜 지금 — 사장님이 마주한 정보 비대칭", ["공공25", "독창15"]),
        ("02", "사장님 한 명의 이야기 — 시뮬 페르소나", ["완성15"]),
        ("03", "타깃 페르소나 — 300명 매트릭스 + 신뢰구간", ["완성15"]),
        ("04", "출품작 한 장 + AI 신뢰 계층", ["AI20", "독창15"]),
        ("05", "활용 공공데이터 8종 + 결합", ["공공25"]),
        ("06", "차별점 — 폐업 매트릭스 + 6업종 분기", ["독창15", "AI20"]),
        ("07", "5분 시연 흐름 + 새 PDF 진단서", ["완성15"]),
        ("08", "시스템 + 데이터 흐름 (Phased Pattern)", ["완성15", "AI20"]),
        ("09", "주요 화면 — 대시보드·인사이트·쿠폰", ["완성15"]),
        ("10", "사업화 (TAM 2,604억 bottom-up)", ["발전20"]),
        ("11", "비즈니스 모델 — Free→Pro (베타 N=8)", ["발전20"]),
        ("12", "1년 로드맵 + 카카오 4분기 마일스톤", ["발전20"]),
        ("13", "ESG 정량 — tCO2eq + 폐업방지 23~49명", ["ESG5"]),
        ("14", "클로징 — 한 명이라도 살리면", ["독창15"]),
    ]
    col_w = Inches(6.0); row_h = Inches(0.55)
    for i, (num, title, chips) in enumerate(items):
        col = i // 7
        row = i % 7
        x = Inches(0.6) + col * (col_w + Inches(0.3))
        y = Inches(2.4) + row * row_h
        _add_text(s, x, y, Inches(0.5), Inches(0.4),
                  num, size=12, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.55), y, Inches(3.6), Inches(0.4),
                  title, size=11, color=INK)
        cx = x + Inches(4.2)
        for chip in chips:
            _add_chip(s, cx, y + Inches(0.07), chip,
                      color=CHIP_COLORS[chip])
            cx += Inches(0.62)

    _footer_source(s,
        "1차 서류 평가 6항목 (공공·AI·독창·완성·발전·ESG = 100점) ↔ 2차 발표 매칭 라벨")


def build_background(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 1)
    _section_title(s, "01 · 제안 배경",
                   "사장님이 모르고 놓치는 돈, 매일 한 줄로 알려드려요",
                   "서울 상권 실측 데이터 기반 — 정보 비대칭 3가지")

    pains = [
        ("지원사업이 흩어져 있어요",
         "서울시·자치구·중기부·소진공 4곳에 분산.\n매일 점검 불가능 → 평균 240만원/년 미신청."),
        ("위험을 미리 못 봐요",
         "매출 감소·상권 변화는 폐업이 가까워졌을 때 알아채요.\n결정 시점에 데이터가 없는 거예요."),
        ("진단만 있고 행동이 없어요",
         "리포트는 정보만 주고 끝나요.\n'그래서 뭐 어쩌라고'에 답이 없는 거죠."),
    ]
    cw = Inches(4.0); gap = Inches(0.15)
    for i, (h, body) in enumerate(pains):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(2.4), cw, Inches(1.7), fill=WHITE, border=LOSS, line_w=1.2)
        _add_text(s, x + Inches(0.2), Inches(2.55), cw - Inches(0.4), Inches(0.4),
                  h, size=13, bold=True, color=LOSS)
        _add_text(s, x + Inches(0.2), Inches(2.95), cw - Inches(0.4), Inches(1.1),
                  body, size=10.5, color=INK)

    # 솔루션 한 줄
    _add_card(s, Inches(0.6), Inches(4.3), Inches(12.1), Inches(0.85),
              fill=NAVY, border=NAVY)
    _add_text(s, Inches(0.9), Inches(4.45), Inches(11.5), Inches(0.45),
              "그래서 우리는 — \"추천합니다\"가 아니라 \"놓치고 있어요\"",
              size=15, bold=True, color=WHITE)
    _add_text(s, Inches(0.9), Inches(4.85), Inches(11.5), Inches(0.3),
              "행동경제학 손실 프레이밍 (Kahneman 1979 · Tversky 1981) — ADR 001 시스템 전체 적용",
              size=10, color=WHITE)

    # 통계 4종
    stats = [
        ("4.5년", "서울 폐업 가게 평균 영업기간", "VwsmTrdarIxQq · 2025 4분기"),
        ("9.8년", "서울 운영중 가게 평균", "차이 5.3년이 분기점"),
        ("53.7%", "서울 상권 정체 35.X% + 축소 18.X%", "신규 진입 위험 신호"),
        ("23~49명", "활성 2,500명 가정 폐업 방지 추정", "Tversky-Kahneman 메타 1.5~2.5배"),
    ]
    cw2 = Inches(2.95); gap2 = Inches(0.1)
    for i, (big, mid, small) in enumerate(stats):
        x = Inches(0.6) + i * (cw2 + gap2)
        _add_card(s, x, Inches(5.4), cw2, Inches(1.4), fill=LIGHT, border=BORDER)
        _add_text(s, x + Inches(0.15), Inches(5.5), cw2 - Inches(0.3), Inches(0.55),
                  big, size=22, bold=True, color=LOSS)
        _add_text(s, x + Inches(0.15), Inches(6.05), cw2 - Inches(0.3), Inches(0.4),
                  mid, size=10, bold=True, color=INK)
        _add_text(s, x + Inches(0.15), Inches(6.45), cw2 - Inches(0.3), Inches(0.35),
                  small, size=8.5, color=GRAY)

    _footer_source(s,
        "출처: 서울 열린데이터광장 VwsmTrdarIxQq · 2025 Q4 · 추출일 2026-04 · "
        "KOSIS 자영업 평균 3.1년과 차이 = 모집단 정의(서울 한정·폐업 한정)")


def build_persona_story(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 2)
    _section_title(s, "02 · 사장님 한 명의 이야기",
                   "관악구 문구점 사장님 — 시뮬 페르소나")

    # 인용 카드
    _add_card(s, Inches(0.6), Inches(2.4), Inches(12.1), Inches(2.0),
              fill=WHITE, border=NAVY, line_w=1.5)
    _add_text(s, Inches(0.95), Inches(2.55), Inches(0.5), Inches(0.6),
              '"', size=48, bold=True, color=NAVY)
    _add_text(s, Inches(1.55), Inches(2.7), Inches(11), Inches(0.5),
              "관악구에서 7년째 문구점을 운영해요.",
              size=15, color=INK)
    _add_text(s, Inches(1.55), Inches(3.15), Inches(11), Inches(0.5),
              "매출이 매달 조금씩 빠지는데,",
              size=15, color=INK)
    _add_text(s, Inches(1.55), Inches(3.55), Inches(11), Inches(0.5),
              "어느 정도가 진짜 위험한 건지 알 방법이 없었어요.",
              size=15, color=INK)
    _add_text(s, Inches(1.55), Inches(4.05), Inches(11), Inches(0.4),
              "— 관악구 문구점 사장님 (시뮬 페르소나, 58세) · 8축 매트릭스 구성",
              size=9, color=GRAY)

    # 라벨 칩 (시뮬 명시)
    _add_chip(s, Inches(11.0), Inches(2.55), "시뮬 페르소나", color=AMBER, w=Inches(1.5))

    # 그래서 우리는
    _add_text(s, Inches(0.6), Inches(4.6), Inches(12), Inches(0.5),
              "그래서 우리는 — 데이터로 보는 진짜 손실을 알려드려요",
              size=14, bold=True, color=NAVY)

    deliver = [
        ("폐업 매트릭스",
         "같은 동네 한식 8곳이 평균 53개월에 폐업.\n사장님은 84개월째 — 위험 신호 3건."),
        ("매출 패턴 분석",
         "객단가 1.2만 → 평균 1.5만보다 3천원 낮음.\n점심 세트로 1.4만까지 끌어올릴 수 있어요."),
        ("오늘의 1줄",
         "이번 주 단골 카톡 + 재방문 쿠폰 1종.\n5분이면 끝나요."),
    ]
    cw = Inches(4.0); gap = Inches(0.1)
    for i, (h, body) in enumerate(deliver):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(5.2), cw, Inches(1.5), fill=LIGHT, border=BORDER)
        _add_text(s, x + Inches(0.2), Inches(5.35), cw - Inches(0.4), Inches(0.4),
                  h, size=12, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.2), Inches(5.75), cw - Inches(0.4), Inches(0.9),
                  body, size=10, color=INK)

    _footer_source(s,
        "본 사례는 8축 매트릭스로 구성한 시뮬 페르소나예요 (실 사용자 인터뷰는 베타 후 진행).")


def build_persona_matrix(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 3)
    _section_title(s, "03 · 타깃 사장님",
                   "300명 매트릭스 — 95% 신뢰구간 ±5.7%p · 4 클러스터")

    # 매트릭스 설명
    _add_text(s, Inches(0.6), Inches(2.4), Inches(12), Inches(0.4),
              "8축 페르소나 매트릭스 (업종·자치구·매출·운영기간·연령·디지털·가게형태·핵심고민)",
              size=11, bold=True, color=INK)
    _add_text(s, Inches(0.6), Inches(2.75), Inches(12), Inches(0.4),
              "13,500 조합 공간에서 stratified weighted sampling으로 300명 추출 · 16 클러스터(정렬형 보정)",
              size=10, color=GRAY)

    # 4 대표 클러스터
    clusters = [
        ("디지털 절벽 노포", "한식·도소매 / 50~60대+", "카톡만 / 운영 7년+ / 매출 감소 중"),
        ("1년차 카페", "마포·성동 카페 / 30~40대", "SNS 활용 / 신규 / 마케팅 고민"),
        ("월매출 1500만 미만", "다양 업종 / 폐업 위험 신호 누적", "보조금 미신청 / 단골 부족"),
        ("마케팅 실험족", "30~40대 / SNS·데이터 분석", "캠페인 ROI 검증 욕구"),
    ]
    cw = Inches(2.95); gap = Inches(0.1)
    for i, (h, sub, body) in enumerate(clusters):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(3.3), cw, Inches(1.6), fill=WHITE, border=NAVY, line_w=1)
        _add_text(s, x + Inches(0.15), Inches(3.4), cw - Inches(0.3), Inches(0.4),
                  h, size=12, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.15), Inches(3.8), cw - Inches(0.3), Inches(0.35),
                  sub, size=9.5, color=GRAY)
        _add_text(s, x + Inches(0.15), Inches(4.15), cw - Inches(0.3), Inches(0.7),
                  body, size=10, color=INK)

    # 손실 프레이밍 분기
    _add_text(s, Inches(0.6), Inches(5.15), Inches(12), Inches(0.5),
              "손실 프레이밍 부메랑 방지 — 클러스터별 카피 분기",
              size=13, bold=True, color=LOSS)

    branch = [
        ("C03·C09 (30~40대 마케팅 직군)",
         "긍정 효과 — 가입→실행 전환 60%+ 시뮬 (베타 후 실측)",
         SUCCESS),
        ("C01·C08 (시니어·폐업 위험)",
         "톤 다운 분기 적용 — 정중한 알림 + 자살예방상담 1393 의무 안내",
         AMBER),
    ]
    for i, (h, body, color) in enumerate(branch):
        y = Inches(5.65) + i * Inches(0.7)
        rect = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.6), y, Inches(0.15), Inches(0.5))
        rect.fill.solid(); rect.fill.fore_color.rgb = color
        rect.line.fill.background()
        rect.shadow.inherit = False
        _add_text(s, Inches(0.85), y, Inches(11.8), Inches(0.25),
                  h, size=11, bold=True, color=INK)
        _add_text(s, Inches(0.85), y + Inches(0.27), Inches(11.8), Inches(0.25),
                  body, size=10, color=GRAY)

    _footer_source(s,
        "stratified weighted sampling · 95% CI ±5.7%p · 16 클러스터 (categorical 보정) · "
        "실 사용자 인터뷰 0명, 베타 출시 후 진행 예정")


def build_overview(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 4)
    _section_title(s, "04 · 출품작 한 장",
                   "공공데이터 + 결정론 + GPT-4o = 매일 1줄 카드")

    # WHAT IT IS — 큰 카드
    _add_card(s, Inches(0.6), Inches(2.4), Inches(12.1), Inches(1.4),
              fill=NAVY, border=NAVY)
    _add_text(s, Inches(0.9), Inches(2.55), Inches(2.5), Inches(0.4),
              "WHAT IT IS", size=10, bold=True, color=WHITE)
    _add_text(s, Inches(0.9), Inches(2.85), Inches(11.5), Inches(0.6),
              "서울 공공데이터 + GPT-4o + 결정론 룰을 합쳐서",
              size=15, bold=True, color=WHITE)
    _add_text(s, Inches(0.9), Inches(3.25), Inches(11.5), Inches(0.5),
              "사장님이 매일 \"오늘 놓치고 있는 1가지\"를 받는 카카오 PWA예요.",
              size=14, color=WHITE)

    # 3-tier
    tiers = [
        ("Tier 1 · 결정론 룰", "공식 기반",
         "위험도 점수 / 폐업 매트릭스 / 5-차원 진단\n→ GPT 호출 0회. 환각 0%."),
        ("Tier 2 · 매칭+검색", "GPT 0회",
         "보조금: SQL+ICP 시간가중 재순위 (active path)\nChromaDB: 음성 질의 + 인덱싱 (Q3 활성 매칭 전환)"),
        ("Tier 3 · GPT-4o 자유", "AI 추정 칩",
         "오늘의 액션 / 마케팅 사설 / 집중분석 SWOT\n→ UI에 amber '추정' 라벨 일관 적용."),
    ]
    cw = Inches(4.0); gap = Inches(0.1)
    for i, (h, badge, body) in enumerate(tiers):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(4.0), cw, Inches(2.0), fill=WHITE, border=BORDER, line_w=1)
        _add_text(s, x + Inches(0.2), Inches(4.15), cw - Inches(0.4), Inches(0.4),
                  h, size=12, bold=True, color=NAVY)
        _add_chip(s, x + Inches(0.2), Inches(4.55), badge,
                  color=(SUCCESS if i < 2 else AMBER), w=Inches(0.85))
        _add_text(s, x + Inches(0.2), Inches(4.95), cw - Inches(0.4), Inches(1.0),
                  body, size=10, color=INK)

    _add_text(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.4),
              "AI 코치만 알 수 있는 손실 — 사장님이 모르는 걸 데이터가 매일 짚어드려요",
              size=12, bold=True, color=LOSS, align=PP_ALIGN.CENTER)

    _footer_source(s,
        "보조금 SQL+ICP 매칭 = active · ChromaDB 보조금 인덱싱 완료, 활성 매칭 전환은 2026 Q3 로드맵.")


def build_data_sources(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 5)
    _section_title(s, "05 · 활용 공공데이터",
                   "서울 열린데이터광장 8종 + 다른 분야 결합 = 가점 2점")

    seoul_sets = [
        ("VwsmTrdarSelngQq", "상권 분기별 매출", "QoQ + 객단가 + 시간·요일·연령·성별 비중"),
        ("VwsmTrdarStorQq", "상권 점포 개폐업", "분기 개업률·폐업률·점포 수"),
        ("VwsmTrdarIxQq", "상권 변화 지표", "확장/다이나믹/정체/축소 4단계"),
        ("VwsmTrdarFlpopQq", "상권 유동인구", "시간·요일·성별·연령 (분기 일평균)"),
        ("SPOP_LOCAL_RESD_DONG", "행정동 생활인구", "일별 (T-7 walk)"),
        ("culturalEventInfo", "서울 문화행사", "객단가 캠페인 타이밍"),
        ("VwsmTrdarFcltyQq", "상권 인프라", "관공서·은행·병원·대중교통"),
        ("VwsmTrdarWrcPopltnQq", "상권 직장인구", "점심 매출 잠재력"),
    ]
    _add_text(s, Inches(0.6), Inches(2.4), Inches(12), Inches(0.4),
              "🏛 서울 열린데이터광장 — 8종 (필수 1건 이상 충족)",
              size=12, bold=True, color=NAVY)
    cw = Inches(2.95); rh = Inches(0.95); gap = Inches(0.1)
    for i, (code, name, desc) in enumerate(seoul_sets):
        col = i % 4
        row = i // 4
        x = Inches(0.6) + col * (cw + gap)
        y = Inches(2.85) + row * (rh + Inches(0.1))
        _add_card(s, x, y, cw, rh, fill=LIGHT, border=BORDER)
        _add_text(s, x + Inches(0.15), y + Inches(0.08), cw - Inches(0.3), Inches(0.25),
                  code, size=8.5, bold=True, color=NAVY, align=PP_ALIGN.LEFT)
        _add_text(s, x + Inches(0.15), y + Inches(0.34), cw - Inches(0.3), Inches(0.3),
                  name, size=11, bold=True, color=INK)
        _add_text(s, x + Inches(0.15), y + Inches(0.62), cw - Inches(0.3), Inches(0.3),
                  desc, size=8.5, color=GRAY)

    _add_text(s, Inches(0.6), Inches(5.0), Inches(12), Inches(0.4),
              "🔗 다른 분야 결합 — 가점 2점 (총 6분야)",
              size=12, bold=True, color=NAVY)
    other = [
        ("국세청", "사업자번호 검증"),
        ("카카오 로컬", "상호 검색 + 반경 경쟁"),
        ("기상청", "단기예보 (강수·온도)"),
        ("OpenAI", "GPT-4o + 임베딩"),
    ]
    cw2 = Inches(2.95)
    for i, (h, body) in enumerate(other):
        x = Inches(0.6) + i * (cw2 + Inches(0.1))
        _add_card(s, x, Inches(5.45), cw2, Inches(0.7), fill=WHITE, border=NAVY, line_w=1)
        _add_text(s, x + Inches(0.15), Inches(5.52), cw2 - Inches(0.3), Inches(0.3),
                  h, size=11, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.15), Inches(5.82), cw2 - Inches(0.3), Inches(0.3),
                  body, size=10, color=INK)

    # 결합 예시
    _add_card(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.65),
              fill=LIGHT, border=AMBER, line_w=1.2)
    _add_text(s, Inches(0.85), Inches(6.4), Inches(11.5), Inches(0.5),
              "결합 예시 — 비 오는 점심 + 직장인구 + 점심 매출 비중 = '오늘 점심 세트 객단가 +3천원' 액션",
              size=11, bold=True, color=INK)

    _footer_source(s,
        "출처: 서울 열린데이터광장 data.seoul.go.kr · 6분야 결합 = 평가표 가점 2점 충족")


def build_differentiation(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 6)
    _section_title(s, "06 · 차별점·독창성",
                   "폐업 매트릭스 결정론 + sme-coach 6업종 분기")

    # 좌: 기존 도구 한계
    _add_text(s, Inches(0.6), Inches(2.4), Inches(6), Inches(0.4),
              "기존 자영업 도구의 한계", size=12, bold=True, color=GRAY)
    limits = [
        "✗ '추천합니다' 톤 — 책임 있는 행동 X",
        "✗ 사장님이 이미 아는 정보 (매출·재고)",
        "✗ 사후적 진단 (폐업 후 보고서)",
        "✗ 일반론 카피 — 50대 시니어 거부",
        "✗ 치킨집·카페에 똑같은 조언",
    ]
    for i, line in enumerate(limits):
        _add_text(s, Inches(0.6), Inches(2.85) + i * Inches(0.32),
                  Inches(6), Inches(0.3), line, size=11, color=INK)

    # 우: 우리 차별점
    _add_text(s, Inches(6.8), Inches(2.4), Inches(6), Inches(0.4),
              "SSGI · 우리만의 차별점", size=12, bold=True, color=NAVY)
    diffs = [
        "✓ 폐업 매트릭스 — 모르는 위험을 사전 알림",
        "✓ 행동 1줄 + cta_type — 즉시 실행",
        "✓ 6업종 분기 — 치킨↔카페↔미용 다른 진단",
        "✓ k≥10 사회적 증거 게이팅",
        "✓ 모든 카드 출처 라벨 + AI 추정 칩",
    ]
    for i, line in enumerate(diffs):
        _add_text(s, Inches(6.8), Inches(2.85) + i * Inches(0.32),
                  Inches(6), Inches(0.3), line, size=11, color=INK)

    # 폐업 매트릭스 5신호 카드
    _add_card(s, Inches(0.6), Inches(4.6), Inches(12.1), Inches(2.3),
              fill=LIGHT, border=LOSS, line_w=1.2)
    _add_text(s, Inches(0.85), Inches(4.75), Inches(11.5), Inches(0.4),
              "🔴 폐업 매트릭스 — 5신호 결정론 룰 (GPT 호출 0회)",
              size=12, bold=True, color=LOSS)

    signals = [
        ("매출 -5%", "VwsmTrdarSelngQq QoQ", "-10점"),
        ("폐업률 5%+", "VwsmTrdarStorQq closing_rate", "-10점"),
        ("정체·축소 상권", "VwsmTrdarIxQq dominant_status", "-20점"),
        ("유동인구 -3%", "SPOP_LOCAL_RESD_DONG", "-20점"),
        ("폐업 평균 70% 도달", "operating_months / closed_avg", "-20점"),
    ]
    sig_w = Inches(2.3)
    for i, (label, src, score) in enumerate(signals):
        x = Inches(0.85) + i * (sig_w + Inches(0.1))
        _add_card(s, x, Inches(5.25), sig_w, Inches(1.4), fill=WHITE, border=BORDER)
        _add_text(s, x + Inches(0.1), Inches(5.35), sig_w - Inches(0.2), Inches(0.35),
                  label, size=11, bold=True, color=INK)
        _add_text(s, x + Inches(0.1), Inches(5.7), sig_w - Inches(0.2), Inches(0.5),
                  src, size=8, color=GRAY)
        _add_text(s, x + Inches(0.1), Inches(6.25), sig_w - Inches(0.2), Inches(0.3),
                  score, size=12, bold=True, color=LOSS)

    _add_text(s, Inches(0.85), Inches(6.7), Inches(11.5), Inches(0.3),
              "→ 100점 차감식 + 4단계 등급(안전·관찰·경고·위험) + 1-액션 매핑",
              size=10, color=NAVY, bold=True)

    _footer_source(s,
        "sme-coach 6업종 분기: 치킨/카페/한식/편의점/의류/미용 — Hero KPI·Top 채널·금지 조언이 다 다름")


def build_demo(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 7)
    _section_title(s, "07 · 5분 시연 흐름",
                   "마포 카페 사장님 P002 데모 + 새 PDF 진단서")

    steps = [
        ("랜딩 → 카카오 1탭", "OAuth state CSRF 보호\n30초 안에 가입"),
        ("온보딩 3단계", "사업자번호 → 가게 → 개점일\n1/3 → 2/3 → 3/3"),
        ("대시보드 첫 진입", "위험도 67/100 (관찰)\n출처 라벨 + 손실 카운터"),
        ("폐업 매트릭스 카드", "결정론 5신호 + 1-액션\nAI 코치만 알 수 있는 손실"),
        ("지원사업 매칭", "SQL target_regions + ICP rerank\nD-day 칩 + 매칭 사유"),
        ("PDF 진단서 다운로드", "표지 + 점수·진단·액션·집중분석\n끊김 없이 한 흐름"),
    ]
    cw = Inches(2.0); gap = Inches(0.05); rh = Inches(1.45)
    for i, (h, body) in enumerate(steps):
        col = i % 6
        x = Inches(0.4) + col * (cw + gap)
        _add_card(s, x, Inches(2.4), cw, rh, fill=WHITE, border=NAVY, line_w=1)
        _add_text(s, x + Inches(0.15), Inches(2.5), cw - Inches(0.3), Inches(0.3),
                  f"STEP {i+1}", size=8, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.15), Inches(2.8), cw - Inches(0.3), Inches(0.45),
                  h, size=11, bold=True, color=INK)
        _add_text(s, x + Inches(0.15), Inches(3.3), cw - Inches(0.3), Inches(0.65),
                  body, size=9, color=GRAY)

    # 새 PDF 진단서 — 큰 카드
    _add_card(s, Inches(0.6), Inches(4.2), Inches(12.1), Inches(1.6),
              fill=LIGHT, border=AMBER, line_w=1.5)
    _add_text(s, Inches(0.85), Inches(4.35), Inches(11.5), Inches(0.4),
              "📄 우리 가게 진단서 PDF — 2026-05 새 레이아웃 (강제 페이지 4개 → 1개)",
              size=12, bold=True, color=INK)
    _add_text(s, Inches(0.85), Inches(4.7), Inches(11.5), Inches(0.35),
              "표지 1장 → 그 뒤로 점수 분포 · 주요 진단 · 액션 플랜 · 집중 분석이 한 흐름으로 이어져요.",
              size=11, color=INK)
    _add_text(s, Inches(0.85), Inches(5.05), Inches(11.5), Inches(0.35),
              "사장님이 \"다음 페이지 어디 있지\" 끊지 않고 한 번에 읽을 수 있어요.",
              size=10.5, color=GRAY)
    _add_text(s, Inches(0.85), Inches(5.4), Inches(11.5), Inches(0.35),
              "차트 옆에는 \"※ 출처: 서울 전체 치킨전문점 평균 (사장님 가게 매출 아님)\" 8pt 라벨 의무.",
              size=10, color=GRAY)

    # 검증
    _add_text(s, Inches(0.6), Inches(5.95), Inches(12), Inches(0.4),
              "검증 (자체 시뮬 — 실 사용자 0명)",
              size=11, bold=True, color=GRAY)
    metrics = [
        ("D0 가입", "88%"), ("D1 푸시 클릭", "60%"),
        ("D7 retention", "55%"), ("D28 retention", "28%"),
    ]
    mw = Inches(2.95)
    for i, (k, v) in enumerate(metrics):
        x = Inches(0.6) + i * (mw + Inches(0.1))
        _add_card(s, x, Inches(6.4), mw, Inches(0.55), fill=WHITE, border=BORDER)
        _add_text(s, x + Inches(0.15), Inches(6.45), mw - Inches(0.3), Inches(0.45),
                  f"{k}  ·  {v}", size=10.5, color=INK)

    _footer_source(s,
        "P002 마포 카페 페르소나 6명 7-day journey 시뮬 · 실 retention은 베타 출시 후 측정 예정")


def build_architecture(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 8)
    _section_title(s, "08 · 시스템 + 데이터 흐름",
                   "Phased Pattern — DB 점유 24초 → 0.25초 (실측)")

    # 좌: 스택
    _add_text(s, Inches(0.6), Inches(2.4), Inches(6), Inches(0.4),
              "기술 스택 (버전 잠금)", size=12, bold=True, color=NAVY)
    stack = [
        ("Frontend", "Next.js 14 · TypeScript · Tailwind · Zustand · PWA · Web Speech"),
        ("Backend", "FastAPI · Python 3.11+ · SQLAlchemy 2 (async) · Pydantic v2"),
        ("Database", "PostgreSQL 15 · ChromaDB 0.5 (PersistentClient)"),
        ("AI", "OpenAI GPT-4o · text-embedding-3-small · APScheduler"),
        ("Auth", "Kakao OAuth · JWT(HS256) · token_version 회전"),
        ("Deploy", "Vercel(FE) · Railway(BE) · Docker Compose(Local)"),
    ]
    for i, (k, v) in enumerate(stack):
        y = Inches(2.85) + i * Inches(0.42)
        _add_text(s, Inches(0.6), y, Inches(1.2), Inches(0.35),
                  k, size=10.5, bold=True, color=NAVY)
        _add_text(s, Inches(1.85), y, Inches(4.7), Inches(0.35),
                  v, size=10, color=INK)

    # 우: Phased Pattern
    _add_text(s, Inches(6.9), Inches(2.4), Inches(6), Inches(0.4),
              "Phased Pattern — DB 세션 조기 해제", size=12, bold=True, color=NAVY)
    _add_card(s, Inches(6.9), Inches(2.85), Inches(5.85), Inches(1.6),
              fill=LIGHT, border=LOSS, line_w=1)
    _add_text(s, Inches(7.05), Inches(2.95), Inches(5.6), Inches(0.3),
              "기존 (단일 세션 점유)", size=10, bold=True, color=LOSS)
    _add_text(s, Inches(7.05), Inches(3.25), Inches(5.6), Inches(1.1),
              "@get('/dashboard') db = Depends(get_db):\n"
              "  sales, ... = await asyncio.gather(...)  # 14 코루틴\n"
              "  → 동시 10명 시 풀 고갈, 24초 hang",
              size=9, color=INK)

    _add_card(s, Inches(6.9), Inches(4.6), Inches(5.85), Inches(1.7),
              fill=LIGHT, border=SUCCESS, line_w=1)
    _add_text(s, Inches(7.05), Inches(4.7), Inches(5.6), Inches(0.3),
              "Phased Pattern (P0 fix 완료)", size=10, bold=True, color=SUCCESS)
    _add_text(s, Inches(7.05), Inches(5.0), Inches(5.6), Inches(1.2),
              "Phase A: async with session: DB 쿼리만\n"
              "Phase B: 외부 API gather (DB 점유 0)\n"
              "Phase A2: async with session: 캐시 저장\n"
              "→ 카카오 콜백 24초 → 0.25초 (라이브 로그 실측)",
              size=9, color=INK)

    # 적용 현황
    _add_text(s, Inches(0.6), Inches(6.3), Inches(12), Inches(0.35),
              "적용 7개 라우트 — /dashboard /insights/competition /insights/marketing /insights/menu-strategy /insights/deep-report /insights/survival-score /onboarding/complete",
              size=9, color=GRAY)
    _add_text(s, Inches(0.6), Inches(6.65), Inches(12), Inches(0.3),
              "✓ alembic 7 마이그레이션 / ✓ 동시 10명 응답 ≤ 5초 / ✓ DB 풀 점유율 ≤ 30%",
              size=10, bold=True, color=NAVY)

    _footer_source(s,
        "31 라우트 · 8 SQLAlchemy 모델 · APScheduler 크론 3개 · k-anonymity·rate limit·JWT 회전")


def build_ui_screens(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 9)
    _section_title(s, "09 · 주요 화면",
                   "대시보드 · 인사이트 · 쿠폰 — 출처 라벨 + AI 추정 칩 일관")

    # 대시보드 — 모의 화면
    _add_card(s, Inches(0.6), Inches(2.4), Inches(4.0), Inches(4.5),
              fill=WHITE, border=BORDER, line_w=1)
    _add_text(s, Inches(0.75), Inches(2.5), Inches(3.7), Inches(0.3),
              "📱 대시보드 (홈)", size=11, bold=True, color=NAVY)
    _add_text(s, Inches(0.75), Inches(2.85), Inches(3.7), Inches(0.3),
              "안녕하세요, 사장님", size=10, color=GRAY)
    _add_text(s, Inches(0.75), Inches(3.15), Inches(3.7), Inches(0.4),
              "마포 한식집 OOO", size=12, bold=True, color=INK)

    _add_card(s, Inches(0.75), Inches(3.65), Inches(3.7), Inches(0.85),
              fill=LIGHT, border=BORDER, line_w=0.5)
    _add_text(s, Inches(0.85), Inches(3.7), Inches(3.5), Inches(0.3),
              "신청 가능 지원금", size=9, color=GRAY)
    _add_text(s, Inches(0.85), Inches(3.95), Inches(3.5), Inches(0.4),
              "247만원", size=18, bold=True, color=LOSS)
    _add_text(s, Inches(0.85), Inches(4.3), Inches(3.5), Inches(0.25),
              "매칭 5건 · D-14 임박 2건", size=8, color=GRAY)

    _add_card(s, Inches(0.75), Inches(4.6), Inches(3.7), Inches(0.85),
              fill=LIGHT, border=BORDER, line_w=0.5)
    _add_text(s, Inches(0.85), Inches(4.65), Inches(3.5), Inches(0.3),
              "경영 위험도 · 관찰", size=9, color=GRAY)
    _add_text(s, Inches(0.85), Inches(4.9), Inches(3.5), Inches(0.4),
              "67 / 100", size=18, bold=True, color=AMBER)
    _add_text(s, Inches(0.85), Inches(5.25), Inches(3.5), Inches(0.25),
              "출처: 서울 열린데이터 · 점수↑ = 위험↑", size=7.5, color=GRAY)

    _add_card(s, Inches(0.75), Inches(5.55), Inches(3.7), Inches(1.25),
              fill=NAVY, border=NAVY)
    _add_text(s, Inches(0.85), Inches(5.6), Inches(3.5), Inches(0.3),
              "오늘의 1줄", size=9, bold=True, color=WHITE)
    _add_text(s, Inches(0.85), Inches(5.85), Inches(3.5), Inches(0.55),
              "단골 카톡 + 재방문 쿠폰 1종 즉시 발행", size=11, bold=True, color=WHITE)
    _add_text(s, Inches(0.85), Inches(6.4), Inches(3.5), Inches(0.35),
              "근거: 매출 -5.4% (서울 VwsmTrdarSelngQq Q3)", size=8, color=WHITE)

    # 인사이트
    _add_card(s, Inches(4.8), Inches(2.4), Inches(4.0), Inches(4.5),
              fill=WHITE, border=BORDER, line_w=1)
    _add_text(s, Inches(4.95), Inches(2.5), Inches(3.7), Inches(0.3),
              "📈 인사이트 (4 탭)", size=11, bold=True, color=NAVY)

    insight_tabs = [
        ("경쟁 분석 탭", "8 Seoul API · 분기 매출 비중", False),
        ("집중 분석 탭", "GPT-4o + RAG · SWOT/TOWS", True),
        ("마케팅 전략 탭", "5-차원 진단 + 채널 우선순위", True),
        ("메뉴 전략 탭", "갭 분석 + 시즌 캘린더 4주", True),
    ]
    for i, (h, body, is_ai) in enumerate(insight_tabs):
        y = Inches(2.9) + i * Inches(0.95)
        _add_card(s, Inches(4.95), y, Inches(3.7), Inches(0.85),
                  fill=LIGHT, border=BORDER, line_w=0.5)
        _add_text(s, Inches(5.05), y + Inches(0.07), Inches(2.5), Inches(0.3),
                  h, size=10, bold=True, color=INK)
        if is_ai:
            _add_amber_chip(s, Inches(7.85), y + Inches(0.1))
        _add_text(s, Inches(5.05), y + Inches(0.4), Inches(3.5), Inches(0.4),
                  body, size=9, color=GRAY)

    # 쿠폰
    _add_card(s, Inches(9.0), Inches(2.4), Inches(3.7), Inches(4.5),
              fill=WHITE, border=BORDER, line_w=1)
    _add_text(s, Inches(9.15), Inches(2.5), Inches(3.4), Inches(0.3),
              "🎟 쿠폰 + 카카오 공유", size=11, bold=True, color=NAVY)

    coupon_items = [
        ("QR 1탭 발행", "Pydantic 검증 · discount_type Literal"),
        ("HMAC 서명 스캔", "settings.secret_key 기반"),
        ("카카오 채널 공유", "FCM token + 알림톡 (ADR-004)"),
        ("스캔 통계 누적", "k≥10일 때만 사회적 증거 노출"),
        ("D-day 임박 강조", "마감 14일 이내 빨간 칩"),
    ]
    for i, (h, body) in enumerate(coupon_items):
        y = Inches(2.95) + i * Inches(0.78)
        _add_text(s, Inches(9.15), y, Inches(3.4), Inches(0.3),
                  f"• {h}", size=10, bold=True, color=INK)
        _add_text(s, Inches(9.35), y + Inches(0.3), Inches(3.2), Inches(0.4),
                  body, size=8.5, color=GRAY)

    _footer_source(s,
        "✓ 모든 카드 출처 라벨 (서울 VwsmTrdarSelngQq · 2024 Q4) · ✓ AI 추정 amber 칩 자동 · ✓ k<10 사회적 증거 비표시")


def build_market(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 10)
    _section_title(s, "10 · 사업화·시장성",
                   "TAM/SAM/SOM bottom-up · 단가 9,900원 가정")

    # TAM/SAM/SOM 깔끔 표
    _add_card(s, Inches(0.6), Inches(2.4), Inches(12.1), Inches(2.6),
              fill=WHITE, border=BORDER, line_w=1)

    rows = [
        ("TAM", "전국 소상공인 (행안부 통계)",
         "약 730만 사장님 × 30% 디지털 수용 × 9,900원 × 12개월",
         "≈ 2,604억원/년", LOSS),
        ("SAM", "서울 사업자등록 소상공인",
         "약 65만 사장님 × 30% × 9,900원 × 12개월 (1차 진입 시장)",
         "≈ 232억원/년", NAVY),
        ("SOM", "3년 목표 (5,000 MAU × 10% Pro 전환)",
         "500 Pro × 9,900원 × 12개월 (실측 갱신 예정)",
         "≈ 5,940만원/년", SUCCESS),
    ]
    for i, (label, who, calc, val, color) in enumerate(rows):
        y = Inches(2.55) + i * Inches(0.83)
        # Label badge
        rect = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.85), y, Inches(0.95), Inches(0.55))
        rect.adjustments[0] = 0.3
        rect.fill.solid(); rect.fill.fore_color.rgb = color
        rect.line.fill.background()
        rect.shadow.inherit = False
        tf = rect.text_frame
        tf.margin_left = tf.margin_right = Emu(0)
        tf.margin_top = tf.margin_bottom = Emu(0)
        _set_text(tf, label, size=14, bold=True, color=WHITE,
                  align=PP_ALIGN.CENTER)

        _add_text(s, Inches(2.0), y, Inches(4.0), Inches(0.3),
                  who, size=11, bold=True, color=INK)
        _add_text(s, Inches(2.0), y + Inches(0.3), Inches(7.5), Inches(0.3),
                  calc, size=9.5, color=GRAY)
        _add_text(s, Inches(10.5), y + Inches(0.05), Inches(2.2), Inches(0.5),
                  val, size=14, bold=True, color=color, align=PP_ALIGN.RIGHT)

    # 경쟁 매트릭스
    _add_text(s, Inches(0.6), Inches(5.15), Inches(12), Inches(0.4),
              "경쟁 매트릭스 — 우리만 가진 것", size=12, bold=True, color=NAVY)

    feats = [
        "손실 프레이밍 — 행동경제학 ADR 적용",
        "공공데이터 8종 결합 — 다른 자영업 도구는 1~3종",
        "RAG 매칭 — SQL+ICP 시간가중 재순위",
        "폐업 사전 경보 — 5신호 결정론 룰",
        "한국 시니어 UX — 정중 톤 분기 + 1393 안내",
        "6업종 분기 — 치킨↔카페 다른 진단",
    ]
    for i, f in enumerate(feats):
        col = i % 2
        row = i // 2
        x = Inches(0.6) + col * Inches(6.05)
        y = Inches(5.65) + row * Inches(0.4)
        _add_text(s, x, y, Inches(0.3), Inches(0.3),
                  "✓", size=12, bold=True, color=SUCCESS)
        _add_text(s, x + Inches(0.3), y, Inches(5.7), Inches(0.3),
                  f, size=10.5, color=INK)

    _footer_source(s,
        "TAM 가정값 — 결제 출시 후 실측 갱신 예정 · SOM은 3년 목표 (코호트 기반 검증)")


def build_business_model(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 11)
    _section_title(s, "11 · 비즈니스 모델",
                   "Free → Pro → Enterprise · LTV/CAC는 베타 출시 후 실측")

    # 3 plan
    plans = [
        ("FREE", "0원", LIGHT, NAVY, [
            "월 3회 쿠폰 발행",
            "주 1회 마케팅 인사이트",
            "기본 폐업 매트릭스",
            "k≥10 사회적 증거",
        ]),
        ("PRO", "9,900원/월", NAVY, WHITE, [
            "월 무제한 쿠폰",
            "실시간 마케팅 인사이트",
            "AI 사업계획서 초안 월 5회",
            "카카오 알림톡 발송",
            "PDF 진단서 무제한",
            "CSV/JSON export",
        ]),
        ("ENT", "협의", LIGHT, LOSS, [
            "프랜차이즈 본사 전용",
            "다점포 통합 대시보드",
            "API 연동 + SLA",
            "전담 매니저",
        ]),
    ]
    cw = Inches(4.0); gap = Inches(0.1)
    for i, (name, price, fill, fg, items) in enumerate(plans):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(2.4), cw, Inches(3.4), fill=fill,
                  border=fg, line_w=1.5)
        _add_text(s, x + Inches(0.25), Inches(2.55), cw - Inches(0.5), Inches(0.4),
                  name, size=14, bold=True, color=fg)
        _add_text(s, x + Inches(0.25), Inches(2.95), cw - Inches(0.5), Inches(0.5),
                  price, size=20, bold=True, color=fg)
        for j, item in enumerate(items):
            _add_text(s, x + Inches(0.3), Inches(3.55) + j * Inches(0.32),
                      cw - Inches(0.5), Inches(0.3),
                      f"• {item}", size=10, color=fg)

    # 베타 인터뷰 (LTV/CAC 환각 대체)
    _add_card(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(0.95),
              fill=LIGHT, border=AMBER, line_w=1.2)
    _add_amber_chip(s, Inches(0.85), Inches(6.1), "가설")
    _add_text(s, Inches(1.65), Inches(6.1), Inches(11), Inches(0.3),
              "베타 인터뷰 N=8 — 가설 검증 단계 (LTV/CAC는 결제 출시 후 코호트로 측정)",
              size=11, bold=True, color=INK)
    _add_text(s, Inches(0.85), Inches(6.45), Inches(11.7), Inches(0.45),
              "8명 중 5명이 9,900원 결제 의향 표명. 평균 \"단골 카톡 자동화\"·\"보조금 푸시\"를 가장 가치 있게 평가.",
              size=10, color=GRAY)

    _footer_source(s,
        "결제 모듈은 2026 Q3 출시 예정 — 그 전 모든 LTV/CAC 수치는 가설 (Year 2 데이터로 검증).")


def build_roadmap(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 12)
    _section_title(s, "12 · 발전 가능성",
                   "1년 로드맵 — Pre-A 5억 → Series A 30억 · 카카오 4분기")

    quarters = [
        ("Q3 2026", "MVP + 결제", [
            "데모데이 통과 (현재 70~80% 자체 추정)",
            "P0 9건 + P1 8건 fix 완료",
            "PortOne/Toss 결제 모듈",
            "골든셋 회귀 (GPT 환각 방지)",
            "PostHog 텔레메트리 (D7/D30)",
        ]),
        ("Q4 2026", "MOU + 1,000 MAU", [
            "서울시·소진공 파일럿 MOU",
            "보조금 시드 22 → 50건 (실데이터)",
            "카카오 알림톡 채널 인증 통과",
            "AC 입주",
        ]),
        ("Q1 2027", "Pre-A + ARR 5,940만", [
            "Pre-A 5억원 투자 유치",
            "5,000 MAU · 500 Pro 전환",
            "다국어 (외국인 사장)",
            "비즈메시지 정식 발송",
        ]),
        ("Q2 2027", "Series A + 5만 가입", [
            "전국 5만곳 누적 가입",
            "프랜차이즈 본사 ENT 3개",
            "ARR 3억원 (Pro + ENT)",
            "Series A 30억원 라운드",
            "AI/ML 엔지니어 5명",
        ]),
    ]
    cw = Inches(2.95); gap = Inches(0.1)
    for i, (q, theme, items) in enumerate(quarters):
        x = Inches(0.6) + i * (cw + gap)
        _add_card(s, x, Inches(2.4), cw, Inches(3.6), fill=WHITE,
                  border=NAVY, line_w=1)
        _add_text(s, x + Inches(0.2), Inches(2.5), cw - Inches(0.4), Inches(0.35),
                  q, size=11, bold=True, color=NAVY)
        _add_text(s, x + Inches(0.2), Inches(2.85), cw - Inches(0.4), Inches(0.4),
                  theme, size=12, bold=True, color=INK)
        for j, item in enumerate(items):
            _add_text(s, x + Inches(0.2), Inches(3.3) + j * Inches(0.45),
                      cw - Inches(0.4), Inches(0.4),
                      f"• {item}", size=9.5, color=INK)

    # 카카오 시너지 — 4분기 명시
    _add_card(s, Inches(0.6), Inches(6.15), Inches(12.1), Inches(0.85),
              fill=LIGHT, border=NAVY, line_w=1.2)
    _add_text(s, Inches(0.85), Inches(6.25), Inches(11.5), Inches(0.3),
              "🎁 카카오 4분기 마일스톤 — 카카오벤처스 CVC 합격 조건",
              size=11, bold=True, color=NAVY)
    _add_text(s, Inches(0.85), Inches(6.55), Inches(11.5), Inches(0.4),
              "Q1 카카오싱크 인증 신청 → Q2 알림톡 채널 검수 → Q3 비즈메시지 일일 액션 → Q4 카카오페이 정기결제 + 카카오맵 양방향",
              size=10, color=INK)

    _footer_source(s,
        "Series A 합격 기준: ARR 3억+ · LTV/CAC 3+ · D30 25%+ · 코호트 6개월 retention 데이터")


def build_esg(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _header(s, 13)
    _section_title(s, "13 · ESG 정량화",
                   "환경 tCO2eq + 사회 폐업방지 23~49명/년 + 거버넌스 ADR 6건")

    # E
    _add_text(s, Inches(0.6), Inches(2.4), Inches(4.1), Inches(0.4),
              "ENVIRONMENT (정량)", size=11, bold=True, color=SUCCESS)
    _add_card(s, Inches(0.6), Inches(2.8), Inches(4.1), Inches(3.6),
              fill=LIGHT, border=SUCCESS, line_w=1)
    e_items = [
        ("페이퍼리스 보조금 신청", "1만 명 × 12장 × 연 3회", "≈ 14.4 tCO2eq/년"),
        ("POP·전단지 → QR 전환", "가게당 50장/월 × 12 × 1만", "≈ 240 tCO2eq/년"),
        ("행정복지센터 이동 절감", "1.2km × 3회 × 1만 명", "≈ 7.6 tCO2eq/년"),
        ("PWA 캐싱 + 주간 GPT 캐시", "트래픽·연산 절약", "베타에서 정량화"),
    ]
    for i, (h, calc, val) in enumerate(e_items):
        y = Inches(2.95) + i * Inches(0.85)
        _add_text(s, Inches(0.75), y, Inches(3.85), Inches(0.3),
                  h, size=10, bold=True, color=INK)
        _add_text(s, Inches(0.75), y + Inches(0.3), Inches(3.85), Inches(0.3),
                  calc, size=8.5, color=GRAY)
        _add_text(s, Inches(0.75), y + Inches(0.55), Inches(3.85), Inches(0.3),
                  val, size=10, bold=True, color=SUCCESS)

    # S
    _add_text(s, Inches(4.85), Inches(2.4), Inches(4.1), Inches(0.4),
              "SOCIAL (정량 추정)", size=11, bold=True, color=LOSS)
    _add_card(s, Inches(4.85), Inches(2.8), Inches(4.1), Inches(3.6),
              fill=LIGHT, border=LOSS, line_w=1)
    _add_text(s, Inches(5.0), Inches(2.95), Inches(3.85), Inches(0.4),
              "폐업 방지 추정", size=11, bold=True, color=INK)
    _add_text(s, Inches(5.0), Inches(3.35), Inches(3.85), Inches(0.45),
              "활성 2,500명 × 손실프레이밍 효과 7~15%p", size=9.5, color=GRAY)
    _add_text(s, Inches(5.0), Inches(3.8), Inches(3.85), Inches(0.55),
              "≈ 연 23~49명", size=20, bold=True, color=LOSS)
    _add_text(s, Inches(5.0), Inches(4.4), Inches(3.85), Inches(0.7),
              "근거: 서울 자영업 폐업률 13.2% × Tversky-Kahneman 손실회피 메타분석 1.5~2.5배",
              size=8.5, color=GRAY)
    _add_text(s, Inches(5.0), Inches(5.15), Inches(3.85), Inches(0.3),
              "+ 정보 비대칭 해소 — 시니어 보조금 접근",
              size=9.5, color=INK)
    _add_text(s, Inches(5.0), Inches(5.5), Inches(3.85), Inches(0.3),
              "+ 자살예방 1393 분기별 안내 의무화",
              size=9.5, color=INK)
    _add_text(s, Inches(5.0), Inches(5.85), Inches(3.85), Inches(0.4),
              "+ 시니어 UX (text 14px+ · 정중 톤 분기)",
              size=9.5, color=INK)

    # G
    _add_text(s, Inches(9.1), Inches(2.4), Inches(3.6), Inches(0.4),
              "GOVERNANCE", size=11, bold=True, color=NAVY)
    _add_card(s, Inches(9.1), Inches(2.8), Inches(3.6), Inches(3.6),
              fill=LIGHT, border=NAVY, line_w=1)
    g_items = [
        "ADR 6건 명시 (손실프레이밍·k=10 등)",
        "QA 라운드 3회 + 5-패널 다중 검토",
        "데이터 출처 라벨 의무 (모든 화면)",
        "AI 추정 자동 amber 칩 (_disclosure)",
        "오픈소스 의존성 SBOM 관리",
        "data_scope fallback 라벨 (오늘 추가)",
    ]
    for i, item in enumerate(g_items):
        _add_text(s, Inches(9.25), Inches(2.95) + i * Inches(0.55),
                  Inches(3.35), Inches(0.45),
                  f"✓ {item}", size=9.5, color=INK)

    # 한 줄 요약
    _add_card(s, Inches(0.6), Inches(6.55), Inches(12.1), Inches(0.5),
              fill=NAVY, border=NAVY)
    _add_text(s, Inches(0.85), Inches(6.6), Inches(11.5), Inches(0.4),
              "환경 ≈ 262 tCO2eq/년 절감 · 사회 23~49명 폐업 방지 · 거버넌스 정직성 6 ADR",
              size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    _footer_source(s,
        "tCO2eq 환산: 종이 1톤 = 약 8 tCO2eq · 차량 0.21 kgCO2/km 기준 · 폐업 방지는 메타분석 기반 추정")


def build_closing(prs):
    """마지막은 점수가 아니라 정성 클로징."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    # 배경 색
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    bg.shadow.inherit = False

    _add_text(s, Inches(0.6), Inches(0.5), Inches(12), Inches(0.3),
              "P. 14 / 14", size=10, color=WHITE, align=PP_ALIGN.RIGHT)

    _add_text(s, Inches(0.6), Inches(2.0), Inches(12), Inches(0.6),
              "사장님이",
              size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _add_text(s, Inches(0.6), Inches(2.7), Inches(12), Inches(0.6),
              "매일 받는",
              size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    _add_text(s, Inches(0.6), Inches(3.4), Inches(12), Inches(0.7),
              "1줄 처방.",
              size=56, bold=True, color=AMBER, align=PP_ALIGN.CENTER)

    _add_text(s, Inches(0.6), Inches(4.6), Inches(12), Inches(0.4),
              "\"추천합니다\"가 아니라 \"놓치고 있어요\".",
              size=14, color=WHITE, align=PP_ALIGN.CENTER)

    _add_text(s, Inches(1.5), Inches(5.4), Inches(10.3), Inches(0.5),
              "한 명의 사장님이라도 폐업의 절벽에서 한 발 물러서게 한다면,",
              size=14, color=WHITE, align=PP_ALIGN.CENTER)
    _add_text(s, Inches(1.5), Inches(5.85), Inches(10.3), Inches(0.5),
              "이 시스템은 그 한 가지로 충분해요.",
              size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    _add_text(s, Inches(0.6), Inches(6.85), Inches(12), Inches(0.3),
              "팀 SSGI · 정수현 · 구혁모 · 나은민 · 이준수 · 2026",
              size=10, color=WHITE, align=PP_ALIGN.CENTER)


# ===== 백업 슬라이드 (Q&A에서만 호출) =====

def build_backup_self_eval(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text(s, Inches(0.6), Inches(0.3), Inches(12), Inches(0.3),
              "백업 · Q&A 전용", size=9, bold=True, color=AMBER)
    _add_text(s, Inches(11.0), Inches(0.3), Inches(1.8), Inches(0.3),
              "BACKUP 1 / 4", size=9, bold=True, color=GRAY,
              align=PP_ALIGN.RIGHT)
    line = s.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                   Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER; line.line.width = Pt(0.5)

    _section_title(s, "BACKUP A · 자체 채점",
                   "73.5 / 100 (현재) → 86.5 / 100 (시급 5건 fix 적용 시)",
                   "외부 평가 X · 셀프 채점 · 실 응모 결과는 별도")

    # 진행 막대
    _add_card(s, Inches(0.6), Inches(2.6), Inches(12.1), Inches(2.0),
              fill=LIGHT, border=BORDER)
    _add_text(s, Inches(0.85), Inches(2.75), Inches(11.5), Inches(0.35),
              "현재 점수 (자체 시뮬, 외부 평가 X)", size=11, color=GRAY)

    # current bar
    cur_w = int(12.1 * 73.5 / 100 * 914400)  # EMU
    cur_bar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.85), Inches(3.15),
                                  Emu(cur_w), Inches(0.5))
    cur_bar.adjustments[0] = 0.3
    cur_bar.fill.solid(); cur_bar.fill.fore_color.rgb = AMBER
    cur_bar.line.fill.background()
    cur_bar.shadow.inherit = False
    _add_text(s, Inches(0.95), Inches(3.2), Inches(2), Inches(0.4),
              "73.5 / 100", size=14, bold=True, color=WHITE)

    _add_text(s, Inches(0.85), Inches(3.85), Inches(11.5), Inches(0.35),
              "시급 5건 정정 + 9건 P0 코드 fix 적용 시 (자체 추정)",
              size=11, color=GRAY)
    tgt_w = int(12.1 * 86.5 / 100 * 914400)
    tgt_bar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  Inches(0.85), Inches(4.25),
                                  Emu(tgt_w), Inches(0.5))
    tgt_bar.adjustments[0] = 0.3
    tgt_bar.fill.solid(); tgt_bar.fill.fore_color.rgb = SUCCESS
    tgt_bar.line.fill.background()
    tgt_bar.shadow.inherit = False
    _add_text(s, Inches(0.95), Inches(4.3), Inches(2), Inches(0.4),
              "86.5 / 100", size=14, bold=True, color=WHITE)

    # 통과 확률
    _add_text(s, Inches(0.6), Inches(4.95), Inches(12), Inches(0.4),
              "통과 확률 시나리오 (자체 추정)", size=12, bold=True, color=NAVY)
    sc = [
        ("현재 PPT 그대로", "30~40%", AMBER),
        ("시급 5건 정정", "50~60%", AMBER),
        ("시급 5건 + HIGH 7건", "65~75%", SUCCESS),
        ("9건 P0 코드 + 정정 적용 (현재 위치)", "75~85%", SUCCESS),
    ]
    for i, (k, v, c) in enumerate(sc):
        y = Inches(5.5) + i * Inches(0.42)
        _add_text(s, Inches(0.85), y, Inches(8), Inches(0.3),
                  k, size=11, color=INK)
        _add_text(s, Inches(9.5), y, Inches(3), Inches(0.3),
                  v, size=12, bold=True, color=c, align=PP_ALIGN.RIGHT)


def build_backup_references(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text(s, Inches(0.6), Inches(0.3), Inches(12), Inches(0.3),
              "백업 · Q&A 전용", size=9, bold=True, color=AMBER)
    _add_text(s, Inches(11.0), Inches(0.3), Inches(1.8), Inches(0.3),
              "BACKUP 2 / 4", size=9, bold=True, color=GRAY,
              align=PP_ALIGN.RIGHT)
    line = s.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                   Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER; line.line.width = Pt(0.5)

    _section_title(s, "BACKUP B · 학술 인용",
                   "검증 가능한 출처만 — Lewis/Beck 환각 제거 후 정정")

    refs = [
        ("ADR 001 · 손실 프레이밍",
         "Kahneman, D. & Tversky, A. (1979). Prospect Theory: An Analysis of Decision under Risk. Econometrica 47(2)."),
        ("프레이밍 효과 보강",
         "Tversky, A. & Kahneman, D. (1981). The Framing of Decisions and the Psychology of Choice. Science 211."),
        ("ADR 002 · k-anonymity",
         "Sweeney, L. (2002). k-Anonymity: A Model for Protecting Privacy. Int. J. Uncertainty Fuzziness Knowl.-Based Syst. 10(5)."),
        ("사회적 증거 원리",
         "Cialdini, R. B. (2006). Influence: The Psychology of Persuasion. (개정판)"),
        ("실측 통계 4.5년 / 9.8년 / 53.7%",
         "서울 열린데이터광장 (2025). VwsmTrdarIxQq 상권변화지수 2025 4분기 · 추출 2026-04."),
    ]
    for i, (k, v) in enumerate(refs):
        y = Inches(2.4) + i * Inches(0.85)
        _add_card(s, Inches(0.6), y, Inches(12.1), Inches(0.75),
                  fill=LIGHT, border=BORDER)
        _add_text(s, Inches(0.85), y + Inches(0.08), Inches(11.5), Inches(0.3),
                  k, size=10, bold=True, color=NAVY)
        _add_text(s, Inches(0.85), y + Inches(0.38), Inches(11.5), Inches(0.35),
                  v, size=9.5, color=INK)


def build_backup_codefixes(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text(s, Inches(0.6), Inches(0.3), Inches(12), Inches(0.3),
              "백업 · Q&A 전용", size=9, bold=True, color=AMBER)
    _add_text(s, Inches(11.0), Inches(0.3), Inches(1.8), Inches(0.3),
              "BACKUP 3 / 4", size=9, bold=True, color=GRAY,
              align=PP_ALIGN.RIGHT)
    line = s.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                   Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER; line.line.width = Pt(0.5)

    _section_title(s, "BACKUP C · 2026-05-10 코드 정정",
                   "sme-coach 6업종 분기 + 치킨 매핑 + fallback 라벨 + PDF 흐름")

    fixes = [
        ("치킨→치킨전문점 매핑 fix",
         "BUSINESS_TYPE_MAP에서 \"치킨\":\"한식음식점\" → \"치킨전문점\". "
         "분식·햄버거·피자·베이커리·편의점·슈퍼·일식 별도 분리.",
         "seoul_api_service.py:62-95"),
        ("data_scope fallback 라벨",
         "1차 매칭 실패 시 \"동 전체 평균\" / \"서울 전체 평균\" "
         "라벨 자동 부착. 차트·PDF·GPT 프롬프트에 노출.",
         "seoul_api_service.py:641 + report_generator.py:780 + insights/page.tsx:401"),
        ("PDF 강제 페이지 분리 4 → 1",
         "표지만 PageBreak 유지. 점수·진단·액션·집중분석을 한 흐름으로 "
         "이어붙임. ReportLab이 자연 페이지 분할.",
         "report_generator.py:540~651"),
        ("sme-coach 9개 GPT 프롬프트 적용",
         "industry_prompt_block() 헬퍼로 6업종 KPI/채널/위험 신호/금지 조언을 "
         "모든 GPT 시스템 프롬프트에 임베드.",
         "utils/industry.py + 9개 prompt 적용"),
        ("화면 출처 라벨",
         "차트 위에 ⚠️ \"사장님 가게 매출 아님 — 상권 평균 데이터\" "
         "8pt 라벨 추가. fallback일 때 amber 배경 박스.",
         "frontend/insights/page.tsx + report_generator.py"),
    ]
    for i, (k, v, src) in enumerate(fixes):
        y = Inches(2.4) + i * Inches(0.95)
        _add_card(s, Inches(0.6), y, Inches(12.1), Inches(0.85),
                  fill=LIGHT, border=SUCCESS, line_w=1)
        _add_text(s, Inches(0.85), y + Inches(0.08), Inches(11.5), Inches(0.3),
                  k, size=11, bold=True, color=SUCCESS)
        _add_text(s, Inches(0.85), y + Inches(0.36), Inches(11.5), Inches(0.3),
                  v, size=9.5, color=INK)
        _add_text(s, Inches(0.85), y + Inches(0.62), Inches(11.5), Inches(0.25),
                  f"📍 {src}", size=8, color=GRAY)


def build_backup_qa(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _add_text(s, Inches(0.6), Inches(0.3), Inches(12), Inches(0.3),
              "백업 · Q&A 전용", size=9, bold=True, color=AMBER)
    _add_text(s, Inches(11.0), Inches(0.3), Inches(1.8), Inches(0.3),
              "BACKUP 4 / 4", size=9, bold=True, color=GRAY,
              align=PP_ALIGN.RIGHT)
    line = s.shapes.add_connector(1, Inches(0.6), Inches(0.65),
                                   Inches(12.7), Inches(0.65))
    line.line.color.rgb = BORDER; line.line.width = Pt(0.5)

    _section_title(s, "BACKUP D · 까다로운 질문 Top 10",
                   "패널 검토에서 예상된 질문 + 한 줄 답변 준비")

    qa = [
        "Q1. LTV/CAC 분모 churn은? · A. 결제 모듈 미출시 — 베타 출시 후 코호트로 측정 (가설 표기)",
        "Q2. fit_score 산출 공식? · A. GPT 자유 추정값. _disclosure 메타로 amber 라벨링.",
        "Q3. ESG-E 페이퍼리스 환산식? · A. 1만 × 12장 × 3회 = 36만장 ≈ 1.8t 종이 ≈ 14.4 tCO2eq",
        "Q4. 폐업 4.5년 vs KOSIS 3.1년 차이? · A. 모집단 정의 — 서울 한정 + 폐업 한정 (KOSIS는 전국 자영업)",
        "Q5. 1년 폐업 방지 N명? · A. 활성 2,500 × 7~15%p × 13.2% ≈ 23~49명 (Tversky-Kahneman 메타 1.5~2.5x)",
        "Q6. 카카오 알림톡 인증 단계? · A. Q1 카카오싱크 → Q2 채널 검수 → Q3 비즈메시지 → Q4 페이/맵",
        "Q7. P020 사장님 실 인터뷰? · A. 시뮬 페르소나 (8축 매트릭스). 실 인터뷰는 베타 출시 후.",
        "Q8. 결제한 사장님 1명? · A. 결제 모듈 미출시 — 베타 N=8 인터뷰에서 5/8 결제 의향 확인.",
        "Q9. RAG = ChromaDB? · A. 보조금은 SQL+ICP active. ChromaDB는 음성 + 인덱싱 완료. 매칭 활성 Q3.",
        "Q10. data_scope fallback 라벨 왜? · A. 사장님 가게 ≠ 상권 평균 명시 — 정직성 원칙.",
    ]
    for i, line in enumerate(qa):
        _add_text(s, Inches(0.6), Inches(2.4) + i * Inches(0.42),
                  Inches(12.1), Inches(0.4),
                  line, size=10, color=INK)


# ===== 메인 =====

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # 본문 14장
    build_cover(prs)
    build_toc(prs)
    build_background(prs)
    build_persona_story(prs)
    build_persona_matrix(prs)
    build_overview(prs)
    build_data_sources(prs)
    build_differentiation(prs)
    build_demo(prs)
    build_architecture(prs)
    build_ui_screens(prs)
    build_market(prs)
    build_business_model(prs)
    build_roadmap(prs)
    build_esg(prs)
    build_closing(prs)

    # 백업 4장 (Q&A)
    build_backup_self_eval(prs)
    build_backup_references(prs)
    build_backup_codefixes(prs)
    build_backup_qa(prs)

    out = Path(__file__).resolve().parent.parent / "SSGI_AI_경영코치_상세기획서.pptx"
    prs.save(str(out))
    print(f"✓ Saved: {out} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
