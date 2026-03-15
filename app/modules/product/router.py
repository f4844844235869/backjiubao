import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.product.models import (
    CategoryCreate,
    CategoryPublic,
    CategoryUpdate,
    FundLimitCreate,
    FundLimitPublic,
    FundLimitUpdate,
    GiftTemplateCreate,
    GiftTemplatePublic,
    GiftTemplateUpdate,
    ProductCreate,
    ProductPublic,
    ProductUpdate,
    SKUCreate,
    SKUPublic,
    SKUUpdate,
)
from app.modules.product.service import (
    create_category,
    create_fund_limit,
    create_gift_template,
    create_product,
    create_sku,
    delete_category,
    delete_fund_limit,
    delete_gift_template,
    delete_product,
    delete_sku,
    get_category_by_id,
    get_fund_limit_by_id,
    get_gift_template_by_id,
    get_product_by_code,
    get_product_by_id,
    get_sku_by_code,
    get_sku_by_id,
    list_categories,
    list_fund_limits,
    list_gift_templates,
    list_products,
    list_skus,
    update_category,
    update_fund_limit,
    update_gift_template,
    update_product,
    update_sku,
)

router = APIRouter(prefix="/product", tags=["Product Center"])


# ---------------------------------------------------------------------------
# Category Routes
# ---------------------------------------------------------------------------


@router.get(
    "/categories",
    summary="获取商品分类列表",
    dependencies=[Depends(require_permissions("product.category.read"))],
    response_model=ApiResponse[list[CategoryPublic]],
)
def read_categories(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[CategoryPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    categories = list_categories(session=session, store_id=store_id)
    return success_response(
        request,
        data=[c.model_dump() for c in categories],
        message="获取商品分类列表成功",
    )


@router.post(
    "/categories",
    summary="创建商品分类",
    dependencies=[Depends(require_permissions("product.category.create"))],
    response_model=ApiResponse[CategoryPublic],
)
def create_category_route(
    request: Request, session: SessionDep, body: CategoryCreate
) -> ApiResponse[CategoryPublic]:
    category = create_category(session=session, body=body)
    return success_response(
        request,
        data=category.model_dump(),
        message="创建商品分类成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/categories/{category_id}",
    summary="更新商品分类",
    dependencies=[Depends(require_permissions("product.category.update"))],
    response_model=ApiResponse[CategoryPublic],
)
def update_category_route(
    request: Request,
    session: SessionDep,
    category_id: uuid.UUID,
    body: CategoryUpdate,
) -> ApiResponse[CategoryPublic]:
    category = get_category_by_id(session=session, category_id=category_id)
    if not category:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CATEGORY_NOT_FOUND",
            message="商品分类不存在",
        )
    updated = update_category(
        session=session, category=category, data=body.model_dump(exclude_unset=True)
    )
    return success_response(
        request, data=updated.model_dump(), message="更新商品分类成功"
    )


@router.delete(
    "/categories/{category_id}",
    summary="删除商品分类",
    dependencies=[Depends(require_permissions("product.category.delete"))],
    response_model=ApiResponse[None],
)
def delete_category_route(
    request: Request, session: SessionDep, category_id: uuid.UUID
) -> ApiResponse[None]:
    category = get_category_by_id(session=session, category_id=category_id)
    if not category:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CATEGORY_NOT_FOUND",
            message="商品分类不存在",
        )
    delete_category(session=session, category=category)
    return success_response(request, data=None, message="删除商品分类成功")


# ---------------------------------------------------------------------------
# Product Routes
# ---------------------------------------------------------------------------


