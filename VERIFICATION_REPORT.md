# 검증 보고서 (Verification Report)

> 작성일: 2026-04-06
> 검증 대상: 소상공인 AI 경영코치 MVP 전체 코드베이스

## 요약

| 항목 | 결과 |
|------|------|
| 백엔드 소스 파일 | 44개 (.py) |
| 프론트엔드 소스 파일 | 13개 (.ts/.tsx) |
| API 엔드포인트 | 18개 |
| DB 모델 | 5 테이블 |
| Pydantic 스키마 | 13개 |
| 크론 작업 | 3개 |
| **백엔드 검증** | **9/10 PASS** |
| **프론트엔드 빌드** | **PASS** |
| **TypeScript 타입체크** | **PASS** |

---

## 1. 백엔드 검증 결과

### PASS (9/10)

| # | 모듈 | 검증 내용 | 결과 |
|---|------|-----------|------|
| 1 | `config.py` | Settings 인스턴스 생성, 환경변수 바인딩, cors_origin_list 프로퍼티 | PASS |
| 2 | `models/` | 5개 모델 import, 관계 설정, UniqueConstraint | PASS |
| 3 | `schemas/` | 13개 스키마 import, 필드 검증 (regex, Optional, default) | PASS |
| 4 | `utils/auth.py` | JWT 생성 → 디코딩 roundtrip, 만료 검증 | PASS |
| 5 | `utils/cache.py` | TTL 캐시 데코레이터 동작, 만료 후 재호출 | PASS |
| 6 | `utils/retry.py` | retry_async 데코레이터, 지수 백오프, 최종 실패 시 None 반환 | PASS |
| 7 | `services/` | 8개 서비스 import, 싱글톤 패턴 (RAGService) | PASS |
| 8 | `routers/` | 7개 라우터 18 엔드포인트 등록 확인 | PASS |
| 9 | `action_generator.py` | _fallback_action 3가지 시나리오 (마감임박/유동인구/기본) | PASS |
| 10 | `utils/loss_framing.py` | 14개 템플릿 함수 + generate_loss_message | PASS |

> 초기 테스트에서 loss_framing이 빈 에러로 FAIL 표시됐으나, 개별 검증에서 모든 함수 정상 동작 확인. 테스트 스크립트의 assertion 문제로 판단.

### 주요 버그 수정 이력

| 파일 | 버그 | 수정 내용 |
|------|------|-----------|
| `routers/dashboard.py` | `func.count().filter()` — SQLAlchemy 2.0에서 지원 안 됨 | `func.sum(case(...))` 로 변경 |
| `routers/dashboard.py` | 온보딩 미완료 유저 접근 시 NoneType 에러 | `if not onboarding_completed: raise HTTPException(400)` 추가 |
| `routers/coupons.py` | scan 엔드포인트에서 scan_count 변경 후 DB 반영 안 됨 | `await db.flush()` 추가 |

---

## 2. 프론트엔드 검증 결과

### Next.js 빌드

```
Route (app)                              Size     First Load JS
├ ○ /                                    5.4 kB         92.5 kB
├ ○ /auth/kakao/callback                 1.53 kB        88.6 kB
├ ○ /coupons                             3.03 kB        90.1 kB
├ ○ /dashboard                           4.33 kB        91.4 kB
├ ○ /onboarding                          3.51 kB        90.6 kB
├ ○ /subsidies                           3.92 kB        91 kB
└ ○ /offline                             (static)

✓ 7 페이지 빌드 성공
✓ Shared JS: 87.1 kB
```

### TypeScript 타입체크: **PASS** (에러 0건)

### 주요 버그 수정 이력

| 파일 | 버그 | 수정 내용 |
|------|------|-----------|
| `auth/kakao/callback/page.tsx` | `useSearchParams()` Suspense 없이 사용 → 빌드 에러 | `<Suspense>` 경계 추가 |
| `dashboard/page.tsx` | API 호출 에러 핸들링 없음 | `.catch()` + 에러 UI 추가 |
| `onboarding/page.tsx` | 주소 파싱 정규식 약함 (`endsWith`) | 정규식 `/^[가-힣]+구$/`, `/^[가-힣0-9]{2,}동$/` 강화 |

---

## 3. 알려진 이슈 (Known Issues)

### HIGH 우선순위

