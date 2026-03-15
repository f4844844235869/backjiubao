# 后台页面、权限与接口对照文档

本文档用于统一后台管理端的页面规划、权限点设计和接口接入方式，作为前端开发、后端联调、测试补充的共同依据。

当前口径：

- 页面按“最小可用后台”设计，先满足员工、门店、组织、权限和小程序关联管理
- 前端开发时默认已知完整权限点集合，再根据当前用户实际权限做显示和拦截
- 后端接口权限校验仍然是最终裁决，前端权限只负责菜单、路由、按钮和交互限制

## 1. 全局约定

### 1.1 当前用户信息来源

前端登录后，优先使用以下接口获取当前用户上下文：

- `POST /api/v1/auth/backend/password-login`
- `POST /api/v1/auth/backend/mobile-code-login`
- `POST /api/v1/auth/miniapp/code-login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/current-store/switch`

`GET /api/v1/auth/me` 当前返回：

- 当前用户基础信息
- `current_store_id`
- `current_org_node_id`
- `roles`
- `permissions`
- `data_scopes`

前端应基于 `permissions` 做：

- 左侧菜单显示与隐藏
- 路由是否允许进入
- 按钮、操作列、批量操作是否显示
- 无权限提示和空态处理

### 1.2 当前门店上下文

多门店用户进入后台后，需要明确“当前正在看哪个门店”。

前端需支持两种方式：

- 页面请求头带 `X-Current-Store-Id`
- 调用 `POST /api/v1/auth/current-store/switch` 切换主门店

前端建议：

- 顶部全局栏固定展示当前门店
- 门店切换后刷新当前页数据
- 所有门店、组织、员工、授权类页面统一透传当前门店上下文

### 1.3 页面权限控制原则

前端建议分三层控制：

1. 菜单权限
   决定页面入口是否可见

2. 路由权限
   决定 URL 是否允许进入

3. 按钮权限
   决定“新增、编辑、删除、授权、离职”等动作是否可操作

建议不要只按“角色名”判断页面权限，统一按权限编码判断。

## 2. 后台页面清单

### 2.1 登录页

页面目标：

- 提供后台登录入口
- 获取并持久化 token
- 登录成功后进入工作台

主要功能：

- 账号密码登录
- 手机号验证码登录入口
- 登录失败提示
- 进入系统后拉取当前用户信息

接口：

- `POST /api/v1/auth/backend/password-login`
- `POST /api/v1/auth/backend/mobile-code-login`
- `GET /api/v1/auth/me`

权限要求：

- 无需业务权限

### 2.2 工作台

页面目标：

- 作为后台首页，展示当前登录状态、当前门店、角色权限摘要和常用入口

主要功能：

- 显示当前用户信息
- 显示当前门店与组织上下文
- 切换当前门店
- 显示当前角色、权限和数据范围
- 快速进入员工、门店、组织、权限等页面

