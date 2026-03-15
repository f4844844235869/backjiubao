import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.models import (
    DataScopePublic,
    Role,
    RolePublic,
    User,
    UserCreate,
    UserDataScope,
    UserPublic,
)
from app.modules.employee.models import (
    EmployeeEmploymentRecordPublic,
    EmployeeLeaveRequest,
    EmployeeOnboardingRequest,
    EmployeeOnboardingResult,
    EmployeeProfilePublic,
)
from app.modules.employee.service import (
    create_employment_record,
    generate_employee_no,
    get_employee_profile_by_user_id,
    list_employment_records_by_user_id,
    mark_employee_left,
    update_employee_profile,
)
from app.modules.iam import service as iam_service
from app.modules.org.models import OrgNode, UserOrgBinding, UserOrgBindingPublic
from app.modules.org.service import (
    clear_primary_binding,
    get_user_binding_in_store,
    sync_user_primary_org,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


def _ensure_user_matches_current_store(
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


def _ensure_permission(
    *,
    current_user: User,
    required_code: str,
    permission_codes: set[str],
) -> None:
    if current_user.is_superuser:
        return
    if required_code in permission_codes:
        return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="AUTH_PERMISSION_DENIED",
        message=f"缺少权限：{required_code}",
    )


def _ensure_scope(
    *,
    scope: DataScopeDep,
    store_id: uuid.UUID | None = None,
    org_node_id: uuid.UUID | None = None,
) -> None:
    if scope.allows(store_id=store_id, org_node_id=org_node_id):
        return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="DATA_SCOPE_DENIED",
        message="当前用户数据范围不足",
    )


@router.get(
    "/{user_id}/profile",
    summary="获取员工档案",
    dependencies=[Depends(require_permissions("employee.read"))],
    response_model=ApiResponse[EmployeeProfilePublic],
)
def read_employee_profile(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    _ensure_user_matches_current_store(
        session=session,
        user=user,
        current_store_id=current_store_id,
        message="当前门店上下文不匹配目标员工",
    )
    if not scope.current_user.is_superuser and not scope.allows_user_record(user=user):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    profile = get_employee_profile_by_user_id(session=session, user_id=user_id)
    if not profile:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EMPLOYEE_PROFILE_NOT_FOUND",
            message="员工档案不存在",
        )
    return success_response(
        request,
        data=profile.model_dump(),
        message="获取员工档案成功",
    )


@router.get(
    "/{user_id}/employment-records",
    summary="获取员工任职记录",
    dependencies=[Depends(require_permissions("employee.read"))],
    response_model=ApiResponse[list[EmployeeEmploymentRecordPublic]],
)
def read_employee_employment_records(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    _ensure_user_matches_current_store(
        session=session,
        user=user,
        current_store_id=current_store_id,
        message="当前门店上下文不匹配目标员工",
    )
    if not scope.current_user.is_superuser and not scope.allows_user_record(user=user):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    records = list_employment_records_by_user_id(session=session, user_id=user_id)
    return success_response(
        request,
        data=[item.model_dump(mode="json") for item in records],
        message="获取员工任职记录成功",
    )


@router.post(
    "/{user_id}/leave",
    summary="办理员工离职",
    dependencies=[Depends(require_permissions("employee.leave"))],
    response_model=ApiResponse[EmployeeProfilePublic],
)
def leave_employee(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    body: EmployeeLeaveRequest,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    _ensure_user_matches_current_store(
        session=session,
        user=user,
        current_store_id=current_store_id,
        message="当前门店上下文不匹配目标员工",
    )
    if not scope.current_user.is_superuser and not scope.allows_user_record(user=user):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    profile = get_employee_profile_by_user_id(session=session, user_id=user_id)
    if not profile:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EMPLOYEE_PROFILE_NOT_FOUND",
            message="员工档案不存在",
        )
    if profile.employment_status == "LEFT":
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="EMPLOYEE_ALREADY_LEFT",
            message="员工已离职，无需重复操作",
        )
    profile = mark_employee_left(
        session=session,
        user=user,
        profile=profile,
        left_at=body.left_at,
        leave_reason=body.leave_reason,
    )
    return success_response(
        request,
        data=profile.model_dump(mode="json"),
        message="员工离职成功",
    )


