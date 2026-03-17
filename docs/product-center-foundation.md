# 商品中心：接口与表结构说明

版本：V1.0  
阶段：商品中心  
迁移文件：`20260316_product_center.py`  
依赖模块：门店（store）、权限（iam）  
被依赖模块：POS、库存、会员钱包、业绩

---

## 1. 本次新增数据库表

本次共新增 **6 张表**，均位于迁移文件 `app/alembic/versions/20260316_product_center.py`。

### 1.1 `product_category` — 商品分类表

用途：管理商品的一级和二级分类，用于商品归类、前台菜单展示和查询筛选。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `parent_id` | UUID / null | 父分类 ID，一级分类为空 |
| `code` | varchar(64) | 分类编码，全局唯一 |
| `name` | varchar(128) | 分类名称，同一父级下唯一 |
| `level` | int | 分类层级，1 或 2 |
| `sort_order` | int | 排序值，越小越靠前 |
| `is_active` | bool | 是否启用 |
| `is_deleted` | bool | 逻辑删除标记 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

约束：`uq_product_category_code`（编码唯一）、`uq_product_category_name_parent`（同一父级下名称唯一）

---

### 1.2 `product` — 商品主表

用途：存储商品的主档信息，定义商品基础属性、业务规则默认值（资金限制、业绩、库存参与等）及酒吧特有字段（存酒、赠送、低消等）。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `code` | varchar(64) | 商品编码，全局唯一 |
| `name` | varchar(128) | 商品名称，全局唯一 |
| `display_name` | varchar(128) | 展示名称（前台用） |
| `print_name` | varchar(64) | 打印名称（小票用） |
| `category_id` | UUID | 关联分类，外键 `product_category.id` |
| `product_type` | varchar(32) | 商品类型：`NORMAL` / `SERVICE` / `FEE` / `VIRTUAL` |
| `brand_name` | varchar(128) | 品牌名称 |
| `series_name` | varchar(128) | 系列名称 |
| `description` | text | 商品描述 |
| `unit` | varchar(32) | 默认销售单位 |
| `suggested_price` | numeric(18,2) | 建议零售价 |
| `default_fund_usage_type` | varchar(32) | 默认资金限制：`CASH_OR_PRINCIPAL_ONLY` / `GIFT_ONLY` / `ALL_ALLOWED` / `NO_MEMBER_BALANCE` / `OFFLINE_ONLY` |
| `is_inventory_item` | bool | 是否参与库存 |
| `is_commission_enabled` | bool | 是否参与业绩 |
| `default_commission_type` | varchar(16) | 默认业绩类型：`NONE` / `FIXED` / `RATIO` |
| `default_commission_value` | numeric(18,2) | 默认业绩值 |
| `is_profit_enabled` | bool | 是否参与利润分析 |
| `standard_cost_price` | numeric(18,2) | 标准成本价（参考） |
| `is_storable` | bool | 是否允许存酒 |
| `is_gift_allowed` | bool | 是否允许赠送 |
| `is_min_consumption_eligible` | bool | 是否计入低消 |
| `is_front_visible` | bool | 是否前台可见 |
| `is_pos_visible` | bool | 是否 POS 可见 |
| `is_sale_enabled` | bool | 是否允许销售 |
| `is_active` | bool | 是否启用 |
| `is_deleted` | bool | 逻辑删除标记 |
| `remark` | varchar(512) | 备注 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

约束：`uq_product_code`（编码唯一）、`uq_product_name`（名称唯一）

---

### 1.3 `product_sku` — 商品 SKU 表

