import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.product.models import (
    ProductCategoryCreate,
    ProductCategoryPublic,
    ProductCategoryUpdate,
    ProductCreate,
    ProductPublic,
    ProductSkuCreate,
    ProductSkuPublic,
    ProductSkuUpdate,
    ProductUpdate,
    SkuInventoryMappingCreate,
    SkuInventoryMappingPublic,
    SkuInventoryMappingUpdate,
    StoreProductCreate,
    StoreProductPublic,
    StoreProductSkuCreate,
    StoreProductSkuPublic,
    StoreProductSkuUpdate,
    StoreProductUpdate,
)
from app.modules.product.service import (
    create_product,
    create_product_category,
    create_product_sku,
    create_sku_inventory_mapping,
    create_store_product,
    create_store_product_sku,
    delete_sku_inventory_mapping,
    get_product_by_code,
    get_product_by_id,
    get_product_category_by_code,
    get_product_category_by_id,
    get_product_sku_by_code,
    get_product_sku_by_id,
    get_sku_inventory_mapping_by_id,
    get_store_product,
    get_store_product_by_id,
    get_store_product_sku,
    get_store_product_sku_by_id,
    has_child_categories,
    has_products_in_category,
    list_product_categories,
    list_product_skus,
    list_products,
    list_sku_inventory_mappings,
    list_store_product_skus,
    list_store_products,
    update_product,
    update_product_category,
    update_product_sku,
    update_sku_inventory_mapping,
    update_store_product,
    update_store_product_sku,
)

router = APIRouter(tags=["Product"])


# ---------------------------------------------------------------------------
# ProductCategory
# ---------------------------------------------------------------------------

category_router = APIRouter(
    prefix="/product-categories",
    tags=["ProductCategory"],
)


@category_router.get(
    "/",
    summary="获取商品分类列表",
    dependencies=[Depends(require_permissions("product.category.read"))],
    response_model=ApiResponse[list[ProductCategoryPublic]],
)
def read_product_categories(request: Request, session: SessionDep):
    categories = list_product_categories(session=session)
    return success_response(
        request,
        data=[c.model_dump() for c in categories],
        message="获取商品分类列表成功",
    )


@category_router.post(
    "/",
    summary="创建商品分类",
    dependencies=[Depends(require_permissions("product.category.manage"))],
    response_model=ApiResponse[ProductCategoryPublic],
)
def create_product_category_route(
    request: Request, session: SessionDep, body: ProductCategoryCreate
):
    existing = get_product_category_by_code(session=session, code=body.code)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CATEGORY_CODE_EXISTS",
            message="分类编码已存在",
        )
    category = create_product_category(session=session, body=body)
    return success_response(
        request,
        data=category.model_dump(),
        message="创建商品分类成功",
        status_code=status.HTTP_201_CREATED,
    )


@category_router.patch(
    "/{category_id}",
    summary="更新商品分类",
    dependencies=[Depends(require_permissions("product.category.manage"))],
    response_model=ApiResponse[ProductCategoryPublic],
)
def update_product_category_route(
    request: Request,
    session: SessionDep,
    category_id: uuid.UUID,
    body: ProductCategoryUpdate,
):
    category = get_product_category_by_id(session=session, category_id=category_id)
    if not category or category.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_CATEGORY_NOT_FOUND",
            message="商品分类不存在",
        )
    if body.code and body.code != category.code:
        existing = get_product_category_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_CATEGORY_CODE_EXISTS",
                message="分类编码已存在",
            )
    updated = update_product_category(
        session=session,
        category=category,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=updated.model_dump(),
        message="更新商品分类成功",
    )


@category_router.post(
    "/{category_id}/disable",
    summary="停用商品分类",
    dependencies=[Depends(require_permissions("product.category.manage"))],
    response_model=ApiResponse[ProductCategoryPublic],
)
def disable_product_category_route(
    request: Request, session: SessionDep, category_id: uuid.UUID
):
    category = get_product_category_by_id(session=session, category_id=category_id)
    if not category or category.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_CATEGORY_NOT_FOUND",
            message="商品分类不存在",
        )
    updated = update_product_category(
        session=session,
        category=category,
        data={"is_active": False},
    )
    return success_response(
        request,
        data=updated.model_dump(),
        message="停用商品分类成功",
    )


