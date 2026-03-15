import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core import security
from app.core.config import settings
from app.models import MiniappAccount, User, UserCreate, UserDataScope, UserPhoneBinding
from app.modules.employee import service as employee_service
from app.modules.org.models import OrgNode, UserOrgBinding
from app.modules.store.models import Store
from tests.utils.utils import random_email, random_lower_string


def test_login_success_returns_standard_response(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={
            "account": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "登录成功"
    assert payload["data"]["access_token"]
    assert payload["data"]["token_type"] == "bearer"
    assert payload["trace_id"]


def test_login_failure_returns_standard_error(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": settings.FIRST_SUPERUSER, "password": "wrong-password"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "AUTH_INVALID_CREDENTIALS"
    assert payload["message"] == "账号或密码错误"
    assert payload["data"] is None
    assert payload["trace_id"]


def test_login_supports_username(client: TestClient, db: Session) -> None:
    username = random_lower_string()
    password = "viewer12345"
    user = UserCreate(
        username=username,
        email=random_email(),
        password=password,
        is_superuser=False,
        is_active=True,
    )
    from app import crud

    crud.create_user(session=db, user_create=user)

    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": username, "password": password},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["access_token"]


def test_get_current_user_profile(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "获取当前用户成功"
    assert payload["data"]["email"] == settings.FIRST_SUPERUSER
    assert "admin" in payload["data"]["roles"]
    assert payload["data"]["permissions"]
    assert "org.store.read" in payload["data"]["permissions"]
    assert "iam.role.read" in payload["data"]["permissions"]
    assert payload["data"]["data_scopes"]
    assert payload["data"]["data_scopes"][0]["scope_type"] == "ALL"
    assert "accessible_stores" in payload["data"]


def test_get_current_user_profile_returns_store_memberships(
    client: TestClient, db: Session
) -> None:
    store = Store(code=f"store_{random_lower_string()[:8]}", name="望京店", status="ACTIVE")
    db.add(store)
    db.commit()
    db.refresh(store)

    org_node = OrgNode(
        store_id=store.id,
        parent_id=None,
        name="望京店前厅部",
        node_type="DEPARTMENT",
        path="",
        level=0,
        sort_order=1,
        is_active=True,
    )
    db.add(org_node)
    db.commit()
    org_node.path = str(org_node.id)
    db.add(org_node)
    db.commit()
    db.refresh(org_node)

    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="门店员工",
            mobile="13800000901",
            is_superuser=False,
            is_active=True,
            primary_store_id=store.id,
            primary_department_id=org_node.id,
        ),
    )
    employee_service.ensure_employee_profile(session=db, user=user)
    binding = UserOrgBinding(
        user_id=user.id,
        org_node_id=org_node.id,
        is_primary=True,
        position_name="值班经理",
    )
    db.add(binding)
    db.commit()

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": user.username, "password": "password1234"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["current_store_id"] == str(store.id)
    assert payload["current_store_name"] == "望京店"
    assert payload["current_org_node_id"] == str(org_node.id)
    assert payload["current_org_node_name"] == "望京店前厅部"
    assert payload["primary_store_name"] == "望京店"
    assert payload["primary_department_name"] == "望京店前厅部"
    assert payload["role_names"] == []
    assert payload["permission_names"] == []
    assert payload["data_scope_labels"] == []
    assert payload["store_memberships"] == [
        {
            "store_id": str(store.id),
            "store_name": "望京店",
            "org_node_id": str(org_node.id),
            "org_node_name": "望京店前厅部",
            "position_name": "值班经理",
            "is_primary": True,
            "is_current": True,
        }
    ]
    assert payload["store_memberships"][0]["store_name"] == "望京店"
    assert payload["store_memberships"][0]["org_node_name"] == "望京店前厅部"


def test_get_current_user_profile_includes_store_memberships_field_for_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert "store_memberships" in payload
    assert isinstance(payload["store_memberships"], list)
    assert "accessible_stores" in payload
    assert isinstance(payload["accessible_stores"], list)


def test_get_current_user_profile_clears_missing_current_store_context(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    admin = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    assert admin is not None
    admin.primary_store_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    admin.primary_department_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    db.add(admin)
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["current_store_id"] is None
    assert payload["current_store_name"] is None
    assert payload["current_org_node_id"] is None


def test_get_current_user_profile_returns_accessible_stores_for_superuser(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store_a = Store(code=f"super_a_{random_lower_string()[:8]}", name="超管一号店", status="ACTIVE")
    store_b = Store(code=f"super_b_{random_lower_string()[:8]}", name="超管二号店", status="ACTIVE")
    db.add(store_a)
    db.add(store_b)
    db.commit()
    db.refresh(store_a)
    db.refresh(store_b)

    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    accessible_store_ids = {item["store_id"] for item in payload["accessible_stores"]}
    assert str(store_a.id) in accessible_store_ids
    assert str(store_b.id) in accessible_store_ids
    assert payload["role_names"] == ["系统管理员"]
    assert "查看门店" in payload["permission_names"]
    assert "全部数据" in payload["data_scope_labels"]
    assert payload["data_scopes"][0]["scope_label"] == "全部数据"


def test_superuser_can_switch_current_store_without_membership(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = Store(code=f"super_switch_{random_lower_string()[:8]}", name="超管切店测试店", status="ACTIVE")
    db.add(store)
    db.commit()
    db.refresh(store)
    org_node = OrgNode(
        store_id=store.id,
        parent_id=None,
        name="超管切店默认组织",
        prefix="QG",
        node_type="DEPARTMENT",
        path="",
        level=1,
        sort_order=1,
        is_active=True,
    )
    db.add(org_node)
    db.commit()
    org_node.path = f"/{store.id}/{org_node.id}"
    db.add(org_node)
    db.commit()
    db.refresh(org_node)

    switch_response = client.post(
        f"{settings.API_V1_STR}/auth/current-store/switch",
        headers=superuser_token_headers,
        json={"store_id": str(store.id)},
    )

    assert switch_response.status_code == 200
    payload = switch_response.json()["data"]
    assert payload["current_store_id"] == str(store.id)
    assert payload["current_store_name"] == "超管切店测试店"
    assert payload["current_org_node_id"] == str(org_node.id)
    assert payload["current_org_node_name"] == "超管切店默认组织"
    matched_store = next(
        item for item in payload["accessible_stores"] if item["store_id"] == str(store.id)
    )
    assert matched_store["store_name"] == "超管切店测试店"
    assert matched_store["is_current"] is True


def test_normal_user_without_org_binding_keeps_current_org_node_empty(
    client: TestClient, db: Session
) -> None:
    store = Store(code=f"plain_store_{random_lower_string()[:8]}", name="无绑定门店", status="ACTIVE")
    db.add(store)
    db.commit()
    db.refresh(store)

    org_node = OrgNode(
        store_id=store.id,
        parent_id=None,
        name="无绑定默认组织",
        prefix="WB",
        node_type="DEPARTMENT",
        path="",
        level=1,
        sort_order=1,
        is_active=True,
    )
    db.add(org_node)
    db.commit()
    org_node.path = f"/{store.id}/{org_node.id}"
    db.add(org_node)
    db.commit()

    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="无组织绑定员工",
            mobile="13800000919",
            is_superuser=False,
            is_active=True,
            primary_store_id=store.id,
            primary_department_id=None,
        ),
    )
    employee_service.ensure_employee_profile(session=db, user=user)

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": user.username, "password": "password1234"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["current_store_id"] == str(store.id)
    assert payload["current_store_name"] == "无绑定门店"
    assert payload["current_org_node_id"] is None
    assert payload["current_org_node_name"] is None


def test_get_current_user_profile_marks_current_store_membership_by_store_id(
    client: TestClient, db: Session
) -> None:
    store_a = Store(code=f"store_a_{random_lower_string()[:8]}", name="国贸店", status="ACTIVE")
    store_b = Store(code=f"store_b_{random_lower_string()[:8]}", name="三里屯店", status="ACTIVE")
    db.add(store_a)
    db.add(store_b)
    db.commit()
    db.refresh(store_a)
    db.refresh(store_b)

    org_a = OrgNode(
        store_id=store_a.id,
        parent_id=None,
        name="国贸店前厅部",
        node_type="DEPARTMENT",
        path="",
        level=0,
        sort_order=1,
        is_active=True,
    )
    org_b = OrgNode(
        store_id=store_b.id,
        parent_id=None,
        name="三里屯店前厅部",
        node_type="DEPARTMENT",
        path="",
        level=0,
        sort_order=1,
        is_active=True,
    )
    db.add(org_a)
    db.add(org_b)
    db.commit()
    org_a.path = str(org_a.id)
    org_b.path = str(org_b.id)
    db.add(org_a)
    db.add(org_b)
    db.commit()
    db.refresh(org_a)
    db.refresh(org_b)

    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="多门店员工",
            mobile="13800000902",
            is_superuser=False,
            is_active=True,
            primary_store_id=store_a.id,
            primary_department_id=org_a.id,
        ),
    )
    employee_service.ensure_employee_profile(session=db, user=user)
    binding_a = UserOrgBinding(
        user_id=user.id,
        org_node_id=org_a.id,
        is_primary=True,
        position_name="店长",
    )
    binding_b = UserOrgBinding(
        user_id=user.id,
        org_node_id=org_b.id,
        is_primary=False,
        position_name="巡店主管",
    )
    db.add(binding_a)
    db.add(binding_b)
    db.add(
        UserDataScope(user_id=user.id, scope_type="STORE", store_id=store_a.id, org_node_id=None)
    )
    db.add(
        UserDataScope(user_id=user.id, scope_type="STORE", store_id=store_b.id, org_node_id=None)
    )
    db.commit()

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": user.username, "password": "password1234"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    default_response = client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert default_response.status_code == 200
    default_memberships = {
        item["store_id"]: item for item in default_response.json()["data"]["store_memberships"]
    }
    assert default_memberships[str(store_a.id)]["is_current"] is True
    assert default_memberships[str(store_b.id)]["is_current"] is False

    switched_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={**headers, "X-Current-Store-Id": str(store_b.id)},
    )
    assert switched_response.status_code == 200
    switched_payload = switched_response.json()["data"]
    switched_memberships = {
        item["store_id"]: item for item in switched_payload["store_memberships"]
    }
    assert switched_payload["current_store_id"] == str(store_b.id)
    assert switched_memberships[str(store_a.id)]["is_current"] is False
    assert switched_memberships[str(store_b.id)]["is_current"] is True
    assert switched_memberships[str(store_b.id)]["store_name"] == "三里屯店"


