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


def test_multi_role_scope_union_flow(client: TestClient) -> None:
    """验证多角色权限和多条数据范围按并集生效。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"union_a_{random_lower_string()[:8]}",
            "name": "并集一号店",
            "status": "ACTIVE",
        },
    )
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"union_b_{random_lower_string()[:8]}",
            "name": "并集二号店",
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

    store_read_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"union_store_{random_lower_string()[:8]}",
            "name": "门店查看角色",
            "status": "ACTIVE",
        },
    )
    store_read_role_id = store_read_role_response.json()["data"]["id"]

    employee_read_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"union_employee_{random_lower_string()[:8]}",
            "name": "员工查看角色",
            "status": "ACTIVE",
        },
    )
    employee_read_role_id = employee_read_role_response.json()["data"]["id"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/roles/{store_read_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["org.store.read"],
                permission_ids_by_code["org.node.read"],
            ]
        },
    ).status_code == 200

    assert client.put(
        f"{settings.API_V1_STR}/iam/roles/{employee_read_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["employee.read"],
                permission_ids_by_code["org.binding.read"],
            ]
        },
    ).status_code == 200

    union_user_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": random_lower_string(),
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "并集用户",
            "nickname": "并集",
            "mobile": "13800000221",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    union_user_id = union_user_response.json()["data"]["id"]
    union_username = union_user_response.json()["data"]["username"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{union_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [store_read_role_id, employee_read_role_id]},
    ).status_code == 200

    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": union_user_id,
            "org_node_id": org_a_id,
            "is_primary": True,
            "position_name": "巡检",
        },
    ).status_code == 201

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{union_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None},
                {"scope_type": "STORE", "store_id": store_b_id, "org_node_id": None},
            ]
        },
    ).status_code == 200

    employee_a_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "并集一号店员工",
                "nickname": "一号店",
                "mobile": "13800000222",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
        },
    )
    employee_a_id = employee_a_response.json()["data"]["user"]["id"]

    employee_b_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "并集二号店员工",
                "nickname": "二号店",
                "mobile": "13800000223",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "服务员",
        },
    )
    employee_b_id = employee_b_response.json()["data"]["user"]["id"]

    union_headers = _login(client, union_username, "password1234")

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=union_headers,
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()["data"]
    assert set(me_payload["roles"]) == {
        store_read_role_response.json()["data"]["code"],
        employee_read_role_response.json()["data"]["code"],
    }
    assert set(me_payload["permissions"]) == {
        "org.store.read",
        "org.node.read",
        "employee.read",
        "org.binding.read",
    }
    assert {item["store_id"] for item in me_payload["data_scopes"]} == {
        store_a_id,
        store_b_id,
    }

    stores_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=union_headers,
    )
    assert stores_response.status_code == 200
    assert {item["id"] for item in stores_response.json()["data"]} == {
        store_a_id,
        store_b_id,
    }

    employee_a_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_a_id}/profile",
        headers=union_headers,
    )
    assert employee_a_profile_response.status_code == 200

    employee_b_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_b_id}/profile",
        headers=union_headers,
    )
    assert employee_b_profile_response.status_code == 200

    auth_summary_response = client.get(
        f"{settings.API_V1_STR}/iam/users/{union_user_id}/authorization-summary",
        headers=admin_headers,
    )
    assert auth_summary_response.status_code == 200
    auth_summary_payload = auth_summary_response.json()["data"]
    assert {item["code"] for item in auth_summary_payload["roles"]} == {
        store_read_role_response.json()["data"]["code"],
        employee_read_role_response.json()["data"]["code"],
    }
    assert {item["code"] for item in auth_summary_payload["permissions"]} == {
        "org.store.read",
        "org.node.read",
        "employee.read",
        "org.binding.read",
    }
