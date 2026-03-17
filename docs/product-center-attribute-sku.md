# 商品中心：属性驱动 SKU 设计

版本：V1.0  
阶段：商品中心动态属性化  
依赖模块：商品中心基础版

---

## 1. 目标

在现有商品中心基础上，引入“商品属性 -> 属性值 -> SKU 组合”的主数据能力，用于解决：

- 不同商品可配置不同属性
- 同一商品的 SKU 不再手工散建，而是由属性值组合生成
- 当前只实现商品中心管理能力
- 为后续 POS、库存、业绩、钱包保留稳定的 `sku_id` 入口

本次不包含订单附加项模型，不处理“加冰/加热”这类下单时临时选择。

---

## 2. 核心对象

### 2.1 商品属性 `product_attribute`

属性定义，例如：

- 杯型
- 颜色
- 容量

关键字段：

- `code`
- `name`
- `display_type`
- `sort_order`
- `is_active`

当前仅支持 `SELECT` 类型。

### 2.2 商品属性值 `product_attribute_value`

属性值定义，例如：

- 杯型：大杯 / 小杯
- 颜色：红色 / 黑色
- 容量：330ml / 500ml

### 2.3 商品属性绑定 `product_attribute_assignment`

表示某商品启用了哪些参与 SKU 的属性。

例如：

- 商品 A 绑定“杯型”“颜色”
- 商品 B 绑定“容量”

### 2.4 商品属性可选值 `product_attribute_assignment_value`

表示某商品在某属性下允许哪些值。

例如：

- 商品 A 的“杯型”只允许：大杯、小杯
- 商品 A 的“颜色”只允许：红色、黑色

### 2.5 SKU 属性值组合 `product_sku_attribute_value`

表示一个 SKU 是由哪些属性值组合生成的。

例如：

- SKU1 = 大杯 + 红色
- SKU2 = 大杯 + 黑色
- SKU3 = 小杯 + 红色
- SKU4 = 小杯 + 黑色

---

## 3. SKU 生成规则

### 3.1 生成入口

接口：

- `POST /api/v1/products/{product_id}/skus/generate`

### 3.2 生成逻辑

1. 读取商品已绑定的属性
2. 读取每个属性下允许的启用属性值
3. 按属性值做笛卡尔积生成目标组合
4. 对每个组合：
   - 已存在则复用原 SKU
   - 不存在则创建新 SKU
5. 已不在目标组合内的旧 SKU 标记为停用

### 3.3 编码规则

SKU 编码统一由后端自动生成：

- 格式：`{product_code}-{seq}`
- 示例：`PRD-BEER-001-01`

编码不直接使用属性值文本，避免属性值名称变更导致编码漂移。

### 3.4 名称规则

- `name`：按属性排序拼接属性值名称，例如 `大杯-红色`
- `spec_text`：默认与 `name` 一致，作为冗余展示字段

---

## 4. 默认 SKU 规则

同一商品只允许一个默认 SKU：

- 首次生成时，按属性排序后的第一个组合默认
- 若已有启用中的默认 SKU，则保留原默认
- 默认 SKU 被停用/删除后，自动切换到同商品下第一个可用 SKU

---

## 5. 兼容规则

### 5.1 无属性商品

若商品未绑定任何参与 SKU 的属性：

- 仍允许调用 `POST /products/{product_id}/skus`
- 可创建单个手工 SKU
- 若未传 `code`，后端自动生成编码

### 5.2 已启用属性驱动的商品

若商品已绑定属性：

- 禁止手工调用 `POST /products/{product_id}/skus` 创建任意 SKU
- 必须通过 SKU 生成接口维护

错误码：

- `PRODUCT_SKU_MANAGED_BY_ATTRIBUTES`

---

## 6. 与后续模块的关系

本次不实现订单、库存、业绩模块，但约定如下：

- 未来订单项以 `sku_id` 为主要引用入口
- 未来库存扣减规则仍挂在 SKU 上
- 未来业绩、利润、资金限制仍以 SKU 当前规则为来源
- 历史业务必须保存快照，不能回查当前主数据解释历史

