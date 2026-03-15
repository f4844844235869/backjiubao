# 第三阶段：组织与权限骨架

本文档说明当前“组织与权限骨架”阶段已经落下的内容。

## 1. 已完成范围

### 1.1 门店

已完成：

- `store` 表
- 门店查询接口
- 门店创建接口

接口：

- `GET /api/v1/stores/`
- `POST /api/v1/stores/`

### 1.2 组织树

已完成：

- `org_node` 表
- 邻接表 + 物化路径基础结构
- 组织节点查询接口
- 组织节点创建接口

接口：

- `GET /api/v1/org/nodes`
- `POST /api/v1/org/nodes`

### 1.3 用户组织绑定

已完成：

- `user_org_binding` 表
- 用户组织绑定查询接口
- 用户组织绑定创建接口
- 主归属绑定时自动回写用户 `primary_store_id`、`primary_department_id`

接口：

- `GET /api/v1/org/bindings`
- `POST /api/v1/org/bindings`

### 1.4 角色权限

已完成：

- 角色表
- 权限表
- 用户角色关联
- 角色权限关联
- 用户数据范围关联
- 默认权限种子初始化
- 管理员角色自动同步默认权限

接口：

- `GET /api/v1/iam/roles`
- `POST /api/v1/iam/roles`
- `GET /api/v1/iam/permissions`
- `POST /api/v1/iam/permissions`
- `PUT /api/v1/iam/roles/{role_id}/permissions`
- `PUT /api/v1/iam/users/{user_id}/roles`
- `PUT /api/v1/iam/users/{user_id}/data-scopes`

### 1.5 数据范围

当前已支持：

- `ALL`
- `STORE`
- `DEPARTMENT`
- `SELF`

当前状态：

- 已有数据结构
- 已有分配接口
- 已在认证依赖中提供统一校验入口
- 已可挂到具体业务接口依赖

## 2. 已完成迁移

当前阶段新增迁移：

- [20260315_org_permission_skeleton.py](/Users/yimo/Desktop/codex/full-stack-fastapi-template/backend/app/alembic/versions/20260315_org_permission_skeleton.py)

## 3. 已完成验证

已验证：

- 管理员登录成功
- 创建门店成功
- 创建组织节点成功
- 创建角色成功
- 获取权限列表成功
- 给用户分配角色成功
- 给用户分配数据范围成功

同时已经补入 `pytest` 自动化测试。

## 4. 当前未完成部分

这一阶段还没有做深的内容：

- 组织树移动、重排、停用传播
- 组织节点删除约束
- 用户多岗位、多门店复杂场景
- 基于组织树子树的自动数据范围展开
- 角色权限页面级或按钮级细粒度控制
- 审计日志

## 5. 下一步建议

建议后续直接进入：

1. `member` 模块
2. `wallet` 模块
3. `pos/order` 模块

同时把 `store_id / org_node_id / created_by` 接到业务表和查询过滤中。
