# 商品中心 · 会员钱包 · 收银 · 库存 — 前端页面与接口对照文档

> **范围**：本文档仅覆盖当前 PR（`parallel-lines-product-center`）新增的四个模块：
> **商品中心（product）、会员钱包（wallet）、收银/订单（pos）、库存管理（inventory）**。
>
> 认证、用户、员工、门店、组织、IAM 等已有模块的页面规范见 `docs/admin-console-spec.md`。

---

## 0. 全局约定

- 所有接口的基础路径：`/api/v1`
- 鉴权：所有请求须携带 `Authorization: Bearer <token>`（登录后获得）
- 门店上下文：请求头 `X-Current-Store-Id: <uuid>` 或查询参数 `?current_store_id=<uuid>`；  
  未传时后端使用当前用户的 `primary_store_id`
- 统一响应结构：

  ```json
  { "code": "SUCCESS", "message": "...", "data": {...}, "trace_id": "..." }
  ```

- 权限校验由后端执行，前端基于 `GET /api/v1/auth/me` 返回的 `permissions` 数组决定菜单/按钮可见性

---

## 1. 接口总览

### 1.1 商品中心（`/api/v1/product`）

| 方法 | 路径 | 权限点 | 说明 |
|---|---|---|---|
| GET | `/product/categories` | `product.category.read` | 商品分类列表 |
| POST | `/product/categories` | `product.category.create` | 创建商品分类 |
| PATCH | `/product/categories/{category_id}` | `product.category.update` | 更新商品分类 |
| DELETE | `/product/categories/{category_id}` | `product.category.delete` | 删除商品分类 |
| GET | `/product/products` | `product.product.read` | 商品列表 |
| POST | `/product/products` | `product.product.create` | 创建商品 |
| PATCH | `/product/products/{product_id}` | `product.product.update` | 更新商品 |
| DELETE | `/product/products/{product_id}` | `product.product.delete` | 删除商品 |
| GET | `/product/products/{product_id}/skus` | `product.sku.read` | SKU 列表 |
| POST | `/product/products/{product_id}/skus` | `product.sku.create` | 创建 SKU |
| PATCH | `/product/skus/{sku_id}` | `product.sku.update` | 更新 SKU |
| DELETE | `/product/skus/{sku_id}` | `product.sku.delete` | 删除 SKU |
| GET | `/product/fund-limits` | `product.fund_limit.read` | 资金限制列表 |
| POST | `/product/fund-limits` | `product.fund_limit.create` | 创建资金限制 |
| PATCH | `/product/fund-limits/{fund_limit_id}` | `product.fund_limit.update` | 更新资金限制 |
| DELETE | `/product/fund-limits/{fund_limit_id}` | `product.fund_limit.delete` | 删除资金限制 |
| GET | `/product/gift-templates` | `product.gift_template.read` | 赠送模板列表 |
| POST | `/product/gift-templates` | `product.gift_template.create` | 创建赠送模板 |
| PATCH | `/product/gift-templates/{gift_template_id}` | `product.gift_template.update` | 更新赠送模板 |
| DELETE | `/product/gift-templates/{gift_template_id}` | `product.gift_template.delete` | 删除赠送模板 |

### 1.2 会员钱包（`/api/v1/wallet`）

| 方法 | 路径 | 权限点 | 说明 |
|---|---|---|---|
| GET | `/wallet/members` | `wallet.member.read` | 会员列表 |
| POST | `/wallet/members` | `wallet.member.create` | 创建会员 |
| PATCH | `/wallet/members/{member_id}` | `wallet.member.update` | 更新会员 |
| DELETE | `/wallet/members/{member_id}` | `wallet.member.delete` | 删除会员 |
| GET | `/wallet/members/{member_id}/principal-account` | `wallet.account.read` | 本金账户 |
| GET | `/wallet/members/{member_id}/gift-account` | `wallet.account.read` | 赠金账户 |
| GET | `/wallet/members/{member_id}/transactions` | `wallet.transaction.read` | 钱包流水 |
| GET | `/wallet/recharge-plans` | `wallet.recharge_plan.read` | 充值方案列表 |
| POST | `/wallet/recharge-plans` | `wallet.recharge_plan.create` | 创建充值方案 |
| PATCH | `/wallet/recharge-plans/{plan_id}` | `wallet.recharge_plan.update` | 更新充值方案 |
| DELETE | `/wallet/recharge-plans/{plan_id}` | `wallet.recharge_plan.delete` | 删除充值方案 |
| POST | `/wallet/recharge` | `wallet.recharge.create` | 会员充值 |

