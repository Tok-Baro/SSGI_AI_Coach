"""업종 지식팩 검증 — backend/app/knowledge/packs/*.yaml 무결성 확인.

확인 항목:
  - YAML 파싱 / id 중복 없음 / _base·unknown 존재
  - 부모(group) 존재 + 상속 순환 없음
  - Pydantic 스키마 (필드/타입/status 값/audit·report 키/report_weights 합 1.0)
  - 경고: status=active 인데 sources 가 비어 있음

사용 (backend/ 에서):
    python -m scripts.validate_packs
"""
from __future__ import annotations

import sys

from app.knowledge import registry


def main() -> int:
    try:
        raw = registry._load_raw()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 팩 로드 실패: {exc}")
        return 1

    try:
        packs = registry.all_packs()  # 머지 + 스키마 검증 (실패 시 예외)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ 팩 검증 실패: {exc}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for pid, pack in packs.items():
        if pack.group and pack.group not in raw:
            errors.append(f"{pid}: 존재하지 않는 group '{pack.group}'")
        if pack.status == "active" and not pack.sources:
            warnings.append(f"{pid}: status=active 인데 sources 가 비어 있음 (출처 추가 권고)")

    for w in warnings:
        print(f"⚠️  {w}")
    if errors:
        for e in errors:
            print(f"❌ {e}")
        return 1

    ids = ", ".join(sorted(packs))
    print(f"✓ 업종 지식팩 {len(packs)}개 검증 통과 — {ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