用途：存储商品的规格单元（SKU），支持同一商品的多个规格（如不同容量、不同包装），每个 SKU 可覆盖商品级的资金限制、业绩、库存配置。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `product_id` | UUID | 所属商品，外键 `product.id` |
| `code` | varchar(64) | SKU 编码，全局唯一 |
| `name` | varchar(128) | SKU 名称，同一商品下唯一 |
| `spec_text` | varchar(256) | 规格描述文本 |
| `suggested_price` | numeric(18,2) | SKU 建议价（空则继承商品） |
| `barcode` | varchar(64) | 条码 |
| `is_default` | bool | 是否默认 SKU |
| `fund_usage_type` | varchar(32) | SKU 级资金限制（空则继承商品） |
| `is_inventory_item` | bool / null | SKU 是否参与库存（空则继承商品） |
| `is_commission_enabled` | bool / null | SKU 是否参与业绩（空则继承商品） |
| `commission_type` | varchar(16) / null | SKU 级业绩类型（空则继承商品） |
| `commission_value` | numeric(18,2) / null | SKU 级业绩值 |
| `is_profit_enabled` | bool / null | SKU 是否参与利润分析 |
| `standard_cost_price` | numeric(18,2) / null | SKU 标准成本价 |
| `inventory_mode` | varchar(16) | 库存模式：`NONE` / `DIRECT` / `MAPPING` |
| `allow_negative_inventory` | bool | 是否允许负库存 |
| `is_sale_enabled` | bool | 是否允许销售 |
| `is_active` | bool | 是否启用 |
| `is_deleted` | bool | 逻辑删除标记 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

约束：`uq_product_sku_code`（编码全局唯一）、`uq_product_sku_product_id_name`（同商品下名称唯一）

---

### 1.4 `store_product` — 门店商品配置表

用途：记录某门店对某商品的启用/可见配置。全局商品默认不挂载到门店，需要门店单独配置上架。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `store_id` | UUID | 门店 ID，外键 `store.id` |
| `product_id` | UUID | 商品 ID，外键 `product.id` |
| `is_enabled` | bool | 该门店内是否启用此商品 |
| `is_visible` | bool | 前台是否可见 |
| `sort_order` | int | 门店内排序 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

约束：`uq_store_product_store_id_product_id`（同一门店内同一商品只允许一条记录）

---

### 1.5 `store_product_sku` — 门店 SKU 销售配置表

用途：记录某门店对某 SKU 的销售价格及相关配置，支持不同门店差异化定价、时效性价格（`effective_from` / `effective_to`）。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `store_id` | UUID | 门店 ID，外键 `store.id` |
| `product_id` | UUID | 商品 ID，外键 `product.id` |
| `sku_id` | UUID | SKU ID，外键 `product_sku.id` |
| `sale_price` | numeric(18,2) | 门店实际售价 |
| `list_price` | numeric(18,2) / null | 划线价 / 参考价 |
| `fund_usage_type` | varchar(32) / null | 门店 SKU 级资金限制（空则继承） |
| `is_sale_enabled` | bool | 门店内该 SKU 是否可销售 |
| `is_visible` | bool | 门店内该 SKU 是否可见 |
| `is_default` | bool | 是否门店默认销售 SKU |
| `effective_from` | timestamptz / null | 价格生效开始时间 |
| `effective_to` | timestamptz / null | 价格生效结束时间 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

约束：`uq_store_product_sku_store_id_sku_id`（同一门店内同一 SKU 只允许一条记录）

---

### 1.6 `sku_inventory_mapping` — SKU 库存扣减映射表

用途：当 SKU 的 `inventory_mode` 为 `MAPPING` 时，通过此表配置销售时应扣减哪个库存商品（或库存 SKU）及扣减数量。支持一对多映射（例如一杯鸡尾酒由多种基酒组合扣减）。

关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `sku_id` | UUID | 销售 SKU ID，外键 `product_sku.id` |
| `inventory_product_id` | UUID / null | 扣减目标库存商品 ID |
| `inventory_sku_id` | UUID / null | 扣减目标库存 SKU ID |
| `deduct_quantity` | numeric(18,4) | 扣减数量 |
| `deduct_unit` | varchar(32) | 扣减单位 |
| `sort_order` | int | 排列顺序 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 最近更新时间 |

---

## 2. 本次新增接口

所有接口均挂载在 `/api/v1` 前缀下，遵循[接口返回规范](./api-convention.md)。

权限要求：

- **只读**接口需要 `product.read` 或 `product.category.read` 权限
- **写操作**接口需要 `product.manage` 或 `product.category.manage` 权限