### 1.3 收银/订单（`/api/v1/pos`）

| 方法 | 路径 | 权限点 | 说明 |
|---|---|---|---|
| GET | `/pos/orders` | `pos.order.read` | 订单列表 |
| POST | `/pos/orders` | `pos.order.create` | 创建订单 |
| PATCH | `/pos/orders/{order_id}` | `pos.order.update` | 更新订单 |
| DELETE | `/pos/orders/{order_id}` | `pos.order.delete` | 删除订单 |
| GET | `/pos/orders/{order_id}/items` | `pos.order.read` | 订单明细列表 |
| POST | `/pos/orders/{order_id}/items` | `pos.order.create` | 新增订单明细 |
| DELETE | `/pos/orders/{order_id}/items/{item_id}` | `pos.order.delete` | 删除订单明细 |
| GET | `/pos/orders/{order_id}/payments` | `pos.payment.read` | 支付记录列表 |
| POST | `/pos/orders/{order_id}/payments` | `pos.payment.create` | 创建支付记录 |
| GET | `/pos/payments/{payment_id}` | `pos.payment.read` | 支付详情 |
| GET | `/pos/shifts` | `pos.shift.read` | 交接班列表 |
| POST | `/pos/shifts` | `pos.shift.create` | 创建交接班（开班） |
| PATCH | `/pos/shifts/{shift_id}` | `pos.shift.update` | 更新交接班（结班） |

### 1.4 库存管理（`/api/v1/inventory`）

| 方法 | 路径 | 权限点 | 说明 |
|---|---|---|---|
| GET | `/inventory/warehouses` | `inventory.warehouse.read` | 仓库列表 |
| POST | `/inventory/warehouses` | `inventory.warehouse.create` | 创建仓库 |
| PATCH | `/inventory/warehouses/{warehouse_id}` | `inventory.warehouse.update` | 更新仓库 |
| DELETE | `/inventory/warehouses/{warehouse_id}` | `inventory.warehouse.delete` | 删除仓库 |
| GET | `/inventory/warehouses/{warehouse_id}/balances` | `inventory.balance.read` | 库存余额列表 |
| GET | `/inventory/warehouses/{warehouse_id}/transactions` | `inventory.transaction.read` | 库存流水列表 |
| POST | `/inventory/transactions` | `inventory.transaction.create` | 记录库存变动 |
| GET | `/inventory/transfers` | `inventory.transfer.read` | 调拨单列表 |
| POST | `/inventory/transfers` | `inventory.transfer.create` | 创建调拨单 |
| PATCH | `/inventory/transfers/{transfer_id}` | `inventory.transfer.update` | 更新调拨单 |

---

## 2. 前端页面清单与接口调度

### 2.1 商品分类管理页

**功能**：维护当前门店的商品分类，支持层级结构（父分类）。

**主要操作**：列表展示 · 新增 · 编辑名称/排序/启停 · 删除

**接口调度**：

```
进入页面
  └─ GET /product/categories          ← 拉取分类列表（门店上下文自动透传）

点击「新增」→ 填写表单 → 提交
  └─ POST /product/categories
       body: { store_id, parent_id?, name, sort_order, is_active }
     成功后重新拉取列表

点击「编辑」→ 回填表单 → 提交
  └─ PATCH /product/categories/{category_id}
       body: { name?, sort_order?, is_active? }   ← 只传修改字段
     成功后刷新当前行

点击「删除」→ 二次确认 → 提交
  └─ DELETE /product/categories/{category_id}
     409 CATEGORY_NOT_FOUND 时提示不存在
```