def test_get_current_user_profile_without_token(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/auth/me")

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "AUTH_INVALID_TOKEN"
    assert payload["message"] == "未登录或登录状态已过期"
    assert payload["trace_id"]


def test_get_current_user_profile_with_invalid_token(client: TestClient) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "AUTH_INVALID_TOKEN"
    assert payload["message"] == "登录状态无效或已过期"
    assert payload["trace_id"]


def test_get_current_user_profile_with_expired_token(client: TestClient) -> None:
    expired_token = security.create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        expires_delta=timedelta(minutes=-1),
    )
    response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "AUTH_INVALID_TOKEN"
    assert payload["message"] == "登录状态无效或已过期"
    assert payload["trace_id"]


def test_login_validation_error(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": settings.FIRST_SUPERUSER},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert payload["message"] == "请求参数校验失败"
    assert payload["data"]["errors"][0]["field"] == "body.password"
    assert payload["data"]["errors"][0]["reason"] == "字段不能为空"


def test_login_alias_keeps_backward_compatibility(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "account": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["access_token"]


def test_backend_mobile_code_login_success(client: TestClient, db: Session) -> None:
    from app import crud

    crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="mobile12345",
            user_type="EMPLOYEE",
            mobile="13800000000",
            is_superuser=False,
            is_active=True,
        ),
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/mobile-code-login",
        json={"mobile": "13800000000", "code": "123456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "登录成功"
    assert payload["data"]["access_token"]


def test_backend_mobile_code_login_invalid_code(client: TestClient, db: Session) -> None:
    from app import crud

    crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="mobile12345",
            user_type="EMPLOYEE",
            mobile="13800000008",
            is_superuser=False,
            is_active=True,
        ),
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/mobile-code-login",
        json={"mobile": "13800000008", "code": "654321"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "AUTH_INVALID_MOBILE_CODE"
    assert payload["message"] == "验证码错误或已失效"


def test_backend_mobile_code_login_unregistered_mobile(client: TestClient) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/mobile-code-login",
        json={"mobile": "19900009999", "code": "123456"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "AUTH_MOBILE_NOT_REGISTERED"
    assert payload["message"] == "手机号未注册后台账号"


def test_miniapp_code_login_first_time_creates_user(
    client: TestClient, db: Session
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-code-demo", "app_id": "wx123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "小程序登录成功"
    assert payload["data"]["access_token"]

    miniapp_account = db.exec(
        select(MiniappAccount).where(MiniappAccount.app_id == "wx123")
    ).first()
    assert miniapp_account is not None
    user = db.get(User, miniapp_account.user_id)
    assert user is not None
    assert user.user_type == "MINI_APP_MEMBER"
    assert user.username.startswith("mini_")


def test_miniapp_code_login_repeat_reuses_same_user(
    client: TestClient, db: Session
) -> None:
    first_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-repeat-demo", "app_id": "wx-repeat"},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-repeat-demo", "app_id": "wx-repeat"},
    )
    assert second_response.status_code == 200

    accounts = db.exec(
        select(MiniappAccount).where(MiniappAccount.app_id == "wx-repeat")
    ).all()
    assert len(accounts) == 1
    user = db.get(User, accounts[0].user_id)
    assert user is not None
    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {second_response.json()['data']['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["id"] == str(user.id)


def test_miniapp_bind_phone_success(client: TestClient, db: Session) -> None:
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-bind-phone", "app_id": "wx-bind"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": "13800000301", "country_code": "+86"},
    )
    assert bind_response.status_code == 200
    payload = bind_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "绑定手机号成功"
    assert payload["data"]["mobile"] == "13800000301"

    binding = db.exec(
        select(UserPhoneBinding).where(UserPhoneBinding.phone == "13800000301")
    ).first()
    assert binding is not None
    assert binding.is_verified is True


def test_miniapp_me_before_bind_phone_has_empty_mobile(client: TestClient) -> None:
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-before-bind", "app_id": "wx-before"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=headers,
    )
    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["mobile"] is None


def test_miniapp_me_after_bind_phone_returns_mobile(client: TestClient) -> None:
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-after-bind", "app_id": "wx-after"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": "13800000305", "country_code": "+86"},
    )
    assert bind_response.status_code == 200

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=headers,
    )
    assert me_response.status_code == 200
    payload = me_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["mobile"] == "13800000305"


