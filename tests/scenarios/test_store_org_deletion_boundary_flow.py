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


def test_store_org_deletion_boundary_flow(client: TestClient) -> None:
    """验证门店和组织节点删除时的在用、历史、空数据边界。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    active_store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"active_{random_lower_string()[:8]}",
            "name": "在用门店",
            "status": "ACTIVE",
        },
    )
    assert active_store_response.status_code == 201
    active_store_id = active_store_response.json()["data"]["id"]

    active_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": active_store_id,
            "parent_id": None,
            "name": "在用组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert active_org_response.status_code == 201
    active_org_id = active_org_response.json()["data"]["id"]

    onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "删除边界员工",
                "nickname": "边界",
                "mobile": f"134{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": active_org_id,
            "position_name": "服务员",
        },
    )
    assert onboard_response.status_code == 201
    active_user_id = onboard_response.json()["data"]["user"]["id"]

    delete_active_org_response = client.delete(
        f"{settings.API_V1_STR}/org/nodes/{active_org_id}",
        headers=admin_headers,
    )
    assert delete_active_org_response.status_code == 409

    delete_active_store_response = client.delete(
        f"{settings.API_V1_STR}/stores/{active_store_id}",
        headers=admin_headers,
    )
    assert delete_active_store_response.status_code == 409

    leave_response = client.post(
        f"{settings.API_V1_STR}/employees/{active_user_id}/leave",
        headers=admin_headers,
        json={"leave_reason": "删除边界测试离职"},
    )
    assert leave_response.status_code == 200

    delete_history_org_response = client.delete(
        f"{settings.API_V1_STR}/org/nodes/{active_org_id}",
        headers=admin_headers,
    )
    assert delete_history_org_response.status_code == 200
    assert "组织节点已停用" in delete_history_org_response.json()["message"]

    delete_history_store_response = client.delete(
        f"{settings.API_V1_STR}/stores/{active_store_id}",
        headers=admin_headers,
    )
    assert delete_history_store_response.status_code == 200
    assert "门店已停用" in delete_history_store_response.json()["message"]

    empty_store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"empty_{random_lower_string()[:8]}",
            "name": "空门店",
            "status": "ACTIVE",
        },
    )
    assert empty_store_response.status_code == 201
    empty_store_id = empty_store_response.json()["data"]["id"]

    empty_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": empty_store_id,
            "parent_id": None,
            "name": "空组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert empty_org_response.status_code == 201
    empty_org_id = empty_org_response.json()["data"]["id"]

    child_org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": empty_store_id,
            "parent_id": empty_org_id,
            "name": "子组织",
            "node_type": "TEAM",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert child_org_response.status_code == 201

    delete_parent_response = client.delete(
        f"{settings.API_V1_STR}/org/nodes/{empty_org_id}",
        headers=admin_headers,
    )
    assert delete_parent_response.status_code == 409

    delete_child_response = client.delete(
        f"{settings.API_V1_STR}/org/nodes/{child_org_response.json()['data']['id']}",
        headers=admin_headers,
    )
    assert delete_child_response.status_code == 200

    delete_empty_org_response = client.delete(
        f"{settings.API_V1_STR}/org/nodes/{empty_org_id}",
        headers=admin_headers,
    )
    assert delete_empty_org_response.status_code == 200

    delete_empty_store_response = client.delete(
        f"{settings.API_V1_STR}/stores/{empty_store_id}",
        headers=admin_headers,
    )
    assert delete_empty_store_response.status_code == 200
