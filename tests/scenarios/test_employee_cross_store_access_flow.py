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


def test_employee_cross_store_access_flow(client: TestClient) -> None:
    """验证只在一家门店入职的员工不能访问另一家门店数据。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"emp_cross_a_{random_lower_string()[:8]}",
            "name": "员工所属门店",
            "status": "ACTIVE",
        },
    )
    assert store_a_response.status_code == 201
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"emp_cross_b_{random_lower_string()[:8]}",
            "name": "另一家门店",
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
            "name": "A店营运部",
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
            "name": "B店营运部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_b_response.status_code == 201
    org_b_id = org_b_response.json()["data"]["id"]

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    employee_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"emp_cross_role_{random_lower_string()[:8]}",
            "name": "单店员工查看角色",
            "status": "ACTIVE",
        },
    )
    assert employee_role_response.status_code == 201
    employee_role_id = employee_role_response.json()["data"]["id"]

    assign_role_permissions_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{employee_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["org.store.read"],
                permission_ids_by_code["org.node.read"],
                permission_ids_by_code["org.binding.read"],
                permission_ids_by_code["employee.read"],
            ]
        },
    )
    assert assign_role_permissions_response.status_code == 200

    employee_password = "password1234"
    employee_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": employee_password,
                "full_name": "单店员工",
                "nickname": "A店员工",
                "mobile": f"134{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
            "role_ids": [employee_role_id],
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None}
            ],
        },
    )
    assert employee_onboard_response.status_code == 201
    employee_payload = employee_onboard_response.json()["data"]
    employee_id = employee_payload["user"]["id"]
    employee_username = employee_payload["user"]["username"]

    other_store_employee_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "另一店员工",
                "nickname": "B店员工",
                "mobile": f"133{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "收银员",
        },
    )
    assert other_store_employee_response.status_code == 201
    other_store_employee_id = other_store_employee_response.json()["data"]["user"]["id"]

    employee_headers = _login(client, employee_username, employee_password)

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=employee_headers,
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["primary_store_id"] == store_a_id

    stores_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=employee_headers,
    )
    assert stores_response.status_code == 200
    assert {item["id"] for item in stores_response.json()["data"]} == {store_a_id}

    org_nodes_response = client.get(
        f"{settings.API_V1_STR}/org/nodes",
        headers=employee_headers,
    )
    assert org_nodes_response.status_code == 200
    assert {item["id"] for item in org_nodes_response.json()["data"]} == {org_a_id}

    own_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_id}/profile",
        headers=employee_headers,
    )
    assert own_profile_response.status_code == 200

    other_store_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{other_store_employee_id}/profile",
        headers=employee_headers,
    )
    assert other_store_profile_response.status_code == 403
    assert other_store_profile_response.json()["code"] == "DATA_SCOPE_DENIED"

    cross_store_context_headers = {**employee_headers, "X-Current-Store-Id": store_b_id}

    store_list_cross_context_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=cross_store_context_headers,
    )
    assert store_list_cross_context_response.status_code == 403
    assert store_list_cross_context_response.json()["code"] == "DATA_SCOPE_DENIED"

    me_cross_context_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=cross_store_context_headers,
    )
    assert me_cross_context_response.status_code == 403
    assert me_cross_context_response.json()["code"] == "DATA_SCOPE_DENIED"
