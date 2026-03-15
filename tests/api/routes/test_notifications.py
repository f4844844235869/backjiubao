from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string


def test_list_my_notifications_after_profile_update(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    update_response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"nickname": "通知测试"},
    )
    assert update_response.status_code == 200

    response = client.get(
        f"{settings.API_V1_STR}/notifications/me",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["unread_count"] >= 1
    assert any(
        item["notification_type"] == "PROFILE_UPDATED"
        for item in payload["data"]["items"]
    )


def test_mark_notification_as_read(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    update_response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"nickname": "已读通知"},
    )
    assert update_response.status_code == 200

    list_response = client.get(
        f"{settings.API_V1_STR}/notifications/me",
        headers=normal_user_token_headers,
    )
    assert list_response.status_code == 200
    notification_id = list_response.json()["data"]["items"][0]["id"]

    read_response = client.patch(
        f"{settings.API_V1_STR}/notifications/{notification_id}/read",
        headers=normal_user_token_headers,
    )

    assert read_response.status_code == 200
    payload = read_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["is_read"] is True
    assert payload["data"]["read_at"] is not None


def test_reset_password_creates_notification_for_target_user(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    username = random_lower_string()
    password = "password1234"
    new_password = "new-password1234"
    create_response = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": random_email(),
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "通知员工",
            "nickname": "通知员工",
            "mobile": "13800000111",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    reset_response = client.patch(
        f"{settings.API_V1_STR}/users/{user_id}/reset-password",
        headers=superuser_token_headers,
        json={"new_password": new_password},
    )
    assert reset_response.status_code == 200

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/backend/password-login",
        json={"account": username, "password": new_password},
    )
    assert login_response.status_code == 200
    user_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    notification_response = client.get(
        f"{settings.API_V1_STR}/notifications/me",
        headers=user_headers,
    )
    assert notification_response.status_code == 200
    items = notification_response.json()["data"]["items"]
    assert any(item["notification_type"] == "PASSWORD_RESET" for item in items)
