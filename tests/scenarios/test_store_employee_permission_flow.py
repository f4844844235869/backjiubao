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


def test_store_employee_permission_flow(client: TestClient) -> None:
    """验证创建门店后的员工新增权限、角色分配权限和数据范围边界。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"store_a_{random_lower_string()[:8]}",
            "name": "一号门店",
            "status": "ACTIVE",
        },
    )
    assert store_a_response.status_code == 201
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"store_b_{random_lower_string()[:8]}",
            "name": "二号门店",
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
            "name": "一号店营运部",
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
            "name": "二号店营运部",
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
    permissions = permissions_response.json()["data"]
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}

    store_manager_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"store_manager_{random_lower_string()[:8]}",
            "name": "门店经理",
            "status": "ACTIVE",
        },
    )
    assert store_manager_role_response.status_code == 201
    store_manager_role_id = store_manager_role_response.json()["data"]["id"]

    assign_store_manager_permissions_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{store_manager_role_id}",
        headers=admin_headers,
        json={
                "permission_ids": [
                    permission_ids_by_code["employee.create"],
                    permission_ids_by_code["employee.bind_org"],
                    permission_ids_by_code["employee.read"],
                    permission_ids_by_code["iam.user.read"],
                    permission_ids_by_code["iam.user.assign_role"],
                    permission_ids_by_code["iam.user.assign_scope"],
                    permission_ids_by_code["org.binding.read"],
                    permission_ids_by_code["org.store.read"],
                    permission_ids_by_code["org.node.read"],
                ]
        },
    )
    assert assign_store_manager_permissions_response.status_code == 200

    basic_staff_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"basic_staff_{random_lower_string()[:8]}",
            "name": "基础员工角色",
            "status": "ACTIVE",
        },
    )
    assert basic_staff_role_response.status_code == 201
    basic_staff_role_id = basic_staff_role_response.json()["data"]["id"]

    manager_username = random_lower_string()
    manager_password = "password1234"
    manager_create_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": manager_username,
            "email": None,
            "password": manager_password,
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "一号店经理",
            "nickname": "经理",
            "mobile": "13800000111",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert manager_create_response.status_code == 201
    manager_user_id = manager_create_response.json()["data"]["id"]

    assign_manager_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [store_manager_role_id]},
    )
    assert assign_manager_role_response.status_code == 200

    bind_manager_org_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": manager_user_id,
            "org_node_id": org_a_id,
            "is_primary": True,
            "position_name": "店经理",
        },
    )
    assert bind_manager_org_response.status_code == 201

    assign_manager_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": store_a_id,
                    "org_node_id": None,
                }
            ]
        },
    )
    assert assign_manager_scope_response.status_code == 200

    manager_auth_summary_response = client.get(
        f"{settings.API_V1_STR}/iam/users/{manager_user_id}/authorization-summary",
        headers=admin_headers,
    )
    assert manager_auth_summary_response.status_code == 200
    manager_auth_summary = manager_auth_summary_response.json()["data"]
    assert {item["code"] for item in manager_auth_summary["roles"]} == {
        store_manager_role_response.json()["data"]["code"]
    }
    assert "employee.create" in {
        item["code"] for item in manager_auth_summary["permissions"]
    }
    assert manager_auth_summary["data_scopes"][0]["scope_type"] == "STORE"
    assert manager_auth_summary["data_scopes"][0]["store_id"] == store_a_id

    manager_headers = _login(client, manager_username, manager_password)

    onboard_same_store_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=manager_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "一号店员工",
                "nickname": "小王",
                "mobile": "13800000112",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
        },
    )
    assert onboard_same_store_response.status_code == 201
    onboard_same_store_payload = onboard_same_store_response.json()["data"]
    assert onboard_same_store_payload["user"]["email"] is None
    assert onboard_same_store_payload["primary_binding"]["org_node_id"] == org_a_id
    assert onboard_same_store_payload["profile"]["employment_status"] == "ACTIVE"
    same_store_employee_id = onboard_same_store_payload["user"]["id"]

    employee_headers = _login(
        client,
        onboard_same_store_payload["user"]["username"],
        "password1234",
    )
    employee_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=employee_headers,
    )
    assert employee_me_response.status_code == 200
    assert employee_me_response.json()["data"]["primary_store_id"] == store_a_id

    store_list_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=manager_headers,
    )
    assert store_list_response.status_code == 200
    visible_store_ids = {item["id"] for item in store_list_response.json()["data"]}
    assert visible_store_ids == {store_a_id}

    org_nodes_response = client.get(
        f"{settings.API_V1_STR}/org/nodes",
        headers=manager_headers,
    )
    assert org_nodes_response.status_code == 200
    visible_org_ids = {item["id"] for item in org_nodes_response.json()["data"]}
    assert visible_org_ids == {org_a_id}

    other_store_employee_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": random_lower_string(),
            "email": None,
            "password": "password1234",
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "二号店员工",
            "nickname": "外店员工",
            "mobile": "13800000116",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert other_store_employee_response.status_code == 201
    other_store_employee_id = other_store_employee_response.json()["data"]["id"]

    other_store_binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": other_store_employee_id,
            "org_node_id": org_b_id,
            "is_primary": True,
            "position_name": "收银员",
        },
    )
    assert other_store_binding_response.status_code == 201

    employee_profile_same_store_response = client.get(
        f"{settings.API_V1_STR}/employees/{same_store_employee_id}/profile",
        headers=manager_headers,
    )
    assert employee_profile_same_store_response.status_code == 200

    employee_profile_other_store_response = client.get(
        f"{settings.API_V1_STR}/employees/{other_store_employee_id}/profile",
        headers=manager_headers,
    )
    assert employee_profile_other_store_response.status_code == 403
    assert employee_profile_other_store_response.json()["code"] == "DATA_SCOPE_DENIED"

    bindings_response = client.get(
        f"{settings.API_V1_STR}/org/bindings",
        headers=manager_headers,
    )
    assert bindings_response.status_code == 200
    visible_binding_org_ids = {item["org_node_id"] for item in bindings_response.json()["data"]}
    assert org_a_id in visible_binding_org_ids
    assert org_b_id not in visible_binding_org_ids

    cross_store_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=manager_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "二号店员工",
                "nickname": "小赵",
                "mobile": "13800000113",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "收银员",
        },
    )
    assert cross_store_onboard_response.status_code == 403
    assert cross_store_onboard_response.json()["code"] == "DATA_SCOPE_DENIED"

    onboard_with_role_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=manager_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "尝试分配角色员工",
                "nickname": "小周",
                "mobile": "13800000114",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
            "role_ids": [basic_staff_role_id],
        },
    )
    assert onboard_with_role_response.status_code == 403
    assert onboard_with_role_response.json()["code"] == "AUTH_PERMISSION_DENIED"
    assert "employee.assign_role" in onboard_with_role_response.json()["message"]

    onboard_with_scope_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=manager_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "尝试分配范围员工",
                "nickname": "小吴",
                "mobile": "13800000115",
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": store_a_id,
                    "org_node_id": None,
                }
            ],
        },
    )
    assert onboard_with_scope_response.status_code == 403
    assert onboard_with_scope_response.json()["code"] == "AUTH_PERMISSION_DENIED"
    assert "employee.assign_scope" in onboard_with_scope_response.json()["message"]

    admin_like_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"store_admin_like_{random_lower_string()[:8]}",
            "name": "高权限角色",
            "status": "ACTIVE",
        },
    )
    assert admin_like_role_response.status_code == 201
    admin_like_role_id = admin_like_role_response.json()["data"]["id"]

    assign_high_role_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{admin_like_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["employee.create"],
                permission_ids_by_code["employee.bind_org"],
                permission_ids_by_code["employee.read"],
                permission_ids_by_code["iam.role.assign_permission"],
            ]
        },
    )
    assert assign_high_role_permission_response.status_code == 200

    manager_assign_high_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{same_store_employee_id}/roles",
        headers=manager_headers,
        json={"role_ids": [admin_like_role_id]},
    )
    assert manager_assign_high_role_response.status_code == 403
    assert manager_assign_high_role_response.json()["code"] == "AUTH_GRANT_DENIED"
    assert "高权限角色" in manager_assign_high_role_response.json()["message"]

    manager_assign_cross_store_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{same_store_employee_id}/data-scopes",
        headers=manager_headers,
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
    assert manager_assign_cross_store_scope_response.status_code == 403
    assert manager_assign_cross_store_scope_response.json()["code"] == "AUTH_GRANT_DENIED"
