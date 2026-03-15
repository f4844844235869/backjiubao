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


def test_backend_miniapp_end_to_end_flow(client: TestClient) -> None:
    """串联后台建档授权与小程序按门店访问员工数据的完整流程。"""

    admin_headers = _login(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )

    store_a_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"e2e_store_a_{random_lower_string()[:8]}",
            "name": "端到端一号店",
            "status": "ACTIVE",
        },
    )
    assert store_a_response.status_code == 201
    store_a_id = store_a_response.json()["data"]["id"]

    store_b_response = client.post(
        f"{settings.API_V1_STR}/stores/",
        headers=admin_headers,
        json={
            "code": f"e2e_store_b_{random_lower_string()[:8]}",
            "name": "端到端二号店",
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
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    miniapp_role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"e2e_miniapp_reader_{random_lower_string()[:8]}",
            "name": "端到端小程序查看角色",
            "status": "ACTIVE",
        },
    )
    assert miniapp_role_response.status_code == 201
    miniapp_role_id = miniapp_role_response.json()["data"]["id"]

    assign_permissions_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{miniapp_role_id}",
        headers=admin_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["employee.read"],
                permission_ids_by_code["org.store.read"],
                permission_ids_by_code["org.node.read"],
            ]
        },
    )
    assert assign_permissions_response.status_code == 200

    common_mobile = f"135{abs(hash(random_lower_string())) % 10**8:08d}"

    employee_a_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "端到端一号店员工",
                "nickname": "E2E一号店",
                "mobile": common_mobile,
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_a_id,
            "position_name": "服务员",
        },
    )
    assert employee_a_response.status_code == 201
    employee_a_id = employee_a_response.json()["data"]["user"]["id"]

    employee_b_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "端到端二号店员工",
                "nickname": "E2E二号店",
                "mobile": common_mobile,
            },
            "employee_no": f"EMP{random_lower_string()[:6]}",
            "primary_org_node_id": org_b_id,
            "position_name": "服务员",
        },
    )
    assert employee_b_response.status_code == 201
    employee_b_id = employee_b_response.json()["data"]["user"]["id"]

    miniapp_login_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/code-login",
        json={"code": "wx-e2e-miniapp", "app_id": "wx-e2e-miniapp"},
    )
    assert miniapp_login_response.status_code == 200
    miniapp_headers = {
        "Authorization": f"Bearer {miniapp_login_response.json()['data']['access_token']}"
    }

    bind_phone_response = client.post(
        f"{settings.API_V1_STR}/auth/miniapp/bind-phone",
        headers=miniapp_headers,
        json={"phone": common_mobile, "country_code": "+86"},
    )
    assert bind_phone_response.status_code == 200

    me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=miniapp_headers,
    )
    assert me_response.status_code == 200
    miniapp_user_id = me_response.json()["data"]["id"]
    assert me_response.json()["data"]["mobile"] == common_mobile

    assign_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{miniapp_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [miniapp_role_id]},
    )
    assert assign_role_response.status_code == 200

    assign_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{miniapp_user_id}/data-scopes",
        headers=admin_headers,
        json={
            "scopes": [
                {"scope_type": "STORE", "store_id": store_a_id, "org_node_id": None},
                {"scope_type": "STORE", "store_id": store_b_id, "org_node_id": None},
            ]
        },
    )
    assert assign_scope_response.status_code == 200

    summary_response = client.get(
        f"{settings.API_V1_STR}/iam/users/{miniapp_user_id}/authorization-summary",
        headers=admin_headers,
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()["data"]
    assert miniapp_role_response.json()["data"]["code"] in {
        item["code"] for item in summary_payload["roles"]
    }
    assert "employee.read" in {
        item["code"] for item in summary_payload["permissions"]
    }

    all_related_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=miniapp_headers,
    )
    assert all_related_response.status_code == 200
    assert {
        item["user_id"] for item in all_related_response.json()["data"]["related_employees"]
    } == {employee_a_id, employee_b_id}

    store_a_headers = {**miniapp_headers, "X-Current-Store-Id": store_a_id}
    store_a_me_response = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers=store_a_headers,
    )
    assert store_a_me_response.status_code == 200
    assert store_a_me_response.json()["data"]["current_store_id"] == store_a_id

    store_a_related_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=store_a_headers,
    )
    assert store_a_related_response.status_code == 200
    assert [item["user_id"] for item in store_a_related_response.json()["data"]["related_employees"]] == [
        employee_a_id
    ]

    store_a_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_a_id}/profile",
        headers=store_a_headers,
    )
    assert store_a_profile_response.status_code == 200

    store_a_forbidden_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_b_id}/profile",
        headers=store_a_headers,
    )
    assert store_a_forbidden_response.status_code == 403
    assert store_a_forbidden_response.json()["code"] == "DATA_SCOPE_DENIED"

    store_b_headers = {**miniapp_headers, "X-Current-Store-Id": store_b_id}
    store_b_related_response = client.get(
        f"{settings.API_V1_STR}/auth/miniapp/phone-related-employees",
        headers=store_b_headers,
    )
    assert store_b_related_response.status_code == 200
    assert [item["user_id"] for item in store_b_related_response.json()["data"]["related_employees"]] == [
        employee_b_id
    ]

    store_b_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{employee_b_id}/profile",
        headers=store_b_headers,
    )
    assert store_b_profile_response.status_code == 200
