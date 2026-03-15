# `/api/v1/auth/me` 返回字段说明

本文档用于说明当前接口 `GET /api/v1/auth/me` 的返回字段含义，重点面向工作台、顶部用户信息区、门店切换区、权限控制等前端展示场景。

## 1. 接口用途

`/api/v1/auth/me` 用于返回当前登录用户的：

- 基础身份信息
- 当前门店上下文
- 主归属信息
- 角色与权限
- 数据范围
- 归属门店列表
- 可切换门店列表

前端在登录成功后，通常应立即调用一次该接口。

切换门店后，也建议重新调用一次该接口，刷新页面上下文。

---

## 2. 返回结构示例

```json
{
  "code": "SUCCESS",
  "message": "获取当前用户成功",
  "data": {
    "id": "用户ID",
    "user_type": "EMPLOYEE",
    "username": "xinghe.manager",
    "email": null,
    "is_active": true,
    "is_superuser": false,
    "full_name": "林嘉豪",
    "nickname": "星河店长",
    "mobile": "13900001002",
    "status": "ACTIVE",
    "primary_store_id": "主门店ID",
    "primary_department_id": "主组织ID",
    "primary_store_name": "星河店",
    "primary_department_name": "店务中心",
    "last_login_at": "2026-03-15T01:00:00Z",
    "created_at": "2026-03-14T20:00:00Z",
    "updated_at": "2026-03-15T01:00:00Z",
    "current_store_id": "当前门店ID",
    "current_store_name": "星河店",
    "current_org_node_id": "当前组织ID",
    "current_org_node_name": "店务中心",
    "roles": ["store_manager"],
    "role_names": ["店长"],
    "permissions": ["employee.read", "org.store.read"],
    "permission_names": ["查看员工", "查看门店"],
    "data_scopes": [
      {
        "scope_type": "STORE",
        "store_id": "门店ID",
        "org_node_id": null,
        "scope_label": "门店：星河店"
      }
    ],
    "data_scope_labels": ["门店：星河店"],
    "store_memberships": [
      {
        "store_id": "门店ID",
        "store_name": "星河店",
        "org_node_id": "组织ID",
        "org_node_name": "店务中心",
        "position_name": "店长",
        "is_primary": true,
        "is_current": true
      }
    ],
    "accessible_stores": [
      {
        "store_id": "门店ID",
        "store_name": "星河店",
        "is_current": true
      }
    ]
  },
  "trace_id": "请求追踪ID"
}
```

---

## 3. 顶层字段

### `code`

- 含义：业务状态码
- 正常值：`SUCCESS`
- 用途：前端统一判断请求是否成功

### `message`

- 含义：本次请求的中文提示
- 示例：`获取当前用户成功`
- 用途：调试、日志提示、接口异常提示

### `data`

- 含义：当前用户上下文数据主体
- 用途：工作台、权限控制、门店切换、用户展示

### `trace_id`

- 含义：本次请求的追踪 ID
- 用途：问题排查、日志检索、联调定位

---

## 4. `data` 字段说明

### 4.1 基础身份信息

#### `id`

- 含义：当前用户 ID
- 用途：前端缓存当前用户标识、查询自己的相关数据

#### `user_type`

- 含义：用户类型
- 常见值：
  - `EMPLOYEE`：员工用户
  - `MINI_APP_MEMBER`：小程序用户
- 用途：区分后台员工和小程序用户

#### `username`

- 含义：登录账号
- 用途：登录信息展示

#### `email`

- 含义：邮箱
- 当前说明：国内场景下通常不是主展示字段，可选

#### `full_name`

- 含义：真实姓名
- 用途：顶部用户卡片、员工信息展示

#### `nickname`

- 含义：昵称
- 用途：工作台欢迎语、顶部用户展示

#### `mobile`

- 含义：手机号
- 用途：用户信息展示、绑定关系展示

#### `is_active`

- 含义：账号是否启用
- 用途：判断账号是否可正常登录使用

#### `status`

- 含义：账号状态
- 常见值：
  - `ACTIVE`
  - `LEFT`
  - `DISABLED`
- 用途：状态标签展示

#### `is_superuser`

- 含义：是否系统超级管理员
- 用途：前端可用于决定是否显示系统级入口

---

### 4.2 时间字段

#### `last_login_at`

- 含义：最近登录时间
- 用途：工作台顶部或个人中心展示

#### `created_at`

- 含义：账号创建时间

#### `updated_at`

- 含义：账号更新时间

---

### 4.3 主归属信息

#### `primary_store_id`

- 含义：主归属门店 ID
- 说明：这是用户默认归属的门店

#### `primary_store_name`

- 含义：主归属门店名称
- 用途：直接展示在工作台，无需前端自行查表

#### `primary_department_id`