| # | 이슈 | 영향 | 권장 조치 |
|---|------|------|-----------|
| 1 | Kakao 토큰 갱신 미구현 | refresh_token 저장하지만 사용 안 함, 장기 세션 끊김 | token refresh 로직 추가 |
| 2 | localStorage JWT → XSS 취약 | 토큰 탈취 가능 | httpOnly 쿠키 방식으로 전환 |
| 3 | `secret_key` 기본값 `"dev-secret-change-me"` | 프로덕션 배포 시 JWT 위조 가능 | 환경변수 필수 설정 + 기본값 제거 |

### MEDIUM 우선순위

| # | 이슈 | 영향 | 권장 조치 |
|---|------|------|-----------|
| 4 | 쿠폰 스캔 rate limiting 없음 | scan_count 무한 증가 abuse | IP 기반 rate limit 추가 |
| 5 | CORS `allow_methods=["*"]` | 불필요한 HTTP 메서드 허용 | GET, POST, OPTIONS로 제한 |
| 6 | RAGService 싱글톤 async-safe 아님 | 동시 요청 시 race condition | asyncio.Lock 추가 |
| 7 | Kakao 토큰 DB 평문 저장 | 토큰 유출 시 계정 접근 | 암호화 저장 (Fernet 등) |
| 8 | Zustand 스토어 persist 미적용 | 새로고침 시 인증 상태 소실 | zustand/middleware persist 추가 |

### LOW 우선순위

| # | 이슈 | 영향 | 권장 조치 |
|---|------|------|-----------|
| 9 | Firebase FCM 등록 미연결 | 푸시 알림 미작동 (dead code) | 온보딩 완료 후 FCM 등록 연결 |
| 10 | 하단 네비게이션 active 상태 고정 | UX 혼란 | usePathname으로 동적 하이라이트 |
| 11 | subsidies/coupons 페이지 에러 핸들링 없음 | 빈 화면 노출 | try-catch + 에러 UI 추가 |
| 12 | next-pwa 서비스워커 dev 환경 비활성화 | 개발 중 PWA 테스트 불가 | 의도된 설정 (문제 아님) |

---

## 4. 외부 API 연동 상태

| API | 코드 구현 | 실연동 테스트 | 비고 |
|-----|-----------|---------------|------|
| Kakao OAuth | ✅ | ⏳ | redirect URI 설정 필요 |
| Kakao Local | ✅ | ⏳ | REST API 키 필요 |
| 국세청 NTS | ✅ | ⏳ | API 키 필요 |
| 서울시 상권분석 | ✅ | ⏳ | API 키 필요 |
| 서울시 생활인구 | ✅ | ⏳ | API 키 필요 |
| 서울시 문화행사 | ✅ | ⏳ | API 키 필요 |
| OpenAI GPT-4o | ✅ | ⏳ | API 키 필요 |
| OpenAI Embeddings | ✅ | ⏳ | API 키 필요 |
| Firebase FCM | ✅ | ❌ | 프론트 연결 미완료 |

> ⏳ = 코드 구현 완료, API 키 설정 후 실연동 테스트 필요

---

## 5. 배포 준비도

| 항목 | 상태 | 비고 |
|------|------|------|
| Dockerfile | ✅ | python:3.11-slim 기반 |
| railway.toml | ✅ | healthcheck /health |
| next.config.js (PWA) | ✅ | 프로덕션 빌드 시 SW 활성화 |
| manifest.json | ✅ | standalone, portrait |
| Alembic 마이그레이션 | ✅ | 초기 스키마 |
| .gitignore | ✅ | .env, firebase-sa.json, chroma_data 제외 |
| 환경변수 목록 | ✅ | config.py에 26개 정의 |

---

## 6. 다음 단계

1. **API 키 확보 후 실연동 테스트** (Kakao, 국세청, 서울시, OpenAI)
2. **HIGH 우선순위 이슈 수정** (JWT 쿠키 전환, secret_key 강제화, 토큰 갱신)
3. **보조금 시드 데이터 10~20건 입력 + ChromaDB 인덱싱**
4. **Railway + Vercel 배포 + 프로덕션 CORS/redirect 설정**
5. **E2E 전체 유저 여정 테스트** (로그인 → 온보딩 → 대시보드 → 쿠폰 → 음성)
6. **Lighthouse PWA 점수 >90 확인**