**权限点**：查看 `product.category.read` · 新增 `product.category.create` · 编辑 `product.category.update` · 删除 `product.category.delete`

---

### 2.2 商品管理页（含 SKU 管理抽屉）

**功能**：查看、创建、编辑、停用商品，并在详情侧边栏内管理该商品的 SKU 规格。

**主要操作**：分页列表（按分类/状态过滤）· 新增商品 · 编辑 · 停用/启用 · 删除 · 展开 SKU 子列表 · SKU 新增/编辑/删除

**接口调度**：

```
进入页面
  ├─ GET /product/categories           ← 填充「按分类过滤」下拉选项
  └─ GET /product/products             ← 拉取商品列表

点击「新增商品」→ 表单提交
  └─ POST /product/products
       body: { store_id, category_id?, code?, name, unit?, status,
               selling_price, cost_price, net_profit_price?,
               price_display_mode?, description? }
     409 PRODUCT_CODE_EXISTS → 提示编码重复

点击「编辑」→ 提交
  └─ PATCH /product/products/{product_id}   ← 只传修改字段

点击「停用/启用」
  └─ PATCH /product/products/{product_id}
       body: { status: "INACTIVE" | "ACTIVE" }

点击「删除」→ 二次确认
  └─ DELETE /product/products/{product_id}

展开/进入商品详情 → 加载 SKU
  └─ GET /product/products/{product_id}/skus

  新增 SKU
    └─ POST /product/products/{product_id}/skus
         body: { sku_code?, spec_name?, barcode?, price?, cost_price?,
                 net_profit_price?, price_display_mode?, is_active }
       409 SKU_CODE_EXISTS → 提示 SKU 编码重复

  编辑 SKU
    └─ PATCH /product/skus/{sku_id}   ← 只传修改字段

  删除 SKU
    └─ DELETE /product/skus/{sku_id}
```

**权限点**：
- 商品：`product.product.read/create/update/delete`
- SKU：`product.sku.read/create/update/delete`

---

### 2.3 资金限制管理页

**功能**：配置商品在活动中的单笔/累计金额限制规则。

**主要操作**：列表 · 新增 · 编辑 · 删除

**接口调度**：

```
进入页面
  └─ GET /product/fund-limits

新增
  └─ POST /product/fund-limits
       body: { store_id, name, ... }

编辑
  └─ PATCH /product/fund-limits/{fund_limit_id}

删除
  └─ DELETE /product/fund-limits/{fund_limit_id}
```

**权限点**：`product.fund_limit.read/create/update/delete`

---

### 2.4 赠送模板管理页

**功能**：维护促销赠品组合模板（如"买满 100 送 A"的赠品清单），供订单和活动引用。

**主要操作**：列表 · 新增 · 编辑 · 删除

**接口调度**：

```
进入页面
  └─ GET /product/gift-templates

新增
  └─ POST /product/gift-templates
       body: { store_id, name, description?, ... }

编辑
  └─ PATCH /product/gift-templates/{gift_template_id}

删除
  └─ DELETE /product/gift-templates/{gift_template_id}
```

**权限点**：`product.gift_template.read/create/update/delete`

---

### 2.5 仓库管理页

**功能**：管理门店下的物理仓库/库位，每个仓库有唯一编码。

**主要操作**：列表 · 新增 · 编辑名称/描述 · 删除

**接口调度**：

```
进入页面
  └─ GET /inventory/warehouses         ← 门店上下文自动透传

新增
  └─ POST /inventory/warehouses
       body: { store_id, code, name, description? }
     409 WAREHOUSE_CODE_EXISTS → 提示编码重复

编辑
  └─ PATCH /inventory/warehouses/{warehouse_id}

删除
  └─ DELETE /inventory/warehouses/{warehouse_id}
```

**权限点**：`inventory.warehouse.read/create/update/delete`

---

### 2.6 库存余额页

**功能**：查看指定仓库中各 SKU 的当前库存数量（只读视图）。