---

## 3. 动态属性化补充（2026-03-17）

在基础商品中心之上，新增“商品属性驱动 SKU”能力。

### 3.1 新增表

新增 5 张表：

- `product_attribute`
- `product_attribute_value`
- `product_attribute_assignment`
- `product_attribute_assignment_value`
- `product_sku_attribute_value`

作用：

- 定义属性与属性值
- 绑定商品可参与 SKU 组合的属性
- 绑定商品在每个属性下允许的值
- 记录 SKU 由哪些属性值组合生成

### 3.2 新增接口

新增接口组：

- `GET/POST/PATCH /api/v1/product-attributes`
- `GET/POST /api/v1/product-attributes/{attribute_id}/values`
- `PATCH /api/v1/product-attribute-values/{attribute_value_id}`
- `GET/POST/PATCH /api/v1/products/{product_id}/attributes`
- `POST /api/v1/products/{product_id}/attributes/{assignment_id}/values`
- `DELETE /api/v1/products/{product_id}/attributes/{assignment_id}/values/{assignment_value_id}`
- `POST /api/v1/products/{product_id}/skus/generate`
- `GET /api/v1/skus/{sku_id}`

### 3.3 SKU 生成规则

- 商品绑定属性和值后，通过 `POST /products/{product_id}/skus/generate` 自动生成 SKU
- SKU 编码规则：`{product_code}-{seq}`
- SKU 名称规则：按属性排序拼接值名称，例如 `大杯-红色`
- 已不再属于目标组合的旧 SKU 自动停用
- 同一商品仅保留一个默认 SKU

### 3.4 兼容说明

- 无属性商品仍允许手工创建单 SKU
- 已绑定属性的商品禁止手工创建任意 SKU，返回 `PRODUCT_SKU_MANAGED_BY_ATTRIBUTES`

更多设计说明见：

- [product-center-attribute-sku.md](./product-center-attribute-sku.md)

### 3.5 前端改造重点

商品中心前端需要同步调整为“属性驱动 SKU”模式：

- 商品编辑页从“手工维护 SKU 列表”改为“先配置属性和值，再生成 SKU”
- 已绑定属性的商品隐藏手工新增 SKU 入口
- SKU 列表新增“属性值组合”列，优先使用接口返回的 `attribute_values`
- 商品详情页建议拆分为：
  - 基础信息
  - 属性配置
  - SKU 生成结果
  - SKU 业务规则编辑
- 重新生成 SKU 时，前端应明确提示：
  - 会新增哪些 SKU
  - 会停用哪些旧 SKU
  - 已存在组合会复用原 SKU

建议前端联调时优先接通以下接口：

- `GET /api/v1/products/{product_id}/attributes`
- `POST /api/v1/products/{product_id}/attributes`
- `POST /api/v1/products/{product_id}/skus/generate`
- `GET /api/v1/products/{product_id}/skus`
- `GET /api/v1/skus/{sku_id}`

---

### 2.1 商品分类接口

#### `GET /api/v1/product-categories/`

**用途**：获取全部商品分类列表（含已停用、不含已逻辑删除）。

**权限**：`product.category.read`

**返回**：`list[ProductCategoryPublic]`

---

#### `POST /api/v1/product-categories/`

**用途**：创建商品分类。`code` 全局唯一，重复时返回 `409 PRODUCT_CATEGORY_CODE_EXISTS`。

**权限**：`product.category.manage`

**请求体**（示例）：
```json
{
  "code": "CAT-001",
  "name": "烈酒",
  "level": 1,
  "sort_order": 0,
  "is_active": true
}
```

**返回**：`201 ProductCategoryPublic`

---

#### `PATCH /api/v1/product-categories/{category_id}`

**用途**：更新商品分类信息（部分更新）。如修改 `code`，会检查新编码是否重复。

**权限**：`product.category.manage`

**返回**：`200 ProductCategoryPublic`

---

#### `POST /api/v1/product-categories/{category_id}/disable`

**用途**：停用指定商品分类，将 `is_active` 设为 `false`。不物理删除，不影响该分类下的商品。

