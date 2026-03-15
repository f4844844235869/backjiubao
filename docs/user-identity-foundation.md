# 统一用户身份骨架说明

本文档说明当前系统对员工用户、小程序用户、手机号绑定的基础建模约定。

## 1. 统一主体

当前统一使用 `user` 作为账号主体表，不再拆成两套完全割裂的用户表。

核心原则：

- `user` 只表示“系统中的一个账号主体”
- `user_type` 表示身份来源类型
- 角色、权限、数据范围决定能做什么
- 组织绑定决定属于哪里

当前已使用的 `user_type`：

- `EMPLOYEE`

后续预留：

- `MINI_APP_MEMBER`
- `SYSTEM`

## 2. 员工身份

员工相关信息单独放在 `employee_profile`：

- `user_id`
- `employee_no`
- `employment_status`
- `hired_at`
- `left_at`

当前约定：

- 员工创建时自动补员工档案
- 离职不修改 `user_type`
- 是否还能登录后台，看 `user.status`
- 是否在职，看 `employee_profile.employment_status`

## 3. 小程序身份

小程序身份单独放在 `miniapp_account`：

- `user_id`
- `app_id`
- `openid`
- `unionid`
- `nickname`
- `avatar_url`
- `gender`
- `country`
- `province`
- `city`
- `language`

当前阶段只完成表骨架，接口仍是占位。

## 4. 手机号绑定

手机号绑定单独放在 `user_phone_binding`：

- `user_id`
- `phone`
- `country_code`
- `is_verified`
- `source`
- `verified_at`

当前设计意图：

- 手机号不是唯一身份来源，而是“经过验证的联系方式”
- 小程序登录后可再补手机号绑定
- 后续 B 端手机号验证码登录也可复用这一层绑定关系

## 5. 登录接口拆分

当前已明确区分两条登录链路：

- B 端密码登录：`POST /api/v1/auth/backend/password-login`
- 小程序登录：`POST /api/v1/auth/miniapp/code-login`

当前兼容入口：

- `POST /api/v1/auth/login`

当前待实现：

- `POST /api/v1/auth/backend/mobile-code-login`
- `POST /api/v1/auth/miniapp/code-login`

## 6. 后续建议

建议下一步继续按这个顺序推进：

1. 接微信小程序 `code` 换会话接口
2. 增加小程序首次登录自动注册/绑定
3. 增加手机号授权绑定流程
4. 给员工档案补充岗位、部门、门店、入离职操作