@category_router.delete(
    "/{category_id}",
    summary="逻辑删除商品分类",
    dependencies=[Depends(require_permissions("product.category.manage"))],
    response_model=ApiResponse[None],
)
def delete_product_category_route(
    request: Request, session: SessionDep, category_id: uuid.UUID
):
    category = get_product_category_by_id(session=session, category_id=category_id)
    if not category or category.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_CATEGORY_NOT_FOUND",
            message="商品分类不存在",
        )
    if has_child_categories(session=session, category_id=category_id):
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CATEGORY_HAS_CHILDREN",
            message="该分类下存在子分类，不可删除",
        )
    if has_products_in_category(session=session, category_id=category_id):
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CATEGORY_HAS_PRODUCTS",
            message="该分类下存在商品，不可删除",
        )
    update_product_category(
        session=session,
        category=category,
        data={"is_deleted": True, "is_active": False},
    )
    return success_response(request, data=None, message="删除商品分类成功")


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

product_router = APIRouter(prefix="/products", tags=["Product"])


@product_router.get(
    "/",
    summary="获取商品列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[ProductPublic]],
)
def read_products(
    request: Request,
    session: SessionDep,
    category_id: uuid.UUID | None = None,
    is_active: bool | None = None,
):
    products = list_products(
        session=session, category_id=category_id, is_active=is_active
    )
    return success_response(
        request,
        data=[p.model_dump() for p in products],
        message="获取商品列表成功",
    )


@product_router.post(
    "/",
    summary="创建商品",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductPublic],
)
def create_product_route(
    request: Request, session: SessionDep, body: ProductCreate
):
    existing = get_product_by_code(session=session, code=body.code)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CODE_EXISTS",
            message="商品编码已存在",
        )
    product = create_product(session=session, body=body)
    return success_response(
        request,
        data=product.model_dump(),
        message="创建商品成功",
        status_code=status.HTTP_201_CREATED,
    )


@product_router.get(
    "/{product_id}",
    summary="获取商品详情",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[ProductPublic],
)
def read_product(request: Request, session: SessionDep, product_id: uuid.UUID):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    return success_response(
        request, data=product.model_dump(), message="获取商品详情成功"
    )


@product_router.patch(
    "/{product_id}",
    summary="更新商品",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductPublic],
)
def update_product_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    body: ProductUpdate,
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    if body.code and body.code != product.code:
        existing = get_product_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_CODE_EXISTS",
                message="商品编码已存在",
            )
    updated = update_product(
        session=session,
        product=product,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新商品成功"
    )


@product_router.post(
    "/{product_id}/disable",
    summary="停用商品",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductPublic],
)
def disable_product_route(
    request: Request, session: SessionDep, product_id: uuid.UUID
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    updated = update_product(
        session=session, product=product, data={"is_active": False}
    )
    return success_response(
        request, data=updated.model_dump(), message="停用商品成功"
    )


@product_router.delete(
    "/{product_id}",
    summary="逻辑删除商品",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[None],
)
def delete_product_route(
    request: Request, session: SessionDep, product_id: uuid.UUID
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    update_product(
        session=session,
        product=product,
        data={"is_deleted": True, "is_active": False},
    )
    return success_response(request, data=None, message="删除商品成功")


# ---------------------------------------------------------------------------
# ProductSku
# ---------------------------------------------------------------------------


@product_router.get(
    "/{product_id}/skus",
    summary="获取商品SKU列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[ProductSkuPublic]],
)
def read_product_skus(
    request: Request, session: SessionDep, product_id: uuid.UUID
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    skus = list_product_skus(session=session, product_id=product_id)
    return success_response(
        request,
        data=[s.model_dump() for s in skus],
        message="获取商品SKU列表成功",
    )


@product_router.post(
    "/{product_id}/skus",
    summary="创建商品SKU",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductSkuPublic],
)
def create_product_sku_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    body: ProductSkuCreate,
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    existing = get_product_sku_by_code(session=session, code=body.code)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_SKU_CODE_EXISTS",
            message="SKU编码已存在",
        )
    # Ensure product_id from path is used
    body.product_id = product_id
    sku = create_product_sku(session=session, body=body)
    return success_response(
        request,
        data=sku.model_dump(),
        message="创建商品SKU成功",
        status_code=status.HTTP_201_CREATED,
    )


sku_router = APIRouter(prefix="/skus", tags=["ProductSku"])


@sku_router.patch(
    "/{sku_id}",
    summary="更新SKU",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductSkuPublic],
)
def update_product_sku_route(
    request: Request,
    session: SessionDep,
    sku_id: uuid.UUID,
    body: ProductSkuUpdate,
):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    if body.code and body.code != sku.code:
        existing = get_product_sku_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_SKU_CODE_EXISTS",
                message="SKU编码已存在",
            )
    updated = update_product_sku(
        session=session,
        sku=sku,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新SKU成功"
    )