**主要操作**：选择仓库 · 查看 SKU 余量列表

**接口调度**：

```
进入页面
  └─ GET /inventory/warehouses         ← 加载仓库选择下拉

选择仓库后
  └─ GET /inventory/warehouses/{warehouse_id}/balances
       ← 返回 [{ sku_id, sku_code, spec_name, quantity, ... }]
```

**权限点**：查看仓库列表 `inventory.warehouse.read` · 查看余额 `inventory.balance.read`

备注：修改库存需通过「库存流水」手动录入变动。

---

### 2.7 库存流水页

**功能**：查看指定仓库的全部库存变动记录，支持手动录入入库/出库/盘点操作。

**主要操作**：选择仓库 · 查看流水列表 · 手动录入库存变动

**接口调度**：

```
进入页面
  └─ GET /inventory/warehouses         ← 加载仓库选择下拉

选择仓库后
  └─ GET /inventory/warehouses/{warehouse_id}/transactions
       ← 返回 [{ sku_id, transaction_type, quantity, remark, created_at, ... }]

点击「录入变动」→ 填写表单 → 提交
  └─ POST /inventory/transactions
       body: {
         warehouse_id,
         sku_id,
         transaction_type,   ← "IN" | "OUT" | "ADJUST"
         quantity,
         ref_order_id?,      ← 关联订单 ID（选填）
         operator_id?,
         remark?
       }
     成功后刷新流水列表和余额
```

**权限点**：`inventory.transaction.read` · 录入 `inventory.transaction.create`

---

### 2.8 调拨管理页

**功能**：管理跨仓库的库存调拨单（从一个仓库转移商品到另一个仓库）。

**主要操作**：列表 · 创建调拨单 · 更新状态（确认/完成/取消）

**接口调度**：

```
进入页面
  └─ GET /inventory/transfers          ← 调拨单列表

点击「创建调拨单」
  ├─ GET /inventory/warehouses         ← 选择源仓库/目标仓库
  └─ POST /inventory/transfers
       body: {
         transfer_no,
         from_warehouse_id,
         to_warehouse_id,
         sku_id,
         quantity,
         remark?
       }
     409 TRANSFER_NO_EXISTS → 提示单号重复

更新状态（确认 / 完成 / 取消）
  └─ PATCH /inventory/transfers/{transfer_id}
       body: { status: "CONFIRMED" | "COMPLETED" | "CANCELLED" }
```

**权限点**：`inventory.transfer.read/create/update`

---

### 2.9 收银台页（POS）

**功能**：门店营业员的核心作业界面，完成开单 → 选商品 → 收款全流程。

**主要操作**：新建订单 · 搜索并添加商品/SKU · 删除明细 · 修改订单信息 · 发起支付 · 取消订单

**接口调度**：

```
打开收银台
  └─ GET /product/products             ← 加载商品列表/搜索框数据源

选中商品后加载规格
  └─ GET /product/products/{product_id}/skus

点击「开单」
  └─ POST /pos/orders
       body: {
         order_no,        ← 前端生成或由后端分配
         store_id,
         member_id?,      ← 会员消费时传入
         remark?
       }
     ← 返回 order_id，后续操作均基于此 ID

逐行添加商品明细
  └─ POST /pos/orders/{order_id}/items
       body: { order_id, sku_id, quantity, unit_price? }
     可循环调用，每次加一行

删除某行明细
  └─ DELETE /pos/orders/{order_id}/items/{item_id}

修改订单备注/折扣
  └─ PATCH /pos/orders/{order_id}
       body: { remark?, discount_amount? }

点击「收款」→ 选择支付方式 → 确认
  └─ POST /pos/orders/{order_id}/payments
       body: {
         order_id,
         method,          ← "CASH" | "WECHAT" | "ALIPAY" | "WALLET_PRINCIPAL" | "WALLET_GIFT"
         amount
       }

查看支付结果
  └─ GET /pos/orders/{order_id}/payments
     或
  └─ GET /pos/payments/{payment_id}

取消/作废订单
  └─ DELETE /pos/orders/{order_id}
```

