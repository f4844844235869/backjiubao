import uuid

from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, SessionDep
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.notification.models import (
    Notification,
    NotificationListResponse,
    NotificationPublic,
)
from app.modules.notification.service import (
    count_unread_notifications,
    list_user_notifications,
    mark_notification_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/me",
    summary="获取我的通知列表",
    response_model=ApiResponse[NotificationListResponse],
)
def read_my_notifications(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
):
    notifications = list_user_notifications(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    unread_count = count_unread_notifications(session=session, user_id=current_user.id)
    return success_response(
        request,
        data=NotificationListResponse(
            items=[
                NotificationPublic.model_validate(item).model_dump(mode="json")
                for item in notifications
            ],
            unread_count=unread_count,
        ).model_dump(mode="json"),
        message="获取通知成功",
    )


@router.patch(
    "/{notification_id}/read",
    summary="确认已读通知",
    response_model=ApiResponse[NotificationPublic],
)
def read_notification(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    notification_id: uuid.UUID,
):
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOTIFICATION_NOT_FOUND",
            message="通知不存在",
        )
    updated = notification
    if not notification.is_read:
        updated = mark_notification_read(session=session, notification=notification)
    return success_response(
        request,
        data=NotificationPublic.model_validate(updated).model_dump(mode="json"),
        message="确认已读成功",
    )