@sku_router.post(
    "/{sku_id}/disable",
    summary="停用SKU",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductSkuPublic],
)
def disable_product_sku_route(
    request: Request, session: SessionDep, sku_id: uuid.UUID
):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    updated = update_product_sku(
        session=session, sku=sku, data={"is_active": False}
    )
    return success_response(
        request, data=updated.model_dump(), message="停用SKU成功"
    )


@sku_router.delete(
    "/{sku_id}",
    summary="逻辑删除SKU",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[None],
)
def delete_product_sku_route(
    request: Request, session: SessionDep, sku_id: uuid.UUID
):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    update_product_sku(
        session=session,
        sku=sku,
        data={"is_deleted": True, "is_active": False},
    )
    return success_response(request, data=None, message="删除SKU成功")


@sku_router.get(
    "/{sku_id}/inventory-mappings",
    summary="获取SKU库存扣减映射",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[SkuInventoryMappingPublic]],
)
def read_sku_inventory_mappings(
    request: Request, session: SessionDep, sku_id: uuid.UUID
):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    mappings = list_sku_inventory_mappings(session=session, sku_id=sku_id)
    return success_response(
        request,
        data=[m.model_dump() for m in mappings],
        message="获取SKU库存扣减映射成功",
    )


@sku_router.post(
    "/{sku_id}/inventory-mappings",
    summary="创建SKU库存扣减映射",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[SkuInventoryMappingPublic],
)
def create_sku_inventory_mapping_route(
    request: Request,
    session: SessionDep,
    sku_id: uuid.UUID,
    body: SkuInventoryMappingCreate,
):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    body.sku_id = sku_id
    mapping = create_sku_inventory_mapping(session=session, body=body)
    return success_response(
        request,
        data=mapping.model_dump(),
        message="创建SKU库存扣减映射成功",
        status_code=status.HTTP_201_CREATED,
    )


@sku_router.patch(
    "/{sku_id}/inventory-mappings/{mapping_id}",
    summary="更新SKU库存扣减映射",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[SkuInventoryMappingPublic],
)
def update_sku_inventory_mapping_route(
    request: Request,
    session: SessionDep,
    sku_id: uuid.UUID,
    mapping_id: uuid.UUID,
    body: SkuInventoryMappingUpdate,
):
    mapping = get_sku_inventory_mapping_by_id(
        session=session, mapping_id=mapping_id
    )
    if not mapping or mapping.sku_id != sku_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SKU_INVENTORY_MAPPING_NOT_FOUND",
            message="库存扣减映射不存在",
        )
    updated = update_sku_inventory_mapping(
        session=session,
        mapping=mapping,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新SKU库存扣减映射成功"
    )