**权限点**：
- 开单/加商品：`pos.order.create`
- 修改订单：`pos.order.update`
- 删除/取消：`pos.order.delete`
- 支付：`pos.payment.create`

备注：

- 会员用钱包支付时，先通过会员管理页查询 `member_id`，传入 `POST /pos/orders` 的 `member_id` 字段
- `method` 为 `WALLET_PRINCIPAL` 或 `WALLET_GIFT` 时后端自动扣减对应账户余额

---

### 2.10 订单列表页

**功能**：查看门店所有历史订单，支持按状态/日期过滤，可展开查看明细和支付记录。

**主要操作**：分页列表 · 过滤 · 展开明细 · 展开支付记录

**接口调度**：

```
进入页面
  └─ GET /pos/orders                   ← 门店上下文自动透传，支持分页

展开某订单的明细
  └─ GET /pos/orders/{order_id}/items

展开某订单的支付记录
  └─ GET /pos/orders/{order_id}/payments
```

**权限点**：`pos.order.read` · `pos.payment.read`

---

### 2.11 交接班管理页

**功能**：记录门店每个营业班次的开班/结班信息，汇总当班销售数据。

**主要操作**：班次列表 · 开班 · 结班（填写汇总数据）

**接口调度**：

```
进入页面
  └─ GET /pos/shifts                   ← 门店上下文自动透传

点击「开班」
  └─ POST /pos/shifts
       body: { store_id, cashier_id, start_cash_amount?, started_at, remark? }

点击「结班」→ 填写收款汇总 → 提交
  └─ PATCH /pos/shifts/{shift_id}
       body: { ended_at, end_cash_amount?, remark? }
```

**权限点**：`pos.shift.read/create/update`

---

### 2.12 会员管理页

**功能**：维护门店会员档案，查看账户余额和充值流水。

**主要操作**：列表（按手机号/姓名搜索）· 新增 · 编辑 · 删除 · 查看本金/赠金账户 · 查看流水 · 发起充值（调用 2.14）

**接口调度**：

```
进入页面
  └─ GET /wallet/members               ← 门店上下文自动透传

新增会员
  └─ POST /wallet/members
       body: { store_id, user_id?, member_no, name?, mobile?, status, level, joined_at? }
     409 MEMBER_NO_EXISTS → 提示编号重复

编辑会员
  └─ PATCH /wallet/members/{member_id}
       body: { name?, mobile?, status?, level?, joined_at? }

删除会员
  └─ DELETE /wallet/members/{member_id}

进入会员详情
  ├─ GET /wallet/members/{member_id}/principal-account   ← 本金余额
  ├─ GET /wallet/members/{member_id}/gift-account        ← 赠金余额
  └─ GET /wallet/members/{member_id}/transactions        ← 充值/消费流水
```

**权限点**：
- 列表/详情：`wallet.member.read`
- 新增：`wallet.member.create`
- 编辑：`wallet.member.update`
- 删除：`wallet.member.delete`
- 账户/流水：`wallet.account.read` · `wallet.transaction.read`

---

### 2.13 充值方案管理页

**功能**：配置充值套餐（充多少本金 → 赠多少赠金），供充值操作选择。

**主要操作**：列表 · 新增 · 编辑 · 删除

**接口调度**：

```
进入页面
  └─ GET /wallet/recharge-plans        ← 门店上下文自动透传

新增方案
  └─ POST /wallet/recharge-plans
       body: { store_id, name, principal_amount, gift_amount, is_active }

编辑方案
  └─ PATCH /wallet/recharge-plans/{plan_id}
       body: { name?, principal_amount?, gift_amount?, is_active? }

删除方案
  └─ DELETE /wallet/recharge-plans/{plan_id}
```

**权限点**：`wallet.recharge_plan.read/create/update/delete`

---

### 2.14 会员充值操作（弹窗/抽屉，嵌入会员详情页）

**功能**：为指定会员选择充值方案并执行充值，同步写入本金账户和赠金账户。

