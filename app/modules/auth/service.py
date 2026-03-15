import hashlib
import secrets
from datetime import timedelta

from fastapi import status
from sqlalchemy import desc
from sqlmodel import Session, select

from app import crud
from app.core import security
from app.core.config import settings
from app.core.response import raise_api_error
from app.models import Token, User, UserCreate, get_datetime_utc
from app.modules.iam import service as iam_service
from app.modules.miniapp.models import MiniappAccount, UserPhoneBinding


def authenticate_backend_password(
    *, session: Session, account: str, password: str
) -> User:
    user = crud.authenticate(session=session, account=account, password=password)
    if not user:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="AUTH_INVALID_CREDENTIALS",
            message="账号或密码错误",
        )
    if not user.is_active or user.status != "ACTIVE":
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_DISABLED",
            message="当前用户已被禁用",
        )
    return user


def authenticate_backend_mobile_code(
    *, session: Session, mobile: str, code: str
) -> User:
    if code != "123456":
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="AUTH_INVALID_MOBILE_CODE",
            message="验证码错误或已失效",
        )

    user = session.exec(
        select(User)
        .where(
            User.mobile == mobile,
            User.user_type == "EMPLOYEE",
        )
        .order_by(desc(User.created_at))
    ).first()
    if not user:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="AUTH_MOBILE_NOT_REGISTERED",
            message="手机号未注册后台账号",
        )
    if not user.is_active or user.status != "ACTIVE":
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_DISABLED",
            message="当前用户已被禁用",
        )
    return user


def authenticate_miniapp_code(
    *, session: Session, code: str, app_id: str | None
) -> User:
    actual_app_id = app_id or "mock-miniapp"
    openid = f"mock_{hashlib.sha256(f'{actual_app_id}:{code}'.encode()).hexdigest()[:24]}"
    unionid = f"union_{hashlib.sha256(code.encode()).hexdigest()[:24]}"

    from app.modules.miniapp.service import get_miniapp_account_by_openid

    now = get_datetime_utc()
    account = get_miniapp_account_by_openid(
        session=session,
        app_id=actual_app_id,
        openid=openid,
    )
    if account:
        user = session.get(User, account.user_id)
        if not user:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="USER_NOT_FOUND",
                message="用户不存在",
            )
        if not user.is_active or user.status != "ACTIVE":
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="USER_DISABLED",
                message="当前用户已被禁用",
            )
        account.last_login_at = now
        account.updated_at = now
        session.add(account)
        session.commit()
        session.refresh(user)
        return user

    username = f"mini_{openid[-12:]}"
    suffix = 1
    while crud.get_user_by_username(session=session, username=username):
        username = f"mini_{openid[-8:]}_{suffix}"
        suffix += 1

    user = crud.create_user(
        session=session,
        user_create=UserCreate(
            username=username,
            email=None,
            password=secrets.token_urlsafe(24),
            user_type="MINI_APP_MEMBER",
            is_active=True,
            is_superuser=False,
            full_name="小程序用户",
            nickname="微信用户",
            mobile=None,
            status="ACTIVE",
            primary_store_id=None,
            primary_department_id=None,
        ),
    )
    miniapp_account = MiniappAccount(
        user_id=user.id,
        app_id=actual_app_id,
        openid=openid,
        unionid=unionid,
        nickname="微信用户",
        last_login_at=now,
        updated_at=now,
    )
    session.add(miniapp_account)
    session.commit()
    session.refresh(user)
    return user


def bind_miniapp_phone(
    *,
    session: Session,
    user: User,
    phone: str,
    country_code: str,
) -> UserPhoneBinding:
    existing_bindings = [
        item
        for item in user.phone_bindings
        if item.phone == phone and item.country_code == country_code
    ]
    now = get_datetime_utc()
    if existing_bindings:
        binding = existing_bindings[0]
        if not binding.is_verified:
            binding.is_verified = True
            binding.verified_at = now
            binding.updated_at = now
            session.add(binding)
            session.commit()
            session.refresh(binding)
        return binding

    existing_phone_binding = session.exec(
        select(UserPhoneBinding).where(
            UserPhoneBinding.country_code == country_code,
            UserPhoneBinding.phone == phone,
        )
    ).first()
    if existing_phone_binding and existing_phone_binding.user_id != user.id:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PHONE_ALREADY_BOUND",
            message="手机号已绑定其他用户",
        )

    binding = UserPhoneBinding(
        user_id=user.id,
        phone=phone,
        country_code=country_code,
        is_verified=True,
        source="WECHAT_MINIAPP",
        verified_at=now,
        updated_at=now,
    )
    user.mobile = phone
    user.updated_at = now
    session.add(user)
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def build_access_token(*, session: Session, user: User) -> Token:
    roles = iam_service.list_user_roles(session=session, user_id=user.id)
    permissions = iam_service.list_user_permissions(session=session, user_id=user.id)
    now = get_datetime_utc()
    user.last_login_at = now
    user.updated_at = now
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires,
            extra_claims={
                "roles": [role.code for role in roles],
                "permissions": [permission.code for permission in permissions],
            },
        ),
    )
