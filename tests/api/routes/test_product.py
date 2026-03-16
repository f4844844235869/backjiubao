"""商品中心 API 测试"""

import uuid

from fastapi.testclient import TestClient

from tests.utils.utils import random_lower_string


def _random_code(prefix: str = "CAT") -> str:
    return f"{prefix}-{random_lower_string()[:8].upper()}"


# ---------------------------------------------------------------------------
# ProductCategory
# ---------------------------------------------------------------------------


def test_create_product_category(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={
            "code": _random_code("CAT"),
            "name": f"一级分类-{random_lower_string()[:6]}",
            "level": 1,
            "sort_order": 0,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["level"] == 1
    assert payload["data"]["is_active"] is True


def test_create_product_category_code_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    code = _random_code("CDUP")
    client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": code, "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    response = client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": code, "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_CATEGORY_CODE_EXISTS"


def test_update_product_category(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_resp = client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": _random_code("UPD"), "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    assert create_resp.status_code == 201
    category_id = create_resp.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/product-categories/{category_id}",
        headers=superuser_token_headers,
        json={"sort_order": 5},
    )
    assert response.status_code == 200
    assert response.json()["data"]["sort_order"] == 5


def test_disable_product_category(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_resp = client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": _random_code("DIS"), "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    assert create_resp.status_code == 201
    category_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/product-categories/{category_id}/disable",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False


def test_delete_product_category(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    create_resp = client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": _random_code("DEL"), "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    assert create_resp.status_code == 201
    category_id = create_resp.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/product-categories/{category_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == "SUCCESS"


def test_delete_category_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"/api/v1/product-categories/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_CATEGORY_NOT_FOUND"


def test_list_product_categories(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    client.post(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
        json={"code": _random_code("LST"), "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    response = client.get(
        "/api/v1/product-categories/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


def _create_category(client: TestClient, headers: dict[str, str]) -> str:
    """Helper: create a category and return its ID."""
    resp = client.post(
        "/api/v1/product-categories/",
        headers=headers,
        json={"code": _random_code("PC"), "name": f"分类-{random_lower_string()[:6]}", "level": 1},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_create_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    response = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={
            "code": _random_code("PRD"),
            "name": f"商品-{random_lower_string()[:6]}",
            "category_id": cat_id,
            "product_type": "NORMAL",
            "unit": "瓶",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["unit"] == "瓶"
    assert payload["data"]["is_active"] is True
    assert payload["data"]["is_deleted"] is False


def test_create_product_code_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    code = _random_code("PDUP")
    client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": code, "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    response = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": code, "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "PRODUCT_CODE_EXISTS"


def test_get_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    create_resp = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": _random_code("GET"), "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    product_id = create_resp.json()["data"]["id"]

    response = client.get(
        f"/api/v1/products/{product_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == product_id


def test_update_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    create_resp = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": _random_code("UPP"), "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    product_id = create_resp.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/products/{product_id}",
        headers=superuser_token_headers,
        json={"is_storable": True, "is_gift_allowed": True},
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_storable"] is True
    assert response.json()["data"]["is_gift_allowed"] is True


def test_disable_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    create_resp = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": _random_code("DIP"), "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    product_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/products/{product_id}/disable",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False


def test_delete_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    cat_id = _create_category(client, superuser_token_headers)
    create_resp = client.post(
        "/api/v1/products/",
        headers=superuser_token_headers,
        json={"code": _random_code("DLP"), "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    product_id = create_resp.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/products/{product_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    # Verify it's logically deleted
    get_resp = client.get(f"/api/v1/products/{product_id}", headers=superuser_token_headers)
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# ProductSku
# ---------------------------------------------------------------------------


def _create_product(client: TestClient, headers: dict[str, str]) -> str:
    cat_id = _create_category(client, headers)
    resp = client.post(
        "/api/v1/products/",
        headers=headers,
        json={"code": _random_code("SKP"), "name": f"商品-{random_lower_string()[:6]}", "category_id": cat_id},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_create_product_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    response = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={
            "product_id": product_id,
            "code": _random_code("SKU"),
            "name": "330ml单瓶",
            "spec_text": "330ml",
            "is_default": True,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["is_default"] is True
    assert payload["data"]["product_id"] == product_id


def test_list_product_skus(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("SKU"), "name": "小瓶"},
    )
    response = client.get(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


def test_update_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("UPS"), "name": "SKU更新测试"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/skus/{sku_id}",
        headers=superuser_token_headers,
        json={"inventory_mode": "DIRECT"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["inventory_mode"] == "DIRECT"


def test_disable_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("DSK"), "name": "停用测试SKU"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/skus/{sku_id}/disable",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False


def test_delete_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("DEK"), "name": "删除测试SKU"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/skus/{sku_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# SkuInventoryMapping
# ---------------------------------------------------------------------------


def test_create_sku_inventory_mapping(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("MPS"), "name": "映射测试SKU", "inventory_mode": "DIRECT"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/skus/{sku_id}/inventory-mappings",
        headers=superuser_token_headers,
        json={
            "sku_id": sku_id,
            "deduct_quantity": "1.00",
            "deduct_unit": "瓶",
            "sort_order": 0,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["code"] == "SUCCESS"
    assert payload["data"]["sku_id"] == sku_id


def test_delete_sku_inventory_mapping(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("DMS"), "name": "映射删除测试SKU", "inventory_mode": "DIRECT"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    mapping_resp = client.post(
        f"/api/v1/skus/{sku_id}/inventory-mappings",
        headers=superuser_token_headers,
        json={"sku_id": sku_id, "deduct_quantity": "1.00", "deduct_unit": "瓶"},
    )
    mapping_id = mapping_resp.json()["data"]["id"]

    response = client.delete(
        f"/api/v1/skus/{sku_id}/inventory-mappings/{mapping_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# StoreProduct
# ---------------------------------------------------------------------------


def _create_store(client: TestClient, headers: dict[str, str]) -> str:
    resp = client.post(
        "/api/v1/stores/",
        headers=headers,
        json={"code": f"ST-{random_lower_string()[:8].upper()}", "name": "测试门店", "status": "ACTIVE"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def test_create_store_product(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_id = _create_store(client, superuser_token_headers)
    product_id = _create_product(client, superuser_token_headers)

    response = client.post(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id, "is_enabled": True, "is_visible": True, "sort_order": 1},
    )
    assert response.status_code == 201
    assert response.json()["data"]["store_id"] == store_id
    assert response.json()["data"]["product_id"] == product_id


def test_create_store_product_conflict(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_id = _create_store(client, superuser_token_headers)
    product_id = _create_product(client, superuser_token_headers)

    client.post(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id},
    )
    response = client.post(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "STORE_PRODUCT_EXISTS"


def test_list_store_products(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_id = _create_store(client, superuser_token_headers)
    product_id = _create_product(client, superuser_token_headers)

    client.post(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id},
    )
    response = client.get(
        f"/api/v1/stores/{store_id}/products",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


# ---------------------------------------------------------------------------
# StoreProductSku
# ---------------------------------------------------------------------------


def test_create_store_product_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_id = _create_store(client, superuser_token_headers)
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("SSK"), "name": "门店SKU测试"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/stores/{store_id}/skus",
        headers=superuser_token_headers,
        json={
            "store_id": store_id,
            "product_id": product_id,
            "sku_id": sku_id,
            "sale_price": "38.00",
            "is_sale_enabled": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["store_id"] == store_id
    assert response.json()["data"]["sku_id"] == sku_id


def test_update_store_product_sku(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    store_id = _create_store(client, superuser_token_headers)
    product_id = _create_product(client, superuser_token_headers)
    sku_resp = client.post(
        f"/api/v1/products/{product_id}/skus",
        headers=superuser_token_headers,
        json={"product_id": product_id, "code": _random_code("USK"), "name": "价格更新测试SKU"},
    )
    sku_id = sku_resp.json()["data"]["id"]

    sps_resp = client.post(
        f"/api/v1/stores/{store_id}/skus",
        headers=superuser_token_headers,
        json={"store_id": store_id, "product_id": product_id, "sku_id": sku_id, "sale_price": "38.00"},
    )
    sps_id = sps_resp.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/stores/{store_id}/skus/{sps_id}",
        headers=superuser_token_headers,
        json={"sale_price": "48.00"},
    )
    assert response.status_code == 200
    assert str(response.json()["data"]["sale_price"]) == "48.00"
