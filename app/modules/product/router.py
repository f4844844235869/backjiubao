import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.product.models import (
    DISPLAY_TYPE_SELECT,
    ProductAttributeAssignmentCreate,
    ProductAttributeAssignmentPublic,
    ProductAttributeAssignmentUpdate,
    ProductAttributeAssignmentValueCreate,
    ProductAttributeAssignmentValuePublic,
    ProductAttributeCreate,
    ProductAttributePublic,
    ProductAttributeUpdate,
    ProductAttributeValueCreate,
    ProductAttributeValuePublic,
    ProductAttributeValueUpdate,
    ProductCategoryCreate,
    ProductCategoryPublic,
    ProductCategoryUpdate,
    ProductCreate,
    ProductPublic,
    ProductSkuCreate,
    ProductSkuGenerationSummary,
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
    create_product_attribute,
    create_product_attribute_assignment,
    create_product_attribute_assignment_value,
    create_product_attribute_value,
    create_product_category,
    create_product_sku,
    create_sku_inventory_mapping,
    create_store_product,
    create_store_product_sku,
    delete_product_attribute_assignment_value,
    delete_sku_inventory_mapping,
    ensure_default_sku_for_product,
    generate_product_skus,
    get_product_attribute_assignment,
    get_product_attribute_assignment_by_id,
    get_product_attribute_assignment_value,
    get_product_attribute_assignment_value_by_id,
    get_product_attribute_by_code,
    get_product_attribute_by_id,
    get_product_attribute_value_by_code,
    get_product_attribute_value_by_id,
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
    list_product_attribute_assignment_values,
    list_product_attribute_assignments,
    list_product_attribute_values,
    list_product_attributes,
    list_product_categories,
    list_product_sku_attribute_values,
    list_product_skus,
    list_products,
    list_sku_inventory_mappings,
    list_store_product_skus,
    list_store_products,
    product_has_attribute_assignments,
    update_product,
    update_product_attribute,
    update_product_attribute_assignment,
    update_product_attribute_value,
    update_product_category,
    update_product_sku,
    update_sku_inventory_mapping,
    update_store_product,
    update_store_product_sku,
)

router = APIRouter(tags=["Product"])


def _serialize_product_attribute(attribute) -> ProductAttributePublic:
    return ProductAttributePublic.model_validate(attribute)


def _serialize_product_attribute_value(attribute_value) -> ProductAttributeValuePublic:
    return ProductAttributeValuePublic.model_validate(attribute_value)


def _serialize_assignment_value(
    *, session: SessionDep, assignment_value
) -> ProductAttributeAssignmentValuePublic:
    value = get_product_attribute_value_by_id(
        session=session, attribute_value_id=assignment_value.attribute_value_id
    )
    if value is None:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PRODUCT_ATTRIBUTE_VALUE_NOT_FOUND",
            message="商品属性值不存在",
        )
    payload = assignment_value.model_dump()
    payload["attribute_value"] = _serialize_product_attribute_value(value).model_dump()
    return ProductAttributeAssignmentValuePublic.model_validate(payload)


def _serialize_assignment(
    *, session: SessionDep, assignment
) -> ProductAttributeAssignmentPublic:
    attribute = get_product_attribute_by_id(
        session=session, attribute_id=assignment.attribute_id
    )
    if attribute is None:
        raise_api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="PRODUCT_ATTRIBUTE_NOT_FOUND",
            message="商品属性不存在",
        )
    values = [
        _serialize_assignment_value(session=session, assignment_value=item)
        for item in list_product_attribute_assignment_values(
            session=session, assignment_id=assignment.id
        )
    ]
    payload = assignment.model_dump()
    payload["attribute"] = _serialize_product_attribute(attribute).model_dump()
    payload["values"] = [item.model_dump() for item in values]
    return ProductAttributeAssignmentPublic.model_validate(payload)


def _serialize_sku(*, session: SessionDep, sku) -> ProductSkuPublic:
    payload = sku.model_dump()
    links = list_product_sku_attribute_values(session=session, sku_id=sku.id)
    attribute_values = []
    for link in links:
        attribute = get_product_attribute_by_id(
            session=session, attribute_id=link.attribute_id
        )
        attribute_value = get_product_attribute_value_by_id(
            session=session, attribute_value_id=link.attribute_value_id
        )
        if attribute is None or attribute_value is None:
            continue
        attribute_values.append(
            {
                "attribute_id": attribute.id,
                "attribute_code": attribute.code,
                "attribute_name": attribute.name,
                "attribute_value_id": attribute_value.id,
                "attribute_value_code": attribute_value.code,
                "attribute_value_name": attribute_value.name,
            }
        )
    payload["attribute_values"] = attribute_values
    return ProductSkuPublic.model_validate(payload)


