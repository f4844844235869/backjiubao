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


def test_org_inheritance_flow(client: TestClient) -> None:
    """验证父组织节点的数据范围会向下覆盖子节点。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"org_inherit_{random_lower_string()[:8]}",
            "name": "组织继承门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    parent_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "营运中心",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert parent_org_response.status_code == 201
    parent_org_id = parent_org_response.json()["data"]["id"]

    child_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": parent_org_id,
            "name": "一组服务部",
            "prefix": "FW",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert child_org_response.status_code == 201
    child_org_id = child_org_response.json()["data"]["id"]

    sibling_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "市场中心",
            "prefix": "SC",
            "node_type": "DEPARTMENT",
            "sort_order": 2,
            "is_active": True,
        },
    )
    assert sibling_org_response.status_code == 201
    sibling_org_id = sibling_org_response.json()["data"]["id"]

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    leader_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"org_leader_{random_lower_string()[:8]}",
            "name": "组织主管",
            "status": "ACTIVE",
        },
    )
    assert leader_role_response.status_code == 201
    leader_role_id = leader_role_response.json()["data"]["id"]

    assign_permissions_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{leader_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["employee.create"],
                permission_ids_by_code["employee.bind_org"],
                permission_ids_by_code["employee.read"],
                permission_ids_by_code["org.node.read"],
                permission_ids_by_code["org.binding.read"],
            ]
        },
    )
    assert assign_permissions_response.status_code == 200

    leader_username = random_lower_string()
    leader_create_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": leader_username,
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "组织主管",
            "nickname": "主管",
            "mobile": "13800000166",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert leader_create_response.status_code == 201
    leader_user_id = leader_create_response.json()["data"]["id"]

    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{leader_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [leader_role_id]},
    ).status_code == 200
    assert client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": leader_user_id,
            "org_node_id": parent_org_id,
            "is_primary": True,
            "position_name": "主管",
        },
    ).status_code == 201
    assert client.put(
        f"{settings.API_V1_STR}/iam/users/{leader_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {
                    "scope_type": "DEPARTMENT",
                    "store_id": None,
                    "org_node_id": parent_org_id,
                }
            ]
        },
    ).status_code == 200

    leader_headers = _login(client, leader_username, "password1234")

    org_nodes_response = client.get(
        f"{settings.API_V1_STR}/org/nodes",
        headers=leader_headers,
    )
    assert org_nodes_response.status_code == 200
    visible_org_ids = {item["id"] for item in org_nodes_response.json()["data"]}
    assert parent_org_id in visible_org_ids
    assert child_org_id in visible_org_ids

    onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=leader_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "子部门员工",
                "nickname": "子部门",
                "mobile": "13800000167",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": child_org_id,
            "position_name": "服务员",
        },
    )
    assert onboard_response.status_code == 201
    child_employee_id = onboard_response.json()["data"]["user"]["id"]

    child_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{child_employee_id}/profile",
        headers=leader_headers,
    )
    assert child_profile_response.status_code == 200
    assert child_profile_response.json()["data"]["user_id"] == child_employee_id

    bindings_response = client.get(
        f"{settings.API_V1_STR}/org/bindings",
        headers=leader_headers,
    )
    assert bindings_response.status_code == 200
    visible_binding_org_ids = {item["org_node_id"] for item in bindings_response.json()["data"]}
    assert child_org_id in visible_binding_org_ids

    members_response = client.get(
        f"{settings.API_V1_STR}/org/nodes/{parent_org_id}/members",
        headers=leader_headers,
    )
    assert members_response.status_code == 200
    members_payload = members_response.json()["data"]
    assert {item["id"] for item in members_payload["org_nodes"]} >= {
        parent_org_id,
        child_org_id,
    }
    child_node = next(
        item for item in members_payload["org_nodes"] if item["id"] == child_org_id
    )
    assert child_node["parent_id"] == parent_org_id
    assert {item["org_node_id"] for item in members_payload["members"]} >= {
        parent_org_id,
        child_org_id,
    }
    assert child_employee_id in {
        item["user"]["id"] for item in members_payload["members"]
    }
    child_member = next(
        item
        for item in members_payload["members"]
        if item["user"]["id"] == child_employee_id
    )
    assert child_member["org_node_name"] == "一组服务部"
    assert child_member["store_name"] == "组织继承门店"

    sibling_members_response = client.get(
        f"{settings.API_V1_STR}/org/nodes/{sibling_org_id}/members",
        headers=leader_headers,
    )
    assert sibling_members_response.status_code == 403
    assert sibling_members_response.json()["code"] == "DATA_SCOPE_DENIED"
