from fastapi.testclient import TestClient

from tests.utils.utils import random_email, random_lower_string


def test_create_store(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-{random_lower_string()[:8]}",
            "name": "测试门店",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["name"] == "测试门店"


def test_update_store(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-UP-{random_lower_string()[:8]}",
            "name": "原门店名称",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    store_id = create_response.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/stores/{store_id}",
        headers=superuser_token_headers,
        json={"name": "新门店名称", "status": "DISABLED"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["name"] == "新门店名称"
    assert payload["data"]["status"] == "DISABLED"


def test_update_store_code_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    first_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-C1-{random_lower_string()[:8]}",
            "name": "门店一",
            "status": "ACTIVE",
        },
    )
    second_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-C2-{random_lower_string()[:8]}",
            "name": "门店二",
            "status": "ACTIVE",
        },
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.patch(
        f"/api/v1/stores/{second_response.json()['data']['id']}",
        headers=superuser_token_headers,
        json={"code": first_response.json()["data"]["code"]},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "STORE_CODE_EXISTS"


def test_delete_store_success_when_unreferenced(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-DEL-{random_lower_string()[:8]}",
            "name": "可删除门店",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    store_id = create_response.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/stores/{store_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    assert response.json()["code"] == "SUCCESS"

    list_response = client.get("/api/v1/stores/", headers=superuser_token_headers)
    assert list_response.status_code == 200
    assert store_id not in {item["id"] for item in list_response.json()["data"]}


def test_delete_store_returns_conflict_when_in_use(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-INUSE-{random_lower_string()[:8]}",
            "name": "在用门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "在用部门",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201

    response = client.delete(
        f"/api/v1/stores/{store_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "STORE_IN_USE"


def test_delete_store_soft_disables_when_only_historical_refs(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-HIS-{random_lower_string()[:8]}",
            "name": "历史门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "历史部门",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert org_response.status_code == 201
    org_id = org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "历史员工",
                "nickname": "历史",
                "mobile": f"139{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": org_id,
            "position_name": "服务员",
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]

    leave_response = client.post(
        f"/api/v1/employees/{user_id}/leave",
        headers=superuser_token_headers,
        json={"leave_reason": "测试离职"},
    )
    assert leave_response.status_code == 200

    delete_org_response = client.delete(
        f"/api/v1/org/nodes/{org_id}",
        headers=superuser_token_headers,
    )
    assert delete_org_response.status_code == 200

    response = client.delete(
        f"/api/v1/stores/{store_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    assert "门店已停用" in response.json()["message"]

    list_response = client.get("/api/v1/stores/", headers=superuser_token_headers)
    store_payload = next(
        item for item in list_response.json()["data"] if item["id"] == store_id
    )
    assert store_payload["status"] == "DISABLED"


def test_update_role(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"role_update_{random_lower_string()[:8]}",
            "name": "原角色名称",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    role_id = create_response.json()["data"]["id"]

    response = client.put(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={
            "code": f"role_updated_{random_lower_string()[:8]}",
            "name": "新角色名称",
            "status": "DISABLED",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["name"] == "新角色名称"
    assert payload["data"]["status"] == "DISABLED"
    assert payload["data"]["created_by_user_id"] is not None


def test_delete_role(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"role_delete_{random_lower_string()[:8]}",
            "name": "待删除角色",
            "status": "ACTIVE",
        },
    )
    assert create_response.status_code == 201
    role_id = create_response.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"] is None

    read_response = client.get("/api/v1/iam/roles", headers=superuser_token_headers)
    assert read_response.status_code == 200
    assert role_id not in {item["id"] for item in read_response.json()["data"]}


def test_create_org_node(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-{random_lower_string()[:8]}",
            "name": "组织门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
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

    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["name"] == "营运部"
    assert payload["data"]["prefix"] == "YY"
    assert payload["data"]["store_id"] == store_id


def test_update_org_node(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-UP-{random_lower_string()[:8]}",
            "name": "组织更新门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    create_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "原部门",
            "prefix": "BM",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert create_response.status_code == 201
    node_id = create_response.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/org/nodes/{node_id}",
        headers=superuser_token_headers,
        json={"name": "新部门", "prefix": "XD", "sort_order": 9, "is_active": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["name"] == "新部门"
    assert payload["data"]["prefix"] == "XD"
    assert payload["data"]["sort_order"] == 9
    assert payload["data"]["is_active"] is False


def test_employee_no_is_generated_from_org_prefix_chain(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-EMP-{random_lower_string()[:8]}",
            "name": "员工编号门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    parent_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
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
    parent_id = parent_response.json()["data"]["id"]

    child_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": parent_id,
            "name": "前厅组",
            "prefix": "QT",
            "node_type": "TEAM",
            "sort_order": 1,
            "is_active": True,
        },
    )
    child_id = child_response.json()["data"]["id"]

    first_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "编号员工一",
                "nickname": "编号一",
                "mobile": f"134{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": child_id,
            "position_name": "服务员",
        },
    )
    assert first_response.status_code == 201
    assert first_response.json()["data"]["profile"]["employee_no"] == "YYQT0001"

    second_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "编号员工二",
                "nickname": "编号二",
                "mobile": f"133{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": child_id,
            "position_name": "服务员",
        },
    )
    assert second_response.status_code == 201
    assert second_response.json()["data"]["profile"]["employee_no"] == "YYQT0002"


def test_delete_org_node_success_when_unreferenced(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-DEL-{random_lower_string()[:8]}",
            "name": "组织删除门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]
    create_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "可删部门",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    node_id = create_response.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/org/nodes/{node_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    assert response.json()["code"] == "SUCCESS"

    list_response = client.get(
        f"/api/v1/org/nodes?store_id={store_id}",
        headers=superuser_token_headers,
    )
    assert node_id not in {item["id"] for item in list_response.json()["data"]}


def test_delete_org_node_returns_conflict_when_in_use(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-INUSE-{random_lower_string()[:8]}",
            "name": "组织在用门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]
    org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "在用组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    org_id = org_response.json()["data"]["id"]
    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "在职员工",
                "nickname": "在职",
                "mobile": f"136{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": org_id,
            "position_name": "服务员",
        },
    )
    assert onboard_response.status_code == 201

    response = client.delete(
        f"/api/v1/org/nodes/{org_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORG_NODE_IN_USE"


def test_delete_org_node_soft_disables_when_only_historical_refs(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-HIS-{random_lower_string()[:8]}",
            "name": "组织历史门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]
    org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "历史组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    org_id = org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "历史组织员工",
                "nickname": "历史组织",
                "mobile": f"135{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": org_id,
            "position_name": "服务员",
        },
    )
    user_id = onboard_response.json()["data"]["user"]["id"]
    leave_response = client.post(
        f"/api/v1/employees/{user_id}/leave",
        headers=superuser_token_headers,
        json={"leave_reason": "测试离职"},
    )
    assert leave_response.status_code == 200

    response = client.delete(
        f"/api/v1/org/nodes/{org_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    assert "组织节点已停用" in response.json()["message"]

    list_response = client.get(
        f"/api/v1/org/nodes?store_id={store_id}",
        headers=superuser_token_headers,
    )
    node_payload = next(item for item in list_response.json()["data"] if item["id"] == org_id)
    assert node_payload["is_active"] is False


def test_delete_org_node_returns_conflict_when_has_children(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-CHILD-{random_lower_string()[:8]}",
            "name": "组织子节点门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]
    parent_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "父组织",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    parent_id = parent_response.json()["data"]["id"]
    child_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": parent_id,
            "name": "子组织",
            "node_type": "TEAM",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert child_response.status_code == 201

    response = client.delete(
        f"/api/v1/org/nodes/{parent_id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ORG_NODE_IN_USE"


def test_assign_user_role(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"role_{random_lower_string()[:8]}",
            "name": "测试角色",
            "status": "ACTIVE",
        },
    )
    role_id = role_response.json()["data"]["id"]

    user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": random_lower_string(),
            "email": random_email(),
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "测试用户",
            "nickname": "测试",
            "mobile": "13800000001",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    user_id = user_response.json()["data"]["id"]

    response = client.put(
        f"/api/v1/iam/users/{user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [role_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"][0]["id"] == role_id


def test_non_superuser_only_reads_own_permissions(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"perm_read_{random_lower_string()[:8]}",
            "name": "权限查看角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["data"]["id"]

    permissions_response = client.get(
        "/api/v1/iam/permissions",
        headers=superuser_token_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }

    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["iam.permission.read"],
                permission_ids_by_code["org.store.read"],
            ]
        },
    )
    assert assign_permission_response.status_code == 200

    username = random_lower_string()
    password = "password1234"
    user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": random_email(),
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "权限查看用户",
            "nickname": "权限查看",
            "mobile": "13800000011",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["data"]["id"]

    assign_role_response = client.put(
        f"/api/v1/iam/users/{user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": username, "password": password},
    )
    assert login_response.status_code == 200
    user_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    filtered_permissions_response = client.get(
        "/api/v1/iam/permissions",
        headers=user_headers,
    )
    assert filtered_permissions_response.status_code == 200
    assert {item["code"] for item in filtered_permissions_response.json()["data"]} == {
        "iam.permission.read",
        "org.store.read",
    }


def test_non_superuser_only_reads_visible_roles(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    regional_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"regional_visible_{random_lower_string()[:8]}",
            "name": "区域经理角色",
            "status": "ACTIVE",
        },
    )
    store_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"store_visible_{random_lower_string()[:8]}",
            "name": "店长角色",
            "status": "ACTIVE",
        },
    )
    staff_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"staff_visible_{random_lower_string()[:8]}",
            "name": "门店员工角色",
            "status": "ACTIVE",
        },
    )
    regional_role_id = regional_role_response.json()["data"]["id"]
    store_role_id = store_role_response.json()["data"]["id"]
    staff_role_id = staff_role_response.json()["data"]["id"]

    permissions_response = client.get(
        "/api/v1/iam/permissions",
        headers=superuser_token_headers,
    )
    permission_ids_by_code = {
        item["code"]: item["id"] for item in permissions_response.json()["data"]
    }
    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{store_role_id}",
        headers=superuser_token_headers,
        json={"permission_ids": [permission_ids_by_code["iam.role.read"]]},
    )
    assert assign_permission_response.status_code == 200

    grant_response = client.put(
        f"/api/v1/iam/roles/{store_role_id}",
        headers=superuser_token_headers,
        json={"grantable_role_ids": [staff_role_id]},
    )
    assert grant_response.status_code == 200

    manager_username = random_lower_string()
    manager_password = "password1234"
    manager_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": manager_username,
            "email": random_email(),
            "password": manager_password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "门店经理",
            "nickname": "经理",
            "mobile": "13800000221",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    manager_user_id = manager_response.json()["data"]["id"]
    assign_role_response = client.put(
        f"/api/v1/iam/users/{manager_user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [store_role_id]},
    )
    assert assign_role_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": manager_username, "password": manager_password},
    )
    assert login_response.status_code == 200
    manager_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    roles_response = client.get("/api/v1/iam/roles", headers=manager_headers)
    assert roles_response.status_code == 200
    store_role_payload = next(
        item for item in roles_response.json()["data"] if item["id"] == store_role_id
    )
    assert "permission_ids" in store_role_payload
    assert "permissions" in store_role_payload
    assert {item["code"] for item in store_role_payload["permissions"]} == {
        "iam.role.read"
    }
    assert set(store_role_payload["grantable_role_ids"]) == {
        store_role_id,
        staff_role_id,
    }
    assert {item["id"] for item in store_role_payload["grantable_roles"]} == {
        store_role_id,
        staff_role_id,
    }
    role_ids = {item["id"] for item in roles_response.json()["data"]}
    assert store_role_id in role_ids
    assert staff_role_id in role_ids
    assert regional_role_id not in role_ids


