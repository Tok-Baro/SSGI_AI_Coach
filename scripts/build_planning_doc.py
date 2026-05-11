"""SSGI AI 경영코치 — 상세기획서 덱 (Manus 디자인 시스템 적용 · Option A 구성).

디자인 토큰 출처: 팀이 Manus 로 만든 19장 HTML 덱 (01-cover.html … 19-backup-anonymity.html).
  · 배경 #F7F8FB · 잉크 #0B1A33 · 슬레이트 #4A5878 · 뮤트 #8A95AE
  · 액센트 블루 #0F4C92 / #1B6FD0 · 하이라이트 박스 #E8F0FA · 손실 레드 #B3261E
  · 라인 #DDE2EC · 카드 흰색 + 1px 라인, 그림자 0
  · 폰트 Pretendard · 캔버스 1920×1080 (= 13.333"×7.5", 1px = 1/144 inch)
  · 표지: 좌측 네이비 사이드바 / 콘텐츠: 좌상 eyebrow + 우상 평가 배지 + 56px 타이틀 + 푸터 라인

평가표(제품·서비스 100점+2): 앱 60(공공·AI 20 / 화면 구동 20 / UI·UX 20) + 상세기획서 40(배경·취지 10 / 기능 상세 30).
→ 무게중심: 개발 배경·취지 + 구현 기능 상세 설명. IR 슬라이드(시장/로드맵/팀)는 백업 1장.

실행: python scripts/build_planning_doc.py   →   SSGI_상세기획서_심사위원용.pptx
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ============================================================
# 디자인 토큰
# ============================================================
def C(hexstr: str) -> RGBColor:
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


BG       = C("F7F8FB")   # 슬라이드 배경
INK      = C("0B1A33")   # 헤드라인 · 큰 숫자
INK2     = C("1F2A44")   # 본문 강조 · 항목명
SLATE    = C("4A5878")   # 본문
MUTE     = C("8A95AE")   # 라벨 · 푸터 · 캡션
LINE     = C("DDE2EC")   # 디바이더 · 카드 보더
BLUE     = C("0F4C92")   # 메인 액센트
BLUE2    = C("1B6FD0")   # 배지 · 디바이더
BLUEBG   = C("E8F0FA")   # 하이라이트 박스
GREYBG   = C("F1F3F8")   # 연한 칩 배경
WHITE    = C("FFFFFF")
RED      = C("B3261E")   # 손실 · 긴급
AMBER    = C("8B6B1F")   # 추정 (어두운 골드)
AMBERBG  = C("FBF3E0")
GREEN    = C("1E6E4A")   # 데이터 출처 (차분한 그린)
NAVYFRAME = C("0B1A33")  # 폰 프레임

FONT = "Pretendard Variable"   # 시스템에 설치돼 있음 (없으면 PPT 가 폴백)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
PXIN = 1.0 / 144.0   # 1px = 1/144 inch (1920px → 13.333", 1080px → 7.5")


def PX(px: float) -> Inches:
    return Inches(px * PXIN)


# ============================================================
# 저수준 헬퍼
# ============================================================
def _txt(slide, x, y, w, h, runs, *, size, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, line_spacing=1.2, spacing_em=0.0):
    """runs: str 또는 [(text, {color,bold,size}), ...]."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Emu(0))
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    if isinstance(runs, str):
        runs = [(runs, {})]
    for text, opt in runs:
        r = p.add_run()
        r.text = text
        r.font.name = FONT
        r.font.size = Pt(opt.get("size", size))
        r.font.bold = opt.get("bold", bold)
        r.font.color.rgb = opt.get("color", color)
    return box


def _rect(slide, x, y, w, h, *, fill=WHITE, line=None, line_w=1.0, radius=None):
    shp = MSO_SHAPE.ROUNDED_RECTANGLE if radius is not None else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shp, x, y, w, h)
    if radius is not None:
        try:
            sh.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    return sh


def _hline(slide, x, y, w, *, color=LINE, weight=1.0):
    ln = slide.shapes.add_connector(1, x, y, x + w, y)
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    ln.shadow.inherit = False
    return ln


def bg(slide):
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=BG)


# ============================================================
# 컴포넌트
# ============================================================
def eyebrow(slide, text):
    _txt(slide, PX(96), PX(72), PX(1000), PX(32), text.upper() if text.isascii() else text,
         size=11, bold=True, color=MUTE)


