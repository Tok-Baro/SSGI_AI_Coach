"""알림 서비스.

채널 우선순위 (ADR-004 v2 — 2026-05-07 재정의):
- 1순위: **FCM (Firebase Cloud Messaging)** — Web Push + Android/iOS 모바일 PWA
- 2순위: 카카오톡 "나에게 보내기" — 본인 메모 채널 (사장님이 활성화한 경우만)
- 3순위: silent fail + 로그 (UI에 알림 미수신 안내 표시 권장)

ADR-004 v1 ("Kakao > FCM > silent")의 한계:
- kakao_service.send_to_me는 talk/memo/default/send API로 **본인에게만** 전송
- 친구톡(AlimTalk)/플러스친구는 사업자 채널 인증 필요 (1개월+ 검수 소요)
- v2에서는 FCM 우선으로 도달성 보장. 카카오톡 비즈메시지는 별도 P1로 도입.

NotificationLog는 매 시도마다 channel/status/error 기록 → 운영 모니터링 가능.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.notification import NotificationLog
from app.services.kakao_service import KakaoService
from app.utils.crypto import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)


class NotificationService:
    async def send_notification(
        self,
        user: User,
        title: str,
        message: str,
        message_type: str,
        db: AsyncSession,
        link_url: str = "",
    ) -> bool:
        """
        알림 전송. ADR-004 v2 우선순위: FCM > 카카오톡 메모 > 로그만.

        반환: True = 어느 채널로든 전송 성공, False = 모든 채널 실패
        (호출자는 False 시 UI에 "알림 설정 확인해주세요" 안내 가능)
        """
        channel = "none"
        status = "failed"
        error_message = None

        # 1. FCM 우선 (도달성 보장 — Web Push 등록된 디바이스 모두)
        if user.fcm_token:
            try:
                await self._send_fcm(
                    user.fcm_token, title, message[:100], link_url, message_type
                )
                channel = "fcm"
                status = "sent"
            except Exception as e:
                logger.warning(f"FCM notification failed for user {user.id}: {e}")
                error_message = f"FCM: {e}"

        # 2. 카카오톡 "나에게 보내기" (본인 메모 채널)
        # 주의: send_to_me는 사장님 본인의 카카오톡 채팅 목록에 들어가지만
        # "나에게 보내기" 채널을 활성화·모니터링하지 않으면 미수신과 동등.
        # 친구톡/플러스친구는 사업자 채널 인증 필요 (P1 로드맵).
        if status != "sent":
            kakao_access = decrypt_token(user.kakao_access_token)
            kakao_refresh = decrypt_token(user.kakao_refresh_token)
            if kakao_access:
                try:
                    kakao = KakaoService()
                    text = f"[AI 경영코치] {title}\n\n{message}"
                    result = await kakao.send_to_me(kakao_access, text, link_url)
                    if result:
                        channel = "kakao_memo"
                        status = "sent"
                        error_message = None
                except Exception as e:
                    # 401 시 토큰 갱신 재시도
                    if "401" in str(e) and kakao_refresh:
                        try:
                            new_tokens = await kakao.refresh_token(kakao_refresh)
                            if new_tokens and "access_token" in new_tokens:
                                kakao_access = new_tokens["access_token"]
                                user.kakao_access_token = encrypt_token(kakao_access)
                                if new_tokens.get("refresh_token"):
                                    user.kakao_refresh_token = encrypt_token(new_tokens["refresh_token"])
                                result = await kakao.send_to_me(kakao_access, text, link_url)
                                if result:
                                    channel = "kakao_memo"
                                    status = "sent"
                                    error_message = None
                        except Exception as refresh_err:
                            logger.warning(f"Kakao token refresh failed for user {user.id}: {refresh_err}")
                    if status != "sent":
                        logger.warning(f"Kakao memo notification failed for user {user.id}: {e}")
                        prev = error_message or ""
                        error_message = (prev + f"; Kakao: {e}").lstrip("; ")

        # 3. 모든 채널 실패 — 로그만, 사용자 측 UI 안내 권장
        if status != "sent":
            logger.error(
                f"Notification fully failed for user {user.id}: fcm_token={bool(user.fcm_token)}, "
                f"kakao_access={bool(decrypt_token(user.kakao_access_token))}, error={error_message}"
            )

        # 3. 로그 저장
        log = NotificationLog(
            user_id=user.id,
            channel=channel,
            message_type=message_type,
            title=title,
            message=message,
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow() if status == "sent" else None,
        )
        db.add(log)

        return status == "sent"

    async def _send_fcm(
        self,
        fcm_token: str,
        title: str,
        body: str,
        link_url: str,
        message_type: str,
    ):
        """Firebase Cloud Messaging 전송."""
        try:
            import firebase_admin
            from firebase_admin import messaging

            if not firebase_admin._apps:
                # Firebase 초기화 (서비스 계정 JSON)
                if settings.firebase_service_account_json:
                    cred = firebase_admin.credentials.Certificate(
                        settings.firebase_service_account_json
                    )
                    firebase_admin.initialize_app(cred)
                elif settings.firebase_service_account:
                    import json
                    import base64
                    sa_json = json.loads(
                        base64.b64decode(settings.firebase_service_account).decode()
                    )
                    cred = firebase_admin.credentials.Certificate(sa_json)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning("Firebase not configured, skipping FCM")
                    return

            msg = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={"link_url": link_url, "message_type": message_type},
                token=fcm_token,
            )
            messaging.send(msg)

        except ImportError:
            logger.warning("firebase-admin not installed, skipping FCM")
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            raise
