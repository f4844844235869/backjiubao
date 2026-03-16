from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import EmployeeProfile, UserCreate
from app.modules.iam import service as iam_service
from app.modules.iam.models import Permission, Role, UserDataScope
from app.modules.org.models import OrgNode
from app.modules.store.models import Store
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string


def test_create_employee_user_auto_builds_profile(db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
        ),
    )

    profile = db.exec(
        select(EmployeeProfile).where(EmployeeProfile.user_id == user.id)
    ).first()
    assert profile is not None
    assert profile.user_id == user.id
    assert profile.employment_status == "ACTIVE"


def test_read_employee_profile(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
        ),
    )

    response = client.get(
        f"/api/v1/employees/{user.id}/profile",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["user_id"] == str(user.id)
    assert payload["data"]["employment_status"] == "ACTIVE"


def test_read_employee_profile_requires_permission(client: TestClient, db: Session) -> None:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
        ),
    )
    headers = authentication_token_from_email(client=client, email=random_email(), db=db)

    response = client.get(f"/api/v1/employees/{user.id}/profile", headers=headers)

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "AUTH_PERMISSION_DENIED"


def test_miniapp_user_cannot_read_employee_profile_without_permission(
    client: TestClient, db: Session
) -> None:
    store = Store(code=f"store_{random_lower_string()[:8]}", name="测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)

    org_node = OrgNode(
        store_id=store.id,
        parent_id=None,
        name="测试部门",
        node_type="DEPARTMENT",
        path=f"/{store.id}",
        level=1,
        sort_order=1,
        is_active=True,
    )
    db.add(org_node)
    db.commit()
    db.refresh(org_node)

    employee = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
            primary_store_id=store.id,
            primary_department_id=org_node.id,
        ),
    )

    login_response = client.post(
        "/api/v1/auth/miniapp/code-login",
        json={"code": "wx-employee-forbidden", "app_id": "wx-employee-forbidden"},
    )
    assert login_response.status_code == 200
    miniapp_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    response = client.get(
        f"/api/v1/employees/{employee.id}/profile",
        headers={**miniapp_headers, "X-Current-Store-Id": str(store.id)},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "AUTH_PERMISSION_DENIED"


def test_miniapp_user_can_read_employee_profile_after_assign_permission_and_scope(
    client: TestClient, db: Session
) -> None:
    store = Store(code=f"store_{random_lower_string()[:8]}", name="小程序员工门店")
    db.add(store)
    db.commit()
    db.refresh(store)

    org_node = OrgNode(
        store_id=store.id,
        parent_id=None,
        name="小程序员工部门",
        node_type="DEPARTMENT",
        path=f"/{store.id}",
        level=1,
        sort_order=1,
        is_active=True,
    )
    db.add(org_node)
    db.commit()
    db.refresh(org_node)

    employee = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
            full_name="可查看员工",
            primary_store_id=store.id,
            primary_department_id=org_node.id,
        ),
    )

    login_response = client.post(
        "/api/v1/auth/miniapp/code-login",
        json={"code": "wx-employee-allowed", "app_id": "wx-employee-allowed"},
    )
    assert login_response.status_code == 200
    miniapp_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }
    me_response = client.get("/api/v1/auth/me", headers=miniapp_headers)
    assert me_response.status_code == 200
    miniapp_user_id = me_response.json()["data"]["id"]

    permission = db.exec(
        select(Permission).where(Permission.code == "employee.read")
    ).first()
    assert permission is not None

    role = Role(code=f"miniapp_emp_{random_lower_string()[:8]}", name="小程序员工查看角色")
    db.add(role)
    db.commit()
    db.refresh(role)

    iam_service.replace_role_permissions(
        session=db, role_id=role.id, permission_ids=[permission.id]
    )
    iam_service.replace_user_store_roles(
        session=db,
        user_id=miniapp_user_id,
        store_id=store.id,
        role_ids=[role.id],
    )
    iam_service.replace_user_data_scopes(
        session=db,
        user_id=miniapp_user_id,
        scopes=[
            UserDataScope(
                user_id=miniapp_user_id,
                scope_type="STORE",
                store_id=store.id,
                org_node_id=None,
            )
        ],
    )

    response = client.get(
        f"/api/v1/employees/{employee.id}/profile",
        headers={**miniapp_headers, "X-Current-Store-Id": str(store.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["user_id"] == str(employee.id)
    assert payload["data"]["employment_status"] == "ACTIVE"


def test_employee_user_cannot_read_miniapp_phone_related_employees(
    client: TestClient, db: Session
) -> None:
    employee = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
            user_type="EMPLOYEE",
            mobile="13900000001",
        ),
    )

    login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": employee.username, "password": "password1234"},
    )
    assert login_response.status_code == 200
    headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    response = client.get(
        "/api/v1/auth/miniapp/phone-related-employees",
        headers=headers,
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "AUTH_PERMISSION_DENIED"
    assert payload["message"] == "当前用户不是小程序用户，无法查看手机号关联员工"


def test_secondary_store_context_can_read_records_and_leave_employee(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    primary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"EMP-CTX-A-{random_lower_string()[:8]}",
            "name": "主门店",
            "status": "ACTIVE",
        },
    )
    primary_store_id = primary_store_response.json()["data"]["id"]

    secondary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"EMP-CTX-B-{random_lower_string()[:8]}",
            "name": "次门店",
            "status": "ACTIVE",
        },
    )
    secondary_store_id = secondary_store_response.json()["data"]["id"]

    primary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": primary_store_id,
            "parent_id": None,
            "name": "主门店营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    primary_org_id = primary_org_response.json()["data"]["id"]

    secondary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": secondary_store_id,
            "parent_id": None,
            "name": "次门店前厅组",
            "prefix": "QT",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    secondary_org_id = secondary_org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": random_email(),
                "password": "password1234",
                "full_name": "多门店员工",
                "nickname": "多门店",
                "mobile": f"137{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": primary_org_id,
            "position_name": "主门店店长",
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]

    create_binding_response = client.post(
        "/api/v1/org/bindings",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={
            "user_id": user_id,
            "org_node_id": secondary_org_id,
            "position_name": "次门店巡店",
            "is_primary": False,
        },
    )
    assert create_binding_response.status_code == 201

    profile_response = client.get(
        f"/api/v1/employees/{user_id}/profile",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
    )
    assert profile_response.status_code == 200

    records_response = client.get(
        f"/api/v1/employees/{user_id}/employment-records",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
    )
    assert records_response.status_code == 200

    leave_response = client.post(
        f"/api/v1/employees/{user_id}/leave",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={"leave_reason": "次门店上下文离职"},
    )
    assert leave_response.status_code == 200