**接口调度**：

```
打开充值弹窗时
  └─ GET /wallet/recharge-plans        ← 展示可选方案列表（过滤 is_active=true）

选择方案 → 确认充值
  └─ POST /wallet/recharge
       body: {
         member_id,
         recharge_plan_id,
         operator_id?,
         remark?
       }
     409 RECHARGE_PLAN_INACTIVE → 提示方案已停用
     404 MEMBER_NOT_FOUND / RECHARGE_PLAN_NOT_FOUND → 提示对应错误

充值成功后刷新账户余额
  ├─ GET /wallet/members/{member_id}/principal-account
  └─ GET /wallet/members/{member_id}/gift-account
```

**权限点**：`wallet.recharge.create`

---

## 3. 权限点汇总

### 3.1 商品中心（product）

| 权限点 | 说明 |
|---|---|
| `product.category.read` | 查看分类列表 |
| `product.category.create` | 创建分类 |
| `product.category.update` | 编辑分类 |
| `product.category.delete` | 删除分类 |
| `product.product.read` | 查看商品列表 |
| `product.product.create` | 创建商品 |
| `product.product.update` | 编辑商品 |
| `product.product.delete` | 删除商品 |
| `product.sku.read` | 查看 SKU |
| `product.sku.create` | 创建 SKU |
| `product.sku.update` | 编辑 SKU |
| `product.sku.delete` | 删除 SKU |
| `product.fund_limit.read` | 查看资金限制 |
| `product.fund_limit.create` | 创建资金限制 |
| `product.fund_limit.update` | 编辑资金限制 |
| `product.fund_limit.delete` | 删除资金限制 |
| `product.gift_template.read` | 查看赠送模板 |
| `product.gift_template.create` | 创建赠送模板 |
| `product.gift_template.update` | 编辑赠送模板 |
| `product.gift_template.delete` | 删除赠送模板 |

### 3.2 收银/订单（pos）

| 权限点 | 说明 |
|---|---|
| `pos.order.read` | 查看订单/明细 |
| `pos.order.create` | 创建订单/添加明细 |
| `pos.order.update` | 修改订单 |
| `pos.order.delete` | 删除订单/明细 |
| `pos.payment.read` | 查看支付记录 |
| `pos.payment.create` | 创建支付记录 |
| `pos.shift.read` | 查看班次 |
| `pos.shift.create` | 开班 |
| `pos.shift.update` | 结班/修改班次 |

### 3.3 库存管理（inventory）

| 权限点 | 说明 |
|---|---|
| `inventory.warehouse.read` | 查看仓库列表 |
| `inventory.warehouse.create` | 创建仓库 |
| `inventory.warehouse.update` | 编辑仓库 |
| `inventory.warehouse.delete` | 删除仓库 |
| `inventory.balance.read` | 查看库存余额 |
| `inventory.transaction.read` | 查看库存流水 |
| `inventory.transaction.create` | 手动录入库存变动 |
| `inventory.transfer.read` | 查看调拨单 |
| `inventory.transfer.create` | 创建调拨单 |
| `inventory.transfer.update` | 更新调拨单状态 |

### 3.4 会员钱包（wallet）

| 权限点 | 说明 |
|---|---|
| `wallet.member.read` | 查看会员 |
| `wallet.member.create` | 创建会员 |
| `wallet.member.update` | 编辑会员 |
| `wallet.member.delete` | 删除会员 |
| `wallet.account.read` | 查看本金/赠金账户 |
| `wallet.transaction.read` | 查看钱包流水 |
| `wallet.recharge_plan.read` | 查看充值方案 |
| `wallet.recharge_plan.create` | 创建充值方案 |
| `wallet.recharge_plan.update` | 编辑充值方案 |
| `wallet.recharge_plan.delete` | 删除充值方案 |
| `wallet.recharge.create` | 执行充值 |

---

## 4. 页面与权限映射