接口：

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/current-store/switch`

权限要求：

- 无单独页面权限，登录后即可进入

### 2.3 用户与员工列表页

页面目标：

- 查看系统用户
- 区分员工用户与普通用户
- 支持从普通用户转成员工

主要功能：

- 分页查看用户列表
- 查看用户详情
- 创建用户
- 更新用户
- 删除用户
- 查看个人信息
- 将普通用户转换成员工

接口：

- `GET /api/v1/users/`
- `POST /api/v1/users/`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `PATCH /api/v1/users/me/password`

权限要求：

- 页面查看：`iam.user.read`
- 创建用户：`iam.user.create`
- 更新用户：`iam.user.update`
- 删除用户：`iam.user.delete`

备注：

- “用户转员工”通过 `PATCH /api/v1/users/{user_id}` 更新 `user_type`
- 如果列表页主要面向人事和后台管理员，建议默认展示 `user_type`、`status`、`primary_store_id`、`primary_department_id`

### 2.4 员工详情页

页面目标：

- 查看单个员工的档案、任职状态、历史任职记录和当前授权状态

主要功能：

- 查看员工档案
- 查看任职记录
- 查看角色和权限摘要
- 查看组织绑定
- 办理离职

接口：

- `GET /api/v1/employees/{user_id}/profile`
- `GET /api/v1/employees/{user_id}/employment-records`
- `GET /api/v1/iam/users/{user_id}/authorization-summary`
- `GET /api/v1/org/bindings?user_id={user_id}`
- `POST /api/v1/employees/{user_id}/leave`

权限要求：

- 页面查看：`employee.read`
- 授权摘要查看：`iam.user.read`
- 查看组织绑定：`org.binding.read`
- 办理离职：`employee.leave`

备注：

- 如果员工已离职，页面应明确展示 `employment_status = LEFT`
- 再次入职按新员工处理，不自动恢复历史权限

### 2.5 员工入职与调岗页

页面目标：

- 处理员工入职、岗位调整、主组织调整、初始授权

主要功能：

- 员工入职
- 设置主组织
- 设置岗位名称
- 初始角色分配
- 初始数据范围分配
- 更新组织绑定
- 修改岗位名称
- 切换主组织

接口：

- `POST /api/v1/employees/onboard`
- `POST /api/v1/org/bindings`
- `PATCH /api/v1/org/bindings/{binding_id}`
- `GET /api/v1/org/bindings?user_id={user_id}`
- `GET /api/v1/employees/{user_id}/employment-records`

权限要求：

- 员工入职：`employee.create`
- 绑定组织：`employee.bind_org`、`org.binding.create`
- 岗位调整/组织绑定更新：`employee.update`、`org.binding.update`
- 分配角色：`employee.assign_role`、`iam.user.assign_role`
- 分配数据范围：`employee.assign_scope`、`iam.user.assign_scope`

备注：

- 岗位名称当前挂在 `user_org_binding.position_name`
- 主组织切换会联动更新 `primary_store_id` 和 `primary_department_id`

### 2.6 门店管理页

页面目标：

- 管理门店基础信息
- 明确门店当前状态
- 处理门店删除与软停用边界

主要功能：

- 查看门店列表
- 创建门店
- 更新门店编码、名称、状态
- 删除门店
- 区分物理删除与软停用结果

接口：

- `GET /api/v1/stores/`
- `POST /api/v1/stores/`
- `PATCH /api/v1/stores/{store_id}`
- `DELETE /api/v1/stores/{store_id}`

权限要求：

- 页面查看：`org.store.read`
- 创建门店：`org.store.create`
- 更新门店：`org.store.update`
- 删除门店：`org.store.delete`

备注：

- 删除规则：
  - 在用门店：返回 `409 STORE_IN_USE`
  - 只有历史引用：返回成功并将状态改为 `DISABLED`
  - 无引用：物理删除

### 2.7 组织管理页

页面目标：

- 管理组织节点与用户组织绑定
- 支持基础组织维护和删除边界控制

主要功能：

- 查看组织节点列表
- 创建组织节点
- 更新组织名称、排序、启停
- 删除组织节点
- 查看用户组织绑定
- 创建用户组织绑定
- 更新用户组织绑定

接口：

- `GET /api/v1/org/nodes`
- `POST /api/v1/org/nodes`
- `PATCH /api/v1/org/nodes/{node_id}`
- `DELETE /api/v1/org/nodes/{node_id}`
- `GET /api/v1/org/bindings`
- `POST /api/v1/org/bindings`
- `PATCH /api/v1/org/bindings/{binding_id}`

权限要求：

- 页面查看：`org.node.read`
- 创建组织：`org.node.create`
- 更新组织：`org.node.update`
- 删除组织：`org.node.delete`
- 查看组织绑定：`org.binding.read`
- 创建组织绑定：`org.binding.create`
- 更新组织绑定：`org.binding.update`

备注：

- 当前组织节点更新只支持：
  - `name`
  - `sort_order`
  - `is_active`
- 当前不支持改父节点，不支持跨门店迁移
- 删除规则：
  - 在用组织：返回 `409 ORG_NODE_IN_USE`
  - 存在子节点：返回 `409 ORG_NODE_IN_USE`
  - 只有历史引用：成功并置 `is_active = false`
  - 无引用无子节点：物理删除

### 2.8 角色权限管理页

页面目标：

- 管理角色、权限、角色授权、用户授权、数据范围授权

主要功能：

- 查看角色列表
- 创建角色
- 更新角色
- 删除角色
- 查看权限列表
- 创建权限
- 给角色分配权限
- 给用户分配角色
- 给用户分配数据范围
- 查看用户授权摘要

接口：

- `GET /api/v1/iam/roles`
- `POST /api/v1/iam/roles`
- `PATCH /api/v1/iam/roles/{role_id}`
- `DELETE /api/v1/iam/roles/{role_id}`
- `GET /api/v1/iam/permissions`
- `POST /api/v1/iam/permissions`
- `PUT /api/v1/iam/roles/{role_id}/permissions`
- `PUT /api/v1/iam/users/{user_id}/roles`
- `PUT /api/v1/iam/users/{user_id}/data-scopes`
- `GET /api/v1/iam/users/{user_id}/authorization-summary`

权限要求：

- 页面查看：`iam.role.read`、`iam.permission.read`
- 创建角色：`iam.role.create`
- 更新角色：`iam.role.update`
- 删除角色：`iam.role.delete`
- 创建权限：`iam.permission.create`
- 分配角色权限：`iam.role.assign_permission`
- 分配用户角色：`iam.user.assign_role`
- 分配用户数据范围：`iam.user.assign_scope`
- 查看授权摘要：`iam.user.read`

备注：

- 前端应明确展示“授权即时生效”
- 当前用户不能越权授权，前端可以先按当前权限做按钮限制，但最终仍以后端校验为准

### 2.9 小程序用户关联页

页面目标：

- 管理小程序登录用户及其手机号关联到的员工关系

主要功能：

- 小程序模拟登录
- 小程序绑定手机号
- 查看手机号关联员工
- 按当前门店过滤关联结果
- 查看关联员工的任职状态

接口：

- `POST /api/v1/auth/miniapp/code-login`
- `POST /api/v1/auth/miniapp/bind-phone`
- `GET /api/v1/auth/miniapp/phone-related-employees`
- `GET /api/v1/auth/me`

权限要求：

- 当前接口主要依赖登录态和 `user_type = MINI_APP_MEMBER`
- 后台查看员工详情仍需对应员工/权限能力

备注：

- 当前小程序账号和员工账号不合并
- 手机号相同只表示可关联，不表示同一个用户主体

## 3. 完整权限点清单

### 3.1 员工模块

- `employee.read`
- `employee.create`
- `employee.update`
- `employee.leave`
- `employee.bind_org`
- `employee.assign_role`
- `employee.assign_scope`

### 3.2 用户与权限模块

- `iam.user.read`
- `iam.user.create`
- `iam.user.update`
- `iam.user.delete`
- `iam.role.read`
- `iam.role.create`
- `iam.role.update`
- `iam.role.delete`
- `iam.permission.read`
- `iam.permission.create`
- `iam.role.assign_permission`
- `iam.user.assign_role`
- `iam.user.assign_scope`

### 3.3 门店与组织模块

- `org.store.read`
- `org.store.create`
- `org.store.update`
- `org.store.delete`
- `org.node.read`
- `org.node.create`
- `org.node.update`
- `org.node.delete`
- `org.binding.read`
- `org.binding.create`
- `org.binding.update`

## 4. 页面与权限映射建议

| 页面 | 页面进入权限 | 关键按钮权限 |
| --- | --- | --- |
| 登录页 | 无 | 无 |
| 工作台 | 登录即可 | 切换门店：登录即可 |
| 用户与员工列表页 | `iam.user.read` | 新增 `iam.user.create`，编辑 `iam.user.update`，删除 `iam.user.delete` |
| 员工详情页 | `employee.read` | 离职 `employee.leave`，查看授权摘要 `iam.user.read` |
| 员工入职与调岗页 | `employee.create` 或 `employee.update` | 绑定组织 `employee.bind_org`/`org.binding.create`，更新绑定 `employee.update`/`org.binding.update`，授权 `employee.assign_role`/`iam.user.assign_role`，范围 `employee.assign_scope`/`iam.user.assign_scope` |
| 门店管理页 | `org.store.read` | 创建 `org.store.create`，更新 `org.store.update`，删除 `org.store.delete` |
| 组织管理页 | `org.node.read` | 创建 `org.node.create`，更新 `org.node.update`，删除 `org.node.delete`，绑定查看 `org.binding.read`，绑定创建 `org.binding.create`，绑定更新 `org.binding.update` |
| 角色权限管理页 | `iam.role.read` + `iam.permission.read` | 创建角色 `iam.role.create`，更新角色 `iam.role.update`，删除角色 `iam.role.delete`，创建权限 `iam.permission.create`，分配角色权限 `iam.role.assign_permission`，分配用户角色 `iam.user.assign_role`，分配数据范围 `iam.user.assign_scope` |
| 小程序用户关联页 | 登录即可 | 依赖小程序用户登录态，后台员工详情操作仍看对应权限 |

## 5. 前端开发建议

### 5.1 菜单建议

建议后台左侧菜单按以下结构组织：

- 工作台
- 用户与员工
- 员工入职与调岗
- 门店管理
- 组织管理
- 角色权限
- 小程序关联

### 5.2 前端状态建议

建议全局状态至少保存：

- `access_token`
- `current_user`
- `current_store_id`
- `roles`
- `permissions`
- `data_scopes`

### 5.3 权限判断建议

建议提供统一工具函数，例如：

- `hasPermission(code: string)`
- `hasAnyPermission(codes: string[])`
- `canAccessStore(storeId: string)`
- `canAccessOrg(orgNodeId: string)`

### 5.4 页面完成标准

一个页面完成，不只是把表单和表格画出来，还需要同时满足：

- 页面入口有权限控制
- 页面内按钮有权限控制
- 调接口时透传当前门店上下文
- 能处理 `403 / 409 / 422` 等典型错误
- 能正确展示统一返回结构中的 `code / message / data / trace_id`

## 6. 当前不在后台一期范围内

以下能力当前不建议作为后台一期页面强依赖：

- 手机号解绑
- 小程序账号解绑与重绑
- 多小程序账号合并
- 组织树改父节点
- 组织节点跨门店迁移
- 更复杂的门店归档与恢复

这些能力可以在后续迭代中再扩展。
