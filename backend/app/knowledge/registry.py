"""업종 지식팩 레지스트리.

`packs/*.yaml` 을 부팅 시 1회 로드 → `_base` → `group` → `leaf` 순으로 머지 →
검증된 `IndustryPack` 으로 캐시. 자유 텍스트 업종명을 pack id 로 분류한다.

공개 API:
- `resolve(business_type) -> IndustryPack`  : 자유 텍스트 → 해당 팩 (없으면 unknown)
- `classify(business_type) -> str`          : 자유 텍스트 → pack id
- `get(pack_id) -> IndustryPack | None`
- `all_packs() -> dict[str, IndustryPack]`
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from app.knowledge.schema import IndustryPack

PACKS_DIR = Path(__file__).parent / "packs"
BASE_ID = "_base"
UNKNOWN_ID = "unknown"


def _load_raw() -> dict[str, dict]:
    """packs/*.yaml 을 그대로(머지 전) 읽어 {pack_id: dict}."""
    raw: dict[str, dict] = {}
    for f in sorted(PACKS_DIR.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{f.name}: YAML 최상위는 매핑이어야 함")
        pid = str(data.get("id") or f.stem)
        data["id"] = pid
        if pid in raw:
            raise ValueError(f"중복 pack id: {pid}")
        raw[pid] = data
    if BASE_ID not in raw:
        raise ValueError(f"{PACKS_DIR}/_base.yaml 이 필요함")
    if UNKNOWN_ID not in raw:
        raise ValueError(f"{PACKS_DIR}/unknown.yaml 이 필요함")
    return raw


def _deep_merge(base: dict, over: dict) -> dict:
    """dict 는 키 단위 재귀 머지, 그 외(list/스칼라)는 over 가 통째로 교체."""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve(pid: str, raw: dict[str, dict], _chain: tuple[str, ...] = ()) -> dict:
    """pid 팩을 _base → (조상 group...) → 자신 순으로 머지한 dict 반환."""
    if pid in _chain:
        raise ValueError(f"pack 상속 순환: {' -> '.join((*_chain, pid))}")
    if pid not in raw:
        raise ValueError(f"존재하지 않는 부모 pack: {pid}")
    node = raw[pid]
    merged = dict(raw[BASE_ID])
    merged.pop("id", None)  # _base 의 id/name 은 자식 것으로 덮어씀
    merged.pop("name", None)
    parent = node.get("group")
    if parent:
        merged = _deep_merge(merged, _resolve(parent, raw, (*_chain, pid)))
    merged = _deep_merge(merged, node)
    merged["id"] = node["id"]
    merged["name"] = node.get("name") or merged.get("name") or node["id"]
    merged["group"] = node.get("group")
    return merged


@lru_cache(maxsize=1)
def _packs() -> dict[str, IndustryPack]:
    raw = _load_raw()
    out: dict[str, IndustryPack] = {}
    for pid in raw:
        if pid == BASE_ID:
            continue
        out[pid] = IndustryPack(**_resolve(pid, raw))
    return out


def all_packs() -> dict[str, IndustryPack]:
    return dict(_packs())


def get(pack_id: str) -> Optional[IndustryPack]:
    return _packs().get(pack_id)


def classify(business_type: Optional[str]) -> str:
    """자유 텍스트 업종명 → pack id. 매칭 없으면 'unknown'.

    match.priority 오름차순(같으면 id 사전순)으로 검사하여 첫 키워드 매칭 팩을 반환한다.
    (기존 app/utils/industry.py 의 _KEYWORDS 리스트 순서와 동일한 결정 규칙을 재현.)
    """
    if not business_type:
        return UNKNOWN_ID
    text = business_type.strip().lower()
    if not text:
        return UNKNOWN_ID
    packs = _packs()
    for pid in sorted(packs, key=lambda p: (packs[p].match.priority, p)):
        if pid == UNKNOWN_ID:
            continue
        m = packs[pid].match
        if any(ex.lower() in text for ex in m.excludes):
            continue
        if any(kw.lower() in text for kw in m.keywords):
            return pid
    return UNKNOWN_ID


def resolve(business_type: Optional[str]) -> IndustryPack:
    return _packs().get(classify(business_type)) or _packs()[UNKNOWN_ID]


def resolve_for(slug: Optional[str], business_type: Optional[str]) -> IndustryPack:
    """업종 pack id(slug) 를 우선하되, 비어 있거나 더 이상 존재하지 않으면 business_type 으로 분류.

    온보딩에서 저장한 `user.industry_slug` 를 다운스트림에서 쓸 때 사용한다.
    """
    if slug:
        pack = _packs().get(slug)
        if pack is not None:
            return pack
    return resolve(business_type)
