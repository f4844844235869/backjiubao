from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_lower_string


def test_employee_rehire_flow(client: TestClient) -> None:
    """验证员工离职后保留历史任职记录，并以新员工身份重新入职且需重新授权。"""

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
            "code": f"rehire_store_{random_lower_string()[:8]}",
            "name": "复职测试门店",
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
            "name": "复职测试营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_node_id = org_response.json()["data"]["id"]

    permissions_response = client.get(
        f"{settings.API_V1_STR}/iam/permissions",
        headers=admin_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids = [
        item["id"]
        for item in permissions_response.json()["data"]
        if item["code"] == "org.store.read"
    ]
    assert len(permission_ids) == 1

    role_response = client.post(
        f"{settings.API_V1_STR}/iam/roles",
        headers=admin_headers,
        json={
            "code": f"rehire_role_{random_lower_string()[:8]}",
            "name": "复职门店查看角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["data"]["id"]

    assign_permission_response = client.put(
        f"{settings.API_V1_STR}/iam/roles/{role_id}",
        headers=admin_headers,
        json={"permission_ids": permission_ids},
    )
    assert assign_permission_response.status_code == 200

    common_mobile = "13800000188"
    common_name = "复职测试员工"

    first_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": common_name,
                "nickname": "第一次入职",
                "mobile": common_mobile,
            },
            "primary_org_node_id": org_node_id,
            "position_name": "服务员",
            "role_ids": [role_id],
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": store_id,
                    "org_node_id": None,
                }
            ],
        },
    )
    assert first_onboard_response.status_code == 201
    first_employee_payload = first_onboard_response.json()["data"]
    first_user_id = first_employee_payload["user"]["id"]
    first_username = first_employee_payload["user"]["username"]
    first_employee_no = first_employee_payload["profile"]["employee_no"]
    assert first_employee_no.startswith("YY")
    assert len(first_employee_no) == 6

    first_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": first_username, "password": "password1234"},
    )
    assert first_login_response.status_code == 200
    first_headers = {
        "Authorization": f"Bearer {first_login_response.json()['data']['access_token']}"
    }
    first_store_response = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=first_headers,
    )
    assert first_store_response.status_code == 200
    assert first_store_response.json()["data"][0]["id"] == store_id

    leave_response = client.post(
        f"{settings.API_V1_STR}/employees/{first_user_id}/leave",
        headers=admin_headers,
        json={"leave_reason": "个人原因离职"},
    )
    assert leave_response.status_code == 200
    assert leave_response.json()["data"]["employment_status"] == "LEFT"
    assert leave_response.json()["data"]["left_at"] is not None

    left_profile_response = client.get(
        f"{settings.API_V1_STR}/employees/{first_user_id}/profile",
        headers=admin_headers,
    )
    assert left_profile_response.status_code == 200
    assert left_profile_response.json()["data"]["employment_status"] == "LEFT"

    left_records_response = client.get(
        f"{settings.API_V1_STR}/employees/{first_user_id}/employment-records",
        headers=admin_headers,
    )
    assert left_records_response.status_code == 200
    left_records = left_records_response.json()["data"]
    assert len(left_records) == 1
    assert left_records[0]["employment_status"] == "LEFT"
    assert left_records[0]["leave_reason"] == "个人原因离职"

    old_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": first_username, "password": "password1234"},
    )
    assert old_login_response.status_code == 403
    assert old_login_response.json()["code"] == "USER_DISABLED"

    second_onboard_response = client.post(
        f"{settings.API_V1_STR}/employees/onboard",
        headers=admin_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": common_name,
                "nickname": "再次入职",
                "mobile": common_mobile,
            },
            "primary_org_node_id": org_node_id,
            "position_name": "服务员",
        },
    )
    assert second_onboard_response.status_code == 201
    second_employee_payload = second_onboard_response.json()["data"]
    second_user_id = second_employee_payload["user"]["id"]
    second_username = second_employee_payload["user"]["username"]
    second_employee_no = second_employee_payload["profile"]["employee_no"]
    assert second_employee_no.startswith("YY")
    assert len(second_employee_no) == 6
    assert second_employee_no != first_employee_no
    assert second_employee_no != first_employee_no

    assert second_user_id != first_user_id
    assert second_employee_payload["profile"]["employment_status"] == "ACTIVE"
    assert second_employee_payload["user"]["mobile"] == common_mobile

    second_records_response = client.get(
        f"{settings.API_V1_STR}/employees/{second_user_id}/employment-records",
        headers=admin_headers,
    )
    assert second_records_response.status_code == 200
    second_records = second_records_response.json()["data"]
    assert len(second_records) == 1
    assert second_records[0]["employment_status"] == "ACTIVE"
    assert second_records[0]["left_at"] is None

    new_login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": second_username, "password": "password1234"},
    )
    assert new_login_response.status_code == 200
    second_headers = {
        "Authorization": f"Bearer {new_login_response.json()['data']['access_token']}"
    }

    second_store_response_before_grant = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=second_headers,
    )
    assert second_store_response_before_grant.status_code == 403
    assert second_store_response_before_grant.json()["code"] == "AUTH_PERMISSION_DENIED"

    assign_role_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{second_user_id}/roles",
        headers=admin_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200

    assign_scope_response = client.put(
        f"{settings.API_V1_STR}/iam/users/{second_user_id}/data-scopes",
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

    second_store_response_after_grant = client.get(
        f"{settings.API_V1_STR}/stores/",
        headers=second_headers,
    )
    assert second_store_response_after_grant.status_code == 200
    assert second_store_response_after_grant.json()["data"][0]["id"] == store_id