def test_miniapp_phone_related_employees_without_phone_returns_empty(
    client: TestClient,
) -> None:
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-related-empty", "app_id": "wx-related-empty"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    relation_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=headers,
    )
    assert relation_response.status_code == 200
    payload = relation_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["phone"] is None
    assert payload["data"]["related_employees"] == []


def test_miniapp_phone_related_employees_returns_employee_history(
    client: TestClient, db: Session
) -> None:
    common_mobile = f"139{abs(hash(random_lower_string())) % 10**8:08d}"
    from app import crud

    first_employee = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="第一次入职员工",
            mobile=common_mobile,
            is_superuser=False,
            is_active=True,
        ),
    )
    first_profile = employee_service.get_employee_profile_by_user_id(
        session=db, user_id=first_employee.id
    )
    assert first_profile is not None
    employee_service.mark_employee_left(
        session=db,
        user=first_employee,
        profile=first_profile,
        left_at=None,
        leave_reason="历史离职",
    )

    second_employee = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="再次入职员工",
            mobile=common_mobile,
            is_superuser=False,
            is_active=True,
        ),
    )

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-related-history", "app_id": "wx-related-history"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": common_mobile, "country_code": "+86"},
    )
    assert bind_response.status_code == 200

    relation_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=headers,
    )
    assert relation_response.status_code == 200
    payload = relation_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "获取手机号关联员工成功"
    assert payload["data"]["phone"] == common_mobile
    related_employees = payload["data"]["related_employees"]
    assert len(related_employees) == 2
    assert related_employees[0]["user_id"] == str(second_employee.id)
    assert related_employees[0]["employment_status"] == "ACTIVE"
    assert related_employees[1]["user_id"] == str(first_employee.id)
    assert related_employees[1]["employment_status"] == "LEFT"