def test_creator_only_sees_new_role_by_default(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    creator_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"creator_role_{random_lower_string()[:8]}",
            "name": "可创建角色",
            "status": "ACTIVE",
        },
    )
    creator_role_id = creator_role_response.json()["data"]["id"]

    creator_permission_response = client.get(
        "/api/v1/iam/permissions",
        headers=superuser_token_headers,
    )
    permission_ids_by_code = {
        item["code"]: item["id"] for item in creator_permission_response.json()["data"]
    }
    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{creator_role_id}",
        headers=superuser_token_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["iam.role.read"],
                permission_ids_by_code["iam.role.create"],
            ]
        },
    )
    assert assign_permission_response.status_code == 200

    creator_username = random_lower_string()
    creator_password = "password1234"
    creator_user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": creator_username,
            "email": random_email(),
            "password": creator_password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "角色创建者",
            "nickname": "创建者",
            "mobile": "13800000222",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    creator_user_id = creator_user_response.json()["data"]["id"]
    client.put(
        f"/api/v1/iam/users/{creator_user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [creator_role_id]},
    )

    other_username = random_lower_string()
    other_password = "password1234"
    other_user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": other_username,
            "email": random_email(),
            "password": other_password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "另一个创建者",
            "nickname": "另一个",
            "mobile": "13800000223",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    other_user_id = other_user_response.json()["data"]["id"]
    client.put(
        f"/api/v1/iam/users/{other_user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [creator_role_id]},
    )

    creator_login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": creator_username, "password": creator_password},
    )
    creator_headers = {
        "Authorization": f"Bearer {creator_login_response.json()['data']['access_token']}"
    }
    other_login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": other_username, "password": other_password},
    )
    other_headers = {
        "Authorization": f"Bearer {other_login_response.json()['data']['access_token']}"
    }

    created_role_response = client.post(
        "/api/v1/iam/roles",
        headers=creator_headers,
        json={
            "code": f"created_by_manager_{random_lower_string()[:8]}",
            "name": "店长自建角色",
            "status": "ACTIVE",
        },
    )
    assert created_role_response.status_code == 201
    created_role_id = created_role_response.json()["data"]["id"]

    creator_roles_response = client.get("/api/v1/iam/roles", headers=creator_headers)
    assert creator_roles_response.status_code == 200
    assert created_role_id in {item["id"] for item in creator_roles_response.json()["data"]}

    other_roles_response = client.get("/api/v1/iam/roles", headers=other_headers)
    assert other_roles_response.status_code == 200
    assert created_role_id not in {item["id"] for item in other_roles_response.json()["data"]}


