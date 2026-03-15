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


def test_employee_multi_store_membership_flow(client: TestClient) -> None:
    """验证同一员工属于多个门店时，可按并集访问并按当前门店上下文收敛。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"multi_emp_a_{random_lower_string()[:8]}",
            "name": "多门店员工一号店",
            "status": "ACTIVE",
        },
    )
    assert store_a_response.status_code == 201
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"multi_emp_b_{random_lower_string()[:8]}",
            "name": "多门店员工二号店",
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

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"multi_emp_role_{random_lower_string()[:8]}",
            "name": "多门店员工查看角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["data"]["id"]

    assign_permissions_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["org.store.read"],
                permission_ids_by_code["org.node.read"],
                permission_ids_by_code["employee.read"],
            ]
        },
    )
    assert assign_permissions_response.status_code == 200

    employee_password = "password1234"
    employee_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": employee_password,
                "full_name": "多门店员工",
                "nickname": "巡店员工",
                "mobile": f"131{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "巡店",
            "role_ids": [role_id],
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None},
                {"scope_type": "STORE", "store_id": store_b_id, "org_node_id": None},
            ],
        },
    )
    assert employee_onboard_response.status_code == 201
    employee_payload = employee_onboard_response.json()["data"]
    employee_id = employee_payload["user"]["id"]
    employee_username = employee_payload["user"]["username"]

    second_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": employee_id,
            "org_node_id": org_b_id,
            "is_primary": False,
            "position_name": "支援巡店",
        },
    )
    assert second_binding_response.status_code == 201

    employee_a_profile_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "一号店目标员工",
                "nickname": "一号店目标",
                "mobile": f"130{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
        },
    )
    assert employee_a_profile_response.status_code == 201
    employee_a_id = employee_a_profile_response.json()["data"]["user"]["id"]

    employee_b_profile_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "二号店目标员工",
                "nickname": "二号店目标",
                "mobile": f"129{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "收银员",
        },
    )
    assert employee_b_profile_response.status_code == 201
    employee_b_id = employee_b_profile_response.json()["data"]["user"]["id"]

    employee_headers = _login(client, employee_username, employee_password)

    stores_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=employee_headers,
    )
    assert stores_response.status_code == 200
    assert {item["id"] for item in stores_response.json()["data"]} == {
        store_a_id,
        store_b_id,
    }

    store_a_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_a_id}/profile",
        headers={**employee_headers, "X-Current-Store-Id": store_a_id},
    )
    assert store_a_profile_response.status_code == 200

    store_b_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_b_id}/profile",
        headers={**employee_headers, "X-Current-Store-Id": store_b_id},
    )
    assert store_b_profile_response.status_code == 200