@sku_router.delete(
    "/{sku_id}/inventory-mappings/{mapping_id}",
    summary="删除SKU库存扣减映射",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[None],
)
def delete_sku_inventory_mapping_route(
    request: Request,
    session: SessionDep,
    sku_id: uuid.UUID,
    mapping_id: uuid.UUID,
):
    mapping = get_sku_inventory_mapping_by_id(
        session=session, mapping_id=mapping_id
    )
    if not mapping or mapping.sku_id != sku_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SKU_INVENTORY_MAPPING_NOT_FOUND",
            message="库存扣减映射不存在",
        )
    delete_sku_inventory_mapping(session=session, mapping=mapping)
    return success_response(request, data=None, message="删除SKU库存扣减映射成功")


# ---------------------------------------------------------------------------
# StoreProduct & StoreProductSku
# ---------------------------------------------------------------------------

store_product_router = APIRouter(prefix="/stores", tags=["StoreProduct"])


@store_product_router.get(
    "/{store_id}/products",
    summary="获取门店商品配置列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[StoreProductPublic]],
)
def read_store_products(
    request: Request, session: SessionDep, store_id: uuid.UUID
):
    items = list_store_products(session=session, store_id=store_id)
    return success_response(
        request,
        data=[i.model_dump() for i in items],
        message="获取门店商品配置列表成功",
    )


@store_product_router.post(
    "/{store_id}/products",
    summary="创建门店商品配置",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[StoreProductPublic],
)
def create_store_product_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    body: StoreProductCreate,
):
    body.store_id = store_id
    existing = get_store_product(
        session=session, store_id=store_id, product_id=body.product_id
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="STORE_PRODUCT_EXISTS",
            message="该商品已在当前门店配置",
        )
    sp = create_store_product(session=session, body=body)
    return success_response(
        request,
        data=sp.model_dump(),
        message="创建门店商品配置成功",
        status_code=status.HTTP_201_CREATED,
    )


@store_product_router.patch(
    "/{store_id}/products/{store_product_id}",
    summary="更新门店商品配置",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[StoreProductPublic],
)
def update_store_product_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    store_product_id: uuid.UUID,
    body: StoreProductUpdate,
):
    sp = get_store_product_by_id(session=session, store_product_id=store_product_id)
    if not sp or sp.store_id != store_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="STORE_PRODUCT_NOT_FOUND",
            message="门店商品配置不存在",
        )
    updated = update_store_product(
        session=session,
        store_product=sp,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新门店商品配置成功"
    )


@store_product_router.get(
    "/{store_id}/skus",
    summary="获取门店SKU销售配置列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[StoreProductSkuPublic]],
)
def read_store_product_skus(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    product_id: uuid.UUID | None = None,
):
    items = list_store_product_skus(
        session=session, store_id=store_id, product_id=product_id
    )
    return success_response(
        request,
        data=[i.model_dump() for i in items],
        message="获取门店SKU销售配置列表成功",
    )


@store_product_router.post(
    "/{store_id}/skus",
    summary="创建门店SKU销售配置",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[StoreProductSkuPublic],
)
def create_store_product_sku_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    body: StoreProductSkuCreate,
):
    body.store_id = store_id
    existing = get_store_product_sku(
        session=session, store_id=store_id, sku_id=body.sku_id
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="STORE_PRODUCT_SKU_EXISTS",
            message="该SKU已在当前门店配置",
        )
    sps = create_store_product_sku(session=session, body=body)
    return success_response(
        request,
        data=sps.model_dump(),
        message="创建门店SKU销售配置成功",
        status_code=status.HTTP_201_CREATED,
    )


@store_product_router.patch(
    "/{store_id}/skus/{store_product_sku_id}",
    summary="更新门店SKU销售配置",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[StoreProductSkuPublic],
)
def update_store_product_sku_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    store_product_sku_id: uuid.UUID,
    body: StoreProductSkuUpdate,
):
    sps = get_store_product_sku_by_id(
        session=session, store_product_sku_id=store_product_sku_id
    )
    if not sps or sps.store_id != store_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="STORE_PRODUCT_SKU_NOT_FOUND",
            message="门店SKU销售配置不存在",
        )
    updated = update_store_product_sku(
        session=session,
        store_product_sku=sps,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新门店SKU销售配置成功"
    )


router.include_router(category_router)
router.include_router(product_router)
router.include_router(sku_router)
router.include_router(store_product_router)
