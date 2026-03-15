import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.security import verify_password
from app.models import UserCreate, UserUpdate
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string


def test_get_users_me_returns_standard_response(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["email"] == settings.FIRST_SUPERUSER
    assert payload["data"]["is_superuser"] is True


def test_list_users_requires_permission(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] == "AUTH_PERMISSION_DENIED"
    assert "缺少权限" in payload["message"]


def test_miniapp_user_with_employee_permission_still_cannot_list_users(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=superuser_token_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"miniapp_emp_only_{random_lower_string()[:8]}",
            "name": "小程序员工权限角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["data"]["id"]

    assign_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={"permission_ids": [permission_ids_by_code["employee.read"]]},
    )
    assert assign_permission_response.status_code == 200

    miniapp_login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-miniapp-users-denied", "app_id": "wx-miniapp-users-denied"},
    )
    assert miniapp_login_response.status_code == 200
    miniapp_headers = {
        "Authorization": f"Bearer {miniapp_login_response.json()['data']['access_token']}"
    }

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=miniapp_headers,
    )
    assert me_response.status_code == 200
    miniapp_user_id = me_response.json()["data"]["id"]

    assign_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{miniapp_user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200

    users_response = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=miniapp_headers,
    )
    assert users_response.status_code == 403
    payload = users_response.json()
    assert payload["code"] == "AUTH_PERMISSION_DENIED"
    assert "iam.user.read" in payload["message"]


def test_list_users_as_superuser(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
        ),
    )

    response = client.get(
        f"{settings.API_V1_STR}/users/?skip=0&limit=10",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["total"] >= 1
    assert isinstance(payload["data"]["items"], list)


def test_create_user_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username = random_lower_string()
    email = random_email()
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": email,
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "测试用户",
            "nickname": "测试",
            "mobile": "13800000000",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "创建用户成功"
    assert payload["data"]["username"] == username
    assert crud.get_user_by_email(session=db, email=email) is not None


def test_create_user_without_email(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username = random_lower_string()
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": None,
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "无邮箱用户",
            "nickname": "本地员工",
            "mobile": "13800000009",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["username"] == username
    assert payload["data"]["email"] is None
    user = crud.get_user_by_username(session=db, username=username)
    assert user is not None
    assert user.email is None


def test_create_user_duplicate_username(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username = random_lower_string()
    crud.create_user(
        session=db,
        user_create=UserCreate(
            username=username,
            email=random_email(),
            password="password1234",
        ),
    )

    response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": random_email(),
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "重复账号",
            "nickname": None,
            "mobile": None,
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["code"] == "USER_USERNAME_EXISTS"
    assert payload["message"] == "登录账号已存在"


def test_read_user_by_id_as_self(client: TestClient, db: Session) -> None:
    email = random_email()
    username = random_lower_string()
    password = "password1234"
    user = crud.create_user(
        session=db,
        user_create=UserCreate(username=username, email=email, password=password),
    )
    headers = authentication_token_from_email(client=client, email=email, db=db)

    response = client.get(f"{settings.API_V1_STR}/users/{user.id}", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["id"] == str(user.id)


def test_read_user_by_id_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "USER_NOT_FOUND"
    assert payload["message"] == "用户不存在"


def test_update_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    email = random_email()
    response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": "已更新姓名", "email": email},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["email"] == email

    user = crud.get_user_by_email(session=db, email=email)
    assert user is not None
    assert user.full_name == "已更新姓名"


def test_update_password_me(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    new_password = "new-password123"
    response = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=superuser_token_headers,
        json={
            "current_password": settings.FIRST_SUPERUSER_PASSWORD,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "修改密码成功"

    user = crud.get_user_by_email(session=db, email=settings.FIRST_SUPERUSER)
    assert user is not None
    verified, _ = verify_password(new_password, user.hashed_password)
    assert verified

    crud.update_user(
        session=db,
        db_user=user,
        user_in=UserUpdate(password=settings.FIRST_SUPERUSER_PASSWORD),
    )


def test_reset_user_password(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    username = random_lower_string()
    old_password = "password1234"
    new_password = "new-password1234"
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=username,
            email=random_email(),
            password=old_password,
        ),
    )

    response = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}/reset-password",
        headers=superuser_token_headers,
        json={"new_password": new_password},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["message"] == "重置密码成功"

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": username, "password": new_password},
    )
    assert login_response.status_code == 200

    old_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": username, "password": old_password},
    )
    assert old_login_response.status_code == 400
    assert old_login_response.json()["code"] == "AUTH_INVALID_CREDENTIALS"


def test_reset_user_password_for_self_is_forbidden(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    me_response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    assert me_response.status_code == 200
    user_id = me_response.json()["data"]["id"]

    response = client.patch(
        f"{settings.API_V1_STR}/users/{user_id}/reset-password",
        headers=superuser_token_headers,
        json={"new_password": "new-password1234"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "USER_RESET_SELF_FORBIDDEN"


def test_delete_user_requires_data_scope(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    other_user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
        ),
    )

    response = client.delete(
        f"{settings.API_V1_STR}/users/{other_user.id}",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["code"] in {"AUTH_PERMISSION_DENIED", "DATA_SCOPE_DENIED"}