def test_miniapp_phone_related_employees_respects_current_store_context(
    client: TestClient, db: Session
) -> None:
    store_a = Store(code=f"mini_rel_a_{random_lower_string()[:8]}", name="小程序关联A店")
    store_b = Store(code=f"mini_rel_b_{random_lower_string()[:8]}", name="小程序关联B店")
    db.add(store_a)
    db.add(store_b)
    db.commit()
    db.refresh(store_a)
    db.refresh(store_b)

    org_a = OrgNode(
        store_id=store_a.id,
        parent_id=None,
        name="A店部门",
        node_type="DEPARTMENT",
        path=f"/{store_a.id}",
        level=1,
        sort_order=1,
        is_active=True,
    )
    org_b = OrgNode(
        store_id=store_b.id,
        parent_id=None,
        name="B店部门",
        node_type="DEPARTMENT",
        path=f"/{store_b.id}",
        level=1,
        sort_order=1,
        is_active=True,
    )
    db.add(org_a)
    db.add(org_b)
    db.commit()
    db.refresh(org_a)
    db.refresh(org_b)

    common_mobile = f"137{abs(hash(random_lower_string())) % 10**8:08d}"
    employee_a = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="门店A员工",
            mobile=common_mobile,
            is_superuser=False,
            is_active=True,
            primary_store_id=store_a.id,
            primary_department_id=org_a.id,
        ),
    )
    employee_b = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=None,
            password="password1234",
            user_type="EMPLOYEE",
            full_name="门店B员工",
            mobile=common_mobile,
            is_superuser=False,
            is_active=True,
            primary_store_id=store_b.id,
            primary_department_id=org_b.id,
        ),
    )

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-related-store-context", "app_id": "wx-related-store-context"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": common_mobile, "country_code": "+86"},
    )
    assert bind_response.status_code == 200

    all_relation_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=headers,
    )
    assert all_relation_response.status_code == 200
    all_related = all_relation_response.json()["data"]["related_employees"]
    assert {item["user_id"] for item in all_related} == {
        str(employee_a.id),
        str(employee_b.id),
    }

    store_a_relation_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers={**headers, "X-Current-Store-Id": str(store_a.id)},
    )
    assert store_a_relation_response.status_code == 200
    store_a_payload = store_a_relation_response.json()["data"]
    assert store_a_payload["current_store_id"] == str(store_a.id)
    assert [item["user_id"] for item in store_a_payload["related_employees"]] == [
        str(employee_a.id)
    ]

    store_b_relation_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers={**headers, "X-Current-Store-Id": str(store_b.id)},
    )
    assert store_b_relation_response.status_code == 200
    store_b_payload = store_b_relation_response.json()["data"]
    assert store_b_payload["current_store_id"] == str(store_b.id)
    assert [item["user_id"] for item in store_b_payload["related_employees"]] == [
        str(employee_b.id)
    ]


