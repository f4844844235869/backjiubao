# 认证与权限基础说明

本文档说明当前阶段已经完成的认证基础、权限基础、数据范围骨架，以及当前未完成部分。

## 1. 当前已完成能力

### 1.1 用户表基础字段

当前用户模型已包含以下核心字段：

- `username`：登录账号
- `email`：邮箱，可选
- `user_type`：用户类型，当前默认 `EMPLOYEE`
- `hashed_password`：密码哈希
- `is_active`：是否启用
- `is_superuser`：是否为超级管理员
- `full_name`：姓名
- `nickname`：昵称
- `mobile`：手机号
- `status`：账号状态
- `primary_store_id`：主门店 ID
- `primary_department_id`：主部门 ID
- `created_at`：创建时间

说明：

- 当前仍保留 `is_superuser`，用于系统初始化和兜底管理。
- 后续业务权限判断应逐步迁移到角色与权限点，不再长期依赖 `is_superuser`。
- `user_type` 不表示在职、离职状态；员工任职状态由员工档案单独维护。

### 1.2 登录

当前登录接口：

- `POST /api/v1/auth/backend/password-login`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/miniapp/code-login`
- `POST /api/v1/auth/miniapp/bind-phone`
- `GET /api/v1/auth/miniapp/phone-related-employees`

请求体：

```json
{
  "account": "admin@example.com",
  "password": "changethis"
}
```

说明：

- `account` 当前支持账号登录，也兼容邮箱登录。
- B 端当前正式使用 `POST /api/v1/auth/backend/password-login`。
- `POST /api/v1/auth/login` 仅作为兼容旧接口保留。
- 小程序登录当前采用模拟模式，`code + app_id` 相同会命中同一小程序账号。
- 小程序登录成功后，可继续调用 `POST /api/v1/auth/miniapp/bind-phone` 绑定手机号。
- 小程序绑定手机号后，可调用 `GET /api/v1/auth/miniapp/phone-related-employees` 查询同手机号关联到的员工账号列表。
- 小程序侧也支持通过请求头 `X-Current-Store-Id` 或查询参数 `current_store_id` 传入当前门店，仅返回该门店下关联到的员工账号。
- 登录成功后返回 JWT。

### 1.3 预留登录接口

当前已预留但尚未实现：

- `POST /api/v1/auth/backend/mobile-code-login`

说明：

- B 端后续支持“手机号 + 验证码”登录。
- B 端当前已提供本地模拟验证码登录，开发联调阶段固定使用验证码 `123456`。
- 小程序端当前已提供模拟登录链路，会根据 `code + app_id` 生成稳定的模拟 `openid/unionid` 并签发业务 JWT。
- 小程序端当前已提供模拟手机号绑定链路，会写入 `user_phone_binding` 并回填 `user.mobile`。
- 后续接入真实微信能力时，再替换为正式的 `code -> openid/unionid -> 业务 JWT` 链路。
- 后续接入真实短信服务时，再替换为正式的短信验证码校验。

### 1.4 JWT

JWT 当前包含以下声明：

- `sub`：用户 ID
- `roles`：角色编码列表
- `permissions`：权限编码列表
- `exp`：过期时间

说明：

- 当前角色和权限声明用于调用链传递和调试辅助。
- 权限判断仍以数据库实时查询为准，避免令牌长期缓存导致权限变更不生效。

### 1.5 当前用户依赖

当前用户依赖位于：

- [deps.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/api/deps.py)

已提供：

- `get_current_user`
- `get_current_user_profile`
- `require_roles(...)`
- `require_permissions(...)`
- `require_data_scope(...)`

### 1.6 当前用户接口

当前接口：

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/current-store/switch`

返回内容包含：

- 基础用户信息
- 当前门店上下文 `current_store_id`
- 当前组织上下文 `current_org_node_id`
- 角色编码列表
- 权限编码列表
- 数据范围列表

### 1.7 角色与权限基础表

当前已建立：

- `role`
- `permission`
- `user_role`
- `role_permission`
- `user_data_scope`

当前已补充员工相关权限点：

- `employee.read`
- `employee.create`
- `employee.update`
- `employee.leave`
- `employee.bind_org`
- `employee.assign_role`
- `employee.assign_scope`

当前已补充门店与组织维护权限点：

- `org.store.update`
- `org.store.delete`
- `org.node.update`
- `org.node.delete`

当前执行初始化脚本时会创建：

- 管理员角色：`admin`
- 默认超级管理员的 `ALL` 数据范围

推荐执行方式：

```bash
cd backend
uv run python -m app.initial_data
```

### 1.9 当前授权边界规则

当前默认采用“不可越权授权”规则：

- 分配角色时，只能分配其权限集合不超出当前操作者已有权限集合的角色
- 分配角色权限时，只能分配自己当前已经具备的权限点
- 分配用户数据范围时，不能分配超出自己当前数据范围的门店或组织节点
- 查看他人授权结果时，也会叠加数据范围校验，避免跨店查看他人权限

当前组织树数据范围规则：

- `DEPARTMENT` 数据范围默认按组织树向下继承
- 拿到父节点数据范围后，可访问该父节点下的所有子节点
- 继承的是数据可见范围，不自动放大角色权限本身
- 具体能否调用接口，仍以角色权限校验为准

当前多角色、多数据范围规则：

- 多个角色的权限按并集生效
- 多条数据范围按并集生效
- `GET /api/v1/auth/me` 和授权摘要接口返回的是最终生效后的并集结果

