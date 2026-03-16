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


def test_multi_store_permission_fetch_flow(client: TestClient) -> None:
    """验证多门店员工切店后，权限集合按当前门店变化。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"perm_fetch_a_{random_lower_string()[:8]}",
            "name": "权限获取一号店",
            "status": "ACTIVE",
        },
    )
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"perm_fetch_b_{random_lower_string()[:8]}",
            "name": "权限获取二号店",
            "status": "ACTIVE",
        },
    )
    store_b_id = store_b_response.json()["data"]["id"]

    org_a_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_a_id,
            "parent_id": None,
            "name": "一号店前厅部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
            "prefix": "QYFA",
        },
    )
    org_a_id = org_a_response.json()["data"]["id"]

    org_b_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_b_id,
            "parent_id": None,
            "name": "二号店前厅部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
            "prefix": "QYFB",
        },
    )
    org_b_id = org_b_response.json()["data"]["id"]

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    read_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"perm_read_{random_lower_string()[:8]}",
            "name": "员工查看角色",
            "status": "ACTIVE",
        },
    )
    read_role_id = read_role_response.json()["data"]["id"]

    create_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"perm_create_{random_lower_string()[:8]}",
            "name": "员工新增角色",
            "status": "ACTIVE",
        },
    )
    create_role_id = create_role_response.json()["data"]["id"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/roles/{read_role_id}",
        headers=admin_headers,
        json={"permission_ids": [permission_ids_by_code["employee.read"]]},
    ).status_code == 200

    assert client.put(
        f"{settings.API_V1_STR}/iam/roles/{create_role_id}",
        headers=admin_headers,
        json={"permission_ids": [permission_ids_by_code["employee.create"]]},
    ).status_code == 200

    employee_username = random_lower_string()
    employee_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": employee_username,
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "多门店权限获取员工",
            "nickname": "权限获取",
            "mobile": "13800000881",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    employee_user_id = employee_response.json()["data"]["id"]

    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": employee_user_id,
            "org_node_id": org_a_id,
            "is_primary": True,
            "position_name": "值班",
        },
    ).status_code == 201

    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": employee_user_id,
            "org_node_id": org_b_id,
            "is_primary": False,
            "position_name": "巡店",
        },
    ).status_code == 201

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers={**admin_headers, "X-Current-Store-Id": store_a_id},
        json={"role_ids": [read_role_id, create_role_id]},
    ).status_code == 200

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers={**admin_headers, "X-Current-Store-Id": store_b_id},
        json={"role_ids": [read_role_id]},
    ).status_code == 200

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None},
                {"scope_type": "STORE", "store_id": store_b_id, "org_node_id": None},
            ]
        },
    ).status_code == 200

    employee_headers = _login(client, employee_username, "password1234")

    default_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=employee_headers,
    )
    assert default_me_response.status_code == 200
    default_me_payload = default_me_response.json()["data"]
    assert default_me_payload["current_store_id"] == store_a_id
    assert default_me_payload["current_store_name"] == "权限获取一号店"
    assert set(default_me_payload["permissions"]) == {
        "employee.read",
        "employee.create",
    }

    switched_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={**employee_headers, "X-Current-Store-Id": store_b_id},
    )
    assert switched_me_response.status_code == 200
    switched_me_payload = switched_me_response.json()["data"]
    assert switched_me_payload["current_store_id"] == store_b_id
    assert switched_me_payload["current_store_name"] == "权限获取二号店"
    assert set(switched_me_payload["permissions"]) == {"employee.read"}
    assert {item["store_id"] for item in switched_me_payload["accessible_stores"]} == {
        store_a_id,
        store_b_id,
    }
