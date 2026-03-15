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


def test_employee_position_change_flow(client: TestClient) -> None:
    """验证员工组织与岗位变更后，主归属、组织绑定和任职记录会同步更新。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"position_{random_lower_string()[:8]}",
            "name": "岗位变更门店",
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
            "name": "营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_id = org_response.json()["data"]["id"]
    target_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "前厅部",
            "prefix": "QT",
            "node_type": "DEPARTMENT",
            "sort_order": 2,
            "is_active": True,
        },
    )
    assert target_org_response.status_code == 201
    target_org_id = target_org_response.json()["data"]["id"]

    onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "岗位变更员工",
                "nickname": "岗位变更",
                "mobile": f"137{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": org_id,
            "position_name": "服务员",
            "role_ids": [],
            "scopes": [],
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]
    binding_id = onboard_response.json()["data"]["primary_binding"]["id"]

    update_binding_response = client.patch(
        f"{settings.API_V1_STR}/org/bindings/{binding_id}",
        headers=admin_headers,
        json={"org_node_id": target_org_id, "position_name": "值班经理"},
    )
    assert update_binding_response.status_code == 200
    assert update_binding_response.json()["data"]["org_node_id"] == target_org_id
    assert update_binding_response.json()["data"]["position_name"] == "值班经理"

    bindings_response = client.get(
        f"{settings.API_V1_STR}/org/bindings?user_id={user_id}",
        headers=admin_headers,
    )
    assert bindings_response.status_code == 200
    assert bindings_response.json()["data"][0]["org_node_id"] == target_org_id
    assert bindings_response.json()["data"][0]["position_name"] == "值班经理"

    records_response = client.get(
        f"{settings.API_V1_STR}/employees/{user_id}/employment-records",
        headers=admin_headers,
    )
    assert records_response.status_code == 200
    assert records_response.json()["data"][0]["org_node_id"] == target_org_id
    assert records_response.json()["data"][0]["position_name"] == "值班经理"

    me_headers = _login(
        client,
        onboard_response.json()["data"]["user"]["username"],
        "password1234",
    )
    me_response = client.get(f"{settings.API_V1_STR}/auth/me", headers=me_headers)
    assert me_response.status_code == 200
    me_payload = me_response.json()["data"]
    assert me_payload["primary_store_id"] == store_id
    assert me_payload["primary_department_id"] == target_org_id
    assert me_payload["current_org_node_id"] == target_org_id

    profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{user_id}/profile",
        headers=admin_headers,
    )
    assert profile_response.status_code == 200
