# 接口返回规范

本文档约定酒吧管理系统后端 API 的统一返回格式、HTTP 状态码使用方式、业务码命名方式，以及错误消息口径。

## 1. 统一返回结构

所有接口默认返回以下结构：

```json
{
  "code": "SUCCESS",
  "message": "请求成功",
  "data": {},
  "trace_id": "7b7f1e88-1dbe-4d98-94d0-2d1b0fd9d66d"
}
```

字段说明：

- `code`：业务响应码，供前端和调用方稳定判断。
- `message`：用户可读消息，默认使用中文。
- `data`：业务数据。成功时为对象或列表，失败时通常为 `null`。
- `trace_id`：请求追踪 ID，同时会写入响应头 `X-Trace-Id`。

## 2. 成功返回规范

### 2.1 查询接口

查询类接口使用：

- HTTP 状态码：`200`
- `code`：`SUCCESS`
- `message`：示例 `获取用户成功`、`获取当前用户成功`

示例：

```json
{
  "code": "SUCCESS",
  "message": "获取当前用户成功",
  "data": {
    "id": "509a32da-607e-419c-a68c-61a53876a930",
    "username": "admin@example.com"
  },
  "trace_id": "..."
}
```

### 2.2 创建接口

创建类接口使用：

- HTTP 状态码：`201`
- `code`：`SUCCESS`
- `message`：示例 `创建用户成功`

### 2.3 更新、删除、动作接口

更新、删除、动作类接口使用：

- HTTP 状态码：`200`
- `code`：`SUCCESS`
- `message`：示例 `更新用户成功`、`删除用户成功`、`修改密码成功`

## 3. 分页返回规范

分页接口的 `data` 使用以下结构：

```json
{
  "items": [],
  "total": 0
}
```

字段说明：

- `items`：当前页数据列表
- `total`：总记录数

## 4. 错误返回规范

错误时仍然返回统一外层结构：

```json
{
  "code": "USER_NOT_FOUND",
  "message": "用户不存在",
  "data": null,
  "trace_id": "..."
}
```

### 4.1 参数校验失败

HTTP 状态码：`422`

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数校验失败",
  "data": {
    "errors": [
      {
        "field": "body.password",
        "reason": "Field required"
      }
    ]
  },
  "trace_id": "..."
}
```

### 4.2 常见业务错误码

- `AUTH_INVALID_CREDENTIALS`：账号或密码错误
- `AUTH_INVALID_TOKEN`：登录状态无效或已过期
- `AUTH_PERMISSION_DENIED`：权限不足
- `AUTH_ROLE_DENIED`：缺少角色
- `DATA_SCOPE_DENIED`：数据范围不足
- `USER_NOT_FOUND`：用户不存在
- `USER_EMAIL_EXISTS`：邮箱已存在
- `USER_USERNAME_EXISTS`：登录账号已存在
- `USER_DISABLED`：当前用户已被禁用
- `USER_PASSWORD_INVALID`：当前密码错误
- `USER_PASSWORD_UNCHANGED`：新密码不能与旧密码一致
- `USER_DELETE_SELF_FORBIDDEN`：超级管理员不能删除自己
- `TODO_NOT_IMPLEMENTED`：预留能力暂未实现
- `INTERNAL_SERVER_ERROR`：服务器内部异常

## 5. HTTP 状态码使用约定

- `200 OK`：查询、更新、删除、动作成功
- `201 Created`：创建成功
- `400 Bad Request`：通用业务请求错误，例如账号或密码错误
- `401 Unauthorized`：身份令牌无效或缺失
- `403 Forbidden`：权限不足、数据范围不足、用户禁用
- `404 Not Found`：目标资源不存在
- `409 Conflict`：唯一性冲突，例如邮箱、用户名重复
- `422 Unprocessable Entity`：请求参数格式不合法
- `500 Internal Server Error`：未捕获异常

## 6. 业务码命名规则

推荐格式：

`模块_动作_结果`

示例：

- `AUTH_INVALID_TOKEN`
- `USER_NOT_FOUND`
- `DATA_SCOPE_DENIED`

命名要求：

- 全大写
- 单词之间使用下划线
- 稳定且可长期复用
- 前端不依赖中文消息，而是依赖 `code`

## 7. 消息口径要求

- 默认使用中文
- 尽量简短明确
- 面向业务使用者可理解
- 不暴露数据库、堆栈、框架内部细节

## 8. 当前实现范围

目前已统一到以下接口：

- `/api/v1/auth/backend/password-login`
- `/api/v1/auth/backend/mobile-code-login`
- `/api/v1/auth/miniapp/code-login`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/users/*`

后续新增接口必须复用统一响应工具，不再直接返回裸对象或 `detail` 字段。
