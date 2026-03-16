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


def test_employee_role_change_flow(client: TestClient) -> None:
    """验证员工角色变更后，已有 token 的权限会立即收敛。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"role_change_store_{random_lower_string()[:8]}",
            "name": "角色变更测试门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    store_reader_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"role_change_reader_{random_lower_string()[:8]}",
            "name": "门店查看角色",
            "status": "ACTIVE",
        },
    )
    assert store_reader_role_response.status_code == 201
    store_reader_role_id = store_reader_role_response.json()["data"]["id"]

    empty_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"role_change_empty_{random_lower_string()[:8]}",
            "name": "空权限角色",
            "status": "ACTIVE",
        },
    )
    assert empty_role_response.status_code == 201
    empty_role_id = empty_role_response.json()["data"]["id"]

    assign_reader_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{store_reader_role_id}",
        headers=admin_headers,
        json={"permission_ids": [permission_ids_by_code["org.store.read"]]},
    )
    assert assign_reader_permission_response.status_code == 200

    username = random_lower_string()
    password = "password1234"
    user_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": username,
            "email": None,
            "password": password,
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "角色变更员工",
            "nickname": "角色变更",
            "mobile": f"132{abs(hash(random_lower_string())) % 10**8:08d}",
            "status": "ACTIVE",
            "primary_store_id": store_id,
            "primary_department_id": None,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["data"]["id"]

    assign_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{user_id}/stores/{store_id}/roles",
        headers=admin_headers,
        json={"role_ids": [store_reader_role_id]},
    )
    assert assign_role_response.status_code == 200

    assign_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {"scope_type": "STORE", "store_id": store_id, "org_node_id": None}
            ]
        },
    )
    assert assign_scope_response.status_code == 200

    user_headers = _login(client, username, password)

    stores_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=user_headers,
    )
    assert stores_response.status_code == 200
    assert {item["id"] for item in stores_response.json()["data"]} == {store_id}

    replace_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{user_id}/stores/{store_id}/roles",
        headers=admin_headers,
        json={"role_ids": [empty_role_id]},
    )
    assert replace_role_response.status_code == 200

    stores_after_change_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=user_headers,
    )
    assert stores_after_change_response.status_code == 403
    assert stores_after_change_response.json()["code"] == "AUTH_PERMISSION_DENIED"