**权限**：`product.category.manage`

**返回**：`200 ProductCategoryPublic`

---

#### `DELETE /api/v1/product-categories/{category_id}`

**用途**：逻辑删除商品分类。满足以下条件才允许删除：

- 该分类下不存在子分类（否则返回 `409 PRODUCT_CATEGORY_HAS_CHILDREN`）
- 该分类下不存在商品（否则返回 `409 PRODUCT_CATEGORY_HAS_PRODUCTS`）

**权限**：`product.category.manage`

**返回**：`200 data=null`

---

### 2.2 商品接口

#### `GET /api/v1/products/`

**用途**：获取商品列表，支持按分类（`category_id`）和启用状态（`is_active`）过滤，不返回已逻辑删除的商品。

**权限**：`product.read`

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `category_id` | UUID（可选） | 按分类筛选 |
| `is_active` | bool（可选） | 按启用状态筛选 |

**返回**：`list[ProductPublic]`

---

#### `POST /api/v1/products/`

**用途**：创建商品。`code` 全局唯一，重复时返回 `409 PRODUCT_CODE_EXISTS`。

**权限**：`product.manage`

**请求体**（最小示例）：
```json
{
  "code": "PRD-001",
  "name": "轩尼诗XO",
  "category_id": "<category_uuid>",
  "product_type": "NORMAL",
  "unit": "瓶"
}
```

**返回**：`201 ProductPublic`

---

#### `GET /api/v1/products/{product_id}`

**用途**：获取单个商品详情。已逻辑删除的商品返回 `404 PRODUCT_NOT_FOUND`。

**权限**：`product.read`

**返回**：`200 ProductPublic`

---

#### `PATCH /api/v1/products/{product_id}`

**用途**：更新商品信息（部分更新）。如修改 `code`，会检查新编码是否重复。

**权限**：`product.manage`

**返回**：`200 ProductPublic`

---

#### `POST /api/v1/products/{product_id}/disable`

**用途**：停用指定商品，将 `is_active` 设为 `false`。不影响已存在的门店配置和历史订单。

**权限**：`product.manage`

**返回**：`200 ProductPublic`

---

#### `DELETE /api/v1/products/{product_id}`

**用途**：逻辑删除商品（`is_deleted=true`，`is_active=false`）。删除后该商品在查询接口中不再返回。

**权限**：`product.manage`

**返回**：`200 data=null`

---

### 2.3 商品 SKU 接口

#### `GET /api/v1/products/{product_id}/skus`

**用途**：获取指定商品下的全部 SKU 列表（不含已逻辑删除的 SKU）。

**权限**：`product.read`

**返回**：`list[ProductSkuPublic]`

---

#### `POST /api/v1/products/{product_id}/skus`

**用途**：为指定商品创建 SKU。`code` 全局唯一，重复时返回 `409 PRODUCT_SKU_CODE_EXISTS`。

**权限**：`product.manage`

**请求体**（示例）：
```json
{
  "product_id": "<product_uuid>",
  "code": "SKU-001",
  "name": "750ml 单瓶",
  "spec_text": "750ml",
  "is_default": true,
  "inventory_mode": "DIRECT"
}
```

**返回**：`201 ProductSkuPublic`

---

#### `PATCH /api/v1/skus/{sku_id}`

**用途**：更新 SKU 信息（部分更新）。如修改 `code`，会检查新编码是否重复。

**权限**：`product.manage`

**返回**：`200 ProductSkuPublic`

---

#### `POST /api/v1/skus/{sku_id}/disable`

**用途**：停用指定 SKU，将 `is_active` 设为 `false`。

**权限**：`product.manage`

**返回**：`200 ProductSkuPublic`

---

#### `DELETE /api/v1/skus/{sku_id}`

**用途**：逻辑删除指定 SKU（`is_deleted=true`，`is_active=false`）。

**权限**：`product.manage`

**返回**：`200 data=null`

---

### 2.4 SKU 库存扣减映射接口

适用场景：当 SKU 的 `inventory_mode` 为 `MAPPING` 时，通过此组接口管理该 SKU 销售时应扣减的库存目标及数量。

