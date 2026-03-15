import uuid

from sqlmodel import Session, func, select

from app.models.base import get_datetime_utc
from app.modules.notification.models import Notification


def create_notification(
    *,
    session: Session,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    content: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
    )
    session.add(notification)
    return notification


def list_user_notifications(
    *,
    session: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Notification]:
    statement = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_unread_notifications(*, session: Session, user_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read.is_(False))
    )
    return int(session.exec(statement).one())


def mark_notification_read(
    *, session: Session, notification: Notification
) -> Notification:
    notification.is_read = True
    notification.read_at = get_datetime_utc()
    notification.updated_at = get_datetime_utc()
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification

