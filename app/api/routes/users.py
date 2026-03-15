import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    DataScopeDep,
    SessionDep,
    require_data_scope,
    require_permissions,
)
from app.core.config import settings
from app.core.response import ApiResponse, PageData, raise_api_error, success_response
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ResetUserPassword,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.modules.notification.service import create_notification
from app.modules.org.service import get_user_binding_in_store
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["Users"])


def to_user_public(user: User) -> dict[str, Any]:
    """统一序列化用户公开字段，避免 ORM 表模型直接导出为空。"""

    return UserPublic.model_validate(user).model_dump(mode="json")


def ensure_user_matches_current_store(
    *,
    session: SessionDep,
    user: User,
    current_store_id: uuid.UUID | None,
    message: str,
) -> None:
    if current_store_id is None:
        return
    if user.primary_store_id == current_store_id:
        return
    if get_user_binding_in_store(
        session=session,
        user_id=user.id,
        store_id=current_store_id,
    ):
        return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="DATA_SCOPE_DENIED",
        message=message,
    )


@router.get(
    "/",
    summary="分页查询用户列表",
    dependencies=[Depends(require_permissions("iam.user.read"))],
    response_model=ApiResponse[PageData[UserPublic]],
)
def read_users(request: Request, session: SessionDep, skip: int = 0, limit: int = 100):
    """分页查询用户列表。"""

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    )
    users = session.exec(statement).all()

    data = PageData[dict[str, Any]](
        items=[to_user_public(user) for user in users],
        total=count,
    )
    return success_response(request, data=data.model_dump(), message="获取用户列表成功")


@router.post(
    "/",
    summary="创建用户",
    dependencies=[Depends(require_permissions("iam.user.create"))],
    response_model=ApiResponse[UserPublic],
)
def create_user(request: Request, *, session: SessionDep, user_in: UserCreate):
    """创建用户。"""
    if user_in.email:
        user = crud.get_user_by_email(session=session, email=user_in.email)
        if user:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="USER_EMAIL_EXISTS",
                message="邮箱已存在",
            )
    username_user = crud.get_user_by_username(session=session, username=user_in.username)
    if username_user:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="USER_USERNAME_EXISTS",
            message="登录账号已存在",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return success_response(
        request,
        data=to_user_public(user),
        message="创建用户成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch("/me", summary="更新个人信息", response_model=ApiResponse[UserPublic])
def update_user_me(
    request: Request,
    *,
    session: SessionDep,
    user_in: UserUpdateMe,
    current_user: CurrentUser,
):
    """更新当前登录用户信息。"""

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="USER_EMAIL_EXISTS",
                message="邮箱已存在",
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    create_notification(
        session=session,
        user_id=current_user.id,
        notification_type="PROFILE_UPDATED",
        title="个人信息已更新",
        content="你的个人信息已更新成功。",
    )
    session.commit()
    session.refresh(current_user)
    return success_response(
        request,
        data=to_user_public(current_user),
        message="更新个人信息成功",
    )


@router.patch("/me/password", summary="修改个人密码", response_model=ApiResponse[None])
def update_password_me(
    request: Request,
    *,
    session: SessionDep,
    body: UpdatePassword,
    current_user: CurrentUser,
):
    """修改当前登录用户密码。"""
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="USER_PASSWORD_INVALID",
            message="当前密码错误",
        )
    if body.current_password == body.new_password:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="USER_PASSWORD_UNCHANGED",
            message="新密码不能与旧密码一致",
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    create_notification(
        session=session,
        user_id=current_user.id,
        notification_type="PASSWORD_UPDATED",
        title="密码已修改",
        content="你的登录密码已修改成功。",
    )
    session.commit()
    return success_response(request, message="修改密码成功")


@router.get("/me", summary="获取个人信息", response_model=ApiResponse[UserPublic])
def read_user_me(request: Request, current_user: CurrentUser):
    """获取当前登录用户。"""
    return success_response(
        request,
        data=to_user_public(current_user),
        message="获取个人信息成功",
    )


@router.delete("/me", summary="删除当前用户", response_model=ApiResponse[None])
def delete_user_me(request: Request, session: SessionDep, current_user: CurrentUser):
    """删除当前登录用户。"""
    if current_user.is_superuser:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_DELETE_SELF_FORBIDDEN",
            message="超级管理员不能删除自己",
        )
    session.delete(current_user)
    session.commit()
    return success_response(request, message="删除用户成功")


@router.get("/{user_id}", summary="按 ID 获取用户", response_model=ApiResponse[UserPublic])
def read_user_by_id(
    request: Request, user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
):
    """按 ID 获取用户。"""
    user = session.get(User, user_id)
    if user == current_user:
        return success_response(request, data=to_user_public(user), message="获取用户成功")
    if user is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    require_permissions("iam.user.read")(session, current_user)
    return success_response(request, data=to_user_public(user), message="获取用户成功")


@router.patch(
    "/{user_id}",
    summary="更新指定用户",
    dependencies=[Depends(require_permissions("iam.user.update"))],
    response_model=ApiResponse[UserPublic],
)
def update_user(
    request: Request,
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
):
    """更新指定用户。"""

    db_user = session.get(User, user_id)
    if not db_user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="USER_EMAIL_EXISTS",
                message="邮箱已存在",
            )
    if user_in.username:
        existing_user = crud.get_user_by_username(
            session=session, username=user_in.username
        )
        if existing_user and existing_user.id != user_id:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="USER_USERNAME_EXISTS",
                message="登录账号已存在",
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    create_notification(
        session=session,
        user_id=db_user.id,
        notification_type="PROFILE_CHANGED",
        title="账号信息已被更新",
        content="你的账号资料已被管理员更新，请注意查看最新信息。",
    )
    session.commit()
    return success_response(request, data=to_user_public(db_user), message="更新用户成功")


@router.patch(
    "/{user_id}/reset-password",
    summary="重置指定用户密码",
    dependencies=[Depends(require_permissions("iam.user.update"))],
    response_model=ApiResponse[None],
)
def reset_user_password(
    request: Request,
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    body: ResetUserPassword,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    if db_user.id == current_user.id:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="USER_RESET_SELF_FORBIDDEN",
            message="请使用个人修改密码接口更新自己的密码",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    ensure_user_matches_current_store(
        session=session,
        user=db_user,
        current_store_id=current_store_id,
        message="当前门店上下文不匹配目标用户",
    )
    if not scope.current_user.is_superuser and not scope.allows_user_record(user=db_user):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    db_user.hashed_password = get_password_hash(body.new_password)
    session.add(db_user)
    create_notification(
        session=session,
        user_id=db_user.id,
        notification_type="PASSWORD_RESET",
        title="密码已被重置",
        content="你的登录密码已被管理员重置，请使用新密码登录。",
    )
    session.commit()
    return success_response(request, message="重置密码成功")


@router.delete(
    "/{user_id}",
    summary="删除指定用户",
    dependencies=[
        Depends(require_permissions("iam.user.delete")),
        Depends(require_data_scope(user_param="user_id")),
    ],
    response_model=ApiResponse[None],
)
def delete_user(
    request: Request, session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
):
    """删除指定用户。"""
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    if user == current_user:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_DELETE_SELF_FORBIDDEN",
            message="超级管理员不能删除自己",
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)
    session.delete(user)
    session.commit()
    return success_response(request, message="删除用户成功")
