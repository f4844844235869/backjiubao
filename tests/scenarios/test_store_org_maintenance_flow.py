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


def test_store_org_maintenance_flow(client: TestClient) -> None:
    """验证门店与组织节点基础维护能力。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"maint_{random_lower_string()[:8]}",
            "name": "待维护门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    update_store_response = client.patch(
        f"{settings.API_V1_STR}/stores/{store_id}",
        headers=admin_headers,
        json={"name": "已维护门店", "status": "DISABLED"},
    )
    assert update_store_response.status_code == 200
    assert update_store_response.json()["data"]["name"] == "已维护门店"
    assert update_store_response.json()["data"]["status"] == "DISABLED"

    org_response = client.post(
        f"{settings.API_V1_STR}/org/nodes",
        headers=admin_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "待维护组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_id = org_response.json()["data"]["id"]

    update_org_response = client.patch(
        f"{settings.API_V1_STR}/org/nodes/{org_id}",
        headers=admin_headers,
        json={"name": "已维护组织", "sort_order": 10, "is_active": False},
    )
    assert update_org_response.status_code == 200
    assert update_org_response.json()["data"]["name"] == "已维护组织"
    assert update_org_response.json()["data"]["sort_order"] == 10
    assert update_org_response.json()["data"]["is_active"] is False
