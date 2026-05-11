"""업종 지식팩 스키마 — `packs/*.yaml` 의 구조 정의 (Pydantic v2).

P0 범위: GPT 프롬프트 블록 + marketing_audit 5축 가중치 + PDF 리포트 6축 가중치 +
         KPI 임계값. (= 기존 app/utils/industry.py 하드코딩 딕셔너리를 데이터로 외부화)
P1~ 확장 예정: hero_kpis / channels / copy_tone / seasonal_calendar / subsidy_tags 등.
            → 그때 이 모델에 Optional 필드를 추가하면 됨 (YAML 은 안 쓰면 그만).
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# PDF 리포트 6 카테고리 (합계 = 1.0)
REPORT_KEYS: tuple[str, ...] = (
    "매출 트렌드",
    "보조금 활용",
    "유동인구 활용",
    "경쟁 포지셔닝",
    "코치 활용도",
    "위험도 추세",
)
# marketing_audit 5 차원 (1.0 기준 배율)
AUDIT_KEYS: tuple[str, ...] = ("positioning", "message_fit", "timing", "social_proof", "friction")
# risk_score_engine 7 시그널 (1.0 기준 배율)
RISK_KEYS: tuple[str, ...] = (
    "sales_trend",
    "competition",
    "commercial_vitality",
    "subsidy_urgency",
    "population_trend",
    "action_engagement",
    "business_maturity",
)
VALID_STATUS: tuple[str, ...] = ("active", "draft", "deprecated")
# 마케팅 채널 적합도
FIT_VALUES: tuple[str, ...] = ("high", "medium", "low", "avoid")
# 수치 신뢰도 — measured(출처 있는 확정값) / estimated(업계 평균 기반 추정) / hypothesis(가설, 단정 금지)
CONFIDENCE_VALUES: tuple[str, ...] = ("measured", "estimated", "hypothesis")


class Source(BaseModel):
    """팩 안의 수치/주장 근거 출처."""

    model_config = ConfigDict(extra="forbid")
    label: str
    url: Optional[str] = None
    year: Optional[int] = None


class KPI(BaseModel):
    """업종 핵심 지표 + 양호/주의/위험 구간 (사람-친화 문자열)."""

    model_config = ConfigDict(extra="forbid")
    key: str
    label: str
    unit: str = ""
    good: Optional[str] = None     # "≥ 5,000"
    warn: Optional[str] = None     # "4,000–4,999"
    danger: Optional[str] = None   # "< 4,000"
    confidence: str = "estimated"
    source: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def _check_conf(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(f"confidence 는 {CONFIDENCE_VALUES} 중 하나여야 함 (got {v!r})")
        return v


class Channel(BaseModel):
    """업종 × 마케팅 채널 적합도 / 비용 / 지표. ROI/ROAS 배수는 전부 '가설'."""

    model_config = ConfigDict(extra="forbid")
    key: str
    name: str
    fit: str = "medium"            # high | medium | low | avoid
    applicable: bool = True        # 업종에 아예 무관한 채널이면 False
    entry_cost_won: Optional[int] = None
    monthly_budget_min_won: Optional[int] = None
    monthly_budget_max_won: Optional[int] = None
    fee_pct: Optional[float] = None        # 중개수수료 % (있으면)
    per_unit_cost_won: Optional[float] = None  # 건당 단가 (SMS/알림톡 등)
    primary_metric: str = ""
    roi_note: str = ""             # ROAS 등은 "가설" 톤으로
    confidence: str = "hypothesis"
    source: Optional[str] = None

    @field_validator("fit")
    @classmethod
    def _check_fit(cls, v: str) -> str:
        if v not in FIT_VALUES:
            raise ValueError(f"fit 는 {FIT_VALUES} 중 하나여야 함 (got {v!r})")
        return v

    @field_validator("confidence")
    @classmethod
    def _check_conf(cls, v: str) -> str:
        if v not in CONFIDENCE_VALUES:
            raise ValueError(f"confidence 는 {CONFIDENCE_VALUES} 중 하나여야 함 (got {v!r})")
        return v


class CopyTone(BaseModel):
    """업종별 카피 톤 — 어휘 / 손실 프레임 / 예시 / 권장·금지."""

    model_config = ConfigDict(extra="forbid")
    vocab: list[str] = Field(default_factory=list)
    loss_frames: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    do: list[str] = Field(default_factory=list)
    dont: list[str] = Field(default_factory=list)


class PackMatch(BaseModel):
    """자유 텍스트 업종명 → 이 팩으로 분류하기 위한 규칙."""

    model_config = ConfigDict(extra="forbid")
    priority: int = 100  # 분류 시 검사 순서 (낮을수록 먼저). 관례: leaf < group < 100
    keywords: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)  # 오분류 방지 negative 키워드
    ksic_codes: list[str] = Field(default_factory=list)  # 한국표준산업분류 (P1)
    seoul_business_codes: list[str] = Field(default_factory=list)  # 서울 상권분석 업종코드 (P1)


class IndustryPack(BaseModel):
    """_base → group → leaf 순으로 머지된 '해결된' 업종 지식팩."""

    model_config = ConfigDict(extra="forbid")

    # --- 메타 ---
    id: str
    name: str
    group: Optional[str] = None  # 부모 pack id (leaf 만). null 이면 최상위 군
    status: str = "active"  # active | draft | deprecated
    version: int = 1
    reviewed_date: Optional[date] = None  # 마지막 검수일 (오래되면 프론트에 경고)
    sources: list[Source] = Field(default_factory=list)
    match: PackMatch = Field(default_factory=PackMatch)

    # --- 콘텐츠 ---
    prompt_block: str = ""  # GPT 시스템/유저 프롬프트에 임베드할 "업종 분기 가이드"
    audit_weights: dict[str, float] = Field(default_factory=dict)  # marketing_audit 5 차원 배율
    report_weights: dict[str, float] = Field(default_factory=dict)  # PDF 리포트 6 카테고리, 합 1.0
    risk_signal_weights: dict[str, float] = Field(default_factory=dict)  # risk_score_engine 7 시그널 배율
    kpi_thresholds: dict[str, str] = Field(default_factory=dict)  # 사람-친화 위험 임계값 표 (구버전 — hero_kpis 로 점진 대체)
    hero_kpis: list[KPI] = Field(default_factory=list)  # 구조화 KPI + 양호/주의/위험 구간
    channels: list[Channel] = Field(default_factory=list)  # 마케팅 채널 적합도/비용/지표 — GPT가 이 표 밖 ROI 생성 금지
    copy_tone: CopyTone = Field(default_factory=CopyTone)  # 카피 톤 (어휘/손실프레임/예시/권장·금지)
    subsidy_tags: list[str] = Field(default_factory=list)  # 이 업종이 자격되기 쉬운 지원사업 카테고리 태그
    data_caveats: list[str] = Field(default_factory=list)  # 공공데이터 해석 주의 (예: 정기결제 업종은 결제일에 매출 쏠림 → 요일패턴 곧이곧대로 X)
    # P3~ 확장 예정: seasonal_calendar / commercial_zone_fit / zone_overrides

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_STATUS:
            raise ValueError(f"status 는 {VALID_STATUS} 중 하나여야 함 (got {v!r})")
        return v

    @field_validator("audit_weights")
    @classmethod
    def _check_audit(cls, v: dict[str, float]) -> dict[str, float]:
        if v and set(v) != set(AUDIT_KEYS):
            raise ValueError(f"audit_weights 키는 {AUDIT_KEYS} 여야 함 (got {sorted(v)})")
        return v

    @field_validator("report_weights")
    @classmethod
    def _check_report(cls, v: dict[str, float]) -> dict[str, float]:
        if not v:
            return v
        if set(v) != set(REPORT_KEYS):
            raise ValueError(f"report_weights 키는 {REPORT_KEYS} 여야 함 (got {sorted(v)})")
        total = sum(v.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"report_weights 합은 1.0 이어야 함 (got {total})")
        return v

    @field_validator("risk_signal_weights")
    @classmethod
    def _check_risk(cls, v: dict[str, float]) -> dict[str, float]:
        if v and set(v) != set(RISK_KEYS):
            raise ValueError(f"risk_signal_weights 키는 {RISK_KEYS} 여야 함 (got {sorted(v)})")
        return v
