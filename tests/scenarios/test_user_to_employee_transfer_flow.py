from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_lower_string


def _login(client: TestClient, account: str, password: str) -> dict[str, str]:
    response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": account, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_to_employee_transfer_flow(client: TestClient) -> None:
    """验证普通用户转员工，并在后续切换主组织和主门店。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"transfer_a_{random_lower_string()[:8]}",
            "name": "转员工一号店",
            "status": "ACTIVE",
        },
    )
    assert store_a_response.status_code == 201
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"transfer_b_{random_lower_string()[:8]}",
            "name": "转员工二号店",
            "status": "ACTIVE",
        },
    )
    assert store_b_response.status_code == 201
    store_b_id = store_b_response.json()["data"]["id"]

    org_a_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_a_id,
            "parent_id": None,
            "name": "一号店部门",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_a_response.status_code == 201
    org_a_id = org_a_response.json()["data"]["id"]

    org_b_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_b_id,
            "parent_id": None,
            "name": "二号店部门",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_b_response.status_code == 201
    org_b_id = org_b_response.json()["data"]["id"]

    password = "password1234"
    user_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": random_lower_string(),
            "email": None,
            "password": password,
            "user_type": "MINI_APP_MEMBER",
            "is_active": True,
            "is_superuser": False,
            "full_name": "待转员工用户",
            "nickname": "待转员工",
            "mobile": f"128{abs(hash(random_lower_string())) % 10**8:08d}",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert user_response.status_code == 201
    user_payload = user_response.json()["data"]
    user_id = user_payload["id"]
    username = user_payload["username"]
    assert user_payload["user_type"] == "MINI_APP_MEMBER"

    transfer_response = client.patch(
        f"{settings.API_V1_STR}/users/{user_id}",
        headers=admin_headers,
        json={"user_type": "EMPLOYEE"},
    )
    assert transfer_response.status_code == 200
    assert transfer_response.json()["data"]["user_type"] == "EMPLOYEE"

    profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{user_id}/profile",
        headers=admin_headers,
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["employment_status"] == "ACTIVE"

    first_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": user_id,
            "org_node_id": org_a_id,
            "is_primary": True,
            "position_name": "一号店店员",
        },
    )
    assert first_binding_response.status_code == 201

    me_headers = _login(client, username, password)
    first_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=me_headers,
    )
    assert first_me_response.status_code == 200
    assert first_me_response.json()["data"]["primary_store_id"] == store_a_id
    assert first_me_response.json()["data"]["primary_department_id"] == org_a_id

    second_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": user_id,
            "org_node_id": org_b_id,
            "is_primary": True,
            "position_name": "二号店支援",
        },
    )
    assert second_binding_response.status_code == 201

    bindings_response = client.get(
        f"{settings.API_V1_STR}/org/bindings?user_id={user_id}",
        headers=admin_headers,
    )
    assert bindings_response.status_code == 200
    bindings = bindings_response.json()["data"]
    primary_binding = next(item for item in bindings if item["is_primary"] is True)
    assert primary_binding["org_node_id"] == org_b_id
    assert any(
        item["org_node_id"] == org_a_id and item["is_primary"] is False for item in bindings
    )

    second_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=me_headers,
    )
    assert second_me_response.status_code == 200
    second_me_payload = second_me_response.json()["data"]
    assert second_me_payload["primary_store_id"] == store_b_id
    assert second_me_payload["primary_department_id"] == org_b_id