#### `GET /api/v1/skus/{sku_id}/inventory-mappings`

**用途**：获取指定 SKU 的全部库存扣减映射列表。

**权限**：`product.read`

**返回**：`list[SkuInventoryMappingPublic]`

---

#### `POST /api/v1/skus/{sku_id}/inventory-mappings`

**用途**：为指定 SKU 新增一条库存扣减映射规则。

**权限**：`product.manage`

**请求体**（示例）：
```json
{
  "sku_id": "<sku_uuid>",
  "inventory_sku_id": "<inventory_sku_uuid>",
  "deduct_quantity": "1.00",
  "deduct_unit": "瓶",
  "sort_order": 0
}
```

**返回**：`201 SkuInventoryMappingPublic`

---

#### `PATCH /api/v1/skus/{sku_id}/inventory-mappings/{mapping_id}`

**用途**：更新指定扣减映射规则（部分更新），例如调整扣减数量或目标库存 SKU。

**权限**：`product.manage`

**返回**：`200 SkuInventoryMappingPublic`

---

#### `DELETE /api/v1/skus/{sku_id}/inventory-mappings/{mapping_id}`

**用途**：删除指定扣减映射规则（物理删除）。

**权限**：`product.manage`

**返回**：`200 data=null`

---

### 2.5 门店商品配置接口

#### `GET /api/v1/stores/{store_id}/products`

**用途**：获取指定门店已配置的商品列表，包含启用/可见状态和排序。

**权限**：`product.read`

**返回**：`list[StoreProductPublic]`

---

#### `POST /api/v1/stores/{store_id}/products`

**用途**：为指定门店配置一个商品（上架）。同一门店同一商品只允许配置一次，重复时返回 `409 STORE_PRODUCT_EXISTS`。

**权限**：`product.manage`

**请求体**（示例）：
```json
{
  "store_id": "<store_uuid>",
  "product_id": "<product_uuid>",
  "is_enabled": true,
  "is_visible": true,
  "sort_order": 1
}
```

**返回**：`201 StoreProductPublic`

---

#### `PATCH /api/v1/stores/{store_id}/products/{store_product_id}`

**用途**：更新门店商品配置（部分更新），例如调整可见性、排序。

**权限**：`product.manage`

**返回**：`200 StoreProductPublic`

---

### 2.6 门店 SKU 销售配置接口

#### `GET /api/v1/stores/{store_id}/skus`

**用途**：获取指定门店已配置的 SKU 销售配置列表。支持按商品（`product_id`）过滤。

**权限**：`product.read`

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `product_id` | UUID（可选） | 按商品筛选 |

**返回**：`list[StoreProductSkuPublic]`

---

#### `POST /api/v1/stores/{store_id}/skus`

**用途**：为指定门店配置一个 SKU 的销售价格及相关信息。同一门店同一 SKU 只允许一条记录，重复时返回 `409 STORE_PRODUCT_SKU_EXISTS`。

**权限**：`product.manage`

**请求体**（示例）：
```json
{
  "store_id": "<store_uuid>",
  "product_id": "<product_uuid>",
  "sku_id": "<sku_uuid>",
  "sale_price": "388.00",
  "list_price": "488.00",
  "is_sale_enabled": true,
  "is_visible": true
}
```

**返回**：`201 StoreProductSkuPublic`

---

#### `PATCH /api/v1/stores/{store_id}/skus/{store_product_sku_id}`

**用途**：更新门店 SKU 销售配置（部分更新），例如调整售价、有效期、是否可见。

**权限**：`product.manage`

**返回**：`200 StoreProductSkuPublic`

---

## 3. 新增权限点

本次同步向 `DEFAULT_PERMISSION_DEFS`（`app/core/db.py`）注册了以下 4 个权限点，初始化时自动授予 `admin` 角色：

| 权限码 | 说明 |
|--------|------|
| `product.category.read` | 查看商品分类 |
| `product.category.manage` | 管理商品分类（创建、编辑、停用、删除） |
| `product.read` | 查看商品、SKU 及门店配置 |
| `product.manage` | 管理商品、SKU 及门店配置（创建、编辑、停用、删除） |

