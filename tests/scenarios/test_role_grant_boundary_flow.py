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


def test_role_grant_boundary_flow(client: TestClient) -> None:
    """验证角色可见/可分配边界，以及动态新角色默认归属创建者和超管。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    regional_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"scenario_regional_{random_lower_string()[:8]}",
            "name": "场景区域经理",
            "status": "ACTIVE",
        },
    )
    assert regional_role_response.status_code == 201
    regional_role_id = regional_role_response.json()["data"]["id"]

    store_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"scenario_store_{random_lower_string()[:8]}",
            "name": "场景店长",
            "status": "ACTIVE",
        },
    )
    assert store_role_response.status_code == 201
    store_role_id = store_role_response.json()["data"]["id"]

    staff_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"scenario_staff_{random_lower_string()[:8]}",
            "name": "场景门店员工",
            "status": "ACTIVE",
        },
    )
    assert staff_role_response.status_code == 201
    staff_role_id = staff_role_response.json()["data"]["id"]

    regional_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{regional_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["iam.role.read"],
                permission_ids_by_code["iam.role.create"],
                permission_ids_by_code["iam.user.assign_role"],
            ]
        },
    )
    assert regional_permission_response.status_code == 200

    store_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{store_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["iam.role.read"],
                permission_ids_by_code["iam.role.create"],
                permission_ids_by_code["iam.user.assign_role"],
            ]
        },
    )
    assert store_permission_response.status_code == 200

    regional_grant_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{regional_role_id}",
        headers=admin_headers,
        json={"grantable_role_ids": [store_role_id, staff_role_id]},
    )
    assert regional_grant_response.status_code == 200

    store_grant_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{store_role_id}",
        headers=admin_headers,
        json={"grantable_role_ids": [staff_role_id]},
    )
    assert store_grant_response.status_code == 200

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"role_grant_store_{random_lower_string()[:8]}",
            "name": "角色边界门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "角色边界组织",
            "prefix": "JB",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_id = org_response.json()["data"]["id"]

    manager_username = random_lower_string()
    manager_password = "password1234"
    manager_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": manager_username,
            "email": None,
            "password": manager_password,
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "角色边界店长",
            "nickname": "角色边界",
            "mobile": f"138{abs(hash(random_lower_string())) % 10**8:08d}",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert manager_response.status_code == 201
    manager_user_id = manager_response.json()["data"]["id"]

    assign_manager_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [store_role_id]},
    )
    assert assign_manager_role_response.status_code == 200
    manager_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": manager_user_id,
            "org_node_id": org_id,
            "is_primary": True,
            "position_name": "店长",
        },
    )
    assert manager_binding_response.status_code == 201
    manager_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": store_id,
                    "org_node_id": None,
                }
            ]
        },
    )
    assert manager_scope_response.status_code == 200

    employee_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": random_lower_string(),
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "角色边界员工",
            "nickname": "待授权员工",
            "mobile": f"137{abs(hash(random_lower_string())) % 10**8:08d}",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert employee_response.status_code == 201
    employee_user_id = employee_response.json()["data"]["id"]
    employee_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": employee_user_id,
            "org_node_id": org_id,
            "is_primary": True,
            "position_name": "员工",
        },
    )
    assert employee_binding_response.status_code == 201

    manager_headers = _login(client, manager_username, manager_password)

    manager_roles_response = client.get(
        f"{settings.API_V1_STR}/iam/roles",
        headers=manager_headers,
    )
    assert manager_roles_response.status_code == 200
    visible_role_ids = {item["id"] for item in manager_roles_response.json()["data"]}
    assert store_role_id in visible_role_ids
    assert staff_role_id in visible_role_ids
    assert regional_role_id not in visible_role_ids

    denied_assign_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers=manager_headers,
        json={"role_ids": [regional_role_id]},
    )
    assert denied_assign_response.status_code == 403
    assert denied_assign_response.json()["code"] == "AUTH_GRANT_DENIED"

    allowed_assign_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers=manager_headers,
        json={"role_ids": [staff_role_id]},
    )
    assert allowed_assign_response.status_code == 200
    assert allowed_assign_response.json()["data"][0]["id"] == staff_role_id

    custom_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=manager_headers,
        json={
            "code": f"scenario_custom_{random_lower_string()[:8]}",
            "name": "店长自建角色",
            "status": "ACTIVE",
        },
    )
    assert custom_role_response.status_code == 201
    custom_role_id = custom_role_response.json()["data"]["id"]

    manager_roles_after_create_response = client.get(
        f"{settings.API_V1_STR}/iam/roles",
        headers=manager_headers,
    )
    assert manager_roles_after_create_response.status_code == 200
    assert custom_role_id in {
        item["id"] for item in manager_roles_after_create_response.json()["data"]
    }

    admin_roles_response = client.get(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
    )
    assert admin_roles_response.status_code == 200
    assert custom_role_id in {
        item["id"] for item in admin_roles_response.json()["data"]
    }

    admin_assign_custom_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [custom_role_id]},
    )
    assert admin_assign_custom_role_response.status_code == 200
    assert admin_assign_custom_role_response.json()["data"][0]["id"] == custom_role_id
