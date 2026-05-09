# Priority 1 + 2 검증 리포트

검증일: 2026-05-07 / 라이브 백엔드 로그 7305줄 + 코드 직접 확인 / curl 샌드박스 차단으로 로그 분석으로 대체

## 1. 코드 변경 7건 모두 OK

| # | 검사 | 상태 | 증거 |
|---|---|:---:|---|
| 1 | `app/utils/auth.py:get_current_user` 로컬 세션 | ✅ | L53-67, `async with async_session_factory()` 내부 처리 후 close |
| 2 | `app/routers/auth.py:register_fcm_token` `db.add(current_user)` | ✅ | L158, fcm_token 변경 직전 |
| 3 | `app/routers/onboarding.py` 두 라우트 재부착 | ✅ | L52, L139 step 0에 `db.add(current_user)` |
| 4 | `app/services/kakao_service.py:get_token` `asyncio.wait_for(12s)` | ✅ | L42-70, httpx Timeout(connect=5,read=8) + outer 12s, retry 없음 |
| 5 | `app/services/seoul_api_service.py:_load_trdar_mapping` Lock + double-check | ✅ | L19-60, fast-path L27, slow-path 재확인 L32 |
| 6 | `app/routers/dashboard.py` phased pattern | ✅ | L50-134 Phase A / L137-145 Phase B / L147+ Phase C |
| 7 | `app/routers/insights.py /competition + /survival-score` phased | ✅ | competition L106-197, survival L1280-1453 |

## 2. 백엔드 라이브 검증

- `kakao_callback` 단계별 타임스탬프 로그 분석 (7305줄):
  - 토큰 교환 0.13s → 사용자 정보 0.23s → DB select 0.25s → JWT 발급 0.25s
  - **end-to-end 0.25s** (이전 24초 hang 완전 해소 확인)
- 한 차례 `invalid_grant` 400 발생 시 0.5s 미만에 정상 반환 (retry 제거 효과)
- TimeoutError·hard-timeout·500 0건
- `/insights/competition`, `/insights/marketing`, `/insights/deep-report`, `/subsidies/matches` 모두 200 OK 캐시 hit 시 ms 단위

## 3. 잔존 병목 (영향도 순)

### Hot — DB 세션이 외부 fanout 내내 점유됨

| 위치 | 패턴 | 영향 |
|---|---|---|
| `insights.py:201-253` `/deep-report` | `Depends(get_db)` + 14-coroutine gather (Seoul 9 + weather + cultural + RAG + Kakao 2) | 가장 큰 fanout. RAG가 gather 안에 있어 리팩터 까다로움 |
| `insights.py:714-755` `/marketing` | `Depends(get_db)` + 8-way gather + sequential `get_sales_detail` + GPT-4o | 10-30s 세션 점유 |
| `insights.py:1086-1125` `/menu-strategy` | `Depends(get_db)` + 5-way gather + GPT-4o | 동일 패턴 |
| `onboarding.py:124+` `/complete` | `Depends(get_db)` + Seoul gather + RAG + ActionGenerator | 사용자 한 번만 호출되지만 여전히 anti-pattern |

### Warm — N+1 / 순차 호출

- `social_proof_service.get_message` 가 `count(*) WHERE dong_name='삼선동'` 를 **10회 순차 실행** (로그 L7127-7197 확인). dashboard Phase A 내부에서. → `GROUP BY business_type` 한 번으로 합치기
- `kakao_service.py:114-135` `get_radius_competitor_summary` 가 8개 카테고리 코드를 `for` 순차. → `asyncio.gather` 로 8× → 1× RTT

## 4. 발견된 새 버그

### 🔴 `insights.py:811-814` 키 mismatch

```python
gender.get("남성_매출", 0)   # 실제 응답엔 없음
gender.get("여성_매출", 0)   # 실제 응답엔 없음
```

`seoul_api_service.get_sales_detail` (L666-671) 가 emit하는 키는:
- `남성_비중`, `여성_비중`, `남성_건수비중`, `여성_건수비중`

→ GPT-4o 마케팅 프롬프트에 항상 `남성 0% / 여성 0%` 가 들어감. 에러 없이 마케팅 결과 품질 저하.

### 🟡 `dashboard.py` Phase A 가 ChromaDB I/O 동안 PG 커넥션 점유
RAG 벡터 검색이 `async with async_session_factory()` 안에서 실행 중. 항목 1보다 우선순위 낮지만 다음 패스에서 분리 권장.

### ⚪ `auth.py:kakao_callback` 은 여전히 `Depends(get_db)` 사용
DB 블록이 작고(L83-103) fanout 없어 0.25s 끝남. 그대로 둬도 무방.

## 5. 다음 픽스 우선순위

1. `/deep-report` + `onboarding.py:complete_onboarding` phased 패턴화 (가장 큰 fanout × 가장 긴 hold)
2. `/marketing` + `/menu-strategy` 동일 템플릿 적용
3. `social_proof_service` 10× count N+1 → 단일 GROUP BY
4. `KakaoService.get_radius_competitor_summary` `asyncio.gather` 병렬
5. 프로세스 수명 공유 `httpx.AsyncClient` 도입 (현재 매 호출 새 TCP+TLS)
6. `_trdar_mapping` 디스크 JSON 24h TTL 영속화 (uvicorn reload 시 cold-fetch)
7. `insights.py:811-814` `남성_매출`/`여성_매출` 키 mismatch 수정
8. SQLAlchemy pool size + overflow 증설 (1-2 완료 후)

## 결론

P1+P2 핫픽스는 작동 — kakao_callback 24s → 0.25s. 이제 P3~P8 항목들이 다음 라운드의 우선순위.
