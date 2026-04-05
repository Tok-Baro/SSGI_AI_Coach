"""알림 서비스: 카카오톡 나에게 보내기 + Firebase FCM."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.notification import NotificationLog
from app.services.kakao_service import KakaoService

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
        알림 전송. 우선순위: 카카오톡 > FCM > 로그만.
        """
        channel = "none"
        status = "failed"
        error_message = None

        # 1. 카카오톡 나에게 보내기
        if user.kakao_access_token:
            try:
                kakao = KakaoService()
                text = f"[AI 경영코치] {title}\n\n{message}"
                result = await kakao.send_to_me(
                    user.kakao_access_token, text, link_url
                )
                if result:
                    channel = "kakao"
                    status = "sent"
            except Exception as e:
                logger.warning(f"Kakao notification failed for user {user.id}: {e}")
                error_message = str(e)

        # 2. Firebase FCM (카카오 실패 시)
        if status != "sent" and user.fcm_token:
            try:
                await self._send_fcm(
                    user.fcm_token, title, message[:100], link_url, message_type
                )
                channel = "fcm"
                status = "sent"
                error_message = None
            except Exception as e:
                logger.warning(f"FCM notification failed for user {user.id}: {e}")
                if error_message:
                    error_message += f"; FCM: {e}"
                else:
                    error_message = str(e)

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
