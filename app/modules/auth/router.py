import uuid

from fastapi import APIRouter, Request, status

from app.api.deps import (
    CurrentUser,
    CurrentUserProfileDep,
    SessionDep,
    get_current_user_profile,
)
from app.core.response import ApiResponse, raise_api_error, success_response
from app.models import (
    BackendMobileCodeLoginRequest,
    BackendPasswordLoginRequest,
    CurrentUserProfile,
    MiniappBindPhoneRequest,
    MiniappCodeLoginRequest,
    MiniappPhoneRelationPublic,
    SwitchCurrentStoreRequest,
    Token,
)
from app.modules.auth.service import (
    authenticate_backend_mobile_code,
    authenticate_backend_password,
    authenticate_miniapp_code,
    bind_miniapp_phone,
    build_access_token,
)
from app.modules.miniapp.service import build_miniapp_phone_relation
from app.modules.org.service import switch_user_primary_store
from app.modules.store.models import Store

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/backend/password-login",
    summary="后台账号密码登录",
    response_model=ApiResponse[Token],
)
def backend_password_login(
    request: Request, session: SessionDep, body: BackendPasswordLoginRequest
):
    user = authenticate_backend_password(
        session=session,
        account=body.account,
        password=body.password,
    )
    token = build_access_token(session=session, user=user)
    return success_response(request, data=token.model_dump(), message="登录成功")


@router.post("/login", summary="兼容旧版后台登录", response_model=ApiResponse[Token])
def login_alias(
    request: Request, session: SessionDep, body: BackendPasswordLoginRequest
):
    """兼容旧版后台登录入口。"""

    return backend_password_login(request=request, session=session, body=body)


@router.post(
    "/backend/mobile-code-login",
    summary="后台手机号验证码登录",
    response_model=ApiResponse[Token],
)
def backend_mobile_code_login(
    request: Request, session: SessionDep, body: BackendMobileCodeLoginRequest
):
    user = authenticate_backend_mobile_code(
        session=session,
        mobile=body.mobile,
        code=body.code,
    )
    token = build_access_token(session=session, user=user)
    return success_response(request, data=token.model_dump(), message="登录成功")


@router.post(
    "/miniapp/code-login",
    summary="小程序登录",
    response_model=ApiResponse[Token],
)
def miniapp_code_login(
    request: Request, session: SessionDep, body: MiniappCodeLoginRequest
):
    user = authenticate_miniapp_code(
        session=session,
        code=body.code,
        app_id=body.app_id,
    )
    token = build_access_token(session=session, user=user)
    return success_response(
        request,
        data=token.model_dump(),
        message="小程序登录成功",
    )


@router.post(
    "/miniapp/bind-phone",
    summary="小程序绑定手机号",
    response_model=ApiResponse[CurrentUserProfile],
)
def miniapp_bind_phone(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    body: MiniappBindPhoneRequest,
):
    if current_user.user_type != "MINI_APP_MEMBER":
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_PERMISSION_DENIED",
            message="当前用户不是小程序用户，无法执行手机号绑定",
        )
    bind_miniapp_phone(
        session=session,
        user=current_user,
        phone=body.phone,
        country_code=body.country_code,
    )
    profile = get_current_user_profile(
        request=request,
        session=session,
        current_user=current_user,
    )
    return success_response(
        request,
        data=profile.model_dump(mode="json"),
        message="绑定手机号成功",
    )


@router.get(
    "/miniapp/phone-related-employees",
    summary="查询手机号关联员工",
    response_model=ApiResponse[MiniappPhoneRelationPublic],
)
def read_miniapp_phone_related_employees(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
):
    if current_user.user_type != "MINI_APP_MEMBER":
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_PERMISSION_DENIED",
            message="当前用户不是小程序用户，无法查看手机号关联员工",
        )
    raw_current_store_id = request.headers.get("X-Current-Store-Id") or request.query_params.get(
        "current_store_id"
    )
    current_store_id: uuid.UUID | None = None
    if raw_current_store_id:
        try:
            current_store_id = uuid.UUID(str(raw_current_store_id))
        except ValueError:
            raise_api_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="current_store_id 不是合法的 UUID",
            )
    relation = build_miniapp_phone_relation(
        session=session,
        user=current_user,
        current_store_id=current_store_id,
    )
    return success_response(
        request,
        data=relation.model_dump(mode="json"),
        message="获取手机号关联员工成功",
    )


@router.get("/me", summary="获取当前用户信息", response_model=ApiResponse[CurrentUserProfile])
def read_current_user(request: Request, profile: CurrentUserProfileDep):
    return success_response(request, data=profile.model_dump(), message="获取当前用户成功")


@router.post(
    "/current-store/switch",
    summary="切换当前门店",
    response_model=ApiResponse[CurrentUserProfile],
)
def switch_current_store(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    body: SwitchCurrentStoreRequest,
):
    try:
        store_id = uuid.UUID(body.store_id)
    except ValueError:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="store_id 不是合法的 UUID",
        )
    if current_user.is_superuser:
        store = session.get(Store, store_id)
        if not store:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="STORE_NOT_FOUND",
                message="目标门店不存在",
            )
        current_user.primary_store_id = store.id
        current_user.primary_department_id = None
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
        profile = get_current_user_profile(
            request=request, session=session, current_user=current_user
        )
        return success_response(
            request,
            data=profile.model_dump(mode="json"),
            message="切换当前门店成功",
        )
    try:
        switch_user_primary_store(
            session=session,
            user=current_user,
            store_id=store_id,
        )
    except ValueError as exc:
        if str(exc) == "USER_NOT_BOUND_TO_STORE":
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户未绑定目标门店，无法切换",
            )
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="目标门店组织信息不存在",
        )
    profile = get_current_user_profile(request=request, session=session, current_user=current_user)
    return success_response(
        request,
        data=profile.model_dump(mode="json"),
        message="切换当前门店成功",
    )
