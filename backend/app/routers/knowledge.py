"""업종 지식팩 조회 API.

- GET /knowledge/industries : 전체 팩 목록 (온보딩 업종 피커용)
- GET /knowledge/my-pack    : 로그인 사용자에게 적용 중인 업종 팩 + 출처 (진단 화면 출처칩용)
"""
from fastapi import APIRouter, Depends

from app.knowledge import registry
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter()


def _sources_payload(pack) -> list[dict]:
    return [{"label": s.label, "url": s.url, "year": s.year} for s in pack.sources]


@router.get("/industries")
async def list_industries() -> list[dict]:
    """등록된 업종 지식팩 목록 (unknown 제외).

    각 항목: id / name / group(부모 pack id, leaf 만) / keywords / priority / status /
            version / reviewed_date / source_count. 프론트는 group 으로 트리를 구성.
    """
    out: list[dict] = []
    for pack_id, pack in sorted(registry.all_packs().items()):
        if pack_id == registry.UNKNOWN_ID:
            continue
        out.append(
            {
                "id": pack.id,
                "name": pack.name,
                "group": pack.group,
                "keywords": pack.match.keywords,
                "priority": pack.match.priority,
                "status": pack.status,
                "version": pack.version,
                "reviewed_date": pack.reviewed_date.isoformat() if pack.reviewed_date else None,
                "source_count": len(pack.sources),
            }
        )
    return out


@router.get("/my-pack")
async def my_pack(current_user: User = Depends(get_current_user)) -> dict:
    """로그인 사용자에게 적용 중인 업종 팩 (industry_slug 우선, 없으면 business_type 분류).

    진단/리포트 화면의 출처칩에 쓴다 — "이 진단은 [name] 플레이북 v{version} · 검수 {reviewed_date} 기준".
    """
    pack = registry.resolve_for(current_user.industry_slug, current_user.business_type)
    return {
        "id": pack.id,
        "name": pack.name,
        "group": pack.group,
        "version": pack.version,
        "reviewed_date": pack.reviewed_date.isoformat() if pack.reviewed_date else None,
        "source_count": len(pack.sources),
        "sources": _sources_payload(pack),
        "is_unknown": pack.id == registry.UNKNOWN_ID,
    }