def test_non_superuser_cannot_assign_ungranted_role(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    regional_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"regional_assign_{random_lower_string()[:8]}",
            "name": "区域经理角色",
            "status": "ACTIVE",
        },
    )
    store_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"store_assign_{random_lower_string()[:8]}",
            "name": "店长角色",
            "status": "ACTIVE",
        },
    )
    staff_role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"staff_assign_{random_lower_string()[:8]}",
            "name": "门店员工角色",
            "status": "ACTIVE",
        },
    )
    regional_role_id = regional_role_response.json()["data"]["id"]
    store_role_id = store_role_response.json()["data"]["id"]
    staff_role_id = staff_role_response.json()["data"]["id"]

    permissions_response = client.get("/api/v1/iam/permissions", headers=superuser_token_headers)
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions_response.json()["data"]}
    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{store_role_id}",
        headers=superuser_token_headers,
        json={
            "permission_ids": [
                permission_ids_by_code["iam.role.read"],
                permission_ids_by_code["iam.user.assign_role"],
            ]
        },
    )
    assert assign_permission_response.status_code == 200

    grant_response = client.put(
        f"/api/v1/iam/roles/{store_role_id}",
        headers=superuser_token_headers,
        json={"grantable_role_ids": [staff_role_id]},
    )
    assert grant_response.status_code == 200

    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ROLE-SCOPE-{random_lower_string()[:8]}",
            "name": "角色边界门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "角色边界组织",
            "prefix": "JS",
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
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": manager_username,
            "email": random_email(),
            "password": manager_password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "店长用户",
            "nickname": "店长",
            "mobile": "13800000224",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    manager_user_id = manager_response.json()["data"]["id"]
    client.put(
        f"/api/v1/iam/users/{manager_user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [store_role_id]},
    )
    manager_binding_response = client.post(
        "/api/v1/org/bindings",
        headers=superuser_token_headers,
        json={
            "user_id": manager_user_id,
            "org_node_id": org_id,
            "is_primary": True,
            "position_name": "店长",
        },
    )
    assert manager_binding_response.status_code == 201
    manager_scope_response = client.put(
        f"/api/v1/iam/users/{manager_user_id}/data-scopes",
        headers=superuser_token_headers,
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
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": random_lower_string(),
            "email": random_email(),
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "普通员工",
            "nickname": "员工",
            "mobile": "13800000225",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    employee_user_id = employee_response.json()["data"]["id"]
    employee_binding_response = client.post(
        "/api/v1/org/bindings",
        headers=superuser_token_headers,
        json={
            "user_id": employee_user_id,
            "org_node_id": org_id,
            "is_primary": True,
            "position_name": "员工",
        },
    )
    assert employee_binding_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": manager_username, "password": manager_password},
    )
    manager_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    denied_response = client.put(
        f"/api/v1/iam/users/{employee_user_id}/roles",
        headers=manager_headers,
        json={"role_ids": [regional_role_id]},
    )
    assert denied_response.status_code == 403
    assert denied_response.json()["code"] == "AUTH_GRANT_DENIED"

    success_response = client.put(
        f"/api/v1/iam/users/{employee_user_id}/roles",
        headers=manager_headers,
        json={"role_ids": [staff_role_id]},
    )
    assert success_response.status_code == 200
    assert success_response.json()["data"][0]["id"] == staff_role_id