@router.post(
    "/onboard",
    summary="办理员工入职",
    dependencies=[Depends(require_permissions("employee.create"))],
    response_model=ApiResponse[EmployeeOnboardingResult],
)
def onboard_employee(
    request: Request,
    session: SessionDep,
    body: EmployeeOnboardingRequest,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    current_store_id = scope.resolve_current_store_id(request=request)
    permission_codes = {
        item.code
        for item in iam_service.list_user_permissions(
            session=session, user_id=current_user.id
        )
    }
    org_node = session.get(OrgNode, body.primary_org_node_id)
    if not org_node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    if current_store_id and org_node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许在其他门店办理入职",
        )

    _ensure_permission(
        current_user=current_user,
        required_code="employee.bind_org",
        permission_codes=permission_codes,
    )
    _ensure_scope(scope=scope, store_id=org_node.store_id, org_node_id=org_node.id)

    if body.user.email:
        existing_email_user = crud.get_user_by_email(session=session, email=body.user.email)
        if existing_email_user:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="USER_EMAIL_EXISTS",
                message="邮箱已存在",
            )
    existing_username_user = crud.get_user_by_username(
        session=session, username=body.user.username
    )
    if existing_username_user:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="USER_USERNAME_EXISTS",
            message="登录账号已存在",
        )
    role_ids = body.role_ids
    roles: list[Role] = []
    if role_ids:
        _ensure_permission(
            current_user=current_user,
            required_code="employee.assign_role",
            permission_codes=permission_codes,
        )
        roles = list(session.exec(select(Role).where(Role.id.in_(role_ids))).all())
        if len(roles) != len(set(role_ids)):
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ROLE_NOT_FOUND",
                message="存在未找到的角色",
            )

    if body.scopes:
        _ensure_permission(
            current_user=current_user,
            required_code="employee.assign_scope",
            permission_codes=permission_codes,
        )
        for item in body.scopes:
            _ensure_scope(
                scope=scope,
                store_id=item.store_id or org_node.store_id,
                org_node_id=item.org_node_id,
            )

    employee_no = generate_employee_no(session=session, org_node=org_node)

    user = crud.create_user(
        session=session,
        user_create=UserCreate(
            user_type="EMPLOYEE",
            username=body.user.username,
            email=body.user.email,
            password=body.user.password,
            full_name=body.user.full_name,
            nickname=body.user.nickname,
            mobile=body.user.mobile,
            is_active=True,
            is_superuser=False,
            status="ACTIVE",
            primary_store_id=None,
            primary_department_id=None,
        ),
    )
    profile = get_employee_profile_by_user_id(session=session, user_id=user.id)
    if not profile:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="EMPLOYEE_PROFILE_NOT_FOUND",
            message="员工档案创建失败",
        )
    profile = update_employee_profile(
        session=session,
        profile=profile,
        employee_no=employee_no,
        hired_at=body.hired_at,
    )

    clear_primary_binding(session=session, user_id=user.id)
    sync_user_primary_org(session=session, user=user, org_node=org_node)
    binding = UserOrgBinding(
        user_id=user.id,
        org_node_id=org_node.id,
        is_primary=True,
        position_name=body.position_name,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    create_employment_record(
        session=session,
        user_id=user.id,
        employee_no=profile.employee_no,
        hired_at=profile.hired_at,
        store_id=org_node.store_id,
        org_node_id=org_node.id,
        position_name=body.position_name,
    )

    saved_roles = []
    if role_ids:
        iam_service.replace_user_roles(session=session, user_id=user.id, role_ids=role_ids)
        saved_roles = list(session.exec(select(Role).where(Role.id.in_(role_ids))).all())

    saved_scopes = []
    if body.scopes:
        scope_models = [
            UserDataScope(
                user_id=user.id,
                scope_type=item.scope_type,
                store_id=item.store_id,
                org_node_id=item.org_node_id,
            )
            for item in body.scopes
        ]
        saved_scopes = iam_service.replace_user_data_scopes(
            session=session,
            user_id=user.id,
            scopes=scope_models,
        )

    result = EmployeeOnboardingResult(
        user=UserPublic.model_validate(user),
        profile=EmployeeProfilePublic.model_validate(profile),
        primary_binding=UserOrgBindingPublic.model_validate(binding),
        roles=[RolePublic.model_validate(role).model_dump(mode="json") for role in saved_roles],
        data_scopes=[
            DataScopePublic(
                scope_type=item.scope_type,
                store_id=item.store_id,
                org_node_id=item.org_node_id,
            )
            for item in saved_scopes
        ],
    )
    return success_response(
        request,
        data=result.model_dump(mode="json"),
        message="员工入职成功",
        status_code=status.HTTP_201_CREATED,
    )