# ---------------------------------------------------------------------------
# ProductAttribute
# ---------------------------------------------------------------------------


attribute_router = APIRouter(prefix="/product-attributes", tags=["ProductAttribute"])


@attribute_router.get(
    "/",
    summary="获取商品属性列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[ProductAttributePublic]],
)
def read_product_attributes(request: Request, session: SessionDep):
    items = list_product_attributes(session=session)
    return success_response(
        request,
        data=[_serialize_product_attribute(item).model_dump() for item in items],
        message="获取商品属性列表成功",
    )


@attribute_router.post(
    "/",
    summary="创建商品属性",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributePublic],
)
def create_product_attribute_route(
    request: Request, session: SessionDep, body: ProductAttributeCreate
):
    if body.display_type != DISPLAY_TYPE_SELECT:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="当前仅支持 SELECT 类型属性",
        )
    existing = get_product_attribute_by_code(session=session, code=body.code)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_ATTRIBUTE_CODE_EXISTS",
            message="属性编码已存在",
        )
    attribute = create_product_attribute(session=session, body=body)
    return success_response(
        request,
        data=_serialize_product_attribute(attribute).model_dump(),
        message="创建商品属性成功",
        status_code=status.HTTP_201_CREATED,
    )


@attribute_router.patch(
    "/{attribute_id}",
    summary="更新商品属性",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributePublic],
)
def update_product_attribute_route(
    request: Request,
    session: SessionDep,
    attribute_id: uuid.UUID,
    body: ProductAttributeUpdate,
):
    attribute = get_product_attribute_by_id(session=session, attribute_id=attribute_id)
    if attribute is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_NOT_FOUND",
            message="商品属性不存在",
        )
    if body.display_type and body.display_type != DISPLAY_TYPE_SELECT:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="当前仅支持 SELECT 类型属性",
        )
    if body.code and body.code != attribute.code:
        existing = get_product_attribute_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_ATTRIBUTE_CODE_EXISTS",
                message="属性编码已存在",
            )
    updated = update_product_attribute(
        session=session,
        attribute=attribute,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=_serialize_product_attribute(updated).model_dump(),
        message="更新商品属性成功",
    )


@attribute_router.get(
    "/{attribute_id}/values",
    summary="获取商品属性值列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[ProductAttributeValuePublic]],
)
def read_product_attribute_values(
    request: Request, session: SessionDep, attribute_id: uuid.UUID
):
    attribute = get_product_attribute_by_id(session=session, attribute_id=attribute_id)
    if attribute is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_NOT_FOUND",
            message="商品属性不存在",
        )
    values = list_product_attribute_values(session=session, attribute_id=attribute_id)
    return success_response(
        request,
        data=[_serialize_product_attribute_value(item).model_dump() for item in values],
        message="获取商品属性值列表成功",
    )


@attribute_router.post(
    "/{attribute_id}/values",
    summary="创建商品属性值",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributeValuePublic],
)
def create_product_attribute_value_route(
    request: Request,
    session: SessionDep,
    attribute_id: uuid.UUID,
    body: ProductAttributeValueCreate,
):
    attribute = get_product_attribute_by_id(session=session, attribute_id=attribute_id)
    if attribute is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_NOT_FOUND",
            message="商品属性不存在",
        )
    existing = get_product_attribute_value_by_code(
        session=session, attribute_id=attribute_id, code=body.code
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_ATTRIBUTE_VALUE_CODE_EXISTS",
            message="属性值编码已存在",
        )
    body.attribute_id = attribute_id
    value = create_product_attribute_value(session=session, body=body)
    return success_response(
        request,
        data=_serialize_product_attribute_value(value).model_dump(),
        message="创建商品属性值成功",
        status_code=status.HTTP_201_CREATED,
    )


attribute_value_router = APIRouter(
    prefix="/product-attribute-values",
    tags=["ProductAttributeValue"],
)


@attribute_value_router.patch(
    "/{attribute_value_id}",
    summary="更新商品属性值",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributeValuePublic],
)
def update_product_attribute_value_route(
    request: Request,
    session: SessionDep,
    attribute_value_id: uuid.UUID,
    body: ProductAttributeValueUpdate,
):
    attribute_value = get_product_attribute_value_by_id(
        session=session, attribute_value_id=attribute_value_id
    )
    if attribute_value is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_VALUE_NOT_FOUND",
            message="商品属性值不存在",
        )
    if body.code and body.code != attribute_value.code:
        existing = get_product_attribute_value_by_code(
            session=session,
            attribute_id=attribute_value.attribute_id,
            code=body.code,
        )
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_ATTRIBUTE_VALUE_CODE_EXISTS",
                message="属性值编码已存在",
            )
    updated = update_product_attribute_value(
        session=session,
        attribute_value=attribute_value,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=_serialize_product_attribute_value(updated).model_dump(),
        message="更新商品属性值成功",
    )