def test_assign_user_data_scope(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"SCOPE-{random_lower_string()[:8]}",
            "name": "范围门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": random_lower_string(),
            "email": random_email(),
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "范围用户",
            "nickname": "范围",
            "mobile": "13800000002",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    user_id = user_response.json()["data"]["id"]

    response = client.put(
        f"/api/v1/iam/users/{user_id}/data-scopes",
        headers=superuser_token_headers,
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

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"][0]["scope_type"] == "STORE"
    assert payload["data"][0]["store_id"] == store_id


def test_assign_roles_and_scopes_for_secondary_store_employee_in_current_store_context(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    primary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"IAM-CTX-A-{random_lower_string()[:8]}",
            "name": "主门店",
            "status": "ACTIVE",
        },
    )
    primary_store_id = primary_store_response.json()["data"]["id"]

    secondary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"IAM-CTX-B-{random_lower_string()[:8]}",
            "name": "次门店",
            "status": "ACTIVE",
        },
    )
    secondary_store_id = secondary_store_response.json()["data"]["id"]

    primary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": primary_store_id,
            "parent_id": None,
            "name": "主门店营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    primary_org_id = primary_org_response.json()["data"]["id"]

    secondary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": secondary_store_id,
            "parent_id": None,
            "name": "次门店前厅组",
            "prefix": "QT",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    secondary_org_id = secondary_org_response.json()["data"]["id"]

    role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"secondary_store_role_{random_lower_string()[:8]}",
            "name": "次门店角色",
            "status": "ACTIVE",
        },
    )
    role_id = role_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "多门店授权员工",
                "nickname": "多门店授权",
                "mobile": f"136{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": primary_org_id,
            "position_name": "主门店店长",
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]

    create_binding_response = client.post(
        "/api/v1/org/bindings",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={
            "user_id": user_id,
            "org_node_id": secondary_org_id,
            "position_name": "次门店巡店",
            "is_primary": False,
        },
    )
    assert create_binding_response.status_code == 201

    assign_role_response = client.put(
        f"/api/v1/iam/users/{user_id}/roles",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200
    assert assign_role_response.json()["data"][0]["id"] == role_id

    assign_scope_response = client.put(
        f"/api/v1/iam/users/{user_id}/data-scopes",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={
            "scopes": [
                {
                    "scope_type": "STORE",
                    "store_id": secondary_store_id,
                    "org_node_id": None,
                }
            ]
        },
    )
    assert assign_scope_response.status_code == 200
    assert assign_scope_response.json()["data"][0]["store_id"] == secondary_store_id


def test_read_user_authorization_summary(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"summary_role_{random_lower_string()[:8]}",
            "name": "授权摘要角色",
            "status": "ACTIVE",
        },
    )
    role_id = role_response.json()["data"]["id"]

    permissions_response = client.get(
        "/api/v1/iam/permissions",
        headers=superuser_token_headers,
    )
    permission_ids = [
        item["id"]
        for item in permissions_response.json()["data"]
        if item["code"] in {"org.store.read", "org.node.read"}
    ]

    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={"permission_ids": permission_ids},
    )
    assert assign_permission_response.status_code == 200

    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"AUTH-{random_lower_string()[:8]}",
            "name": "授权摘要门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": random_lower_string(),
            "email": random_email(),
            "password": "password1234",
            "is_active": True,
            "is_superuser": False,
            "full_name": "摘要用户",
            "nickname": "摘要",
            "mobile": "13800000003",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    user_id = user_response.json()["data"]["id"]

    assign_role_response = client.put(
        f"/api/v1/iam/users/{user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200

    assign_scope_response = client.put(
        f"/api/v1/iam/users/{user_id}/data-scopes",
        headers=superuser_token_headers,
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

    summary_response = client.get(
        f"/api/v1/iam/users/{user_id}/authorization-summary",
        headers=superuser_token_headers,
    )
    assert summary_response.status_code == 200
    payload = summary_response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["id"] == user_id
    assert {item["code"] for item in payload["data"]["roles"]} == {
        role_response.json()["data"]["code"]
    }
    assert {item["code"] for item in payload["data"]["permissions"]} == {
        "org.store.read",
        "org.node.read",
    }
    assert payload["data"]["data_scopes"][0]["store_id"] == store_id


def test_unbind_role_permissions_takes_effect_immediately(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    role_response = client.post(
        "/api/v1/iam/roles",
        headers=superuser_token_headers,
        json={
            "code": f"unbind_role_{random_lower_string()[:8]}",
            "name": "权限解绑角色",
            "status": "ACTIVE",
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["data"]["id"]

    permissions_response = client.get(
        "/api/v1/iam/permissions",
        headers=superuser_token_headers,
    )
    assert permissions_response.status_code == 200
    permission_ids = [
        item["id"]
        for item in permissions_response.json()["data"]
        if item["code"] == "org.store.read"
    ]
    assert len(permission_ids) == 1

    assign_permission_response = client.put(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={"permission_ids": permission_ids},
    )
    assert assign_permission_response.status_code == 200

    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"UNBIND-{random_lower_string()[:8]}",
            "name": "解绑权限门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    username = random_lower_string()
    password = "password1234"
    user_response = client.post(
        "/api/v1/users/",
        headers=superuser_token_headers,
        json={
            "username": username,
            "email": random_email(),
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "full_name": "解绑权限用户",
            "nickname": "解绑权限",
            "mobile": "13800000004",
            "status": "ACTIVE",
            "primary_store_id": None,
            "primary_department_id": None,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["data"]["id"]

    assign_role_response = client.put(
        f"/api/v1/iam/users/{user_id}/roles",
        headers=superuser_token_headers,
        json={"role_ids": [role_id]},
    )
    assert assign_role_response.status_code == 200

    assign_scope_response = client.put(
        f"/api/v1/iam/users/{user_id}/data-scopes",
        headers=superuser_token_headers,
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

    login_response = client.post(
        "/api/v1/auth/backend/password-login",
        json={"account": username, "password": password},
    )
    assert login_response.status_code == 200
    user_headers = {
        "Authorization": f"Bearer {login_response.json()['data']['access_token']}"
    }

    before_response = client.get("/api/v1/stores/", headers=user_headers)
    assert before_response.status_code == 200
    assert before_response.json()["data"][0]["id"] == store_id

    unbind_response = client.put(
        f"/api/v1/iam/roles/{role_id}",
        headers=superuser_token_headers,
        json={"permission_ids": []},
    )
    assert unbind_response.status_code == 200
    assert unbind_response.json()["data"]["permission_ids"] == []

    after_response = client.get("/api/v1/stores/", headers=user_headers)
    assert after_response.status_code == 403
    assert after_response.json()["code"] == "AUTH_PERMISSION_DENIED"


def test_read_org_node_members_returns_flat_members_with_org_fields(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"STORE-MEM-{random_lower_string()[:8]}",
            "name": "组织成员门店",
            "status": "ACTIVE",
        },
    )
    assert store_response.status_code == 201
    store_id = store_response.json()["data"]["id"]

    parent_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": None,
            "name": "营运中心",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert parent_org_response.status_code == 201
    parent_org_id = parent_org_response.json()["data"]["id"]

    child_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "parent_id": parent_org_id,
            "name": "前厅组",
            "prefix": "QT",
            "node_type": "TEAM",
            "sort_order": 1,
            "is_active": True,
        },
    )
    assert child_org_response.status_code == 201
    child_org_id = child_org_response.json()["data"]["id"]

    parent_employee_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "父组织员工",
                "nickname": "父组织",
                "mobile": f"138{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": parent_org_id,
            "position_name": "主管",
        },
    )
    assert parent_employee_response.status_code == 201
    parent_user_id = parent_employee_response.json()["data"]["user"]["id"]

    child_employee_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "子组织员工",
                "nickname": "子组织",
                "mobile": f"139{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "employee_no": f"EMP-{random_lower_string()[:6]}",
            "primary_org_node_id": child_org_id,
            "position_name": "服务员",
        },
    )
    assert child_employee_response.status_code == 201
    child_user_id = child_employee_response.json()["data"]["user"]["id"]

    members_response = client.get(
        f"/api/v1/org/nodes/{parent_org_id}/members",
        headers=superuser_token_headers,
    )

    assert members_response.status_code == 200
    payload = members_response.json()
    assert payload["code"] == "SUCCESS"
    assert set(payload["data"].keys()) == {"org_nodes", "members"}
    org_nodes = payload["data"]["org_nodes"]
    members = payload["data"]["members"]
    assert isinstance(org_nodes, list)
    assert isinstance(members, list)
    assert {item["user"]["id"] for item in members} == {parent_user_id, child_user_id}
    assert {item["id"] for item in org_nodes} == {parent_org_id, child_org_id}
    child_node = next(item for item in org_nodes if item["id"] == child_org_id)
    assert child_node["parent_id"] == parent_org_id

    parent_member = next(item for item in members if item["user"]["id"] == parent_user_id)
    child_member = next(item for item in members if item["user"]["id"] == child_user_id)

    assert parent_member["store_id"] == store_id
    assert parent_member["store_name"] == "组织成员门店"
    assert parent_member["org_node_id"] == parent_org_id
    assert parent_member["org_node_name"] == "营运中心"
    assert parent_member["position_name"] == "主管"

    assert child_member["store_id"] == store_id
    assert child_member["store_name"] == "组织成员门店"
    assert child_member["org_node_id"] == child_org_id
    assert child_member["org_node_name"] == "前厅组"
    assert child_member["position_name"] == "服务员"


def test_update_user_org_binding_changes_org_within_same_store(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-MOVE-{random_lower_string()[:8]}",
            "name": "组织调整门店",
            "status": "ACTIVE",
        },
    )
    store_id = store_response.json()["data"]["id"]

    source_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
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
    source_org_id = source_org_response.json()["data"]["id"]

    target_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
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
    target_org_id = target_org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "组织调整员工",
                "nickname": "组织调整",
                "mobile": f"132{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": source_org_id,
            "position_name": "服务员",
        },
    )
    assert onboard_response.status_code == 201
    payload = onboard_response.json()["data"]
    binding_id = payload["primary_binding"]["id"]
    user_id = payload["user"]["id"]
    employee_no = payload["profile"]["employee_no"]

    update_response = client.patch(
        f"/api/v1/org/bindings/{binding_id}",
        headers=superuser_token_headers,
        json={"org_node_id": target_org_id, "position_name": "值班经理"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["org_node_id"] == target_org_id
    assert update_response.json()["data"]["position_name"] == "值班经理"

    records_response = client.get(
        f"/api/v1/employees/{user_id}/employment-records",
        headers=superuser_token_headers,
    )
    assert records_response.status_code == 200
    assert records_response.json()["data"][0]["employee_no"] == employee_no
    assert records_response.json()["data"][0]["org_node_id"] == target_org_id
    assert records_response.json()["data"][0]["position_name"] == "值班经理"


def test_update_user_org_binding_rejects_cross_store_change(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_a_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-MOVE-A-{random_lower_string()[:8]}",
            "name": "组织调整一号店",
            "status": "ACTIVE",
        },
    )
    store_a_id = store_a_response.json()["data"]["id"]
    store_b_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-MOVE-B-{random_lower_string()[:8]}",
            "name": "组织调整二号店",
            "status": "ACTIVE",
        },
    )
    store_b_id = store_b_response.json()["data"]["id"]

    source_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_a_id,
            "parent_id": None,
            "name": "一号店营运部",
            "prefix": "YA",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    source_org_id = source_org_response.json()["data"]["id"]
    target_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": store_b_id,
            "parent_id": None,
            "name": "二号店前厅部",
            "prefix": "QB",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    target_org_id = target_org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "跨店组织调整员工",
                "nickname": "跨店调整",
                "mobile": f"131{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": source_org_id,
            "position_name": "服务员",
        },
    )
    binding_id = onboard_response.json()["data"]["primary_binding"]["id"]

    update_response = client.patch(
        f"/api/v1/org/bindings/{binding_id}",
        headers=superuser_token_headers,
        json={"org_node_id": target_org_id},
    )
    assert update_response.status_code == 400
    assert update_response.json()["code"] == "ORG_BINDING_STORE_MISMATCH"