@router.get(
    "/products",
    summary="获取商品列表",
    dependencies=[Depends(require_permissions("product.product.read"))],
    response_model=ApiResponse[list[ProductPublic]],
)
def read_products(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[ProductPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    products = list_products(session=session, store_id=store_id)
    return success_response(
        request,
        data=[p.model_dump() for p in products],
        message="获取商品列表成功",
    )


@router.post(
    "/products",
    summary="创建商品",
    dependencies=[Depends(require_permissions("product.product.create"))],
    response_model=ApiResponse[ProductPublic],
)
def create_product_route(
    request: Request, session: SessionDep, body: ProductCreate
) -> ApiResponse[ProductPublic]:
    existing = get_product_by_code(
        session=session, store_id=body.store_id, code=body.code
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CODE_EXISTS",
            message="商品编码在该门店中已存在",
        )
    product = create_product(session=session, body=body)
    return success_response(
        request,
        data=product.model_dump(),
        message="创建商品成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/products/{product_id}",
    summary="更新商品",
    dependencies=[Depends(require_permissions("product.product.update"))],
    response_model=ApiResponse[ProductPublic],
)
def update_product_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    body: ProductUpdate,
) -> ApiResponse[ProductPublic]:
    product = get_product_by_id(session=session, product_id=product_id)
    if not product:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    updated = update_product(
        session=session, product=product, data=body.model_dump(exclude_unset=True)
    )
    return success_response(
        request, data=updated.model_dump(), message="更新商品成功"
    )


@router.delete(
    "/products/{product_id}",
    summary="删除商品",
    dependencies=[Depends(require_permissions("product.product.delete"))],
    response_model=ApiResponse[None],
)
def delete_product_route(
    request: Request, session: SessionDep, product_id: uuid.UUID
) -> ApiResponse[None]:
    product = get_product_by_id(session=session, product_id=product_id)
    if not product:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message="商品不存在",
        )
    delete_product(session=session, product=product)
    return success_response(request, data=None, message="删除商品成功")


# ---------------------------------------------------------------------------
# SKU Routes
# ---------------------------------------------------------------------------


@router.get(
    "/products/{product_id}/skus",
    summary="获取 SKU 列表",
    dependencies=[Depends(require_permissions("product.sku.read"))],
    response_model=ApiResponse[list[SKUPublic]],
)
def read_skus(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
) -> ApiResponse[list[SKUPublic]]:
    skus = list_skus(session=session, product_id=product_id)
    return success_response(
        request, data=[s.model_dump() for s in skus], message="获取 SKU 列表成功"
    )


@router.post(
    "/products/{product_id}/skus",
    summary="创建 SKU",
    dependencies=[Depends(require_permissions("product.sku.create"))],
    response_model=ApiResponse[SKUPublic],
)
def create_sku_route(
    request: Request,
    session: SessionDep,
    product_id: uuid.UUID,
    body: SKUCreate,
) -> ApiResponse[SKUPublic]:
    existing = get_sku_by_code(
        session=session, product_id=product_id, sku_code=body.sku_code
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="SKU_CODE_EXISTS",
            message="SKU 编码在该商品中已存在",
        )
    sku = create_sku(session=session, body=body)
    return success_response(
        request,
        data=sku.model_dump(),
        message="创建 SKU 成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/skus/{sku_id}",
    summary="更新 SKU",
    dependencies=[Depends(require_permissions("product.sku.update"))],
    response_model=ApiResponse[SKUPublic],
)
def update_sku_route(
    request: Request,
    session: SessionDep,
    sku_id: uuid.UUID,
    body: SKUUpdate,
) -> ApiResponse[SKUPublic]:
    sku = get_sku_by_id(session=session, sku_id=sku_id)
    if not sku:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SKU_NOT_FOUND",
            message="SKU 不存在",
        )
    updated = update_sku(
        session=session, sku=sku, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新 SKU 成功")


@router.delete(
    "/skus/{sku_id}",
    summary="删除 SKU",
    dependencies=[Depends(require_permissions("product.sku.delete"))],
    response_model=ApiResponse[None],
)
def delete_sku_route(
    request: Request, session: SessionDep, sku_id: uuid.UUID
) -> ApiResponse[None]:
    sku = get_sku_by_id(session=session, sku_id=sku_id)
    if not sku:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SKU_NOT_FOUND",
            message="SKU 不存在",
        )
    delete_sku(session=session, sku=sku)
    return success_response(request, data=None, message="删除 SKU 成功")


# ---------------------------------------------------------------------------
# FundLimit Routes
# ---------------------------------------------------------------------------


