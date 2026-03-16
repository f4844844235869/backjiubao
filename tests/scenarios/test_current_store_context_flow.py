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


def test_current_store_context_flow(client: TestClient) -> None:
    """验证多门店用户切换当前门店上下文后，只能看到当前门店数据。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"context_a_{random_lower_string()[:8]}",
            "name": "上下文一号店",
            "status": "ACTIVE",
        },
    )
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"context_b_{random_lower_string()[:8]}",
            "name": "上下文二号店",
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
            "name": "一号店营运部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    org_a_id = org_a_response.json()["data"]["id"]

    org_b_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_b_id,
            "parent_id": None,
            "name": "二号店营运部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
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

    manager_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"context_mgr_{random_lower_string()[:8]}",
            "name": "多门店主管",
            "status": "ACTIVE",
        },
    )
    manager_role_id = manager_role_response.json()["data"]["id"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/roles/{manager_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["employee.create"],
                permission_ids_by_code["employee.bind_org"],
                permission_ids_by_code["employee.read"],
                permission_ids_by_code["iam.user.read"],
                permission_ids_by_code["iam.user.assign_scope"],
                permission_ids_by_code["org.store.read"],
                permission_ids_by_code["org.node.read"],
                permission_ids_by_code["org.binding.read"],
                permission_ids_by_code["org.binding.create"],
            ]
        },
    ).status_code == 200

    manager_username = random_lower_string()
    manager_create_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": manager_username,
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "多门店主管",
            "nickname": "主管",
            "mobile": "13800000199",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    manager_user_id = manager_create_response.json()["data"]["id"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/roles",
        headers={**admin_headers, "X-Current-Store-Id": store_a_id},
        json={"role_ids": [manager_role_id]},
    ).status_code == 200
    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/roles",
        headers={**admin_headers, "X-Current-Store-Id": store_b_id},
        json={"role_ids": [manager_role_id]},
    ).status_code == 200

    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": manager_user_id,
            "org_node_id": org_a_id,
            "is_primary": True,
            "position_name": "主管",
        },
    ).status_code == 201
    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": manager_user_id,
            "org_node_id": org_b_id,
            "is_primary": False,
            "position_name": "巡店主管",
        },
    ).status_code == 201

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None},
                {"scope_type": "STORE", "store_id": store_b_id, "org_node_id": None},
            ]
        },
    ).status_code == 200

    manager_headers = _login(client, manager_username, "password1234")

    switch_store_response = client.post(
        f"{settings.API_V1_STR}/auth/current-store/switch",
        headers=manager_headers,
        json={"store_id": store_b_id},
    )
    assert switch_store_response.status_code == 200
    switch_payload = switch_store_response.json()["data"]
    assert switch_payload["current_store_id"] == store_b_id
    assert switch_payload["current_org_node_id"] == org_b_id
    assert switch_payload["primary_store_id"] == store_b_id

    switched_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=manager_headers,
    )
    assert switched_me_response.status_code == 200
    switched_me_payload = switched_me_response.json()["data"]
    assert switched_me_payload["current_store_id"] == store_b_id
    assert switched_me_payload["current_org_node_id"] == org_b_id
    assert switched_me_payload["current_store_name"] == "上下文二号店"
    assert {item["store_id"] for item in switched_me_payload["accessible_stores"]} == {
        store_a_id,
        store_b_id,
    }

    employee_a_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers={**manager_headers, "X-Current-Store-Id": store_a_id},
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "一号店员工",
                "nickname": "一号店",
                "mobile": "13800000201",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
        },
    )
    employee_a_id = employee_a_response.json()["data"]["user"]["id"]

    employee_b_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers={**manager_headers, "X-Current-Store-Id": store_b_id},
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "二号店员工",
                "nickname": "二号店",
                "mobile": "13800000202",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "服务员",
        },
    )
    employee_b_id = employee_b_response.json()["data"]["user"]["id"]

    stores_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=manager_headers,
    )
    assert stores_response.status_code == 200
    assert {item["id"] for item in stores_response.json()["data"]} == {
        store_a_id,
        store_b_id,
    }

    store_a_context_headers = {
        **manager_headers,
        "X-Current-Store-Id": store_a_id,
    }
    stores_a_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=store_a_context_headers,
    )
    assert stores_a_response.status_code == 200
    assert {item["id"] for item in stores_a_response.json()["data"]} == {store_a_id}

    org_nodes_a_response = client.get(
        f"{settings.API_V1_STR}/org/nodes",
        headers=store_a_context_headers,
    )
    assert org_nodes_a_response.status_code == 200
    assert {item["id"] for item in org_nodes_a_response.json()["data"]} == {org_a_id}

    bindings_a_response = client.get(
        f"{settings.API_V1_STR}/org/bindings",
        headers=store_a_context_headers,
    )
    assert bindings_a_response.status_code == 200
    assert org_b_id not in {
        item["org_node_id"] for item in bindings_a_response.json()["data"]
    }

    employee_a_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_a_id}/profile",
        headers=store_a_context_headers,
    )
    assert employee_a_profile_response.status_code == 200

    employee_b_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_b_id}/profile",
        headers=store_a_context_headers,
    )
    assert employee_b_profile_response.status_code == 403
    assert employee_b_profile_response.json()["code"] == "DATA_SCOPE_DENIED"

    cross_store_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=store_a_context_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "跨店入职员工",
                "nickname": "跨店",
                "mobile": "13800000203",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "服务员",
        },
    )
    assert cross_store_onboard_response.status_code == 403
    assert cross_store_onboard_response.json()["code"] == "DATA_SCOPE_DENIED"

    cross_store_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=store_a_context_headers,
        json={
            "user_id": employee_b_id,
            "org_node_id": org_a_id,
            "is_primary": False,
            "position_name": "临时支援",
        },
    )
    assert cross_store_binding_response.status_code == 201
    assert cross_store_binding_response.json()["data"]["org_node_id"] == org_a_id

    cross_store_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_a_id}/data-scopes",
        headers=store_a_context_headers,
        json={
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": store_b_id,
                    "org_node_id": None,
                }
            ]
        },
    )
    assert cross_store_scope_response.status_code == 403
    assert cross_store_scope_response.json()["code"] == "DATA_SCOPE_DENIED"
