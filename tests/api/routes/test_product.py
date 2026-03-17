"""商品中心 API 测试"""

from fastapi.testclient import TestClient

from tests.utils.utils import random_lower_string


def _random_code(prefix: str = "CAT") -> str:
    return f"{prefix}-{random_lower_string()[:8].upper()}"


def _create_category(client: TestClient, headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/product-categories/",
        headers=headers,
        json={
            "code": _random_code("CAT"),
            "name": f"分类-{random_lower_string()[:6]}",
            "level": 1,
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_product(client: TestClient, headers: dict[str, str]) -> str:
    category_id = _create_category(client, headers)
    resp = client.post(
        "/api/v1/products/",
        headers=headers,
        json={
            "code": _random_code("PRD"),
            "name": f"商品-{random_lower_string()[:6]}",
            "category_id": category_id,
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_store(client: TestClient, headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/stores/",
        headers=headers,
        json={
            "code": f"ST-{random_lower_string()[:8].upper()}",
            "name": "测试门店",
            "status": "ACTIVE",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_attribute(
    client: TestClient, headers: dict[str, str], name: str, code_prefix: str
) -> str:
    resp = client.post(
        "/api/v1/product-attributes/",
        headers=headers,
        json={
            "code": _random_code(code_prefix),
            "name": name,
            "display_type": "SELECT",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_attribute_value(
    client: TestClient,
    headers: dict[str, str],
    attribute_id: str,
    name: str,
    code_prefix: str,
) -> str:
    resp = client.post(
        f"/api/v1/product-attributes/{attribute_id}/values",
        headers=headers,
        json={"attribute_id": attribute_id, "code": _random_code(code_prefix), "name": name},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _bind_attribute(
    client: TestClient, headers: dict[str, str], product_id: str, attribute_id: str
) -> str:
    resp = client.post(
        f"/api/v1/products/{product_id}/attributes",
        headers=headers,
        json={"product_id": product_id, "attribute_id": attribute_id, "is_required": True},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _bind_attribute_value(
    client: TestClient,
    headers: dict[str, str],
    product_id: str,
    assignment_id: str,
    attribute_value_id: str,
) -> str:
    resp = client.post(
        f"/api/v1/products/{product_id}/attributes/{assignment_id}/values",
        headers=headers,
        json={
            "assignment_id": assignment_id,
            "attribute_value_id": attribute_value_id,
            "is_default": False,
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_create_product_attribute_and_value(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="杯型", code_prefix="ATTR"
    )
    response = client.get(
        f"/api/v1/product-attributes/{attribute_id}/values",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"] == []

    value_id = _create_attribute_value(
        client,
        superuser_token_headers,
        attribute_id=attribute_id,
        name="大杯",
        code_prefix="VAL",
    )
    list_resp = client.get(
        f"/api/v1/product-attributes/{attribute_id}/values",
        headers=superuser_token_headers,
    )
    assert list_resp.status_code == 200
    assert any(item["id"] == value_id for item in list_resp.json()["data"])


def test_bind_product_attributes_and_values(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="颜色", code_prefix="COL"
    )
    value_id = _create_attribute_value(
        client,
        superuser_token_headers,
        attribute_id=attribute_id,
        name="红色",
        code_prefix="RED",
    )
    assignment_id = _bind_attribute(
        client, superuser_token_headers, product_id=product_id, attribute_id=attribute_id
    )
    _bind_attribute_value(
        client,
        superuser_token_headers,
        product_id=product_id,
        assignment_id=assignment_id,
        attribute_value_id=value_id,
    )

    response = client.get(
        f"/api/v1/products/{product_id}/attributes",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["attribute"]["id"] == attribute_id
    assert response.json()["data"][0]["values"][0]["attribute_value"]["id"] == value_id


def test_generate_product_skus_from_single_attribute(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="杯型", code_prefix="CUP"
    )
    large_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "大杯", "LAR"
    )
    small_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "小杯", "SML"
    )
    assignment_id = _bind_attribute(
        client, superuser_token_headers, product_id, attribute_id
    )
    _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, large_id
    )
    _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, small_id
    )

    response = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert len(payload["created"]) == 2
    assert payload["created"][0]["code"].endswith("-01")
    assert payload["created"][0]["is_default"] is True


def test_generate_product_skus_from_two_attributes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    cup_id = _create_attribute(client, superuser_token_headers, "杯型", "CUP")
    color_id = _create_attribute(client, superuser_token_headers, "颜色", "COL")
    large_id = _create_attribute_value(
        client, superuser_token_headers, cup_id, "大杯", "LAR"
    )
    small_id = _create_attribute_value(
        client, superuser_token_headers, cup_id, "小杯", "SML"
    )
    red_id = _create_attribute_value(
        client, superuser_token_headers, color_id, "红色", "RED"
    )
    black_id = _create_attribute_value(
        client, superuser_token_headers, color_id, "黑色", "BLK"
    )

    cup_assignment = _bind_attribute(
        client, superuser_token_headers, product_id, cup_id
    )
    color_assignment = _bind_attribute(
        client, superuser_token_headers, product_id, color_id
    )
    for value_id in (large_id, small_id):
        _bind_attribute_value(
            client, superuser_token_headers, product_id, cup_assignment, value_id
        )
    for value_id in (red_id, black_id):
        _bind_attribute_value(
            client, superuser_token_headers, product_id, color_assignment, value_id
        )

    response = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["created"]) == 4

    list_resp = client.get(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 4
    assert len(list_resp.json()["data"][0]["attribute_values"]) == 2


def test_regenerate_product_skus_add_new_value(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="容量", code_prefix="VOL"
    )
    small_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "330ml", "V33"
    )
    assignment_id = _bind_attribute(
        client, superuser_token_headers, product_id, attribute_id
    )
    _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, small_id
    )
    first_resp = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert first_resp.status_code == 200
    first_sku_id = first_resp.json()["data"]["created"][0]["id"]

    large_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "500ml", "V50"
    )
    _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, large_id
    )

    second_resp = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert second_resp.status_code == 200
    assert len(second_resp.json()["data"]["created"]) == 1
    assert any(item["id"] == first_sku_id for item in second_resp.json()["data"]["retained"])


def test_regenerate_product_skus_deactivate_removed_combination(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="杯型", code_prefix="CUP"
    )
    large_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "大杯", "LAR"
    )
    small_id = _create_attribute_value(
        client, superuser_token_headers, attribute_id, "小杯", "SML"
    )
    assignment_id = _bind_attribute(
        client, superuser_token_headers, product_id, attribute_id
    )
    large_binding_id = _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, large_id
    )
    _bind_attribute_value(
        client, superuser_token_headers, product_id, assignment_id, small_id
    )
    first_resp = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert first_resp.status_code == 200
    created_count = len(first_resp.json()["data"]["created"])
    assert created_count == 2

    delete_resp = client.delete(
        f"/api/v1/products/{product_id}/attributes/{assignment_id}/values/{large_binding_id}",
        headers=superuser_token_headers,
    )
    assert delete_resp.status_code == 200

    second_resp = client.post(
        f"/api/v1/products/{product_id}/skus/generate",
        headers=superuser_token_headers,
    )
    assert second_resp.status_code == 200
    assert len(second_resp.json()["data"]["deactivated"]) == 1


def test_manual_sku_create_is_blocked_after_attribute_binding(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="颜色", code_prefix="COL"
    )
    _bind_attribute(client, superuser_token_headers, product_id, attribute_id)

    response = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "name": "手工SKU"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_SKU_MANAGED_BY_ATTRIBUTES"


def test_manual_single_sku_create_still_works_without_attributes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    response = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "name": "标准版"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["code"].endswith("-01")


def test_update_sku_code_is_forbidden(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "name": "标准版"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/skus/{sku_id}",
        headers=superuser_token_headers,
        json={"code": _random_code("SKU")},
    )
    assert response.status_code == 422


def test_store_product_sku_and_inventory_mapping_still_work(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "name": "标准版"},
    )
    sku_id = sku_resp.json()["data"]["id"]
    store_id = _create_store(client, superuser_token_headers)

    store_product_resp = client.post(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id},
    )
    assert store_product_resp.status_code == 201

    store_sku_resp = client.post(
        f"/api/v1/stores/{store_id}/skus",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "product_id": product_id,
            "sku_id": sku_id,
            "sale_price": "38.00",
        },
    )
    assert store_sku_resp.status_code == 201

    mapping_resp = client.post(
        f"/api/v1/skus/{sku_id}/inventory-mappings",
        headers=superuser_token_headers,
        json={
            "sku_id": sku_id,
            "deduct_quantity": "1.00",
            "deduct_unit": "瓶",
        },
    )
    assert mapping_resp.status_code == 201


def test_attribute_assignment_duplicate_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    attribute_id = _create_attribute(
        client, superuser_token_headers, name="口味", code_prefix="FLV"
    )
    _bind_attribute(client, superuser_token_headers, product_id, attribute_id)
    response = client.post(
        f"/api/v1/products/{product_id}/attributes",
        headers=superuser_token_headers,
        json={"product_id": product_id, "attribute_id": attribute_id},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_ATTRIBUTE_ALREADY_ASSIGNED"