当前门店上下文规则：

- 多门店用户可通过请求头 `X-Current-Store-Id` 指定当前门店
- 也兼容查询参数 `current_store_id`
- 不传时，默认返回当前可访问范围内的全部门店数据
- 传入后，会将门店、组织、组织绑定、员工档案、授权摘要等接口收敛到当前门店
- 小程序手机号关联员工接口也会按 `X-Current-Store-Id` / `current_store_id` 收敛到当前门店
- 传入后，员工入职、组织绑定、数据范围分配等写操作也只能作用于当前门店
- 也可通过 `POST /api/v1/auth/current-store/switch` 显式切换当前主门店
- 如果传入的门店不在当前用户可访问范围内，会返回 `DATA_SCOPE_DENIED`

当前新增接口：

- `GET /api/v1/iam/users/{user_id}/authorization-summary`
- `GET /api/v1/employees/{user_id}/employment-records`
- `POST /api/v1/employees/{user_id}/leave`
- `PATCH /api/v1/stores/{store_id}`
- `DELETE /api/v1/stores/{store_id}`
- `PATCH /api/v1/org/nodes/{node_id}`
- `DELETE /api/v1/org/nodes/{node_id}`

返回内容包含：

- 用户基础信息
- 当前角色列表
- 当前生效权限列表
- 当前数据范围列表

### 1.8 员工档案与小程序身份骨架

当前已建立：

- `employee_profile`
- `employee_employment_record`
- `miniapp_account`
- `user_phone_binding`

当前约定：

- 员工都属于统一 `user` 主体，默认 `user_type = EMPLOYEE`
- 员工离职不修改 `user_type`，而是修改员工档案任职状态
- 每次正式入职都会新增一条 `employee_employment_record`
- 员工离职后保留历史任职记录，再次入职按新员工重新入职，不覆盖旧记录
- 员工再次入职时默认不恢复历史角色和数据范围，必须重新授权
- 门店或组织节点正在被在职员工、有效组织/范围使用时不允许删除
- 门店或组织节点若只剩历史引用，则执行软停用，不做物理删除
- 小程序用户未来同样落到统一 `user` 主体，但通过 `miniapp_account` 和 `user_phone_binding` 维护身份来源与手机号绑定
- 小程序用户当前已支持本地模拟手机号绑定，重复绑定同一手机号会幂等返回，绑定他人已占用手机号会返回 `PHONE_ALREADY_BOUND`
- 小程序用户与员工账号当前保持独立主体，不做强制合并；如手机号一致，可通过手机号关联接口查询关联到的员工账号和历史任职状态
- 员工用户创建后会自动补一条员工档案

## 2. 数据范围骨架

当前数据范围支持以下类型：

- `ALL`
- `STORE`
- `DEPARTMENT`
- `SELF`

当前能力：

- 已有统一依赖校验入口
- 可基于 `store_id`、`org_node_id`、`user_id` 做访问校验

当前限制：

- 还没有与具体业务模块全面接入
- 还没有正式的组织树与门店实体表联动
- 还没有复杂的“多门店并集、多部门并集、跨组织继承”规则

## 3. 当前接口范围

目前已接入这一套基础能力的接口：

- `/api/v1/auth/backend/password-login`
- `/api/v1/auth/login`
- `/api/v1/auth/miniapp/code-login`
- `/api/v1/auth/miniapp/bind-phone`
- `/api/v1/auth/miniapp/phone-related-employees`
- `/api/v1/auth/me`
- `/api/v1/employees/{user_id}/profile`
- `/api/v1/users/*`

## 4. 已完成测试

当前已使用 `pytest` 覆盖的重点能力：

- 登录成功
- 登录失败
- 用户名登录
- 无邮箱创建后台用户
- 旧登录别名兼容
- B 端手机号验证码登录占位接口
- B 端手机号验证码登录成功
- B 端手机号验证码错误
- B 端手机号未注册登录
- 小程序 code 首次登录
- 小程序 code 重复登录
- 小程序登录后未绑定手机号
- 小程序登录后已绑定手机号
- 小程序手机号绑定成功
- 小程序重复绑定同一手机号幂等成功
- 小程序绑定已被其他用户占用的手机号
- 小程序通过手机号关联员工账号
- 小程序通过当前门店上下文过滤手机号关联员工
- 获取当前用户
- 创建员工时自动生成员工档案
- 获取员工档案
- 门店级员工新增与权限边界场景
- 登录参数校验失败
- 获取个人信息
- 获取用户列表的权限校验
- 超级管理员获取用户列表
- 创建用户
- 用户名重复冲突
- 用户查看自己
- 用户不存在
- 更新个人信息
- 修改密码
- 删除用户时的权限/数据范围拦截
- CRUD 层按邮箱或账号认证
- bcrypt 密码升级为 argon2

## 5. 下一步建议

建议按这个顺序继续：

1. 将模拟 B 端验证码登录替换为真实短信验证码登录
2. 将模拟小程序登录替换为真实微信 `code` 登录
3. 增加手机号解绑与手机号关联
4. 增加员工档案维护接口
5. 将数据范围校验正式挂到业务查询条件

## 6. 当前注意事项

- `.env` 中超级管理员密码、`SECRET_KEY` 仍是默认值，只适合本地开发
- 现阶段响应规范只覆盖认证和用户接口，其它新增接口必须沿用统一返回工具
- 模板遗留的示例业务接口已不作为当前主线能力继续维护
