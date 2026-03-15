from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string


def test_employee_onboarding_flow(client: TestClient) -> None:
    """模拟管理员完成员工建档、授权，员工再登录后台的完整流程。"""

    admin_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={
            "account": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )
    assert admin_login_response.status_code == 200
    admin_token = admin_login_response.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"SCENE-{random_lower_string()[:8]}",
            "name": "场景测试门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_payload = store_response.json()
    store_id = store_payload["data"]["id"]
    assert store_payload["data"]["name"] == "场景测试门店"

    org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "场景测试营运部",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_payload = org_response.json()
    org_node_id = org_payload["data"]["id"]
    assert org_payload["data"]["store_id"] == store_id

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permissions_payload = permissions_response.json()["data"]
    permission_ids = [
        item["id"]
        for item in permissions_payload
        if item["code"] in {"org.store.read", "org.node.read"}
    ]
    assert len(permission_ids) == 2

    role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"store_mgr_{random_lower_string()[:8]}",
            "name": "门店查看角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_payload = role_response.json()
    role_id = role_payload["data"]["id"]

    assign_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{role_id}",
        headers=admin_headers,
        json={"permission_ids": permission_ids},
    )
    assert assign_permission_response.status_code == 200
    assigned_permission_codes = {
        item["code"] for item in assign_permission_response.json()["data"]["permissions"]
    }
    assert assigned_permission_codes == {"org.store.read", "org.node.read"}

    username = random_lower_string()
    employee_email = random_email()
    employee_password = "password1234"
    employee_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=admin_headers,
        json={
            "username": username,
            "email": employee_email,
            "password": employee_password,
            "user_type": "EMPLOYEE",
            "is_active": True,
            "is_superuser": False,
            "full_name": "场景测试员工",
            "nickname": "小李",
            "mobile": "13800000066",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert employee_response.status_code == 201
    employee_payload = employee_response.json()["data"]
    employee_user_id = employee_payload["id"]
    assert employee_payload["user_type"] == "EMPLOYEE"

    employee_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_user_id}/profile",
        headers=admin_headers,
    )
    assert employee_profile_response.status_code == 200
    employee_profile_payload = employee_profile_response.json()["data"]
    assert employee_profile_payload["user_id"] == employee_user_id
    assert employee_profile_payload["employment_status"] == "ACTIVE"

    binding_response = client.post(
        f"{settings.API_V1_STR}/org/bindings",
        headers=admin_headers,
        json={
            "user_id": employee_user_id,
            "org_node_id": org_node_id,
            "is_primary": True,
            "position_name": "店长",
        },
    )
    assert binding_response.status_code == 201
    binding_payload = binding_response.json()["data"]
    assert binding_payload["user_id"] == employee_user_id
    assert binding_payload["org_node_id"] == org_node_id
    assert binding_payload["is_primary"] is True

    assign_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200
    assigned_role_payload = assign_role_response.json()["data"]
    assert len(assigned_role_payload) == 1
    assert assigned_role_payload[0]["id"] == role_id

    assign_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{employee_user_id}/data-scopes",
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
    assert assign_scope_response.status_code == 200
    assigned_scope_payload = assign_scope_response.json()["data"]
    assert len(assigned_scope_payload) == 1
    assert assigned_scope_payload[0]["scope_type"] == "STORE"
    assert assigned_scope_payload[0]["store_id"] == store_id

    employee_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": username, "password": employee_password},
    )
    assert employee_login_response.status_code == 200
    employee_token = employee_login_response.json()["data"]["access_token"]
    employee_headers = {"Authorization": f"Bearer {employee_token}"}

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=employee_headers,
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()["data"]
    assert me_payload["id"] == employee_user_id
    assert role_payload["data"]["code"] in me_payload["roles"]
    assert "org.store.read" in me_payload["permissions"]
    assert me_payload["data_scopes"][0]["scope_type"] == "STORE"
    assert me_payload["data_scopes"][0]["store_id"] == store_id

    store_list_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=employee_headers,
    )
    assert store_list_response.status_code == 200
    store_ids = {item["id"] for item in store_list_response.json()["data"]}
    assert store_id in store_ids

    users_response = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=employee_headers,
    )
    assert users_response.status_code == 403
    assert users_response.json()["code"] == "AUTH_PERMISSION_DENIED"
