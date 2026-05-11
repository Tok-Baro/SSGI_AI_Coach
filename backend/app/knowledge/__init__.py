"""업종 지식팩 (Industry Knowledge Packs).

각 업종(군/세부)의 도메인 지식 — GPT 프롬프트 블록, 마케팅 진단 가중치,
PDF 리포트 가중치, KPI 임계값 등 — 을 `packs/*.yaml` 데이터 파일로 외부화한다.
런타임 진입점은 `app.knowledge.registry` (resolve / classify / get / all_packs).

기존 호출부는 `app.utils.industry` 의 호환 shim 함수를 그대로 쓰면 된다.
"""