def test_miniapp_bind_phone_repeat_is_idempotent(
    client: TestClient, db: Session
) -> None:
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-bind-repeat", "app_id": "wx-bind-repeat"},
    )
    headers = {"Authorization": f"Bearer {login_response.json()['data']['access_token']}"}

    first_bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": "13800000302", "country_code": "+86"},
    )
    assert first_bind_response.status_code == 200

    second_bind_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=headers,
        json={"phone": "13800000302", "country_code": "+86"},
    )
    assert second_bind_response.status_code == 200

    bindings = db.exec(
        select(UserPhoneBinding).where(UserPhoneBinding.phone == "13800000302")
    ).all()
    assert len(bindings) == 1


def test_miniapp_bind_phone_conflict_with_other_user(client: TestClient) -> None:
    first_login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-bind-conflict-a", "app_id": "wx-bind-conflict"},
    )
    first_headers = {
        "Authorization": f"Bearer {first_login_response.json()['data']['access_token']}"
    }
    assert client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=first_headers,
        json={"phone": "13800000303", "country_code": "+86"},
    ).status_code == 200

    second_login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-bind-conflict-b", "app_id": "wx-bind-conflict"},
    )
    second_headers = {
        "Authorization": f"Bearer {second_login_response.json()['data']['access_token']}"
    }
    conflict_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=second_headers,
        json={"phone": "13800000303", "country_code": "+86"},
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json()["code"] == "PHONE_ALREADY_BOUND"