- 含义：主归属组织节点 ID

#### `primary_department_name`

- 含义：主归属组织节点名称
- 用途：展示用户默认所属部门

说明：

- 主归属表示“这个用户默认属于哪里”
- 不一定等于当前正在查看的门店

---

### 4.4 当前上下文信息

#### `current_store_id`

- 含义：当前正在使用的门店 ID
- 来源：
  - 当前主门店
  - 或通过 `X-Current-Store-Id` 指定
  - 或通过切店接口切换

#### `current_store_name`

- 含义：当前正在使用的门店名称
- 用途：工作台顶部当前门店显示

#### `current_org_node_id`

- 含义：当前门店上下文下对应的组织节点 ID

#### `current_org_node_name`

- 含义：当前门店上下文下对应的组织节点名称
- 用途：展示当前门店下的组织归属

说明：

- 当前上下文是“现在正在看哪家店”
- 它会随着切店变化

---

### 4.5 角色信息

#### `roles`

- 含义：角色编码列表
- 示例：`["admin"]`、`["store_manager"]`
- 用途：程序判断、日志输出、调试

#### `role_names`

- 含义：角色中文名称列表
- 示例：`["系统管理员"]`、`["店长"]`
- 用途：前端直接展示角色标签

说明：

- 展示时优先使用 `role_names`
- 程序判断时使用 `roles`

---

### 4.6 权限信息

#### `permissions`

- 含义：权限编码列表
- 示例：
  - `employee.read`
  - `employee.create`
  - `org.store.read`
- 用途：前端菜单、按钮、路由权限判断

#### `permission_names`

- 含义：权限中文名称列表
- 示例：
  - `查看员工`
  - `新增员工`
  - `查看门店`
- 用途：前端展示当前权限摘要、调试面板、管理员查看

说明：

- 展示时优先使用 `permission_names`
- 权限判断时使用 `permissions`

---

### 4.7 数据范围信息

#### `data_scopes`

- 含义：当前用户的数据范围明细列表

每项字段：

- `scope_type`：数据范围类型
- `store_id`：门店范围对应的门店 ID
- `org_node_id`：组织范围对应的组织节点 ID
- `scope_label`：中文说明

#### `data_scope_labels`

- 含义：当前用户数据范围的中文说明列表
- 示例：
  - `全部数据`
  - `门店：星河店`
  - `组织：前厅组`

常见 `scope_type`：

- `ALL`：全部数据
- `STORE`：指定门店数据
- `DEPARTMENT`：指定组织数据
- `SELF`：仅本人数据

用途：

- 工作台权限范围说明
- 权限摘要展示
- 管理端调试与核对

---

### 4.8 归属门店信息

#### `store_memberships`

- 含义：当前用户实际归属到哪些门店
- 来源：组织绑定关系
- 用途：展示“我属于哪些门店、在哪个组织、担任什么岗位”

每项字段：

- `store_id`：归属门店 ID
- `store_name`：归属门店名称
- `org_node_id`：归属组织节点 ID
- `org_node_name`：归属组织节点名称
- `position_name`：岗位名称
- `is_primary`：是否主归属门店
- `is_current`：是否当前门店

说明：

- `store_memberships` 表示“归属关系”
- 不等于“全部可访问门店”

---

### 4.9 可切换门店信息

#### `accessible_stores`

- 含义：当前用户可访问、可切换的门店列表
- 用途：门店切换下拉框

每项字段：

- `store_id`：可访问门店 ID
- `store_name`：可访问门店名称
- `is_current`：是否当前门店

说明：

- 普通用户：通常返回其权限范围内可访问的门店
- 超级管理员：返回全部门店

建议：

- 前端切店下拉框应优先使用 `accessible_stores`
- 不要使用 `store_memberships` 作为切店列表来源

---

## 5. 工作台展示建议

### 顶部用户卡片

建议使用：

- `nickname`
- `full_name`
- `username`
- `mobile`
- `role_names`

### 顶部当前门店

建议使用：

- `current_store_name`
- `current_org_node_name`

### 门店切换下拉

建议使用：

- `accessible_stores`

### 我的归属信息

建议使用：

- `store_memberships`

### 权限摘要

建议使用：

- `role_names`
- `permission_names`
- `data_scope_labels`

### 前端权限判断

建议使用：

- `permissions`

---

## 6. 使用建议

### 登录后

调用一次：

- `GET /api/v1/auth/me`

### 切店后

调用：

- `POST /api/v1/auth/current-store/switch`

再重新调用：

- `GET /api/v1/auth/me`

### 使用请求头临时切店时

也建议重新请求：

- `GET /api/v1/auth/me`

请求头示例：

```http
X-Current-Store-Id: 门店ID
```

说明：

- `X-Current-Store-Id` 就是门店表里的 `store.id`