---

## 4. 业务码速查

| 业务码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `PRODUCT_CATEGORY_NOT_FOUND` | 404 | 商品分类不存在 |
| `PRODUCT_CATEGORY_CODE_EXISTS` | 409 | 分类编码已存在 |
| `PRODUCT_CATEGORY_HAS_CHILDREN` | 409 | 分类下存在子分类，不可删除 |
| `PRODUCT_CATEGORY_HAS_PRODUCTS` | 409 | 分类下存在商品，不可删除 |
| `PRODUCT_NOT_FOUND` | 404 | 商品不存在 |
| `PRODUCT_CODE_EXISTS` | 409 | 商品编码已存在 |
| `PRODUCT_SKU_NOT_FOUND` | 404 | SKU 不存在 |
| `PRODUCT_SKU_CODE_EXISTS` | 409 | SKU 编码已存在 |
| `SKU_INVENTORY_MAPPING_NOT_FOUND` | 404 | 库存扣减映射不存在 |
| `STORE_PRODUCT_NOT_FOUND` | 404 | 门店商品配置不存在 |
| `STORE_PRODUCT_EXISTS` | 409 | 该商品已在当前门店配置 |
| `STORE_PRODUCT_SKU_NOT_FOUND` | 404 | 门店 SKU 销售配置不存在 |
| `STORE_PRODUCT_SKU_EXISTS` | 409 | 该 SKU 已在当前门店配置 |

---

## 5. 接口汇总

共新增 **21 个接口**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/product-categories/` | 获取商品分类列表 |
| POST | `/api/v1/product-categories/` | 创建商品分类 |
| PATCH | `/api/v1/product-categories/{category_id}` | 更新商品分类 |
| POST | `/api/v1/product-categories/{category_id}/disable` | 停用商品分类 |
| DELETE | `/api/v1/product-categories/{category_id}` | 逻辑删除商品分类 |
| GET | `/api/v1/products/` | 获取商品列表 |
| POST | `/api/v1/products/` | 创建商品 |
| GET | `/api/v1/products/{product_id}` | 获取商品详情 |
| PATCH | `/api/v1/products/{product_id}` | 更新商品 |
| POST | `/api/v1/products/{product_id}/disable` | 停用商品 |
| DELETE | `/api/v1/products/{product_id}` | 逻辑删除商品 |
| GET | `/api/v1/products/{product_id}/skus` | 获取商品 SKU 列表 |
| POST | `/api/v1/products/{product_id}/skus` | 创建商品 SKU |
| PATCH | `/api/v1/skus/{sku_id}` | 更新 SKU |
| POST | `/api/v1/skus/{sku_id}/disable` | 停用 SKU |
| DELETE | `/api/v1/skus/{sku_id}` | 逻辑删除 SKU |
| GET | `/api/v1/skus/{sku_id}/inventory-mappings` | 获取 SKU 库存扣减映射列表 |
| POST | `/api/v1/skus/{sku_id}/inventory-mappings` | 创建 SKU 库存扣减映射 |
| PATCH | `/api/v1/skus/{sku_id}/inventory-mappings/{mapping_id}` | 更新 SKU 库存扣减映射 |
| DELETE | `/api/v1/skus/{sku_id}/inventory-mappings/{mapping_id}` | 删除 SKU 库存扣减映射 |
| GET | `/api/v1/stores/{store_id}/products` | 获取门店商品配置列表 |
| POST | `/api/v1/stores/{store_id}/products` | 创建门店商品配置 |
| PATCH | `/api/v1/stores/{store_id}/products/{store_product_id}` | 更新门店商品配置 |
| GET | `/api/v1/stores/{store_id}/skus` | 获取门店 SKU 销售配置列表 |
| POST | `/api/v1/stores/{store_id}/skus` | 创建门店 SKU 销售配置 |
| PATCH | `/api/v1/stores/{store_id}/skus/{store_product_sku_id}` | 更新门店 SKU 销售配置 |