---

## 7. 当前不包含的范围

本次不包含：

- 订单附加选项模型
- 加冰 / 加热 / 少糖这类下单临时选择
- 多选属性
- 文本输入属性
- 订单/库存/业绩快照表

这些能力后续可在当前属性驱动 SKU 基础上继续扩展。

---

## 8. 前端展示与交互调整建议

本次后端能力上线后，商品中心前端不应再把 SKU 当成“纯手工新增行”来维护，而应拆成“属性配置 + SKU 生成结果”两个区域。

### 8.1 商品编辑页建议拆为 4 个区块

1. 基础信息

- 商品编码
- 商品名称
- 分类
- 单位
- 建议零售价
- 商品级规则字段

2. 规格属性配置

- 展示商品已绑定的属性列表
- 每个属性可配置：
  - 是否启用
  - 排序
  - 是否必填
- 每个属性下展示当前商品允许使用的属性值

3. SKU 生成结果

- 点击“生成 SKU”后展示当前组合结果
- 列表建议字段：
  - SKU 编码
  - SKU 名称
  - 规格文本
  - 属性值组合
  - 建议价
  - 是否默认
  - 是否可售
  - 是否启用

4. SKU 业务规则编辑

- 在 SKU 行或详情抽屉中编辑：
  - `suggested_price`
  - `barcode`
  - `fund_usage_type`
  - `inventory_mode`
  - `allow_negative_inventory`
  - `is_commission_enabled`
  - `commission_type`
  - `commission_value`
  - `standard_cost_price`
  - `is_sale_enabled`
  - `is_active`

### 8.2 前端交互流建议

推荐操作顺序：

1. 创建商品
2. 绑定商品属性
3. 选择每个属性允许的属性值
4. 点击“生成 SKU”
5. 在生成后的 SKU 列表中补充价格、条码、库存规则等业务字段

注意：

- 已绑定属性的商品，不应继续显示“手工新增 SKU”按钮
- 无属性商品才允许保留“新增单 SKU”入口
- “生成 SKU”按钮应在属性和值配置完成后显式提供
- 重新生成 SKU 时，前端应提示：
  - 可能新增 SKU
  - 可能停用旧 SKU
  - 已存在组合会复用原 SKU

### 8.3 前端列表与详情展示建议

商品列表页建议继续以商品维度展示，不直接铺平 SKU。

商品详情页建议增加：

- 属性配置区
- SKU 生成摘要
- SKU 列表

SKU 列表中建议新增一列“属性值组合”，例如：

- `杯型: 大杯 / 颜色: 红色`
- `容量: 500ml`

这样前端不必依赖 `spec_text` 做唯一展示，后续即使规格文案调整，也能稳定回显结构化属性。

### 8.4 前端接口适配重点

前端需要新增适配以下接口：

- 属性定义：
  - `GET /api/v1/product-attributes/`
  - `POST /api/v1/product-attributes/`
  - `PATCH /api/v1/product-attributes/{attribute_id}`
- 属性值定义：
  - `GET /api/v1/product-attributes/{attribute_id}/values`
  - `POST /api/v1/product-attributes/{attribute_id}/values`
  - `PATCH /api/v1/product-attribute-values/{attribute_value_id}`
- 商品属性绑定：
  - `GET /api/v1/products/{product_id}/attributes`
  - `POST /api/v1/products/{product_id}/attributes`
  - `PATCH /api/v1/products/{product_id}/attributes/{assignment_id}`
  - `POST /api/v1/products/{product_id}/attributes/{assignment_id}/values`
  - `DELETE /api/v1/products/{product_id}/attributes/{assignment_id}/values/{assignment_value_id}`
- SKU 生成与查询：
  - `POST /api/v1/products/{product_id}/skus/generate`
  - `GET /api/v1/products/{product_id}/skus`
  - `GET /api/v1/skus/{sku_id}`

`GET /api/v1/products/{product_id}/skus` 和 `GET /api/v1/skus/{sku_id}` 现在会返回结构化的 `attribute_values`，前端应优先使用该字段渲染规格组合。