# ---------------------------------------------------------------------------
# ProductCategory
# ---------------------------------------------------------------------------


category_router = APIRouter(prefix="/product-categories", tags=["ProductCategory"])


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


@product_router.get(
    "/{product_id}/attributes",
    summary="获取商品属性绑定列表",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[list[ProductAttributeAssignmentPublic]],
)
def read_product_attribute_assignments(
    request: Request, session: SessionDep, product_id: uuid.UUID
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    items = list_product_attribute_assignments(session=session, product_id=product_id)
    return success_response(
        request,
        data=[_serialize_assignment(session=session, assignment=item).model_dump() for item in items],
        message="获取商品属性绑定列表成功",
    )


@product_router.post(
    "/{product_id}/attributes",
    summary="绑定商品属性",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributeAssignmentPublic],
)
def create_product_attribute_assignment_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    body: ProductAttributeAssignmentCreate,
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    attribute = get_product_attribute_by_id(session=session, attribute_id=body.attribute_id)
    if attribute is None:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_NOT_FOUND",
            message="商品属性不存在",
        )
    existing = get_product_attribute_assignment(
        session=session, product_id=product_id, attribute_id=body.attribute_id
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_ATTRIBUTE_ALREADY_ASSIGNED",
            message="该商品已绑定当前属性",
        )
    body.product_id = product_id
    assignment = create_product_attribute_assignment(session=session, body=body)
    return success_response(
        request,
        data=_serialize_assignment(session=session, assignment=assignment).model_dump(),
        message="绑定商品属性成功",
        status_code=status.HTTP_201_CREATED,
    )


@product_router.patch(
    "/{product_id}/attributes/{assignment_id}",
    summary="更新商品属性绑定",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributeAssignmentPublic],
)
def update_product_attribute_assignment_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: ProductAttributeAssignmentUpdate,
):
    assignment = get_product_attribute_assignment_by_id(
        session=session, assignment_id=assignment_id
    )
    if assignment is None or assignment.product_id != product_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_ASSIGNMENT_NOT_FOUND",
            message="商品属性绑定不存在",
        )
    updated = update_product_attribute_assignment(
        session=session,
        assignment=assignment,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=_serialize_assignment(session=session, assignment=updated).model_dump(),
        message="更新商品属性绑定成功",
    )


@product_router.post(
    "/{product_id}/attributes/{assignment_id}/values",
    summary="为商品属性绑定可选值",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductAttributeAssignmentValuePublic],
)
def create_product_attribute_assignment_value_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: ProductAttributeAssignmentValueCreate,
):
    assignment = get_product_attribute_assignment_by_id(
        session=session, assignment_id=assignment_id
    )
    if assignment is None or assignment.product_id != product_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_ASSIGNMENT_NOT_FOUND",
            message="商品属性绑定不存在",
        )
    attribute_value = get_product_attribute_value_by_id(
        session=session, attribute_value_id=body.attribute_value_id
    )
    if attribute_value is None or attribute_value.attribute_id != assignment.attribute_id:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="属性值不属于当前商品属性",
        )
    existing = get_product_attribute_assignment_value(
        session=session,
        assignment_id=assignment_id,
        attribute_value_id=body.attribute_value_id,
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_ATTRIBUTE_VALUE_ALREADY_ASSIGNED",
            message="该属性值已绑定到当前商品属性",
        )
    body.assignment_id = assignment_id
    assignment_value = create_product_attribute_assignment_value(session=session, body=body)
    return success_response(
        request,
        data=_serialize_assignment_value(
            session=session, assignment_value=assignment_value
        ).model_dump(),
        message="绑定商品属性值成功",
        status_code=status.HTTP_201_CREATED,
    )