@router.get(
    "/fund-limits",
    summary="获取资金限制列表",
    dependencies=[Depends(require_permissions("product.fund_limit.read"))],
    response_model=ApiResponse[list[FundLimitPublic]],
)
def read_fund_limits(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[FundLimitPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    fund_limits = list_fund_limits(session=session, store_id=store_id)
    return success_response(
        request,
        data=[f.model_dump() for f in fund_limits],
        message="获取资金限制列表成功",
    )


@router.post(
    "/fund-limits",
    summary="创建资金限制",
    dependencies=[Depends(require_permissions("product.fund_limit.create"))],
    response_model=ApiResponse[FundLimitPublic],
)
def create_fund_limit_route(
    request: Request, session: SessionDep, body: FundLimitCreate
) -> ApiResponse[FundLimitPublic]:
    fund_limit = create_fund_limit(session=session, body=body)
    return success_response(
        request,
        data=fund_limit.model_dump(),
        message="创建资金限制成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/fund-limits/{fund_limit_id}",
    summary="更新资金限制",
    dependencies=[Depends(require_permissions("product.fund_limit.update"))],
    response_model=ApiResponse[FundLimitPublic],
)
def update_fund_limit_route(
    request: Request,
    session: SessionDep,
    fund_limit_id: uuid.UUID,
    body: FundLimitUpdate,
) -> ApiResponse[FundLimitPublic]:
    fund_limit = get_fund_limit_by_id(session=session, fund_limit_id=fund_limit_id)
    if not fund_limit:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FUND_LIMIT_NOT_FOUND",
            message="资金限制不存在",
        )
    updated = update_fund_limit(
        session=session, fund_limit=fund_limit, data=body.model_dump(exclude_unset=True)
    )
    return success_response(
        request, data=updated.model_dump(), message="更新资金限制成功"
    )


@router.delete(
    "/fund-limits/{fund_limit_id}",
    summary="删除资金限制",
    dependencies=[Depends(require_permissions("product.fund_limit.delete"))],
    response_model=ApiResponse[None],
)
def delete_fund_limit_route(
    request: Request, session: SessionDep, fund_limit_id: uuid.UUID
) -> ApiResponse[None]:
    fund_limit = get_fund_limit_by_id(session=session, fund_limit_id=fund_limit_id)
    if not fund_limit:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FUND_LIMIT_NOT_FOUND",
            message="资金限制不存在",
        )
    delete_fund_limit(session=session, fund_limit=fund_limit)
    return success_response(request, data=None, message="删除资金限制成功")


# ---------------------------------------------------------------------------
# GiftTemplate Routes
# ---------------------------------------------------------------------------


@router.get(
    "/gift-templates",
    summary="获取赠送模板列表",
    dependencies=[Depends(require_permissions("product.gift_template.read"))],
    response_model=ApiResponse[list[GiftTemplatePublic]],
)
def read_gift_templates(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[GiftTemplatePublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    gift_templates = list_gift_templates(session=session, store_id=store_id)
    return success_response(
        request,
        data=[g.model_dump() for g in gift_templates],
        message="获取赠送模板列表成功",
    )


@router.post(
    "/gift-templates",
    summary="创建赠送模板",
    dependencies=[Depends(require_permissions("product.gift_template.create"))],
    response_model=ApiResponse[GiftTemplatePublic],
)
def create_gift_template_route(
    request: Request, session: SessionDep, body: GiftTemplateCreate
) -> ApiResponse[GiftTemplatePublic]:
    gift_template = create_gift_template(session=session, body=body)
    return success_response(
        request,
        data=gift_template.model_dump(),
        message="创建赠送模板成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/gift-templates/{gift_template_id}",
    summary="更新赠送模板",
    dependencies=[Depends(require_permissions("product.gift_template.update"))],
    response_model=ApiResponse[GiftTemplatePublic],
)
def update_gift_template_route(
    request: Request,
    session: SessionDep,
    gift_template_id: uuid.UUID,
    body: GiftTemplateUpdate,
) -> ApiResponse[GiftTemplatePublic]:
    gift_template = get_gift_template_by_id(
        session=session, gift_template_id=gift_template_id
    )
    if not gift_template:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="GIFT_TEMPLATE_NOT_FOUND",
            message="赠送模板不存在",
        )
    updated = update_gift_template(
        session=session,
        gift_template=gift_template,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request, data=updated.model_dump(), message="更新赠送模板成功"
    )


@router.delete(
    "/gift-templates/{gift_template_id}",
    summary="删除赠送模板",
    dependencies=[Depends(require_permissions("product.gift_template.delete"))],
    response_model=ApiResponse[None],
)
def delete_gift_template_route(
    request: Request, session: SessionDep, gift_template_id: uuid.UUID
) -> ApiResponse[None]:
    gift_template = get_gift_template_by_id(
        session=session, gift_template_id=gift_template_id
    )
    if not gift_template:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="GIFT_TEMPLATE_NOT_FOUND",
            message="赠送模板不存在",
        )
    delete_gift_template(session=session, gift_template=gift_template)
    return success_response(request, data=None, message="删除赠送模板成功")