| 页面 | 进入权限 | 关键按钮权限 |
|---|---|---|
| 商品分类管理 | `product.category.read` | 新增 `…create`，编辑 `…update`，删除 `…delete` |
| 商品管理（含 SKU） | `product.product.read` | 新增 `…create`，编辑/停用 `…update`，删除 `…delete`，SKU 操作 `product.sku.*` |
| 资金限制管理 | `product.fund_limit.read` | 新增/编辑/删除 `…create/update/delete` |
| 赠送模板管理 | `product.gift_template.read` | 新增/编辑/删除 `…create/update/delete` |
| 仓库管理 | `inventory.warehouse.read` | 新增/编辑/删除 `…create/update/delete` |
| 库存余额 | `inventory.balance.read` | 无写操作 |
| 库存流水 | `inventory.transaction.read` | 手动录入 `inventory.transaction.create` |
| 调拨管理 | `inventory.transfer.read` | 创建 `…create`，更新状态 `…update` |
| 收银台（POS） | `pos.order.create` | 支付 `pos.payment.create`，删除 `pos.order.delete` |
| 订单列表 | `pos.order.read` | — |
| 交接班管理 | `pos.shift.read` | 开班 `pos.shift.create`，结班 `pos.shift.update` |
| 会员管理 | `wallet.member.read` | 新增/编辑/删除 `…create/update/delete`，账户 `wallet.account.read`，充值 `wallet.recharge.create` |
| 充值方案管理 | `wallet.recharge_plan.read` | 新增/编辑/删除 `…create/update/delete` |

---

## 5. 建议的菜单结构

```
商品中心
  ├─ 商品分类
  ├─ 商品列表（含 SKU）
  ├─ 资金限制
  └─ 赠送模板

库存管理
  ├─ 仓库管理
  ├─ 库存余额
  ├─ 库存流水
  └─ 调拨管理

收银与订单
  ├─ 收银台
  ├─ 订单列表
  └─ 交接班管理

会员中心
  ├─ 会员管理
  └─ 充值方案管理
```

---

## 6. 错误码参考

| 错误码 | HTTP 状态 | 触发场景 |
|---|---|---|
| `CATEGORY_NOT_FOUND` | 404 | 分类 ID 不存在 |
| `PRODUCT_CODE_EXISTS` | 409 | 同门店商品编码重复 |
| `PRODUCT_NOT_FOUND` | 404 | 商品 ID 不存在 |
| `SKU_CODE_EXISTS` | 409 | 同商品 SKU 编码重复 |
| `SKU_NOT_FOUND` | 404 | SKU ID 不存在 |
| `FUND_LIMIT_NOT_FOUND` | 404 | 资金限制 ID 不存在 |
| `GIFT_TEMPLATE_NOT_FOUND` | 404 | 赠送模板 ID 不存在 |
| `WAREHOUSE_CODE_EXISTS` | 409 | 同门店仓库编码重复 |
| `WAREHOUSE_NOT_FOUND` | 404 | 仓库 ID 不存在 |
| `TRANSFER_NO_EXISTS` | 409 | 调拨单编号重复 |
| `TRANSFER_NOT_FOUND` | 404 | 调拨单 ID 不存在 |
| `ORDER_NO_EXISTS` | 409 | 订单编号重复 |
| `ORDER_NOT_FOUND` | 404 | 订单 ID 不存在 |
| `ORDER_ITEM_NOT_FOUND` | 404 | 订单明细 ID 不存在或不属于该订单 |
| `PAYMENT_NOT_FOUND` | 404 | 支付记录 ID 不存在 |
| `SHIFT_NOT_FOUND` | 404 | 班次 ID 不存在 |
| `MEMBER_NO_EXISTS` | 409 | 会员编号重复 |
| `MEMBER_NOT_FOUND` | 404 | 会员 ID 不存在 |
| `ACCOUNT_NOT_FOUND` | 404 | 本金/赠金账户不存在 |
| `RECHARGE_PLAN_NOT_FOUND` | 404 | 充值方案 ID 不存在 |
| `RECHARGE_PLAN_INACTIVE` | 409 | 充值方案已停用 |