@product_router.delete(
    "/{product_id}/attributes/{assignment_id}/values/{assignment_value_id}",
    summary="删除商品属性绑定值",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[None],
)
def delete_product_attribute_assignment_value_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    assignment_id: uuid.UUID,
    assignment_value_id: uuid.UUID,
):
    assignment = get_product_attribute_assignment_by_id(
        session=session, assignment_id=assignment_id
    )
    if assignment is None or assignment.product_id != product_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_ASSIGNMENT_NOT_FOUND",
            message="商品属性绑定不存在",
        )
    assignment_value = get_product_attribute_assignment_value_by_id(
        session=session, assignment_value_id=assignment_value_id
    )
    if assignment_value is None or assignment_value.assignment_id != assignment_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_ATTRIBUTE_ASSIGNMENT_VALUE_NOT_FOUND",
            message="商品属性绑定值不存在",
        )
    delete_product_attribute_assignment_value(
        session=session, assignment_value=assignment_value
    )
    return success_response(request, data=None, message="删除商品属性绑定值成功")


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
        data=[_serialize_sku(session=session, sku=item).model_dump() for item in skus],
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
    if product_has_attribute_assignments(session=session, product_id=product_id):
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_SKU_MANAGED_BY_ATTRIBUTES",
            message="当前商品已启用属性驱动SKU，请使用SKU生成接口",
        )
    if body.code:
        existing = get_product_sku_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_SKU_CODE_EXISTS",
                message="SKU编码已存在",
            )
    body.product_id = product_id
    sku = create_product_sku(session=session, body=body)
    return success_response(
        request,
        data=_serialize_sku(session=session, sku=sku).model_dump(),
        message="创建商品SKU成功",
        status_code=status.HTTP_201_CREATED,
    )


@product_router.post(
    "/{product_id}/skus/generate",
    summary="生成商品SKU",
    dependencies=[Depends(require_permissions("product.manage"))],
    response_model=ApiResponse[ProductSkuGenerationSummary],
)
def generate_product_skus_route(
    request: Request, session: SessionDep, product_id: uuid.UUID
):
    product = get_product_by_id(session=session, product_id=product_id)
    if not product or product.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    try:
        result = generate_product_skus(session=session, product=product)
    except ValueError as exc:
        if str(exc) == "PRODUCT_HAS_NO_SKU_ATTRIBUTES":
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_HAS_NO_SKU_ATTRIBUTES",
                message="当前商品尚未绑定参与SKU的属性",
            )
        if str(exc) == "PRODUCT_ATTRIBUTE_VALUES_REQUIRED":
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_ATTRIBUTE_VALUES_REQUIRED",
                message="商品属性必须至少绑定一个启用的属性值",
            )
        raise
    payload = ProductSkuGenerationSummary(
        created=[_serialize_sku(session=session, sku=item) for item in result["created"]],
        retained=[_serialize_sku(session=session, sku=item) for item in result["retained"]],
        deactivated=[
            _serialize_sku(session=session, sku=item) for item in result["deactivated"]
        ],
    )
    return success_response(
        request,
        data=payload.model_dump(),
        message="生成商品SKU成功",
    )


sku_router = APIRouter(prefix="/skus", tags=["ProductSku"])


@sku_router.get(
    "/{sku_id}",
    summary="获取SKU详情",
    dependencies=[Depends(require_permissions("product.read"))],
    response_model=ApiResponse[ProductSkuPublic],
)
def read_product_sku(request: Request, session: SessionDep, sku_id: uuid.UUID):
    sku = get_product_sku_by_id(session=session, sku_id=sku_id)
    if not sku or sku.is_deleted:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_SKU_NOT_FOUND",
            message="SKU不存在",
        )
    return success_response(
        request,
        data=_serialize_sku(session=session, sku=sku).model_dump(),
        message="获取SKU详情成功",
    )


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
    if body.code is not None:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="SKU编码不允许修改",
        )
    updated = update_product_sku(
        session=session,
        sku=sku,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=_serialize_sku(session=session, sku=updated).model_dump(),
        message="更新SKU成功",
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
        session=session,
        sku=sku,
        data={"is_active": False, "is_default": False},
    )
    ensure_default_sku_for_product(session=session, product_id=updated.product_id)
    updated = get_product_sku_by_id(session=session, sku_id=sku_id)
    assert updated is not None
    return success_response(
        request,
        data=_serialize_sku(session=session, sku=updated).model_dump(),
        message="停用SKU成功",
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
        data={"is_deleted": True, "is_active": False, "is_default": False},
    )
    ensure_default_sku_for_product(session=session, product_id=sku.product_id)
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
    mapping = get_sku_inventory_mapping_by_id(session=session, mapping_id=mapping_id)
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
    mapping = get_sku_inventory_mapping_by_id(session=session, mapping_id=mapping_id)
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


router.include_router(attribute_router)
router.include_router(attribute_value_router)
router.include_router(category_router)
router.include_router(product_router)
router.include_router(sku_router)
router.include_router(store_product_router)