def rubric_badge(slide, label):
    """우상단 블루 배지 (흰 글씨) — 평가표 매칭."""
    w = PX(84 + 38 * len(label))
    x = SLIDE_W - PX(96) - w
    _rect(slide, x, PX(68), w, PX(44), fill=BLUE2, radius=0.18)
    _txt(slide, x, PX(68), w, PX(44), label, size=10, bold=True, color=WHITE,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def section_title(slide, parts, *, y=128, w=1500, size=28):
    """parts: str 또는 [(text, accent?), ...] — accent True 면 BLUE."""
    if isinstance(parts, str):
        parts = [(parts, False)]
    runs = [(t, {"color": BLUE if acc else INK}) for t, acc in parts]
    _txt(slide, PX(96), PX(y), PX(w), PX(120), runs, size=size, bold=True, color=INK, line_spacing=1.18)


def subtitle(slide, text, *, y=226, w=1500, size=13):
    _txt(slide, PX(96), PX(y), PX(w), PX(60), text, size=size, color=SLATE, line_spacing=1.4)


def footer(slide, page_no, source=""):
    _hline(slide, PX(96), PX(1018), PX(1728), color=LINE, weight=1.0)
    _txt(slide, PX(96), PX(1030), PX(1300), PX(32), source, size=9.5, color=MUTE, line_spacing=1.25)
    label = f"팀 SSGI  ·  {page_no} / 20" if isinstance(page_no, int) else f"팀 SSGI  ·  {page_no}"
    _txt(slide, PX(1424), PX(1030), PX(400), PX(32), label, size=10, color=MUTE, align=PP_ALIGN.RIGHT)


def card(slide, x_px, y_px, w_px, h_px, title, body, *, accent=BLUE, body_size=12.5,
         title_size=15, num=None, title_color=INK):
    """흰 카드 + 1px 라인. accent 좌측 스트라이프(또는 num 큰 숫자)."""
    _rect(slide, PX(x_px), PX(y_px), PX(w_px), PX(h_px), fill=WHITE, line=LINE, line_w=1.0, radius=0.045)
    tx = x_px + 32
    if num is not None:
        _txt(slide, PX(x_px + 26), PX(y_px + 16), PX(86), PX(72), num, size=32, bold=True, color=accent)
        tx = x_px + 26 + 92
    else:
        _rect(slide, PX(x_px), PX(y_px + 14), PX(6), PX(h_px - 28), fill=accent)
    tw = w_px - (tx - x_px) - 26
    _txt(slide, PX(tx), PX(y_px + 16), PX(tw), PX(42), title, size=title_size, bold=True, color=title_color)
    if body:
        _txt(slide, PX(tx), PX(y_px + 60), PX(tw), PX(h_px - 76), body, size=body_size, color=SLATE,
             line_spacing=1.32)


def numrow(slide, x_px, y_px, w_px, h_px, num, head_runs, body):
    """5번 슬라이드의 '01 ... 설명' 패턴 — 흰 카드 + 큰 번호 + 헤드 + 설명."""
    _rect(slide, PX(x_px), PX(y_px), PX(w_px), PX(h_px), fill=WHITE, line=LINE, line_w=1.0, radius=0.045)
    _txt(slide, PX(x_px + 28), PX(y_px + 18), PX(90), PX(h_px - 24), num, size=26, bold=True, color=BLUE,
         anchor=MSO_ANCHOR.MIDDLE)
    cx = x_px + 130
    cw = w_px - 130 - 28
    if isinstance(head_runs, str):
        head_runs = [(head_runs, {})]
    _txt(slide, PX(cx), PX(y_px + 22), PX(cw), PX(38), head_runs, size=13, bold=True, color=INK)
    _txt(slide, PX(cx), PX(y_px + 60), PX(cw), PX(h_px - 72), body, size=9, color=SLATE, line_spacing=1.35)


def bignum(slide, x_px, y_px, w_px, label, number, unit, caption, *, color=INK):
    _txt(slide, PX(x_px), PX(y_px), PX(w_px), PX(28), label, size=11, bold=True, color=MUTE)
    runs = [(number, {"size": 46, "bold": True, "color": color})]
    if unit:
        runs.append((" " + unit, {"size": 17, "bold": True, "color": SLATE}))
    _txt(slide, PX(x_px), PX(y_px + 32), PX(w_px), PX(84), runs, size=46, bold=True, color=color, line_spacing=1.05)
    _txt(slide, PX(x_px), PX(y_px + 122), PX(w_px), PX(44), caption, size=11.5, color=SLATE, line_spacing=1.3)


PHONE_RATIO = 1179 / 2556


def phone(slide, img_path, *, cx_px, top_px, h_px):
    """화면 캡처를 네이비 둥근 프레임 안에 배치. cx_px = 가로 중심."""
    w_px = h_px * PHONE_RATIO
    x_px = cx_px - w_px / 2
    pad = 7
    _rect(slide, PX(x_px - pad), PX(top_px - pad), PX(w_px + 2 * pad), PX(h_px + 2 * pad),
          fill=NAVYFRAME, radius=0.07)
    slide.shapes.add_picture(str(img_path), PX(x_px), PX(top_px), width=PX(w_px), height=PX(h_px))


def chip(slide, x_px, y_px, label, *, fg=BLUE, bg_=BLUEBG):
    w = PX(56 + 28 * len(label))
    _rect(slide, PX(x_px), PX(y_px), w, PX(30), fill=bg_, radius=0.3)
    _txt(slide, PX(x_px), PX(y_px), w, PX(30), label, size=9, bold=True, color=fg,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return float(w) / 914400.0 * 144  # px


# ============================================================
# 슬라이드 빌더
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
SHOTS = {
    "01": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-58 001.png",  # 홈 — 위험도·오늘의 액션·매칭 지원금
    "02": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-59 002.png",  # 홈 — 매칭 지원사업 3건
    "03": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-59 003.png",  # 홈 — 서울 문화행사 · PREMIUM PDF
    "04": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-59 004.png",  # 지원사업 탭 — 최대 31,400만원
    "05": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-59 005.png",  # 인사이트>경쟁 — 데이터 출처 명시
    "07": ROOT / "KakaoTalk_Photo_2026-05-11-16-36-59 007.png",  # 인사이트>마케팅 — 진단 진입
    "08": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-00 008.png",  # 인사이트>집중분석 — 이번 주 1가지 · PREMIUM
    "09": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-00 009.png",  # 인사이트>집중분석 — 강점/약점·우리 가게 자리
    "10": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-00 010.png",  # 인사이트>마케팅 — 예산별 시나리오 0/5만
    "11": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-00 011.png",  # 인사이트>마케팅 — 채널 우선순위·ROI·객단가
    "12": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-00 012.png",  # 인사이트>마케팅 — 카피 3종(신뢰·친근·긴급)
    "13": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-01 013.png",  # 인사이트>마케팅 — 지원금 활용 카피·화요일 이벤트
    "14": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-01 014.png",  # 인사이트>메뉴 — 메뉴 전략(갭+시즌+차별화)
    "15": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-01 015.png",  # 인사이트>메뉴 — 갭 분석(음악·코딩·창의융합)
    "16": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-01 016.png",  # 인사이트>메뉴 — 시즌 캘린더 4주
    "17": ROOT / "KakaoTalk_Photo_2026-05-11-16-37-01 017.png",  # 인사이트>메뉴 — 차별화 한 수
    # 2026-05-11 19:43 추가분 — 음성·PDF·사업계획서·결제
    "voice":   ROOT / "KakaoTalk_Photo_2026-05-11-19-43-46.png",      # 홈 — AI 음성 질문("마케팅") 처리 중 + 받을 수 있는 지원금
    "pdf":     ROOT / "KakaoTalk_Photo_2026-05-11-19-43-37 002.png",  # PREMIUM PDF 진단서 — 67점·등급 C·카테고리별 평가
    "bizplan": ROOT / "KakaoTalk_Photo_2026-05-11-19-43-37 001.png",  # 지원사업 상세 — AI 사업계획서 초안(빈칸 자동 채움·절약 약 2시간)
    "paywall": ROOT / "KakaoTalk_Photo_2026-05-11-19-43-11.png",      # 인사이트>메뉴 — Pro 전용 페이월
    "pay_up":  ROOT / "KakaoTalk_Photo_2026-05-11-19-43-15.png",      # SSGI Pro 업그레이드 — 페이월 카피·혜택 5종·9,900원
    "pay_done": ROOT / "KakaoTalk_Photo_2026-05-11-19-43-19.png",     # 결제 완료 — SSGI Pro 1개월(테스트)·만료일 표시
}


def newslide(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg(s)
    return s


def content_head(slide, eyebrow_text, title_parts, sub_text, rubric=None, *, title_w=1500, title_size=28):
    eyebrow(slide, eyebrow_text)
    if rubric:
        rubric_badge(slide, rubric)
    section_title(slide, title_parts, w=title_w, size=title_size)
    if sub_text:
        subtitle(slide, sub_text, y=228, w=min(title_w, 1480))


# -------------------- 기능 상세 슬라이드 --------------------
def feature_slide(prs, page, eb, title_parts, sub_text, *, what, data, ai, flow,
                  shots, caption, source):
    s = newslide(prs)
    eyebrow(s, eb)
    rubric_badge(s, "기능 상세 30")
    n = len(shots)
    # 스크린샷이 3장이면 우측 영역을 넓히고(좌 884px), 1~2장이면 좌 1044px.
    if n >= 3:
        left_w = 884
        right_x, right_w = 1020, 804
        cw = (left_w - 30) // 2  # 427
    else:
        left_w = 1044
        right_x, right_w = 1180, 644
        cw = 507
    section_title(s, title_parts, y=126, w=left_w, size=26)
    _txt(s, PX(96), PX(280), PX(left_w), PX(66), sub_text, size=12.5, color=SLATE, line_spacing=1.32)
    # 2×2 카드
    cards = [
        ("무엇을", what, INK),
        ("어떤 서울 데이터", data, GREEN),
        ("어떤 AI", ai, BLUE),
        ("동작 흐름", flow, BLUE2),
    ]
    chh, gx, gy = 318, 30, 24
    x0, y0 = 96, 358
    for i, (t, b, ac) in enumerate(cards):
        x = x0 + (i % 2) * (cw + gx)
        y = y0 + (i // 2) * (chh + gy)
        card(s, x, y, cw, chh, t, b, accent=ac, body_size=12, title_size=14.5)
    # 우측 스크린샷
    if n == 1:
        phone(s, SHOTS[shots[0]], cx_px=right_x + right_w / 2, top_px=270, h_px=700)
    elif n == 2:
        h = 600
        w = h * PHONE_RATIO
        gap = 30
        total = w * 2 + gap
        x0p = right_x + (right_w - total) / 2
        phone(s, SHOTS[shots[0]], cx_px=x0p + w / 2, top_px=280, h_px=h)
        phone(s, SHOTS[shots[1]], cx_px=x0p + w + gap + w / 2, top_px=280, h_px=h)
    else:  # 3장
        h = 560
        w = h * PHONE_RATIO
        gap = 16
        total = w * 3 + gap * 2
        x0p = right_x + (right_w - total) / 2
        for j in range(3):
            phone(s, SHOTS[shots[j]], cx_px=x0p + w / 2 + j * (w + gap), top_px=300, h_px=h)
    _txt(s, PX(right_x), PX(984), PX(right_w), PX(40), caption, size=11, color=MUTE,
         align=PP_ALIGN.CENTER, line_spacing=1.22)
    footer(s, page, source)
    return s


# ============================================================
def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # ───────────────── 01 표지 ─────────────────
    s = newslide(prs)
    # 좌측 네이비 사이드바 (560px)
    _rect(s, 0, 0, PX(560), SLIDE_H, fill=INK)
    _txt(s, PX(80), PX(96), PX(432), PX(96), "2026 SEOUL BIG DATA\nCOMPETITION · 창업부문",
         size=11, bold=False, color=C("8A95AE"), line_spacing=1.5)
    _hline(s, PX(80), PX(884), PX(60), color=BLUE2, weight=2.0)
    _txt(s, PX(80), PX(908), PX(432), PX(80),
         [("팀 SSGI\n", {"color": C("8A95AE")}), ("제출 · 2026. 05. 13.", {"color": C("D7DCE7")})],
         size=10, color=C("8A95AE"), line_spacing=1.6)
    _txt(s, PX(80), PX(1024), PX(432), PX(36), "PRODUCT · SERVICE TRACK · 상세기획서",
         size=8.5, color=C("4A5878"))
    # 우측 메인
    _txt(s, PX(640), PX(196), PX(1200), PX(32), "SOSANGGONGIN · AI BUSINESS COACH",
         size=10, bold=True, color=BLUE)
    _txt(s, PX(640), PX(240), PX(1200), PX(180), "SSGI", size=72, bold=True, color=INK, line_spacing=1.0)
    _txt(s, PX(640), PX(404), PX(1200), PX(56), "소상공인 AI 경영코치", size=22, bold=True, color=INK2)
    _txt(s, PX(640), PX(516), PX(1200), PX(220),
         [("사장님이 모르고 놓치는 돈,\n", {}), ("서울시 데이터", {"color": BLUE}), ("로 찾아드립니다.", {})],
         size=35, bold=True, color=INK, line_spacing=1.25)
    _hline(s, PX(640), PX(836), PX(1200), color=LINE, weight=1.0)
    bignum(s, 640, 868, 380, "LIVE FEATURES", "10", "개", "지금 실제 작동 중인 기능", color=INK)
    bignum(s, 1060, 868, 380, "SEOUL OPEN DATA", "8", "종", "열린데이터광장 데이터셋", color=BLUE)
    bignum(s, 1480, 868, 380, "PAID USERS", "0", "명", "베타 · 트랙션 부풀리지 않습니다", color=INK)

    # ───────────────── 02 목차 ─────────────────
    s = newslide(prs)
    eyebrow(s, "02 · CONTENTS")
    section_title(s, "상세기획서 구성 — 평가표 매칭", y=128, w=1300)
    subtitle(s, "분량과 강조는 심사 가중치(배경·취지 10 / 기능 상세 30 / 앱 60)에 맞춰 배분했어요.", w=1300)
    # 우상단 가중치 카드
    _rect(s, PX(1424), PX(84), PX(400), PX(196), fill=WHITE, line=LINE, line_w=1.0, radius=0.04)
    _txt(s, PX(1452), PX(100), PX(348), PX(22), "SCORING WEIGHTS", size=8, bold=True, color=MUTE)
    weights = [("기능 상세 설명", 30, BLUE), ("화면 구동", 20, BLUE2), ("UI/UX 완성도", 20, BLUE2),
               ("공공·AI 활용", 20, BLUE2), ("개발 배경·취지", 10, SLATE)]
    for i, (lbl, val, col) in enumerate(weights):
        yy = 130 + i * 29
        _txt(s, PX(1452), PX(yy), PX(118), PX(24), lbl, size=9, bold=True, color=INK2,
             anchor=MSO_ANCHOR.MIDDLE)
        _rect(s, PX(1578), PX(yy + 8), PX(176), PX(8), fill=C("ECEFF5"), radius=0.5)
        _rect(s, PX(1578), PX(yy + 8), PX(176 * val / 30), PX(8), fill=col, radius=0.5)
        _txt(s, PX(1762), PX(yy), PX(38), PX(24), str(val), size=9.5, bold=True, color=INK2,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    # 목차 2열
    toc = [
        ("01", "표지", "COVER", None),
        ("03", "개발 배경 ① — 사장님의 정보 비대칭 3가지", None, ("배경·취지 10", BLUE, BLUEBG)),
        ("04", "개발 배경 ② — 누가·왜 + 공공데이터 이용 활성화", None, ("배경·취지 10", BLUE, BLUEBG)),
        ("05", "서비스 개요 — 한 줄 정의 + 전체 기능 지도", None, ("기능 상세 30", WHITE, BLUE)),
        ("06", "활용 공공데이터 — 서울 8종 + 국세청 표", None, ("공공·AI 20", BLUE, BLUEBG)),
        ("07", "AI 활용 — 결정론 엔진 + RAG + GPT-4o 4층", None, ("공공·AI 20", BLUE, BLUEBG)),
        ("08", "기능 상세 ① — 폐업 위험도 진단", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("09", "기능 상세 ② — 매일 1줄 액션", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("10", "기능 상세 ③ — 지원금 매칭 + AI 사업계획서 초안 (RAG)", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("11", "기능 상세 ④ — 인사이트: 경쟁·집중 분석", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("12", "기능 상세 ⑤ — AI 종합 진단 + PREMIUM PDF 진단서", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("13", "기능 상세 ⑥ — 마케팅 진단: 채널·카피·객단가", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("14", "기능 상세 ⑦ — 메뉴 전략: 갭·시즌·차별화", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("15", "기능 상세 ⑧ — 음성 질문 + 서울 문화행사 알림", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("16", "기능 상세 ⑨ — 카카오페이 결제 + Pro 업그레이드", None, ("기능 상세 30 ★", WHITE, BLUE)),
        ("17", "화면 흐름도 — 메인 4탭 → 인사이트 4탭", None, ("화면 구동 20", BLUE, BLUEBG)),
        ("18", "라이브 화면 — 실제 캡처 모음", None, ("화면 구동 20", BLUE, BLUEBG)),
        ("19", "UI/UX — 시니어 친화 + 3-클릭 룰", None, ("UI/UX 20", SLATE, GREYBG)),
        ("B", "백업 — 시장·로드맵·팀 (2차 발표용)", "BACKUP", None),
    ]
    for i, (n, t, en, badge) in enumerate(toc):
        col = i // 10
        row = i % 10
        x = 96 + col * 880
        y = 308 + row * 70
        _hline(s, PX(x), PX(y + 58), PX(840), color=LINE, weight=0.75)
        ncol = BLUE if n != "B" else MUTE
        _txt(s, PX(x), PX(y + 8), PX(52), PX(40), n, size=14.5, bold=True, color=ncol)
        tcol = INK2 if n not in ("B",) else MUTE
        tw = 430 if badge else 720
        _txt(s, PX(x + 62), PX(y + 6), PX(tw), PX(54), t, size=11.5, bold=True, color=tcol,
             anchor=MSO_ANCHOR.MIDDLE if len(t) < 20 else MSO_ANCHOR.TOP, line_spacing=1.1)
        if badge:
            lbl, fg, bg_ = badge
            bw = PX(44 + 23 * len(lbl))
            bx = PX(x + 840) - bw
            _rect(s, bx, PX(y + 13), bw, PX(28), fill=bg_, radius=0.3)
            _txt(s, bx, PX(y + 13), bw, PX(28), lbl, size=8, bold=True,
                 color=fg, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        elif en:
            _txt(s, PX(x + 600), PX(y + 15), PX(240), PX(26), en, size=8.5, color=MUTE,
                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    footer(s, 2, "1차 서류 100점 = 앱 60(공공·AI 20 / 화면 20 / UI·UX 20) + 상세기획서 40(배경·취지 10 / 기능 상세 30) + 결합 가점 2")

    # ───────────────── 03 개발 배경 ① ─────────────────
    s = newslide(prs)
    content_head(s, "01 · 개발 배경 및 취지",
                 [("사장님은 ", False), ("자기 가게가 위험한지조차", True), (" 모르고 문을 닫습니다.", False)],
                 "소상공인 730만 · 5년 생존율 약 33% — 그런데 정보는 흩어져 있고, raw 해서 못 씁니다.",
                 rubric="배경·취지 10")
    _txt(s, PX(96), PX(310), PX(1500), PX(30), "사장님이 마주한 정보 비대칭 3가지", size=13.5, bold=True, color=INK)
    cards3 = [
        ("① 내 가게가 위험한가?", "상권 매출은 줄고, 옆 가게는 늘고 있는데 — 어디서 확인하나요? 통계청·서울 열린데이터에 다 있지만, 사장님이 직접 API 를 뜯어볼 수는 없습니다.", RED),
        ("② 받을 수 있는 돈을 모름", "소상공인시장진흥공단·서울시 지원사업이 매년 수십 건. 자격이 되는데도 공고를 못 찾아 신청 못 한 사장님이 많습니다.", AMBER),
        ("③ 그래서 뭘 해야 하나?", "조언은 넘치지만 \"우리 동네 우리 업종\"에 맞는 한 가지는 없습니다. 정보 과부하 → 결국 아무것도 안 함.", BLUE),
    ]
    cw = 562
    for i, (t, b, ac) in enumerate(cards3):
        card(s, 96 + i * (cw + 21), 356, cw, 376, t, b, accent=ac, body_size=13, title_size=15.5)
    _rect(s, PX(96), PX(766), PX(1728), PX(178), fill=BLUEBG, radius=0.04)
    _txt(s, PX(128), PX(788), PX(1664), PX(140),
         [("데이터는 이미 공개돼 있습니다. 문제는 \"사장님이 쓸 수 있는 형태\"가 아니라는 것.\n", {}),
          ("SSGI 는 서울 공공데이터를 사장님 언어로 번역해, 매일 \"오늘 이거 하세요\" 한 줄로 바꿉니다.", {"color": BLUE})],
         size=17, bold=True, color=INK, line_spacing=1.4)
    footer(s, 3, "출처: 통계청 소상공인현황 / 중소벤처기업부 / 서울 열린데이터광장")

    # ───────────────── 04 개발 배경 ② ─────────────────
    s = newslide(prs)
    content_head(s, "01 · 개발 배경 및 취지",
                 [("누가 쓰나 — ", False), ("컨설팅 받을 여유 없는", True), (" 동네 가게 사장님.", False)],
                 "그리고 이 서비스가 \"공공데이터 이용 활성화\"에 어떻게 기여하는가.",
                 rubric="배경·취지 10", title_w=1700)
    # 좌: 타깃
    _txt(s, PX(96), PX(310), PX(820), PX(30), "타깃 사용자", size=13.5, bold=True, color=INK)
    tcards = [
        ("누가", "서울·수도권 동네 가게 사장님(음식·카페·미용·소매·학원 등). 시뮬 페르소나: 의정부LC 금오동에서 학원을 운영하는 4050 사장님.", INK),
        ("왜 못 했나", "전문 컨설팅은 회당 수십만 원. 공공데이터는 자치구·행정동·상권코드 매핑을 알아야 쓸 수 있음. 사장님에겐 둘 다 장벽.", RED),
        ("왜 지금", "GPT-4o 로 \"raw 데이터 → 사장님 문장\" 번역이 가능해짐. 카카오 OAuth·알림으로 추가 앱 설치 없이 도달.", BLUE),
    ]
    for i, (t, b, ac) in enumerate(tcards):
        card(s, 96, 356 + i * 198, 820, 184, t, b, accent=ac, body_size=12, title_size=14.5)
    # 우: 공공데이터 이용 활성화 기여
    _txt(s, PX(960), PX(310), PX(864), PX(30), "공공데이터 이용 활성화 기여", size=13.5, bold=True, color=INK)
    contrib = [
        ("데이터 → 의사결정", "서울 열린데이터 8종을 한 화면에 결합·해석. \"열려는 있지만 안 쓰이던\" 데이터를 실제 경영 판단으로 연결."),
        ("이용자 저변 확대", "API 를 다룰 줄 모르는 소상공인을 새 공공데이터 수요자로 편입. 사장님은 데이터를 \"읽지\" 않고 \"받아\" 씀."),
        ("재사용 파이프라인", "상권코드↔행정동 매핑·분기 캐싱·업종 정규화를 모듈화 — 다른 서비스도 같은 방식으로 서울 데이터 활용. 업종 지식은 YAML 플레이북으로 분리(파일 1개 = 새 업종)."),
        ("개방 데이터 가치 입증", "\"공개했더니 이렇게 쓰이더라\"의 사례. 데이터 1건이 사장님 1명의 폐업 위험 신호로 바뀌는 경로를 보여줌."),
    ]
    for i, (t, b) in enumerate(contrib):
        card(s, 960, 356 + i * 156, 864, 142, t, b, accent=GREEN, body_size=11.5, title_size=13.5)
    footer(s, 4, "공고 5번 의무: 활용한 공공데이터 목록 정확 기재 / 데이터 이용 활성화 기여 서술")

    # ───────────────── 05 서비스 개요 ─────────────────
    s = newslide(prs)
    content_head(s, "02 · 서비스 개요",
                 [("한 줄 정의 — ", False), ("\"서울 공공데이터로 진단하는, 매일 1줄 AI 경영코치\"", True), (".", False)],
                 "온보딩 한 번 → 가게 자동 분석 → 매일·매주 액션. 10개 기능이 한 흐름으로 연결됩니다.",
                 rubric="기능 상세 30", title_w=1700)
    groups = [
        ("진단 · 자동 (GPT 미사용)", BLUE2, ["폐업 위험도 점수 0~100 + 위험 신호", "5차원 입지 분석", "경쟁 비교 — 같은 동네·같은 업종"]),
        ("매일·매주 액션 (GPT-4o)", RED, ["매일 아침 7시 — 오늘 할 일 1개", "이번 주 1가지 — 집중분석 우선순위", "손실 프레이밍 — \"놓치고 있어요\""]),
        ("돈·성장 (RAG + GPT-4o)", BLUE, ["지원금 매칭 + AI 사업계획서 초안", "마케팅 진단 — 채널·카피·객단가", "메뉴 전략 — 갭·시즌·차별화"]),
        ("접근 · 증빙 · 결제", AMBER, ["음성 질문 — 마이크 한 번 → 답변+화면 이동", "PREMIUM PDF 진단서 + 서울 문화행사 알림", "카카오페이 결제 — Pro 업그레이드(테스트)"]),
    ]
    cw = 414
    for i, (t, ac, items) in enumerate(groups):
        x = 96 + i * (cw + 22)
        _rect(s, PX(x), PX(312), PX(cw), PX(568), fill=WHITE, line=LINE, line_w=1.0, radius=0.035)
        _rect(s, PX(x), PX(312), PX(cw), PX(8), fill=ac)
        _txt(s, PX(x + 28), PX(338), PX(cw - 50), PX(64), t, size=15.5, bold=True, color=INK, line_spacing=1.2)
        for j, it in enumerate(items):
            yy = 432 + j * 142
            _txt(s, PX(x + 26), PX(yy + 1), PX(20), PX(22),
                 [("●", {"size": 9, "color": ac})], size=9, color=ac)
            _txt(s, PX(x + 48), PX(yy - 3), PX(cw - 70), PX(136), it, size=12.5, color=SLATE, line_spacing=1.3)
    _rect(s, PX(96), PX(902), PX(1728), PX(98), fill=BLUEBG, radius=0.04)
    _txt(s, PX(124), PX(920), PX(1672), PX(64),
         [("온보딩(가게 검색·등록) → 자치구·행정동·업종 매핑 → ", {}), ("4개 그룹이 같은 데이터를 공유하며 매일 갱신.", {"color": BLUE})],
         size=15.5, bold=True, color=INK, line_spacing=1.3)
    footer(s, 5, "라이브 배포: ssgi-ai-coach.vercel.app — 33개 API 라우트 구동 중")

    # ───────────────── 06 활용 공공데이터 ─────────────────
    s = newslide(prs)
    content_head(s, "03 · 활용 공공데이터",
                 [("서울 열린데이터광장 ", False), ("8종", True), (" + 국세청 + 카카오 — 모두 라이브 호출 중.", False)],
                 "상권코드↔행정동 매핑(TbgisTrdarRelm)으로 \"우리 동네\"만 골라냅니다.",
                 rubric="공공·AI 20", title_w=1700)
    # 표 헤더
    hx = [96, 480, 1380, 1700]
    hcols = ["제공처 / API", "데이터셋 (호출 식별자)", "쓰는 곳", "주기"]
    _hline(s, PX(96), PX(310), PX(1728), color=LINE)
    for x, name in zip(hx, hcols):
        _txt(s, PX(x), PX(318), PX(360), PX(26), name, size=11.5, bold=True, color=INK)
    rows = [
        ("서울 열린데이터", "VwsmTrdarSelngQq · 우리마을가게 상권분석(추정매출)", "위험도·경쟁·객단가", "분기"),
        ("서울 열린데이터", "VwsmTrdarStorQq · 우리마을가게 상권분석(점포수·개폐업)", "위험도·경쟁", "분기"),
        ("서울 열린데이터", "VwsmTrdarIxQq · 상권변화지표(활성/정체/축소/다이나믹)", "위험도 2×2 매트릭스", "분기"),
        ("서울 열린데이터", "VwsmTrdarFlpopQq · 상권 유동인구(시간대·요일·성·연령)", "마케팅 피크 타게팅", "분기"),
        ("서울 열린데이터", "SPOP_LOCAL_RESD_DONG · 행정동 생활인구(거주)", "5차원 입지 분석", "일"),
        ("서울 열린데이터", "TbgisTrdarRelm · 상권영역-행정동 매핑", "지역 필터링(전 기능)", "정적"),
        ("서울 열린데이터", "culturalEventInfo · 서울 문화행사 정보", "이벤트 알림·메뉴 시즌", "수시"),
        ("서울 열린데이터", "VwsmTrdarWrcPopltnQq · 상권 직장인구", "직주비율 산출", "분기"),
        ("공공데이터포털", "국세청 사업자등록정보 진위확인", "온보딩 가게 검증", "실시간"),
        ("민간 API", "Kakao Local Search · 카카오 디벨로퍼스", "가게 검색·좌표", "실시간"),
    ]
    for i, (prov, ds, use, per) in enumerate(rows):
        y = 358 + i * 60
        if i % 2 == 0:
            _rect(s, PX(96), PX(y - 6), PX(1728), PX(56), fill=WHITE)
        seoul = prov == "서울 열린데이터"
        _txt(s, PX(96), PX(y), PX(380), PX(44), prov, size=11, bold=True,
             color=BLUE if seoul else MUTE, anchor=MSO_ANCHOR.MIDDLE)
        _txt(s, PX(480), PX(y), PX(880), PX(44), ds, size=11, color=SLATE, anchor=MSO_ANCHOR.MIDDLE)
        _txt(s, PX(1380), PX(y), PX(310), PX(44), use, size=11, color=SLATE, anchor=MSO_ANCHOR.MIDDLE)
        _txt(s, PX(1700), PX(y), PX(124), PX(44), per, size=11, color=MUTE, anchor=MSO_ANCHOR.MIDDLE)
    _txt(s, PX(96), PX(966), PX(1500), PX(30),
         "공공데이터 8종 결합 — 경진대회 결합 활용 가점(+2) 요건 충족. 추출일 2026-04.",
         size=12, bold=True, color=GREEN)
    footer(s, 6, "전 API 는 backend/app/services/seoul_api_service.py 에서 retry+fallback 패턴으로 호출")

    # ───────────────── 07 AI 활용 ─────────────────
    s = newslide(prs)
    content_head(s, "04 · AI 활용",
                 [("AI 를 두 층으로 — ", False), ("\"숫자는 결정론, 말은 GPT\"", True), (".", False)],
                 "거짓말 안 하게 만드는 구조: 점수는 코드가 계산하고, GPT 는 그 위에서 사장님 문장만 씁니다.",
                 rubric="공공·AI 20", title_w=1700)
    layers = [
        ("① 결정론 위험 엔진", "재현성·신뢰", BLUE2,
         "GPT 미사용. 매출↓ · 개폐업률 · 상권변화지표 2×2(생존기간×폐업기간 vs 서울평균) · 지원금 마감 임박 · 유동인구↓ — 5개 시그널 가중합 → 0~100점. 같은 입력이면 항상 같은 점수."),
        ("② RAG 검색 레이어", "환각 차단", GREEN,
         "지원사업 공고를 text-embedding-3-small 로 임베딩 → ChromaDB(코사인)에 인덱싱. 사장님 업종·매출·사업기간을 쿼리로 top-k 매칭 + 업종별 지원금 카테고리 태그로 가중. \"왜 맞는지\" 근거 문장도 함께."),
        ("③ GPT-4o 생성 레이어", "사장님 언어", BLUE,
         "매일 1줄 액션 · AI 종합진단 · 마케팅/메뉴 전략. 시스템 프롬프트에 \"업종 플레이북(40개 세부 업종 YAML 지식팩 — KPI·채널 근거표·카피 톤·데이터 해석 주의)\" + \"손실 프레이밍 어법\"을 런타임 주입. 추정치는 amber \"AI 추정\" 라벨 강제."),
        ("④ 가드레일 레이어", "정직성", AMBER,
         "하루 1액션(UniqueConstraint) · 사회적 증거 k≥10일 때만 노출 · 한자 0건 검수 · 결제 0건 사실 그대로 표기. 시스템 설계로 폭주·과장 방지."),
    ]
    cw, chh = 856, 290
    for i, (t, tag, ac, b) in enumerate(layers):
        x = 96 + (i % 2) * (cw + 16)
        y = 332 + (i // 2) * (chh + 20)
        _rect(s, PX(x), PX(y), PX(cw), PX(chh), fill=WHITE, line=LINE, line_w=1.0, radius=0.03)
        _rect(s, PX(x), PX(y + 14), PX(6), PX(chh - 28), fill=ac)
        _txt(s, PX(x + 30), PX(y + 18), PX(cw - 250), PX(38), t, size=16.5, bold=True, color=INK)
        bw = PX(48 + 28 * len(tag))
        _rect(s, PX(x + cw - 26) - bw, PX(y + 20), bw, PX(30), fill=GREYBG, radius=0.3)
        _txt(s, PX(x + cw - 26) - bw, PX(y + 20), bw, PX(30), tag, size=10.5, bold=True, color=SLATE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        _txt(s, PX(x + 30), PX(y + 64), PX(cw - 56), PX(chh - 78), b, size=13, color=SLATE, line_spacing=1.34)
    footer(s, 7, "GPT-4o · text-embedding-3-small / 프롬프트: backend/app/routers/insights.py · services/action_generator.py")

    # ───────────────── 08~15 기능 상세 8장 ─────────────────
    feature_slide(
        prs, 8, "05 · 기능 상세 ① — 폐업 위험도 진단",
        [("홈을 열면 제일 먼저: ", False), ("\"내 가게 위험도 100점 중 ○○점\"", True), (".", False)],
        "GPT 가 아니라 결정론 엔진이 계산한 점수 + 위험 신호 5개를 카드로.",
        what="가게 폐업 위험을 0~100 점수로. 무엇이 위험을 끌어올렸는지 \"위험 신호\"로 분해해 보여줌.",
        data="우리마을가게 상권분석(추정매출 VwsmTrdarSelngQq·점포수 VwsmTrdarStorQq) · 상권변화지표(VwsmTrdarIxQq) · 상권 유동인구(VwsmTrdarFlpopQq).",
        ai="결정론 위험 엔진 — GPT 미사용. 5개 시그널 가중합. 상권변화지표는 2×2 매트릭스(생존기간×폐업기간 vs 서울평균)로 판정. 개점 1년 미만 사장님은 통계 폐업률 반영해 가산.",
        flow="온보딩에서 가게 검색·등록 → 자치구·행정동·상권코드 매핑 → 분기 데이터 갱신 시 재계산 → 홈 상단 점수 카드 렌더.",
        shots=["01"],
        caption="홈 화면 — 폐업 위험도 점수 + 위험 신호 카드 (라이브 배포 실제 화면, 시뮬 계정)",
        source="risk_score_engine.py — 결정론 산출 / 점수는 GPT 호출 없이 재현 가능",
    )
    feature_slide(
        prs, 9, "06 · 기능 상세 ② — 매일 1줄 액션",
        [("매일 아침 7시, ", False), ("오늘 할 일 딱 1개", True), (". 그 이상은 안 줍니다.", False)],
        "정보 과부하 방지가 설계 원칙 — \"추천합니다\"가 아니라 \"놓치고 있습니다\".",
        what="매일 1개 액션 + 왜 해야 하는지 1줄 근거. 카카오 알림으로 도달. 하루에 1개만(중복 제약).",
        data="위험 신호 · 매칭된 지원사업(마감 임박) · 서울 문화행사(culturalEventInfo) 를 종합.",
        ai="GPT-4o. 시스템 프롬프트에 업종 플레이북(40개 세부 업종 YAML 지식팩 — 업종별 KPI·채널·데이터 함정) + 손실 프레이밍 어법 주입. 같은 가게에 같은 액션 반복 방지.",
        flow="APScheduler 크론 07:00 → 사용자별 데이터 수집 → GPT-4o 액션 1줄 → DB UniqueConstraint(가게,날짜) 저장 → 카카오 알림(실패 시 FCM → 조용히 패스).",
        shots=["01"],
        caption="홈 화면 — 오늘의 액션 (예: \"1,040만원 지원금, 신청 마감 전\")",
        source="action_generator.py — daily action 시스템 프롬프트 / ADR 003: 하루 1액션",
    )
    feature_slide(
        prs, 10, "07 · 기능 상세 ③ — 지원금 매칭 + AI 사업계획서 초안",
        [("받을 수 있는 지원사업을 찾고, ", False), ("사업계획서 초안까지", True), (" 써줍니다.", False)],
        "공고를 벡터로 인덱싱(RAG) → 사장님 자격으로 검색 → GPT 가 매칭 사유 + 사업계획서 초안 작성.",
        what="소상공인시장진흥공단·서울시 지원사업을 업종·매출·사업기간으로 매칭. 카드마다 \"왜 맞는지\" 사유 + \"초안 받기\". 초안은 가게 개요·경영 현황 빈칸을 아는 정보로 자동 채움(나머지는 [사장님 작성 필요] 표시).",
        data="공공 지원사업 공고(소상공인시장진흥공단·서울시 등) 15건+ 를 시드로 적재. 가게 자격·개요는 온보딩·국세청 검증값 사용.",
        ai="text-embedding-3-small 로 공고 임베딩 → ChromaDB(코사인)에 인덱싱 → 사장님 조건을 쿼리로 top-k 검색 → GPT-4o 가 매칭 사유 + 사업계획서 초안(개요/현황/차별점 섹션) 생성.",
        flow="인덱싱 크론(주 1회) → 지원사업 탭 → 자격 임베딩 쿼리 → 매칭 카드(홈에도 상위 노출) → \"초안 받기\" → GPT-4o 초안(절약 시간 표시).",
        shots=["02", "04", "bizplan"],
        caption="홈 매칭 3건(좌) · 지원사업 탭 — 최대 31,400만원·신청하기·초안 받기(중) · AI 사업계획서 초안 — 빈칸 자동 채움·절약 약 2시간(우)",
        source="rag_service.py · ChromaDB PersistentClient / scripts/seed_subsidies.py",
    )
    feature_slide(
        prs, 11, "08 · 기능 상세 ④ — 인사이트: 경쟁·집중 분석",
        [("같은 동네, 같은 업종과 비교해서 — ", False), ("강점·약점·우리 가게 자리", True), ("를 보여줍니다.", False)],
        "5차원 입지 분석은 코드가 계산하고, 강점/약점 해석만 GPT 가 합니다. 데이터 출처도 화면에 명시.",
        what="경쟁 탭: 같은 상권·같은 업종 매출/점포수 비교. 집중분석 탭: 강점·약점·\"우리 가게 자리\"·시급한 신호.",
        data="우리마을가게 상권분석(매출·점포수) · 행정동 생활인구(SPOP_LOCAL_RESD_DONG) · 상권 유동인구·직장인구.",
        ai="5차원 입지 분석(직주비율·다양성·집객력·동선효율·시간집중 + 서울 포지셔닝·생애주기)은 결정론 산출 → GPT-4o 가 강점/약점만 사장님 문장으로 해석. 맛·친절 등 데이터 밖은 모른다고 명시.",
        flow="인사이트 탭 → 경쟁/집중분석 → 상권코드 기준 동종업종 집계 → 5차원 산출 → GPT 해석 → 카드 + 데이터 출처 표기.",
        shots=["05", "09"],
        caption="경쟁 탭 — 데이터 출처 명시(좌) · 집중분석 — 강점·약점·우리 가게 자리(우)",
        source="insights.py(deep-report 영역) · 5차원 location_analysis 결정론 / 출처 화면 노출",
    )
    feature_slide(
        prs, 12, "09 · 기능 상세 ⑤ — AI 종합 진단 + PREMIUM PDF",
        [("가게 전체를 종합 진단하고, ", False), ("\"이번 주 1가지\"", True), ("를 정해줍니다. PDF 진단서도.", False)],
        "여러 데이터를 결합한 종합 리포트 — 추정치는 모두 amber \"AI 추정\" 라벨.",
        what="집중분석의 \"AI 종합 진단\" — 위험·입지·경쟁·마케팅을 한 번에 요약 + 이번 주 우선순위 1가지. PREMIUM 은 PDF 진단서 다운로드.",
        data="위 기능들의 결과(위험 점수·5차원·경쟁 비교·매출 추이)를 결합. 추가 호출 없이 캐시된 분기 데이터 재사용.",
        ai="GPT-4o (deep-report 프롬프트). 세부 업종 플레이북(데이터 해석 주의 포함) + 사장님 화법. \"이번 주 1가지\"로 우선순위를 좁힘. 추정 매출·효과는 amber \"AI 추정\" 라벨 의무.",
        flow="집중분석 탭 → AI 종합 진단 카드 → 이번 주 1가지 → PREMIUM REPORT → report_generator 가 PDF 렌더 → 다운로드/공유(CSV·JSON 내보내기도).",
        shots=["08", "03", "pdf"],
        caption="집중분석 — AI 종합 진단·이번 주 1가지(좌) · 홈 — PREMIUM 진단서 진입(중) · 다운로드된 PDF 진단서 — 67점·등급 C·카테고리별 평가표(우)",
        source="insights.py · report_generator.py — PDF 생성 / 추정치 amber 라벨 일관 적용",
    )
    feature_slide(
        prs, 13, "10 · 기능 상세 ⑥ — 마케팅 진단: 채널·카피·객단가",
        [("예산 0원이면 0원대로, 5만원이면 5만원대로 — ", False), ("시나리오별로", True), (" 알려줍니다.", False)],
        "유동인구 데이터로 \"언제·누구에게\"를 정하고, 카피 3종(신뢰·친근·긴급)까지 써줍니다.",
        what="예산별 시나리오(0원/5만원) · 채널 우선순위 + ROI(가설) · 카피 3종(신뢰·친근·긴급형: 단골 SMS·매장 POP·SNS·배달앱) · 객단가 끌어올리기.",
        data="상권 유동인구(VwsmTrdarFlpopQq — 시간대·요일·성·연령 → 피크 타임/타깃) · 우리마을가게 추정매출(객단가 비교).",
        ai="GPT-4o (marketing-strategy 프롬프트). 업종 플레이북의 채널 근거표를 그대로 주입(이 표 밖의 ROI/ROAS 숫자 생성 금지) — 업종 안 맞는 헛조언 차단. ROI 수치는 \"가설\" 라벨, 결제 데이터 아님.",
        flow="인사이트 마케팅 탭 → 마케팅 진단 → 유동인구 피크 분석 → 채널 우선순위 + 카피 생성 → \"오늘 당장\" 1가지로 연결.",
        shots=["10", "11", "12"],
        caption="예산별 시나리오 0원/5만원(좌) · 채널 우선순위 SMS ROI 150%·전단지 100%(중) · 카피 3종 신뢰·친근·긴급형(우)",
        source="insights.py(marketing-strategy) · marketing_audit.py / ROI 는 가설 라벨",
    )
    feature_slide(
        prs, 14, "11 · 기능 상세 ⑦ — 메뉴 전략: 갭·시즌·차별화",
        [("옆 가게엔 있고 우리 가게엔 없는 메뉴 — ", False), ("4주 캘린더", True), ("로 만들어줍니다.", False)],
        "상권 업종 구성과 서울 문화행사·계절을 엮어 \"이번 달 뭘 추가할지\"를 제시.",
        what="메뉴 갭 분석(상권엔 있는데 우리 가게엔 없는 카테고리) · 시즌 캘린더 4주(주차별 테마·연계 채널) · 차별화 한 수(경쟁사가 안 하는 1가지).",
        data="상권 업종 구성(다양성지수 — 우리마을가게 상권분석 기반) · 서울 문화행사(culturalEventInfo) · 계절·학사 일정.",
        ai="GPT-4o (menu-strategy 프롬프트). 업종 미등록이면 \"업종 등록 필요\" 안내로 정확도 보호. 도입 비용·난이도도 함께 표기해 사장님이 고를 수 있게.",
        flow="인사이트 메뉴 탭 → 메뉴 전략 → 갭/시즌/차별화 3 섹션 → 각 항목 \"도입 비용·기간\" → 단골 SMS·POP·SNS·배달앱 연계 제안.",
        shots=["15", "16", "17"],
        caption="갭 분석 — 음악·코딩·창의융합 교육(좌) · 시즌 캘린더 4주 5/13~6/7(중) · 차별화 한 수 — 자녀 맞춤 상담(우)",
        source="insights.py(menu-strategy) / 업종 미등록 시 정확도 가드",
    )
    feature_slide(
        prs, 15, "12 · 기능 상세 ⑧ — 음성 질문 + 서울 문화행사 알림",
        [("마이크 한 번 누르고 \"지원금 알려줘\" — ", False), ("AI 가 답하고 그 화면으로", True), (" 데려갑니다.", False)],
        "키보드가 불편한 사장님을 위한 입력. 그리고 동네 행사 = 손님 늘릴 기회로 알림.",
        what="음성 질문: 플로팅 마이크 → 말하면 → AI 답변 + 의도에 맞는 화면 자동 이동. 문화행사 알림: 우리 자치구 행사를 \"이날 손님 늘 수 있어요\"로 변환.",
        data="서울 문화행사 정보(culturalEventInfo — 자치구 필터).",
        ai="GPT-4o + 브라우저 Web Speech API(STT, 한국어). 발화 → 의도 분류(지원금·마케팅·경쟁·집중분석·이벤트·매출·홈) → 답변 + 해당 화면 라우팅. 답을 모르면 모른다고.",
        flow="대시보드 플로팅 마이크 → 음성 인식(종료 시 자동 전송) → POST /voice/query → 의도 분류 → 답변 카드 + 후속 질문 칩 + 화면 이동.",
        shots=["voice", "03"],
        caption="홈 — AI 음성 질문 \"마케팅\" 발화 → 답 찾는 중(마이크 우하단 상주)(좌) · 홈 — 서울시 문화행사 카드 + PREMIUM 진단서(우)",
        source="voice.py — intent 분류·라우팅 / useSTT.ts — Web Speech API(Chrome·Edge)",
    )
    feature_slide(
        prs, 16, "13 · 기능 상세 ⑨ — 카카오페이 결제 + Pro 업그레이드",
        [("가치를 느끼면 ", False), ("월 9,900원 — 하루 330원", True), ("으로 잡기. 카카오페이 결제.", False)],
        "결제 모듈은 연동 완료·테스트 환경. 정식 결제는 사업자 가맹 후 2026 Q3 — 지금도 테스트 결제로 전 흐름이 동작합니다.",
        what="Free 로 충분히 쓰다가, Pro 전용 기능(쿠폰 무제한·인사이트 4탭·AI 사업계획서 초안·PDF 내보내기)에서 페이월 → SSGI Pro 9,900원/월. \"미신청 보조금 평균 240만원 → Pro 1년 12만원으로 회수\" 손실 프레이밍.",
        data="결제 자체엔 공공데이터 미사용. 단, 페이월 카피의 \"미신청 보조금 N건·평균 ○○만원\"은 RAG 매칭 결과 + 지원사업 공고 데이터에서 산출.",
        ai="GPT 미사용 — 결정론 결제 플로우. 카카오페이 단건결제 API(ready → 카카오페이 화면 리다이렉트 → approve). 결제 성공 시 DB 에 Pro 만료일(+1개월) 기록 → 페이월 자동 해제, 만료 시 자동 복귀.",
        flow="Pro 전용 기능 클릭(페이월) → /upgrade → \"카카오페이로 결제(테스트)\" → 카카오페이 화면 → 승인 → 결제 완료(만료일·테스트 안내) → \"Pro 로 대시보드 가기\".",
        shots=["paywall", "pay_up", "pay_done"],
        caption="페이월 — 메뉴 전략 Pro 전용(좌) · SSGI Pro 업그레이드 — 혜택 5종·9,900원·테스트 안내(중) · 결제 완료 — 만료일 표시·실제 청구 없음(우)",
        source="kakao_pay_service.py · routers/payments.py — TC0ONETIME 테스트 cid / frontend/src/app/upgrade · 페이월 트리거",
    )

    # ───────────────── 17 화면 흐름도 ─────────────────
    s = newslide(prs)
    content_head(s, "14 · 화면 흐름도 — 메인 → 세부",
                 [("메인 4탭 → 인사이트 4탭 — ", False), ("3번 안에", True), (" 답에 닿습니다.", False)],
                 "온보딩(가게 검색·등록) 후 하단 탭 4개. 인사이트 안에 다시 4개 탭.",
                 rubric="화면 구동 20", title_w=1700)
    _txt(s, PX(96), PX(306), PX(1500), PX(30), "① 메인 — 하단 탭 4종", size=14.5, bold=True, color=INK)
    mains = [
        ("홈", "위험도 · 오늘의 액션 · 매칭 지원금 3건 · 문화행사 · PREMIUM PDF", BLUE2),
        ("지원사업", "매칭 리스트 · 자격 사유 · 신청하기 · 초안 받기 (최대 ○○만원)", GREEN),
        ("인사이트", "경쟁 · 집중분석 · 마케팅 · 메뉴 — 4개 세부 탭", BLUE),
        ("쿠폰", "쿠폰 발행 · 피크 타임 타게팅 · 단골 관리", AMBER),
    ]
    cw = 414
    for i, (t, b, ac) in enumerate(mains):
        card(s, 96 + i * (cw + 22), 346, cw, 204, t, b, accent=ac, body_size=11.5, title_size=14.5)
    _txt(s, PX(96), PX(584), PX(1700), PX(30), "② 인사이트 세부 — 탭 4종 (각 탭에서 AI 진단 + 실행 액션)",
         size=14.5, bold=True, color=INK)
    subs = [
        ("경쟁", "같은 동네·같은 업종 매출·점포수 비교 + 데이터 출처 명시", INK2),
        ("집중분석", "5차원 입지 + 강점/약점/우리 가게 자리 + AI 종합진단 + 이번 주 1가지 + PREMIUM PDF", INK2),
        ("마케팅", "예산 시나리오 0원/5만원 + 채널 우선순위·ROI + 카피 3종 + 객단가", INK2),
        ("메뉴", "갭 분석 + 시즌 캘린더 4주 + 차별화 한 수 + 도입 비용·기간", INK2),
    ]
    for i, (t, b, ac) in enumerate(subs):
        card(s, 96 + i * (cw + 22), 622, cw, 232, t, b, accent=BLUE, body_size=11, title_size=14.5)
    _rect(s, PX(96), PX(872), PX(1728), PX(94), fill=BLUEBG, radius=0.04)
    _txt(s, PX(124), PX(884), PX(1680), PX(72),
         "+ 음성 질문(플로팅 마이크) 어디서나 → 답변 + 해당 화면 자동 이동.\n"
         "+ 내 가게 페이지 — 로그인한 사장님도 업종 재설정(/profile) · \"이 진단은 ○○ 플레이북 v1 · 검수 2026-05-11 · 출처 N건\" 출처 칩.",
         size=12.5, bold=True, color=BLUE, line_spacing=1.3)
    footer(s, 17, "frontend/src/app — 메인 4 라우트 + insights 4탭 + onboarding·내 가게 / 라이브 시연 가능")

    # ───────────────── 18 라이브 화면 갤러리 ─────────────────
    s = newslide(prs)
    content_head(s, "14 · 화면 흐름도 — 실제 캡처 모음",
                 [("앱은 ", False), ("\"설명용 목업\"이 아니라 지금 도는 화면", True), ("입니다.", False)],
                 "ssgi-ai-coach.vercel.app — 시뮬 계정(의정부LC·금오동 학원)으로 실제 캡처. 모두 라이브.",
                 rubric="화면 구동 20", title_w=1700)
    gallery = [
        ("01", "홈 — 폐업 위험도 + 오늘의 액션"),
        ("02", "홈 — 매칭 지원사업 3건"),
        ("bizplan", "지원사업 — AI 사업계획서 초안"),
        ("voice", "홈 — AI 음성 질문 처리 중"),
        ("08", "인사이트>집중분석 — 이번 주 1가지"),
        ("pdf", "PREMIUM PDF 진단서 — 67점·등급 C"),
        ("14", "인사이트>메뉴 — 메뉴 전략"),
        ("pay_done", "결제 완료 — SSGI Pro(테스트)"),
    ]
    ph = 286
    for i, (key, lbl) in enumerate(gallery):
        col, row = i % 4, i // 4
        cx = 96 + 432 * col + 216
        top = 360 + row * 318
        phone(s, SHOTS[key], cx_px=cx, top_px=top, h_px=ph)
        _txt(s, PX(cx - 210), PX(top + ph + 12), PX(420), PX(30), lbl, size=11, color=MUTE,
             align=PP_ALIGN.CENTER, line_spacing=1.15)
    footer(s, 18, "전 화면 라이브 호출 — 백엔드 33개 API 라우트 / 시연 시 실물 데모 가능")

    # ───────────────── 19 UI/UX ─────────────────
    s = newslide(prs)
    content_head(s, "15 · UI/UX 완성도",
                 [("4050 사장님이 ", False), ("\"한 번에 알아보게\"", True), (" — 큰 글씨·1색 강조·3번 클릭.", False)],
                 "PWA(설치형 웹) · 카카오 로그인 15초 · 손실 프레이밍 카피 일관.",
                 rubric="UI/UX 20", title_w=1700)
    ux = [
        ("시니어 친화", "본문 큰 글씨 · 한 화면 한 메시지 · 카드형 레이아웃 · 강조색 1개(나머지 회색). 한자 0건 검수.", BLUE2),
        ("3-클릭 룰", "어떤 답이든 3번 안에. 하단 탭 4 → 세부 탭 → 액션. 음성으로는 1번에 점프.", GREEN),
        ("마찰 최소화", "카카오 OAuth 15초 가입 · 추가 앱 설치 없이 PWA · 알림은 카카오톡으로(도달률 최고).", BLUE),
        ("손실 프레이밍 UX", "\"추천\"이 아니라 \"놓치고 있어요\". 마감 D-카운트 · 같은 동네 ○명(k≥10) · 금액 강조 — 행동을 끌어내는 화면 어법.", RED),
        ("정직한 화면", "추정치는 amber \"AI 추정\" 칩 · 데이터 출처는 화면에 노출 · 결제 0건은 그대로 표기. 과장 없는 UI.", AMBER),
        ("반응형·접근성", "모바일 우선 · 에러 메시지는 사장님 말투로(\"마이크 권한이 막혀 있어요\") · 로딩/빈 화면 카피까지 설계.", INK2),
    ]
    cw, chh = 562, 290
    for i, (t, b, ac) in enumerate(ux):
        x = 96 + (i % 3) * (cw + 21)
        y = 332 + (i // 3) * (chh + 24)
        card(s, x, y, cw, chh, t, b, accent=ac, body_size=12, title_size=14.5)
    footer(s, 19, "Next.js 14 App Router · next-pwa · Tailwind / 라이브: ssgi-ai-coach.vercel.app")

    # ───────────────── 20 백업 ─────────────────
    s = newslide(prs)
    content_head(s, "B · 백업 — 시장·로드맵·팀",
                 "참고 — 사업화 관점 (1차는 상세기획서 중심, 아래는 2차 발표 때 펼칩니다).",
                 None, title_w=1700)
    _txt(s, PX(96), PX(310), PX(560), PX(30), "시장 (bottom-up)", size=14.5, bold=True, color=INK)
    _rect(s, PX(96), PX(350), PX(560), PX(404), fill=WHITE, line=LINE, line_w=1.0, radius=0.035)
    _txt(s, PX(128), PX(378), PX(500), PX(352),
         "소상공인 약 730만 사업자\n× 디지털 수용 약 30%\n× 월 9,900원 × 12개월\n= 약 2,604억 (SAM, 가설)\n\nSOM: 서울·수도권 우선,\n1년차 1,000 MAU 도전 목표.",
         size=13, color=SLATE, line_spacing=1.5)
    _txt(s, PX(700), PX(310), PX(560), PX(30), "1년 로드맵", size=14.5, bold=True, color=INK)
    _rect(s, PX(700), PX(350), PX(560), PX(404), fill=WHITE, line=LINE, line_w=1.0, radius=0.035)
    rm = [("Q1", "결제 모듈 안정화 · 카카오페이 정기결제"), ("Q2", "MAU 확대 · D7 리텐션 25%+ 도전"),
          ("Q3", "지원사업 DB 자동 수집 · 업종 플레이북 40→100+ · 1차 출처 보강"), ("Q4", "1,000 MAU · Pre-A 라운드 검토")]
    for i, (q, t) in enumerate(rm):
        y = 386 + i * 92
        _txt(s, PX(730), PX(y), PX(74), PX(32), q, size=14.5, bold=True, color=BLUE)
        _txt(s, PX(814), PX(y + 2), PX(424), PX(64), t, size=13, color=SLATE, line_spacing=1.2)
    _txt(s, PX(1304), PX(310), PX(520), PX(30), "팀 SSGI (4인)", size=14.5, bold=True, color=INK)
    _rect(s, PX(1304), PX(350), PX(520), PX(404), fill=WHITE, line=LINE, line_w=1.0, radius=0.035)
    _txt(s, PX(1336), PX(378), PX(460), PX(352),
         "PM·데이터 / 백엔드 / 프론트엔드 / AI — 4인 분업.\n\n* 공고 규정상 개인정보(실명) 미기재.\n  팀 구성·역할만 표기.",
         size=13, color=SLATE, line_spacing=1.5)
    _rect(s, PX(96), PX(780), PX(1728), PX(176), fill=BLUEBG, radius=0.04)
    _txt(s, PX(128), PX(800), PX(1664), PX(140),
         "정직성 — 결제 0건 · 트랙션은 시뮬/베타 단계. LTV/CAC 등은 결제 데이터 확보 후 코호트로 갱신 예정.\nVC·데모데이 재활용 시: Ask 슬라이드(모집 금액·사용처)와 트랙션 추이를 추가합니다.",
         size=14.5, bold=True, color=INK, line_spacing=1.4)
    footer(s, 20, "TAM/SAM/SOM·로드맵·팀은 2차 발표(사업화 심사)에서 상세 전개")

    out = ROOT / "SSGI_상세기획서_심사위원용.pptx"
    prs.save(out)
    print(f"✓ 저장: {out}")
    print(f"  슬라이드: {len(prs.slides)}장 (Manus 디자인 · 표지·목차 2 / 배경 2 / 개요·데이터·AI 3 / 기능 상세 9 / 흐름도·갤러리 2 / UI·UX 1 / 백업 1)")
    return out


if __name__ == "__main__":
    build()