def test_update_secondary_store_binding_in_current_store_context(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    primary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-CTX-A-{random_lower_string()[:8]}",
            "name": "主门店",
            "status": "ACTIVE",
        },
    )
    primary_store_id = primary_store_response.json()["data"]["id"]

    secondary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"ORG-CTX-B-{random_lower_string()[:8]}",
            "name": "次门店",
            "status": "ACTIVE",
        },
    )
    secondary_store_id = secondary_store_response.json()["data"]["id"]

    primary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": primary_store_id,
            "parent_id": None,
            "name": "主门店营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    primary_org_id = primary_org_response.json()["data"]["id"]

    secondary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": secondary_store_id,
            "parent_id": None,
            "name": "次门店巡店组",
            "prefix": "XD",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    secondary_org_id = secondary_org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "多门店员工",
                "nickname": "多门店",
                "mobile": f"130{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": primary_org_id,
            "position_name": "主门店店长",
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]

    create_binding_response = client.post(
        "/api/v1/org/bindings",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={
            "user_id": user_id,
            "org_node_id": secondary_org_id,
            "position_name": "区域巡店",
            "is_primary": False,
        },
    )
    assert create_binding_response.status_code == 201
    binding_id = create_binding_response.json()["data"]["id"]

    update_response = client.patch(
        f"/api/v1/org/bindings/{binding_id}",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={"position_name": "测试111"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["code"] == "SUCCESS"
    assert update_response.json()["data"]["org_node_id"] == secondary_org_id
    assert update_response.json()["data"]["position_name"] == "测试111"


def test_read_authorization_summary_for_secondary_store_employee_in_current_store_context(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    primary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"SUM-CTX-A-{random_lower_string()[:8]}",
            "name": "主门店",
            "status": "ACTIVE",
        },
    )
    primary_store_id = primary_store_response.json()["data"]["id"]

    secondary_store_response = client.post(
        "/api/v1/stores/",
        headers=superuser_token_headers,
        json={
            "code": f"SUM-CTX-B-{random_lower_string()[:8]}",
            "name": "次门店",
            "status": "ACTIVE",
        },
    )
    secondary_store_id = secondary_store_response.json()["data"]["id"]

    primary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": primary_store_id,
            "parent_id": None,
            "name": "主门店营运部",
            "prefix": "YY",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    primary_org_id = primary_org_response.json()["data"]["id"]

    secondary_org_response = client.post(
        "/api/v1/org/nodes",
        headers=superuser_token_headers,
        json={
            "store_id": secondary_store_id,
            "parent_id": None,
            "name": "次门店前厅组",
            "prefix": "QT",
            "node_type": "DEPARTMENT",
            "sort_order": 1,
            "is_active": True,
        },
    )
    secondary_org_id = secondary_org_response.json()["data"]["id"]

    onboard_response = client.post(
        "/api/v1/employees/onboard",
        headers=superuser_token_headers,
        json={
            "user": {
                "username": random_lower_string(),
                "email": None,
                "password": "password1234",
                "full_name": "授权摘要多门店员工",
                "nickname": "授权摘要",
                "mobile": f"135{abs(hash(random_lower_string())) % 10**8:08d}",
            },
            "primary_org_node_id": primary_org_id,
            "position_name": "主门店店长",
        },
    )
    assert onboard_response.status_code == 201
    user_id = onboard_response.json()["data"]["user"]["id"]

    create_binding_response = client.post(
        "/api/v1/org/bindings",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
        json={
            "user_id": user_id,
            "org_node_id": secondary_org_id,
            "position_name": "次门店巡店",
            "is_primary": False,
        },
    )
    assert create_binding_response.status_code == 201

    summary_response = client.get(
        f"/api/v1/iam/users/{user_id}/authorization-summary",
        headers={
            **superuser_token_headers,
            "X-Current-Store-Id": secondary_store_id,
        },
    )
    assert summary_response.status_code == 200
    assert summary_response.json()["code"] == "SUCCESS"
    assert summary_response.json()["data"]["id"] == user_id
